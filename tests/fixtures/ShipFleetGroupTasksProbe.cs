using System;
using System.Collections.Generic;
using AncientConquest.Simulation;

class ShipFleetGroupTasksProbe
{
    private static readonly uint[] Local = { 11, 12, 13 };
    // Source11/12/13 cells are input to4dc600/4cc970,not injected membership.
    private static ShipFleetNormalTask.Member[] Registry() => new[] {
        new ShipFleetNormalTask.Member(11,16,2),new ShipFleetNormalTask.Member(12,21,5),new ShipFleetNormalTask.Member(13,19,4) };
    private static string Hex(byte[] bytes) => BitConverter.ToString(bytes).Replace("-", "").ToLowerInvariant();
    // Observe the same group/task/actor fields as the x86 oracle;no behavior duplicated here.
    private static string Snapshot(ShipFleetMembership fleet, string result, int before, int emittedGroup)
    {
        var groups = new List<string>(); var actors = new List<string>(); var all = new List<string>(); var delta = new List<string>();
        for (int g = 0; g < fleet.GroupCount; g++)
        {
            var members = new List<int>(); var slots = new List<int>(); var assignments = new List<string>(); var events = new List<string>();
            for (int i = 0; i < fleet.GetGroupMemberCount(g); i++) members.Add(fleet.GetGroupMemberRegistryIndex(g,i));
            for (int i = 0; i < fleet.GetGroupRetainedSlotCount(g); i++) slots.Add(fleet.GetGroupRetainedSlotRegistryIndex(g,i));
            for (int i = 0; i < fleet.GetNormalTaskAssignmentCount(g); i++)
            { var a = fleet.GetNormalTaskAssignment(g,i); assignments.Add(a.InstanceId+","+a.X+","+a.Y); }
            for (int i = 0; i < fleet.GetGroupEventCount(g); i++) events.Add(Hex(fleet.GetGroupEvent(g,i).CaptureRecord()));
            string header = fleet.HasNormalTask(g) ? string.Join(",",new object[] {100,1,fleet.GetNormalTaskRequestedAt(g),
                unchecked((uint)fleet.GetNormalTaskGoalX(g)),unchecked((uint)fleet.GetNormalTaskGoalY(g)),1,0}) : "-";
            groups.Add(string.Join("~",new object[] {fleet.GetGroupMode(g),fleet.GetGroupSerial(g),fleet.GetGroupWorkAge(g),
                string.Join(",",members),string.Join(",",slots),header,string.Join(";",assignments),string.Join(";",events)}));
        }
        for (int i = 0; i < fleet.ActorCount; i++) actors.Add(string.Join(",",new object[] {
            fleet.GetActorId(i),fleet.GetUiGroup(i),fleet.GetSimulationGroup(i),fleet.GetMemberIndex(i)}));
        for (int i = 0; i < fleet.CommandCount; i++)
        { var c = fleet.GetCommand(i); string s = c.InstanceId+":41:"+Hex(c.CapturePayload()); all.Add(s); if (i >= before) delta.Add(s); }
        if (emittedGroup >= 0) for (int i = 0; i < fleet.GetNormalTaskCommandCount(emittedGroup); i++)
        { var c = fleet.GetNormalTaskCommand(emittedGroup,i); delta.Add(c.InstanceId+":"+c.Action+":"+Hex(c.CapturePayload())); }
        return string.Join("\t",new object[] {result,fleet.CurrentGroup,fleet.ConsumedCommandCount,
            string.Join("/",groups),string.Join(";",actors),string.Join(";",all),string.Join(";",delta)});
    }
    private static int controls;
    private static void Check(bool value) { if (!value) throw new Exception("API failed "+controls); controls++; }
    // Managed invalid-projection guards are outside x86's represented valid domain.
    private static void Reject<T>(Action action, ShipFleetMembership fleet) where T:Exception
    {
        string before = Snapshot(fleet,"-",fleet.CommandCount,-1);
        try { action(); } catch (T) { Check(before == Snapshot(fleet,"-",fleet.CommandCount,-1)); return; }
        throw new Exception("Expected "+typeof(T).Name);
    }
    private static void Api()
    {
        var f = new ShipFleetMembership(Local); var r = Registry(); var map = new short[576];
        f.CommitPending(new uint[]{11,12}); f.CommitPending(new uint[]{13});
        Check(!f.NotifyMemberAdded(0,11,1) && f.GetGroupEventCount(0) == 0);
        f.WorkNormalTask(0,null,null,0,0,100); Check(f.GetGroupWorkAge(0) == 0);
        Reject<ArgumentNullException>(()=>f.RequestNormalMove(0,null,map,24,24,18,5,1),f);
        Reject<ArgumentException>(()=>f.RequestNormalMove(0,new[]{r[0]},map,24,24,18,5,1),f);
        Reject<ArgumentException>(()=>f.RequestNormalMove(0,new[]{r[1],r[0],r[2]},map,24,24,18,5,1),f);
        f.RequestNormalMove(0,r,map,24,24,18,5,1);
        Check(f.HasNormalTask(0) && !f.HasNormalTask(1) && f.GetNormalTaskCommandCount(0) == 2);
        Reject<NotSupportedException>(()=>f.CommitPending(new uint[]{11}),f);
        Reject<NotSupportedException>(()=>f.AddToGroup(11,1,2,null),f);
        Reject<NotSupportedException>(()=>f.RemoveFromGroup(11,2,null),f);
        Reject<ArgumentException>(()=>f.AddToGroup(11,1,2,new[]{r[1],r[0],r[2]}),f);
        Reject<ArgumentException>(()=>f.AddToGroup(999,1,2,r),f);
        Reject<ArgumentOutOfRangeException>(()=>f.AddToGroup(11,2,2,r),f);
        int packets = f.CommandCount;
        Check(f.AddToGroup(11,0,3,null) == 0 && f.CommandCount == packets);
        Check(f.NotifyMemberAdded(0,11,3) && f.GetGroupEventCount(0) == 1);
        byte[] record = f.GetGroupEvent(0,0).CaptureRecord(); record[0] = 0;
        Check(f.GetGroupEvent(0,0).CaptureRecord()[0] == 44);
        Check(f.RemoveFromGroup(11,4,r) == 0 && f.GetGroupEvent(0,1).Code == 311 && f.GetGroupEvent(0,1).MemberIndex == 0);
        Check(f.GetGroupMemberCount(0) == 1 && f.GetGroupRetainedSlotCount(0) == 2 && f.GetMemberIndex(1) == 0);
        Reject<ArgumentOutOfRangeException>(()=>f.GetGroupMemberRegistryIndex(0,1),f);
        Check(f.GetGroupRetainedSlotRegistryIndex(0,1) == 1 && f.GetSimulationGroup(0) == -1);
        Check(f.RemoveFromGroup(11,5,null) == 0);
        f.WorkNormalTask(0,r,map,24,24,100); Check(f.GetGroupWorkAge(0) == 100 && f.GetGroupEventCount(0) == 0);
        f.ClearNormalTask(0); Check(!f.HasNormalTask(0) && f.GetGroupWorkAge(0) == 100 && f.GetGroupRetainedSlotCount(0) == 2);
        Check(!f.NotifyMemberAdded(0,12,6));
        f.RequestNormalMove(0,r,map,24,24,18,5,7); f.WorkNormalTask(0,r,map,24,24,1);
        Check(f.GetGroupWorkAge(0) == 101 && f.GetNormalTaskRequestedAt(0) == 7);
        var interrupted = Registry(); interrupted[1] = new ShipFleetNormalTask.Member(12,21,5,0,true);
        Reject<NotSupportedException>(()=>f.WorkNormalTask(0,interrupted,map,24,24,1),f);
        Check(f.GetNormalTaskAssignment(0,0).InstanceId == 12);
        Console.WriteLine("API\t"+controls);
    }
    // Explicit source-equivalent phases only;no Update/Time/float or automatic delivery.
    private static void Main(string[] arguments)
    {
        if (arguments.Length != 0) { Api(); return; }
        var maps = new Dictionary<string,short[]>(); string active = "mission",line;
        ShipFleetMembership fleet = null; ShipFleetNormalTask.Member[] registry = null;
        while ((line = Console.ReadLine()) != null)
        {
            string[] p = line.Split('\t');
            if (p[0] == "MAP")
            { byte[] raw=Convert.FromBase64String(p[2]); var map=new short[raw.Length/2]; Buffer.BlockCopy(raw,0,map,0,raw.Length); maps.Add(p[1],map); continue; }
            if (p[0] == "CASE") { fleet=new ShipFleetMembership(Local); registry=Registry(); active="mission"; continue; }
            int before = fleet.CommandCount,emitted = -1; string result = "-";
            if (p[0] == "C")
            { var ids=new uint[p.Length-2]; for(int i=0;i<ids.Length;i++)ids[i]=uint.Parse(p[i+2]); result=fleet.CommitPending(ids,uint.Parse(p[1]),registry).ToString(); }
            else if (p[0] == "B") result=fleet.AddToGroup(uint.Parse(p[2]),int.Parse(p[1]),uint.Parse(p[3]),registry).ToString();
            else if (p[0] == "D") result=fleet.RemoveFromGroup(uint.Parse(p[1]),uint.Parse(p[2]),registry).ToString();
            else if (p[0] == "N") fleet.NotifyMemberAdded(int.Parse(p[1]),uint.Parse(p[2]),uint.Parse(p[3]));
            else if (p[0] == "R")
            { emitted=int.Parse(p[1]); fleet.RequestNormalMove(emitted,registry,maps[active],24,24,int.Parse(p[2]),int.Parse(p[3]),uint.Parse(p[4])); }
            else if (p[0] == "T")
            { emitted=int.Parse(p[1]); fleet.WorkNormalTask(emitted,registry,maps[active],24,24,uint.Parse(p[2])); }
            else if (p[0] == "X") fleet.ClearNormalTask(int.Parse(p[1]));
            else if (p[0] == "Q") { if(!fleet.ConsumeNext())throw new Exception("Missing41"); }
            else if (p[0] == "M") active=p[1];
            else if (p[0] == "P") { uint id=uint.Parse(p[1]);registry[(int)id-11]=new ShipFleetNormalTask.Member(id,int.Parse(p[2]),int.Parse(p[3]),byte.Parse(p[4])); }
            else throw new Exception(line);
            Console.WriteLine(Snapshot(fleet,result,before,emitted));
        }
    }
}
