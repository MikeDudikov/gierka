using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using AncientConquest.World;
using AncientConquest.Simulation;

class ShipStatePortProbe
{
    private sealed class Owner { public override bool Equals(object value)=>value is Owner; public override int GetHashCode()=>0; }
    private static readonly int[,] Cells={{16,2},{21,5},{19,4},{11,18},{9,21},{10,22},{6,13},{6,14}};
    private static readonly int[] Ids={11,12,13,16,39,40,41,42};
    private static readonly uint[] Classes={200,200,207,201,206,206,206,206};
    private static readonly object[] Owners=new object[8];
    private static readonly ShipMoveOrder[] Motion=new ShipMoveOrder[3];
    private static readonly MissionShipSeed[] Seeds=new MissionShipSeed[3];
    private static readonly byte[][] Payloads=new byte[3][];
    private static MissionOccupancyGrid grid;
    private static readonly short[] Groups=new short[8];
    private static ShipPlanningOccupant DescribePlanning(object owner)
    {for(int i=0;i<8;i++)if(ReferenceEquals(owner,Owners[i]))return new ShipPlanningOccupant(Classes[i],i<3?Motion[i].Current.Motion.State:(byte)0,Groups[i]);throw new Exception("Unknown owner");}
    private static byte[] Hex(string text)
    {var bytes=new byte[text.Length/2];for(int i=0;i<bytes.Length;i++)bytes[i]=Convert.ToByte(text.Substring(i*2,2),16);return bytes;}
    private static string Hex(byte[] bytes)=>BitConverter.ToString(bytes).Replace("-","").ToLowerInvariant();
    private static string Hex(short[] field)
    {var bytes=new byte[field.Length*2];for(int i=0;i<field.Length;i++){bytes[2*i]=unchecked((byte)field[i]);bytes[2*i+1]=unchecked((byte)(field[i]>>8));}return Hex(bytes);}
    private static void Planning(string[] f)
    {
        Reset(0);int peer=int.Parse(f[1])-11;short group=short.Parse(f[2]);byte state=byte.Parse(f[3]);uint tag=uint.Parse(f[4]);byte retry=byte.Parse(f[5]);
        var cache=new List<int>();if(f[6].Length!=0)foreach(string cell in f[6].Split(','))cache.Add(int.Parse(cell));
        ShipPlanningOccupant View(object owner)
        {for(int i=0;i<8;i++)if(ReferenceEquals(owner,Owners[i]))return new ShipPlanningOccupant(i==peer?tag:Classes[i],i==peer?state:(byte)0,i==peer?group:i==0?(short)0:(short)-1);throw new Exception("Unknown owner");}
        var result=ShipReplanPlanner.PlanLive(grid,Owners[0],16,2,16,2,20,4,0,retry,true,0,View,uint.MaxValue,cache.ToArray());
        Console.WriteLine(string.Join("\t",new object[]{"P",Hex(result.CapturePoints()),Hex(result.CapturePlanningField()),Hex(result.CaptureWorkingField()),string.Join(",",result.CaptureCachedObstacles()),result.RandomStateAfter,result.PointCount,result.UsedNearest?1:0,result.ReachedWithinRange?1:0}));
    }
    private static ShipNavigationOccupant Describe(object owner)
    {
        for(int i=0;i<8;i++)if(ReferenceEquals(owner,Owners[i]))return new ShipNavigationOccupant(Classes[i],i<3?Motion[i].Current.Motion.State:(byte)0);
        throw new Exception("Unknown owner");
    }
    private static void Reset(uint seed)
    {
        byte[] raw=File.ReadAllBytes("tests/fixtures/mission_cell_flags.bin");var flags=new uint[576];Buffer.BlockCopy(raw,0,flags,0,raw.Length);
        grid=new MissionOccupancyGrid(24,24,flags);
        for(int i=0;i<8;i++){Owners[i]=new Owner();if(!grid.TryClaim(Cells[i,0],Cells[i,1],Owners[i]))throw new Exception("claim");}
        for(int i=0;i<8;i++)Groups[i]=-1;
        for(int i=0;i<3;i++){int index=i;Motion[i]=ShipMoveOrder.CreateLiveLocal(grid,Owners[i],Seeds[i],Describe,()=>Groups[index],DescribePlanning,seed);}
    }
    private static void Emit(int index)
    {
        var body=Motion[index];var s=body.Current;var m=s.Motion;var pubs=new List<string>();
        for(int i=0;i<body.LastStepPublicationCount;i++){var p=body.GetLastStepPublication(i);pubs.Add(string.Join(",",p.Frame,p.WorldPixelX,p.WorldPixelY,p.Depth));}
        var changes=new List<string>();
        var flags=BindingFlags.Instance|BindingFlags.NonPublic;
        int count=(int)typeof(ShipMoveOrder).GetProperty("LastStepGridMutationCount",flags).GetValue(body);
        for(int i=0;i<count;i++)
        {
            object entry=typeof(ShipMoveOrder).GetMethod("GetLastStepGridMutation",flags).Invoke(body,new object[]{i});
            int cell=(int)entry.GetType().GetProperty("CellIndex",flags).GetValue(entry);
            bool occupied=(bool)entry.GetType().GetProperty("Occupied",flags).GetValue(entry);
            changes.Add(cell+","+(occupied?Ids[index]:0));
        }
        var claims=new List<string>();
        for(int y=0;y<24;y++)for(int x=0;x<24;x++)
        {object owner=grid.GetOccupant(x,y);if(owner==null)continue;int id=-1;for(int i=0;i<8;i++)if(ReferenceEquals(owner,Owners[i]))id=Ids[i];claims.Add((y*24+x)+","+id);}
        Console.WriteLine(string.Join("\t",new object[]{Ids[index],m.CellX,m.CellY,m.WorldPixelX,m.WorldPixelY,m.State,m.CenterGate?1:0,m.Heading,m.TargetHeading,m.TurnStep,
            m.Speed,m.Remainder,m.Deceleration,m.ReservedCellIndex,m.NextCellIndex,m.LastCellIndex,m.PathIndex,m.PathCount,m.StoredFrame,m.LastFrameTick,m.LastStateCounter,s.RandomState,
            body.CurrentAcceleration,s.Retry,body.LastStepReachedForwardTail?1:0,m.DrawnFrame,m.PublishedWorldX,m.PublishedWorldY,string.Join(";",pubs),string.Join(";",changes),string.Join(";",claims),s.PendingFlags,s.ActiveFlags,s.DeferredFlags,s.StopMask,s.ReadyMask,s.Capabilities,s.RequestedGoalX,s.RequestedGoalY,s.TargetX,s.TargetY,s.FirstNavigation?1:0,s.LastPlanCounter,s.RetryInterval,s.NavigationRadius,s.SnapshotRetry,s.SnapshotTargetX,s.SnapshotTargetY,s.SnapshotCellX,s.SnapshotCellY,Hex(body.CaptureRoutePoints()),string.Join(",",body.CaptureCachedObstacles()),Hex(body.CapturePendingMoveRecord()),Groups[index],body.MoveBlockingGate}));
    }
    private static int controls;
    private static void Check(bool value){if(!value)throw new Exception("API failed "+controls);controls++;}
    private static void Reject<T>(Action action)where T:Exception
    {try{action();}catch(T){controls++;return;}throw new Exception("Expected "+typeof(T).Name);}
    private static ShipPlanningResult Plan(int[] cache=null,short group=-1)=>
        ShipReplanPlanner.PlanLive(grid,Owners[0],16,2,16,2,18,5,0,0,false,group,DescribePlanning,0,cache);
    //4e2ba0/4a9e30 receiver bounds and observable overwrite/promotion semantics.
    private static byte[] FirstRecord;
    //Managed bounds around the source4e2180 record projection.
    private static void Guards()
    {
        Reset(0);var body=Motion[0];
        Reject<ArgumentNullException>(()=>body.RestoreSourceMovementState(null,1));
        Reject<ArgumentException>(()=>body.RestoreSourceMovementState(new byte[10],1));
        var bad=(byte[])FirstRecord.Clone();bad[0x18]=12;
        Reject<NotSupportedException>(()=>body.RestoreSourceMovementState(bad,1));
        bad=(byte[])FirstRecord.Clone();bad[0x214]|=16;
        Reject<NotSupportedException>(()=>body.RestoreSourceMovementState(bad,1));
        bad=(byte[])FirstRecord.Clone();bad[0x26]=0;bad[0x27]=0;
        Reject<InvalidOperationException>(()=>body.RestoreSourceMovementState(bad,1));
        bad=(byte[])FirstRecord.Clone();bad[0x1c]=2;
        Reject<NotSupportedException>(()=>body.RestoreSourceMovementState(bad,1));
        var prepared=ShipMoveOrder.CreatePreparedLocal(grid,Owners[0],Seeds[0],Describe);
        Reject<NotSupportedException>(()=>prepared.RestoreSourceMovementState(FirstRecord,1));
        Check(body.Current.SourceCounter==0&&body.Current.ActiveFlags==0);
        body.RestoreSourceMovementState(FirstRecord,1);Check(body.Current.SourceCounter==1);
        bad=(byte[])FirstRecord.Clone();bad[0x542]=255;
        body.RestoreSourceMovementState(bad,1);bad[0x542]=0;Check(body.MoveBlockingGate==255);
        Console.WriteLine("API\t"+controls);
    }
    private static void Main(string[] arguments)
    {
        string line;
        while((line=Console.ReadLine())!=null)
        {
            string[] f=line.Split('\t');
            if(f[0]=="SEED"){int i=int.Parse(f[1])-11;Payloads[i]=Hex(f[2]);if(!MissionShipSeed.TryRead(new MissionObjectSeed("OBJ_"+(i+11).ToString("x8"),Payloads[i]),out Seeds[i]))throw new Exception("seed");}
            else if(f[0]=="START")Reset(uint.Parse(f[1]));
            else if(f[0]=="R"){int i=int.Parse(f[1])-11;Motion[i].ReceiveNormalCellMove((uint)(i+11),int.Parse(f[2]),int.Parse(f[3]),byte.Parse(f[4]));Emit(i);}
            else if(f[0]=="G")Groups[int.Parse(f[1])-11]=short.Parse(f[2]);
            else if(f[0]=="I")Emit(int.Parse(f[1])-11);
            //Explicit preexisting actor context for omitted265,not a production setter.
            else if(f[0]=="DEFER")typeof(ShipMoveOrder).GetField("deferredFlags",BindingFlags.Instance|BindingFlags.NonPublic).SetValue(Motion[int.Parse(f[1])-11],uint.Parse(f[2]));
            else if(f[0]=="WARM"){int i=int.Parse(f[1])-11;Motion[i].ReceiveNormalCellMove((uint)(i+11),int.Parse(f[3]),int.Parse(f[4]));for(uint t=1;t<=uint.Parse(f[2]);t++)Motion[i].Tick(t);}
            else if(f[0]=="RESTORE"){int i=int.Parse(f[1])-11;var raw=Hex(f[3]);if(FirstRecord==null)FirstRecord=(byte[])raw.Clone();Motion[i].RestoreSourceMovementState(raw,uint.Parse(f[2]));Emit(i);}
            else if(f[0]=="CONTEXT"){
                for(int y=0;y<24;y++)for(int x=0;x<24;x++){object o=grid.GetOccupant(x,y);if(o!=null)grid.Release(x,y,o);}
                foreach(string pair in f[1].Split(';')){string[] p=pair.Split(',');int c=int.Parse(p[0]),id=int.Parse(p[1]);grid.TryClaim(c%24,c/24,Owners[Array.IndexOf(Ids,id)]);}
            }
            else if(f[0]=="T"){int i=int.Parse(f[1])-11;Motion[i].Tick(uint.Parse(f[2]),int.Parse(f[3]));Emit(i);}
            else if(f[0]=="P")Planning(f);
            else throw new Exception("operation");
        }
        if(arguments.Length!=0)Guards();
    }
}
