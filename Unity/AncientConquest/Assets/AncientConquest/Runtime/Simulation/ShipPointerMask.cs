using System;

namespace AncientConquest.Simulation
{
    /// <summary>
    /// Ship virtual hit predicate4e06c0 with the separate source type18 masks.
    /// This is not a world picker, ownership filter or rendered-alpha test.
    /// </summary>
    public sealed class ShipPointerMask
    {
        private readonly byte[][] planes;
        private readonly int rowBits;
        public int Width { get; }
        public int Height { get; }

        public ShipPointerMask(int width, int height, byte[][] sourcePlanes)
        {
            if (width < 1 || width > 2048) throw new ArgumentOutOfRangeException(nameof(width));
            if (height < 1 || height > 2048) throw new ArgumentOutOfRangeException(nameof(height));
            if (sourcePlanes == null) throw new ArgumentNullException(nameof(sourcePlanes));
            if (sourcePlanes.Length != 24) throw new ArgumentException("Exactly24 source masks are required.", nameof(sourcePlanes));
            Width = width; Height = height; rowBits = (width + 7) & ~7;
            int length = rowBits / 8 * height;
            planes = new byte[24][];
            for (int index = 0; index < planes.Length; index++)
            {
                if (sourcePlanes[index] == null || sourcePlanes[index].Length != length)
                    throw new ArgumentException("A source mask has an invalid padded plane length.", nameof(sourcePlanes));
                planes[index] = (byte[])sourcePlanes[index].Clone();
            }
        }

        public static int SelectMaskIndex(int storedFrame, sbyte heading)
        {
            if (storedFrame >= 32 && storedFrame <= 55) return storedFrame - 32;
            if (heading < 0 || heading > 7)
                throw new NotSupportedException("Only normal ship headings0..7 are supported.");
            return heading * 3;
        }

        public bool Contains(int worldX, int worldY, int publishedSpriteX, int publishedSpriteY,
                             int storedFrame, sbyte heading, bool precise)
        {
            // The native coarse branch returns before sprite geometry/masks.
            if (!precise) return true;
            int x = unchecked(worldX - publishedSpriteX);
            int y = unchecked(worldY - publishedSpriteY);
            if (x < 0 || x >= Width || y < 0 || y >= Height) return false;
            int index = SelectMaskIndex(storedFrame, heading);
            int bit = rowBits * y + x;
            return (planes[index][bit >> 3] & (0x80 >> (bit & 7))) != 0;
        }
    }
}
