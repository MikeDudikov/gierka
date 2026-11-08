using System;
using System.IO;
using AncientConquest.World;

public static class TerrainMapDataProbe
{
    private static void Check(string name, bool condition)
    {
        if (!condition) throw new Exception("Map-data contract failed: " + name);
        Console.WriteLine("CHECK\t" + name);
    }

    private static bool Throws<T>(Action action) where T : Exception
    {
        try { action(); }
        catch (T) { return true; }
        return false;
    }

    private static void GuardChecks(TerrainMapData map)
    {
        Check("geometry_properties", map.WidthCells == 24 && map.HeightCells == 24 &&
              map.TileWidth == 64 && map.TileHeight == 64);
        Check("layer_count", TerrainMapData.LayerCount == 8);
        int[] invalid = { 0, -1, 32768, int.MaxValue };
        for (int axis = 0; axis < 4; axis++)
        {
            for (int value = 0; value < invalid.Length; value++)
            {
                int[] dimensions = { 1, 1, 64, 64 };
                dimensions[axis] = invalid[value];
                Check("ctor_dimension_" + axis + "_" + value,
                    Throws<ArgumentOutOfRangeException>(() => new TerrainMapData(
                        dimensions[0], dimensions[1], dimensions[2], dimensions[3], new byte[16])));
            }
        }
        Check("ctor_length_null", Throws<ArgumentException>(() => new TerrainMapData(1, 1, 64, 64, null)));
        Check("ctor_length_empty", Throws<ArgumentException>(() => new TerrainMapData(1, 1, 64, 64, new byte[0])));
        Check("ctor_length_short", Throws<ArgumentException>(() => new TerrainMapData(1, 1, 64, 64, new byte[15])));
        Check("ctor_length_long", Throws<ArgumentException>(() => new TerrainMapData(1, 1, 64, 64, new byte[17])));
        Check("ctor_large_length", Throws<ArgumentException>(() => new TerrainMapData(32767, 32767, 64, 64, new byte[16])));

        byte[] input = new byte[16];
        input[0] = 0x02;
        input[1] = 0x34;
        TerrainMapData retained = new TerrainMapData(1, 1, 64, 64, input);
        for (int index = 0; index < input.Length; index++) input[index] = 0xff;
        TerrainTileReference preserved;
        Check("input_immutability", retained.GetWord(0, 0, 0) == 0x3402 &&
            retained.TryGetReference(0, 0, 0, out preserved) && preserved.Word == 0x3402);

        string[] boundsNames = { "x_negative", "x_end", "y_negative", "y_end", "layer_negative", "layer_end",
                                 "x_min", "x_max", "y_min", "y_max", "layer_min", "layer_max" };
        int[,] bounds = { { -1, 0, 0 }, { 24, 0, 0 }, { 0, -1, 0 }, { 0, 24, 0 }, { 0, 0, -1 }, { 0, 0, 8 },
                         { int.MinValue, 0, 0 }, { int.MaxValue, 0, 0 }, { 0, int.MinValue, 0 },
                         { 0, int.MaxValue, 0 }, { 0, 0, int.MinValue }, { 0, 0, int.MaxValue } };
        for (int index = 0; index < boundsNames.Length; index++)
        {
            int x = bounds[index, 0], y = bounds[index, 1], layer = bounds[index, 2];
            TerrainTileReference unused;
            Check("bounds_" + boundsNames[index], !map.TryGetReference(x, y, layer, out unused) &&
                Throws<ArgumentOutOfRangeException>(() => map.GetWord(x, y, layer)));
        }

        // These are API boundary vectors; no claim is made that every high-ID
        // reference resolves to a bitmap in the original game's libraries.
        ushort[] words = { 0x3400, 0x8001, 0xffff, 0x0001, 0xff00, 0x7f7f, 0x01ff, 0xab80 };
        byte[] selectors = { 0, 1, 255, 1, 0, 127, 255, 128 };
        byte[] libraries = { 52, 128, 255, 0, 255, 127, 1, 171 };
        int[] frames = { -1, 0, 254, 0, -1, 126, 254, 127 };
        bool[] presence = { false, true, true, true, false, true, true, true };
        byte[] synthetic = new byte[16];
        for (int index = 0; index < words.Length; index++)
        {
            synthetic[index * 2] = unchecked((byte)words[index]);
            synthetic[index * 2 + 1] = (byte)(words[index] >> 8);
        }
        TerrainMapData byteCases = new TerrainMapData(1, 1, 64, 64, synthetic);
        for (int layer = 0; layer < words.Length; layer++)
        {
            TerrainTileReference reference;
            bool present = byteCases.TryGetReference(0, 0, layer, out reference);
            Check("selector_bytes_" + layer, present == presence[layer] &&
                byteCases.GetWord(0, 0, layer) == words[layer] && reference.Word == words[layer] &&
                reference.Selector == selectors[layer] && reference.LibraryId == libraries[layer] &&
                reference.FrameIndex == frames[layer]);
        }
    }

    public static int Main(string[] arguments)
    {
        if (arguments.Length != 1) throw new ArgumentException("Expected the checked planar map path.");
        TerrainMapData map = new TerrainMapData(24, 24, 64, 64, File.ReadAllBytes(arguments[0]));
        GuardChecks(map);
        for (int x = 0; x < map.WidthCells; x++)
        {
            for (int y = 0; y < map.HeightCells; y++)
            {
                for (int layer = 0; layer < TerrainMapData.LayerCount; layer++)
                {
                    TerrainTileReference reference;
                    bool present = map.TryGetReference(x, y, layer, out reference);
                    ushort word = map.GetWord(x, y, layer);
                    if (reference.Word != word) throw new Exception("GetWord and reference.Word differ.");
                    Console.WriteLine("ROW\t" + x + "\t" + y + "\t" + layer + "\t" + word + "\t" +
                        reference.FrameIndex + "\t" + (present ? 1 : 0) + "\t" + reference.LibraryId + "\t" + reference.Selector);
                }
            }
        }
        return 0;
    }
}
