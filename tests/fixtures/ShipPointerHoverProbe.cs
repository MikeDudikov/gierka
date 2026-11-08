using System;
using System.Collections.Generic;
using System.IO;
using AncientConquest.Simulation;
using AncientConquest.World;

internal static class ShipPointerHoverProbe
{
    private sealed class Actor
    {
        internal int Id,X,Y,Frame;
        internal sbyte Heading;
        internal byte Side,Player;
        internal uint Caps,Class;
        internal ShipPointerMask Mask;
    }
    private static byte[] Hex(string value)
    {var bytes=new byte[value.Length/2];for(int i=0;i<bytes.Length;i++)bytes[i]=Convert.ToByte(value.Substring(i*2,2),16);return bytes;}
    private static int guards;
    private static void Check(string name,bool value)
    {if(!value)throw new Exception("Hover guard failed: "+name);guards++;Console.WriteLine("GUARD\t"+name);}
    private static bool Throws<T>(Action action)where T:Exception
    {try{action();return false;}catch(T){return true;}}
    private static void Main(string[] args)
    {
        byte[] raw=File.ReadAllBytes(args[0]);var flags=new uint[576];for(int i=0;i<flags.Length;i++)flags[i]=BitConverter.ToUInt32(raw,i*4);
        var grid=new MissionOccupancyGrid(24,24,flags);var masks=new Dictionary<string,ShipPointerMask>();var actors=new Dictionary<int,Actor>();var visits=new List<int>();ShipPointerHover hover=null;
        Func<object,ShipPointerPose> poses=value=>{var a=(Actor)value;visits.Add(a.Id);return new ShipPointerPose(a.Mask,a.X,a.Y,a.Frame,a.Heading,a.Class);};
        Func<object,ShipHoverActor> metadata=value=>{var a=(Actor)value;return new ShipHoverActor(a.Side,a.Player,a.Caps,a.Class);};
        string line;
        while((line=Console.ReadLine())!=null)
        {
            string[] p=line.Split('\t');string kind=p[0];
            if(kind=="F")
            {
                int width=int.Parse(p[2]),height=int.Parse(p[3]),length=(width+7)/8*height;byte[] all=Hex(p[4]);var planes=new byte[24][];
                for(int i=0;i<24;i++){planes[i]=new byte[length];Buffer.BlockCopy(all,i*length,planes[i],0,length);}masks.Add(p[1],new ShipPointerMask(width,height,planes));continue;
            }
            if(kind=="A")
            {
                var a=new Actor{Id=int.Parse(p[1]),Mask=masks[p[2]],X=int.Parse(p[3]),Y=int.Parse(p[4]),Frame=int.Parse(p[5]),Heading=sbyte.Parse(p[6]),Side=byte.Parse(p[7]),Player=byte.Parse(p[8]),Caps=uint.Parse(p[9]),Class=uint.Parse(p[10])};actors.Add(a.Id,a);grid.TryClaim(int.Parse(p[11]),int.Parse(p[12]),a);continue;
            }
            if(kind=="START"){hover=new ShipPointerHover(grid,actors[11],poses,metadata);continue;}
            if(kind=="CAPS"){actors[int.Parse(p[2])].Caps=uint.Parse(p[3]);continue;}
            if(kind=="POSE")
            {var a=actors[int.Parse(p[2])];a.X=int.Parse(p[3]);a.Y=int.Parse(p[4]);a.Frame=int.Parse(p[5]);a.Heading=sbyte.Parse(p[6]);continue;}
            if(kind=="CLAIMS")
            {
                for(int i=0;i<576;i++){object owner=grid.GetOccupant(i%24,i/24);if(owner!=null)grid.Release(i%24,i/24,owner);}
                foreach(string part in p[2].Split(',')){string[] pair=part.Split(':');int index=int.Parse(pair[0]);grid.TryClaim(index%24,index/24,actors[int.Parse(pair[1])]);}continue;
            }
            if(hover==null)throw new Exception("Missing hover START");
            visits.Clear();
            if(kind=="MOVE")hover.Move(int.Parse(p[2]),int.Parse(p[3]),int.Parse(p[4]),int.Parse(p[5]),int.Parse(p[6]),int.Parse(p[7]),p[8]=="1");
            else if(kind=="REFRESH")hover.Refresh(p[2]=="1");
            else if(kind=="IMPORT")hover.ApplyReleaseCursor(ushort.Parse(p[2]),ushort.Parse(p[3]),ushort.Parse(p[4]),p[5]=="1");
            else if(kind=="INVALIDATE")hover.InvalidateMap();
            else throw new Exception("Unknown hover input "+kind);
            var s=hover.Current;
            Console.WriteLine(string.Join("\t",new object[]{"STATE",p[1],s.HasMapPosition?1:0,s.ScreenX,s.ScreenY,s.WorldX,s.WorldY,s.CellX,s.CellY,s.HoveredOwner==null?"-":((Actor)s.HoveredOwner).Id.ToString(),s.CursorType,s.ActionMask,s.ActionBit,s.Blocked?1:0,s.Selector,s.LastQueryPerformed?1:0,visits.Count==0?"-":string.Join(",",visits)}));
        }
        if(hover==null)throw new Exception("No hover fixture");
        Check("null-grid",Throws<ArgumentNullException>(()=>new ShipPointerHover(null,actors[11],poses,metadata)));
        Check("wrong-grid",Throws<NotSupportedException>(()=>new ShipPointerHover(new MissionOccupancyGrid(23,24,new uint[552]),actors[11],poses,metadata)));
        Check("null-owner",Throws<ArgumentNullException>(()=>new ShipPointerHover(grid,null,poses,metadata)));
        Check("null-poses",Throws<ArgumentNullException>(()=>new ShipPointerHover(grid,actors[11],null,metadata)));
        Check("null-metadata",Throws<ArgumentNullException>(()=>new ShipPointerHover(grid,actors[11],poses,null)));
        Check("negative-x",Throws<ArgumentOutOfRangeException>(()=>hover.Move(1,1,1,1,-1,0,false)));
        Check("past-x",Throws<ArgumentOutOfRangeException>(()=>hover.Move(1,1,1,1,24,0,false)));
        Check("negative-y",Throws<ArgumentOutOfRangeException>(()=>hover.Move(1,1,1,1,0,-1,false)));
        Check("past-y",Throws<ArgumentOutOfRangeException>(()=>hover.Move(1,1,1,1,0,24,false)));
        Check("class-before-ships",Throws<NotSupportedException>(()=>new ShipHoverActor(1,1,0,199)));
        Check("class-after-ships",Throws<NotSupportedException>(()=>new ShipHoverActor(1,1,0,212)));
        Check("class-max",Throws<NotSupportedException>(()=>new ShipHoverActor(1,1,0,uint.MaxValue)));
        visits.Clear();hover.InvalidateMap();hover.Refresh(false);Check("invalid-map-no-query",visits.Count==0&&!hover.Current.LastQueryPerformed&&!hover.Current.HasMapPosition);
        var first=new ShipPointerHover(grid,actors[11],poses,metadata,selector:37);visits.Clear();first.Move(0,0,0,0,0,0,false);Check("initial-zero-screen",!first.Current.HasMapPosition&&visits.Count==0);
        first.ApplyReleaseCursor(5,0x101,1,false);Check("import-without-query",!first.Current.LastQueryPerformed&&first.Current.CursorType==5&&first.Current.Selector==37);
        Console.WriteLine("GUARDS\t"+guards);
    }
}
