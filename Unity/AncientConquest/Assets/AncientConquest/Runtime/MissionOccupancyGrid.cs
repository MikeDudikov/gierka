using System;

namespace AncientConquest.World
{
    /// <summary>
    /// Bounded source cell flags and single-owner references. This does not run
    /// pathfinding, populate all object slots or replace the original world grid.
    /// Owners are identities: a valid owner may have source instance ID0.
    /// </summary>
    public sealed class MissionOccupancyGrid
    {
        private readonly uint[] flags;
        private readonly object[] owners;
        public int Width { get; }
        public int Height { get; }

        public MissionOccupancyGrid(int width, int height, uint[] initialFlags)
        {
            if (width <= 0 || height <= 0 || width > short.MaxValue || height > short.MaxValue)
                throw new ArgumentOutOfRangeException(nameof(width));
            if (initialFlags == null || (long)width * height != initialFlags.LongLength)
                throw new ArgumentException("Cell flags must match the source grid dimensions.", nameof(initialFlags));
            Width = width;
            Height = height;
            flags = (uint[])initialFlags.Clone();
            owners = new object[flags.Length];
        }

        private int Index(int x, int y)
        {
            if (x < 0 || x >= Width || y < 0 || y >= Height)
                throw new ArgumentOutOfRangeException(nameof(x));
            return y * Width + x;
        }

        public uint GetFlags(int x, int y) => flags[Index(x, y)];
        public object GetOccupant(int x, int y) => owners[Index(x, y)];

        /// <summary>Source499800 writes only an empty cell; an occupied cell is unchanged.</summary>
        public bool TryClaim(int x, int y, object owner)
        {
            if (owner == null) throw new ArgumentNullException(nameof(owner));
            int index = Index(x, y);
            if (owners[index] != null) return false;
            owners[index] = owner;
            return true;
        }

        /// <summary>Source499860 clears only its current owner, by reference identity.</summary>
        public bool Release(int x, int y, object owner)
        {
            if (owner == null) throw new ArgumentNullException(nameof(owner));
            int index = Index(x, y);
            if (!ReferenceEquals(owners[index], owner)) return false;
            owners[index] = null;
            return true;
        }

        private static bool PassesFlags(uint value, byte restriction)
        {
            uint lower = value & 15;
            uint upper = value >> 4 & 15;
            return lower < 8 && upper != 4 && upper != 5 && upper != 6 &&
                   (restriction == 0 || upper != 3);
        }

        /// <summary>Bounded source4999e0 flag query; ignores an occupant.</summary>
        public bool IsTerrainPassable(int x, int y, byte restriction)
        {
            return PassesFlags(flags[Index(x, y)], restriction);
        }

        /// <summary>Bounded source499a40 flag query plus the source single-owner slot.</summary>
        public bool CanEnter(int x, int y, byte restriction)
        {
            int index = Index(x, y);
            return PassesFlags(flags[index], restriction) && owners[index] == null;
        }
    }
}
