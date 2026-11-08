using System;
using System.Globalization;
using System.IO;
using AncientConquest.World;
using AncientConquest.Simulation;

internal static class ShipAdjacentQueryProbe
{
    private sealed class Owner
    {
        public readonly int Token;
        public Owner(int token) { Token = token; }
        // Deliberately equal values with distinct identities.
        public override bool Equals(object other) => other is Owner;
        public override int GetHashCode() => 11;
    }

    private static readonly Owner[] Owners = MakeOwners();
    private static Owner[] MakeOwners()
    {
        var values = new Owner[13];
        for (int index = 1; index < values.Length; ++index) values[index] = new Owner(index);
        return values;
    }
    private static int Int(string value) => int.Parse(value, CultureInfo.InvariantCulture);
    private static uint UInt(string value) => uint.Parse(value, CultureInfo.InvariantCulture);
    private static byte Byte(string value) => byte.Parse(value, CultureInfo.InvariantCulture);
    private static void Require(bool condition, string message) { if (!condition) throw new Exception(message); }
    private static void Check(string name) => Console.WriteLine("CHECK\t" + name);
    private static void Reject<T>(string name, Action action) where T : Exception
    {
        try { action(); }
        catch (T) { Check(name); return; }
        throw new Exception("Missing adjacent-query guard: " + name);
    }
    private static uint[] Flags()
    {
        var flags = new uint[576]; for (int index = 0; index < flags.Length; ++index) flags[index] = 1;
        return flags;
    }
    private static void Pairs(string text, Action<int, uint> use)
    {
        if (text == "-") return;
        foreach (string pair in text.Split(';'))
        {
            string[] values = pair.Split(':'); use(Int(values[0]), UInt(values[1]));
        }
    }
    private static ShipNavigationOccupant Unexpected(object owner) => throw new Exception("Resolver ran before its source gate.");

    private static void Contracts()
    {
        var grid = new MissionOccupancyGrid(24, 24, Flags());
        object self = Owners[1];
        Reject<ArgumentNullException>("null_grid", () => ShipAdjacentQuery.CanEnter(null, self, 1, 1, 0, 0, Unexpected));
        Reject<ArgumentNullException>("null_requester", () => ShipAdjacentQuery.CanEnter(grid, null, 1, 1, 0, 0, Unexpected));
        Reject<ArgumentNullException>("null_resolver", () => ShipAdjacentQuery.CanEnter(grid, self, 1, 1, 0, 0, null));
        foreach (byte heading in new byte[] { 8, 127, 128, 255 })
            Reject<ArgumentOutOfRangeException>("heading_" + heading,
                () => ShipAdjacentQuery.CanEnter(grid, self, 1, 1, heading, 0, Unexpected));
        int[,] positions = { { -1, 0 }, { 24, 0 }, { 0, -1 }, { 0, 24 },
                             { int.MinValue, 0 }, { int.MaxValue, 0 }, { 0, int.MinValue }, { 0, int.MaxValue } };
        for (int index = 0; index < positions.GetLength(0); ++index)
        {
            int x = positions[index, 0], y = positions[index, 1];
            Reject<ArgumentOutOfRangeException>("bounds_" + index,
                () => ShipAdjacentQuery.CanEnter(grid, self, x, y, 1, 0, Unexpected));
        }
        var view = new ShipNavigationOccupant(uint.MaxValue, 255, true, 0x80000000u, int.MinValue, int.MaxValue);
        Require(view.RuntimeClassTag == uint.MaxValue && view.MovementState == 255 && view.HasLink &&
                view.LinkRecordType == 0x80000000u && view.LinkedCellX == int.MinValue && view.LinkedCellY == int.MaxValue,
                "Occupant value projection changed fields.");
        Check("value_projection");
        uint[] blocked = Flags(); blocked[87] = 8;
        var terrain = new MissionOccupancyGrid(24, 24, blocked); terrain.TryClaim(16, 3, Owners[2]);
        Require(!ShipAdjacentQuery.CanEnter(terrain, self, 15, 3, 5, 0, Unexpected), "Terrain gate.");
        Check("terrain_resolver_gate");
        var occupied = new MissionOccupancyGrid(24, 24, Flags());
        occupied.TryClaim(15, 3, Owners[2]); occupied.TryClaim(16, 3, Owners[3]);
        Require(!ShipAdjacentQuery.CanEnter(occupied, self, 15, 3, 5, 0, Unexpected), "Foreign target gate.");
        Check("target_resolver_gate");
        foreach (byte heading in new byte[] { 0, 2, 4, 6 })
            Require(ShipAdjacentQuery.CanEnter(grid, self, 15, 3, heading, 0, Unexpected), "Cardinal gate.");
        Check("cardinal_resolver_gate");
        int[,] border = { { 0, 1, 1 }, { 1, 23, 3 }, { 1, 0, 5 }, { 0, 1, 7 } };
        for (int index = 0; index < border.GetLength(0); ++index)
            Require(ShipAdjacentQuery.CanEnter(grid, self, border[index, 0], border[index, 1],
                    unchecked((byte)border[index, 2]), 0, Unexpected), "Boundary gate.");
        Check("boundary_resolver_gate");
        var secondOnly = new MissionOccupancyGrid(24, 24, Flags()); secondOnly.TryClaim(15, 2, Owners[2]);
        Require(ShipAdjacentQuery.CanEnter(secondOnly, self, 15, 3, 5, 0, Unexpected), "Empty cornerA gate.");
        Check("empty_corner_resolver_gate");
        var corners = new MissionOccupancyGrid(24, 24, Flags());
        corners.TryClaim(16, 3, Owners[2]); corners.TryClaim(15, 2, Owners[3]);
        int calls = 0;
        bool allowed = ShipAdjacentQuery.CanEnter(corners, self, 15, 3, 5, 0, value =>
        {
            Require(ReferenceEquals(value, Owners[2]), "Resolver read a different corner."); ++calls;
            return new ShipNavigationOccupant(999, 0);
        });
        Require(allowed && calls == 1 && Owners[2].Equals(Owners[3]), "Resolver identity/count.");
        Check("only_first_corner_resolved");
    }

    private static void Main(string[] args)
    {
        byte[] raw = File.ReadAllBytes(args[0]); Require(raw.Length == 2304, "Source flag fixture length.");
        uint[] source = new uint[576];
        for (int index = 0; index < source.Length; ++index)
            source[index] = (uint)raw[index * 4] | ((uint)raw[index * 4 + 1] << 8) |
                            ((uint)raw[index * 4 + 2] << 16) | ((uint)raw[index * 4 + 3] << 24);
        string line;
        while ((line = Console.ReadLine()) != null)
        {
            string[] fields = line.Split('\t');
            uint[] flags = fields[0] == "1" ? (uint[])source.Clone() : Flags();
            Pairs(fields[5], (index, value) => flags[index] = value);
            object[] expectedOwners = new object[576];
            int fill = Int(fields[1]);
            for (int index = 0; index < expectedOwners.Length; ++index) expectedOwners[index] = Owners[fill];
            Pairs(fields[6], (index, value) => expectedOwners[index] = Owners[value]);
            var grid = new MissionOccupancyGrid(24, 24, flags);
            for (int index = 0; index < expectedOwners.Length; ++index)
                if (expectedOwners[index] != null) Require(grid.TryClaim(index % 24, index / 24, expectedOwners[index]), "Probe owner initialization.");
            var descriptions = new ShipNavigationOccupant[Owners.Length];
            foreach (string descriptor in fields[7].Split(';'))
            {
                string[] values = descriptor.Split(':');
                descriptions[Int(values[0])] = new ShipNavigationOccupant(UInt(values[1]), Byte(values[2]),
                    values[3] == "1", UInt(values[4]), Int(values[5]), Int(values[6]));
            }
            int target = Int(fields[2]);
            bool result = ShipAdjacentQuery.CanEnter(grid, Owners[1], target % 24, target / 24,
                Byte(fields[3]), Byte(fields[4]), value => descriptions[((Owner)value).Token]);
            for (int index = 0; index < flags.Length; ++index)
                Require(grid.GetFlags(index % 24, index / 24) == flags[index] &&
                        ReferenceEquals(grid.GetOccupant(index % 24, index / 24), expectedOwners[index]), "Query mutated its input grid.");
            Console.WriteLine("RESULT\t" + (result ? 1 : 0));
        }
        Check("all_case_grids_unchanged");
        Contracts();
    }
}
