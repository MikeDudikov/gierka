using System;
using System.Collections.Generic;

namespace AncientConquest.Simulation
{
    public readonly struct ShipBoxSpan
    {
        public int X { get; }
        public int Y { get; }
        public int Width { get; }
        public int Height { get; }
        internal ShipBoxSpan(int x, int y, int width, int height) { X=x;Y=y;Width=width;Height=height; }
    }
    /// <summary>5195c0 patterns,56ff10 edges and clipped8-bit line mask semantics.</summary>
    public static class ShipBoxOutline
    {
        private static uint Rotate(uint v, int count) => (v << (count & 31)) | (v >> ((32 - count) & 31));
        private static uint Reverse(uint v)
        { uint r=0;for(int i=0;i<32;i++){r=(r<<1)|(v&1);v>>=1;}return r; }
        public static void Build(List<ShipBoxSpan> output, int x, int y, int width, int height,
            int phase, int clipX, int clipY, int clipWidth, int clipHeight, int thickness = 1)
        {
            if(output==null)throw new ArgumentNullException(nameof(output));
            if(x<0||x>=1536||y<0||y>=1536||clipX<0||clipY<0||clipX>=1536||clipY>=1536||
               phase<0||phase>31||thickness<1||thickness>2||clipWidth<1||clipHeight<1||
               clipWidth>1536-clipX||clipHeight>1536-clipY||
               width < -1536 || width > 1536 || height < -1536 || height > 1536)
                throw new ArgumentOutOfRangeException(nameof(phase));
            output.Clear();
            if(width<0){x=unchecked(x+1+width);width=-width;}
            if(height<0){y=unchecked(y+1+height);height=-height;}
            int right=unchecked(x-1+width),bottom=unchecked(y-1+height);
            uint top=Rotate(0xf0fff0ffu,phase),side=Rotate(0xfff0fff0u,phase);
            uint left=Rotate(0xfff0fff0u,(32-phase)&31);
            for(int i=0;i<thickness;i++)Line(output,x,y+i,right-thickness,y+i,top,clipX,clipY,clipWidth,clipHeight);
            for(int i=0;i<thickness;i++)Line(output,right-i,y,right-i,bottom-thickness,side,clipX,clipY,clipWidth,clipHeight);
            for(int i=0;i<thickness;i++)Line(output,right,bottom-i,x+thickness,bottom-i,side,clipX,clipY,clipWidth,clipHeight);
            for(int i=0;i<thickness;i++)Line(output,x+i,bottom,x+i,y+thickness,left,clipX,clipY,clipWidth,clipHeight);
        }
        private static void Line(List<ShipBoxSpan> spans,int x1,int y1,int x2,int y2,uint pattern,int cx,int cy,int cw,int ch)
        {
            uint bit=0x80000000u;
            if(x2<x1)
            {
                bit=1u<<(Math.Max(Math.Abs(x2-x1),Math.Abs(y2-y1))&31);pattern=Reverse(pattern);
                int t=x1;x1=x2;x2=t;t=y1;y1=y2;y2=t;
            }
            bool horizontal=y1==y2;
            if(!horizontal && y2<y1){int t=y1;y1=y2;y2=t;}
            if(horizontal)
            {if(y1<cy||y1>=cy+ch)return;x1=Math.Max(x1,cx);x2=Math.Min(x2,cx+cw-1);}
            else
            {if(x1<cx||x1>=cx+cw)return;y1=Math.Max(y1,cy);y2=Math.Min(y2,cy+ch-1);}
            int count=horizontal?x2-x1+1:y2-y1+1,start=-1;
            for(int i=0;i<count;i++)
            {
                bool ink=(pattern&bit)!=0;
                if(ink&&start<0)start=i;
                if(!ink&&start>=0){Add(spans,horizontal,x1,y1,start,i-start);start=-1;}
                bit>>=1;if(bit==0)bit=0x80000000u;
            }
            if(start>=0)Add(spans,horizontal,x1,y1,start,count-start);
        }
        private static void Add(List<ShipBoxSpan>s,bool h,int x,int y,int start,int count)
        {s.Add(new ShipBoxSpan(x+(h?start:0),y+(h?0:start),h?count:1,h?1:count));}
    }
}
