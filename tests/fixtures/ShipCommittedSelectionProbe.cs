using System;
using System.Collections.Generic;
using AncientConquest.Simulation;
class ShipCommittedSelectionProbe
{
 static readonly object[] owners={new object(),new object(),new object()};
 static ShipFleetMembership membership;
 static ShipPendingSelection selection;
 static int[] visual;
 static int Id(object owner){for(int i=0;i<3;i++)if(ReferenceEquals(owner,owners[i]))return i+11;throw new Exception("owner");}
 static object[] Group(short group)
 {var a=new object[membership.GetGroupMemberCount(group)];for(int i=0;i<a.Length;i++)a[i]=owners[membership.GetGroupMemberRegistryIndex(group,i)];return a;}
 static void Main()
 {
  string line;
  while((line=Console.ReadLine())!=null)
  {
   string[] f=line.Split('\t');
   if(f[0]=="CASE"){membership=new ShipFleetMembership(new uint[]{11,12,13});selection=new ShipPendingSelection(owners,o=>membership.GetUiGroup(Id(o)-11),Group);visual=new int[3];}
   else if(f[0]=="G"){var ids=new List<uint>();foreach(string id in f[1].Split(','))ids.Add(uint.Parse(id));membership.CommitPending(ids);}
   else
   {
    bool clear=f[0]=="clear";object target=clear?null:owners[int.Parse(f[1])-11];
    var r=selection.ProcessRelease(new ShipPointerCommandInput(target,18,5,clear?7:5),clear?100:98,f[0]=="ctrl"?8u:0u);
    var events=new List<string>();for(int i=0;i<selection.EventCount;i++){var e=selection.GetEvent(i);int id=Id(e.Owner);events.Add(id+":"+(e.Selected?1:0));visual[id-11]=e.Selected?1:visual[id-11]!=0?2:0;}
    var ids=new List<int>();for(int i=0;i<selection.Count;i++)ids.Add(Id(selection.GetMember(i)));
    Console.WriteLine(string.Join("\t",new object[]{string.Join(",",ids),selection.TemporaryCount,selection.Selected?1:0,selection.Pending?1:0,selection.CurrentGroup,string.Join(",",visual),string.Join(",",events),r.CursorType,r.ActionMask,r.ActionBit,r.Blocked?1:0}));
   }
  }
 }
}
