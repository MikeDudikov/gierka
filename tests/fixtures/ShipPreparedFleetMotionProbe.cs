using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using AncientConquest.World;
using AncientConquest.Simulation;

class ShipPreparedFleetMotionProbe
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
    private static byte[] Hex(string text)
    {var bytes=new byte[text.Length/2];for(int i=0;i<bytes.Length;i++)bytes[i]=Convert.ToByte(text.Substring(i*2,2),16);return bytes;}
    private static string Hex(byte[] bytes)=>BitConverter.ToString(bytes).Replace("-","").ToLowerInvariant();
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
        for(int i=0;i<3;i++)Motion[i]=ShipMoveOrder.CreatePreparedLocal(grid,Owners[i],Seeds[i],Describe,seed);
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
            body.CurrentAcceleration,s.Retry,body.LastStepReachedForwardTail?1:0,m.DrawnFrame,m.PublishedWorldX,m.PublishedWorldY,string.Join(";",pubs),string.Join(";",changes),string.Join(";",claims)}));
    }
    private static int controls;
    private static void Check(bool value){if(!value)throw new Exception("API failed "+controls);controls++;}
    private static void Reject<T>(Action action)where T:Exception
    {try{action();}catch(T){controls++;return;}throw new Exception("Expected "+typeof(T).Name);}
    private static void Guards()
    {
        Reset(0);
        Reject<ArgumentNullException>(()=>ShipMoveOrder.CreatePreparedLocal(null,Owners[0],Seeds[0],Describe));
        Reject<ArgumentNullException>(()=>ShipMoveOrder.CreatePreparedLocal(grid,null,Seeds[0],Describe));
        Reject<ArgumentNullException>(()=>ShipMoveOrder.CreatePreparedLocal(grid,Owners[0],Seeds[0],null));
        Reject<NotSupportedException>(()=>ShipMoveOrder.CreatePreparedLocal(new MissionOccupancyGrid(1,1,new uint[1]),Owners[0],Seeds[0],Describe));
        Reject<ArgumentException>(()=>ShipMoveOrder.CreatePreparedLocal(grid,new Owner(),Seeds[0],Describe));
        MissionShipSeed.TryRead(new MissionObjectSeed("OBJ_0000000e",Payloads[0]),out var wrong);
        Reject<NotSupportedException>(()=>ShipMoveOrder.CreatePreparedLocal(grid,Owners[0],wrong,Describe));
        byte[] damaged=(byte[])Payloads[2].Clone();damaged[60]=0;
        MissionShipSeed.TryRead(new MissionObjectSeed("OBJ_0000000d",damaged),out wrong);
        Reject<NotSupportedException>(()=>ShipMoveOrder.CreatePreparedLocal(grid,Owners[2],wrong,Describe));
        var body=Motion[0];
        Reject<ArgumentNullException>(()=>body.InstallPreparedRoute(null));
        Reject<ArgumentException>(()=>body.InstallPreparedRoute(new byte[5]));
        Reject<ArgumentException>(()=>body.InstallPreparedRoute(Hex("00000000000000010006")));
        Reject<ArgumentException>(()=>body.InstallPreparedRoute(Hex("10000200050f00030008")));
        Reject<NotSupportedException>(()=>body.InstallPreparedRoute(Hex("10000200050d00030005")));
        Check(!body.HasRoute && !body.CanRequestMove && body.Current.SourceCounter==0);
        byte[] route=Hex("10000200050f00030005");body.InstallPreparedRoute(route);route[0]=0;
        Check(body.CaptureRoutePoints()[0]==16 && body.Current.Motion.State==3);
        Reject<InvalidOperationException>(()=>body.InstallPreparedRoute(route));
        Reject<ArgumentException>(()=>body.Tick(0));
        Reject<ArgumentException>(()=>body.Tick(2));
        Reject<ArgumentOutOfRangeException>(()=>body.Tick(1,4));
        Reject<NotSupportedException>(()=>body.RequestCellMove(18,5));
        Check(Motion[2].CurrentAcceleration==884 && Motion[2].MaximumSpeed==52000 && Motion[2].LogicalSize==72 && Motion[2].Current.Motion.WorldPixelX==1212);
        var legacy=new ShipMoveOrder(grid,Owners[0],Seeds[0]);
        Reject<NotSupportedException>(()=>legacy.InstallPreparedRoute(Hex("10000200050f00030005")));
        Reset(0);Motion[0].Tick(1);
        Reject<InvalidOperationException>(()=>Motion[0].InstallPreparedRoute(Hex("10000200050f00030005")));
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
            else if(f[0]=="ROUTE")Motion[int.Parse(f[1])-11].InstallPreparedRoute(Hex(f[2]));
            else if(f[0]=="I")Emit(int.Parse(f[1])-11);
            else if(f[0]=="T"){int i=int.Parse(f[1])-11;Motion[i].Tick(uint.Parse(f[2]),int.Parse(f[3]));Emit(i);}
            else throw new Exception("operation");
        }
        if(arguments.Length!=0)Guards();
    }
}
