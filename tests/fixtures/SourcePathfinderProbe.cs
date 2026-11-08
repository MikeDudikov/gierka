using System;
using System.Globalization;
using AncientConquest.Simulation;

internal static class SourcePathfinderProbe
{
    private static byte[] Hex(string text)
    {
        var bytes = new byte[text.Length / 2];
        for (int i = 0; i < bytes.Length; i++) bytes[i] = byte.Parse(text.Substring(i*2,2),NumberStyles.HexNumber,CultureInfo.InvariantCulture);
        return bytes;
    }
    private static string Hex(byte[] bytes) => BitConverter.ToString(bytes).Replace("-", "").ToLowerInvariant();
    private static byte[] Pack(short[] field)
    {
        var bytes = new byte[field.Length*2];
        for (int i = 0; i < field.Length; i++) { bytes[i*2] = unchecked((byte)field[i]); bytes[i*2+1] = unchecked((byte)(field[i]>>8)); }
        return bytes;
    }
    private static void Guard<T>(string name,Action action) where T:Exception
    {
        try { action(); } catch(T) { Console.WriteLine("GUARD\t"+name); return; }
        throw new Exception("Missing guard "+name);
    }
    private static void Main()
    {
        string line;
        while ((line = Console.ReadLine()) != null)
        {
            if(line.Length==0)continue;
            var f=line.Split('\t');int width=int.Parse(f[1]),height=int.Parse(f[2]);var raw=Hex(f[8]);var field=new short[width*height];
            for(int i=0;i<field.Length;i++)field[i]=unchecked((short)(raw[i*2]|raw[i*2+1]<<8));
            var result=SourcePathfinder.Find(field,width,height,int.Parse(f[3]),int.Parse(f[4]),int.Parse(f[5]),int.Parse(f[6]),int.Parse(f[7]));
            if(Hex(Pack(field))!=f[8])throw new Exception("Caller input map was modified");
            Console.WriteLine(string.Join("\t","ROW",f[0],result.PointCount,result.UsedWave?1:0,Hex(result.CapturePoints()),Hex(Pack(result.CaptureWorkingField()))));
            var points=result.CapturePoints();if(points.Length>0){points[0]^=255;if(Hex(points)==Hex(result.CapturePoints()))throw new Exception("Path alias");}
            var copy=result.CaptureWorkingField();copy[0]=123;if(result.CaptureWorkingField()[0]==123)throw new Exception("Field alias");
        }
        Guard<ArgumentNullException>("null_map",()=>SourcePathfinder.Find(null,1,1,0,0,0,0));
        Guard<ArgumentException>("dimension_mismatch",()=>SourcePathfinder.Find(new short[2],1,1,0,0,0,0));
        Guard<ArgumentException>("dimension_limit",()=>SourcePathfinder.Find(new short[129],129,1,0,0,0,0));
        Guard<ArgumentOutOfRangeException>("heading8",()=>SourcePathfinder.Find(new short[1],1,1,0,0,0,0,8));
        Guard<ArgumentOutOfRangeException>("heading_minus2",()=>SourcePathfinder.Find(new short[1],1,1,0,0,0,0,-2));
        Guard<NotSupportedException>("weighted_input",()=>SourcePathfinder.Find(new short[]{1},1,1,0,0,0,0));
    }
}
