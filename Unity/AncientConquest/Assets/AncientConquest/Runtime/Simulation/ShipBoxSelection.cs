using System;
using System.Collections.Generic;
using AncientConquest.World;

namespace AncientConquest.Simulation
{
    /// <summary>Normal ship projection of49c3f0/49c520 and actual temporary-vector uniqueness.</summary>
    public static class ShipBoxSelection
    {
        public static object[] Collect(MissionOccupancyGrid grid, int x, int y, int width, int height,
            Func<object, ShipHoverActor> describe, Func<object, int> reservedCell,
            byte localSide = 1, byte localPlayer = 1)
        {
            if (grid == null || describe == null || reservedCell == null) throw new ArgumentNullException();
            if (grid.Width != 24 || grid.Height != 24) throw new NotSupportedException("The24x24 reference is required.");
            if (x < 0 || x >= 24 || y < 0 || y >= 24 || width < 1 || height < 1 ||
                width > 24 - x || height > 24 - y) throw new ArgumentOutOfRangeException(nameof(width));
            var found = new List<object>();
            for (int row = y; row < y + height; row++) for (int column = x; column < x + width; column++)
            {
                object owner = grid.GetOccupant(column, row);
                if (owner == null) continue;
                ShipHoverActor actor = describe(owner);
                if (actor.RuntimeClassTag < 200 || actor.RuntimeClassTag > 211)
                    throw new NotSupportedException("Only normal ships are supported.");
                if (actor.OwnerSide * 4 + actor.OwnerPlayer != localSide * 4 + localPlayer ||
                    reservedCell(owner) == row * 24 + column) continue;
                bool duplicate = false;
                foreach (object old in found) if (ReferenceEquals(old, owner)) { duplicate = true; break; }
                if (!duplicate) found.Add(owner);
            }
            return found.ToArray();
        }
    }
}
