namespace AncientConquest.Simulation
{
    /// <summary>The normal ShipsStopMove turn step (0x4a3320 and 0x4b5390).</summary>
    public static class ShipTurnProgression
    {
        public readonly struct Result
        {
            public int Frame { get; }
            public sbyte Heading { get; }
            public sbyte TurnStep { get; }
            public uint LastTick { get; }
            public byte State { get; }
            public byte ChangedMarker { get; }
            public bool PublishesPose { get; }

            internal Result(int frame, sbyte heading, sbyte turnStep, uint lastTick,
                            byte state, byte changedMarker, bool publishesPose)
            {
                Frame = frame;
                Heading = heading;
                TurnStep = turnStep;
                LastTick = lastTick;
                State = state;
                ChangedMarker = changedMarker;
                PublishesPose = publishesPose;
            }
        }

        public static Result Advance(int frame, sbyte heading, sbyte targetHeading, sbyte turnStep,
                                     uint now, uint lastTick, uint interval, bool hasPath,
                                     byte state, byte changedMarker)
        {
            unchecked
            {
                if (turnStep == 0)
                {
                    // Original helper may reset idle/other poses before it
                    // chooses a direction from the 8-heading or 24-pose ring.
                    if (frame > 55) frame = heading << 2;
                    int difference;
                    if (frame < 32)
                    {
                        difference = targetHeading - heading;
                        if ((difference < 0 ? -difference : difference) > 4)
                            difference += difference > 0 ? -8 : 8;
                    }
                    else
                    {
                        difference = (short)(targetHeading * 3 + 32) - frame;
                        if ((difference < 0 ? -difference : difference) > 12)
                            difference += difference > 0 ? -24 : 24;
                    }
                    turnStep = (sbyte)(difference > 0 ? 1 : difference < 0 ? -1 : 0);
                    if (frame < 32) frame = heading * 3 + 32;
                }

                bool publishesPose = now - lastTick > interval;
                if (publishesPose)
                {
                    frame += turnStep;
                    if (frame > 55) frame = 32;
                    if (frame < 32) frame = 55;
                    int direction = (frame - 32) / 3;
                    heading = (sbyte)direction;
                    if (direction == targetHeading && (frame - 32) % 3 == 0)
                    {
                        frame = heading << 2;
                        state = (byte)(hasPath ? 3 : 0);
                        changedMarker = 1;
                    }
                    lastTick = now;
                }
                // The original routine returns zero even on completion.
                // Its MoveShip caller returns immediately for this entire
                // call; state3 movement starts on the following call.
                return new Result(frame, heading, turnStep, lastTick, state, changedMarker, publishesPose);
            }
        }
    }
}
