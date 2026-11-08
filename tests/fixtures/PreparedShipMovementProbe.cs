using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using AncientConquest.World;
using AncientConquest.Simulation;

internal static class PreparedShipMovementProbe
{
    private sealed class Owner
    {
        public readonly uint Id;
        public Owner(uint id) { Id = id; }
        public override bool Equals(object other) => other is Owner owner && owner.Id == Id;
        public override int GetHashCode() => Id.GetHashCode();
    }
    private static readonly int[,] Cells = { {16,2}, {21,5}, {19,4}, {11,18}, {9,21}, {10,22}, {6,13}, {6,14} };
    private static uint[] flags;
    private static byte[] sourceRaw;
    private static MissionShipSeed sourceSeed;
    private static int guardCount;
    private static byte[] Hex(string text)
    {
        var result = new byte[text.Length / 2];
        for (int i = 0; i < result.Length; i++)
            result[i] = byte.Parse(text.Substring(i * 2, 2), NumberStyles.AllowHexSpecifier, CultureInfo.InvariantCulture);
        return result;
    }
    private static void Put(byte[] data, int offset, uint value)
    {
        for (int i = 0; i < 4; i++) data[offset + i] = unchecked((byte)(value >> (i * 8)));
    }
    private static MissionShipSeed Seed(byte[] raw, string name = "OBJ_0000000b")
    {
        if (!MissionShipSeed.TryRead(new MissionObjectSeed(name, raw), out MissionShipSeed seed)) throw new Exception("ship class");
        return seed;
    }
    private static MissionOccupancyGrid Grid(out object[] owners)
    {
        var grid = new MissionOccupancyGrid(24, 24, flags);
        owners = new object[8];
        for (int i = 0; i < owners.Length; i++)
        {
            // Equal-valued ID0 identities must remain eight different owners.
            owners[i] = new Owner(0);
            if (!grid.TryClaim(Cells[i,0], Cells[i,1], owners[i])) throw new Exception("fleet claim");
        }
        return grid;
    }
    private static void Require(bool value, string label)
    {
        if (!value) throw new Exception(label);
        Console.WriteLine("CHECK\t" + label); guardCount++;
    }
    private static void Reject<T>(string label, Action action) where T : Exception
    {
        try { action(); }
        catch (T) { Console.WriteLine("CHECK\t" + label); guardCount++; return; }
        throw new Exception("Missing guard " + label);
    }
    private static void Emit(string label, int tick, PreparedShipMovement motion,
                             MissionOccupancyGrid grid, object owner, int frame, bool tail,
                             int publishedFrame, int publishedX, int publishedY)
    {
        var s = motion.Current; var owned = new List<int>(); int occupied = 0;
        for (int y = 0; y < 24; y++)
            for (int x = 0; x < 24; x++)
            {
                object actual = grid.GetOccupant(x, y);
                if (actual != null) occupied++;
                if (ReferenceEquals(actual, owner)) owned.Add(y * 24 + x);
            }
        Console.WriteLine(string.Join("\t", "ROW", label, tick,
            s.CellX, s.CellY, s.WorldPixelX, s.WorldPixelY, s.State, s.CenterGate ? 1 : 0,
            s.Heading, s.Speed, s.Remainder, s.Deceleration, s.ReservedCellIndex,
            s.NextCellIndex, s.PathIndex, s.PathCount, frame, tail ? 1 : 0,
            occupied, string.Join(",", owned), motion.LastStepPublishesPose ? 1 : 0,
            publishedFrame, publishedX, publishedY));
    }
    private static void Guards()
    {
        var grid = Grid(out object[] owners);
        Reject<ArgumentNullException>("null_grid", () => new PreparedShipMovement(null, owners[0], sourceSeed));
        Reject<ArgumentNullException>("null_owner", () => new PreparedShipMovement(grid, null, sourceSeed));
        Reject<ArgumentException>("wrong_identity", () => new PreparedShipMovement(grid, new Owner(0), sourceSeed));
        Reject<NotSupportedException>("wrong_geometry", () => new PreparedShipMovement(new MissionOccupancyGrid(1,1,new uint[1]), owners[0], sourceSeed));
        foreach (int field in new[] { 20, 24, 28, 36, 40, 44, 48, 56, 60, 512 })
        {
            int offset = field; byte[] raw = (byte[])sourceRaw.Clone();
            Put(raw, offset, unchecked((uint)(BitConverter.ToInt32(raw, offset) + 1)));
            Reject<NotSupportedException>("seed_field_" + offset, () => new PreparedShipMovement(grid, owners[0], Seed(raw)));
        }
        Reject<NotSupportedException>("other_instance", () => new PreparedShipMovement(grid, owners[0], Seed(sourceRaw,"OBJ_00000000")));
        foreach (int index in new[] { 64, 87, 63, 88 })
        {
            uint[] altered = (uint[])flags.Clone(); altered[index] ^= 1u;
            var other = new MissionOccupancyGrid(24,24,altered);
            Reject<NotSupportedException>("local_flag_" + index, () => new PreparedShipMovement(other, owners[0], sourceSeed));
        }
        grid.Release(21,5,owners[1]);
        Reject<NotSupportedException>("missing_fleet_owner", () => new PreparedShipMovement(grid, owners[0], sourceSeed));
        grid.TryClaim(21,5,owners[0]);
        Reject<NotSupportedException>("duplicate_fleet_identity", () => new PreparedShipMovement(grid, owners[0], sourceSeed));
        grid.Release(21,5,owners[0]); grid.TryClaim(21,5,owners[1]); grid.TryClaim(0,0,new Owner(0));
        Reject<NotSupportedException>("extra_occupant", () => new PreparedShipMovement(grid, owners[0], sourceSeed));
        grid = Grid(out owners); var motion = new PreparedShipMovement(grid, owners[0], sourceSeed);
        Reject<InvalidOperationException>("step_before_begin", () => motion.Step(1,1));
        foreach (int pending in new[] { int.MinValue, -1, 0, 4, 5, 6, 8, int.MaxValue })
        {
            int value = pending;
            Reject<ArgumentOutOfRangeException>("pending_" + value, () => motion.Step(value,1));
        }
        object foreign = new Owner(0); grid.TryClaim(15,3,foreign);
        Require(!motion.TryBeginAdjacentReferenceMove() && !grid.Release(15,3,owners[0]) &&
                ReferenceEquals(grid.GetOccupant(15,3),foreign), "blocked_begin_preserves_foreign_owner");
        grid.Release(15,3,foreign); Require(motion.TryBeginAdjacentReferenceMove(), "blocked_then_clear_begin");
        Reject<InvalidOperationException>("begin_twice", () => motion.TryBeginAdjacentReferenceMove());
        motion.Step(1,1); grid.Release(15,3,owners[0]); grid.TryClaim(15,3,foreign);
        Reject<InvalidOperationException>("reserved_owner_changed", () => motion.Step(1,2));
        grid = Grid(out owners); motion = new PreparedShipMovement(grid, owners[0], sourceSeed);
        grid.TryClaim(16,3,foreign);
        Reject<NotSupportedException>("unsupported_diagonal_occupant", () => motion.TryBeginAdjacentReferenceMove());
        grid = Grid(out owners); motion = new PreparedShipMovement(grid, owners[0], sourceSeed);
        grid.Release(16,2,owners[0]); grid.TryClaim(16,2,foreign);
        Reject<InvalidOperationException>("origin_changed_before_begin", () => motion.TryBeginAdjacentReferenceMove());
        grid = Grid(out owners); motion = new PreparedShipMovement(grid, owners[0], sourceSeed);
        Require(motion.TryBeginAdjacentReferenceMove(),"equal_id0_distinct_fleet_accepted");
        for (uint tick = 1; tick <= 44; tick++) motion.Step(1,tick);
        var end = motion.Current;
        Require(end.IsComplete && motion.IsStopped && !motion.Step(1,45) && !motion.LastStepPublishesPose &&
                motion.Current.WorldPixelX == end.WorldPixelX && motion.Current.WorldPixelY == end.WorldPixelY &&
                ReferenceEquals(grid.GetOccupant(15,3),owners[0]) && grid.GetOccupant(16,2) == null,
                "stopped_reference_is_frozen");
        for (int i = 1; i < owners.Length; i++)
            if (!ReferenceEquals(grid.GetOccupant(Cells[i,0],Cells[i,1]),owners[i])) throw new Exception("other fleet owner changed");
        Require(!grid.Release(15,3,new Owner(0)) && ReferenceEquals(grid.GetOccupant(15,3),owners[0]),
                "id0_equal_owner_cannot_release_moved_ship");
        Console.WriteLine("GUARDS\t" + guardCount);
    }
    private static void Main(string[] args)
    {
        byte[] rawFlags = File.ReadAllBytes(args[0]); flags = new uint[rawFlags.Length / 4];
        for (int i = 0; i < flags.Length; i++) flags[i] = BitConverter.ToUInt32(rawFlags,i*4);
        sourceRaw = Hex(File.ReadAllText(args[1]).Trim()); sourceSeed = Seed(sourceRaw);
        string line;
        while ((line = Console.ReadLine()) != null)
        {
            string[] fields = line.Split('\t'); string label = fields[0];
            int pending = int.Parse(fields[1]), count = int.Parse(fields[3]);
            uint start = uint.Parse(fields[2]); bool blocked = fields[4] == "1";
            var grid = Grid(out object[] owners); var motion = new PreparedShipMovement(grid,owners[0],sourceSeed);
            if (!motion.TryBeginAdjacentReferenceMove()) throw new Exception("begin failed");
            if (blocked) grid.TryClaim(15,3,owners[1]);
            int frame = 20, publishedFrame = 20, publishedX = 1028, publishedY = 132; uint lastFrame = 0;
            Emit(label,0,motion,grid,owners[0],frame,false,publishedFrame,publishedX,publishedY);
            for (int tick = 1; tick <= count; tick++)
            {
                uint now = unchecked(start + (uint)tick); bool tail = motion.Step(pending,now);
                if (tail)
                {
                    var result = ShipFrameProgression.AdvanceForward(frame,motion.Current.Heading,now,lastFrame,2);
                    frame = result.Frame; lastFrame = result.LastTick;
                }
                if (motion.LastStepPublishesPose)
                {
                    publishedFrame = frame;
                    publishedX = motion.Current.WorldPixelX; publishedY = motion.Current.WorldPixelY;
                }
                Emit(label,tick,motion,grid,owners[0],frame,tail,publishedFrame,publishedX,publishedY);
            }
        }
        Guards();
    }
}
