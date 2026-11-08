using System;

namespace AncientConquest.World
{
    public readonly struct TerrainTileReference
    {
        public ushort Word { get; }
        public byte Selector => (byte)(Word & 255);
        public byte LibraryId => (byte)(Word >> 8);
        public int FrameIndex => Selector - 1;

        internal TerrainTileReference(ushort word) { Word = word; }
    }

    /// <summary>The source type17 map: eight planar little-endian uint16 layers.</summary>
    public sealed class TerrainMapData
    {
        public const int LayerCount = 8;
        private readonly byte[] data;
        public int WidthCells { get; }
        public int HeightCells { get; }
        public int TileWidth { get; }
        public int TileHeight { get; }

        public TerrainMapData(int widthCells, int heightCells, int tileWidth, int tileHeight,
                              byte[] planarPayload)
        {
            if (widthCells <= 0 || widthCells > short.MaxValue ||
                heightCells <= 0 || heightCells > short.MaxValue ||
                tileWidth <= 0 || tileWidth > short.MaxValue ||
                tileHeight <= 0 || tileHeight > short.MaxValue)
                throw new ArgumentOutOfRangeException(nameof(widthCells));
            long expected = (long)widthCells * heightCells * LayerCount * 2;
            if (planarPayload == null || planarPayload.LongLength != expected)
                throw new ArgumentException("Map payload does not match eight planar layers.", nameof(planarPayload));
            WidthCells = widthCells;
            HeightCells = heightCells;
            TileWidth = tileWidth;
            TileHeight = tileHeight;
            data = (byte[])planarPayload.Clone();
        }

        private bool InBounds(int x, int y, int layer)
        {
            return x >= 0 && x < WidthCells && y >= 0 && y < HeightCells &&
                   layer >= 0 && layer < LayerCount;
        }

        public ushort GetWord(int x, int y, int layer)
        {
            if (!InBounds(x, y, layer)) throw new ArgumentOutOfRangeException(nameof(x));
            int offset = 2 * ((layer * HeightCells + y) * WidthCells + x);
            return (ushort)(data[offset] | data[offset + 1] << 8);
        }

        /// <summary>Decodes a reference; resolving its library/bitmap is a separate operation.</summary>
        public bool TryGetReference(int x, int y, int layer, out TerrainTileReference tile)
        {
            tile = default;
            if (!InBounds(x, y, layer)) return false;
            tile = new TerrainTileReference(GetWord(x, y, layer));
            return tile.Selector != 0;
        }
    }
}
