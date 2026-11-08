using System;
using System.Collections.Generic;

namespace AncientConquest.Simulation
{
    /// <summary>
    /// Source55b9e0 partial/range path over an owned0/-1 map. Preserves
    /// forward-wave ring order, raw five-byte records and its two distinct
    /// distance functions; this is not a generic nearest-free-cell search.
    /// </summary>
    public static class SourceNearestPathfinder
    {
        public sealed class Result
        {
            private readonly byte[] points;
            private readonly short[] field;
            public int PointCount => points.Length / 5;
            public bool Succeeded => PointCount != 0;
            public bool ReachedWithinRange { get; }
            public bool UsedWave { get; }
            public int WaveIterations { get; }
            internal Result(byte[] points,short[] field,bool reached,bool usedWave,int iterations)
            {
                this.points=points;this.field=field;ReachedWithinRange=reached;
                UsedWave=usedWave;WaveIterations=iterations;
            }
            public byte[] CapturePoints() => (byte[])points.Clone();
            public short[] CaptureWorkingField() => (short[])field.Clone();
        }

        private static readonly int[] Dx={1,1,0,-1,-1,-1,0,1};
        private static readonly int[] Dy={0,-1,-1,-1,0,1,1,1};

        public static Result Find(short[] initialField,int width,int height,int originX,int originY,
                                  int requestedX,int requestedY,int range=0,int preferredHeading=0)
        {
            if(initialField==null) throw new ArgumentNullException(nameof(initialField));
            if(width<1||width>128||height<1||height>128||(long)width*height!=initialField.LongLength)
                throw new ArgumentException("A bounded matching source map is required.");
            if(range<0||range>256) throw new ArgumentOutOfRangeException(nameof(range));
            if(preferredHeading < -1 || preferredHeading > 7)
                throw new ArgumentOutOfRangeException(nameof(preferredHeading));
            foreach(short value in initialField)
                if(value!=0&&value!=-1)
                    throw new NotSupportedException("This partial path projection accepts free0/blocked-1 maps.");
            short[] field=(short[])initialField.Clone();
            if(!Inside(originX,originY,width,height)||!Inside(requestedX,requestedY,width,height))
                return new Result(new byte[0],field,false,false,0);

            if(TryDirect(field,width,originX,originY,requestedX,requestedY,preferredHeading,range,
                         out int first,out int second,out int cornerX,out int cornerY))
            {
                var direct=new List<byte>();
                if(originX==requestedX&&originY==requestedY)
                {
                    Append(direct,originX,originY,preferredHeading);
                    Append(direct,requestedX,requestedY,preferredHeading);
                }
                else
                {
                    int count=Math.Max(Math.Abs(requestedX-originX),Math.Abs(requestedY-originY))+1;
                    int x=originX,y=originY,heading=first;
                    for(int index=0;index<count;index++)
                    {
                        Append(direct,x,y,heading);
                        // Original557410 differs from5573d0 exactly at(2,2).
                        if(StopDistance(x,y,requestedX,requestedY)<=range)
                        {
                            if(index==0) Append(direct,x,y,heading);
                            break;
                        }
                        if(x==cornerX&&y==cornerY) heading=second;
                        x+=Dx[heading];y+=Dy[heading];
                    }
                }
                return new Result(direct.ToArray(),field,true,false,0);
            }

            int iterations=SourceWaveField.FillFromOrigin(field,width,height,originX,originY,
                                                          requestedX,requestedY,preferredHeading);
            if(iterations<0) return new Result(new byte[0],field,false,true,iterations);
            int endpointX=requestedX,endpointY=requestedY;
            if(field[requestedY*width+requestedX]<1||range>0)
            {
                int bestMetric=int.MaxValue,bestWave=int.MaxValue;
                bool found=false;
                void ConsiderMetric(int x,int y,int radius,int metricTwice,int value)
                {
                    if(value<1) return;
                    bool choose;
                    if(radius<3&&radius<=range) choose=value<bestWave;
                    else
                    {
                        int metric=metricTwice/2;
                        choose=range<metric
                            ? metric<bestMetric/2 || metric==bestMetric/2&&value<bestWave
                            : value<bestWave || range<bestMetric/2;
                    }
                    if(choose)
                    {
                        endpointX=x;endpointY=y;bestWave=value;bestMetric=metricTwice;found=true;
                    }
                }
                // Source order is RIGHT, TOP, LEFT, BOTTOM, including corner
                // duplicates. Choosing a different equal-cost point changes
                // the raw route and therefore the ship's later steering.
                for(int radius=1;radius<=range || radius<=bestMetric/2&&(radius!=3||bestMetric>6);radius++)
                {
                    int left=Math.Max(0,requestedX-radius),right=Math.Min(width-1,requestedX+radius);
                    int top=Math.Max(0,requestedY-radius),bottom=Math.Min(height-1,requestedY+radius);
                    if(radius<=right-requestedX)
                        for(int y=top;y<=bottom;y++)
                            ConsiderMetric(right,y,radius,2*radius+Math.Abs(y-requestedY),field[y*width+right]);
                    if(radius<=requestedY-top)
                        for(int x=left;x<=right;x++)
                            ConsiderMetric(x,top,radius,2*radius+Math.Abs(x-requestedX),field[top*width+x]);
                    if(radius<=requestedX-left)
                        for(int y=top;y<=bottom;y++)
                            ConsiderMetric(left,y,radius,2*radius+Math.Abs(y-requestedY),field[y*width+left]);
                    if(radius<=bottom-requestedY)
                        for(int x=left;x<=right;x++)
                            ConsiderMetric(x,bottom,radius,2*radius+Math.Abs(x-requestedX),field[bottom*width+x]);
                }
                if(!found) return new Result(new byte[0],field,false,true,iterations);
            }

            var reverse=new List<byte>();
            Append(reverse,endpointX,endpointY,0);
            int currentX=endpointX,currentY=endpointY,previous=-1;
            for(int safety=0;safety<=width*height;safety++)
            {
                int selected=0,nextX=originX,nextY=originY;
                if(currentX!=originX||currentY!=originY)
                {
                    int best=30000;selected=-1;
                    for(int heading=1;heading<8;heading+=2)
                    {
                        int x=currentX+Dx[heading],y=currentY+Dy[heading];
                        if(!Inside(x,y,width,height)) continue;
                        if(x==originX&&y==originY){selected=heading;nextX=x;nextY=y;break;}
                        int value=field[y*width+x];
                        if(value>0&&(value+1<best||value+1==best&&previous==heading))
                        {best=value+1;selected=heading;nextX=x;nextY=y;}
                    }
                    bool adjacentOrigin=selected>=0&&nextX==originX&&nextY==originY;
                    if(!adjacentOrigin)
                    {
                        for(int heading=0;heading<8;heading+=2)
                        {
                            int x=currentX+Dx[heading],y=currentY+Dy[heading];
                            if(!Inside(x,y,width,height)) continue;
                            if(x==originX&&y==originY){selected=heading;nextX=x;nextY=y;break;}
                            int value=field[y*width+x];
                            if(value>0&&(value<best||value==best&&previous!=selected&&(previous&1)==0))
                            {best=value;selected=heading;nextX=x;nextY=y;}
                        }
                    }
                    if(selected<0) throw new InvalidOperationException("Source partial wave has no positive predecessor.");
                }
                reverse[reverse.Count-1]=(byte)((selected-4)&7);
                Append(reverse,nextX,nextY,0);
                if(nextX==originX&&nextY==originY)
                {
                    int count=reverse.Count/5;byte[] points=new byte[reverse.Count];
                    for(int index=0;index<count;index++)
                        for(int b=0;b<5;b++) points[index*5+b]=reverse[(count-1-index)*5+b];
                    return new Result(points,field,Distance(endpointX,endpointY,requestedX,requestedY)<=range,true,iterations);
                }
                currentX=nextX;currentY=nextY;previous=selected;
            }
            throw new InvalidOperationException("Source partial wave reconstruction exceeded its map bound.");
        }

        private static bool Inside(int x,int y,int w,int h)=>x>=0&&y>=0&&x<w&&y<h;
        private static int Distance(int x,int y,int targetX,int targetY)
        {
            int a=Math.Abs(targetX-x),b=Math.Abs(targetY-y);
            return (Math.Min(a,b)+Math.Max(a,b)*2)/2;
        }
        private static int StopDistance(int x,int y,int targetX,int targetY)
        {
            int a=Math.Abs(targetX-x),b=Math.Abs(targetY-y);
            return a==2&&b==2 ? 2 : (Math.Min(a,b)+Math.Max(a,b)*2)/2;
        }
        private static int DirectionDistance(int a,int b)
        {int value=Math.Abs(a-b);return value>4?8-value:value;}
        private static void Append(List<byte> points,int x,int y,int heading)
        {
            unchecked
            {
                points.Add((byte)x);points.Add((byte)(x>>8));
                points.Add((byte)y);points.Add((byte)(y>>8));points.Add((byte)heading);
            }
        }
        private static bool TryDirect(short[] field,int width,int x,int y,int targetX,int targetY,int preferred,int range,
                                      out int first,out int second,out int cornerX,out int cornerY)
        {
            cornerX=x;cornerY=y;
            if(x==targetX&&y==targetY){first=second=preferred;return true;}
            int absX=Math.Abs(targetX-x),absY=Math.Abs(targetY-y);
            int horizontal=targetX<x?4:0,vertical=targetY<y?2:6;
            int diagonal=targetX<x?(targetY<y?3:5):(targetY<y?1:7);
            if(absX>=absY*2){first=horizontal;second=diagonal;}
            else if(absY>=absX*2){first=vertical;second=diagonal;}
            else{first=diagonal;second=absX<absY?vertical:horizontal;}
            if(absX==0||absY==0||absX==absY) second=first;
            if(preferred>=0&&DirectionDistance(second,preferred)<DirectionDistance(first,preferred))
            {int t=first;first=second;second=t;}
            if(TrySegments(field,width,x,y,targetX,targetY,absX,absY,first,second,range,out cornerX,out cornerY))return true;
            if(first==second)return false;
            int temp=first;first=second;second=temp;
            return TrySegments(field,width,x,y,targetX,targetY,absX,absY,first,second,range,out cornerX,out cornerY);
        }
        private static bool TrySegments(short[] field,int width,int x,int y,int targetX,int targetY,
                                        int remainingX,int remainingY,int first,int second,int range,
                                        out int cornerX,out int cornerY)
        {
            while(true)
            {
                if(range>0&&Distance(x,y,targetX,targetY)<=range){cornerX=x;cornerY=y;return true;}
                x+=Dx[first];y+=Dy[first];remainingX-=Math.Abs(Dx[first]);remainingY-=Math.Abs(Dy[first]);
                if(field[y*width+x]!=0){cornerX=x;cornerY=y;return false;}
                if((first&1)!=0 ? remainingX==0||remainingY==0 : remainingX==remainingY)break;
            }
            cornerX=x;cornerY=y;
            while(remainingX!=0||remainingY!=0)
            {
                if(range>0&&Distance(x,y,targetX,targetY)<=range)return true;
                x+=Dx[second];y+=Dy[second];remainingX-=Math.Abs(Dx[second]);remainingY-=Math.Abs(Dy[second]);
                if(field[y*width+x]!=0)return false;
            }
            return true;
        }
    }
}
