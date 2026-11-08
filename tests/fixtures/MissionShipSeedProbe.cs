using System;
using System.Globalization;
using AncientConquest.World;

internal static class MissionShipSeedProbe
{
    private static int guards;

    private static byte[] Hex(string text)
    {
        var data = new byte[text.Length / 2];
        for (int i = 0; i < data.Length; ++i)
            data[i] = byte.Parse(text.Substring(i * 2, 2), NumberStyles.AllowHexSpecifier, CultureInfo.InvariantCulture);
        return data;
    }

    private static void Put(byte[] data, int offset, uint value)
    {
        for (int i = 0; i < 4; ++i) data[offset + i] = unchecked((byte)(value >> (i * 8)));
    }

    private static byte[] Data(int length, uint tag = 200, uint mode = 0)
    {
        var data = new byte[length];
        Put(data, 0, tag);
        if (length >= 20) Put(data, 16, mode);
        return data;
    }

    private static void Reject<T>(Action operation) where T : Exception
    {
        try { operation(); }
        catch (T) { ++guards; return; }
        throw new InvalidOperationException("Expected ship adapter rejection was not observed.");
    }

    private static void CheckContracts()
    {
        Reject<ArgumentNullException>(() => MissionShipSeed.TryRead(null, out _));
        foreach (int length in new[] { 16, 615, 617 })
        {
            var seed = new MissionObjectSeed("OBJ_00000001", Data(length));
            Reject<ArgumentException>(() => MissionShipSeed.TryRead(seed, out _));
        }
        foreach (uint mode in new[] { 1U, 2U, uint.MaxValue })
        {
            var seed = new MissionObjectSeed("OBJ_00000001", Data(616, 200, mode));
            Reject<NotSupportedException>(() => MissionShipSeed.TryRead(seed, out _));
        }
        var valid = new MissionObjectSeed("OBJ_00000001", Data(616));
        if (!MissionShipSeed.TryRead(valid, out MissionShipSeed result))
            throw new InvalidOperationException("Valid ship recipe rejected.");
        var other = new MissionObjectSeed("OBJ_00000002", Data(16, 601));
        if (MissionShipSeed.TryRead(other, out result) || result.InstanceId != 0)
            throw new InvalidOperationException("An unrelated class retained a ship recipe.");
        ++guards;
        var otherMode = new MissionObjectSeed("OBJ_00000002", Data(616, 400, 2));
        if (MissionShipSeed.TryRead(otherMode, out _))
            throw new InvalidOperationException("An unrelated saved class became a ship.");
        ++guards;
    }

    private static void Main()
    {
        string line;
        while ((line = Console.ReadLine()) != null)
        {
            string[] fields = line.Split('\t');
            var seed = new MissionObjectSeed(fields[0], Hex(fields[1]));
            if (!MissionShipSeed.TryRead(seed, out MissionShipSeed ship))
                throw new InvalidOperationException("Expected source ship was rejected.");
            int width = int.Parse(fields[2], CultureInfo.InvariantCulture);
            int height = int.Parse(fields[3], CultureInfo.InvariantCulture);
            long[] values = { ship.InstanceId, ship.OwnerSide, ship.OwnerPlayer, ship.ModelValue,
                              ship.ModelVariant, ship.RuntimeClassTag, ship.CellX, ship.CellY,
                              ship.Heading, ship.ReferenceFrameIndex, ship.RequestedHealthPercent,
                              ship.SourceEquipmentA, ship.SourceEquipmentB, ship.SourceOrderCount,
                              ship.GetWorldPixelX(width), ship.GetWorldPixelY(height) };
            Console.WriteLine(string.Join("\t", Array.ConvertAll(values,
                value => value.ToString(CultureInfo.InvariantCulture))));
        }
        CheckContracts();
        Console.WriteLine("GUARDS\t" + guards);
    }
}
