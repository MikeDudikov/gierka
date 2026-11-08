using System;
using System.Collections.Generic;

namespace AncientConquest.Simulation
{
    /// <summary>
    /// Source560090/560f10/5612f0/55f800 for2..8 normal category0 ships on one
    /// water field. The one-member4cc970 branch bypasses formation entirely.
    /// This assigns cell goals; it does not dispatch commands or move actors.
    /// </summary>
    public static class SourceFleetFormation
    {
        public readonly struct Cell
        {
            public int X { get; }
            public int Y { get; }
            public Cell(int x, int y) { X = x; Y = y; }
        }

        public sealed class Result
        {
            private readonly Cell[] targets;
            private readonly int[] bands;
            private readonly short[] reserved;
            private readonly short[][] fields;
            public int SourceCode { get; }
            public bool Succeeded => SourceCode >= 0;
            public bool UsedMatching { get; }
            public int Count => targets.Length;
            public int FieldCount => fields.Length;
            public Cell GetTarget(int index) => targets[index];
            public int GetBand(int index) => bands[index];
            public short[] CaptureReservedField() => (short[])reserved.Clone();
            // Source call order: cleared goal component, goal wave, origin wave
            // before restoring the blocked clicked cell. These are QA snapshots.
            public short[] CaptureField(int index) => (short[])fields[index].Clone();
            internal Result(int code, bool matching, Cell[] targets, int[] bands,
                            short[] reserved, List<short[]> fields)
            {
                SourceCode = code; UsedMatching = matching;
                this.targets = targets; this.bands = bands; this.reserved = reserved;
                this.fields = fields.ToArray();
            }
        }

        private sealed class Candidate
        {
            internal int X, Y, Radius, OriginCost, Projection;
            internal bool Translated;
        }
        private static readonly int[] Dx = { 1, 1, 0, -1, -1, -1, 0, 1 };
        private static readonly int[] Dy = { 0, -1, -1, -1, 0, 1, 1, 1 };
        private static bool Inside(int x, int y, int width, int height) => x >= 0 && y >= 0 && x < width && y < height;

        public static Result Assign(short[] terrain, int width, int height, Cell[] origins, int goalX, int goalY)
        {
            if (terrain == null) throw new ArgumentNullException(nameof(terrain));
            if (origins == null) throw new ArgumentNullException(nameof(origins));
            if (width < 1 || height < 1 || width > 128 || height > 128 || (long)width * height != terrain.LongLength)
                throw new ArgumentException("A bounded complete water terrain field is required.");
            if (origins.Length < 2 || origins.Length > 8)
                throw new ArgumentOutOfRangeException(nameof(origins), "This source branch requires2..8 homogeneous normal ships.");
            foreach (short value in terrain)
                if (value != 0 && value != -1) throw new NotSupportedException("Only source free0/blocked-1 terrain is supported.");
            foreach (Cell cell in origins)
                if (!Inside(cell.X, cell.Y, width, height)) throw new ArgumentOutOfRangeException(nameof(origins));

            var map = (short[])terrain.Clone();
            var targets = new Cell[origins.Length];
            var bands = new int[origins.Length];
            var fields = new List<short[]>(3);
            Result Finish(int code, bool matching = false) => new Result(code, matching, targets, bands, map, fields);
            if (!Inside(goalX, goalY, width, height)) return Finish(-4);
            int[] xs = new int[origins.Length], ys = new int[origins.Length];
            for (int i = 0; i < origins.Length; i++) { xs[i] = origins[i].X; ys[i] = origins[i].Y; }
            int originalX = Median(xs), originalY = Median(ys), originX = originalX, originY = originalY;
            var goalWave = (short[])map.Clone();
            ClearGoalComponent(goalWave, width, height, goalX, goalY);
            fields.Add((short[])goalWave.Clone());
            int waveCode = SourceWaveField.FillAll(goalWave, width, height, goalX, goalY);
            fields.Add((short[])goalWave.Clone());
            if (waveCode < 1) return Finish(waveCode == 0 ? -4 : waveCode);
            if (map[originY * width + originX] < 0 &&
                !RelocateOrigin(map, goalWave, width, height, ref originX, ref originY)) return Finish(-4);
            var originWave = (short[])map.Clone();
            waveCode = SourceWaveField.FillAll(originWave, width, height, originX, originY);
            fields.Add((short[])originWave.Clone());
            if (waveCode < 1) return Finish(waveCode == 0 ? -4 : waveCode);
            if (map[goalY * width + goalX] < 0) originWave[goalY * width + goalX] = map[goalY * width + goalX];

            var candidates = new List<Candidate>(origins.Length);
            bool Translated(int x, int y)
            {
                foreach (Cell cell in origins)
                    if (cell.X + goalX - originX == x && cell.Y + goalY - originY == y) return true;
                return false;
            }
            void Consider(int x, int y, int radius)
            {
                int cell = y * width + x;
                if (map[cell] != 0 || radius >= 11) return;
                var candidate = new Candidate { X = x, Y = y, Radius = radius,
                    OriginCost = originWave[cell], Translated = Translated(x, y) };
                int index = 0;
                for (; index < candidates.Count; index++)
                {
                    Candidate old = candidates[index];
                    if (candidate.Translated == old.Translated)
                    {
                        if (radius < old.Radius || radius == old.Radius && candidate.OriginCost < old.OriginCost) break;
                    }
                    else if (!candidate.Translated ? radius < old.Radius - 1 : radius <= old.Radius + 1) break;
                }
                if (index >= origins.Length) return;
                candidates.Insert(index, candidate);
                if (candidates.Count > origins.Length) candidates.RemoveAt(origins.Length);
            }
            // Source560f10: right/up/left/down, each with its own direction.
            // Clipped edges must not create extra corners or change stable ties.
            for (int ring = 0; ring <= 10; ring++)
            {
                int left = Math.Max(0, goalX - ring), right = Math.Min(width - 1, goalX + ring);
                int top = Math.Max(0, goalY - ring), bottom = Math.Min(height - 1, goalY + ring);
                int y = bottom;
                if (ring <= bottom - goalY && ring != 0) y--;
                int x;
                if (right - goalX < ring) x = right;
                else
                {
                    for (; y >= top; y--) Consider(right, y, (2 * ring + Math.Abs(y - goalY)) / 2);
                    x = right - 1;
                }
                if (ring == 0) continue;
                if (ring <= goalY - top)
                {
                    for (; x >= left; x--) Consider(x, top, (2 * ring + Math.Abs(x - goalX)) / 2);
                    top++;
                }
                if (ring <= goalX - left)
                {
                    for (; top <= bottom; top++) Consider(left, top, (2 * ring + Math.Abs(top - goalY)) / 2);
                    left++;
                }
                if (ring <= bottom - goalY)
                    for (; left <= right; left++) Consider(left, bottom, (2 * ring + Math.Abs(left - goalX)) / 2);
            }
            if (candidates.Count != origins.Length) return Finish(-4);
            bool exact = true;
            foreach (Candidate cell in candidates)
            {
                map[cell.Y * width + cell.X] = unchecked((short)0x8000);
                if (!cell.Translated) exact = false;
            }
            if (exact)
            {
                for (int index = 0; index < origins.Length; index++)
                    targets[index] = new Cell(origins[index].X + goalX - originX, origins[index].Y + goalY - originY);
                return Finish(0);
            }

            for (int i = 0; i < candidates.Count; i++) { xs[i] = candidates[i].X; ys[i] = candidates[i].Y; }
            int centerX = Median(xs, goalX), centerY = Median(ys, goalY);
            int actorHeading = Approach(goalWave, width, height, originX, originY, centerX, centerY, true);
            int targetHeading = (Approach(originWave, width, height, centerX, centerY, originX, originY, false) - 4) & 7;
            foreach (Candidate cell in candidates) cell.Projection = Project(centerX, centerY, targetHeading, cell.X, cell.Y);
            // Original candidate tie is DESCENDING origin cost (55fb12).
            for (int pass = candidates.Count - 2; pass >= 0; pass--)
                for (int index = 0; index <= pass; index++)
                {
                    Candidate a = candidates[index], b = candidates[index + 1];
                    if (b.Projection < a.Projection || b.Projection == a.Projection && a.OriginCost < b.OriginCost)
                    { candidates[index] = b; candidates[index + 1] = a; }
                }
            var actors = new int[origins.Length];
            var projections = new int[origins.Length];
            for (int i = 0; i < actors.Length; i++)
            { actors[i] = i; projections[i] = Project(originalX, originalY, actorHeading, origins[i].X, origins[i].Y); }
            int GoalCost(int index) => goalWave[origins[index].Y * width + origins[index].X] & 0x7fff;
            for (int pass = actors.Length - 2; pass >= 0; pass--)
                for (int index = 0; index <= pass; index++)
                {
                    int a = actors[index], b = actors[index + 1];
                    if (projections[b] < projections[a] || projections[b] == projections[a] && GoalCost(b) < GoalCost(a))
                    { actors[index] = b; actors[index + 1] = a; }
                }
            int result = 0, third = origins.Length / 3, second = (origins.Length - third + 1) / 2 + third;
            for (int index = 0; index < actors.Length; index++)
            {
                int actor = actors[index]; Candidate candidate = candidates[index];
                targets[actor] = new Cell(candidate.X, candidate.Y);
                bands[actor] = index < third ? 1 : index < second ? 2 : 3;
                result = Math.Max(result, GoalCost(actor));
            }
            return Finish(result, true);
        }

        private static int Median(int[] values, int toward = -1)
        {
            Array.Sort(values);
            int half = values.Length / 2;
            if ((values.Length & 1) != 0) return values[half];
            int sum = values[half - 1] + values[half];
            if ((sum & 1) != 0 && sum / 2 < toward) sum++;
            return sum / 2;
        }

        private static void ClearGoalComponent(short[] map, int width, int height, int x, int y)
        {
            int seed = y * width + x;
            if (map[seed] != -1) return;
            //5732e0's8-connected component result is order independent. This
            // only clears its blocked component; it does not replace the wave.
            var stack = new Stack<int>(); stack.Push(seed); map[seed] = 0;
            while (stack.Count != 0)
            {
                int cell = stack.Pop(), cx = cell % width, cy = cell / width;
                for (int heading = 0; heading < 8; heading++)
                {
                    int nx = cx + Dx[heading], ny = cy + Dy[heading];
                    if (!Inside(nx, ny, width, height) || map[ny * width + nx] != -1) continue;
                    map[ny * width + nx] = 0; stack.Push(ny * width + nx);
                }
            }
        }

        private static bool RelocateOrigin(short[] map, short[] wave, int width, int height, ref int x, ref int y)
        {
            int ox = x, oy = y, bestCost = int.MaxValue, bestMetric = int.MaxValue, bx = x, by = y;
            void Consider(int cx, int cy, int firstIndex, int metric)
            {
                // The native loop deliberately keeps the terrain index fixed
                // at the first cell of each edge while advancing the wave.
                // Confirmed instruction560661; do not "correct" this quirk.
                if (map[firstIndex] != 0) return;
                int cost = wave[cy * width + cx];
                if (cost < bestCost || cost == bestCost && metric < bestMetric)
                { bestCost = cost; bestMetric = metric; bx = cx; by = cy; }
            }
            for (int ring = 1; ring < 4; ring++)
            {
                int left = Math.Max(0, ox - ring), right = Math.Min(width - 1, ox + ring);
                int top = Math.Max(0, oy - ring), bottom = Math.Min(height - 1, oy + ring);
                if (ring <= right - ox)
                    for (int cy = top; cy <= bottom; cy++) Consider(right, cy, top * width + right, 2 * ring + Math.Abs(cy - oy));
                if (ring <= oy - top)
                    for (int cx = left; cx <= right; cx++) Consider(cx, top, top * width + left, 2 * ring + Math.Abs(cx - ox));
                if (ring <= ox - left)
                    for (int cy = top; cy <= bottom; cy++) Consider(left, cy, top * width + left, 2 * ring + Math.Abs(cy - oy));
                if (ring <= bottom - oy)
                    for (int cx = left; cx <= right; cx++) Consider(cx, bottom, bottom * width + left, 2 * ring + Math.Abs(cx - ox));
            }
            if (bestMetric == int.MaxValue) return false;
            x = bx; y = by; return true;
        }

        private static int Approach(short[] wave, int width, int height, int x, int y, int tx, int ty, bool masked)
        {
            int preferred = Direction(x, y, tx, ty), best = 30000, heading = -1;
            for (int index = 0; index < 8; index++)
            {
                int nx = x + Dx[index], ny = y + Dy[index];
                if (!Inside(nx, ny, width, height)) continue;
                int cost = masked ? wave[ny * width + nx] & 0x7fff : wave[ny * width + nx];
                if (cost <= 0) continue;
                if ((index & 1) != 0) cost++;
                if (cost < best || cost == best && index == preferred) { best = cost; heading = index; }
            }
            if (heading < 0) throw new NotSupportedException("Original55f800 did not select an approach heading for this geometry.");
            return heading;
        }

        private static int Direction(int x, int y, int tx, int ty)
        {
            int ax = Math.Abs(tx - x), ay = Math.Abs(ty - y);
            if (ax == 0 && ay == 0) return 127;
            if (ty < y)
            {
                if (tx < x) return ax < ay * 2 ? (ay < ax * 2 ? 3 : 2) : 4;
                return ax < ay * 2 ? (ax * 2 <= ay ? 2 : 1) : 0;
            }
            if (tx < x) return ax < ay * 2 ? (ax * 2 <= ay ? 6 : 5) : 4;
            return ax < ay * 2 ? (ay < ax * 2 ? 7 : 6) : 0;
        }

        private static int Project(int x, int y, int direction, int tx, int ty)
        {
            int a = tx - x, b = ty - y, major = b;
            switch (direction)
            {
                case 1: case 2: major = a; a = -b; break;
                case 3: case 4: major = -b; a = -a; break;
                case 5: case 6: major = -a; a = b; break;
            }
            if ((direction & 1) == 0) return major * 2;
            int value = (a - major) * 4 + 1;
            int quotient = (int)(((long)value * 0x55555555L) >> 32) - value;
            return (quotient >> 1) - (quotient >> 31);
        }
    }
}
