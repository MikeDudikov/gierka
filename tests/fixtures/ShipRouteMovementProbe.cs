using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using AncientConquest.World;
using AncientConquest.Simulation;

internal static class ShipRouteMovementProbe
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
    private static void Emit(string label, int tick, ShipRouteMovement motion,
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
            occupied, string.Join(",",owned), s.IsComplete ? 1 : 0, s.WaypointX,s.WaypointY,s.NextWaypointX,s.NextWaypointY,s.LastStepPublicationCount));
        for(int i=0;i<motion.LastStepPublicationCount;i++) { var p=motion.GetLastStepPublication(i);Console.WriteLine(string.Join("\t","PUB",label,tick,i,p.Frame,p.WorldPixelX,p.WorldPixelY,p.Depth)); }
        for(int i=0;i<motion.LastStepGridMutationCount;i++) { var m=motion.GetLastStepGridMutation(i);Console.WriteLine(string.Join("\t","GRID",label,tick,i,m.CellIndex,m.Occupied?1:0)); }
    }
    private static void Guards()
    {
        var grid=Grid(out object[] owners);
        Reject<ArgumentNullException>("null_grid",()=>new ShipRouteMovement(null,owners[0],sourceSeed));
        Reject<ArgumentNullException>("null_owner",()=>new ShipRouteMovement(grid,null,sourceSeed));
        Reject<ArgumentException>("wrong_identity",()=>new ShipRouteMovement(grid,new Owner(0),sourceSeed));
        Reject<NotSupportedException>("wrong_geometry",()=>new ShipRouteMovement(new MissionOccupancyGrid(1,1,new uint[1]),owners[0],sourceSeed));
        foreach(int field in new[]{20,24,28,36,40,44,48,56,60,512})
        {
            int offset=field;byte[] raw=(byte[])sourceRaw.Clone();Put(raw,offset,unchecked((uint)(BitConverter.ToInt32(raw,offset)+1)));
            Reject<NotSupportedException>("seed_field_"+offset,()=>new ShipRouteMovement(grid,owners[0],Seed(raw)));
        }
        Reject<NotSupportedException>("other_instance",()=>new ShipRouteMovement(grid,owners[0],Seed(sourceRaw,"OBJ_00000000")));
        foreach(int length in new[]{0,5,9,11,2890})
        {
            int size=length;Reject<ArgumentException>("plan_length_"+size,()=>new ShipRoutePlan(new byte[size],14,4));
        }
        Reject<ArgumentException>("plan_null",()=>new ShipRoutePlan(null,14,4));
        byte[] good=Hex("10000200050f000300050e00040005");
        byte[] rawInput=(byte[])good.Clone();var plan=new ShipRoutePlan(rawInput,14,4);rawInput[0]=0;
        byte[] copy=plan.CapturePoints();copy[0]=0;
        Require(plan.CapturePoints()[0]==16,"plan_copies_input_and_capture");
        foreach(int mode in new[]{0,1,2,3,4})
        {
            byte[] changed=(byte[])good.Clone();
            if(mode==0)changed[5]=24;
            if(mode==1)changed[9]=8;
            if(mode==2)changed[9]=4;
            if(mode==3)changed[0]=15;
            if(mode==4)changed[5]=13;
            int current=mode;
            Reject<NotSupportedException>("plan_record_"+current,()=>new ShipRoutePlan(changed,14,4));
        }
        Reject<NotSupportedException>("plan_goal_mismatch",()=>new ShipRoutePlan(good,14,5));
        byte[] waveFirst=(byte[])good.Clone();waveFirst[4]=0;
        Require(new ShipRoutePlan(waveFirst,14,4).TargetHeading==5,"first_record_heading_is_not_first_segment");
        var motion=new ShipRouteMovement(grid,owners[0],sourceSeed);
        foreach(uint initial in new[]{0u,2u,uint.MaxValue})
        {
            uint value=initial;Reject<NotSupportedException>("planner_counter_"+value,()=>motion.TryBegin(plan,value));
        }
        foreach(int pending in new[]{int.MinValue,-1,0,4,5,6,8,int.MaxValue})
        {
            int value=pending;Reject<ArgumentOutOfRangeException>("pending_"+value,()=>motion.Step(value,2));
        }
        Reject<InvalidOperationException>("step_without_plan",()=>motion.Step(1,2));
        Require(!motion.TryBegin(null,1) && motion.Current.SourceCounter==1 && motion.CaptureRoutePoints().Length==0,
                "null_plan_is_explicit_no_route");
        Reject<ArgumentOutOfRangeException>("publication_empty",()=>motion.GetLastStepPublication(0));
        Reject<ArgumentOutOfRangeException>("publication_negative",()=>motion.GetLastStepPublication(-1));
        Require(motion.TryBegin(plan,1),"begin_source_plan");
        byte[] route=motion.CaptureRoutePoints();route[0]=0;
        Require(motion.CaptureRoutePoints()[0]==16,"core_copies_route_capture");
        Reject<InvalidOperationException>("begin_twice",()=>motion.TryBegin(plan,1));
        foreach(uint wrong in new[]{0u,1u,3u,uint.MaxValue})
        {
            uint value=wrong;Reject<ArgumentException>("nonsequential_counter_"+value,()=>motion.Step(1,value));
        }
        uint now=2;
        while(!motion.IsStopped)motion.Step(1,now++);
        var ended=motion.Current;motion.Step(1,now);
        Require(ended.IsComplete && motion.Current.SourceCounter==ended.SourceCounter && motion.LastStepPublicationCount==0 &&
                motion.LastStepGridMutationCount==0 && !motion.LastStepReachedForwardTail &&
                ReferenceEquals(grid.GetOccupant(14,4),owners[0]),"stopped_reference_does_not_replay_side_effects");
        Reject<ArgumentOutOfRangeException>("stopped_publication_hidden",()=>motion.GetLastStepPublication(0));
        Require(!grid.Release(14,4,new Owner(0)) && ReferenceEquals(grid.GetOccupant(14,4),owners[0]),"equal_id0_cannot_release_owner");
        grid=Grid(out owners);motion=new ShipRouteMovement(grid,owners[0],sourceSeed);
        ShipRoutePlanner.TryPlan(grid,owners[0],sourceSeed,17,4,out ShipRoutePlan corner);
        motion.TryBegin(corner,1);now=2;bool sawDouble=false,sawReclaim=false;
        while(!motion.IsStopped)
        {
            motion.Step(1,now++);
            if(motion.LastStepGridMutationCount==2)
            {
                var a=motion.GetLastStepGridMutation(0);var b=motion.GetLastStepGridMutation(1);
                if(a.CellIndex==b.CellIndex && !a.Occupied && b.Occupied)sawReclaim=true;
            }
            if(motion.LastStepPublicationCount==2)
            {
                var a=motion.GetLastStepPublication(0);var b=motion.GetLastStepPublication(1);
                Require(a.Frame==b.Frame && (a.WorldPixelX!=b.WorldPixelX || a.WorldPixelY!=b.WorldPixelY) &&
                        b.WorldPixelX==motion.Current.PublishedWorldX && b.WorldPixelY==motion.Current.PublishedWorldY,
                        "two_publications_are_ordered_values");
                Reject<ArgumentOutOfRangeException>("publication_upper_bound",()=>motion.GetLastStepPublication(2));
                sawDouble=true;
            }
        }
        Require(sawDouble && sawReclaim,"native_corner_double_publish_and_reclaim_seen");
        for(int i=1;i<owners.Length;i++)
            if(!ReferenceEquals(grid.GetOccupant(Cells[i,0],Cells[i,1]),owners[i]))throw new Exception("Static fleet owner changed");
        Console.WriteLine("GUARDS\t"+guardCount);
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
            bool accepted = f[5] == "1"; byte[] rawPoints=Hex(f[6]);
            var grid = Grid(out object[] owners); var motion = new ShipRouteMovement(grid,owners[0],sourceSeed);
            bool plannerResult=ShipRoutePlanner.TryPlan(grid,owners[0],sourceSeed,x,y,out ShipRoutePlan plan);
            if(plannerResult!=accepted || Hex(plan==null?new byte[0]:plan.CapturePoints())!=Hex(rawPoints))
                throw new Exception("Actual C# planner differs from native plan "+label);
            bool planned = motion.TryBegin(plan,1);
            if (planned != accepted) throw new Exception("Unexpected adjacent plan outcome " + label);
            Console.WriteLine("PLAN\t" + label + "\t" + (planned ? 1 : 0) + "\t" + Hex(motion.CaptureRoutePoints()));

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
