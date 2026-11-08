using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using AncientConquest.Simulation;
using AncientConquest.World;
using UnityEngine;

namespace AncientConquest.Presentation
{
    /// <summary>Bounded source0b order-cycle diagnostic, separate from normal gameplay input.</summary>
    internal sealed class ShipOrderReference : IDisposable
    {
        private const string Prefix = "[ShipOrderReference]";
        private readonly MissionOccupancyGrid grid;
        private readonly ShipMoveOrder command;
        private readonly SourceShipPoseReference poses;
        private readonly SourceCohortOrderReference order;
        private readonly Dictionary<int, SpriteRenderer> renderers;
        private readonly Action<string, int, ShipMoveOrder.Snapshot> checkpointObserver;
        private readonly int goalX, goalY, nextX, nextY, stopAt;
        private readonly uint sessionSeed;
        private readonly bool hasNext;
        private readonly HashSet<string> observed = new HashSet<string>(StringComparer.Ordinal);
        private readonly List<string> events = new List<string>(12);
        private uint counter;
        private int calls, sample, epoch = 1;
        private string operation = "initial";
        private bool ran, disposed, accepted;

        internal ShipOrderReference(MissionOccupancyGrid grid, object owner, MissionShipSeed seed,
                                    Dictionary<int, SpriteRenderer> sourceRenderers,
                                    SourceCohortOrderReference sourceOrder,
                                    Action<string, int, ShipMoveOrder.Snapshot> checkpointObserver = null)
        {
            this.grid = grid;
            this.checkpointObserver = checkpointObserver;
            order = sourceOrder ?? throw new ArgumentNullException(nameof(sourceOrder));
            goalX = ReadArgument("--ship-order-target-x", 18);
            goalY = ReadArgument("--ship-order-target-y", 5);
            nextX = ReadArgument("--ship-order-next-x", -1);
            nextY = ReadArgument("--ship-order-next-y", -1);
            hasNext = HasArgument("--ship-order-next-x") || HasArgument("--ship-order-next-y");
            if (hasNext && (!HasArgument("--ship-order-next-x") || !HasArgument("--ship-order-next-y")))
                throw new ArgumentException("Both coordinates of the next diagnostic target are required.");
            stopAt = ReadArgument("--ship-order-stop-at", -1);
            if (stopAt < -1 || stopAt > 4096) throw new ArgumentOutOfRangeException(nameof(stopAt));
            sessionSeed = ReadUnsignedArgument("--ship-order-session-seed", 0);
            renderers = new Dictionary<int, SpriteRenderer>(sourceRenderers);
            command = new ShipMoveOrder(grid, owner, seed, sessionSeed);
            poses = new SourceShipPoseReference(renderers);
        }

        internal IEnumerator Run()
        {
            if (ran || disposed) throw new InvalidOperationException("The order diagnostic can run once.");
            ran = true;
            order.LogReadiness(Prefix);
            Debug.Log(Prefix + " conditions: id=0000000b; origin=16,2; goal=" + goalX + "," + goalY +
                      "; next=" + (hasNext ? nextX + "," + nextY : "none") + "; session_seed=" + sessionSeed +
                      "; planner=source-normal-work; initial_counter=0; wind_force=0; wind_heading=5; " +
                      "owner_upgrade=0; quantum_ms=40; pending_steps=1; clock=bounded-single-step; " +
                      "input=domain-reference; full_simulation=False; sorting=source-normal-cohort");
            var initial = command.Current.Motion;
            ApplyPose(initial.DrawnFrame, initial.PublishedWorldX, initial.PublishedWorldY,
                      Math.Max(10000, 20000 - 56 - initial.PublishedWorldY));
            yield return new WaitForEndOfFrame();
            LogStage("initial");
            yield return new WaitForSecondsRealtime(1.25f);
            Request(goalX, goalY);
            yield return new WaitForEndOfFrame();
            LogStage("request-1");
            yield return new WaitForSecondsRealtime(1.25f);
            double segmentStart = Time.realtimeSinceStartupAsDouble;
            int accumulatedTime = 0, previousTime = 0;
            while (true)
            {
                if (calls == stopAt)
                {
                    yield return new WaitForEndOfFrame();
                    LogStage("halted");
                    yield return new WaitForSecondsRealtime(1.25f);
                    Debug.Log(Prefix + " halted: calls=" + calls + "; counter=" + counter + "; diagnostic_only=True");
                    yield break;
                }
                if (calls >= 4096) throw new InvalidOperationException("Source order exceeded its diagnostic bound.");
                int capturedTime = accumulatedTime + (int)((Time.realtimeSinceStartupAsDouble - segmentStart) * 1000.0);
                SingleStepClock.StartResult tick = SingleStepClock.Begin(capturedTime, previousTime, counter, 40);
                if (!tick.StepRequested) { yield return null; continue; }
                var before = command.Current;
                counter = tick.Counter;
                command.Tick(counter, 1);
                calls++; sample++; operation = "tick";
                var after = command.Current;
                var m = after.Motion;
                if (m.SourceCounter != counter)
                    throw new InvalidOperationException("Source order counter drifted from its diagnostic clock.");
                ApplyPublications();
                previousTime = SingleStepClock.Complete(capturedTime, previousTime, 40);
                events.Clear();
                Observe("promoted", (after.ActiveFlags & 0x80u) != 0);
                Observe("path", m.PathCount > 0);
                Observe("turn", command.LastStepPublishesPose && m.State == 2);
                Observe("reserved", m.ReservedCellIndex >= 0);
                Observe("moving", m.WorldPixelX != before.Motion.WorldPixelX || m.WorldPixelY != before.Motion.WorldPixelY);
                Observe("transferred", m.CellX != before.Motion.CellX || m.CellY != before.Motion.CellY);
                Observe("path-complete", m.IsComplete);
                Observe("stop-request", (after.PendingFlags & 8u) != 0);
                Observe("active-cleared", (before.ActiveFlags & 0x80u) != 0 && (after.ActiveFlags & 0x80u) == 0);
                bool idlePublished = command.CanRequestMove && command.LastStepPublishesPose && m.DrawnFrame >= 56 && m.DrawnFrame <= 87;
                Observe("idle-published", idlePublished);
                if (events.Count > 0)
                {
                    foreach (string stage in events)
                    {
                        yield return new WaitForEndOfFrame();
                        LogStage(stage);
                        yield return new WaitForSecondsRealtime(1.25f);
                    }
                    accumulatedTime = capturedTime;
                    segmentStart = Time.realtimeSinceStartupAsDouble;
                }
                else yield return null;
                // A bound captures the state after its final Tick, before
                // any following request or normal diagnostic completion.
                if (calls == stopAt || !idlePublished) continue;
                if (hasNext && epoch == 1)
                {
                    epoch++;
                    Request(nextX, nextY);
                    yield return new WaitForEndOfFrame();
                    LogStage("request-2");
                    yield return new WaitForSecondsRealtime(1.25f);
                    accumulatedTime = capturedTime;
                    segmentStart = Time.realtimeSinceStartupAsDouble;
                    continue;
                }
                if (OccupiedCells() != 8) throw new InvalidOperationException("Completed order retained an extra reservation.");
                Debug.Log(Prefix + " complete: calls=" + calls + "; counter=" + counter + "; epochs=" + epoch +
                          "; target_reached=" + after.RequestedTargetReached + "; active_flags=" + after.ActiveFlags +
                          "; idle_rng=True; full_simulation=False");
                yield break;
            }
        }

        private void Request(int x, int y)
        {
            accepted = command.RequestCellMove(x, y, 255);
            if (!accepted) throw new InvalidOperationException("The supported idle diagnostic move request was refused.");
            sample++; operation = "request";
            ApplyPublications();
        }

        private void Observe(string family, bool condition)
        {
            string stage = family + "-" + epoch;
            if (condition && observed.Add(stage)) events.Add(stage);
        }

        private void ApplyPublications()
        {
            for (int i = 0; i < command.LastStepPublicationCount; i++)
            {
                var publication = command.GetLastStepPublication(i);
                ApplyPose(publication.Frame, publication.WorldPixelX, publication.WorldPixelY, publication.Depth);
            }
            var s = command.Current.Motion;
            if (poses.DrawnFrame != s.DrawnFrame || poses.WorldPixelX != s.PublishedWorldX || poses.WorldPixelY != s.PublishedWorldY)
                throw new InvalidOperationException("The visible pose differs from the last source order publication.");
        }

        private void ApplyPose(int frame, int x, int y, int depth)
        {
            if (frame < 0 || frame > 87 || x < 0 || y < 0 || x + 56 > 1536 || y + 56 > 1536 ||
                depth != Math.Max(10000, 20000 - 56 - y))
                throw new InvalidOperationException("The order pose left its verified normal source0b geometry.");
            order.UpdateParent(0xbu, depth);
            poses.Apply(frame, x, y);
        }

        private int OccupiedCells()
        {
            int count = 0;
            for (int y = 0; y < grid.Height; y++) for (int x = 0; x < grid.Width; x++)
                if (grid.GetOccupant(x, y) != null) count++;
            return count;
        }

        private void LogStage(string stage)
        {
            var s = command.Current;
            var m = s.Motion;
            Debug.Log(Prefix + " stage=" + stage + " call=" + calls + " counter=" + counter +
                      " goal=" + s.TargetX + "," + s.TargetY + " accepted=" + accepted +
                      " cell=" + m.CellX + "," + m.CellY + " world=" + m.WorldPixelX + "," + m.WorldPixelY +
                      " published_world=" + m.PublishedWorldX + "," + m.PublishedWorldY +
                      " heading=" + m.Heading + " target_heading=" + m.TargetHeading + " state=" + m.State +
                      " frame=" + m.StoredFrame + " drawn_frame=" + m.DrawnFrame + " last_tick=" + m.LastFrameTick +
                      " last_state_counter=" + m.LastStateCounter + " turn_step=" + m.TurnStep +
                      " center_gate=" + m.CenterGate + " speed=" + m.Speed + " remainder=" + m.Remainder +
                      " deceleration=" + m.Deceleration + " reserved=" + m.ReservedCellIndex + " next=" + m.NextCellIndex +
                      " path_index=" + m.PathIndex + " path_count=" + m.PathCount + " occupied=" + OccupiedCells() +
                      " complete=" + m.IsComplete + " publishes_pose=" + command.LastStepPublishesPose +
                      " forward_tail=" + command.LastStepReachedForwardTail +
                      " waypoint=" + m.WaypointX + "," + m.WaypointY +
                      " next_waypoint=" + m.NextWaypointX + "," + m.NextWaypointY +
                      " publication_count=" + command.LastStepPublicationCount +
                      " sample_index=" + sample + " epoch=" + epoch + " operation=" + operation +
                      " pending_flags=" + s.PendingFlags + " active_flags=" + s.ActiveFlags +
                      " deferred_flags=" + s.DeferredFlags + " stop_mask=" + s.StopMask + " ready_mask=" + s.ReadyMask +
                      " first_navigation=" + s.FirstNavigation + " retry=" + s.Retry +
                      " last_plan_counter=" + s.LastPlanCounter + " retry_interval=" + s.RetryInterval +
                      " snapshot_retry=" + s.SnapshotRetry + " snapshot_target=" + s.SnapshotTargetX + "," + s.SnapshotTargetY +
                      " snapshot_cell=" + s.SnapshotCellX + "," + s.SnapshotCellY +
                      " random_state=" + s.RandomState + " can_request=" + command.CanRequestMove +
                      " requested_goal=" + s.RequestedGoalX + "," + s.RequestedGoalY +
                      " path_endpoint=" + m.PathEndpointX + "," + m.PathEndpointY +
                      " requested_reached=" + s.RequestedTargetReached + " last_cell=" + m.LastCellIndex +
                      " cache_count=" + s.CachedObstacleCount + " cache_hex=" + CacheHex());
            byte[] points = command.CaptureRoutePoints();
            Debug.Log(Prefix + " path: stage=" + stage + "; count=" + m.PathCount + "; points_hex=" +
                      BitConverter.ToString(points).Replace("-", "").ToLowerInvariant());
            foreach (KeyValuePair<int, SpriteRenderer> part in renderers)
                Debug.Log(Prefix + " part: stage=" + stage + "; source_index=" + part.Key +
                          "; sprite=" + part.Value.sprite.name + "; order=" + part.Value.sortingOrder +
                          "; position=" + (int)part.Value.transform.localPosition.x + "," + (int)-part.Value.transform.localPosition.y);
            order.LogStage(stage, Prefix);
            checkpointObserver?.Invoke(stage, sample, s);
        }

        private string CacheHex()
        {
            var text = new System.Text.StringBuilder();
            foreach (int index in command.CaptureCachedObstacles()) text.Append(index.ToString("x4", CultureInfo.InvariantCulture));
            return text.ToString();
        }

        private static bool HasArgument(string name) => Array.IndexOf(Environment.GetCommandLineArgs(), name) >= 0;
        private static string ArgumentValue(string name)
        {
            string[] args = Environment.GetCommandLineArgs();
            int index = Array.IndexOf(args, name);
            if (index < 0) return null;
            if (Array.LastIndexOf(args, name) != index || index + 1 >= args.Length)
                throw new ArgumentException("Expected one value after " + name);
            return args[index + 1];
        }
        private static int ReadArgument(string name, int fallback)
        {
            string raw = ArgumentValue(name);
            if (raw == null) return fallback;
            if (!int.TryParse(raw, NumberStyles.Integer, CultureInfo.InvariantCulture, out int result))
                throw new ArgumentException("Expected one integer after " + name);
            return result;
        }
        private static uint ReadUnsignedArgument(string name, uint fallback)
        {
            string raw = ArgumentValue(name);
            if (raw == null) return fallback;
            if (!uint.TryParse(raw, NumberStyles.None, CultureInfo.InvariantCulture, out uint result))
                throw new ArgumentException("Expected one unsigned integer after " + name);
            return result;
        }
        public void Dispose()
        {
            if (disposed) return;
            disposed = true;
            poses?.Dispose();
        }
    }
}
