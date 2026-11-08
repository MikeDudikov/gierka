using System;
using System.Collections.Generic;
using AncientConquest.Simulation;
using AncientConquest.World;
class ShipPendingSelectionProbe
{
 static object[] owners={new object(),new object(),new object()};
 static object Owner(int id)=>id==0?null:owners[id-11];
 static int Id(object owner){for(int i=0;i<3;i++)if(ReferenceEquals(owner,owners[i]))return i+11;throw new Exception("owner");}
 static void Main(){string line;SourceSpriteSlotQueue queue=null;
 while((line=Console.ReadLine())!=null){string[] f=line.Split('\t');
 if(f[0]=="P"){
  int mask=int.Parse(f[2]);var s=new ShipPendingSelection(owners);var initial=new List<object>();for(int i=0;i<3;i++)if((mask&(1<<i))!=0)initial.Add(owners[i]);
  if(initial.Count>0)s.ProcessBox(new ShipPointerCommandInput(null,0,0,0),24,24,initial.ToArray(),0);
  else if(f[3]=="1"){s.ProcessBox(new ShipPointerCommandInput(null,0,0,0),2,2,new[]{owners[0]},0);s.ProcessRelease(new ShipPointerCommandInput(owners[0],0,0,5),98,4);}
  int kind=int.Parse(f[5]);var input=new ShipPointerCommandInput(Owner(int.Parse(f[6])),18,5,kind,blocked:f[9]=="1",enabled:f[10]=="1");
  ShipPointerCommands.Result r;
  if(f[4]=="release")r=s.ProcessRelease(input,int.Parse(f[8]),uint.Parse(f[7]));
  else {var candidates=new List<object>();foreach(string v in f[13].Split(','))if(v!="-")candidates.Add(Owner(int.Parse(v)));r=s.ProcessBox(input,int.Parse(f[11]),int.Parse(f[12]),candidates.ToArray(),uint.Parse(f[7]));}
  var ids=new List<int>();for(int i=0;i<s.Count;i++)ids.Add(Id(s.GetMember(i)));var events=new List<string>();var visual=new int[3];for(int i=0;i<3;i++)visual[i]=(mask>>i)&1;
  for(int i=0;i<s.EventCount;i++){var e=s.GetEvent(i);int id=Id(e.Owner);events.Add(id+":"+(e.Selected?1:0));visual[id-11]=e.Selected?1:visual[id-11]!=0?2:0;}
  Console.WriteLine(string.Join("\t",new object[]{"P",f[1],string.Join(",",ids),s.Selected?1:0,s.Pending?1:0,string.Join(",",visual),string.Join(",",events),r.CursorType,r.ActionMask,r.ActionBit,r.Blocked?1:0}));
 }
 else if(f[0]=="CASE")queue=new SourceSpriteSlotQueue();
 else {
  int result=-1;
  if(f[0]=="R")result=queue.Register(int.Parse(f[1]),f[2]=="1");else if(f[0]=="D")queue.Release(int.Parse(f[1]));else queue.UpdateDepth(int.Parse(f[1]),int.Parse(f[2]));
  var depths=new List<int>();var alive=new List<int>();var draw=new List<int>();for(int i=0;i<queue.AllocatedCount;i++){depths.Add(queue.GetDepth(i));alive.Add(queue.IsAlive(i)?1:0);draw.Add(queue.GetAllocatedDrawNode(i));}
  Console.WriteLine(string.Join("\t",new object[]{"Q",result,string.Join(",",depths),string.Join(",",alive),string.Join(",",draw)}));
 }
 }
 }
}
