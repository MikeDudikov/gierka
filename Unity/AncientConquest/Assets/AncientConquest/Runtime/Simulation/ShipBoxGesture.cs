using System;

namespace AncientConquest.Simulation
{
    /// <summary>Normal map1 tile64 drag latch, dimensions and50ms rectangle publication.</summary>
    public sealed class ShipBoxGesture
    {
        public bool Candidate { get; private set; }
        public bool Active { get; private set; }
        public bool Visible { get; private set; }
        public int StartX { get; private set; }
        public int StartY { get; private set; }
        public int Width { get; private set; }
        public int Height { get; private set; }
        public int Phase { get; private set; }
        public uint LastMilliseconds { get; private set; }
        public void Begin(int worldX, int worldY)
        {
            Check(worldX, worldY); Cancel(); Candidate = true; StartX = worldX; StartY = worldY;
        }
        public void Move(int worldX, int worldY, uint milliseconds)
        {
            Check(worldX, worldY);
            if (!Candidate) return;
            int w = worldX - StartX + 1, h = worldY - StartY + 1;
            if (!Active)
            {
                if (Math.Abs(w) <= 9 || Math.Abs(h) <= 9) return;
                Active = true; Width = Height = Phase = 0; Visible = false; LastMilliseconds = milliseconds;
                //51cd60 publishes zero dimensions when creating the node. Only
                //a subsequent Move stores the actual signed extent.
            }
            else { Width = w; Height = h; }
        }
        public void Life(uint milliseconds)
        {
            if (!Active || unchecked(milliseconds - LastMilliseconds) <= 49u) return;
            LastMilliseconds = milliseconds; Phase = (Phase + 1) & 31; Visible = true;
        }
        public int[] CellBounds(int releaseX, int releaseY)
        {
            Check(releaseX, releaseY);
            if (!Active) throw new InvalidOperationException("No active source rectangle.");
            int x = Math.Min(StartX / 64, releaseX / 64), y = Math.Min(StartY / 64, releaseY / 64);
            return new[] { x, y, Math.Abs(StartX / 64 - releaseX / 64) + 1,
                           Math.Abs(StartY / 64 - releaseY / 64) + 1 };
        }
        public void Cancel() { Candidate = Active = Visible = false; Width = Height = Phase = 0; LastMilliseconds = 0; }
        private static void Check(int x, int y)
        { if (x < 0 || x >= 1536 || y < 0 || y >= 1536) throw new ArgumentOutOfRangeException(nameof(x)); }
    }
}
