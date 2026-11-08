using System;
using System.Globalization;
using AncientConquest.World;

internal static class MissionObjectSelectionProbe
{
    private static int guards;

    private static byte[] FromHex(string text)
    {
        var result = new byte[text.Length / 2];
        for (int i = 0; i < result.Length; ++i)
            result[i] = byte.Parse(text.Substring(i * 2, 2), NumberStyles.AllowHexSpecifier,
                                   CultureInfo.InvariantCulture);
        return result;
    }

    private static void Check(bool condition)
    {
        if (!condition) throw new InvalidOperationException("Mission object contract check failed.");
        ++guards;
    }

    private static void Reject(Action operation)
    {
        try { operation(); }
        catch (ArgumentException) { ++guards; return; }
        throw new InvalidOperationException("Invalid mission-object input was accepted.");
    }

    private static byte[] Payload(uint tag, uint kind, uint side, uint player)
    {
        var data = new byte[16];
        uint[] words = { tag, kind, side, player };
        for (int i = 0; i < words.Length; ++i)
            for (int j = 0; j < 4; ++j)
                data[i * 4 + j] = unchecked((byte)(words[i] >> (j * 8)));
        return data;
    }

    private static void CheckContracts()
    {
        byte[] data = Payload(0x78563412, 0x80000000, 0xffffffff, 0x04030201);
        var seed = new MissionObjectSeed("OBJ_FFFFFFFF", data);
        Check(seed.ResourceName == "OBJ_FFFFFFFF" && seed.InstanceId == uint.MaxValue);
        Check(seed.ByteLength == 16 && seed.ClassTag == 0x78563412 && seed.Kind == 0x80000000);
        Check(seed.SideIndex == uint.MaxValue && seed.PlayerIndex == 0x04030201);
        Check(seed.ReadInt32(4) == int.MinValue && seed.ReadInt32(8) == -1);
        Check(seed.ReadUInt32(1) == 0x00785634 && seed.ReadUInt32(12) == 0x04030201);
        Check(seed.ReadByte(0) == 0x12 && seed.ReadByte(15) == 4);
        data[0] = 0;
        data[15] = 0;
        Check(seed.ClassTag == 0x78563412 && seed.ReadByte(15) == 4);
        foreach (int offset in new[] { -1, 13, 16, int.MaxValue })
            Reject(() => seed.ReadUInt32(offset));
        foreach (int offset in new[] { -1, 16, int.MaxValue })
            Reject(() => seed.ReadByte(offset));
        foreach (string name in new[] { null, "", "OBJ_0000000", "OBJ_000000001",
                                        "obj_00000001", "OBJ_0000000G", "OBJ_ 0000001", "OBJ_-0000001" })
            Reject(() => new MissionObjectSeed(name, new byte[16]));
        Reject(() => new MissionObjectSeed("OBJ_00000001", null));
        Reject(() => new MissionObjectSeed("OBJ_00000001", new byte[15]));
        var valid = new MissionObjectSeed("OBJ_00000001", Payload(401, 1, 4, 3));
        Reject(() => MissionObjectSelection.TrySelect(null, new byte[20], out _));
        Reject(() => MissionObjectSelection.TrySelect(valid, null, out _));
        foreach (int length in new[] { 0, 19, 21 })
            Reject(() => MissionObjectSelection.TrySelect(valid, new byte[length], out _));
        foreach (uint side in new[] { 5U, uint.MaxValue })
        {
            var invalid = new MissionObjectSeed("OBJ_00000001", Payload(401, 1, side, 0));
            Reject(() => MissionObjectSelection.TrySelect(invalid, new byte[20], out _));
        }
        foreach (uint player in new[] { 4U, uint.MaxValue })
        {
            var invalid = new MissionObjectSeed("OBJ_00000001", Payload(401, 1, 0, player));
            Reject(() => MissionObjectSelection.TrySelect(invalid, new byte[20], out _));
        }
        Check(!MissionObjectSelection.TrySelect(valid, new byte[20], out int emptyFactory) && emptyFactory == 0);
        var players = new byte[20]; players[19] = 255;
        Check(MissionObjectSelection.TrySelect(valid, players, out int selectedFactory) && selectedFactory == 5756);
        Check(players[19] == 255);
    }

    private static void Main()
    {
        string line;
        while ((line = Console.ReadLine()) != null)
        {
            string[] fields = line.Split('\t');
            var seed = new MissionObjectSeed(fields[0], FromHex(fields[1]));
            bool selected = MissionObjectSelection.TrySelect(seed, FromHex(fields[2]), out int factory);
            Console.WriteLine((selected ? 1 : 0) + "\t" + factory + "\t" +
                              seed.InstanceId.ToString(CultureInfo.InvariantCulture));
        }
        CheckContracts();
        Console.WriteLine("GUARDS\t" + guards);
    }
}
