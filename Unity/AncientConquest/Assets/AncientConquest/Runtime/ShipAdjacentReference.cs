using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using AncientConquest.Simulation;
using AncientConquest.World;
using UnityEngine;

namespace AncientConquest.Presentation
{
    /// <summary>Opt-in source0b adjacent planning, turn and movement diagnostic.</summary>
    internal sealed class ShipAdjacentReference : IDisposable
    {
        private const int Quantum = 40;
        private readonly MissionOccupancyGrid grid;
        private readonly ShipAdjacentMovement motion;
        private readonly SourceShipPoseReference poses;
        private readonly Dictionary<int, SpriteRenderer> renderers;
        private readonly int goalX, goalY, stopAt;
        private readonly HashSet<string> observed = new HashSet<string>(StringComparer.Ordinal);
        private readonly List<string> events = new List<string>(7);
        private uint counter = 1;
        private int calls;
        private bool accepted, ran, disposed;

        internal ShipAdjacentReference(MissionOccupancyGrid grid, object owner, MissionShipSeed seed,
                                       Dictionary<int, SpriteRenderer> sourceRenderers)
        {
            this.grid = grid;
            goalX = ReadArgument("--ship-adjacent-target-x", 17);
            goalY = ReadArgument("--ship-adjacent-target-y", 2);
            stopAt = ReadArgument("--ship-adjacent-stop-at", -1);
            if (stopAt < -1 || stopAt > 512)
                throw new ArgumentOutOfRangeException(nameof(stopAt));
            renderers = new Dictionary<int, SpriteRenderer>(sourceRenderers);
            motion = new ShipAdjacentMovement(grid, owner, seed);
            poses = new SourceShipPoseReference(renderers);
        }

        internal IEnumerator Run()
        {
            if (ran || disposed) throw new InvalidOperationException("The adjacent diagnostic can run once.");
            ran = true;
            Debug.Log("[ShipAdjacentReference] conditions: id=0000000b; origin=16,2; goal=" + goalX + "," + goalY +
                      "; planner=bounded-source-adjacent; planner_counter=1; wind_force=0; wind_heading=5; " +
                      "owner_upgrade=0; quantum_ms=40; pending_steps=1; clock=bounded-single-step; " +
                      "input=domain-reference; full_simulation=False");
            var inbox = new ShipMoveRequestInbox(0xfffff7ffu);
            if (!inbox.RequestCellMove(goalX, goalY, 255))
                throw new InvalidOperationException("The adjacent move request was not copied.");
            byte[] record = inbox.CapturePendingRecord();
            ShipMovePromotionOutcome promoted = inbox.ConsumeInitialIdleMove();
            if (record.Length != 26 || record[25] != 255 || promoted != ShipMovePromotionOutcome.Promoted ||
                inbox.TargetX != goalX || inbox.TargetY != goalY || inbox.HasPendingMove ||
                inbox.ActiveFlags != 0x80u || inbox.RouteByte != 0 || !inbox.FirstMove)
                throw new InvalidOperationException("The adjacent request promotion differs from its verified source contract.");
            accepted = motion.TryBeginAdjacentReferenceMove(goalX, goalY, counter);
            Debug.Log("[ShipAdjacentReference] command: copied_bytes=" + record.Length + "; target=" +
                      goalX + "," + goalY + "; opaque_byte=" + record[25] + "; promotion=" + promoted +
                      "; active_flags=" + inbox.ActiveFlags + "; pending_flags=" + inbox.PendingFlags +
                      "; route_byte=" + inbox.RouteByte + "; has_route=" + accepted);
            ApplyPublishedPose();
            yield return new WaitForEndOfFrame();
            LogStage("initial");
            yield return new WaitForSecondsRealtime(1.25f);
            if (!accepted)
            {
                yield return new WaitForEndOfFrame();
                LogStage("rejected");
                yield return new WaitForSecondsRealtime(1.25f);
                Debug.Log("[ShipAdjacentReference] rejected: goal=" + goalX + "," + goalY +
                          "; calls=0; counter=1; no_route=True; frozen=True");
                yield break;
            }
            double segmentStart = Time.realtimeSinceStartupAsDouble;
            int accumulatedTime = 0, previousTime = 0;
            while (!motion.IsStopped && calls != stopAt)
            {
                if (calls >= 512)
                    throw new InvalidOperationException("Adjacent source movement exceeded its diagnostic bound.");
                int capturedTime = accumulatedTime + (int)((Time.realtimeSinceStartupAsDouble - segmentStart) * 1000.0);
                SingleStepClock.StartResult tick = SingleStepClock.Begin(capturedTime, previousTime, counter, Quantum);
                if (!tick.StepRequested) { yield return null; continue; }
                byte previousState = motion.Current.State;
                counter = tick.Counter;
                motion.Step(1, counter);
                calls++;
                if (motion.Current.SourceCounter != counter)
                    throw new InvalidOperationException("The adjacent source counter drifted from its diagnostic clock.");
                if (motion.LastStepPublishesPose) ApplyPublishedPose();
                previousTime = SingleStepClock.Complete(capturedTime, previousTime, Quantum);
                ShipAdjacentMovement.Snapshot state = motion.Current;
                events.Clear();
                Observe("turn-start", state.StoredFrame >= 32 && state.StoredFrame <= 55);
                Observe("turn-published", motion.LastStepPublishesPose && state.State == 2);
                Observe("turn-complete", previousState == 2 && state.State == 3);
                Observe("reserved", state.ReservedCellIndex >= 0);
                Observe("first-pixel", state.WorldPixelX != 1028 || state.WorldPixelY != 132);
                Observe("transferred", state.CellX != 16 || state.CellY != 2);
                Observe("arrived", state.IsComplete);
                if (events.Count > 0)
                {
                    foreach (string stage in events)
                    {
                        yield return new WaitForEndOfFrame();
                        LogStage(stage);
                        yield return new WaitForSecondsRealtime(1.25f);
                    }
                    // Presentation holds belong to this harness. Preserve the
                    // source clock's remainder without advancing its counter.
                    accumulatedTime = capturedTime;
                    segmentStart = Time.realtimeSinceStartupAsDouble;
                }
                else yield return null;
            }
            if (stopAt >= 0 && calls == stopAt && !motion.IsStopped)
            {
                Debug.Log("[ShipAdjacentReference] halted: calls=" + calls + "; counter=" + counter + "; diagnostic_only=True");
                yield break;
            }
            if (!motion.Current.IsComplete || OccupiedCells() != 8)
                throw new InvalidOperationException("The adjacent source movement did not reach its target state.");
            Debug.Log("[ShipAdjacentReference] complete: goal=" + goalX + "," + goalY + "; calls=" + calls +
                      "; counter=" + counter + "; frame=" + motion.Current.StoredFrame +
                      "; drawn_frame=" + motion.Current.DrawnFrame + "; frozen_after_arrival=True; idle_rng=False");
        }

        private void Observe(string stage, bool condition)
        {
            if (condition && observed.Add(stage)) events.Add(stage);
        }

        private void ApplyPublishedPose()
        {
            ShipAdjacentMovement.Snapshot state = motion.Current;
            // These six local routes keep body depths19748..19876 above the
            // next static body19676; no queue rank crossing occurs.
            if (state.PublishedWorldX < 964 || state.PublishedWorldX > 1092 ||
                state.PublishedWorldY < 68 || state.PublishedWorldY > 196 ||
                state.DrawnFrame < 0 || state.DrawnFrame > 55)
                throw new InvalidOperationException("The adjacent pose left its proven geometry or sorting range.");
            poses.Apply(state.DrawnFrame, state.PublishedWorldX, state.PublishedWorldY);
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
            ShipAdjacentMovement.Snapshot s = motion.Current;
            Debug.Log("[ShipAdjacentReference] stage=" + stage + " call=" + calls + " counter=" + counter +
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
                      " forward_tail=" + motion.LastStepReachedForwardTail);
            foreach (KeyValuePair<int, SpriteRenderer> part in renderers)
                Debug.Log("[ShipAdjacentReference] part: stage=" + stage + "; source_index=" + part.Key +
                          "; sprite=" + part.Value.sprite.name + "; order=" + part.Value.sortingOrder +
                          "; position=" + (int)part.Value.transform.localPosition.x + "," +
                          (int)-part.Value.transform.localPosition.y);
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
