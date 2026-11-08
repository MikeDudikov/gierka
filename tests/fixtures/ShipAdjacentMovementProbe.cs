using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using AncientConquest.World;
using AncientConquest.Simulation;

internal static class ShipAdjacentMovementProbe
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
    private static string Hex(byte[] bytes) => BitConverter.ToString(bytes).Replace("-", "").ToLowerInvariant();
    private static void Put(byte[] data, int offset, uint value)
    {
        for (int i = 0; i < 4; i++) data[offset + i] = unchecked((byte)(value >> (i * 8)));
    }
    private static MissionShipSeed Seed(byte[] raw, string name = "OBJ_0000000b")
    {
        if (!MissionShipSeed.TryRead(new MissionObjectSeed(name, raw), out MissionShipSeed seed)) throw new Exception("source class");
        return seed;
    }
    private static MissionOccupancyGrid Grid(out object[] owners)
    {
        var grid = new MissionOccupancyGrid(24,24,flags); owners = new object[8];
        for (int i = 0; i < owners.Length; i++)
        {
            owners[i] = new Owner(0);
            if (!grid.TryClaim(Cells[i,0],Cells[i,1],owners[i])) throw new Exception("fleet claim");
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
    private static void Emit(string label, int tick, ShipAdjacentMovement motion,
                             MissionOccupancyGrid grid, object owner)
    {
        var s = motion.Current; var owned = new List<int>(); int occupied = 0;
        for (int y = 0; y < 24; y++)
            for (int x = 0; x < 24; x++)
            {
                object actual = grid.GetOccupant(x,y);
                if (actual != null) occupied++;
                if (ReferenceEquals(actual,owner)) owned.Add(y * 24 + x);
            }
        Console.WriteLine(string.Join("\t", "ROW", label, tick, s.SourceCounter,
            s.CellX, s.CellY, s.WorldPixelX, s.WorldPixelY, s.State, s.CenterGate ? 1 : 0,
            s.Heading, s.TargetHeading, s.TurnStep, s.Speed, s.Remainder, s.Deceleration,
            s.ReservedCellIndex, s.NextCellIndex, s.PathIndex, s.PathCount, s.StoredFrame,
            s.LastFrameTick, s.LastStateCounter, s.DrawnFrame, s.PublishedWorldX, s.PublishedWorldY,
            motion.LastStepReachedForwardTail ? 1 : 0, motion.LastStepPublishesPose ? 1 : 0,
            occupied, string.Join(",",owned), s.IsComplete ? 1 : 0));
    }
    private static void Guards()
    {
        var grid = Grid(out object[] owners);
        Reject<ArgumentNullException>("null_grid", () => new ShipAdjacentMovement(null,owners[0],sourceSeed));
        Reject<ArgumentNullException>("null_owner", () => new ShipAdjacentMovement(grid,null,sourceSeed));
        Reject<ArgumentException>("wrong_identity", () => new ShipAdjacentMovement(grid,new Owner(0),sourceSeed));
        Reject<NotSupportedException>("wrong_geometry", () => new ShipAdjacentMovement(new MissionOccupancyGrid(1,1,new uint[1]),owners[0],sourceSeed));
        foreach (int field in new[] {20,24,28,36,40,44,48,56,60,512})
        {
            int offset = field; byte[] raw = (byte[])sourceRaw.Clone();
            Put(raw,offset,unchecked((uint)(BitConverter.ToInt32(raw,offset) + 1)));
            Reject<NotSupportedException>("seed_field_" + offset, () => new ShipAdjacentMovement(grid,owners[0],Seed(raw)));
        }
        Reject<NotSupportedException>("other_instance", () => new ShipAdjacentMovement(grid,owners[0],Seed(sourceRaw,"OBJ_00000000")));
        var motion = new ShipAdjacentMovement(grid,owners[0],sourceSeed);
        foreach (uint planner in new[] {0u,2u,uint.MaxValue})
        {
            uint value = planner;
            Reject<NotSupportedException>("planner_counter_" + value, () => motion.TryBeginAdjacentReferenceMove(17,2,value));
        }
        foreach (int pending in new[] {int.MinValue,-1,0,4,5,6,8,int.MaxValue})
        {
            int value = pending;
            Reject<ArgumentOutOfRangeException>("pending_" + value, () => motion.Step(value,2));
        }
        Reject<InvalidOperationException>("step_before_route", () => motion.Step(1,2));
        Require(!motion.TryBeginAdjacentReferenceMove(16,1) && !motion.HasRoute && motion.CaptureRoutePoints().Length == 0,
                "source_north_refused");
        Reject<InvalidOperationException>("step_rejected_route", () => motion.Step(1,2));
        Require(motion.TryBeginAdjacentReferenceMove(17,2),"retry_other_adjacent_goal_after_refusal");
        byte[] route = motion.CaptureRoutePoints(); route[0] = 0;
        Require(motion.CaptureRoutePoints()[0] == 16,"route_points_are_copied");
        Reject<InvalidOperationException>("begin_twice", () => motion.TryBeginAdjacentReferenceMove(15,3));
        foreach (uint counter in new[] {0u,1u,3u,uint.MaxValue})
        {
            uint value = counter;
            Reject<ArgumentException>("nonsequential_counter_" + value, () => motion.Step(1,value));
        }
        motion.Step(1,2);
        Require(motion.Current.State == 2 && motion.Current.StoredFrame == 47 && motion.Current.DrawnFrame == 20 &&
                !motion.LastStepReachedForwardTail && !motion.LastStepPublishesPose,
                "turn_start_does_not_publish_or_move");
        uint now = 3;
        while (motion.Current.State == 2) motion.Step(1,now++);
        Require(motion.Current.State == 3 && motion.Current.ReservedCellIndex == -1 &&
                !motion.LastStepReachedForwardTail && grid.GetOccupant(17,2) == null,
                "turn_completion_does_not_reserve_same_call");
        while (!motion.IsStopped) motion.Step(1,now++);
        var complete = motion.Current; motion.Step(1,now);
        Require(complete.IsComplete && motion.Current.SourceCounter == complete.SourceCounter &&
                motion.Current.StoredFrame == complete.StoredFrame && !motion.LastStepPublishesPose &&
                !motion.LastStepReachedForwardTail && grid.GetOccupant(16,2) == null &&
                ReferenceEquals(grid.GetOccupant(17,2),owners[0]),"stopped_reference_is_frozen");
        Require(!grid.Release(17,2,new Owner(0)) && ReferenceEquals(grid.GetOccupant(17,2),owners[0]),
                "equal_id0_cannot_release_moved_owner");
        for (int i = 1; i < owners.Length; i++)
            if (!ReferenceEquals(grid.GetOccupant(Cells[i,0],Cells[i,1]),owners[i])) throw new Exception("other fleet owner changed");
        grid = Grid(out owners); motion = new ShipAdjacentMovement(grid,owners[0],sourceSeed);
        motion.TryBeginAdjacentReferenceMove(15,3); motion.Step(1,2);
        grid.Release(15,3,owners[0]); object foreign = new Owner(0); grid.TryClaim(15,3,foreign);
        Reject<InvalidOperationException>("reserved_owner_changed", () => motion.Step(1,3));
        Require(ReferenceEquals(grid.GetOccupant(15,3),foreign) && ReferenceEquals(grid.GetOccupant(16,2),owners[0]),
                "foreign_target_is_preserved_on_failure");
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
            string[] f = line.Split('\t'); string label = f[0];
            int pending = int.Parse(f[1]), x = int.Parse(f[2]), y = int.Parse(f[3]), count = int.Parse(f[4]);
            bool accepted = f[5] == "1", occupiedAfterPlan = f[6] == "1";
            var grid = Grid(out object[] owners); var motion = new ShipAdjacentMovement(grid,owners[0],sourceSeed);
            bool planned = motion.TryBeginAdjacentReferenceMove(x,y,1);
            if (planned != accepted) throw new Exception("Unexpected adjacent plan outcome " + label);
            Console.WriteLine("PLAN\t" + label + "\t" + (planned ? 1 : 0) + "\t" + Hex(motion.CaptureRoutePoints()));
            if (occupiedAfterPlan && !grid.TryClaim(x,y,owners[1])) throw new Exception("postplan occupancy control");
            Emit(label,0,motion,grid,owners[0]);
            for (int tick = 1; tick <= count; tick++)
            {
                motion.Step(pending,unchecked(1u+(uint)tick));
                Emit(label,tick,motion,grid,owners[0]);
            }
        }
        Guards();
    }
}
