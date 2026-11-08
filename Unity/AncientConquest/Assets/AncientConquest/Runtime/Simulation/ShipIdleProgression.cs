namespace AncientConquest.Simulation
{
    /// <summary>
    /// Normal sprite-mode0 idle step from ShipsStateWait (0x4a3150).
    /// Draw occurs before the stored frame advances. Grid release is returned
    /// for the caller to apply with its existing owner identity.
    /// </summary>
    public static class ShipIdleProgression
    {
        public readonly struct Result
        {
            public int Frame { get; }
            public int PublishedFrame { get; }
            public sbyte FrameStep { get; }
            public uint LastTick { get; }
            public uint Interval { get; }
            public uint RandomState { get; }
            public int Speed { get; }
            public int ReservedCellIndex { get; }
            public int ReleasedCellIndex { get; }
            public bool PublishesPose { get; }

            internal Result(int frame, int publishedFrame, sbyte frameStep, uint lastTick,
                            uint interval, uint randomState, int speed, int reservedCellIndex,
                            int releasedCellIndex, bool publishesPose)
            {
                Frame = frame; PublishedFrame = publishedFrame; FrameStep = frameStep;
                LastTick = lastTick; Interval = interval; RandomState = randomState;
                Speed = speed; ReservedCellIndex = reservedCellIndex;
                ReleasedCellIndex = releasedCellIndex; PublishesPose = publishesPose;
            }
        }

        /// <summary>Message2 init block 0x4dc6d9: session seed times source instance ID.</summary>
        public static uint InitialRandomState(uint sessionSeed, uint instanceId)
        {
            return unchecked(sessionSeed * instanceId);
        }

        public static Result Advance(int frame, sbyte heading, sbyte frameStep,
                                     uint now, uint lastTick, uint interval, uint randomState,
                                     int speed, int reservedCellIndex, int cellIndex)
        {
            unchecked
            {
                randomState = randomState * 0x41c64e6du + 0x3039u;
                uint temporaryInterval = (randomState >> 16) % 7u + 15u;
                bool publishesPose = now - lastTick > temporaryInterval;
                int publishedFrame = frame, releasedCellIndex = -1;
                if (publishesPose)
                {
                    if (speed > 0) speed /= 2;
                    if (reservedCellIndex >= 0)
                    {
                        if (reservedCellIndex != cellIndex) releasedCellIndex = reservedCellIndex;
                        reservedCellIndex = -1;
                    }
                    int first = (byte)((heading + 14) * 4);
                    if (frame < first) { frame = first; frameStep = 1; }
                    if (frame > first + 3) { --frame; frameStep = -1; }
                    publishedFrame = frame;
                    lastTick = now;
                    frame += frameStep;
                    if (frame < first) { frame = first; frameStep = 1; }
                    if (frame > first + 3) { --frame; frameStep = -1; }
                }
                // 4a3150 restores the old sprite interval after its temporary
                // random threshold, and returns0 to the MoveShip caller.
                return new Result(frame, publishedFrame, frameStep, lastTick, interval,
                                  randomState, speed, reservedCellIndex, releasedCellIndex, publishesPose);
            }
        }
    }
}
