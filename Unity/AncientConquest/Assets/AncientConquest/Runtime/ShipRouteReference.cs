using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using AncientConquest.Simulation;
using AncientConquest.World;
using UnityEngine;

namespace AncientConquest.Presentation
{
    /// <summary>Explicit longer-route reference with ordered publication/depth updates.</summary>
    internal sealed class ShipRouteReference : IDisposable
    {
        private const int Quantum = 40;
        private readonly MissionOccupancyGrid grid;
        private readonly object owner;
        private readonly MissionShipSeed seed;
        private readonly ShipRouteMovement motion;
        private readonly SourceShipPoseReference poses;
        private readonly SourceCohortOrderReference order;
        private readonly Dictionary<int, SpriteRenderer> renderers;
        private readonly int goalX, goalY, stopAt;
        private readonly HashSet<string> observed = new HashSet<string>(StringComparer.Ordinal);
        private readonly List<string> events = new List<string>(8);
        private byte[] points;
        private string[,] labels;
        private uint counter = 1;
        private int calls;
        private bool accepted, ran, disposed;

        internal ShipRouteReference(MissionOccupancyGrid grid, object owner, MissionShipSeed seed,
                                    Dictionary<int, SpriteRenderer> sourceRenderers, SourceCohortOrderReference sourceOrder)
        {
            this.grid = grid; this.owner = owner; this.seed = seed;
            order = sourceOrder ?? throw new ArgumentNullException(nameof(sourceOrder));
            goalX = ReadArgument("--ship-route-target-x", 20);
            goalY = ReadArgument("--ship-route-target-y", 6);
            stopAt = ReadArgument("--ship-route-stop-at", -1);
            if (stopAt < -1 || stopAt > 2048) throw new ArgumentOutOfRangeException(nameof(stopAt));
            renderers = new Dictionary<int, SpriteRenderer>(sourceRenderers);
            motion = new ShipRouteMovement(grid, owner, seed);
            poses = new SourceShipPoseReference(renderers);
        }

        internal IEnumerator Run()
        {
            if (ran || disposed) throw new InvalidOperationException("The route diagnostic can run once.");
            ran = true;
            order.LogReadiness();
            Debug.Log("[ShipRouteReference] conditions: id=0000000b; origin=16,2; goal=" + goalX + "," + goalY +
                      "; planner=source-line-wave-static-fleet; planner_counter=1; wind_force=0; wind_heading=5; " +
                      "owner_upgrade=0; quantum_ms=40; pending_steps=1; clock=bounded-single-step; " +
                      "input=domain-reference; full_simulation=False; sorting=source-normal-cohort");
            var inbox = new ShipMoveRequestInbox(0xfffff7ffu);
            if (!inbox.RequestCellMove(goalX, goalY, 255))
                throw new InvalidOperationException("The route move request was not copied.");
            byte[] record = inbox.CapturePendingRecord();
            ShipMovePromotionOutcome promoted = inbox.ConsumeInitialIdleMove();
            if (record.Length != 26 || record[25] != 255 || promoted != ShipMovePromotionOutcome.Promoted ||
                inbox.TargetX != goalX || inbox.TargetY != goalY || inbox.HasPendingMove ||
                inbox.ActiveFlags != 0x80u || inbox.RouteByte != 0 || !inbox.FirstMove)
                throw new InvalidOperationException("The source route request could not be promoted.");
            bool planned = ShipRoutePlanner.TryPlan(grid, owner, seed, goalX, goalY, out ShipRoutePlan plan);
            accepted = motion.TryBegin(planned ? plan : null, counter);
            if (accepted != planned) throw new InvalidOperationException("Planner and motion disagree about the route.");
            points = motion.CaptureRoutePoints();
            string[] families = { "turn-start", "turn-published", "turn-complete", "reserved", "first-pixel", "transferred", "waypoint" };
            labels = new string[families.Length, points.Length / 5];
            for (int family = 0; family < families.Length; family++)
                for (int point = 1; point < points.Length / 5; point++) labels[family, point] = families[family] + "-" + point;
            Debug.Log("[ShipRouteReference] command: copied_bytes=" + record.Length + "; target=" + goalX + "," + goalY +
                      "; opaque_byte=" + record[25] + "; promotion=" + promoted + "; active_flags=" + inbox.ActiveFlags +
                      "; pending_flags=" + inbox.PendingFlags + "; route_byte=" + inbox.RouteByte + "; has_route=" + accepted);
            Debug.Log("[ShipRouteReference] path: count=" + motion.Current.PathCount +
                      "; points_hex=" + BitConverter.ToString(points).Replace("-", "").ToLowerInvariant());
            ApplyPose(motion.Current.DrawnFrame, motion.Current.PublishedWorldX, motion.Current.PublishedWorldY,
                      Math.Max(10000, 20000 - 56 - motion.Current.PublishedWorldY));
            yield return new WaitForEndOfFrame();
            LogStage("initial");
            yield return new WaitForSecondsRealtime(1.25f);
            if (!accepted)
            {
                yield return new WaitForEndOfFrame();
                LogStage("rejected");
                yield return new WaitForSecondsRealtime(1.25f);
                Debug.Log("[ShipRouteReference] rejected: goal=" + goalX + "," + goalY +
                          "; calls=0; counter=1; no_route=True; frozen=True");
                yield break;
            }
            double segmentStart = Time.realtimeSinceStartupAsDouble;
            int accumulatedTime = 0, previousTime = 0;
            while (!motion.IsStopped && calls != stopAt)
            {
                if (calls >= 2048) throw new InvalidOperationException("Source route exceeded its diagnostic bound.");
                int capturedTime = accumulatedTime + (int)((Time.realtimeSinceStartupAsDouble - segmentStart) * 1000.0);
                SingleStepClock.StartResult tick = SingleStepClock.Begin(capturedTime, previousTime, counter, Quantum);
                if (!tick.StepRequested) { yield return null; continue; }
                ShipRouteMovement.Snapshot before = motion.Current;
                counter = tick.Counter;
                motion.Step(1, counter);
                calls++;
                ShipRouteMovement.Snapshot state = motion.Current;
                if (state.SourceCounter != counter)
                    throw new InvalidOperationException("Source route counter drifted from its diagnostic clock.");
                // Replay every publication. Reconstructing the final depth
                // alone loses the source queue's direction-dependent ties.
                for (int index = 0; index < motion.LastStepPublicationCount; index++)
                {
                    ShipRouteMovement.Publication publication = motion.GetLastStepPublication(index);
                    ApplyPose(publication.Frame, publication.WorldPixelX, publication.WorldPixelY, publication.Depth);
                }
                if (poses.DrawnFrame != state.DrawnFrame || poses.WorldPixelX != state.PublishedWorldX ||
                    poses.WorldPixelY != state.PublishedWorldY)
                    throw new InvalidOperationException("The visible pose differs from the last source publication.");
                previousTime = SingleStepClock.Complete(capturedTime, previousTime, Quantum);
                events.Clear();
                ObservePoint(0, before.PathIndex, state.StoredFrame >= 32 && state.StoredFrame <= 55);
                ObservePoint(1, before.PathIndex, motion.LastStepPublishesPose && state.State == 2);
                ObservePoint(2, before.PathIndex, before.State == 2 && state.State == 3);
                if (state.ReservedCellIndex >= 0)
                    ObservePoint(3, PointIndex(state.ReservedCellIndex % grid.Width, state.ReservedCellIndex / grid.Width), true);
                ObservePoint(4, before.PathIndex,
                        state.WorldPixelX != before.WorldPixelX || state.WorldPixelY != before.WorldPixelY);
                if (state.CellX != before.CellX || state.CellY != before.CellY)
                    ObservePoint(5, PointIndex(state.CellX, state.CellY), true);
                ObservePoint(6, before.PathIndex, state.PathIndex > before.PathIndex);
                Observe("arrived", state.IsComplete);
                Observe("stalled", motion.IsStopped && !state.IsComplete);
                if (events.Count > 0)
                {
                    foreach (string stage in events)
                    {
                        yield return new WaitForEndOfFrame();
                        LogStage(stage);
                        yield return new WaitForSecondsRealtime(1.25f);
                    }
                    // Holds are diagnostic. Preserve the source quantum's
                    // remainder and exclude all hold time from the counter.
                    accumulatedTime = capturedTime;
                    segmentStart = Time.realtimeSinceStartupAsDouble;
                }
                else yield return null;
            }
            if (stopAt >= 0 && calls == stopAt && !motion.IsStopped)
            {
                Debug.Log("[ShipRouteReference] halted: calls=" + calls + "; counter=" + counter + "; diagnostic_only=True");
                yield break;
            }
            if (!motion.IsStopped || OccupiedCells() != 8)
                throw new InvalidOperationException("The source route did not stop with its original fleet claims.");
            if (!motion.Current.IsComplete)
            {
                Debug.Log("[ShipRouteReference] stalled: goal=" + goalX + "," + goalY + "; calls=" + calls +
                          "; counter=" + counter + "; target_reached=False; frozen=True");
                yield break;
            }
            Debug.Log("[ShipRouteReference] complete: goal=" + goalX + "," + goalY + "; calls=" + calls +
                      "; counter=" + counter + "; frame=" + motion.Current.StoredFrame +
                      "; drawn_frame=" + motion.Current.DrawnFrame + "; frozen_after_arrival=True; idle_rng=False");
        }

        private void Observe(string stage, bool condition)
        {
            if (condition && observed.Add(stage)) events.Add(stage);
        }

        private void ObservePoint(int family, int point, bool condition)
        {
            if (!condition) return;
            if (point < 1 || point >= labels.GetLength(1))
                throw new InvalidOperationException("A source event refers to a waypoint outside its route.");
            Observe(labels[family, point], true);
        }

        private int PointIndex(int x, int y)
        {
            for (int index = 1; index < points.Length / 5; index++)
                if (ReadCoordinate(index, 0) == x && ReadCoordinate(index, 2) == y) return index;
            throw new InvalidOperationException("The source reservation/transfer is outside its active route.");
        }

        private int ReadCoordinate(int index, int offset)
        {
            return unchecked((short)(points[index * 5 + offset] | points[index * 5 + offset + 1] << 8));
        }

        private void ApplyPose(int frame, int worldX, int worldY, int depth)
        {
            if (frame < 0 || frame > 55 || worldX < 0 || worldY < 0 || worldX + 56 > 1536 || worldY + 56 > 1536 ||
                depth != Math.Max(10000, 20000 - 56 - worldY))
                throw new InvalidOperationException("The route pose left its verified source0b geometry.");
            order.UpdateParent(0xbu, depth);
            poses.Apply(frame, worldX, worldY);
        }

        private int OccupiedCells()
        {
            int count = 0;
            for (int y = 0; y < grid.Height; y++)
                for (int x = 0; x < grid.Width; x++)
                    if (grid.GetOccupant(x, y) != null) count++;
            return count;
        }

        private void LogStage(string stage)
        {
            ShipRouteMovement.Snapshot s = motion.Current;
            Debug.Log("[ShipRouteReference] stage=" + stage + " call=" + calls + " counter=" + counter +
                      " goal=" + goalX + "," + goalY + " accepted=" + accepted +
                      " cell=" + s.CellX + "," + s.CellY + " world=" + s.WorldPixelX + "," + s.WorldPixelY +
                      " published_world=" + s.PublishedWorldX + "," + s.PublishedWorldY +
                      " heading=" + s.Heading + " target_heading=" + s.TargetHeading + " state=" + s.State +
                      " frame=" + s.StoredFrame + " drawn_frame=" + s.DrawnFrame + " last_tick=" + s.LastFrameTick +
                      " last_state_counter=" + s.LastStateCounter + " turn_step=" + s.TurnStep +
                      " center_gate=" + s.CenterGate + " speed=" + s.Speed + " remainder=" + s.Remainder +
                      " deceleration=" + s.Deceleration + " reserved=" + s.ReservedCellIndex + " next=" + s.NextCellIndex +
                      " path_index=" + s.PathIndex + " path_count=" + s.PathCount + " occupied=" + OccupiedCells() +
                      " complete=" + s.IsComplete + " publishes_pose=" + motion.LastStepPublishesPose +
                      " forward_tail=" + motion.LastStepReachedForwardTail +
                      " waypoint=" + s.WaypointX + "," + s.WaypointY +
                      " next_waypoint=" + s.NextWaypointX + "," + s.NextWaypointY +
                      " publication_count=" + motion.LastStepPublicationCount);
            foreach (KeyValuePair<int, SpriteRenderer> part in renderers)
                Debug.Log("[ShipRouteReference] part: stage=" + stage + "; source_index=" + part.Key +
                          "; sprite=" + part.Value.sprite.name + "; order=" + part.Value.sortingOrder +
                          "; position=" + (int)part.Value.transform.localPosition.x + "," +
                          (int)-part.Value.transform.localPosition.y);
            order.LogStage(stage);
        }

        private static int ReadArgument(string name, int fallback)
        {
            string[] arguments = Environment.GetCommandLineArgs();
            int index = Array.IndexOf(arguments, name);
            if (index < 0) return fallback;
            if (Array.LastIndexOf(arguments, name) != index || index + 1 >= arguments.Length ||
                !int.TryParse(arguments[index + 1], NumberStyles.Integer, CultureInfo.InvariantCulture, out int value))
                throw new ArgumentException("Expected one integer after " + name);
            return value;
        }

        public void Dispose()
        {
            if (disposed) return;
            disposed = true;
            poses?.Dispose();
        }
    }
}
