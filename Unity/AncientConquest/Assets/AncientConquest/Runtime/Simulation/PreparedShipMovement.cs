using System;
using AncientConquest.World;

namespace AncientConquest.Simulation
{
    /// <summary>
    /// Bounded projection of MoveShip4a3f40 for the native planned route
    /// source0b(16,2,h5) to(15,3). Weather(force0,heading5), upgrade0,
    /// full health and the other seven static source occupants are explicit
    /// reference conditions. This does not implement native pathfinding,
    /// command intake, weather updates, combat, idle RNG or the full world.
    /// </summary>
    public sealed class PreparedShipMovement
    {
        public readonly struct Snapshot
        {
            public int CellX { get; }
            public int CellY { get; }
            public int WorldPixelX { get; }
            public int WorldPixelY { get; }
            public sbyte Heading => 5;
            public byte State { get; }
            public bool CenterGate { get; }
            public int Speed { get; }
            public int Remainder { get; }
            public int Deceleration { get; }
            public int ReservedCellIndex { get; }
            public int NextCellIndex { get; }
            public int PathIndex => 1;
            public int PathCount => 2;
            public bool IsComplete => State == 0 && CellX == 15 && CellY == 3 &&
                                      WorldPixelX == 964 && WorldPixelY == 196;
            internal Snapshot(int x, int y, int worldX, int worldY, byte state,
                              bool center, int speed, int remainder, int deceleration,
                              int reserved, int next)
            {
                CellX = x; CellY = y; WorldPixelX = worldX; WorldPixelY = worldY;
                State = state; CenterGate = center; Speed = speed;
                Remainder = remainder; Deceleration = deceleration;
                ReservedCellIndex = reserved; NextCellIndex = next;
            }
        }

        private static readonly int[,] SourceFleetCells =
        { {16,2}, {21,5}, {19,4}, {11,18}, {9,21}, {10,22}, {6,13}, {6,14} };
        private readonly MissionOccupancyGrid grid;
        private readonly object owner;
        private int cellX = 16, cellY = 2, worldX = 1028, worldY = 132;
        private byte state;
        private bool center = true, started, stopped;
        private int speed, remainder, deceleration, reserved = -1, next;

        public Snapshot Current => new Snapshot(cellX, cellY, worldX, worldY, state,
                                                 center, speed, remainder, deceleration,
                                                 reserved, next);
        public bool IsStopped => stopped;
        /// <summary>True only when the last Step reached native DrawSprite4a4da9.</summary>
        public bool LastStepPublishesPose { get; private set; }

        public PreparedShipMovement(MissionOccupancyGrid grid, object ownerIdentity,
                                    MissionShipSeed source0b)
        {
            if (grid == null) throw new ArgumentNullException(nameof(grid));
            if (ownerIdentity == null) throw new ArgumentNullException(nameof(ownerIdentity));
            if (source0b.InstanceId != 0xbu || source0b.CellX != 16 || source0b.CellY != 2 ||
                source0b.Heading != 5 || source0b.ModelValue != 0 ||
                source0b.OwnerSide != 1 || source0b.OwnerPlayer != 1 ||
                source0b.RequestedHealthPercent != 100 || source0b.SourceEquipmentA != 0 ||
                source0b.SourceEquipmentB != 0 || source0b.SourceOrderCount != 0)
                throw new NotSupportedException("Only the verified full-health source0b reference recipe is supported.");
            if (grid.Width != 24 || grid.Height != 24 ||
                grid.GetFlags(16, 2) != 1u || grid.GetFlags(15, 3) != 7u ||
                grid.GetFlags(15, 2) != 1u || grid.GetFlags(16, 3) != 7u)
                throw new NotSupportedException("The verified source route geometry and local flags are required.");
            this.grid = grid; owner = ownerIdentity;
            if (!ReferenceEquals(grid.GetOccupant(16, 2), owner))
                throw new ArgumentException("The caller must retain the source origin owner reference.", nameof(ownerIdentity));
            ValidateSourceFleet();
        }

        private void ValidateSourceFleet()
        {
            var identities = new object[8];
            for (int i = 0; i < identities.Length; i++)
            {
                identities[i] = grid.GetOccupant(SourceFleetCells[i, 0], SourceFleetCells[i, 1]);
                if (identities[i] == null) throw new NotSupportedException("All eight static source fleet owners are required.");
                for (int j = 0; j < i; j++)
                    if (ReferenceEquals(identities[i], identities[j]))
                        throw new NotSupportedException("Each source fleet owner must retain a distinct identity.");
            }
            int occupied = 0;
            for (int y = 0; y < grid.Height; y++)
                for (int x = 0; x < grid.Width; x++)
                    if (grid.GetOccupant(x, y) != null) occupied++;
            if (occupied != 8) throw new NotSupportedException("Only the eight static source fleet owners are supported.");
        }

        private bool TargetAvailable()
        {
            if (!grid.IsTerrainPassable(15, 3, 0)) return false;
            object target = grid.GetOccupant(15, 3);
            if (target != null && !ReferenceEquals(target, owner)) return false;
            // 499aa0's linked/state6 cases are outside this stationary fleet
            // projection. Never silently guess their result if they appear.
            foreach (object side in new[] { grid.GetOccupant(16, 3), grid.GetOccupant(15, 2) })
                if (side != null)
                    throw new NotSupportedException("The two verified diagonal side cells must remain empty.");
            return true;
        }

        /// <summary>Install only the frozen native two-point route; no path search is ported.</summary>
        public bool TryBeginAdjacentReferenceMove()
        {
            if (started) throw new InvalidOperationException("This reference route can begin once.");
            if (!ReferenceEquals(grid.GetOccupant(16, 2), owner))
                throw new InvalidOperationException("The source origin owner changed before movement.");
            if (!TargetAvailable()) return false;
            started = true; state = 3; center = true;
            return true;
        }

        /// <summary>
        /// Execute one source MoveShip invocation. True means its forward
        /// animation tail was reached: invoke ShipFrameProgression separately,
        /// including the call that stops at the target. A stopped reference
        /// is frozen and returns false; native idle animation is not run.
        /// </summary>
        public bool Step(int pendingSteps, uint sourceCounter)
        {
            if (pendingSteps != 1 && pendingSteps != 2 && pendingSteps != 3 && pendingSteps != 7)
                throw new ArgumentOutOfRangeException(nameof(pendingSteps));
            if (!started) throw new InvalidOperationException("Begin the prepared route before stepping.");
            LastStepPublishesPose = false;
            if (stopped) return false;
            if (state != 3 && !ReferenceEquals(grid.GetOccupant(15, 3), owner))
                throw new InvalidOperationException("The reserved target owner changed during the reference movement.");
            unchecked
            {
                if (state == 3)
                {
                    if (!TargetAvailable())
                    {
                        // Original58d starts at0 for this prepared reference;
                        // strict unsigned elapsed>49 in ShipsStateMove4a3560.
                        if (sourceCounter > 49u) { state = 0; stopped = true; }
                        return false;
                    }
                    if (grid.GetOccupant(15, 3) == null && !grid.TryClaim(15, 3, owner))
                        throw new InvalidOperationException("The target owner changed during reservation.");
                    reserved = 87; next = 87; state = 5; center = true;
                }
                int oldWorldX = worldX, oldWorldY = worldY;
                // Original tables: sourceA max60000/accel1200. Explicit
                // force0 gives60%; native signed /100 truncates toward zero.
                int acceleration = state == 4 ? deceleration * 60 / 100 : 720;
                int newSpeed = speed + pendingSteps * acceleration;
                if (newSpeed <= 0 && state == 4) { newSpeed = 0; deceleration = 0; }
                if (newSpeed > 36000) newSpeed = 36000;
                if (newSpeed <= 6000 && acceleration < 0) newSpeed = speed;
                speed = newSpeed;
                int total = pendingSteps * speed + remainder;
                remainder = total % 3000;
                int quotient = total / 3000;
                int candidateX = oldWorldX - quotient / 3;
                int candidateY = oldWorldY + quotient / 3;
                remainder += (quotient % 3) * 3000;
                if (candidateX < 964) candidateX = 964;
                if (candidateY > 196) candidateY = 196;
                bool moved = candidateX != oldWorldX || candidateY != oldWorldY;
                worldX = candidateX; worldY = candidateY;
                if (moved)
                {
                    // Native deliberately tests the previous sprite center,
                    // after publishing the candidate world position.
                    int previousCellX = (oldWorldX + 28) / 64;
                    int previousCellY = (oldWorldY + 28) / 64;
                    if (center && previousCellY * 24 + previousCellX == next)
                    {
                        if (!grid.Release(cellX, cellY, owner))
                            throw new InvalidOperationException("The source cell owner changed before release.");
                        center = false;
                        cellX = previousCellX; cellY = previousCellY; reserved = -1;
                        state = 4;
                        int distance = Math.Max(Math.Abs(worldX + 28 - cellX * 64 - 32) + 64,
                                                Math.Abs(worldY + 28 - cellY * 64 - 32) + 64);
                        deceleration = speed * speed / (distance * -6000);
                    }
                    if (worldX == 964 && worldY == 196)
                    {
                        center = true; state = 0; speed = 0; reserved = -1; stopped = true;
                    }
                }
                LastStepPublishesPose = moved;
                return true;
            }
        }
    }
}
