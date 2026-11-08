using System;
using AncientConquest.World;

namespace AncientConquest.Simulation
{
    /// <summary>
    /// Initial source0b GetWayNew projection: mode0, restriction0, priority0,
    /// eight static source owner identities and no links. The other seven
    /// reference actors have the oracle's class200-family/state0/group0
    /// metadata; this is not a dynamic world's complete planning policy.
    /// </summary>
    public static class ShipRoutePlanner
    {
        private static readonly int[,] Fleet =
        { {16,2}, {21,5}, {19,4}, {11,18}, {9,21}, {10,22}, {6,13}, {6,14} };

        public static bool TryPlan(MissionOccupancyGrid grid, object owner, MissionShipSeed source0b,
                                   int goalX, int goalY, out ShipRoutePlan plan)
        {
            plan = null;
            Validate(grid, owner, source0b, goalX, goalY);
            if (goalX == 16 && goalY == 2) return false;
            if (!grid.IsTerrainPassable(goalX, goalY, 0)) return false;
            int distance = Math.Max(Math.Abs(goalX - 16), Math.Abs(goalY - 2));
            if (distance == 1)
            {
                byte heading = Heading(goalX - 16, goalY - 2);
                if (!ShipAdjacentQuery.CanEnter(grid, owner, goalX, goalY, heading, 0, UnknownCorner))
                    return false;
            }
            short[] map = CapturePlanningField(grid, owner, goalX, goalY);
            SourcePathfinder.Result result = SourcePathfinder.Find(map, grid.Width, grid.Height,
                                                                  16, 2, goalX, goalY, 0);
            if (!result.Succeeded) return false;
            plan = new ShipRoutePlan(result.CapturePoints(), goalX, goalY);
            return true;
        }

        /// <summary>
        /// Exact static reference branch of49a950 then4a4e20/4a5740. The
        /// destination restores its base terrain value after the7x7 overlay;
        /// a distant occupied goal can therefore plan and later wait in motion.
        /// </summary>
        public static short[] CapturePlanningField(MissionOccupancyGrid grid, object owner,
                                                   int goalX, int goalY)
        {
            if (grid == null) throw new ArgumentNullException(nameof(grid));
            if (owner == null) throw new ArgumentNullException(nameof(owner));
            if (grid.Width != 24 || grid.Height != 24)
                throw new NotSupportedException("The initial source reference requires its24x24 map.");
            if (goalX < 0 || goalX >= grid.Width || goalY < 0 || goalY >= grid.Height)
                throw new ArgumentOutOfRangeException(nameof(goalX));
            ValidateFleet(grid, owner);
            var field = new short[grid.Width * grid.Height];
            for (int y = 0; y < grid.Height; y++)
                for (int x = 0; x < grid.Width; x++)
                    field[y * grid.Width + x] = grid.IsTerrainPassable(x, y, 0) ? (short)0 : (short)-1;
            short destination = field[goalY * grid.Width + goalX];
            for (int y = 0; y < 6; y++)
                for (int x = 13; x < 20; x++)
                {
                    object occupant = grid.GetOccupant(x, y);
                    if (occupant != null && !ReferenceEquals(occupant, owner))
                        field[y * grid.Width + x] = -1;
                }
            field[goalY * grid.Width + goalX] = destination;
            return field;
        }

        private static void Validate(MissionOccupancyGrid grid, object owner, MissionShipSeed seed,
                                     int goalX, int goalY)
        {
            if (grid == null) throw new ArgumentNullException(nameof(grid));
            if (owner == null) throw new ArgumentNullException(nameof(owner));
            if (seed.InstanceId != 0xbu || seed.CellX != 16 || seed.CellY != 2 || seed.Heading != 5 ||
                seed.ModelValue != 0 || seed.OwnerSide != 1 || seed.OwnerPlayer != 1 ||
                seed.RequestedHealthPercent != 100 || seed.SourceEquipmentA != 0 ||
                seed.SourceEquipmentB != 0 || seed.SourceOrderCount != 0)
                throw new NotSupportedException("Only initial full-health source0b is supported.");
            if (grid.Width != 24 || grid.Height != 24)
                throw new NotSupportedException("The initial source reference requires its24x24 map.");
            if (goalX < 0 || goalX >= 24 || goalY < 0 || goalY >= 24)
                throw new ArgumentOutOfRangeException(nameof(goalX));
            ValidateFleet(grid, owner);
        }

        private static void ValidateFleet(MissionOccupancyGrid grid, object owner)
        {
            var identities = new object[8];
            for (int i = 0; i < identities.Length; i++)
            {
                identities[i] = grid.GetOccupant(Fleet[i, 0], Fleet[i, 1]);
                if (identities[i] == null) throw new NotSupportedException("The eight static source fleet claims are required.");
                for (int previous = 0; previous < i; previous++)
                    if (ReferenceEquals(identities[i], identities[previous]))
                        throw new NotSupportedException("Source fleet identities must be distinct.");
            }
            if (!ReferenceEquals(identities[0], owner))
                throw new ArgumentException("The requesting owner must retain source0b's origin.", nameof(owner));
            int occupied = 0;
            for (int y = 0; y < grid.Height; y++)
                for (int x = 0; x < grid.Width; x++)
                    if (grid.GetOccupant(x, y) != null) occupied++;
            if (occupied != 8) throw new NotSupportedException("Only the eight reference fleet claims are supported.");
        }

        private static ShipNavigationOccupant UnknownCorner(object occupant)
        {
            throw new NotSupportedException("The initial source adjacent corners are empty.");
        }

        private static byte Heading(int x, int y)
        {
            if (x > 0) return y < 0 ? (byte)1 : y > 0 ? (byte)7 : (byte)0;
            if (x < 0) return y < 0 ? (byte)3 : y > 0 ? (byte)5 : (byte)4;
            return y < 0 ? (byte)2 : (byte)6;
        }
    }
}
