using System;
using System.Collections.Generic;

namespace AncientConquest.Simulation
{
    /// <summary>
    /// Source55c9a0 over an owned short map (0 free, -1 blocked). Preserves
    /// the original two-segment trial and wave reconstruction/tie order.
    /// This does not construct a ship's map or implement its order policy.
    /// </summary>
    public static class SourcePathfinder
    {
        public sealed class Result
        {
            private readonly byte[] points;
            private readonly short[] field;
            public int PointCount => points.Length / 5;
            public bool Succeeded => PointCount != 0;
            public bool UsedWave { get; }
            public int WaveIterations { get; }
            internal Result(byte[] points, short[] field, bool usedWave, int waveIterations)
            {
                this.points = points; this.field = field;
                UsedWave = usedWave; WaveIterations = waveIterations;
            }
            public byte[] CapturePoints() => (byte[])points.Clone();
            public short[] CaptureWorkingField() => (short[])field.Clone();
        }

        private static readonly int[] Dx = { 1, 1, 0, -1, -1, -1, 0, 1 };
        private static readonly int[] Dy = { 0, -1, -1, -1, 0, 1, 1, 1 };

        public static Result Find(short[] initialField, int width, int height,
                                  int originX, int originY, int targetX, int targetY,
                                  int preferredHeading = 0)
        {
            if (initialField == null) throw new ArgumentNullException(nameof(initialField));
            if (width <= 0 || width > 128 || height <= 0 || height > 128 ||
                (long)width * height != initialField.LongLength)
                throw new ArgumentException("A bounded matching source map is required.");
            if (preferredHeading < -1 || preferredHeading > 7)
                throw new ArgumentOutOfRangeException(nameof(preferredHeading));
            foreach (short value in initialField)
                if (value != 0 && value != -1)
                    throw new NotSupportedException("This source path projection accepts free0/blocked-1 input maps.");
            short[] field = (short[])initialField.Clone();
            if (!Inside(originX, originY, width, height) || !Inside(targetX, targetY, width, height) ||
                field[originY * width + originX] != 0 || field[targetY * width + targetX] != 0)
                return new Result(new byte[0], field, false, 0);
            if (originX == targetX && originY == targetY)
            {
                var same = new List<byte>(10);
                Append(same, originX, originY, preferredHeading);
                Append(same, targetX, targetY, preferredHeading);
                return new Result(same.ToArray(), field, false, 0);
            }
            if (TryDirect(field, width, originX, originY, targetX, targetY, preferredHeading,
                          out int first, out int second, out int cornerX, out int cornerY))
            {
                int count = Math.Max(Math.Abs(targetX - originX), Math.Abs(targetY - originY)) + 1;
                var direct = new List<byte>(count * 5);
                int x = originX, y = originY, heading = first;
                for (int index = 0; index < count; index++)
                {
                    Append(direct, x, y, heading);
                    if (x == cornerX && y == cornerY) heading = second;
                    x += Dx[heading]; y += Dy[heading];
                }
                return new Result(direct.ToArray(), field, false, 0);
            }
            int iterations = SourceWaveField.Fill(field, width, height, targetX, targetY, originX, originY);
            if (iterations < 0 || field[originY * width + originX] == 0)
                return new Result(new byte[0], field, true, iterations);
            var wave = new List<byte>();
            int currentX = originX, currentY = originY, previousHeading = preferredHeading;
            Append(wave, currentX, currentY, 0);
            for (int safety = 0; safety <= width * height; safety++)
            {
                int best = 30000, selected = -1, selectedX = 0, selectedY = 0;
                for (int heading = 1; heading < 8; heading += 2)
                {
                    int x = currentX + Dx[heading], y = currentY + Dy[heading];
                    if (!Inside(x, y, width, height)) continue;
                    if (x == targetX && y == targetY)
                    {
                        Append(wave, x, y, heading);
                        return new Result(wave.ToArray(), field, true, iterations);
                    }
                    int value = field[y * width + x];
                    if (value > 0 && (value + 1 < best || value + 1 == best && previousHeading == heading))
                    {
                        best = value + 1; selected = heading; selectedX = x; selectedY = y;
                    }
                }
                for (int heading = 0; heading < 8; heading += 2)
                {
                    int x = currentX + Dx[heading], y = currentY + Dy[heading];
                    if (!Inside(x, y, width, height)) continue;
                    if (x == targetX && y == targetY)
                    {
                        Append(wave, x, y, heading);
                        return new Result(wave.ToArray(), field, true, iterations);
                    }
                    int value = field[y * width + x];
                    if (value > 0 && (value < best || value == best && previousHeading != selected &&
                                     (previousHeading & 1) == 0))
                    {
                        best = value; selected = heading; selectedX = x; selectedY = y;
                    }
                }
                if (selected < 0) throw new InvalidOperationException("The source wave has no positive predecessor.");
                Append(wave, selectedX, selectedY, selected);
                currentX = selectedX; currentY = selectedY; previousHeading = selected;
            }
            throw new InvalidOperationException("The source wave reconstruction exceeded its map bound.");
        }

        private static bool Inside(int x, int y, int width, int height) =>
            x >= 0 && x < width && y >= 0 && y < height;

        private static void Append(List<byte> result, int x, int y, int heading)
        {
            unchecked
            {
                result.Add((byte)x); result.Add((byte)(x >> 8));
                result.Add((byte)y); result.Add((byte)(y >> 8));
                result.Add((byte)heading);
            }
        }

        private static int Distance(int a, int b)
        {
            int value = Math.Abs(a - b);
            return value > 4 ? 8 - value : value;
        }

        private static bool TryDirect(short[] field, int width, int x, int y, int targetX, int targetY,
                                      int preferred, out int first, out int second,
                                      out int cornerX, out int cornerY)
        {
            int absX = Math.Abs(targetX - x), absY = Math.Abs(targetY - y);
            int horizontal = targetX < x ? 4 : 0;
            int vertical = targetY < y ? 2 : 6;
            int diagonal = targetX < x ? (targetY < y ? 3 : 5) : (targetY < y ? 1 : 7);
            if (absX >= absY * 2) { first = horizontal; second = diagonal; }
            else if (absY >= absX * 2) { first = vertical; second = diagonal; }
            else { first = diagonal; second = absX < absY ? vertical : horizontal; }
            if (absX == 0 || absY == 0 || absX == absY) second = first;
            if (preferred >= 0 && Distance(second, preferred) < Distance(first, preferred))
            {
                int swap = first; first = second; second = swap;
            }
            if (TrySegments(field, width, x, y, absX, absY, first, second, out cornerX, out cornerY)) return true;
            if (first == second) return false;
            int temporary = first; first = second; second = temporary;
            return TrySegments(field, width, x, y, absX, absY, first, second, out cornerX, out cornerY);
        }

        private static bool TrySegments(short[] field, int width, int x, int y, int remainingX, int remainingY,
                                        int first, int second, out int cornerX, out int cornerY)
        {
            do
            {
                x += Dx[first]; y += Dy[first];
                remainingX -= Math.Abs(Dx[first]); remainingY -= Math.Abs(Dy[first]);
                if (field[y * width + x] != 0) { cornerX = x; cornerY = y; return false; }
            } while ((first & 1) != 0 ? remainingX != 0 && remainingY != 0 : remainingX != remainingY);
            cornerX = x; cornerY = y;
            while (remainingX != 0 || remainingY != 0)
            {
                x += Dx[second]; y += Dy[second];
                remainingX -= Math.Abs(Dx[second]); remainingY -= Math.Abs(Dy[second]);
                if (field[y * width + x] != 0) return false;
            }
            return true;
        }
    }
}
