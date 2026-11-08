using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using AncientConquest.World;
using AncientConquest.Simulation;

internal static class ShipMoveOrderProbe
{
    private sealed class Owner
    {
        public override bool Equals(object other) => other is Owner;
        public override int GetHashCode() => 0;
    }
    private static readonly int[,] Cells={{16,2},{21,5},{19,4},{11,18},{9,21},{10,22},{6,13},{6,14}};
    private static uint[] flags;
    private static MissionShipSeed seed;
    private static byte[] rawSeed;
    private static MissionOccupancyGrid grid;
    private static object owner;
    private static ShipMoveOrder command;
    private static string label;
    private static int sample;
    private static byte[] Hex(string text)
    {
        var result=new byte[text.Length/2];
        for(int i=0;i<result.Length;i++)result[i]=byte.Parse(text.Substring(i*2,2),NumberStyles.AllowHexSpecifier,CultureInfo.InvariantCulture);
        return result;
    }
    private static string Hex(byte[] data)=>BitConverter.ToString(data).Replace("-","").ToLowerInvariant();
    private static MissionOccupancyGrid Grid(out object own)
    {
        var result=new MissionOccupancyGrid(24,24,flags);own=null;
        for(int i=0;i<8;i++) {object current=new Owner();result.TryClaim(Cells[i,0],Cells[i,1],current);if(i==0)own=current;}
        return result;
    }
    private static void Emit(string operation)
    {
        var s=command.Current;var m=s.Motion;int occupied=0;var own=new List<int>();
        for(int y=0;y<24;y++)for(int x=0;x<24;x++)
        {object value=grid.GetOccupant(x,y);if(value!=null)occupied++;if(ReferenceEquals(value,owner))own.Add(y*24+x);}
        Console.WriteLine(string.Join("\t","ROW",label,sample,operation,m.SourceCounter,
            m.CellX,m.CellY,m.WorldPixelX,m.WorldPixelY,m.State,m.CenterGate?1:0,
            m.Heading,m.TargetHeading,m.TurnStep,m.Speed,m.Remainder,m.Deceleration,
            m.ReservedCellIndex,m.NextCellIndex,m.PathIndex,m.PathCount,m.StoredFrame,
            m.LastFrameTick,m.LastStateCounter,m.DrawnFrame,m.PublishedWorldX,m.PublishedWorldY,
            command.LastStepReachedForwardTail?1:0,command.LastStepPublishesPose?1:0,
            occupied,string.Join(",",own),m.IsComplete?1:0,m.WaypointX,m.WaypointY,m.NextWaypointX,m.NextWaypointY,
            command.LastStepPublicationCount,s.PendingFlags,s.ActiveFlags,s.DeferredFlags,s.StopMask,s.ReadyMask,s.Capabilities,
            s.RequestedGoalX,s.RequestedGoalY,s.TargetX,s.TargetY,s.FirstNavigation?1:0,s.Retry,s.LastPlanCounter,s.RetryInterval,
            s.SnapshotRetry,s.SnapshotTargetX,s.SnapshotTargetY,s.SnapshotCellX,s.SnapshotCellY,s.RandomState,
            command.CanRequestMove?1:0,m.PathEndpointX,m.PathEndpointY,s.RequestedTargetReached?1:0,m.LastCellIndex,
            s.CachedObstacleCount,string.Join(",",command.CaptureCachedObstacles()),Hex(command.CaptureRoutePoints()),s.NavigationRadius));
        for(int i=0;i<command.LastStepPublicationCount;i++) {var p=command.GetLastStepPublication(i);Console.WriteLine(string.Join("\t","PUB",label,sample,i,p.Frame,p.WorldPixelX,p.WorldPixelY,p.Depth));}
        for(int i=0;i<command.LastStepGridMutationCount;i++) {var g=command.GetLastStepGridMutation(i);Console.WriteLine(string.Join("\t","GRID",label,sample,i,g.CellIndex,g.Occupied?1:0));}
    }
    private static int guards;
    private static void Reject<T>(string name,Action action) where T:Exception
    {
        try{action();}catch(T){Console.WriteLine("CHECK\t"+name);guards++;return;}
        throw new Exception("Missing guard "+name);
    }
    private static void Require(bool value,string name)
    {if(!value)throw new Exception(name);Console.WriteLine("CHECK\t"+name);guards++;}
    private static void Guards()
    {
        grid=Grid(out owner);
        Reject<ArgumentNullException>("null_grid",()=>new ShipMoveOrder(null,owner,seed));
        Reject<ArgumentNullException>("null_owner",()=>new ShipMoveOrder(grid,null,seed));
        Reject<ArgumentException>("equal_owner_is_not_identity",()=>new ShipMoveOrder(grid,new Owner(),seed));
        Reject<NotSupportedException>("wrong_geometry",()=>new ShipMoveOrder(new MissionOccupancyGrid(1,1,new uint[1]),owner,seed));
        command=new ShipMoveOrder(grid,owner,seed);
        Require(command.CanRequestMove && command.Current.SourceCounter==0 && command.LastStepPublicationCount==0,"initial_ready");
        foreach(int value in new[]{-1,24,int.MinValue,int.MaxValue})
        {int v=value;Reject<ArgumentOutOfRangeException>("goal_x_"+v,()=>command.RequestCellMove(v,2));Reject<ArgumentOutOfRangeException>("goal_y_"+v,()=>command.RequestCellMove(16,v));}
        foreach(byte value in new byte[]{1,50,51,254}) {byte v=value;Reject<NotSupportedException>("priority_"+v,()=>command.RequestCellMove(18,5,v));}
        foreach(int value in new[]{-1,0,4,5,6,8,int.MaxValue}) {int v=value;Reject<ArgumentOutOfRangeException>("pending_"+v,()=>command.Tick(1,v));}
        foreach(uint value in new[]{0u,2u,uint.MaxValue}) {uint v=value;Reject<ArgumentException>("counter_"+v,()=>command.Tick(v));}
        Reject<ArgumentOutOfRangeException>("publication_empty",()=>command.GetLastStepPublication(0));
        Require(command.RequestCellMove(18,5),"request_accepted");
        Reject<NotSupportedException>("pending_replacement",()=>command.RequestCellMove(16,4));
        command.Tick(1);Reject<NotSupportedException>("active_replacement",()=>command.RequestCellMove(16,4));
        var copy=command.CaptureRoutePoints();copy[0]=0;
        Require(command.CaptureRoutePoints()[0]==16,"route_capture_owned");
        var cache=command.CaptureCachedObstacles();if(cache.Length>0)cache[0]=0;
        Require(command.CaptureCachedObstacles().Length>0 && command.CaptureCachedObstacles()[0]==115,"cache_capture_owned");
        uint now=1;
        while(now<400 && !(command.CanRequestMove && command.LastStepPublishesPose && command.Current.Motion.DrawnFrame>=56))
        {command.Tick(++now);}
        Require(now<400 && command.Current.RequestedTargetReached,"normal_clear_idle");
        int idleFrame=command.Current.Motion.StoredFrame;uint idleTick=command.Current.Motion.LastFrameTick,rng=command.Current.RandomState;
        command.RequestCellMove(16,4);
        Require(command.LastStepPublicationCount==0 && !command.LastStepReachedForwardTail && command.LastStepGridMutationCount==0 &&
            command.Current.Motion.StoredFrame==idleFrame && command.Current.Motion.LastFrameTick==idleTick && command.Current.RandomState==rng,"request_clears_effects_preserves_idle");
        Console.WriteLine("GUARDS\t"+guards);
    }
    private static void Main(string[] args)
    {
        byte[] rawFlags=File.ReadAllBytes(args[0]);flags=new uint[rawFlags.Length/4];
        for(int i=0;i<flags.Length;i++)flags[i]=BitConverter.ToUInt32(rawFlags,i*4);
        rawSeed=Hex(File.ReadAllText(args[1]).Trim());
        if(!MissionShipSeed.TryRead(new MissionObjectSeed("OBJ_0000000b",rawSeed),out seed))throw new Exception("seed");
        string line;
        while((line=Console.ReadLine())!=null)
        {
            string[] f=line.Split('\t');
            if(f[0]=="START") {label=f[1];sample=0;grid=Grid(out owner);command=new ShipMoveOrder(grid,owner,seed,uint.Parse(f[2]));Emit("initial");}
            else if(f[0]=="R") {command.RequestCellMove(int.Parse(f[1]),int.Parse(f[2]),byte.Parse(f[3]));sample++;Emit("request");}
            else if(f[0]=="T") {command.Tick(uint.Parse(f[1]),int.Parse(f[2]));sample++;Emit("tick");}
            else throw new Exception("operation");
        }
        Guards();
    }
}
