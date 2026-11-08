using System;
using System.Collections.Generic;
using AncientConquest.Simulation;
using AncientConquest.World;
class ShipBoxSelectionProbe
{
 static readonly Dictionary<int,object> owners=new Dictionary<int,object>();
 static readonly Dictionary<object,ShipHoverActor> actors=new Dictionary<object,ShipHoverActor>();
 static string Hex(byte[] b)=>BitConverter.ToString(b).Replace("-", "").ToLowerInvariant();
 static int guards;
 static void Reject(Action action){try{action();}catch(ArgumentException){guards++;return;}catch(NotSupportedException){guards++;return;}catch(InvalidOperationException){guards++;return;}throw new Exception("Missing box guard");}
 static void Check(bool value){if(!value)throw new Exception("Gesture invariant");guards++;}
 static void Guards(){
  var b=new ShipBoxGesture();Reject(()=>b.Begin(-1,0));Reject(()=>b.Begin(0,1536));Reject(()=>b.CellBounds(0,0));
  b.Begin(100,100);b.Move(108,200,10);Check(!b.Active);b.Move(109,109,20);Check(b.Active&&!b.Visible&&b.Width==0&&b.Height==0);
  b.Life(69);Check(!b.Visible);b.Life(70);Check(b.Visible&&b.Phase==1&&b.LastMilliseconds==70);b.Life(1000);Check(b.Phase==2);
  b.Move(80,80,1000);Check(b.Width==-19&&b.Height==-19);Check(string.Join(",",b.CellBounds(80,80))=="1,1,1,1");
  b.Begin(100,100);b.Move(90,90,0);Check(!b.Active);b.Move(89,89,0);Check(b.Active);
  b.Begin(100,100);b.Move(110,110,uint.MaxValue-20);b.Life(29);Check(b.Visible&&b.Phase==1);b.Cancel();b.Life(100);Check(!b.Active&&!b.Visible&&!b.Candidate);
  var g=new MissionOccupancyGrid(24,24,new uint[576]);Func<object,ShipHoverActor>d=o=>new ShipHoverActor(1,1,0,200);Func<object,int>r=o=>-1;
  Reject(()=>ShipBoxSelection.Collect(null,0,0,1,1,d,r));Reject(()=>ShipBoxSelection.Collect(g,-1,0,1,1,d,r));Reject(()=>ShipBoxSelection.Collect(g,23,23,2,1,d,r));Reject(()=>ShipBoxSelection.Collect(g,0,0,0,1,d,r));
  g.TryClaim(0,0,new object());Reject(()=>ShipBoxSelection.Collect(g,0,0,1,1,o=>new ShipHoverActor(1,1,0,50),r));
  var spans=new List<ShipBoxSpan>();Reject(()=>ShipBoxOutline.Build(null,0,0,1,1,0,0,0,64,64));Reject(()=>ShipBoxOutline.Build(spans,0,0,1,1,32,0,0,64,64));Reject(()=>ShipBoxOutline.Build(spans,int.MaxValue,0,1,1,0,0,0,64,64));Reject(()=>ShipBoxOutline.Build(spans,0,0,1,1,0,1535,0,2,64));
  var c=new ShipPointerCommands(new object());Reject(()=>c.ProcessBoxSelection(new ShipPointerCommandInput(null,0,0,0),0,1,true,0));
  Check(!c.ProcessBoxSelection(new ShipPointerCommandInput(null,0,0,0,enabled:false),1,1,true,0).SelectionRequested);
 }
 static void Main(){
  string line;while((line=Console.ReadLine())!=null){var f=line.Split('\t');
   if(f[0]=="A"){int id=int.Parse(f[1]);object o=new object();owners[id]=o;actors[o]=new ShipHoverActor(byte.Parse(f[2]),byte.Parse(f[3]),0,uint.Parse(f[4]));}
   else if(f[0]=="Q"){
    var g=new MissionOccupancyGrid(24,24,new uint[576]);
    foreach(string pair in f[8].Split(',')){if(pair=="-")continue;var p=pair.Split(':');int c=int.Parse(p[0]);if(!g.TryClaim(c%24,c/24,owners[int.Parse(p[1])]))throw new Exception("claim");}
    int reserved=int.Parse(f[7]),owner=int.Parse(f[6]);var found=ShipBoxSelection.Collect(g,int.Parse(f[2]),int.Parse(f[3]),int.Parse(f[4]),int.Parse(f[5]),o=>actors[o],o=>ReferenceEquals(o,owners[11])?reserved:-1,(byte)(owner/4),(byte)(owner%4));
    var ids=new List<int>();foreach(object o in found)foreach(var p in owners)if(ReferenceEquals(p.Value,o))ids.Add(p.Key);
    Console.WriteLine("Q\t"+f[1]+"\t"+string.Join(",",ids));
   }
   else if(f[0]=="P"){
    var c=new ShipPointerCommands(owners[11]);
    if(f[2]!="none"){
     c.ProcessRelease(new ShipPointerCommandInput(owners[11],16,2,5),0x62,0);
     if(f[2]=="group"){c.ProcessRelease(new ShipPointerCommandInput(null,18,5,7),0x62,0);c.ConsumeMembership41(0);}
    }
    int kind=int.Parse(f[3]),w=int.Parse(f[5]),h=int.Parse(f[6]);
    var r=c.ProcessBoxSelection(new ShipPointerCommandInput(null,18,5,kind),w,h,f[7]=="1",uint.Parse(f[4]));var s=c.Current;
    Console.WriteLine(string.Join("\t",new object[]{"P",f[1],s.Selected?1:0,s.PendingSelection?1:0,s.CurrentGroupIndex,s.UiGroup,s.SimulationGroup,s.SelectionVisualFlag,s.GroupCount,s.LastCommandCount,r.CursorType,r.SelectionClearRequested?1:0,r.SelectionRequested?1:0}));
   }
   else if(f[0]=="R"){
    var spans=new List<ShipBoxSpan>();ShipBoxOutline.Build(spans,int.Parse(f[2]),int.Parse(f[3]),int.Parse(f[4]),int.Parse(f[5]),int.Parse(f[6]),0,0,64,64,int.Parse(f[7]));
    var bits=new byte[512];foreach(var s in spans)for(int y=s.Y;y<s.Y+s.Height;y++)for(int x=s.X;x<s.X+s.Width;x++){int i=y*64+x;bits[i/8]|=(byte)(128>>(i%8));}
    Console.WriteLine("R\t"+f[1]+"\t"+Hex(bits));
   }
   else if(f[0]=="G"){Guards();Console.WriteLine("G\t"+guards);}
   else throw new Exception("Unknown row");
  }
 }
}
