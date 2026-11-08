using System;
using System.Globalization;
using AncientConquest.World;

public static class MissionReefSeedProbe
{
    private static byte[] Payload(uint tag, uint mode, int length)
    {
        byte[] data = new byte[length];
        foreach (int offset in new[] { 0, 16 })
        {
            uint value = offset == 0 ? tag : mode;
            for (int i = 0; i < 4 && offset + i < length; i++)
                data[offset + i] = unchecked((byte)(value >> (i * 8)));
        }
        return data;
    }

    private static void Throws<T>(string name, Action action) where T : Exception
    {
        try { action(); }
        catch (T) { Console.WriteLine("CHECK\t" + name); return; }
        throw new Exception("Missing expected guard: " + name);
    }

    public static int Main()
    {
        Throws<ArgumentNullException>("null_seed", () => MissionReefSeed.TryRead(null, out _));
        if (MissionReefSeed.TryRead(new MissionObjectSeed("OBJ_00000001", Payload(400, 0, 16)), out _))
            throw new Exception("Another class must not decode as a reef.");
        Console.WriteLine("CHECK\tunsupported_class");
        foreach (int length in new[] { 16, 20, 28, 31, 33, 36 })
        {
            int current = length;
            Throws<ArgumentException>("length_" + current, () => MissionReefSeed.TryRead(
                new MissionObjectSeed("OBJ_00000001", Payload(601, 0, current)), out _));
        }
        foreach (uint mode in new uint[] { 1, 2, 0xffffffff })
        {
            uint current = mode;
            Throws<NotSupportedException>("mode_" + current, () => MissionReefSeed.TryRead(
                new MissionObjectSeed("OBJ_00000001", Payload(601, current, 32)), out _));
        }
        string line;
        while ((line = Console.ReadLine()) != null)
        {
            string[] input = line.Split('\t');
            if (input.Length != 2 || input[1].Length != 64) throw new Exception("Invalid reef probe input.");
            byte[] data = new byte[32];
            for (int i = 0; i < data.Length; i++)
                data[i] = byte.Parse(input[1].Substring(i * 2, 2), NumberStyles.AllowHexSpecifier, CultureInfo.InvariantCulture);
            var seed = new MissionObjectSeed(input[0], data);
            if (!MissionReefSeed.TryRead(seed, out MissionReefSeed reef)) throw new Exception("Expected a reef reference.");
            Console.WriteLine(string.Join("\t", "ROW", input[0], reef.InstanceId,
                reef.CellX, reef.CellY, reef.Variant, reef.ReferenceState,
                reef.ReferenceFrameIndex, reef.WorldPixelX, reef.WorldPixelY, reef.ReferenceResourceName));
        }
        return 0;
    }
}
