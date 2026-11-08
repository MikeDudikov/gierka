using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using AncientConquest.World;
using AncientConquest.Simulation;

class ShipWorldStepProbe
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
    private static ShipFleetMembership Membership;
    private static ShipWorldStep World;
    private static readonly List<ShipWorldStep.Command> Outgoing=new List<ShipWorldStep.Command>();
    private static uint Counter;
    private static int Phase;
    private static short[] Terrain;
    private static int[] ArrivalReplayOrder;
    private static short[] WaveWords;
    private static bool TraceArrivalEvents;
    private static short ReadGroup(int i)=>i<3?Membership.GetSimulationGroup(i):(short)-1;

    private static ShipPlanningOccupant DescribePlanning(object owner)
    {for(int i=0;i<8;i++)if(ReferenceEquals(owner,Owners[i]))return new ShipPlanningOccupant(Classes[i],i<3?Motion[i].Current.Motion.State:(byte)0,ReadGroup(i));throw new Exception("Unknown owner");}
    private static byte[] Hex(string text)
    {var bytes=new byte[text.Length/2];for(int i=0;i<bytes.Length;i++)bytes[i]=Convert.ToByte(text.Substring(i*2,2),16);return bytes;}
    private static string Hex(byte[] bytes)=>BitConverter.ToString(bytes).Replace("-","").ToLowerInvariant();
    private static string Hex(short[] field)
    {var bytes=new byte[field.Length*2];for(int i=0;i<field.Length;i++){bytes[2*i]=unchecked((byte)field[i]);bytes[2*i+1]=unchecked((byte)(field[i]>>8));}return Hex(bytes);}
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
        Membership=new ShipFleetMembership(new uint[]{11,12,13});
        for(int i=0;i<3;i++){int index=i;Motion[i]=ShipMoveOrder.CreateLiveLocal(grid,Owners[i],Seeds[i],Describe,()=>ReadGroup(index),DescribePlanning,seed);}
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
            body.CurrentAcceleration,s.Retry,body.LastStepReachedForwardTail?1:0,m.DrawnFrame,m.PublishedWorldX,m.PublishedWorldY,string.Join(";",pubs),string.Join(";",changes),string.Join(";",claims),s.PendingFlags,s.ActiveFlags,s.DeferredFlags,s.StopMask,s.ReadyMask,s.Capabilities,s.RequestedGoalX,s.RequestedGoalY,s.TargetX,s.TargetY,s.FirstNavigation?1:0,s.LastPlanCounter,s.RetryInterval,s.NavigationRadius,s.SnapshotRetry,s.SnapshotTargetX,s.SnapshotTargetY,s.SnapshotCellX,s.SnapshotCellY,Hex(body.CaptureRoutePoints()),string.Join(",",body.CaptureCachedObstacles()),Hex(body.CapturePendingMoveRecord()),ReadGroup(index)}));
    }

    //Source520c50 queue records,normalized without native pointers.
    private static string Packet(ShipWorldStep.Command p)=>p.InstanceId+":"+p.Action+":"+p.Counter+":"+Hex(p.CapturePayload());
    //Observe clock/mail/registry/task and ordered50d5f0 outputs after each branch.
    private static void WorldRow()
    {
        var visits=new List<int>();var received=new List<string>();var emitted=new List<string>();var outgoing=new List<string>();var pubs=new List<string>();
        var assignment=new List<string>();var events=new List<string>();
        for(int i=0;i<World.VisitCount;i++){int v=World.GetVisit(i);visits.Add(v<0?-1:Ids[v]);}
        for(int i=0;i<World.ReceivedCount;i++)received.Add(Packet(World.GetReceived(i)));
        for(int i=0;i<World.EmittedCount;i++)emitted.Add(Packet(World.GetEmitted(i)));
        foreach(var p in Outgoing)outgoing.Add(Packet(p));
        for(int i=0;i<World.PublicationCount;i++){var p=World.GetPublication(i);var v=p.Value;pubs.Add(string.Join(",",Ids[p.RegistryIndex],v.Frame,v.WorldPixelX,v.WorldPixelY,v.Depth));}
        for(int i=0;i<Membership.GetNormalTaskAssignmentCount(0);i++){var a=Membership.GetNormalTaskAssignment(0,i);assignment.Add(a.InstanceId+","+a.X+","+a.Y);}
        // Historical fixtures explicitly replaced4a1700 with ret;their observer
        //projects that older boundary. TRACE310 enables the strict full record.
        for(int i=0;i<Membership.GetGroupEventCount(0);i++)
        {var e=Membership.GetGroupEvent(0,i);if(TraceArrivalEvents||e.Code!=310)events.Add(Hex(e.CaptureRecord()));}
        Console.WriteLine(string.Join("\t",new object[]{"W",Counter,Phase,World.PreparationCounter,string.Join(",",visits),
            string.Join(";",received),string.Join(";",emitted),string.Join(";",outgoing),string.Join(";",pubs),
            Membership.GetGroupWorkAge(0),Membership.ConsumedCommandCount,string.Join(";",assignment),string.Join(";",events)}));
        for(int i=0;i<3;i++)Emit(i);
    }
    //Explicit source registry input,not original mission registration inferred from IDs.
    private static void Start(string[] f)
    {
        Reset(0);Counter=0;Phase=0;Outgoing.Clear();string[] order=f[2].Split(',');var slots=new int[order.Length];
        for(int i=0;i<slots.Length;i++){int id=int.Parse(order[i]);slots[i]=id<0?-1:id-11;}
        World=new ShipWorldStep(Membership,grid,Motion,slots,byte.Parse(f[1]));
        string[] selected=f[3].Split(',');var ids=new uint[selected.Length];for(int i=0;i<ids.Length;i++)ids[i]=uint.Parse(selected[i]);
        Membership.CommitPending(ids);
        for(int i=0;i<Membership.CommandCount;i++)Outgoing.Add(ShipWorldStep.Command.Membership(Counter,Membership.GetCommand(i)));
        var registry=new ShipFleetNormalTask.Member[3];for(int i=0;i<3;i++)registry[i]=new ShipFleetNormalTask.Member((uint)Ids[i],Cells[i,0],Cells[i,1]);
        Membership.RequestNormalMove(0,registry,Terrain,24,24,18,5,Counter);
        for(int i=0;i<Membership.GetNormalTaskCommandCount(0);i++)Outgoing.Add(ShipWorldStep.Command.Task(Counter,Membership.GetNormalTaskCommand(0,i)));
    }
    //Actual0x83 already-member path:49bd60 no-op then4a1340.
    private static void Notify()
    {
        var r=new ShipFleetNormalTask.Member[3];for(int i=0;i<3;i++){var m=Motion[i].Current.Motion;r[i]=new ShipFleetNormalTask.Member((uint)Ids[i],m.CellX,m.CellY,m.State);}
        Membership.AddToGroup(11,0,Counter,r);Membership.NotifyMemberAdded(0,11,Counter);
    }
    private static int controls;
    private static void Check(bool value){if(!value)throw new Exception("API failed "+controls);controls++;}
    private static void Reject<T>(Action action)where T:Exception
    {try{action();}catch(T){controls++;return;}throw new Exception("Expected "+typeof(T).Name);}
    //Managed projection guards and source mail boundaries,not invented ship behavior.
    private static void Api()
    {
        string[] start={"START","2","-1,11,12,13","11"};Start(start);var order=new[]{-1,0,1,2};
        Reject<ArgumentNullException>(()=>new ShipWorldStep(null,grid,Motion,order,2));
        Reject<ArgumentNullException>(()=>new ShipWorldStep(Membership,null,Motion,order,2));
        Reject<ArgumentNullException>(()=>new ShipWorldStep(Membership,grid,null,order,2));
        Reject<ArgumentNullException>(()=>new ShipWorldStep(Membership,grid,Motion,null,2));
        Reject<NotSupportedException>(()=>new ShipWorldStep(Membership,grid,Motion,new[]{0,1,2},2));
        Reject<ArgumentException>(()=>new ShipWorldStep(Membership,grid,Motion,new[]{-1,0,0,2},2));
        Reject<ArgumentException>(()=>new ShipWorldStep(Membership,grid,Motion,new[]{-1,0,1,3},2));
        Reject<ArgumentException>(()=>new ShipWorldStep(Membership,grid,new[]{Motion[1],Motion[0],Motion[2]},order,2));
        byte[] bytes=Outgoing[0].CapturePayload();bytes[0]=0;Check(Outgoing[0].CapturePayload()[0]==1);
        Check(!World.TryAdvance(39,ref Phase,ref Counter,Terrain,Outgoing)&&Counter==0&&Phase==0&&Outgoing.Count==2&&Membership.GetSimulationGroup(0)==-1);
        Check(World.TryAdvance(40,ref Phase,ref Counter,Terrain,Outgoing)&&Counter==1&&Phase==40&&Outgoing.Count==0&&(Motion[0].Current.ActiveFlags&128)!=0);
        Check(World.ReceivedCount==2&&World.GetReceived(0).Action==41&&World.GetReceived(1).Action==20);
        Start(start);Outgoing.Add(Outgoing[1]);
        Check(World.TryAdvance(40,ref Phase,ref Counter,Terrain,Outgoing)&&World.ReceivedCount==3);
        Check(Counter==1&&Phase==40&&Outgoing.Count==0&&Membership.GetSimulationGroup(0)==0);
        Start(start);Counter=5;Reject<InvalidOperationException>(()=>World.TryAdvance(40,ref Phase,ref Counter,Terrain,Outgoing));
        Start(start);Reject<ArgumentNullException>(()=>World.TryAdvance(40,ref Phase,ref Counter,Terrain,null));
        var t=new ShipFleetNormalTask();var members=new[]{new ShipFleetNormalTask.Member(11,16,2),new ShipFleetNormalTask.Member(12,21,5)};
        var blocked=new short[576];for(int i=0;i<blocked.Length;i++)blocked[i]=-1;
        t.Request(blocked,24,24,members,18,5,0);t.MemberAdded(0,0,11);t.Work(blocked,24,24,members,new uint[]{11,12},0,1);
        Outgoing.Clear();Outgoing.Add(ShipWorldStep.Command.Task(0,t.GetCommand(1)));
        Reject<NotSupportedException>(()=>World.TryAdvance(40,ref Phase,ref Counter,Terrain,Outgoing));
        Start(new[]{"START","0","-1,11,12,13","11"});World.TryAdvance(40,ref Phase,ref Counter,Terrain,Outgoing);
        Check(World.PreparationCounter==1&&World.ReceivedCount==0&&Outgoing.Count==2);
        World.TryAdvance(80,ref Phase,ref Counter,Terrain,Outgoing);Check(World.PreparationCounter==2&&World.ReceivedCount==0&&Outgoing.Count==2);
        World.TryAdvance(120,ref Phase,ref Counter,Terrain,Outgoing);Check(World.ReceivedCount==2&&Membership.GetSimulationGroup(0)==0&&Motion[0].Current.PendingFlags==0&&(Motion[0].Current.ActiveFlags&128)!=0);
        Console.WriteLine("API\t"+controls);
    }
    private static void Main(string[] arguments)
    {
        string line;
        while((line=Console.ReadLine())!=null)
        {
            string[] f=line.Split('\t');
            if(f[0]=="SEED"){int i=int.Parse(f[1])-11;Payloads[i]=Hex(f[2]);if(!MissionShipSeed.TryRead(new MissionObjectSeed("OBJ_"+(i+11).ToString("x8"),Payloads[i]),out Seeds[i]))throw new Exception("seed");}
            else if(f[0]=="MAP"){byte[] raw=Convert.FromBase64String(f[1]);Terrain=new short[raw.Length/2];Buffer.BlockCopy(raw,0,Terrain,0,raw.Length);}
            else if(f[0]=="START")Start(f);
            else if(f[0]=="TRACE310")TraceArrivalEvents=true;
            else if(f[0]=="WSTART")QueuedWorldStart(f);
            else if(f[0]=="USTART")
            {
                Start(new[]{"START",f[1],f[2],f[3]});string[] words=f[4].Split(',');WaveWords=new short[words.Length];
                for(int i=0;i<words.Length;i++)WaveWords[i]=short.Parse(words[i]);
            }
            else if(f[0]=="UR")UiWorldRequest(f);
            else if(f[0]=="WF"){World.TryAdvance(int.Parse(f[1]),ref Phase,ref Counter,Terrain,WaveWords,Outgoing);QueuedWorldRow();}
            else if(f[0]=="QSTART")ArrivalReplayStart(f);
            else if(f[0]=="QFRAME")ArrivalReplayFrame(f);
            else if(f[0]=="N")Notify();
            else if(f[0]=="F"){World.TryAdvance(int.Parse(f[1]),ref Phase,ref Counter,Terrain,Outgoing);WorldRow();}
            else throw new Exception(line);
        }
        if(arguments.Length!=0)
        {
            if(arguments[0]=="--queued-guard") QueuedGuard();
            else if(arguments[0]=="--integrated-api") IntegratedApi();
            else if(arguments[0]=="--arrival-api") ArrivalApi(); else Api();
        }
    }

    // Test input49de70 dispatch:requests the existing owner at held source
    //counter;no packet receipt,actor Work or time advance occurs on a click.
    private static void UiWorldRequest(string[] f)
    {
        var registry=new ShipFleetNormalTask.Member[3];
        for(int i=0;i<3;i++){var m=Motion[i].Current.Motion;registry[i]=new ShipFleetNormalTask.Member((uint)Ids[i],m.CellX,m.CellY,m.State);}
        int x=int.Parse(f[2]),y=int.Parse(f[3]);
        if(f[1]=="shift")Membership.RequestQueuedMove(0,registry,24,24,x,y,Counter);
        else Membership.RequestNormalMove(0,registry,Terrain,24,24,x,y,Counter);
        for(int i=0;i<Membership.GetTaskCommandCount(0);i++)Outgoing.Add(ShipWorldStep.Command.Task(Counter,Membership.GetTaskCommand(0,i)));
        QueuedWorldRow();
    }

    // Projection guards around520352/4cf550:bad memory/map/event inputs must
    //fail before clock/mail/actor/task mutations. Does not invent gameplay rules.
    private static void IntegratedApi()
    {
        int checkedCases=0;
        Action<string> setup=age=>QueuedWorldStart(new[]{"WSTART","0","11,12,13,-1","13,11","32767,117,-32768","16,2;18,6;16,4",age});
        Action<Action> reject=action=>
        {
            var output=Console.Out;var before=new StringWriter();Console.SetOut(before);QueuedWorldRow();Console.SetOut(output);
            bool failed=false;try{action();}catch(ArgumentException){failed=true;}catch(NotSupportedException){failed=true;}
            if(!failed)throw new Exception("Invalid integrated input accepted");
            var after=new StringWriter();Console.SetOut(after);QueuedWorldRow();Console.SetOut(output);
            if(before.ToString()!=after.ToString())throw new Exception("Integrated guard changed state");checkedCases++;
        };
        setup("101");reject(()=>World.TryAdvance(40,ref Phase,ref Counter,Terrain,(short[])null,Outgoing));
        reject(()=>World.TryAdvance(40,ref Phase,ref Counter,Terrain,new short[2],Outgoing));
        reject(()=>World.TryAdvance(40,ref Phase,ref Counter,(short[])null,WaveWords,Outgoing));
        reject(()=>World.TryAdvance(40,ref Phase,ref Counter,new short[1],WaveWords,Outgoing));
        var invalid=new short[576];invalid[0]=1;reject(()=>World.TryAdvance(40,ref Phase,ref Counter,invalid,WaveWords,Outgoing));
        reject(()=>World.TryAdvance(40,ref Phase,ref Counter,Terrain,Outgoing));
        setup("0");Membership.NotifyMemberAdded(0,13,0);
        reject(()=>World.TryAdvance(40,ref Phase,ref Counter,Terrain,WaveWords,Outgoing));
        setup("101");
        if(!World.TryAdvance(40,ref Phase,ref Counter,Terrain,WaveWords,Outgoing)||Counter!=1||Phase!=40||World.PreparationCounter!=1)
            throw new Exception("Integrated accepted branch failed");
        if(World.EmittedCount!=1||World.GetEmitted(0).InstanceId!=13||Membership.GetGroupWorkAge(0)!=1)
            throw new Exception("Registry prefix/member mapping failed");checkedCases++;
        reject(()=>World.TryAdvance(80,ref Phase,ref Counter,(short[])null,WaveWords,Outgoing));
        if(World.TryAdvance(79,ref Phase,ref Counter,Terrain,WaveWords,Outgoing)||Counter!=1||Phase!=40)
            throw new Exception("Integrated held branch failed");checkedCases++;
        Console.WriteLine("INTEGRATED_API\t"+checkedCases);
    }

    // Test-only49ca60/4cf2c0 request boundary,then the ACTUAL C#World owns all
    //later40ms mail/task/actor work. No x86 packets are supplied after startup.
    private static void QueuedWorldStart(string[] f)
    {
        Reset(0);Counter=0;Phase=0;Outgoing.Clear();
        string[] order=f[2].Split(',');var registration=new int[order.Length];
        for(int i=0;i<order.Length;i++){int id=int.Parse(order[i]);registration[i]=id<0?-1:id-11;}
        World=new ShipWorldStep(Membership,grid,Motion,registration,byte.Parse(f[1]));
        string[] words=f[4].Split(',');WaveWords=new short[words.Length];
        for(int i=0;i<words.Length;i++)WaveWords[i]=short.Parse(words[i]);
        string[] selection=f[3].Split(',');var ids=new uint[selection.Length];
        for(int i=0;i<ids.Length;i++)ids[i]=uint.Parse(selection[i]);Membership.CommitPending(ids);
        for(int i=0;i<Membership.CommandCount;i++)Outgoing.Add(ShipWorldStep.Command.Membership(0,Membership.GetCommand(i)));
        var registry=new ShipFleetNormalTask.Member[3];
        for(int i=0;i<3;i++)registry[i]=new ShipFleetNormalTask.Member((uint)Ids[i],Cells[i,0],Cells[i,1]);
        foreach(string point in f[5].Split(';'))
        {
            string[] p=point.Split(',');Membership.RequestQueuedMove(0,registry,24,24,int.Parse(p[0]),int.Parse(p[1]),0);
            for(int i=0;i<Membership.GetTaskCommandCount(0);i++)Outgoing.Add(ShipWorldStep.Command.Task(0,Membership.GetTaskCommand(0,i)));
        }
        // Corresponds ONLY to the labelled source input write to group+8.
        if(f[6]!="-")
        {
            var groups=(System.Collections.IList)typeof(ShipFleetMembership).GetField("groups",BindingFlags.Instance|BindingFlags.NonPublic).GetValue(Membership);
            object group=groups[0];group.GetType().GetField("Age",BindingFlags.Instance|BindingFlags.NonPublic).SetValue(group,uint.Parse(f[6]));
        }
    }

    // Complete4cf550 route/events plus clock,source2e FIFO and ordered publications.
    private static void QueuedWorldRow()
    {
        var visits=new List<int>();var received=new List<string>();var emitted=new List<string>();var outgoing=new List<string>();var pubs=new List<string>();
        var slots=new List<int>();var events=new List<string>();var points=new List<string>();var members=new List<string>();
        var assignments=new List<string>();
        for(int i=0;i<World.VisitCount;i++){int v=World.GetVisit(i);visits.Add(v<0?-1:Ids[v]);}
        for(int i=0;i<World.ReceivedCount;i++)received.Add(Packet(World.GetReceived(i)));
        for(int i=0;i<World.EmittedCount;i++)emitted.Add(Packet(World.GetEmitted(i)));
        foreach(var p in Outgoing)outgoing.Add(Packet(p));
        for(int i=0;i<World.PublicationCount;i++){var p=World.GetPublication(i);var v=p.Value;pubs.Add(string.Join(",",Ids[p.RegistryIndex],v.Frame,v.WorldPixelX,v.WorldPixelY,v.Depth));}
        for(int i=0;i<Membership.GetGroupMemberCount(0);i++)slots.Add(Membership.GetGroupMemberRegistryIndex(0,i));
        for(int i=0;i<Membership.GetGroupEventCount(0);i++)events.Add(Hex(Membership.GetGroupEvent(0,i).CaptureRecord()));
        for(int i=0;i<Membership.GetQueuedPointCount(0);i++){var p=Membership.GetQueuedPoint(0,i);points.Add(p.X+","+p.Y);}
        for(int i=0;i<Membership.GetQueuedMemberCount(0);i++){var m=Membership.GetQueuedMember(0,i);members.Add(m.InstanceId+","+m.Mode+","+m.X+","+m.Y);}
        for(int i=0;i<Membership.GetNormalTaskAssignmentCount(0);i++){var a=Membership.GetNormalTaskAssignment(0,i);assignments.Add(a.InstanceId+","+a.X+","+a.Y);}
        string header=string.Join(",",new object[]{100,Membership.GetTaskSubtype(0),Membership.GetNormalTaskRequestedAt(0),Membership.GetNormalTaskGoalX(0),Membership.GetNormalTaskGoalY(0),1,0});
        Console.WriteLine(string.Join("\t",new object[]{"K",Counter,Phase,World.PreparationCounter,string.Join(",",visits),
            string.Join(";",received),string.Join(";",emitted),string.Join(";",outgoing),string.Join(";",pubs),Membership.GetGroupWorkAge(0),
            Membership.ConsumedCommandCount,header,string.Join(",",slots),string.Join(";",events),string.Join(";",points),
            Membership.GetQueuedMemberCount(0),string.Join(";",members),string.Join(";",assignments)}));
        for(int i=0;i<3;i++){Emit(i);ArrivalRow(i,World.VisitCount!=0);}
    }

    //520352 accepted branch/4c4f40:unrepresented100/2 world context must fail
    //before counter,phase,mail,membership,grid or any actor is advanced.
    private static void QueuedGuard()
    {
        Start(new[]{"START","2","11,-1,12,13","11,12,13"});
        var registry=new ShipFleetNormalTask.Member[3];
        for(int i=0;i<3;i++)registry[i]=new ShipFleetNormalTask.Member((uint)Ids[i],Cells[i,0],Cells[i,1]);
        Membership.RequestQueuedMove(0,registry,24,24,18,6,0);
        var output=Console.Out;var before=new StringWriter();
        Console.SetOut(before);WorldRow();Console.SetOut(output);
        int count=Outgoing.Count;
        try{World.TryAdvance(40,ref Phase,ref Counter,Terrain,Outgoing);throw new Exception("Queued world accepted");}
        catch(NotSupportedException){ }
        if(Counter!=0||Phase!=0||World.PreparationCounter!=2||Outgoing.Count!=count||Membership.ConsumedCommandCount!=0||
            Membership.GetGroupWorkAge(0)!=0||World.VisitCount!=0||World.ReceivedCount!=0||World.EmittedCount!=0||World.PublicationCount!=0)
            throw new Exception("Queued world changed state");
        var after=new StringWriter();Console.SetOut(after);WorldRow();Console.SetOut(output);
        if(before.ToString()!=after.ToString())throw new Exception("Queued guard changed actor/grid/world snapshots");
        Console.WriteLine("QUEUED_WORLD_GUARD_OK");
    }

    // Test-only49ca60/50c970 identity boundary. NO C#task/World execution:
    //the source100/2 world's immutable delivery stream drives the actor kernel.
    private static void ArrivalReplayStart(string[] f)
    {
        Reset(0);Counter=0;Phase=0;Outgoing.Clear();
        string[] order=f[1].Split(',');ArrivalReplayOrder=new int[order.Length];
        for(int i=0;i<order.Length;i++){int id=int.Parse(order[i]);ArrivalReplayOrder[i]=id<0?-1:id-11;}
        string[] selected=f[2].Split(',');var ids=new uint[selected.Length];
        for(int i=0;i<ids.Length;i++)ids[i]=uint.Parse(selected[i]);Membership.CommitPending(ids);
        for(int i=0;i<3;i++){Emit(i);ArrivalRow(i,false);}
    }

    // Test-only522850 ->source4ab720/4ab930 replay. Fleet callbacks do not run
    //in this adapter;their actual x86 packets are compared as explicit inputs.
    private static void ArrivalReplayFrame(string[] f)
    {
        Counter=uint.Parse(f[1]);bool accepted=f[2]=="1";
        if(accepted)
        {
            if(f[3]!="-")foreach(string text in f[3].Split(';'))
            {
                string[] p=text.Split(':');int index=int.Parse(p[0])-11;byte action=byte.Parse(p[1]);byte[] raw=Hex(p[2]);
                if(action==41)
                {
                    var next=Membership.GetCommand(Membership.ConsumedCommandCount);
                    if(next.InstanceId!=(uint)Ids[index]||Hex(next.CapturePayload())!=p[2]||!Membership.ConsumeNext())throw new Exception("Source41 FIFO differs");
                }
                else if(action==20)
                {
                    if(!Motion[index].ReceiveNormalCellMove((uint)Ids[index],BitConverter.ToInt32(raw,0),BitConverter.ToInt32(raw,4),raw[8]))
                        throw new Exception("Source20 capability differs");
                }
                else throw new Exception("Unrepresented replay action");
            }
            foreach(int index in ArrivalReplayOrder)if(index>=0)Motion[index].Tick(Counter,1);
        }
        for(int i=0;i<3;i++){Emit(i);ArrivalRow(i,accepted);}
    }

    // Observes4a1700 counter+4/cell+10 after4a49af or4a4a67,not a guessed
    //target-reached predicate. Source membership/group events are not synthesized.
    private static void ArrivalRow(int index,bool accepted)
    {
        var rows=new List<string>();
        if(accepted)for(int i=0;i<Motion[index].LastStepArrivalCount;i++)
        {var a=Motion[index].GetLastStepArrival(i);rows.Add(a.Counter+","+a.CellIndex);}
        Console.WriteLine("A\t"+Ids[index]+"\t"+string.Join(";",rows));
    }

    // Managed bounds on the4a1700 effect observation;not original gameplay logic.
    private static void ArrivalApi()
    {
        Reset(0);
        int rejected=0;
        foreach(int index in new[]{-1,0})
            try{Motion[0].GetLastStepArrival(index);throw new Exception("Arrival index accepted");}
            catch(ArgumentOutOfRangeException){rejected++;}
        Console.WriteLine("ARRIVAL_API\t"+rejected);
    }
}
