using System;
using AncientConquest.World;

namespace AncientConquest.Simulation
{
    public readonly struct ShipAdjacentPlan
    {
        private readonly byte[] points;
        public int OriginX { get; }
        public int OriginY { get; }
        public int TargetX { get; }
        public int TargetY { get; }
        public sbyte TargetHeading { get; }
        public byte InitialState { get; }
        public bool CenterGate { get; }
        public int PathIndex => points == null ? 0 : 1;
        public int PathCount => points == null ? 0 : 2;

        internal ShipAdjacentPlan(int targetX, int targetY, sbyte targetHeading)
        {
            OriginX = 16; OriginY = 2;
            TargetX = targetX; TargetY = targetY; TargetHeading = targetHeading;
            InitialState = targetHeading == 5 ? (byte)3 : (byte)2;
            CenterGate = targetHeading == 5;
            points = new byte[10];
            points[0] = 16; points[2] = 2; points[4] = unchecked((byte)targetHeading);
            points[5] = unchecked((byte)targetX); points[7] = unchecked((byte)targetY);
            points[9] = unchecked((byte)targetHeading);
        }

        /// <summary>Two native5-byte records (int16X,int16Y,heading), copied by value.</summary>
        public byte[] CapturePoints()
        {
            return points == null ? new byte[0] : (byte[])points.Clone();
        }
    }

    /// <summary>
    /// Closed initial source0b adjacent branch proved through native4a6330,
    /// 4a5740 and55c9a0. This is not the original general pathfinder.
    /// Only the original local flags and eight stationary source fleet cells
    /// are supported; other worlds fail explicitly rather than invent a route.
    /// </summary>
    public static class ShipAdjacentPlanner
    {
        private static readonly int[,] Fleet =
        { {16,2}, {21,5}, {19,4}, {11,18}, {9,21}, {10,22}, {6,13}, {6,14} };
        private static readonly uint[,] LocalFlags =
        { {0x308u,8u,1u}, {1u,1u,1u}, {7u,7u,1u} };
        private static readonly int[,] Directions =
        { {1,0}, {1,-1}, {0,-1}, {-1,-1}, {-1,0}, {-1,1}, {0,1}, {1,1} };

        public static bool TryPlan(MissionOccupancyGrid grid, object owner, int originX, int originY,
                                   sbyte heading, int goalX, int goalY, byte restriction,
                                   out ShipAdjacentPlan plan)
        {
            plan = default;
            if (grid == null) throw new ArgumentNullException(nameof(grid));
            if (owner == null) throw new ArgumentNullException(nameof(owner));
            if (originX != 16 || originY != 2 || heading != 5 || restriction != 0)
                throw new NotSupportedException("Only initial source0b16,2/heading5/restriction0 is supported.");
            if (grid.Width != 24 || grid.Height != 24)
                throw new NotSupportedException("The original24x24 source map is required.");
            if (goalX < 15 || goalX > 17 || goalY < 1 || goalY > 3 ||
                (goalX == originX && goalY == originY))
                throw new NotSupportedException("The goal must be one of the eight initial adjacent cells.");
            ValidateInitialFleet(grid, owner);
            for (int y = 0; y < 3; ++y)
                for (int x = 0; x < 3; ++x)
                    if (grid.GetFlags(15 + x, 1 + y) != LocalFlags[y, x])
                        throw new NotSupportedException("The original local source flags are required.");

            sbyte targetHeading = -1;
            for (sbyte index = 0; index < 8; ++index)
                if (originX + Directions[index, 0] == goalX && originY + Directions[index, 1] == goalY)
                    targetHeading = index;
            if (!ShipAdjacentQuery.CanEnter(grid, owner, goalX, goalY, unchecked((byte)targetHeading),
                                            restriction, RejectUnexpectedCorner))
                return false;

            // The actual native planner selects its direct two-point branch
            // for all six passable source goals. N and NW fail before search.
            // Native EAXlow0 also occurs on success; it is not a bool result.
            plan = new ShipAdjacentPlan(goalX, goalY, targetHeading);
            return true;
        }

        private static ShipNavigationOccupant RejectUnexpectedCorner(object occupant)
        {
            // Validated initial fleet geometry leaves every adjacent corner
            // empty. Never assume a state/class for an unknown owner identity.
            throw new NotSupportedException("The initial source reference has no occupied adjacent corner.");
        }

        private static void ValidateInitialFleet(MissionOccupancyGrid grid, object owner)
        {
            var identities = new object[8];
            for (int index = 0; index < identities.Length; ++index)
            {
                identities[index] = grid.GetOccupant(Fleet[index, 0], Fleet[index, 1]);
                if (identities[index] == null)
                    throw new NotSupportedException("All eight initial source fleet claims are required.");
                for (int earlier = 0; earlier < index; ++earlier)
                    if (ReferenceEquals(identities[index], identities[earlier]))
                        throw new NotSupportedException("The eight source fleet owner identities must be distinct.");
            }
            if (!ReferenceEquals(identities[0], owner))
                throw new ArgumentException("The requesting owner must retain source0b's origin claim.", nameof(owner));
            int occupied = 0;
            for (int y = 0; y < grid.Height; ++y)
                for (int x = 0; x < grid.Width; ++x)
                    if (grid.GetOccupant(x, y) != null) ++occupied;
            if (occupied != 8)
                throw new NotSupportedException("Only the eight initial source fleet claims are supported.");
        }
    }
}
