using System;

namespace AncientConquest.Simulation
{
    /// <summary>
    /// Original5578a0's bounded zero/minus-one branches used by55c9a0/55b9e0,
    /// plus the distinct545960 descending wave used by4a1e90. Each entry keeps
    /// its source frontier order;neither substitutes a general pathfinder.
    /// </summary>
    public static class SourceWaveField
    {
        /// <summary>
        /// Matches4a1e90 ->545db0 ->545960(field,w,h,x,y,5000,3).
        /// Descending first-visit wave, NOT5578a0. Caller clones navigation;
        /// allocation-prefix memory is a separate explicit input.
        /// </summary>
        public static void FillQueuedRoute(short[] field, int width, int height, int x, int y)
        {
            if (field == null) throw new ArgumentNullException(nameof(field));
            if (width < 1 || height < 1 || width > 128 || height > 128 ||
                (long)width * height != field.Length) throw new ArgumentException("Complete bounded navigation field required.");
            if (x < 0 || y < 0 || x >= width || y >= height) throw new ArgumentOutOfRangeException(nameof(x));
            foreach (short value in field)
                if (value != 0 && value != -1) throw new NotSupportedException("Only zero/free and minus-one/blocked navigation is represented.");
            //5459f3 overwrites even a blocked seed. Cells enter a frontier once;
            //native5-byte queue records have no observable padding here.
            int[] current = new int[field.Length], next = new int[field.Length];
            current[0] = y * width + x; int count = 1;
            field[current[0]] = 30006;
            for (int remaining = 5001; remaining > 0 && count > 0; remaining--)
            {
                int nextCount = 0;
                for (int i = 0; i < count; i++)
                {
                    int cell = current[i], cx = cell % width, cy = cell / width;
                    int value = field[cell] - 6;
                    if (value <= 0) continue;
                    //545b45..545d43: R,U,L,D,RU,LU,LD,RD; no relaxation.
                    Visit(cx + 1, cy, value); Visit(cx, cy - 1, value);
                    Visit(cx - 1, cy, value); Visit(cx, cy + 1, value);
                    value -= 3;
                    if (value > 0)
                    {
                        Visit(cx + 1, cy - 1, value); Visit(cx - 1, cy - 1, value);
                        Visit(cx - 1, cy + 1, value); Visit(cx + 1, cy + 1, value);
                    }
                }
                int[] swap = current; current = next; next = swap; count = nextCount;
                // Matches545b4d..545d40: only zero cells are labelled/enqueued.
                void Visit(int nx, int ny, int value)
                {
                    if (nx < 0 || ny < 0 || nx >= width || ny >= height) return;
                    int cell = ny * width + nx;
                    if (field[cell] != 0) return;
                    field[cell] = unchecked((short)value); next[nextCount++] = cell;
                }
            }
        }
        private static readonly int[] DirectionX={1,1,0,-1,-1,-1,0,1};
        private static readonly int[] DirectionY={0,-1,-1,-1,0,1,1,1};
        /// <summary>Source560090's complete flood: no destination/early termination, heading-1.</summary>
        public static int FillAll(short[] field, int width, int height, int seedX, int seedY)
        {
            if (field == null) throw new ArgumentNullException(nameof(field));
            if (width < 1 || height < 1 || width > 256 || height > 256 || (long)width * height != field.LongLength)
                throw new ArgumentException("A bounded complete source wave map is required.");
            if (seedX < 0 || seedY < 0 || seedX >= width || seedY >= height)
                throw new ArgumentOutOfRangeException(nameof(seedX));
            var map = new ushort[field.Length];
            for (int index = 0; index < field.Length; index++)
            {
                if (field[index] != 0 && field[index] != -1)
                    throw new NotSupportedException("Only source zero/free and minus-one/blocked input is projected.");
                map[index] = unchecked((ushort)field[index]);
            }
            // Like5578a0 itself, this entry overwrites a blocked seed with1.
            int result = Calculate(map, width, 0, 0, width - 1, height - 1, seedX, seedY,
                                   -1, -1, 2 * (width + height), -1, 0, 0);
            for (int index = 0; index < field.Length; index++) field[index] = unchecked((short)map[index]);
            return result;
        }
        public static int Fill(short[] field,int width,int height,int seedX,int seedY,int targetX,int targetY)
        {
            if(field==null) throw new ArgumentNullException(nameof(field));
            if(width<1||height<1||width>256||height>256||(long)width*height!=field.LongLength)
                throw new ArgumentException("A bounded complete source wave map is required.");
            if(seedX<0||seedY<0||targetX<0||targetY<0||seedX>=width||targetX>=width||seedY>=height||targetY>=height)
                throw new ArgumentOutOfRangeException(nameof(seedX));
            ushort[] map=new ushort[field.Length];
            for(int i=0;i<field.Length;i++)
            {
                if(field[i]!=0&&field[i]!=-1) throw new NotSupportedException("Only the source zero/free and minus-one/blocked map is projected.");
                map[i]=unchecked((ushort)field[i]);
            }
            if(field[seedY*width+seedX]!=0||field[targetY*width+targetX]!=0)
                throw new ArgumentException("Source55c9a0 checks both endpoints before entering this wave branch.");
            int result=Calculate(map,width,0,0,width-1,height-1,seedX,seedY,targetX,targetY,2*(width+height),-1,0,0);
            for(int i=0;i<field.Length;i++) field[i]=unchecked((short)map[i]);
            return result;
        }

        /// <summary>
        /// Forward branch used by55b9e0: the origin is the wave seed and its
        /// preferred neighbor receives the source first-iteration bias.
        /// The requested target and even the seed may initially be blocked;
        /// native5578a0 overwrites the seed with1. Existing Fill remains the
        /// reverse55c9a0 entry with both free endpoints and preference-1.
        /// </summary>
        public static int FillFromOrigin(short[] field,int width,int height,int originX,int originY,
                                         int targetX,int targetY,int preferredHeading=0)
        {
            if(field==null) throw new ArgumentNullException(nameof(field));
            if(width<1||height<1||width>256||height>256||(long)width*height!=field.LongLength)
                throw new ArgumentException("A bounded complete source wave map is required.");
            if(originX<0||originY<0||targetX<0||targetY<0||originX>=width||targetX>=width||originY>=height||targetY>=height)
                throw new ArgumentOutOfRangeException(nameof(originX));
            if(preferredHeading < -1 || preferredHeading > 7)
                throw new ArgumentOutOfRangeException(nameof(preferredHeading));
            ushort[] map=new ushort[field.Length];
            for(int i=0;i<field.Length;i++)
            {
                if(field[i]!=0&&field[i]!=-1)
                    throw new NotSupportedException("Only source zero/free and minus-one/blocked input is projected.");
                map[i]=unchecked((ushort)field[i]);
            }
            int result=Calculate(map,width,0,0,width-1,height-1,originX,originY,targetX,targetY,
                                 2*(width+height),preferredHeading,0,0);
            for(int i=0;i<field.Length;i++) field[i]=unchecked((short)map[i]);
            return result;
        }
        private static int ReadInt32(ushort[] words,int index) => unchecked((int)((uint)words[index]|(uint)words[index+1]<<16));
        private static void WriteInt32(ushort[] words,int index,int value)
        { unchecked { words[index]=(ushort)value;words[index+1]=(ushort)(value>>16); } }
        private static int Calculate(ushort[] map,int param_2,int param_3,int param_4,int param_5,int param_6,
                                     int param_7,int param_8,int param_9,int param_10,int param_11,int param_12,int param_13,int param_14)
        {
            // Address labels retain the original scanline control flow. The
            // additional flow labels only lower C jumps into scopes that C#
            // cannot enter. Queue offsets are native16-byte records measured
            // in managed16-bit words; map offsets likewise use word indices.
            unchecked
            {
                int iVar1=0,iVar5=0,iVar7=0,iVar11=0;
                uint uVar6=0;
                ushort uVar3=0,uVar4=0,sVar8=0,uVar12=0;
                int psVar2=0,puVar9=0,puVar10=0;
                int local_60=0,local_5c=0,local_58=0,local_54=0,local_50=0,local_4c=0,local_48=0;
                int local_44=0,local_40=0,local_3c=0,local_38=0,local_34=0,local_30=0,local_2c=0;
                int local_28=0,local_24=0,local_20=0,local_1c=0,local_18=0,local_14=0,local_10=0,local_c=0,local_8=0,local_4=0;
                // Every emitted nonempty segment owns newly labelled cells.
                // Traversal never turns a labelled cell back into a free0;
                // the optional first-neighbor bias also leaves it nonzero.
                // With no16-bit cost wrap, cells+4 therefore covers the seed's
                // four initial segments without native pointer reallocation.
                int capacity = map.Length + 4;
                ushort[] queue = new ushort[capacity * 16];
                int Enqueue(short direction)
                {
                    if(local_2c >= capacity) throw new InvalidOperationException("Source wave frontier exceeded its proven map bound.");
                    int at=local_2c-1;
                    while(at>=0 && ReadInt32(queue,local_24+at*8+4)>local_4)
                    {
                        Array.Copy(queue,local_24+at*8,queue,local_24+(at+1)*8,8);
                        at--;
                    }
                    int record=local_24+(at+1)*8;
                    queue[record]=(ushort)direction;queue[record+1]=(ushort)local_c;
                    WriteInt32(queue,record+2,local_8);WriteInt32(queue,record+4,local_4);
                    queue[record+6]=(ushort)local_14;queue[record+7]=(ushort)local_10;
                    local_2c++;local_1c+=8;local_4=0x7fff;local_c=(short)queue[local_60+1];
                    return 0;
                }
                iVar1 = (int)(param_2);
                local_50 = (int)(0);
                local_30 = (int)(capacity);
                local_28 = (int)(0);
                local_20 = (int)((local_28 + (local_30 * 8)));
                local_5c = (int)(param_7);
                local_58 = (int)(param_8);
                puVar10 = (int)(((0 + (((param_2 * param_8) + param_7) * 2))) / 2);
                local_38 = (int)(4);
                local_54 = (int)(30000);
                map[puVar10] = (ushort)(1);
                sVar8 = (ushort)((short)(param_7));
                queue[local_20 + 0x1e] = (ushort)(sVar8);
                param_2 = (int)(0);
                queue[local_20 + 0x16] = (ushort)(sVar8);
                queue[local_20 + 0xe] = (ushort)(sVar8);
                queue[local_20 + 6] = (ushort)(sVar8);
                sVar8 = (ushort)((short)(param_8));
                queue[local_20 + 0x1f] = (ushort)(sVar8);
                queue[local_20 + 0x17] = (ushort)(sVar8);
                queue[local_20 + 0xf] = (ushort)(sVar8);
                queue[local_20 + 7] = (ushort)(sVar8);
                queue[local_20 + 0x1a] = (ushort)(1);
                queue[local_20 + 0x1b] = (ushort)(0);
                queue[local_20 + 0x12] = (ushort)(1);
                queue[local_20 + 0x13] = (ushort)(0);
                queue[local_20 + 10] = (ushort)(1);
                queue[local_20 + 0xb] = (ushort)(0);
                queue[local_20 + 2] = (ushort)(1);
                queue[local_20 + 3] = (ushort)(0);
                queue[local_20] = (ushort)(0);
                queue[local_20 + 8] = (ushort)(2);
                queue[local_20 + 0x10] = (ushort)(4);
                queue[local_20 + 0x18] = (ushort)(6);
                queue[local_20 + 0x19] = (ushort)(0);
                queue[local_20 + 0x11] = (ushort)(0);
                queue[local_20 + 9] = (ushort)(0);
                queue[local_20 + 1] = (ushort)(0);
                local_24 = (int)(local_28);
                if (!(0 < param_11)) goto _flow_1;
                _flow_2:;
                local_60 = (int)(local_20);
                local_4 = (int)(0x7fff);
                local_2c = (int)(0);
                local_1c = (int)(local_24);
                local_18 = (int)(0);
                if (!(0 < local_38)) goto _flow_4;
                _flow_5:;
                local_40 = (int)((int)((short)queue[local_60 + 1]));
                local_34 = (int)((int)((short)queue[local_60]));
                iVar11 = (int)(ReadInt32(queue,(local_60 + 2)));
                local_8 = (int)(0);
                local_c = (int)(local_40);
                switch ((short)queue[local_60]) {
                case 0: goto _flow_8;
                case 2: goto _flow_9;
                case 4: goto _flow_10;
                case 6: goto _flow_11;
                default: goto _flow_7;
                }
                _flow_8:;
                if (!((short)queue[local_60 + 6] < param_5)) goto _flow_12;
                local_4c = (int)(0);
                local_44 = (int)(-(1));
                local_48 = (int)(-(1));
                local_3c = (int)(-(iVar1));
                local_5c = (int)(((short)queue[local_60 + 6] + 1));
                local_10 = (int)((int)((short)queue[local_60 + 7]));
                local_58 = (int)((local_10 + 1));
                puVar10 = (int)(((0 + (((local_58 * iVar1) + local_5c) * 2))) / 2);
                iVar7 = (int)(((map[(((puVar10 * 2) - ((iVar1 * 2) + 2))) / 2] & 0x3fff) + 3));
                local_14 = (int)(local_5c);
                if (!(((local_58 <= param_6) && (iVar7 <= ((param_11 * 2) + 2))) && ((short)(map[puVar10]) == local_40))) goto _flow_13;
                map[puVar10] = (ushort)((ushort)(iVar7));
                local_10 = (int)(local_58);
                local_4 = (int)(iVar7);
                if (!(local_40 == 0)) goto _flow_14;
                goto LAB_00557c47;
                _flow_14:;
                map[puVar10] = (ushort)(((ushort)(iVar7) | 0x4000));
                local_8 = (int)(1);
                _flow_13:;
                goto _flow_7;
                _flow_12:;
                goto LAB_00557f9b;
                _flow_9:;
                if (!((short)queue[local_60 + 7] <= param_4)) goto _flow_15;
                goto LAB_00557f9b;
                _flow_15:;
                local_4c = (int)(-(1));
                local_3c = (int)(-(1));
                local_44 = (int)(iVar1);
                local_48 = (int)(0);
                local_14 = (int)((int)((short)queue[local_60 + 6]));
                local_5c = (int)((local_14 + 1));
                local_58 = (int)(((short)queue[local_60 + 7] + -(1)));
                puVar10 = (int)(((0 + (((local_58 * iVar1) + local_5c) * 2))) / 2);
                iVar7 = (int)(((map[puVar10 + (iVar1 + -(1))] & 0x3fff) + 3));
                local_10 = (int)(local_58);
                if (!(((param_5 < local_5c) || (((param_11 * 2) + 2) < iVar7)) || ((short)(map[puVar10]) != local_40))) goto _flow_17;
                LAB_00557d0e:;
                local_48 = (int)(0);
                local_58 = (int)(local_10);
                goto _flow_16;
                _flow_17:;
                map[puVar10] = (ushort)((ushort)(iVar7));
                local_14 = (int)(local_5c);
                local_4 = (int)(iVar7);
                if (!(local_40 == 0)) goto _flow_18;
                goto LAB_00557d03;
                _flow_18:;
                map[puVar10] = (ushort)(((ushort)(iVar7) | 0x4000));
                local_8 = (int)(1);
                _flow_16:;
                goto _flow_7;
                _flow_10:;
                if (!((short)queue[local_60 + 6] <= param_3)) goto _flow_19;
                goto LAB_00557f9b;
                _flow_19:;
                local_44 = (int)(1);
                local_48 = (int)(1);
                local_5c = (int)(((short)queue[local_60 + 6] + -(1)));
                local_4c = (int)(0);
                local_10 = (int)((int)((short)queue[local_60 + 7]));
                local_58 = (int)((local_10 + -(1)));
                local_3c = (int)(iVar1);
                puVar10 = (int)(((0 + (((local_58 * iVar1) + local_5c) * 2))) / 2);
                iVar7 = (int)(((map[puVar10 + (iVar1 + 1)] & 0x3fff) + 3));
                local_14 = (int)(local_5c);
                if (!(((local_58 < param_4) || (((param_11 * 2) + 2) < iVar7)) || ((short)(map[puVar10]) != local_40))) goto _flow_21;
                goto _flow_20;
                _flow_21:;
                map[puVar10] = (ushort)((ushort)(iVar7));
                local_10 = (int)(local_58);
                local_4 = (int)(iVar7);
                if (!(local_40 != 0)) goto _flow_22;
                map[puVar10] = (ushort)(((ushort)(iVar7) | 0x4000));
                _flow_22:;
                LAB_00557c47:;
                local_4c = (int)(0);
                local_8 = (int)(1);
                local_5c = (int)(local_14);
                local_58 = (int)(local_10);
                _flow_20:;
                goto _flow_7;
                _flow_11:;
                if (!(param_6 <= (short)queue[local_60 + 7])) goto _flow_23;
                goto LAB_00557f9b;
                _flow_23:;
                local_44 = (int)(-(iVar1));
                local_4c = (int)(1);
                local_3c = (int)(1);
                local_14 = (int)((int)((short)queue[local_60 + 6]));
                local_5c = (int)((local_14 + -(1)));
                local_10 = (int)(((short)queue[local_60 + 7] + 1));
                puVar10 = (int)(((0 + (((local_10 * iVar1) + local_5c) * 2))) / 2);
                iVar7 = (int)(((map[puVar10 + (1 - iVar1)] & 0x3fff) + 3));
                if (!(((local_5c < param_3) || (((param_11 * 2) + 2) < iVar7)) || ((short)(map[puVar10]) != local_40))) goto _flow_24;
                goto LAB_00557d0e;
                _flow_24:;
                map[puVar10] = (ushort)((ushort)(iVar7));
                local_14 = (int)(local_5c);
                local_4 = (int)(iVar7);
                if (!(local_40 != 0)) goto _flow_25;
                map[puVar10] = (ushort)(((ushort)(iVar7) | 0x4000));
                _flow_25:;
                LAB_00557d03:;
                local_48 = (int)(0);
                local_8 = (int)(1);
                local_5c = (int)(local_14);
                local_58 = (int)(local_10);
                _flow_7:;
                iVar7 = (int)(local_3c);
                local_5c = (int)((local_5c + local_4c));
                local_58 = (int)((local_58 + local_48));
                puVar10 = (int)((puVar10 + local_3c));
                _flow_26:;
                if (!(iVar11 != 0)) goto _flow_27;
                _flow_28:;
                if (!(((short)(map[puVar10]) == local_c) && (((iVar5 = (int)(((map[puVar10 + local_44] & 0x3fff) + 2))) == iVar5) && (iVar5 <= ((param_11 * 2) + 2))))) goto _flow_29;
                if (!(iVar5 < local_4)) goto _flow_30;
                local_4 = (int)(iVar5);
                _flow_30:;
                map[puVar10] = (ushort)((ushort)(iVar5));
                if (!(local_c != 0)) goto _flow_31;
                map[puVar10] = (ushort)(((ushort)(iVar5) | 0x4000));
                _flow_31:;
                puVar10 = (int)((puVar10 + iVar7));
                iVar11 = (int)((iVar11 + -(1)));
                local_8 = (int)((local_8 + 1));
                if (!((local_58 == param_10) && (local_5c == param_9))) goto _flow_32;
                if (!(param_14 < 1)) goto _flow_33;
                goto LAB_00558ed3;
                _flow_33:;
                local_54 = (int)((param_14 + 1));
                _flow_32:;
                local_5c = (int)((local_5c + local_4c));
                local_58 = (int)((local_58 + local_48));
                if (!(iVar11 == 0)) goto _flow_34;
                goto LAB_00557ec0;
                _flow_34:;
                goto _flow_28;
                _flow_29:;
                if (!(iVar11 == 0)) goto _flow_35;
                goto _flow_27;
                _flow_35:;
                if (!((local_8 != 0) && (((local_50 = (int)(Enqueue((short)((short)(local_34))))) == local_50) && (local_50 != 0)))) goto _flow_36;
                goto LAB_00558ed7;
                _flow_36:;
                _flow_37:;
                if (!(((int)(((map[puVar10 + local_44] & 0x3fff) + 2)) <= ((param_11 * 2) + 2)) && (((short)(map[puVar10]) == local_40) || ((short)(map[puVar10]) == param_13)))) goto _flow_39;
                goto _flow_38;
                _flow_39:;
                puVar10 = (int)((puVar10 + iVar7));
                iVar11 = (int)((iVar11 + -(1)));
                if (!((local_58 == param_10) && (local_5c == param_9))) goto _flow_40;
                if (!(param_14 < 1)) goto _flow_41;
                goto LAB_00558ed3;
                _flow_41:;
                local_54 = (int)((param_14 + 1));
                _flow_40:;
                local_5c = (int)((local_5c + local_4c));
                local_58 = (int)((local_58 + local_48));
                if (iVar11 != 0) goto _flow_37;
                _flow_38:;
                local_14 = (int)(local_5c);
                local_8 = (int)(0);
                local_10 = (int)(local_58);
                if (!(iVar11 == 0)) goto _flow_42;
                goto _flow_27;
                _flow_42:;
                local_c = (int)((int)((short)(map[puVar10])));
                goto _flow_26;
                _flow_27:;
                LAB_00557ec0:;
                if (!(((((param_3 <= local_5c) && (local_5c <= param_5)) && (param_4 <= local_58)) && ((local_58 <= param_6) && (((iVar11 = (int)(((map[puVar10 + (local_44 - local_3c)] & 0x3fff) + 3))) == iVar11) && (iVar11 <= ((param_11 * 2) + 2))))) && ((short)(map[puVar10]) == local_c))) goto _flow_43;
                if (!(iVar11 < local_4)) goto _flow_44;
                local_4 = (int)(iVar11);
                _flow_44:;
                map[puVar10] = (ushort)((ushort)(iVar11));
                if (!(local_c != 0)) goto _flow_45;
                map[puVar10] = (ushort)(((ushort)(iVar11) | 0x4000));
                _flow_45:;
                local_8 = (int)((local_8 + 1));
                if (!((local_58 == param_10) && (local_5c == param_9))) goto _flow_46;
                if (!(param_14 < 1)) goto _flow_47;
                goto LAB_00558ed3;
                _flow_47:;
                local_54 = (int)((param_14 + 1));
                _flow_46:;
                _flow_43:;
                if (!((local_8 != 0) && (((local_50 = (int)(Enqueue((short)((short)(local_34))))) == local_50) && (local_50 != 0)))) goto _flow_48;
                goto LAB_00558ed7;
                _flow_48:;
                LAB_00557f9b:;
                local_18 = (int)((local_18 + 1));
                local_60 = (int)((local_60 + 8));
                if (local_18 < local_38) goto _flow_5;

                _flow_4:;
                local_60 = (int)(local_20);
                local_18 = (int)(0);
                if (!(0 < local_38)) goto _flow_49;
                LAB_00557fe5:;
                switch ((short)queue[local_60]) {
                case 0: goto _flow_51;
                default: goto _flow_52;
                case 2: goto _flow_53;
                case 4: goto _flow_54;
                case 6: goto _flow_55;
                }
                _flow_51:;
                goto switchD_00557ff1_caseD_0;
                _flow_52:;
                goto switchD_00557ff1_caseD_1;
                _flow_53:;
                local_14 = (int)(((short)queue[local_60 + 6] + 1));
                if (!(local_14 <= param_5)) goto _flow_56;
                iVar11 = (int)((int)((short)queue[local_60 + 7]));
                local_58 = (int)((iVar11 + 1));
                puVar10 = (int)(((0 + (((local_58 * iVar1) + local_14) * 2))) / 2);
                uVar6 = (uint)((map[(((puVar10 * 2) - ((iVar1 * 2) + 2))) / 2] & 0x3fff));
                iVar7 = (int)((uVar6 + 3));
                if (!(((param_6 < local_58) || (((local_c = (int)((int)((short)(map[puVar10])))) == local_c) && (local_c != (short)queue[local_60 + 1]))) || (((param_11 * 2) + 2) < iVar7))) goto _flow_58;
                iVar7 = (int)(0);
                local_8 = (int)(0);
                local_10 = (int)(iVar11);
                local_c = (int)((int)((short)queue[local_60 + 1]));
                goto _flow_57;
                _flow_58:;
                uVar4 = (ushort)((ushort)(iVar7));
                map[puVar10] = (ushort)(uVar4);
                if (!(local_c != 0)) goto _flow_59;
                map[puVar10] = (ushort)((uVar4 | 0x4000));
                _flow_59:;
                iVar7 = (int)(1);
                local_8 = (int)(1);
                local_10 = (int)(local_58);
                if (!(local_14 == param_9)) goto _flow_60;
                local_10 = (int)(local_58);
                if (!(local_58 == param_10)) goto _flow_61;
                local_10 = (int)(local_58);
                if (!(param_14 < 1)) goto _flow_62;
                goto LAB_00558ed3;
                _flow_62:;
                local_54 = (int)((param_14 + 1));
                local_10 = (int)(local_58);
                _flow_61:;
                _flow_60:;
                _flow_57:;
                iVar5 = (int)((uVar6 + 2));
                if (!(((param_11 * 2) + 2) < iVar5)) goto _flow_64;
                LAB_005584ac:;
                if (!(iVar7 == 0)) goto _flow_65;
                goto LAB_005584cd;
                _flow_65:;
                goto _flow_63;
                _flow_64:;
                puVar9 = (int)((puVar10 + -(iVar1)));
                uVar4 = (ushort)((ushort)(iVar5));
                if (!((short)(map[puVar9]) == local_c)) goto _flow_66;
                map[puVar9] = (ushort)(uVar4);
                if (!(local_c != 0)) goto _flow_67;
                map[puVar9] = (ushort)((uVar4 | 0x4000));
                _flow_67:;
                iVar7 = (int)((local_8 + 1));
                local_8 = (int)(iVar7);
                if (!((local_14 == param_9) && (iVar11 == param_10))) goto _flow_68;
                if (!(0 < param_14)) goto _flow_69;
                local_54 = (int)((param_14 + 1));
                goto LAB_005584ac;
                _flow_69:;
                goto LAB_00558ed3;
                _flow_68:;
                goto LAB_005584ac;
                _flow_66:;
                if (!((short)(map[puVar9]) != param_13)) goto _flow_70;
                goto LAB_005584ac;
                _flow_70:;
                if (!((iVar7 != 0) && (((local_50 = (int)(Enqueue((short)(0)))) == local_50) && (local_50 != 0)))) goto _flow_71;
                goto LAB_00558ed7;
                _flow_71:;
                local_c = (int)(param_13);
                map[puVar9] = (ushort)(uVar4);
                if (!(param_13 != 0)) goto _flow_72;
                map[puVar9] = (ushort)((uVar4 | 0x4000));
                _flow_72:;
                local_8 = (int)(1);
                if (!((local_14 == param_9) && ((local_58 + -(1)) == param_10))) goto _flow_73;
                if (!(param_14 < 1)) goto _flow_74;
                goto LAB_00558ed3;
                _flow_74:;
                local_54 = (int)((param_14 + 1));
                _flow_73:;
                _flow_63:;
                local_50 = (int)(Enqueue((short)(0)));
                if (!(local_50 != 0)) goto _flow_75;
                goto LAB_00558ed7;
                _flow_75:;
                _flow_56:;
                LAB_005584cd:;
                local_14 = (int)(((int)((short)queue[local_60 + 6]) - ReadInt32(queue,(local_60 + 2))));
                if (!(param_3 <= local_14)) goto _flow_76;
                local_58 = (int)((int)((short)queue[local_60 + 7]));
                iVar11 = (int)(((local_58 * iVar1) + local_14));
                puVar10 = (int)(((0 + (iVar11 * 2))) / 2);
                local_c = (int)((int)((short)(map[puVar10])));
                uVar6 = (uint)((map[(((0 + 2) + (iVar11 * 2))) / 2] & 0x3fff));
                iVar11 = (int)((uVar6 + 2));
                if (!(((local_c == (short)queue[local_60 + 1]) || (local_c == param_13)) && (iVar11 <= ((param_11 * 2) + 2)))) goto _flow_78;
                uVar4 = (ushort)((ushort)(iVar11));
                map[puVar10] = (ushort)(uVar4);
                if (!(local_c != 0)) goto _flow_79;
                map[puVar10] = (ushort)((uVar4 | 0x4000));
                _flow_79:;
                local_8 = (int)(1);
                local_10 = (int)(local_58);
                if (!((local_14 == param_9) && (local_58 == param_10))) goto _flow_80;
                if (!(param_14 < 1)) goto _flow_81;
                goto LAB_00558ed3;
                _flow_81:;
                local_54 = (int)((param_14 + 1));
                _flow_80:;
                goto _flow_77;
                _flow_78:;
                local_10 = (int)((local_58 + 1));
                local_8 = (int)(0);
                local_c = (int)((int)((short)queue[local_60 + 1]));
                _flow_77:;
                iVar11 = (int)((uVar6 + 3));
                if (!(((local_58 < param_6) && (iVar11 <= ((param_11 * 2) + 2))) && ((short)(map[puVar10 + iVar1]) == local_c))) goto _flow_82;
                uVar4 = (ushort)((ushort)(iVar11));
                map[puVar10 + iVar1] = (ushort)(uVar4);
                if (!(local_c != 0)) goto _flow_83;
                map[puVar10 + iVar1] = (ushort)((uVar4 | 0x4000));
                _flow_83:;
                local_8 = (int)((local_8 + 1));
                if (!((local_14 == param_9) && ((local_58 + 1) == param_10))) goto _flow_84;
                if (!(param_14 < 1)) goto _flow_85;
                goto LAB_00558ed3;
                _flow_85:;
                local_54 = (int)((param_14 + 1));
                _flow_84:;
                _flow_82:;
                if (!(local_8 != 0)) goto _flow_86;
                uVar12 = (ushort)(4);
                goto LAB_00558a3f;
                _flow_86:;
                _flow_76:;
                goto switchD_00557ff1_caseD_1;
                _flow_54:;
                local_10 = (int)(((short)queue[local_60 + 7] + -(1)));
                if (!(param_4 <= local_10)) goto _flow_87;
                iVar11 = (int)((int)((short)queue[local_60 + 6]));
                local_5c = (int)((iVar11 + 1));
                puVar10 = (int)(((0 + (((local_10 * iVar1) + local_5c) * 2))) / 2);
                uVar4 = (ushort)(map[puVar10 + (iVar1 + -(1))]);
                iVar7 = (int)(((uVar4 & 0x3fff) + 3));
                if (!(((param_5 < local_5c) || (((local_c = (int)((int)((short)(map[puVar10])))) == local_c) && (local_c != (short)queue[local_60 + 1]))) || (((param_11 * 2) + 2) < iVar7))) goto _flow_89;
                iVar7 = (int)(0);
                local_8 = (int)(0);
                local_14 = (int)(iVar11);
                local_c = (int)((int)((short)queue[local_60 + 1]));
                goto _flow_88;
                _flow_89:;
                uVar3 = (ushort)((ushort)(iVar7));
                map[puVar10] = (ushort)(uVar3);
                if (!(local_c != 0)) goto _flow_90;
                map[puVar10] = (ushort)((uVar3 | 0x4000));
                _flow_90:;
                iVar7 = (int)(1);
                local_8 = (int)(1);
                if (!((local_10 == param_10) && (local_5c == param_9))) goto _flow_91;
                local_14 = (int)(local_5c);
                if (!(param_14 < 1)) goto _flow_92;
                goto LAB_00558ed3;
                _flow_92:;
                local_54 = (int)((param_14 + 1));
                _flow_91:;
                local_14 = (int)(local_5c);
                _flow_88:;
                iVar5 = (int)(((uVar4 & 0x3fff) + 2));
                if (!(((param_11 * 2) + 2) < iVar5)) goto _flow_94;
                LAB_005588c1:;
                if (!(iVar7 == 0)) goto _flow_95;
                goto LAB_005588e6;
                _flow_95:;
                goto _flow_93;
                _flow_94:;
                uVar4 = (ushort)((ushort)(iVar5));
                if (!((short)(map[puVar10 + -(1)]) == local_c)) goto _flow_96;
                map[puVar10 + -(1)] = (ushort)(uVar4);
                if (!(local_c != 0)) goto _flow_97;
                map[puVar10 + -(1)] = (ushort)((uVar4 | 0x4000));
                _flow_97:;
                iVar7 = (int)((local_8 + 1));
                local_8 = (int)(iVar7);
                if (!((local_10 == param_10) && (iVar11 == param_9))) goto _flow_98;
                if (!(0 < param_14)) goto _flow_99;
                local_54 = (int)((param_14 + 1));
                goto LAB_005588c1;
                _flow_99:;
                goto LAB_00558ed3;
                _flow_98:;
                goto LAB_005588c1;
                _flow_96:;
                if (!((short)(map[puVar10 + -(1)]) != param_13)) goto _flow_100;
                goto LAB_005588c1;
                _flow_100:;
                if (!((iVar7 != 0) && (((local_50 = (int)(Enqueue((short)(2)))) == local_50) && (local_50 != 0)))) goto _flow_101;
                goto LAB_00558ed7;
                _flow_101:;
                local_c = (int)(param_13);
                map[puVar10 + -(1)] = (ushort)(uVar4);
                if (!(param_13 != 0)) goto _flow_102;
                map[puVar10 + -(1)] = (ushort)((uVar4 | 0x4000));
                _flow_102:;
                local_8 = (int)(1);
                if (!((local_10 == param_10) && ((local_5c + -(1)) == param_9))) goto _flow_103;
                if (!(param_14 < 1)) goto _flow_104;
                goto LAB_00558ed3;
                _flow_104:;
                local_54 = (int)((param_14 + 1));
                _flow_103:;
                _flow_93:;
                local_50 = (int)(Enqueue((short)(2)));
                if (!(local_50 != 0)) goto _flow_105;
                goto LAB_00558ed7;
                _flow_105:;
                _flow_87:;
                LAB_005588e6:;
                local_10 = (int)(((int)((short)queue[local_60 + 7]) + ReadInt32(queue,(local_60 + 2))));
                if (!(local_10 <= param_6)) goto _flow_106;
                local_5c = (int)((int)((short)queue[local_60 + 6]));
                puVar10 = (int)(((0 + (((local_10 * iVar1) + local_5c) * 2))) / 2);
                uVar4 = (ushort)(map[puVar10 + -(iVar1)]);
                local_c = (int)((int)((short)(map[puVar10])));
                iVar11 = (int)(((uVar4 & 0x3fff) + 2));
                if (!(((local_c == (short)queue[local_60 + 1]) || (local_c == param_13)) && (iVar11 <= ((param_11 * 2) + 2)))) goto _flow_108;
                uVar3 = (ushort)((ushort)(iVar11));
                map[puVar10] = (ushort)(uVar3);
                if (!(local_c != 0)) goto _flow_109;
                map[puVar10] = (ushort)((uVar3 | 0x4000));
                _flow_109:;
                local_8 = (int)(1);
                local_14 = (int)(local_5c);
                if (!((local_10 == param_10) && (local_5c == param_9))) goto _flow_110;
                if (!(param_14 < 1)) goto _flow_111;
                goto LAB_00558ed3;
                _flow_111:;
                local_54 = (int)((param_14 + 1));
                _flow_110:;
                goto _flow_107;
                _flow_108:;
                local_14 = (int)((local_5c + 1));
                local_8 = (int)(0);
                local_c = (int)((int)((short)queue[local_60 + 1]));
                _flow_107:;
                iVar11 = (int)(((uVar4 & 0x3fff) + 3));
                if (!(((local_5c < param_5) && (iVar11 <= ((param_11 * 2) + 2))) && ((short)(map[puVar10 + 1]) == local_c))) goto _flow_112;
                uVar4 = (ushort)((ushort)(iVar11));
                map[puVar10 + 1] = (ushort)(uVar4);
                if (!(local_c != 0)) goto _flow_113;
                map[puVar10 + 1] = (ushort)((uVar4 | 0x4000));
                _flow_113:;
                local_8 = (int)((local_8 + 1));
                if (!((local_10 == param_10) && ((local_5c + 1) == param_9))) goto _flow_114;
                if (!(param_14 < 1)) goto _flow_115;
                goto LAB_00558ed3;
                _flow_115:;
                local_54 = (int)((param_14 + 1));
                _flow_114:;
                _flow_112:;
                if (!(local_8 != 0)) goto _flow_116;
                uVar12 = (ushort)(6);
                goto LAB_00558a3f;
                _flow_116:;
                _flow_106:;
                goto switchD_00557ff1_caseD_1;
                _flow_55:;
                local_14 = (int)(((short)queue[local_60 + 6] + -(1)));
                if (!(param_3 <= local_14)) goto _flow_117;
                iVar11 = (int)((int)((short)queue[local_60 + 7]));
                local_58 = (int)((iVar11 + -(1)));
                puVar10 = (int)(((0 + (((local_58 * iVar1) + local_14) * 2))) / 2);
                uVar4 = (ushort)(map[puVar10 + (iVar1 + 1)]);
                iVar7 = (int)(((uVar4 & 0x3fff) + 3));
                if (!(((local_58 < param_4) || (((local_c = (int)((int)((short)(map[puVar10])))) == local_c) && (local_c != (short)queue[local_60 + 1]))) || (((param_11 * 2) + 2) < iVar7))) goto _flow_119;
                iVar7 = (int)(0);
                local_8 = (int)(0);
                local_10 = (int)(iVar11);
                local_c = (int)((int)((short)queue[local_60 + 1]));
                goto _flow_118;
                _flow_119:;
                uVar3 = (ushort)((ushort)(iVar7));
                map[puVar10] = (ushort)(uVar3);
                if (!(local_c != 0)) goto _flow_120;
                map[puVar10] = (ushort)((uVar3 | 0x4000));
                _flow_120:;
                iVar7 = (int)(1);
                local_8 = (int)(1);
                if (!((local_14 == param_9) && (local_58 == param_10))) goto _flow_121;
                local_10 = (int)(local_58);
                if (!(param_14 < 1)) goto _flow_122;
                goto LAB_00558ed3;
                _flow_122:;
                local_54 = (int)((param_14 + 1));
                _flow_121:;
                local_10 = (int)(local_58);
                _flow_118:;
                iVar5 = (int)(((uVar4 & 0x3fff) + 2));
                if (!(((param_11 * 2) + 2) < iVar5)) goto _flow_124;
                LAB_00558c46:;
                if (!(iVar7 == 0)) goto _flow_125;
                goto LAB_00558c6b;
                _flow_125:;
                goto _flow_123;
                _flow_124:;
                uVar4 = (ushort)((ushort)(iVar5));
                if (!((short)(map[puVar10 + iVar1]) == local_c)) goto _flow_126;
                map[puVar10 + iVar1] = (ushort)(uVar4);
                if (!(local_c != 0)) goto _flow_127;
                map[puVar10 + iVar1] = (ushort)((uVar4 | 0x4000));
                _flow_127:;
                iVar7 = (int)((local_8 + 1));
                local_8 = (int)(iVar7);
                if (!((local_14 == param_9) && (iVar11 == param_10))) goto _flow_128;
                if (!(0 < param_14)) goto _flow_129;
                local_54 = (int)((param_14 + 1));
                goto LAB_00558c46;
                _flow_129:;
                goto LAB_00558ed3;
                _flow_128:;
                goto LAB_00558c46;
                _flow_126:;
                if (!((short)(map[puVar10 + iVar1]) != param_13)) goto _flow_130;
                goto LAB_00558c46;
                _flow_130:;
                if (!((iVar7 != 0) && (((local_50 = (int)(Enqueue((short)(4)))) == local_50) && (local_50 != 0)))) goto _flow_131;
                goto LAB_00558ed7;
                _flow_131:;
                local_c = (int)(param_13);
                map[puVar10 + iVar1] = (ushort)(uVar4);
                if (!(param_13 != 0)) goto _flow_132;
                map[puVar10 + iVar1] = (ushort)((uVar4 | 0x4000));
                _flow_132:;
                local_8 = (int)(1);
                if (!((local_14 == param_9) && ((local_58 + 1) == param_10))) goto _flow_133;
                if (!(param_14 < 1)) goto _flow_134;
                goto LAB_00558ed3;
                _flow_134:;
                local_54 = (int)((param_14 + 1));
                _flow_133:;
                _flow_123:;
                local_50 = (int)(Enqueue((short)(4)));
                if (!(local_50 != 0)) goto _flow_135;
                goto LAB_00558ed7;
                _flow_135:;
                _flow_117:;
                LAB_00558c6b:;
                local_14 = (int)(((int)((short)queue[local_60 + 6]) + ReadInt32(queue,(local_60 + 2))));
                if (!(local_14 <= param_5)) goto _flow_136;
                local_58 = (int)((int)((short)queue[local_60 + 7]));
                iVar11 = (int)(((local_58 * iVar1) + local_14));
                puVar10 = (int)(((0 + (iVar11 * 2))) / 2);
                local_c = (int)((int)((short)(map[puVar10])));
                uVar6 = (uint)((map[(((0 + -(2)) + (iVar11 * 2))) / 2] & 0x3fff));
                iVar11 = (int)((uVar6 + 2));
                if (!(((local_c == (short)queue[local_60 + 1]) || (local_c == param_13)) && (iVar11 <= ((param_11 * 2) + 2)))) goto _flow_138;
                uVar4 = (ushort)((ushort)(iVar11));
                map[puVar10] = (ushort)(uVar4);
                if (!(local_c != 0)) goto _flow_139;
                map[puVar10] = (ushort)((uVar4 | 0x4000));
                _flow_139:;
                local_8 = (int)(1);
                local_10 = (int)(local_58);
                if (!((local_14 == param_9) && (local_58 == param_10))) goto _flow_140;
                if (!(param_14 < 1)) goto _flow_141;
                goto LAB_00558ed3;
                _flow_141:;
                local_54 = (int)((param_14 + 1));
                _flow_140:;
                goto _flow_137;
                _flow_138:;
                local_10 = (int)((local_58 + -(1)));
                local_8 = (int)(0);
                local_c = (int)((int)((short)queue[local_60 + 1]));
                _flow_137:;
                iVar11 = (int)((uVar6 + 3));
                if (!(((param_4 < local_58) && (iVar11 <= ((param_11 * 2) + 2))) && (((puVar9 = (int)((puVar10 + -(iVar1)))) == puVar9) && ((short)(map[puVar9]) == local_c)))) goto _flow_142;
                uVar4 = (ushort)((ushort)(iVar11));
                map[puVar9] = (ushort)(uVar4);
                if (!(local_c != 0)) goto _flow_143;
                map[puVar9] = (ushort)((uVar4 | 0x4000));
                _flow_143:;
                local_8 = (int)((local_8 + 1));
                if (!((local_14 == param_9) && ((local_58 + -(1)) == param_10))) goto _flow_144;
                if (!(param_14 < 1)) goto _flow_145;
                goto LAB_00558ed3;
                _flow_145:;
                local_54 = (int)((param_14 + 1));
                _flow_144:;
                _flow_142:;
                if (!(local_8 != 0)) goto _flow_146;
                local_50 = (int)(Enqueue((short)(0)));
                goto joined_r0x00558dd5;
                _flow_146:;
                _flow_136:;
                goto switchD_00557ff1_caseD_1;

                _flow_49:;
                LAB_00558e19:;
                psVar2 = (int)(local_20);
                if (!(local_2c == 0)) goto _flow_147;
                goto _flow_3;
                _flow_147:;
                local_54 = (int)((local_54 + -(1)));
                if (!(local_54 < 1)) goto _flow_148;
                LAB_00558ed3:;
                param_2 = (int)((param_2 + 1));
                goto _flow_3;
                _flow_148:;
                local_20 = (int)(local_24);
                local_38 = (int)(local_2c);
                local_24 = (int)(psVar2);
                if (!(((((param_2 == 0) && (-(1) < param_12)) && (param_12 < 8)) && (((iVar11 = (int)((DirectionX[param_12] + param_7))) == iVar11) && ((param_3 <= iVar11) && (iVar11 <= param_5)))) && (((iVar7 = (int)((DirectionY[param_12] + param_8))) == iVar7) && ((param_4 <= iVar7) && (iVar7 <= param_6))))) goto _flow_149;
                iVar11 = (int)(((iVar7 * iVar1) + iVar11));
                puVar10 = (int)(((0 + (iVar11 * 2))) / 2);
                uVar4 = (ushort)(map[((0 + (iVar11 * 2))) / 2]);
                if (!((uVar4 & 0x3fff) != 0)) goto _flow_150;
                map[puVar10] = (ushort)((uVar4 - 1));
                _flow_150:;
                _flow_149:;
                param_2 = (int)((param_2 + 1));
                if (param_2 < param_11) goto _flow_2;
                _flow_3:;
                _flow_1:;
                LAB_00558ed7:;
                // Native buffer free; managed arrays have no externally visible deallocation effect.
                if (!(local_50 == 0)) goto _flow_151;
                local_50 = (int)(param_2);
                _flow_151:;
                return local_50;
                switchD_00557ff1_caseD_0:;
                local_10 = (int)(((short)queue[local_60 + 7] + 1));
                if (!(local_10 <= param_6)) goto _flow_152;
                iVar11 = (int)((int)((short)queue[local_60 + 6]));
                local_5c = (int)((iVar11 + -(1)));
                puVar10 = (int)(((0 + (((local_10 * iVar1) + local_5c) * 2))) / 2);
                uVar4 = (ushort)(map[puVar10 + (1 - iVar1)]);
                iVar7 = (int)(((uVar4 & 0x3fff) + 3));
                if (!(((local_5c < param_3) || (((local_c = (int)((int)((short)(map[puVar10])))) == local_c) && (local_c != (short)queue[local_60 + 1]))) || (((param_11 * 2) + 2) < iVar7))) goto _flow_154;
                iVar7 = (int)(0);
                local_8 = (int)(0);
                local_14 = (int)(iVar11);
                local_c = (int)((int)((short)queue[local_60 + 1]));
                goto _flow_153;
                _flow_154:;
                uVar3 = (ushort)((ushort)(iVar7));
                map[puVar10] = (ushort)(uVar3);
                if (!(local_c != 0)) goto _flow_155;
                map[puVar10] = (ushort)((uVar3 | 0x4000));
                _flow_155:;
                iVar7 = (int)(1);
                local_8 = (int)(1);
                if (!((local_10 == param_10) && (local_5c == param_9))) goto _flow_156;
                local_14 = (int)(local_5c);
                if (!(param_14 < 1)) goto _flow_157;
                goto LAB_00558ed3;
                _flow_157:;
                local_54 = (int)((param_14 + 1));
                _flow_156:;
                local_14 = (int)(local_5c);
                _flow_153:;
                iVar5 = (int)(((uVar4 & 0x3fff) + 2));
                if (!(((param_11 * 2) + 2) < iVar5)) goto _flow_159;
                LAB_005581e9:;
                if (!(iVar7 == 0)) goto _flow_160;
                goto LAB_0055820e;
                _flow_160:;
                goto _flow_158;
                _flow_159:;
                uVar4 = (ushort)((ushort)(iVar5));
                if (!((short)(map[puVar10 + 1]) == local_c)) goto _flow_161;
                map[puVar10 + 1] = (ushort)(uVar4);
                if (!(local_c != 0)) goto _flow_162;
                map[puVar10 + 1] = (ushort)((uVar4 | 0x4000));
                _flow_162:;
                iVar7 = (int)((local_8 + 1));
                local_8 = (int)(iVar7);
                if (!((local_10 == param_10) && (iVar11 == param_9))) goto _flow_163;
                if (!(0 < param_14)) goto _flow_164;
                local_54 = (int)((param_14 + 1));
                goto LAB_005581e9;
                _flow_164:;
                goto LAB_00558ed3;
                _flow_163:;
                goto LAB_005581e9;
                _flow_161:;
                if (!((short)(map[puVar10 + 1]) != param_13)) goto _flow_165;
                goto LAB_005581e9;
                _flow_165:;
                if (!((iVar7 != 0) && (((local_50 = (int)(Enqueue((short)(6)))) == local_50) && (local_50 != 0)))) goto _flow_166;
                goto LAB_00558ed7;
                _flow_166:;
                local_c = (int)(param_13);
                map[puVar10 + 1] = (ushort)(uVar4);
                if (!(param_13 != 0)) goto _flow_167;
                map[puVar10 + 1] = (ushort)((uVar4 | 0x4000));
                _flow_167:;
                local_8 = (int)(1);
                if (!((local_10 == param_10) && ((local_5c + 1) == param_9))) goto _flow_168;
                if (!(param_14 < 1)) goto _flow_169;
                goto LAB_00558ed3;
                _flow_169:;
                local_54 = (int)((param_14 + 1));
                _flow_168:;
                _flow_158:;
                local_50 = (int)(Enqueue((short)(6)));
                if (!(local_50 != 0)) goto _flow_170;
                goto LAB_00558ed7;
                _flow_170:;
                _flow_152:;
                LAB_0055820e:;
                local_10 = (int)(((int)((short)queue[local_60 + 7]) - ReadInt32(queue,(local_60 + 2))));
                if (!(param_4 <= local_10)) goto _flow_171;
                local_5c = (int)((int)((short)queue[local_60 + 6]));
                puVar10 = (int)(((0 + (((local_10 * iVar1) + local_5c) * 2))) / 2);
                uVar4 = (ushort)(map[puVar10 + iVar1]);
                local_c = (int)((int)((short)(map[puVar10])));
                iVar11 = (int)(((uVar4 & 0x3fff) + 2));
                if (!(((local_c == (short)queue[local_60 + 1]) || (local_c == param_13)) && (iVar11 <= ((param_11 * 2) + 2)))) goto _flow_173;
                uVar3 = (ushort)((ushort)(iVar11));
                map[puVar10] = (ushort)(uVar3);
                if (!(local_c != 0)) goto _flow_174;
                map[puVar10] = (ushort)((uVar3 | 0x4000));
                _flow_174:;
                local_8 = (int)(1);
                local_14 = (int)(local_5c);
                if (!((local_10 == param_10) && (local_5c == param_9))) goto _flow_175;
                if (!(param_14 < 1)) goto _flow_176;
                goto LAB_00558ed3;
                _flow_176:;
                local_54 = (int)((param_14 + 1));
                _flow_175:;
                goto _flow_172;
                _flow_173:;
                local_14 = (int)((local_5c + -(1)));
                local_8 = (int)(0);
                local_c = (int)((int)((short)queue[local_60 + 1]));
                _flow_172:;
                iVar11 = (int)(((uVar4 & 0x3fff) + 3));
                if (!(((param_3 < local_5c) && (iVar11 <= ((param_11 * 2) + 2))) && ((short)(map[puVar10 + -(1)]) == local_c))) goto _flow_177;
                uVar4 = (ushort)((ushort)(iVar11));
                map[puVar10 + -(1)] = (ushort)(uVar4);
                if (!(local_c != 0)) goto _flow_178;
                map[puVar10 + -(1)] = (ushort)((uVar4 | 0x4000));
                _flow_178:;
                local_8 = (int)((local_8 + 1));
                if (!((local_10 == param_10) && ((local_5c + -(1)) == param_9))) goto _flow_179;
                if (!(param_14 < 1)) goto _flow_180;
                goto LAB_00558ed3;
                _flow_180:;
                local_54 = (int)((param_14 + 1));
                _flow_179:;
                _flow_177:;
                if (!(local_8 != 0)) goto _flow_181;
                uVar12 = (ushort)(2);
                LAB_00558a3f:;
                local_50 = (int)(Enqueue((short)(uVar12)));
                joined_r0x00558dd5:;
                if (!(local_50 != 0)) goto _flow_182;
                goto LAB_00558ed7;
                _flow_182:;
                _flow_181:;
                _flow_171:;
                switchD_00557ff1_caseD_1:;
                local_18 = (int)((local_18 + 1));
                local_60 = (int)((local_60 + 8));
                if (!(local_38 <= local_18)) goto _flow_183;
                goto LAB_00558e19;
                _flow_183:;
                goto LAB_00557fe5;
            }
        }
    }
}
