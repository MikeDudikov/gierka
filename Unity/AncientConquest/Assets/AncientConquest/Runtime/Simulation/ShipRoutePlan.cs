using System;

namespace AncientConquest.Simulation
{
    /// <summary>Immutable native5-byte route records, not a live order queue.</summary>
    public sealed class ShipRoutePlan
    {
        private readonly byte[] points;
        public int OriginX => 16;
        public int OriginY => 2;
        public int TargetX { get; }
        public int TargetY { get; }
        public sbyte InitialHeading => 5;
        public sbyte TargetHeading { get; }
        public byte InitialState => TargetHeading == 5 ? (byte)3 : (byte)2;
        public bool CenterGate => TargetHeading == 5;
        public int PathIndex => 1;
        public int PathCount => points.Length / 5;

        internal ShipRoutePlan(byte[] rawPoints, int goalX, int goalY)
        {
            if (rawPoints == null || rawPoints.Length < 10 || rawPoints.Length % 5 != 0 || rawPoints.Length > 577 * 5)
                throw new ArgumentException("A bounded native route needs at least two complete5-byte records.", nameof(rawPoints));
            points = (byte[])rawPoints.Clone(); TargetX = goalX; TargetY = goalY;
            for (int index = 0; index < PathCount; index++)
            {
                int x = ReadCoordinate(index,0), y = ReadCoordinate(index,2);
                if (x < 0 || x >= 24 || y < 0 || y >= 24 || points[index*5+4] > 7)
                    throw new NotSupportedException("Native source route coordinates/headings must remain inside24x24.");
                if (index == 0) continue;
                int dx = x - ReadCoordinate(index-1,0), dy = y - ReadCoordinate(index-1,2);
                sbyte direction = Direction(dx,dy);
                if (points[index*5+4] != unchecked((byte)direction))
                    throw new NotSupportedException("Route records after the first must describe their incoming segment.");
            }
            if (ReadCoordinate(0,0) != OriginX || ReadCoordinate(0,2) != OriginY ||
                ReadCoordinate(PathCount-1,0) != goalX || ReadCoordinate(PathCount-1,2) != goalY)
                throw new NotSupportedException("The route must connect source0b16,2 to its declared target.");
            TargetHeading = Direction(ReadCoordinate(1,0)-OriginX,ReadCoordinate(1,2)-OriginY);
        }

        private int ReadCoordinate(int index,int offset) => unchecked((short)(points[index*5+offset] | points[index*5+offset+1]<<8));
        private static sbyte Direction(int dx,int dy)
        {
            if (dx < -1 || dx > 1 || dy < -1 || dy > 1 || dx == 0 && dy == 0)
                throw new NotSupportedException("A native source route advances by one adjacent cell per record.");
            if (dx == 1) return dy < 0 ? (sbyte)1 : dy > 0 ? (sbyte)7 : (sbyte)0;
            if (dx == -1) return dy < 0 ? (sbyte)3 : dy > 0 ? (sbyte)5 : (sbyte)4;
            return dy < 0 ? (sbyte)2 : (sbyte)6;
        }
        public byte[] CapturePoints() => (byte[])points.Clone();
    }
}
