using System;
using System.Globalization;
using AncientConquest.Simulation;
public static class PointerCursorProgressionProbe
{
 public static int Main()
 {
  PointerCursorProgression p=null;string label="";int index=0;string line;
  while((line=Console.ReadLine())!=null)
  {
   string[]f=line.Split('\t');if(f[0]=="CASE"){p=new PointerCursorProgression();label=f[1];index=0;continue;}
   if(f[0]=="S")p.SetCursor(int.Parse(f[1]),int.Parse(f[2])!=0,uint.Parse(f[3],CultureInfo.InvariantCulture),int.Parse(f[4]),int.Parse(f[5]));
   else if(f[0]=="C")p.Confirm(int.Parse(f[1]),int.Parse(f[2]));
   else p.Draw(uint.Parse(f[1],CultureInfo.InvariantCulture),int.Parse(f[2]),int.Parse(f[3]));
   var s=p.Current;
   Console.WriteLine(string.Join("\t",new object[]{"ROW",label,index++,s.CursorType,s.GreenVariant?1:0,s.CursorFrame,s.ScreenX,s.ScreenY,s.CursorVisible?1:0,s.CursorWorldX,s.CursorWorldY,s.CursorLastTick,s.CursorInterval,s.ConfirmExists?1:0,s.ConfirmFrame,s.ConfirmDrawnFrame,s.ConfirmVisible?1:0,s.ConfirmWorldX,s.ConfirmWorldY,s.ConfirmLastTick,p.LastStepCursorPublishesPose?1:0,p.LastStepConfirmPublishesPose?1:0,p.LastStepDeletesConfirm?1:0}));
  }
  int guards=0;foreach(int t in new[]{int.MinValue,-1,1,4,8,100,int.MaxValue})
  {var a=new PointerCursorProgression();bool rejected=false;try{a.SetCursor(t,false,0,0,0);}catch(NotSupportedException){rejected=true;}if(!rejected||a.Current.CursorType!=-1)throw new Exception("cursor guard");guards++;}
  Console.WriteLine("GUARDS\t"+guards);return 0;
 }
}
