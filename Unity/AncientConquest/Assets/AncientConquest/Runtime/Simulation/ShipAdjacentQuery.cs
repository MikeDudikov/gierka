using System;
using AncientConquest.World;

namespace AncientConquest.Simulation
{
    // Value projection of the fields read from a valid corner-owner/link graph.
    // A malformed native linked-target pointer is outside this adapter's inputs.
    public readonly struct ShipNavigationOccupant
    {
        public uint RuntimeClassTag { get; }
        public byte MovementState { get; }
        public bool HasLink { get; }
        public uint LinkRecordType { get; }
        public int LinkedCellX { get; }
        public int LinkedCellY { get; }

        public ShipNavigationOccupant(uint runtimeClassTag, byte movementState, bool hasLink = false,
                                     uint linkRecordType = 0, int linkedCellX = 0, int linkedCellY = 0)
        {
            RuntimeClassTag = runtimeClassTag;
            MovementState = movementState;
            HasLink = hasLink;
            LinkRecordType = linkRecordType;
            LinkedCellX = linkedCellX;
            LinkedCellY = linkedCellY;
        }
    }

    // Original499aa0 cell predicate only. Corner terrain is deliberately not
    // tested; this is not a pathfinder or a general diagonal-clearance rule.
    public static class ShipAdjacentQuery
    {
        public static bool CanEnter(MissionOccupancyGrid grid, object requester, int targetX, int targetY,
                                    byte heading, byte restriction,
                                    Func<object, ShipNavigationOccupant> describeOccupant)
        {
            if (grid == null) throw new ArgumentNullException(nameof(grid));
            if (requester == null) throw new ArgumentNullException(nameof(requester));
            if (describeOccupant == null) throw new ArgumentNullException(nameof(describeOccupant));
            if (heading > 7) throw new ArgumentOutOfRangeException(nameof(heading));
            if (targetX < 0 || targetX >= grid.Width || targetY < 0 || targetY >= grid.Height)
                throw new ArgumentOutOfRangeException(nameof(targetX));
            if (!grid.IsTerrainPassable(targetX, targetY, restriction)) return false;
            object targetOwner = grid.GetOccupant(targetX, targetY);
            if (targetOwner != null && !ReferenceEquals(targetOwner, requester)) return false;
            if ((heading & 1) == 0) return true;

            int ax, ay, bx, by;
            switch (heading)
            {
                case 1:
                    if (targetX == 0 || targetY == grid.Height - 1) return true;
                    ax = targetX - 1; ay = targetY; bx = targetX; by = targetY + 1;
                    break;
                case 3:
                    if (targetY == grid.Height - 1 || targetX == grid.Width - 1) return true;
                    ax = targetX; ay = targetY + 1; bx = targetX + 1; by = targetY;
                    break;
                case 5:
                    if (targetY == 0 || targetX == grid.Width - 1) return true;
                    ax = targetX + 1; ay = targetY; bx = targetX; by = targetY - 1;
                    break;
                default: // Proven domain leaves only heading7 here.
                    if (targetY == 0 || targetX == 0) return true;
                    ax = targetX; ay = targetY - 1; bx = targetX - 1; by = targetY;
                    break;
            }

            object first = grid.GetOccupant(ax, ay);
            if (first != null)
            {
                ShipNavigationOccupant view = describeOccupant(first);
                if (view.RuntimeClassTag >= 200u && view.RuntimeClassTag <= 211u &&
                    view.MovementState == 6 && view.HasLink && view.LinkRecordType == 200u &&
                    unchecked(view.LinkedCellY * grid.Width + view.LinkedCellX) == by * grid.Width + bx)
                    return false;
            }
            object second = grid.GetOccupant(bx, by);
            return first == null || second == null || !ReferenceEquals(first, second);
        }
    }
}
