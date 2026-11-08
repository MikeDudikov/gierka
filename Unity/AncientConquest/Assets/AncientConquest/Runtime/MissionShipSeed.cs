using System;

namespace AncientConquest.World
{
    /// <summary>
    /// Source class200/mode0 field projection, not ShipClassTy construction or combat state.
    /// Header ownership used by MissionObjectSelection is separate from the class payload ownership.
    /// </summary>
    public readonly struct MissionShipSeed
    {
        public uint InstanceId { get; }
        public byte OwnerSide { get; }
        public byte OwnerPlayer { get; }
        public uint ModelValue { get; }
        public byte ModelVariant => unchecked((byte)ModelValue);
        public uint RuntimeClassTag => unchecked(ModelValue + 200u);
        public int CellX { get; }
        public int CellY { get; }
        public sbyte Heading { get; }
        public int ReferenceFrameIndex => unchecked(Heading << 2);
        public int RequestedHealthPercent { get; }
        public byte SourceEquipmentA { get; }
        public sbyte SourceEquipmentB { get; }
        public uint SourceOrderCount { get; }

        // Logical composite dimensions, not a cropped component's bounding box.
        // Preserve signed division toward zero and x86 32-bit wrapping.
        public int GetWorldPixelX(int frameWidth) =>
            unchecked((CellX << 6) + (64 - frameWidth) / 2);
        public int GetWorldPixelY(int frameHeight) =>
            unchecked((CellY << 6) + (64 - frameHeight) / 2);

        private MissionShipSeed(MissionObjectSeed seed)
        {
            InstanceId = seed.InstanceId;
            OwnerSide = seed.ReadByte(20);
            OwnerPlayer = seed.ReadByte(24);
            ModelValue = seed.ReadUInt32(28);
            CellX = seed.ReadInt32(36);
            CellY = seed.ReadInt32(40);
            Heading = unchecked((sbyte)seed.ReadByte(44));
            RequestedHealthPercent = seed.ReadInt32(48);
            SourceEquipmentA = seed.ReadByte(60);
            SourceEquipmentB = unchecked((sbyte)(seed.ReadByte(56) - 3));
            SourceOrderCount = seed.ReadUInt32(512);
        }

        /// <summary>
        /// Returns false for another class. Only the observed 616-byte mode0 source layout is supported.
        /// No unread bytes, order-capacity padding or duplicated header indices acquire invented meanings.
        /// </summary>
        public static bool TryRead(MissionObjectSeed seed, out MissionShipSeed ship)
        {
            if (seed == null) throw new ArgumentNullException(nameof(seed));
            ship = default;
            if (seed.ClassTag != 200) return false;
            if (seed.ByteLength != 616)
                throw new ArgumentException("A source class200 ship seed must contain exactly 616 bytes.", nameof(seed));
            if (seed.ReadUInt32(16) != 0)
                throw new NotSupportedException("Only the source ship mode0 field projection is supported.");
            ship = new MissionShipSeed(seed);
            return true;
        }
    }
}
