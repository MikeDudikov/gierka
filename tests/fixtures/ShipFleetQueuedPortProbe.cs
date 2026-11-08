using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using AncientConquest.Simulation;

// Test-only adapter for explicit x86 operations;not a second task implementation.
class ShipFleetQueuedPortProbe
{
    static readonly uint[] Local = { 11, 12, 13 };
    static ShipFleetNormalTask.Member[] Registry() => new[] {
        new ShipFleetNormalTask.Member(11,16,2),new ShipFleetNormalTask.Member(12,21,5),new ShipFleetNormalTask.Member(13,19,4) };
    static string Hex(byte[] b) => BitConverter.ToString(b).Replace("-", "").ToLowerInvariant();
    // Matches oracle's explicitly labelled input write to group+8. No shipping setter.
    static void SetAge(ShipFleetMembership f, uint age)
    {
        if (f.GroupCount == 0) return;
        var groups = (IList)typeof(ShipFleetMembership).GetField("groups", BindingFlags.NonPublic | BindingFlags.Instance).GetValue(f);
        object group = groups[0]; group.GetType().GetField("Age", BindingFlags.NonPublic | BindingFlags.Instance).SetValue(group, age);
    }
    // Logical projection only:opaque task/marker pointers and marker graphics are excluded.
    static string Snapshot(ShipFleetMembership f, int before, bool emitted, string value, uint inactiveAge = 0)
    {
        var points=new List<string>(); var members=new List<string>(); var events=new List<string>();
        var actors=new List<string>(); var groups=new List<string>(); var packets=new List<string>(); string header="-";
        for(int i=0;i<f.ActorCount;i++) actors.Add(string.Join(",",new object[]{f.GetActorId(i),f.GetUiGroup(i),f.GetSimulationGroup(i),f.GetMemberIndex(i)}));
        for(int g=0;g<f.GroupCount;g++)
        {
            var ids=new List<int>();for(int j=0;j<f.GetGroupMemberCount(g);j++)ids.Add(f.GetGroupMemberRegistryIndex(g,j));
            groups.Add(f.GetGroupMode(g)+":"+f.GetGroupSerial(g)+":"+string.Join(",",ids));
        }
        uint age=f.GroupCount==0?inactiveAge:f.GetGroupWorkAge(0);
        if(f.GroupCount>0)
        {
            if(f.GetTaskSubtype(0)!=0) header=string.Join(",",new object[]{100,f.GetTaskSubtype(0),f.GetNormalTaskRequestedAt(0),
                unchecked((uint)f.GetNormalTaskGoalX(0)),unchecked((uint)f.GetNormalTaskGoalY(0)),1,0});
            for(int i=0;i<f.GetQueuedPointCount(0);i++){var p=f.GetQueuedPoint(0,i);points.Add(p.X+","+p.Y);}
            for(int i=0;i<f.GetQueuedMemberCount(0);i++){var m=f.GetQueuedMember(0,i);members.Add(m.InstanceId+","+m.Mode+","+m.X+","+m.Y);}
            for(int i=0;i<f.GetGroupEventCount(0);i++)events.Add(Hex(f.GetGroupEvent(0,i).CaptureRecord()));
        }
        for(int i=before;i<f.CommandCount;i++){var c=f.GetCommand(i);packets.Add(c.InstanceId+":41:"+Hex(c.CapturePayload()));}
        if(emitted)for(int i=0;i<f.GetTaskCommandCount(0);i++){var c=f.GetTaskCommand(0,i);packets.Add(c.InstanceId+":"+c.Action+":"+Hex(c.CapturePayload()));}
        return string.Join("\t",new object[]{age,header,string.Join(";",points),string.Join(";",members),string.Join(";",events),
            f.CurrentGroup,string.Join("/",groups),string.Join(";",actors),f.ConsumedCommandCount,string.Join(";",packets),value});
    }
    static int controls;
    static void Check(bool value){if(!value)throw new Exception("API control "+controls);controls++;}
    static void Reject<T>(Action action,ShipFleetMembership f)where T:Exception
    {
        string before=Snapshot(f,0,true,"-");
        try{action();}catch(T){Check(before==Snapshot(f,0,true,"-"));return;}
        throw new Exception("Expected "+typeof(T));
    }
    static void Api()
    {
        var f=new ShipFleetMembership(Local);var r=Registry();var map=new short[576];
        f.CommitPending(Local);f.RequestQueuedMove(0,r,24,24,18,6,1);
        Check(f.GetTaskSubtype(0)==2&&!f.HasNormalTask(0)&&f.GetQueuedMemberCount(0)==3&&f.GetTaskCommandCount(0)==3);
        Reject<NotSupportedException>(()=>f.ValidateNormalTaskScheduling(),f);
        Reject<NotSupportedException>(()=>f.WorkNormalTask(0,r,map,24,24,1),f);
        Reject<ArgumentNullException>(()=>f.WorkQueuedTask(0,r,map,24,24,null,2,1),f);
        Reject<ArgumentException>(()=>f.WorkQueuedTask(0,r,map,24,24,new short[2],2,1),f);
        Reject<ArgumentOutOfRangeException>(()=>f.RequestQueuedMove(0,r,24,24,-1,6,1),f);
        Reject<ArgumentException>(()=>f.RequestQueuedMove(0,new[]{r[1],r[0],r[2]},24,24,18,6,1),f);
        Reject<NotSupportedException>(()=>f.CommitPending(new uint[]{11},2,r),f);
        Reject<NotSupportedException>(()=>f.RemoveFromGroup(11,2,r),f);
        f.RequestQueuedMove(0,r,24,24,16,4,3);f.RequestQueuedMove(0,r,24,24,18,6,4);
        Check(f.GetQueuedPointCount(0)==2&&f.GetTaskCommandCount(0)==0&&f.GetNormalTaskRequestedAt(0)==4);
        SetAge(f,101);
        Reject<ArgumentNullException>(()=>f.WorkQueuedTask(0,r,null,24,24,new short[3],5,1),f);
        var bad=(short[])map.Clone();bad[0]=1;
        Reject<NotSupportedException>(()=>f.WorkQueuedTask(0,r,bad,24,24,new short[3],5,1),f);
        var interrupted=Registry();interrupted[0]=new ShipFleetNormalTask.Member(11,16,2,0,true);
        Reject<NotSupportedException>(()=>f.WorkQueuedTask(0,interrupted,map,24,24,new short[3],5,1),f);
        // Per-allocation signed context must follow member order independently.
        f.WorkQueuedTask(0,r,map,24,24,new short[]{32767,-32768,0},5,1);
        Check(f.GetTaskCommandCount(0)==2&&f.GetTaskCommand(0,0).InstanceId==12&&f.GetGroupWorkAge(0)==1);
        f.NotifyMemberAdded(0,11,6);
        Reject<NotSupportedException>(()=>f.WorkQueuedTask(0,r,map,24,24,new short[3],6,1),f);
        f.RequestNormalMove(0,r,map,24,24,18,5,7);
        Check(f.HasNormalTask(0)&&f.GetQueuedPointCount(0)==0&&f.GetQueuedMemberCount(0)==0&&f.GetGroupEventCount(0)==0&&f.GetGroupWorkAge(0)==1);
        f.ValidateNormalTaskScheduling();Check(true);
        f.RequestQueuedMove(0,r,24,24,18,6,8);f.ClearNormalTask(0);
        Check(f.GetTaskSubtype(0)==0&&f.GetQueuedPointCount(0)==0&&f.GetQueuedMemberCount(0)==0&&f.GetGroupWorkAge(0)==1);
        // Pure task guards also retain events and prior emissions on rejection.
        var task=new ShipFleetNormalTask();task.RequestQueued(24,24,r,18,6,0);task.MemberRemoved(1,0,11,16,2);
        try{task.WorkQueued(map,24,24,r,Local,new short[3],1,101,1);throw new Exception("311 accepted");}
        catch(NotSupportedException){Check(task.EventCount==1&&task.CommandCount==3);}
        Console.WriteLine("API\t"+controls);
    }
    static void Main(string[] args)
    {
        if(args.Length!=0){Api();return;}
        var maps=new Dictionary<string,short[]>();ShipFleetMembership f=null;ShipFleetNormalTask.Member[] registry=null;
        uint[] selection=null;short[] prefixes=null;uint inactiveAge=0;string active="mission",line;
        while((line=Console.ReadLine())!=null)
        {
            string[] p=line.Split('\t');
            if(p[0]=="MAP"){byte[] raw=Convert.FromBase64String(p[2]);var map=new short[raw.Length/2];Buffer.BlockCopy(raw,0,map,0,raw.Length);maps.Add(p[1],map);continue;}
            if(p[0]=="CASE"){f=new ShipFleetMembership(Local);registry=Registry();selection=null;prefixes=new short[3];inactiveAge=0;active="mission";continue;}
            if(p[0]=="CONTEXT"){active=p[1];for(int i=0;i<3;i++)prefixes[i]=short.Parse(p[i+2]);continue;}
            if(p[0]=="WAVE")
            {var wave=(short[])maps[p[1]].Clone();SourceWaveField.FillQueuedRoute(wave,24,24,int.Parse(p[2]),int.Parse(p[3]));var bytes=new byte[1152];Buffer.BlockCopy(wave,0,bytes,0,1152);Console.WriteLine(Convert.ToBase64String(bytes));continue;}
            int before=f.CommandCount;bool emitted=false;string value="-";
            if(p[0]=="select"){selection=new uint[p.Length-1];for(int i=0;i<selection.Length;i++)selection[i]=uint.Parse(p[i+1]);}
            else if(p[0]=="click"||p[0]=="shift")
            {
                uint counter=uint.Parse(p[3]);
                if(f.GroupCount==0)f.CommitPending(selection,counter,registry);
                if(p[0]=="click")f.RequestNormalMove(0,registry,maps[active],24,24,int.Parse(p[1]),int.Parse(p[2]),counter);
                else f.RequestQueuedMove(0,registry,24,24,int.Parse(p[1]),int.Parse(p[2]),counter);
                emitted=true;
            }
            else if(p[0]=="age"){inactiveAge=uint.Parse(p[1]);SetAge(f,inactiveAge);}
            else if(p[0]=="work")
            {
                if(f.GetTaskSubtype(0)==2)
                {var words=new short[f.GetGroupMemberCount(0)];for(int i=0;i<words.Length;i++)words[i]=prefixes[f.GetGroupMemberRegistryIndex(0,i)];
                 f.WorkQueuedTask(0,registry,maps[active],24,24,words,uint.Parse(p[2]),uint.Parse(p[1]));}
                else f.WorkNormalTask(0,registry,maps[active],24,24,uint.Parse(p[1]));
                emitted=true;
            }
            else if(p[0]=="pose"){int i=int.Parse(p[1])-11;registry[i]=new ShipFleetNormalTask.Member(uint.Parse(p[1]),int.Parse(p[2]),int.Parse(p[3]),byte.Parse(p[4]));}
            else if(p[0]=="arrival")f.NotifyMemberArrived(0,uint.Parse(p[1]),int.Parse(p[3])*24+int.Parse(p[2]),uint.Parse(p[4]));
            else if(p[0]=="next"){int cell=f.NextQueuedCell(0,24,int.Parse(p[1]),int.Parse(p[2]),sbyte.Parse(p[3]),out bool end);value=cell+","+(end?1:0);}
            else if(p[0]=="clear")f.ClearNormalTask(0);
            else throw new Exception(line);
            Console.WriteLine(Snapshot(f,before,emitted,value,inactiveAge));
        }
    }
}
