using System;
using System.Globalization;
using AncientConquest.Simulation;
public static class ShipFleetProgressionProbe
{
 public static int Main()
 {
  ShipSelectionProgression p=null;string label="";int index=0;string line;
  while((line=Console.ReadLine())!=null)
  {
   string[] f=line.Split('\t');
   if(f[0]=="CASE"){p=new ShipSelectionProgression(int.Parse(f[2],CultureInfo.InvariantCulture));label=f[1];index=0;continue;}
   if(f[0]=="S")p.Select(int.Parse(f[1],CultureInfo.InvariantCulture),int.Parse(f[2],CultureInfo.InvariantCulture));
   else if(f[0]=="D")p.Deselect();
   else p.Advance(uint.Parse(f[1],CultureInfo.InvariantCulture),int.Parse(f[2],CultureInfo.InvariantCulture),int.Parse(f[3],CultureInfo.InvariantCulture),int.Parse(f[4],CultureInfo.InvariantCulture));
   var s=p.Current;
   Console.WriteLine(string.Join("\t",new object[]{"ROW",label,index++,s.SelectionState,s.Exists?1:0,s.StoredFrame,s.DrawnFrame,s.LastCounter,s.SelectorVisible?1:0,s.WorldPixelX,s.WorldPixelY,s.HealthExists?1:0,s.HealthVisible?1:0,s.HealthWorldX,s.HealthWorldY,p.LastStepPublishesPose?1:0,p.LastStepDeletesSelector?1:0,p.LastStepHidesHealth?1:0}));
  }
  int guards=0;foreach(int pending in new int[]{int.MinValue,-1,0,256,int.MaxValue})
  {
   var a=new ShipSelectionProgression();a.Select(1028,132);bool failed=false;
   try{a.Advance(1,pending,1028,132);}catch(ArgumentOutOfRangeException){failed=true;}
   if(!failed||a.Current.StoredFrame!=0||a.Current.LastCounter!=0)throw new Exception("pending guard");guards++;
  }
  Console.WriteLine("GUARDS\t"+guards);return 0;
 }
}
