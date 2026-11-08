using System;
using System.Globalization;

namespace AncientConquest.World
{
    /// <summary>Immutable source type12 OBJ_ payload; not an instantiated game object.</summary>
    public sealed class MissionObjectSeed
    {
        private readonly byte[] payload;
        public string ResourceName { get; }
        public uint InstanceId { get; }
        public uint ClassTag => ReadUInt32(0);
        public uint Kind => ReadUInt32(4);
        public uint SideIndex => ReadUInt32(8);
        public uint PlayerIndex => ReadUInt32(12);
        public int ByteLength => payload.Length;

        public MissionObjectSeed(string resourceName, byte[] sourcePayload)
        {
            // The adapter accepts the canonical names exported by this source DB.
            // It does not emulate the original parser's noncanonical/error inputs.
            if (resourceName == null || resourceName.Length != 12 ||
                !resourceName.StartsWith("OBJ_", StringComparison.Ordinal) ||
                !uint.TryParse(resourceName.Substring(4), NumberStyles.AllowHexSpecifier,
                               CultureInfo.InvariantCulture, out uint identifier))
                throw new ArgumentException("Expected a canonical OBJ_ name with eight hexadecimal digits.", nameof(resourceName));
            if (sourcePayload == null || sourcePayload.Length < 16)
                throw new ArgumentException("An object seed needs its four source header words.", nameof(sourcePayload));
            ResourceName = resourceName;
            InstanceId = identifier;
            payload = (byte[])sourcePayload.Clone();
        }

        public uint ReadUInt32(int offset)
        {
            if (offset < 0 || offset > payload.Length - 4)
                throw new ArgumentOutOfRangeException(nameof(offset));
            return (uint)payload[offset] | (uint)payload[offset + 1] << 8 |
                   (uint)payload[offset + 2] << 16 | (uint)payload[offset + 3] << 24;
        }

        public int ReadInt32(int offset) => unchecked((int)ReadUInt32(offset));

        public byte ReadByte(int offset)
        {
            if (offset < 0 || offset >= payload.Length)
                throw new ArgumentOutOfRangeException(nameof(offset));
            return payload[offset];
        }
    }
}
