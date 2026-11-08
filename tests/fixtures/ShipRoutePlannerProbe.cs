using System;
using System.Globalization;
using System.IO;
using AncientConquest.World;
using AncientConquest.Simulation;

internal static class ShipRoutePlannerProbe
{
    private sealed class Owner
    {
        public override bool Equals(object other) => other is Owner;
        public override int GetHashCode() => 0;
    }
    private static readonly int[,] Cells={{16,2},{21,5},{19,4},{11,18},{9,21},{10,22},{6,13},{6,14}};
    private static uint[] flags;
    private static MissionShipSeed seed;
    private static MissionOccupancyGrid Grid(out object[] owners)
    {
        var grid=new MissionOccupancyGrid(24,24,flags);owners=new object[8];
        for(int i=0;i<8;i++){owners[i]=new Owner();if(!grid.TryClaim(Cells[i,0],Cells[i,1],owners[i]))throw new Exception("fleet");}
        return grid;
    }
    private static byte[] Hex(string text)
    {
        var data=new byte[text.Length/2];for(int i=0;i<data.Length;i++)data[i]=byte.Parse(text.Substring(i*2,2),NumberStyles.HexNumber,CultureInfo.InvariantCulture);return data;
    }
    private static string Hex(byte[] bytes)=>BitConverter.ToString(bytes).Replace("-","").ToLowerInvariant();
    private static string Pack(short[] field)
    {
        var data=new byte[field.Length*2];for(int i=0;i<field.Length;i++){data[i*2]=unchecked((byte)field[i]);data[i*2+1]=unchecked((byte)(field[i]>>8));}return Hex(data);
    }
    private static void Guard<T>(string label,Action action)where T:Exception
    {try{action();}catch(T){Console.WriteLine("GUARD\t"+label);return;}throw new Exception("Missing guard "+label);}
    private static void Main(string[] args)
    {
        var raw=File.ReadAllBytes(args[0]);flags=new uint[576];for(int i=0;i<flags.Length;i++)flags[i]=BitConverter.ToUInt32(raw,i*4);
        if(!MissionShipSeed.TryRead(new MissionObjectSeed("OBJ_0000000b",Hex(File.ReadAllText(args[1]).Trim())),out seed))throw new Exception("seed");
        var grid=Grid(out object[] owners);
        for(int y=0;y<24;y++)for(int x=0;x<24;x++)
        {
            bool planned=ShipRoutePlanner.TryPlan(grid,owners[0],seed,x,y,out ShipRoutePlan plan);
            var map=ShipRoutePlanner.CapturePlanningField(grid,owners[0],x,y);
            Console.WriteLine(string.Join("\t","ROW",x,y,planned?1:0,planned?plan.PathCount:0,planned?plan.PathIndex:0,
                planned?plan.InitialState:0,planned&&plan.CenterGate?1:0,planned?plan.TargetHeading:0,
                planned?Hex(plan.CapturePoints()):"",Pack(map)));
            for(int i=0;i<8;i++)if(!ReferenceEquals(grid.GetOccupant(Cells[i,0],Cells[i,1]),owners[i]))throw new Exception("planner mutated grid");
            if(planned){var copy=plan.CapturePoints();copy[0]^=255;if(Hex(copy)==Hex(plan.CapturePoints()))throw new Exception("plan aliases");}
        }
        Guard<ArgumentNullException>("null_grid",()=>ShipRoutePlanner.TryPlan(null,owners[0],seed,18,4,out _));
        Guard<ArgumentNullException>("null_owner",()=>ShipRoutePlanner.TryPlan(grid,null,seed,18,4,out _));
        Guard<NotSupportedException>("wrong_map",()=>ShipRoutePlanner.TryPlan(new MissionOccupancyGrid(1,1,new uint[1]),owners[0],seed,0,0,out _));
        Guard<ArgumentOutOfRangeException>("negative_goal",()=>ShipRoutePlanner.TryPlan(grid,owners[0],seed,-1,2,out _));
        Guard<ArgumentOutOfRangeException>("outside_goal",()=>ShipRoutePlanner.TryPlan(grid,owners[0],seed,24,2,out _));
        Guard<ArgumentException>("wrong_requester",()=>ShipRoutePlanner.TryPlan(grid,owners[1],seed,18,4,out _));
        var missing=Grid(out object[] m);missing.Release(19,4,m[2]);
        Guard<NotSupportedException>("missing_owner",()=>ShipRoutePlanner.TryPlan(missing,m[0],seed,18,4,out _));
        var extra=Grid(out object[] e);extra.TryClaim(20,4,new Owner());
        Guard<NotSupportedException>("extra_owner",()=>ShipRoutePlanner.TryPlan(extra,e[0],seed,18,4,out _));
        var duplicate=Grid(out object[] dup);duplicate.Release(19,4,dup[2]);duplicate.TryClaim(19,4,dup[1]);
        Guard<NotSupportedException>("same_identity_twice",()=>ShipRoutePlanner.TryPlan(duplicate,dup[0],seed,18,4,out _));
    }
}
