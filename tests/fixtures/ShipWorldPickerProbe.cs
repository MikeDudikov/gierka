using System;
using System.Collections.Generic;
using AncientConquest.Simulation;
using AncientConquest.World;

internal static class ShipWorldPickerProbe
{
    private sealed class Owner { public readonly int Id; public Owner(int id) { Id=id; } }
    private static int guards;
    private static void Check(string name,bool condition)
    { if(!condition)throw new Exception("Guard failed: "+name);Console.WriteLine("GUARD\t"+name);guards++; }
    private static bool Throws<T>(Action action) where T:Exception
    {try{action();return false;}catch(T){return true;}}
    private static ShipPointerMask MakeMask()
    {
        var planes=new byte[24][];
        for(int i=0;i<24;i++){planes[i]=new byte[392];for(int j=0;j<392;j++)planes[i][j]=255;}
        return new ShipPointerMask(56,56,planes);
    }
    private static void Main()
    {
        var mask=MakeMask();var grid=new MissionOccupancyGrid(24,24,new uint[576]);var owners=new Owner[576];
        for(int i=0;i<576;i++){owners[i]=new Owner(i);grid.TryClaim(i%24,i/24,owners[i]);}
        string line;
        while((line=Console.ReadLine())!=null)
        {
            var p=line.Split('\t');if(p.Length!=9||p[0]!="Q")throw new Exception("Bad query input");
            int wx=int.Parse(p[2]),wy=int.Parse(p[3]),cx=int.Parse(p[4]),cy=int.Parse(p[5]);bool precise=p[6]=="1";
            var hits=new HashSet<int>();if(p[7]!="-")foreach(string id in p[7].Split(','))hits.Add(int.Parse(id));
            var aliases=new Dictionary<int,int>();
            if(p[8]!="-")foreach(string pair in p[8].Split(',')){var a=pair.Split(':');aliases.Add(int.Parse(a[0]),int.Parse(a[1]));}
            foreach(var alias in aliases){grid.Release(alias.Key%24,alias.Key/24,owners[alias.Key]);grid.TryClaim(alias.Key%24,alias.Key/24,owners[alias.Value]);}
            var visits=new List<int>();
            Func<object,ShipPointerPose> describe=value=>{var owner=(Owner)value;visits.Add(owner.Id);bool hit=hits.Contains(owner.Id);return new ShipPointerPose(mask,hit?wx-1:10000,hit?wy-1:10000,20,5);};
            object found=ShipWorldPicker.Pick(grid,wx,wy,cx,cy,precise,describe);
            Console.WriteLine("ROW\t"+p[1]+"\t"+(found==null?"-":((Owner)found).Id.ToString())+"\t"+(visits.Count==0?"-":string.Join(",",visits)));
            foreach(var alias in aliases){grid.Release(alias.Key%24,alias.Key/24,owners[alias.Value]);grid.TryClaim(alias.Key%24,alias.Key/24,owners[alias.Key]);}
        }
        Func<object,ShipPointerPose> good=value=>new ShipPointerPose(mask,0,0,20,5);
        Check("null-grid",Throws<ArgumentNullException>(()=>ShipWorldPicker.Pick(null,0,0,0,0,true,good)));
        Check("width-contract",Throws<NotSupportedException>(()=>ShipWorldPicker.Pick(new MissionOccupancyGrid(23,24,new uint[552]),0,0,0,0,true,good)));
        Check("height-contract",Throws<NotSupportedException>(()=>ShipWorldPicker.Pick(new MissionOccupancyGrid(24,23,new uint[552]),0,0,0,0,true,good)));
        Check("null-describe",Throws<ArgumentNullException>(()=>ShipWorldPicker.Pick(grid,0,0,0,0,true,null)));
        Check("negative-x",Throws<ArgumentOutOfRangeException>(()=>ShipWorldPicker.Pick(grid,0,0,-1,0,true,good)));
        Check("past-x",Throws<ArgumentOutOfRangeException>(()=>ShipWorldPicker.Pick(grid,0,0,24,0,true,good)));
        Check("negative-y",Throws<ArgumentOutOfRangeException>(()=>ShipWorldPicker.Pick(grid,0,0,0,-1,true,good)));
        Check("past-y",Throws<ArgumentOutOfRangeException>(()=>ShipWorldPicker.Pick(grid,0,0,0,24,true,good)));
        Check("min-x",Throws<ArgumentOutOfRangeException>(()=>ShipWorldPicker.Pick(grid,0,0,int.MinValue,0,true,good)));
        Check("max-y",Throws<ArgumentOutOfRangeException>(()=>ShipWorldPicker.Pick(grid,0,0,0,int.MaxValue,true,good)));
        Check("null-mask",Throws<ArgumentNullException>(()=>new ShipPointerPose(null,0,0,20,5)));
        Check("class-before-ships",Throws<NotSupportedException>(()=>new ShipPointerPose(mask,0,0,20,5,199)));
        Check("class-after-ships",Throws<NotSupportedException>(()=>new ShipPointerPose(mask,0,0,20,5,212)));
        Check("class-max",Throws<NotSupportedException>(()=>new ShipPointerPose(mask,0,0,20,5,uint.MaxValue)));
        Check("default-pose",Throws<InvalidOperationException>(()=>ShipWorldPicker.Pick(grid,0,0,0,0,true,value=>default(ShipPointerPose))));
        int calls=0;Func<object,ShipPointerPose> counting=value=>{calls++;return good(value);};
        Check("invalid-before-callback",Throws<ArgumentOutOfRangeException>(()=>ShipWorldPicker.Pick(grid,0,0,24,0,true,counting))&&calls==0);
        var empty=new MissionOccupancyGrid(24,24,new uint[576]);
        Check("empty-no-callback",ShipWorldPicker.Pick(empty,0,0,12,12,true,counting)==null&&calls==0);
        Check("coarse-before-geometry",ReferenceEquals(ShipWorldPicker.Pick(grid,int.MinValue,int.MaxValue,0,0,false,value=>new ShipPointerPose(mask,0,0,999,-128)),owners[0]));
        Check("identity-zero",ReferenceEquals(ShipWorldPicker.Pick(grid,1,1,0,0,true,good),owners[0]));
        Check("class211",ReferenceEquals(ShipWorldPicker.Pick(grid,1,1,0,0,true,value=>new ShipPointerPose(mask,0,0,20,5,211)),owners[0]));
        bool unchanged=true;for(int i=0;i<576;i++)unchanged&=ReferenceEquals(grid.GetOccupant(i%24,i/24),owners[i])&&grid.GetFlags(i%24,i/24)==0;
        Check("grid-unchanged",unchanged);
        Console.WriteLine("GUARDS\t"+guards);
    }
}
