using System;

namespace AncientConquest.Simulation
{
    public readonly struct ShipFleetMoveCommand
    {
        public uint InstanceId { get; }
        public byte Action => 20;
        public int X { get; }
        public int Y { get; }
        public byte ByteArgument { get; }
        internal ShipFleetMoveCommand(uint instanceId, int x, int y, byte argument)
        { InstanceId = instanceId; X = x; Y = y; ByteArgument = argument; }
        public byte[] CapturePayload()
        {
            var bytes = new byte[9];
            Put32(bytes, 0, X); Put32(bytes, 4, Y); bytes[8] = ByteArgument;
            return bytes;
        }
        /// <summary>Caller routes by InstanceId. Copies the request without promoting or moving.</summary>
        public bool CopyTo(ShipMoveRequestInbox inbox)
        {
            if (inbox == null) throw new ArgumentNullException(nameof(inbox));
            return inbox.RequestCellMove(X, Y, ByteArgument);
        }
        private static void Put32(byte[] bytes, int offset, int value)
        {
            uint bits = unchecked((uint)value);
            for (int i = 0; i < 4; i++) bytes[offset + i] = unchecked((byte)(bits >> (i * 8)));
        }
    }

    /// <summary>
    /// Normal4cc970/4cf070 and4ccc30/4cc650 command construction. One member
    /// bypasses formation. Failed source formation sends the clicked goal with
    /// byte255; assigned targets use byte0. Membership41 is a preceding step.
    /// </summary>
    public static class ShipFleetMoveCommands
    {
        public static ShipFleetMoveCommand[] Build(short[] terrain, int width, int height,
            uint[] orderedInstanceIds, SourceFleetFormation.Cell[] origins, int goalX, int goalY)
        {
            if (orderedInstanceIds == null) throw new ArgumentNullException(nameof(orderedInstanceIds));
            if (origins == null) throw new ArgumentNullException(nameof(origins));
            if (orderedInstanceIds.Length < 1 || orderedInstanceIds.Length > 8 || origins.Length != orderedInstanceIds.Length)
                throw new ArgumentException("A matching1..8 member normal water fleet is required.");
            for (int i = 0; i < orderedInstanceIds.Length; i++)
                for (int j = 0; j < i; j++)
                    if (orderedInstanceIds[i] == orderedInstanceIds[j]) throw new ArgumentException("Fleet members must be unique.");
            // The initialized mission/cursor owns map and goal eligibility.
            // Source4cc970 does not request a field for a one-member fleet.
            if (orderedInstanceIds.Length == 1)
                return new[] { new ShipFleetMoveCommand(orderedInstanceIds[0], goalX, goalY, 0) };
            SourceFleetFormation.Result formation = SourceFleetFormation.Assign(terrain, width, height, origins, goalX, goalY);
            var result = new ShipFleetMoveCommand[orderedInstanceIds.Length];
            for (int index = 0; index < result.Length; index++)
            {
                var target = formation.Succeeded ? formation.GetTarget(index) : new SourceFleetFormation.Cell(goalX, goalY);
                result[index] = new ShipFleetMoveCommand(orderedInstanceIds[index], target.X, target.Y,
                                                       formation.Succeeded ? (byte)0 : (byte)255);
            }
            return result;
        }
    }
}
