using System;
using AncientConquest.Simulation;
class SourceNearestPathfinderProbe
{
    static byte[] Hex(string s){var b=new byte[s.Length/2];for(int i=0;i<b.Length;i++)b[i]=Convert.ToByte(s.Substring(i*2,2),16);return b;}
    static string Hex(byte[] b)=>BitConverter.ToString(b).Replace("-","").ToLowerInvariant();
    static void Guard(string name,Action action){try{action();throw new Exception("Did not reject "+name);}catch(ArgumentException){Console.WriteLine("GUARD\t"+name);}catch(NotSupportedException){Console.WriteLine("GUARD\t"+name);}}
    static void Main()
    {
        Guard("null",()=>SourceNearestPathfinder.Find(null,1,1,0,0,0,0));
        Guard("width",()=>SourceNearestPathfinder.Find(new short[1],0,1,0,0,0,0));
        Guard("size",()=>SourceNearestPathfinder.Find(new short[2],1,1,0,0,0,0));
        Guard("weighted",()=>SourceNearestPathfinder.Find(new short[]{2},1,1,0,0,0,0));
        Guard("range-negative",()=>SourceNearestPathfinder.Find(new short[1],1,1,0,0,0,0,-1));
        Guard("range-bounded",()=>SourceNearestPathfinder.Find(new short[1],1,1,0,0,0,0,257));
        Guard("heading",()=>SourceNearestPathfinder.Find(new short[1],1,1,0,0,0,0,0,8));
        var initial=new short[9];var owned=SourceNearestPathfinder.Find(initial,3,3,0,0,2,2,0);var path=owned.CapturePoints();path[0]=99;var f=owned.CaptureWorkingField();f[0]=99;
        var waveInput=new short[]{0,0,0,0,-1,0,0,0,0};
        var waveCopy=SourceNearestPathfinder.Find(waveInput,3,3,0,0,2,2);
        if(owned.CapturePoints()[0]==99||owned.CaptureWorkingField()[0]==99||initial[0]!=0||
           !waveCopy.UsedWave||waveCopy.CaptureWorkingField()[0]!=1||waveInput[0]!=0)
            throw new Exception("Copy ownership broken");Console.WriteLine("GUARD\tclone");
        Guard("wave-heading",()=>SourceWaveField.FillFromOrigin(new short[1],1,1,0,0,0,0,8));
        string line;while((line=Console.ReadLine())!=null){var p=line.Split('\t');int w=int.Parse(p[1]),h=int.Parse(p[2]);byte[] raw=Hex(p[9]);var field=new short[w*h];Buffer.BlockCopy(raw,0,field,0,raw.Length);
            var r=SourceNearestPathfinder.Find(field,w,h,int.Parse(p[3]),int.Parse(p[4]),int.Parse(p[5]),int.Parse(p[6]),int.Parse(p[7]),int.Parse(p[8]));
            var working=r.CaptureWorkingField();Buffer.BlockCopy(working,0,raw,0,raw.Length);
            Console.WriteLine("ROW\t"+p[0]+"\t"+r.PointCount+"\t"+(r.ReachedWithinRange?1:0)+"\t"+(r.UsedWave?1:0)+"\t"+r.WaveIterations+"\t"+Hex(r.CapturePoints())+"\t"+Hex(raw));}
    }
}
