using System;
using System.Globalization;

namespace AncientConquest.World
{
    /// <summary>
    /// A source-derived, frozen reef reference recipe. State1/frame0 assumes an
    /// empty collision cell; this does not instantiate the original class or
    /// establish its state after all mission objects and simulation run.
    /// </summary>
    public readonly struct MissionReefSeed
    {
        public uint InstanceId { get; }
        public int CellX { get; }
        public int CellY { get; }
        public byte Variant { get; }
        public int ReferenceState => 1;
        public int ReferenceFrameIndex => 0;
        public int WorldPixelX => unchecked(CellX << 6);
        public int WorldPixelY => unchecked(CellY << 6);
        public string ReferenceResourceName => "BREEF" + Variant.ToString(CultureInfo.InvariantCulture) + "SPR_1";

        private MissionReefSeed(uint instanceId, int cellX, int cellY, byte variant)
        {
            InstanceId = instanceId;
            CellX = cellX;
            CellY = cellY;
            Variant = variant;
        }

        /// <summary>
        /// Returns false for another class. Malformed class601 or a saved-state
        /// load mode fails explicitly; the supported source mission uses mode0.
        /// Coordinates preserve x86 32-bit shift wrapping, without map clamping.
        /// </summary>
        public static bool TryRead(MissionObjectSeed seed, out MissionReefSeed reef)
        {
            if (seed == null) throw new ArgumentNullException(nameof(seed));
            reef = default;
            if (seed.ClassTag != 601) return false;
            if (seed.ByteLength != 32)
                throw new ArgumentException("A mode0 class601 reef seed must contain exactly 32 bytes.", nameof(seed));
            if (seed.ReadUInt32(16) != 0)
                throw new NotSupportedException("Only the source reef mode0 reference recipe is supported.");
            reef = new MissionReefSeed(seed.InstanceId, seed.ReadInt32(20),
                                      seed.ReadInt32(24), seed.ReadByte(28));
            return true;
        }
    }
}
