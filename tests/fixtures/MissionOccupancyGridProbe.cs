using System;
using System.IO;
using AncientConquest.World;

public static class MissionOccupancyGridProbe
{
    private sealed class Owner
    {
        public readonly uint InstanceId;
        public Owner(uint instanceId) { InstanceId = instanceId; }
        public override bool Equals(object other) => other is Owner owner && owner.InstanceId == InstanceId;
        public override int GetHashCode() => InstanceId.GetHashCode();
    }
    private static readonly object[] Owners = { null, new Owner(0), new Owner(0), new Owner(0xffffffff) };
    private static int Token(object owner)
    {
        for (int i = 0; i < Owners.Length; i++) if (ReferenceEquals(owner, Owners[i])) return i;
        throw new Exception("Unknown owner reference.");
    }
    private static void Require(bool value, string name)
    {
        if (!value) throw new Exception(name);
    }
    private static void Throws<T>(string name, Action action) where T : Exception
    {
        try { action(); }
        catch (T) { Console.WriteLine("CHECK\t" + name); return; }
        throw new Exception("Missing expected guard: " + name);
    }
    public static int Main(string[] args)
    {
        byte[] raw = File.ReadAllBytes(args[0]);
        Require(raw.Length == 2304, "Unexpected source flags fixture length.");
        uint[] flags = new uint[raw.Length / 4];
        for (int i = 0; i < flags.Length; i++)
            flags[i] = (uint)raw[i * 4] | (uint)raw[i * 4 + 1] << 8 |
                       (uint)raw[i * 4 + 2] << 16 | (uint)raw[i * 4 + 3] << 24;
        var source = new MissionOccupancyGrid(24, 24, flags);
        Require(source.Width == 24 && source.Height == 24, "Grid geometry.");
        Console.WriteLine("CHECK\tgeometry");
        for (int y = 0; y < 24; y++)
            for (int x = 0; x < 24; x++)
            {
                Require(source.GetOccupant(x, y) == null, "Source flags must start without occupants.");
                Console.WriteLine("FLAG\t" + x + "\t" + y + "\t" + source.GetFlags(x, y));
            }
        uint first = flags[0]; flags[0] ^= 0xffffffff;
        Require(source.GetFlags(0, 0) == first, "Grid must clone flags input.");
        Console.WriteLine("CHECK\tflags_clone");
        foreach (int size in new[] { -1, 0, 32768, int.MinValue, int.MaxValue })
        {
            int current = size;
            Throws<ArgumentOutOfRangeException>("width_" + current, () => new MissionOccupancyGrid(current, 1, new uint[1]));
            Throws<ArgumentOutOfRangeException>("height_" + current, () => new MissionOccupancyGrid(1, current, new uint[1]));
        }
        Throws<ArgumentException>("flags_null", () => new MissionOccupancyGrid(24, 24, null));
        foreach (int count in new[] { 0, 575, 577 })
        {
            int current = count;
            Throws<ArgumentException>("flags_length_" + current, () => new MissionOccupancyGrid(24, 24, new uint[current]));
        }
        int[,] positions = { { -1, 0 }, { 24, 0 }, { 0, -1 }, { 0, 24 },
                             { int.MinValue, 0 }, { int.MaxValue, 0 }, { 0, int.MinValue }, { 0, int.MaxValue } };
        for (int index = 0; index < positions.GetLength(0); index++)
        {
            int x = positions[index, 0], y = positions[index, 1];
            Throws<ArgumentOutOfRangeException>("bounds_flags_" + index, () => source.GetFlags(x, y));
            Throws<ArgumentOutOfRangeException>("bounds_owner_" + index, () => source.GetOccupant(x, y));
            Throws<ArgumentOutOfRangeException>("bounds_claim_" + index, () => source.TryClaim(x, y, Owners[1]));
            Throws<ArgumentOutOfRangeException>("bounds_release_" + index, () => source.Release(x, y, Owners[1]));
            Throws<ArgumentOutOfRangeException>("bounds_terrain_" + index, () => source.IsTerrainPassable(x, y, 0));
            Throws<ArgumentOutOfRangeException>("bounds_enter_" + index, () => source.CanEnter(x, y, 0));
        }
        Throws<ArgumentNullException>("claim_null", () => source.TryClaim(0, 0, null));
        Throws<ArgumentNullException>("release_null", () => source.Release(0, 0, null));
        Require(Owners[1].Equals(Owners[2]) && !ReferenceEquals(Owners[1], Owners[2]), "Equality control.");
        Require(source.TryClaim(0, 0, Owners[1]) && !source.Release(0, 0, Owners[2]) &&
                ReferenceEquals(source.GetOccupant(0, 0), Owners[1]) && source.Release(0, 0, Owners[1]), "Reference owner identity.");
        Console.WriteLine("CHECK\treference_identity");
        var spatial = new MissionOccupancyGrid(24, 24, new uint[576]);
        Require(spatial.TryClaim(7, 12, Owners[1]) &&
                ReferenceEquals(spatial.GetOccupant(7, 12), Owners[1]) &&
                spatial.GetOccupant(0, 0) == null && spatial.GetOccupant(7, 11) == null &&
                !spatial.Release(7, 11, Owners[1]) &&
                ReferenceEquals(spatial.GetOccupant(7, 12), Owners[1]) &&
                spatial.Release(7, 12, Owners[1]), "Distinct cells retain independent ownership.");
        Console.WriteLine("CHECK\tspatial_identity");
        string line;
        while ((line = Console.ReadLine()) != null)
        {
            string[] fields = line.Split('\t');
            if (fields[0] == "Q" && fields.Length == 4)
            {
                uint flag = uint.Parse(fields[1]); byte restriction = byte.Parse(fields[2]); int owner = int.Parse(fields[3]);
                var grid = new MissionOccupancyGrid(1, 1, new[] { flag });
                if (owner != 0) grid.TryClaim(0, 0, Owners[owner]);
                Console.WriteLine("QUERY\t" + (grid.IsTerrainPassable(0, 0, restriction) ? 1 : 0) + "\t" +
                                  (grid.CanEnter(0, 0, restriction) ? 1 : 0));
            }
            else if (fields[0] == "C" && fields.Length == 4)
            {
                int before = int.Parse(fields[1]), claimant = int.Parse(fields[2]), release = int.Parse(fields[3]);
                var grid = new MissionOccupancyGrid(1, 1, new uint[1]);
                if (before != 0) grid.TryClaim(0, 0, Owners[before]);
                grid.TryClaim(0, 0, Owners[claimant]); int after = Token(grid.GetOccupant(0, 0));
                grid.Release(0, 0, Owners[release]);
                Console.WriteLine("OWNER\t" + after + "\t" + Token(grid.GetOccupant(0, 0)));
            }
            else throw new Exception("Invalid occupancy probe input.");
        }
        return 0;
    }
}
