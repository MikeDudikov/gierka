using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using AncientConquest.Simulation;
using AncientConquest.World;
using UnityEngine;

namespace AncientConquest.Presentation
{
    /// <summary>
    /// Explicit source0b diagnostic: one prepared native route with controlled
    /// weather0/5 and upgrade0. No general navigation, input, idle RNG or AI.
    /// </summary>
    internal sealed class ShipMovementReference : IDisposable
    {
        private const int Quantum = 40;
        private readonly Dictionary<int, SpriteRenderer> renderers;
        private readonly PreparedShipMovement motion;
        private readonly MissionOccupancyGrid grid;
        private readonly SourceShipPoseReference poses;
        private int frame = 20, calls;
        private readonly int stopAt;
        private uint counter, lastTick;
        private bool disposed, ran;

        internal ShipMovementReference(MissionOccupancyGrid grid, object owner, MissionShipSeed seed,
                                       Dictionary<int, SpriteRenderer> sourceRenderers)
        {
            this.grid = grid;
            renderers = new Dictionary<int, SpriteRenderer>(sourceRenderers);
            if (renderers.Count != 3 || !renderers.ContainsKey(0) || !renderers.ContainsKey(1) ||
                !renderers.ContainsKey(7))
                throw new InvalidOperationException("Source0b requires its shadow, hull and sail renderers.");
            motion = new PreparedShipMovement(grid, owner, seed);
            stopAt = ReadStopAt();
            poses = new SourceShipPoseReference(renderers);
        }

        internal IEnumerator Run()
        {
            if (ran || disposed) throw new InvalidOperationException("The movement diagnostic can run once.");
            ran = true;
            Debug.Log("[ShipMovementReference] conditions: id=0000000b; route=16,2>15,3; path=prepared-native-two-point; " +
                      "wind_force=0; wind_heading=5; owner_upgrade=0; quantum_ms=40; pending_steps=1; " +
                      "clock=bounded-single-step; input=domain-reference; full_simulation=False");
            // Capability value is the verified source0b post-construction mask.
            // The input copy/promotion and prepared path installation are
            // distinct adapters; no general source pathfinder is run in C#.
            var inbox = new ShipMoveRequestInbox(0xfffff7ffu);
            if (!inbox.RequestCellMove(15, 3, 255) || !inbox.HasPendingMove)
                throw new InvalidOperationException("The source move request was not copied.");
            byte[] record = inbox.CapturePendingRecord();
            ShipMovePromotionOutcome promoted = inbox.ConsumeInitialIdleMove();
            if (promoted != ShipMovePromotionOutcome.Promoted || inbox.TargetX != 15 || inbox.TargetY != 3 ||
                !inbox.FirstMove || inbox.HasPendingMove || inbox.ActiveFlags != 0x80u || inbox.RouteByte != 0 ||
                record.Length != 26 || record[25] != 255 || !motion.TryBeginAdjacentReferenceMove())
                throw new InvalidOperationException("The bounded source move request could not begin.");
            Debug.Log("[ShipMovementReference] command: copied_bytes=" + record.Length +
                      "; target=" + inbox.TargetX + "," + inbox.TargetY + "; opaque_byte=" + record[25] +
                      "; promotion=" + promoted + "; active_flags=" + inbox.ActiveFlags +
                      "; pending_flags=" + inbox.PendingFlags + "; route_byte=" + inbox.RouteByte);
            ApplyPose();
            yield return new WaitForEndOfFrame();
            LogStage("initial");
            yield return new WaitForSecondsRealtime(1.25f);

            double segmentStart = Time.realtimeSinceStartupAsDouble;
            int accumulatedTime = 0, previousTime = 0;
            while (!motion.IsStopped && calls < stopAt)
            {
                int capturedTime = accumulatedTime + (int)((Time.realtimeSinceStartupAsDouble - segmentStart) * 1000.0);
                SingleStepClock.StartResult tick = SingleStepClock.Begin(capturedTime, previousTime, counter, Quantum);
                if (!tick.StepRequested) { yield return null; continue; }
                counter = tick.Counter;
                bool forwardTail = motion.Step(1, counter);
                calls++;
                if (forwardTail)
                {
                    ShipFrameProgression.Result pose = ShipFrameProgression.AdvanceForward(frame, 5, counter, lastTick, 2);
                    frame = pose.Frame; lastTick = pose.LastTick;
                }
                previousTime = SingleStepClock.Complete(capturedTime, previousTime, Quantum);
                if (motion.LastStepPublishesPose) ApplyPose();
                string stage = calls == 1 ? "reserved" : calls == 3 ? "animation-only" : calls == 5 ? "first-pixel" :
                               calls == 29 ? "before-transfer" : calls == 30 ? "transferred" :
                               calls == 44 ? "arrived" : null;
                if (stage != null)
                {
                    yield return new WaitForEndOfFrame();
                    LogStage(stage);
                    yield return new WaitForSecondsRealtime(1.25f);
                    // Harness holds freeze this diagnostic's source clock.
                    // This is not a port of the original game's pause mode.
                    accumulatedTime = capturedTime;
                    segmentStart = Time.realtimeSinceStartupAsDouble;
                }
                else yield return null;
                if (calls > 44) throw new InvalidOperationException("Source reference movement exceeded its proven route.");
            }
            if (stopAt < 44)
            {
                Debug.Log("[ShipMovementReference] halted: calls=" + calls + "; counter=" + counter + "; diagnostic_only=True");
                yield break;
            }
            if (!motion.Current.IsComplete || calls != 44 || counter != 44 || frame != 22 || OccupiedCells() != 8)
                throw new InvalidOperationException("The source reference move did not reach its proven final state.");
            Debug.Log("[ShipMovementReference] complete: calls=44; counter=44; frame=22; frozen_after_arrival=True; idle_rng=False");
        }

        private void ApplyPose()
        {
            PreparedShipMovement.Snapshot state = motion.Current;
            if (frame < 20 || frame > 23 || state.WorldPixelY < 132 || state.WorldPixelY > 196)
                throw new InvalidOperationException("The bounded movement left its proven pose or sorting range.");
            poses.Apply(frame, state.WorldPixelX, state.WorldPixelY);
        }

        private static int ReadStopAt()
        {
            string[] arguments = Environment.GetCommandLineArgs();
            int index = Array.IndexOf(arguments, "--ship-movement-stop-at");
            if (index < 0) return 44;
            if (index + 1 >= arguments.Length ||
                !int.TryParse(arguments[index + 1], NumberStyles.Integer, CultureInfo.InvariantCulture, out int stop) ||
                (stop != 0 && stop != 1 && stop != 3 && stop != 5 && stop != 29 && stop != 30 && stop != 44))
                throw new ArgumentException("Movement diagnostic stop must be a supported checkpoint.");
            return stop;
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
            PreparedShipMovement.Snapshot state = motion.Current;
            Debug.Log("[ShipMovementReference] stage=" + stage + " call=" + calls + " counter=" + counter +
                      " cell=" + state.CellX + "," + state.CellY + " world=" + state.WorldPixelX + "," + state.WorldPixelY +
                      " frame=" + frame + " drawn_frame=" + poses.DrawnFrame + " occupied=" + OccupiedCells() + " reserved=" + state.ReservedCellIndex +
                      " complete=" + state.IsComplete + " state=" + state.State + " speed=" + state.Speed +
                      " remainder=" + state.Remainder + " deceleration=" + state.Deceleration +
                      " next=" + state.NextCellIndex + " center_gate=" + state.CenterGate + " last_tick=" + lastTick);
            foreach (KeyValuePair<int, SpriteRenderer> part in renderers)
                Debug.Log("[ShipMovementReference] part: stage=" + stage + "; source_index=" + part.Key +
                          "; sprite=" + part.Value.sprite.name + "; order=" + part.Value.sortingOrder +
                          "; position=" + (int)part.Value.transform.localPosition.x + "," +
                          (int)-part.Value.transform.localPosition.y);
        }

        public void Dispose()
        {
            if (disposed) return;
            disposed = true;
            poses?.Dispose();
        }
    }
}
