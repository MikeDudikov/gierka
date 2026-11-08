using System;
using System.Globalization;
using System.IO;
using AncientConquest.World;
using AncientConquest.Simulation;

internal static class ShipReplanPlannerProbe
{
    private sealed class Owner
    {
        public override bool Equals(object other)=>other is Owner;
        public override int GetHashCode()=>0;
    }
    private static readonly int[,] StaticCells={{21,5},{19,4},{11,18},{9,21},{10,22},{6,13},{6,14}};
    private static uint[] flags;
    private static MissionOccupancyGrid Grid(int x,int y,int rx,int ry,out object owner)
    {
        var grid=new MissionOccupancyGrid(24,24,flags);owner=new Owner();grid.TryClaim(x,y,owner);
        if(rx>=0)grid.TryClaim(rx,ry,owner);
        for(int i=0;i<7;i++)grid.TryClaim(StaticCells[i,0],StaticCells[i,1],new Owner());
        return grid;
    }
    private static string Hex(byte[] data)=>BitConverter.ToString(data).Replace("-","").ToLowerInvariant();
    private static string Pack(short[] field)
    {var raw=new byte[field.Length*2];for(int i=0;i<field.Length;i++){raw[i*2]=unchecked((byte)field[i]);raw[i*2+1]=unchecked((byte)(field[i]>>8));}return Hex(raw);}
    private static int[] ParseCache(string value)
    {if(value.Length==0)return new int[0];var values=value.Split(',');var result=new int[values.Length];for(int i=0;i<result.Length;i++)result[i]=int.Parse(values[i]);return result;}
    private static void Guard<T>(string label,Action action)where T:Exception
    {try{action();}catch(T){Console.WriteLine("GUARD\t"+label);return;}throw new Exception("Missing guard "+label);}
    private static void Main(string[] args)
    {
        var raw=File.ReadAllBytes(args[0]);flags=new uint[576];for(int i=0;i<576;i++)flags[i]=BitConverter.ToUInt32(raw,i*4);
        string line;
        while((line=Console.ReadLine())!=null)
        {
            if(line.Length==0)continue;
            var f=line.Split('\t');int cx=int.Parse(f[1]),cy=int.Parse(f[2]);var grid=Grid(cx,cy,int.Parse(f[12]),int.Parse(f[13]),out object owner);
            int[] cache=ParseCache(f[11]);string before=string.Join(",",cache);
            var result=ShipReplanPlanner.Plan(grid,owner,cx,cy,int.Parse(f[3]),int.Parse(f[4]),int.Parse(f[5]),int.Parse(f[6]),
                int.Parse(f[7]),byte.Parse(f[8]),f[9]=="1",uint.Parse(f[10],CultureInfo.InvariantCulture),cache);
            if(before!=string.Join(",",cache))throw new Exception("input cache alias");
            Console.WriteLine(string.Join("\t","ROW",f[0],result.PointCount,result.UsedNearest?1:0,result.ReachedWithinRange?1:0,
                result.HasInstallableRoute?1:0,result.FirstHeading,result.EndpointX,result.EndpointY,result.RadiusAfterPlan,
                result.RandomStateAfter,result.RandomStateAdvanced?1:0,string.Join(",",result.CaptureCachedObstacles()),
                Hex(result.CapturePoints()),Pack(result.CapturePlanningField()),Pack(result.CaptureWorkingField())));
            var points=result.CapturePoints();if(points.Length>0){points[0]^=255;if(Hex(points)==Hex(result.CapturePoints()))throw new Exception("point alias");}
            var map=result.CapturePlanningField();map[0]=123;if(result.CapturePlanningField()[0]==123)throw new Exception("map alias");
            var cached=result.CaptureCachedObstacles();if(cached.Length>0){cached[0]=-1;if(result.CaptureCachedObstacles()[0]==-1)throw new Exception("cache alias");}
        }
        var g=Grid(16,2,-1,-1,out object own);
        Guard<ArgumentNullException>("null_grid",()=>ShipReplanPlanner.Plan(null,own,16,2,16,2,20,4,0,0,true));
        Guard<ArgumentNullException>("null_owner",()=>ShipReplanPlanner.Plan(g,null,16,2,16,2,20,4,0,0,true));
        Guard<NotSupportedException>("wrong_map",()=>ShipReplanPlanner.Plan(new MissionOccupancyGrid(1,1,new uint[1]),own,0,0,0,0,0,0,0,0,true));
        Guard<ArgumentOutOfRangeException>("negative_cell",()=>ShipReplanPlanner.Plan(g,own,-1,2,16,2,20,4,0,0,true));
        Guard<ArgumentOutOfRangeException>("outside_origin",()=>ShipReplanPlanner.Plan(g,own,16,2,24,2,20,4,0,0,true));
        Guard<ArgumentOutOfRangeException>("outside_goal",()=>ShipReplanPlanner.Plan(g,own,16,2,16,2,20,24,0,0,true));
        Guard<ArgumentOutOfRangeException>("negative_radius",()=>ShipReplanPlanner.Plan(g,own,16,2,16,2,20,4,-1,0,true));
        Guard<ArgumentOutOfRangeException>("outside_radius",()=>ShipReplanPlanner.Plan(g,own,16,2,16,2,20,4,33,0,true));
        Guard<ArgumentException>("wrong_owner",()=>ShipReplanPlanner.Plan(g,new Owner(),16,2,16,2,20,4,0,0,true));
        Guard<NotSupportedException>("unknown_cache",()=>ShipReplanPlanner.Plan(g,own,16,2,16,2,20,4,0,0,true,0,new[]{1}));
        Guard<NotSupportedException>("duplicate_cache",()=>ShipReplanPlanner.Plan(g,own,16,2,16,2,20,4,0,0,true,0,new[]{115,115}));
        var many=Grid(16,2,17,2,out object m);many.TryClaim(18,3,m);
        Guard<NotSupportedException>("three_owner_claims",()=>ShipReplanPlanner.Plan(many,m,16,2,17,2,20,4,0,0,true));
        var extra=Grid(16,2,-1,-1,out object e);extra.TryClaim(20,4,new Owner());
        Guard<NotSupportedException>("foreign_dynamic",()=>ShipReplanPlanner.Plan(extra,e,16,2,16,2,20,4,0,0,true));
    }
}
