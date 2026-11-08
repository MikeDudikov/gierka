using System;

namespace AncientConquest.World
{
    /// <summary>
    /// The bounded campaign-player selection and saved source viewport lookup.
    /// This does not create objects, simulate a mission, or choose modern FOV.
    /// </summary>
    public sealed class MissionInitialSetup
    {
        private const int DescriptorPrefixBytes = 20;
        private const int PlayerRecordBytes = 104;
        private const int SlotCount = 20;
        private readonly byte[] playersDescriptor = new byte[SlotCount];

        public byte SelectedSide { get; }
        public byte SelectedPlayer { get; }
        public int SavedOriginX { get; }
        public int SavedOriginY { get; }
        public int SourceViewWidthCells => 9;
        public int SourceViewHeightCells => 8;

        public MissionInitialSetup(byte[] descriptor, byte[] savedViews, int campaignIndex = 0)
        {
            if (campaignIndex < 0 || campaignIndex > 3)
                throw new ArgumentOutOfRangeException(nameof(campaignIndex));
            if (descriptor == null || descriptor.Length < DescriptorPrefixBytes)
                throw new ArgumentException("The source descriptor prefix is missing.", nameof(descriptor));
            if (savedViews == null || savedViews.Length != SlotCount * 4)
                throw new ArgumentException("The saved source views require twenty packed positions.", nameof(savedViews));
            int count = ReadInt32(descriptor, 16);
            if (count <= 0 || DescriptorPrefixBytes + (long)count * PlayerRecordBytes > descriptor.LongLength)
                throw new ArgumentException("The source descriptor player records are truncated or invalid.", nameof(descriptor));

            // Original537ef0 maps campaign0 to(1,1), campaign1 to(0,0), then2/3.
            int chosen = campaignIndex == 0 ? 1 : campaignIndex == 1 ? 0 : campaignIndex;
            bool found = false;
            for (int index = 0; index < count; index++)
            {
                int offset = DescriptorPrefixBytes + index * PlayerRecordBytes;
                int side = ReadInt32(descriptor, offset + 8);
                int player = ReadInt32(descriptor, offset + 12);
                if (side < 0 || side >= 5 || player < 0 || player >= 4)
                    throw new ArgumentException("A source player record addresses a slot outside the twenty-entry table.", nameof(descriptor));
                bool selected = side == chosen && player == chosen;
                playersDescriptor[side * 4 + player] = selected ? (byte)1 : (byte)3;
                if (selected)
                {
                    SelectedSide = (byte)side;
                    SelectedPlayer = (byte)player;
                    found = true;
                }
            }
            // With no match the original retains a previous application's slot
            // byte. This API has no previous state, so it refuses that case.
            if (!found)
                throw new ArgumentException("This descriptor has no selected player for the requested campaign.", nameof(descriptor));
            int viewOffset = (SelectedSide * 4 + SelectedPlayer) * 4;
            SavedOriginX = savedViews[viewOffset] | savedViews[viewOffset + 1] << 8;
            SavedOriginY = savedViews[viewOffset + 2] | savedViews[viewOffset + 3] << 8;
        }

        public byte[] CopyPlayersDescriptor() => (byte[])playersDescriptor.Clone();

        private static int ReadInt32(byte[] input, int offset)
        {
            return unchecked(input[offset] | input[offset + 1] << 8 |
                             input[offset + 2] << 16 | input[offset + 3] << 24);
        }
    }
}
