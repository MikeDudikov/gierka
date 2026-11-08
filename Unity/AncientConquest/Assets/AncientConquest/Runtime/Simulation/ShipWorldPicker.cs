using System;
using AncientConquest.World;

namespace AncientConquest.Simulation
{
    /// <summary>A normal ship's current logical sprite geometry and separate hit masks.</summary>
    public readonly struct ShipPointerPose
    {
        public ShipPointerMask Mask { get; }
        public int PublishedWorldX { get; }
        public int PublishedWorldY { get; }
        public int StoredFrame { get; }
        public sbyte Heading { get; }
        public uint RuntimeClassTag { get; }

        public ShipPointerPose(ShipPointerMask mask, int publishedWorldX, int publishedWorldY,
                               int storedFrame, sbyte heading, uint runtimeClassTag = 200u)
        {
            if (mask == null) throw new ArgumentNullException(nameof(mask));
            if (runtimeClassTag < 200u || runtimeClassTag > 211u)
                throw new NotSupportedException("Only normal source ship classes200..211 are supported.");
            Mask = mask;
            PublishedWorldX = publishedWorldX; PublishedWorldY = publishedWorldY;
            StoredFrame = storedFrame; Heading = heading; RuntimeClassTag = runtimeClassTag;
        }

        internal bool Contains(int worldX, int worldY, bool precise)
        {
            if (Mask == null)
                throw new InvalidOperationException("The picker requires an initialized source ship pose.");
            return Mask.Contains(worldX, worldY, PublishedWorldX, PublishedWorldY, StoredFrame, Heading, precise);
        }
    }

    /// <summary>
    /// Normal-ship projection of Dump49a580 on the reference24x24 world.
    /// The caller supplies no-fog visibility and empty non-ship object slots.
    /// This is not the full source object-slot/fog/ownership policy.
    /// </summary>
    public static class ShipWorldPicker
    {
        // Clockwise directions beginning at NW. These are source table entries,
        // not a render-depth ordering or a sort around the cursor.
        private static readonly int[] DirectionX = {-1,0,1,1,1,0,-1,-1};
        private static readonly int[] DirectionY = {-1,-1,-1,0,1,1,1,0};
        private static readonly int[][] Neighbours =
        {
            new[] {3,4,5},             // top-left
            new[] {5,6,7},             // top-right
            new[] {7,0,1},             // bottom-right
            new[] {1,2,3},             // bottom-left
            new[] {3,4,5,6,7},         // top
            new[] {5,6,7,0,1},         // right
            new[] {7,0,1,2,3},         // bottom
            new[] {1,2,3,4,5},         // left
            new[] {0,1,2,3,4,5,6,7}    // interior
        };

        public static object Pick(MissionOccupancyGrid grid, int worldX, int worldY,
                                  int cellX, int cellY, bool precise,
                                  Func<object, ShipPointerPose> describe)
        {
            if (grid == null) throw new ArgumentNullException(nameof(grid));
            if (grid.Width != 24 || grid.Height != 24)
                throw new NotSupportedException("The bounded source picker requires the24x24 reference world.");
            if (describe == null) throw new ArgumentNullException(nameof(describe));
            if (cellX < 0 || cellX >= grid.Width || cellY < 0 || cellY >= grid.Height)
                throw new ArgumentOutOfRangeException(nameof(cellX));
            object candidate = Hit(grid, cellX, cellY, worldX, worldY, precise, describe);
            if (candidate != null || !precise) return candidate;
            int[] neighbours = Neighbours[BorderKind(cellX, cellY, grid.Width, grid.Height)];
            for (int index = 0; index < neighbours.Length; index++)
            {
                int direction = neighbours[index];
                candidate = Hit(grid, cellX + DirectionX[direction], cellY + DirectionY[direction],
                                worldX, worldY, true, describe);
                if (candidate != null) return candidate;
            }
            return null;
        }

        private static object Hit(MissionOccupancyGrid grid, int cellX, int cellY,
                                  int worldX, int worldY, bool precise,
                                  Func<object, ShipPointerPose> describe)
        {
            object owner = grid.GetOccupant(cellX, cellY);
            return owner != null && describe(owner).Contains(worldX, worldY, precise) ? owner : null;
        }

        // Zero-based projection of49a1d0's source kinds1..9.
        private static int BorderKind(int x, int y, int width, int height)
        {
            if (x == 0) return y == 0 ? 0 : y == height - 1 ? 3 : 7;
            if (x == width - 1) return y == 0 ? 1 : y == height - 1 ? 2 : 5;
            return y == height - 1 ? 6 : y == 0 ? 4 : 8;
        }
    }
}
