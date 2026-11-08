namespace AncientConquest.Simulation
{
    /// <summary>The bounded forward-animation tail of original MoveShip (0x4a4d49).</summary>
    public static class ShipFrameProgression
    {
        public readonly struct Result
        {
            public int Frame { get; }
            public uint LastTick { get; }

            internal Result(int frame, uint lastTick)
            {
                Frame = frame;
                LastTick = lastTick;
            }
        }

        public static Result AdvanceForward(int frame, sbyte heading, uint now, uint lastTick, uint interval)
        {
            unchecked
            {
                // Source uses unsigned elapsed time and a strict threshold.
                // A delayed call advances once, then stores the current tick.
                if (now - lastTick > interval)
                {
                    frame++;
                    lastTick = now;
                    if (frame >= heading * 4 + 4)
                        frame = heading << 2;
                }
                return new Result(frame, lastTick);
            }
        }
    }
}
