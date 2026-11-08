using System;
using AncientConquest.Simulation;
class SourceWaveFieldProbe
{
    private static void Check(string name, Action action)
    {
        try { action(); throw new Exception("Guard did not reject:"+name); }
        catch(ArgumentException) { Console.WriteLine("CHECK\t"+name); }
        catch(NotSupportedException) { Console.WriteLine("CHECK\t"+name); }
    }
    static void Main()
    {
        Check("null",()=>SourceWaveField.Fill(null,1,1,0,0,0,0));
        Check("width0",()=>SourceWaveField.Fill(new short[1],0,1,0,0,0,0));
        Check("height0",()=>SourceWaveField.Fill(new short[1],1,0,0,0,0,0));
        Check("size",()=>SourceWaveField.Fill(new short[1],2,2,0,0,0,0));
        Check("bounds",()=>SourceWaveField.Fill(new short[4],2,2,-1,0,1,1));
        Check("bounded",()=>SourceWaveField.Fill(new short[257],257,1,0,0,1,0));
        Check("weighted",()=>SourceWaveField.Fill(new short[]{0,2,0,0},2,2,0,0,1,1));
        Check("seed",()=>SourceWaveField.Fill(new short[]{-1,0,0,0},2,2,0,0,1,1));
        Check("target",()=>SourceWaveField.Fill(new short[]{0,0,0,-1},2,2,0,0,1,1));
        string line;
        while((line=Console.ReadLine())!=null)
        {
            string[] p=line.Split('\t');int w=int.Parse(p[0]),h=int.Parse(p[1]);
            byte[] raw=Convert.FromBase64String(p[6]);short[] field=new short[w*h];
            Buffer.BlockCopy(raw,0,field,0,raw.Length);
            int count=SourceWaveField.Fill(field,w,h,int.Parse(p[2]),int.Parse(p[3]),int.Parse(p[4]),int.Parse(p[5]));
            Buffer.BlockCopy(field,0,raw,0,raw.Length);
            Console.WriteLine("RESULT\t"+count+"\t"+Convert.ToBase64String(raw));
        }
    }
}
