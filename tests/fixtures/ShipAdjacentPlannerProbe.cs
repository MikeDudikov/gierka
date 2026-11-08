using System;
using System.IO;
using AncientConquest.World;
using AncientConquest.Simulation;

internal static class ShipAdjacentPlannerProbe
{
    private static readonly int[,] Fleet =
    { {16,2}, {21,5}, {19,4}, {11,18}, {9,21}, {10,22}, {6,13}, {6,14} };
    private static readonly int[,] Directions =
    { {1,0}, {1,-1}, {0,-1}, {-1,-1}, {-1,0}, {-1,1}, {0,1}, {1,1} };
    private static uint[] flags;
    private sealed class Identity
    {
        public override bool Equals(object other) => other is Identity;
        public override int GetHashCode() => 0;
    }
    private static MissionOccupancyGrid Grid(out object[] owners)
    {
        var grid = new MissionOccupancyGrid(24, 24, flags);
        owners = new object[8];
        for (int i = 0; i < 8; ++i)
        {
            owners[i] = new Identity();
            if (!grid.TryClaim(Fleet[i,0], Fleet[i,1], owners[i])) throw new Exception("Cannot claim source fleet.");
        }
        return grid;
    }
    private static bool Plan(MissionOccupancyGrid grid, object owner, int x, int y, out ShipAdjacentPlan plan)
        => ShipAdjacentPlanner.TryPlan(grid, owner, 16, 2, 5, x, y, 0, out plan);
    private static void Guard<T>(string name, Action action) where T:Exception
    {
        try { action(); }
        catch(T) { Console.WriteLine("GUARD\t"+name); return; }
        throw new Exception("Missing adapter rejection: "+name);
    }
    private static string Hex(byte[] bytes) => BitConverter.ToString(bytes).Replace("-", "").ToLowerInvariant();
    private static void Main(string[] args)
    {
        byte[] raw=File.ReadAllBytes(args[0]);flags=new uint[576];
        for(int i=0;i<flags.Length;++i)flags[i]=BitConverter.ToUInt32(raw,i*4);
        var grid=Grid(out object[] owners);
        for(int h=0;h<8;++h)
        {
            bool accepted=Plan(grid,owners[0],16+Directions[h,0],2+Directions[h,1],out ShipAdjacentPlan plan);
            Console.WriteLine(string.Join("\t","ROW",h,accepted?1:0,plan.PathCount,plan.PathIndex,plan.InitialState,
                                          plan.CenterGate?1:0,Hex(plan.CapturePoints())));
            for(int y=0;y<24;++y)for(int x=0;x<24;++x)
            {
                object expected=null;
                for(int i=0;i<8;++i)if(Fleet[i,0]==x&&Fleet[i,1]==y)expected=owners[i];
                if(!ReferenceEquals(grid.GetOccupant(x,y),expected)||grid.GetFlags(x,y)!=flags[y*24+x])
                    throw new Exception("Planner changed source flags or owner identities.");
            }
        }
        Console.WriteLine("GUARD\teight-distinct-equal-value-identities-and-grid-immutability");
        Plan(grid,owners[0],17,2,out ShipAdjacentPlan copied);
        byte[] first=copied.CapturePoints(),second=copied.CapturePoints();first[0]=99;first[9]=99;
        if(ReferenceEquals(first,second)||Hex(copied.CapturePoints())!=Hex(second))throw new Exception("Mutable path escaped.");
        if(copied.OriginX!=16||copied.OriginY!=2||copied.TargetX!=17||copied.TargetY!=2||copied.TargetHeading!=0)
            throw new Exception("Path metadata differs from its native points.");
        Console.WriteLine("GUARD\tpath-copy-and-metadata");
        if(Plan(grid,owners[0],16,1,out copied)||copied.PathCount!=0||copied.CapturePoints().Length!=0)
            throw new Exception("Blocked path retained a previous result.");
        Console.WriteLine("GUARD\tblocked-clears-previous-plan");
        Guard<ArgumentNullException>("null-grid",()=>Plan(null,owners[0],17,2,out _));
        Guard<ArgumentNullException>("null-owner",()=>Plan(grid,null,17,2,out _));
        Guard<ArgumentException>("wrong-requester",()=>Plan(grid,new Identity(),17,2,out _));
        Guard<NotSupportedException>("wrong-origin",()=>ShipAdjacentPlanner.TryPlan(grid,owners[0],15,2,5,17,2,0,out _));
        Guard<NotSupportedException>("wrong-heading",()=>ShipAdjacentPlanner.TryPlan(grid,owners[0],16,2,4,17,2,0,out _));
        Guard<NotSupportedException>("unsupported-restriction",()=>ShipAdjacentPlanner.TryPlan(grid,owners[0],16,2,5,17,2,1,out _));
        foreach(int x in new[]{16,14,int.MinValue,int.MaxValue})
        {
            int saved=x;Guard<NotSupportedException>("nonadjacent-goal:"+x,()=>Plan(grid,owners[0],saved,2,out _));
        }
        Guard<NotSupportedException>("wrong-map",()=>Plan(new MissionOccupancyGrid(23,24,new uint[23*24]),owners[0],17,2,out _));
        var missing=Grid(out object[] missingOwners);missing.Release(21,5,missingOwners[1]);
        Guard<NotSupportedException>("missing-source-owner",()=>Plan(missing,missingOwners[0],17,2,out _));
        var duplicate=Grid(out object[] duplicateOwners);duplicate.Release(21,5,duplicateOwners[1]);duplicate.TryClaim(21,5,duplicateOwners[0]);
        Guard<NotSupportedException>("duplicated-source-identity",()=>Plan(duplicate,duplicateOwners[0],17,2,out _));
        var extra=Grid(out object[] extraOwners);extra.TryClaim(17,2,new Identity());
        Guard<NotSupportedException>("additional-target-claim",()=>Plan(extra,extraOwners[0],17,2,out _));
        uint savedFlag=flags[1*24+16];flags[1*24+16]=1;
        var changed=Grid(out object[] changedOwners);flags[1*24+16]=savedFlag;
        Guard<NotSupportedException>("changed-local-flags",()=>Plan(changed,changedOwners[0],17,2,out _));
    }
}
