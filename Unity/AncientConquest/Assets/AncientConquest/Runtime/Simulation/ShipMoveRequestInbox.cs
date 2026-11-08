using System;

namespace AncientConquest.Simulation
{
    public enum ShipMovePromotionOutcome
    {
        None,
        Deferred,
        Discarded,
        Promoted
    }

    // Bounded action20 -> opcode80 -> idle promotion from original ancient.exe.
    // Caller explicitly guarantees that no busy subtask is running. This class
    // does not execute navigation, the general order collection, Life or AI.
    public sealed class ShipMoveRequestInbox
    {
        private readonly byte[] pendingRecord = new byte[26];
        private uint capabilities;
        private uint readyMask;
        private byte status;

        public uint PendingFlags { get; private set; }
        public uint ActiveFlags { get; private set; }
        public bool HasPendingMove => (PendingFlags & 0x80u) != 0;
        public int TargetX { get; private set; }
        public int TargetY { get; private set; }
        public byte RouteByte { get; private set; }
        public bool FirstMove { get; private set; }

        public ShipMoveRequestInbox(uint capabilities, uint readyMask = uint.MaxValue,
                                    byte status = 0, byte routeByte = 0)
        {
            UpdateContext(capabilities, readyMask, status);
            RouteByte = routeByte;
        }

        public void UpdateContext(uint capabilities, uint readyMask, byte status)
        {
            if (status != 0 && status != 1 && status != 2 && status != 4)
                throw new NotSupportedException("Only proven ship statuses 0, 1, 2 and 4 are supported.");
            this.capabilities = capabilities;
            this.readyMask = readyMask;
            this.status = status;
        }

        // True means the source action gate accepted a copied request. It is
        // not a claim that the target is in bounds, reachable or unobstructed.
        public bool RequestCellMove(int x, int y, byte opaqueByte = 255)
        {
            if ((capabilities & 0x400u) == 0) return false;
            Array.Clear(pendingRecord, 0, pendingRecord.Length);
            WriteInt32(pendingRecord, 4, x);
            WriteInt32(pendingRecord, 8, y);
            pendingRecord[25] = opaqueByte;
            PendingFlags |= 0x80u;
            return true;
        }

        public byte[] CapturePendingRecord()
        {
            return (byte[])pendingRecord.Clone();
        }

        public ShipMovePromotionOutcome ConsumeInitialIdleMove(bool busyContext = false)
        {
            if (busyContext)
                throw new NotSupportedException("Busy ship cancellation and arbitration are outside this adapter.");
            if (!HasPendingMove) return ShipMovePromotionOutcome.None;
            if (status == 1 || status == 2 || status == 4 || (capabilities & 0x1f0u) == 0)
                return ShipMovePromotionOutcome.Deferred;

            // Original idle arbitration runs before checking the ready bit.
            ActiveFlags &= ~0xf0u;
            if ((readyMask & 0x80u) == 0) return ShipMovePromotionOutcome.Deferred;
            PendingFlags &= ~0x80u;
            if ((capabilities & 0x400u) == 0) return ShipMovePromotionOutcome.Discarded;

            TargetX = ReadInt32(pendingRecord, 4);
            TargetY = ReadInt32(pendingRecord, 8);
            if (pendingRecord[25] != 255) RouteByte = pendingRecord[25];
            FirstMove = true;
            ActiveFlags |= 0x80u;
            return ShipMovePromotionOutcome.Promoted;
        }

        private static void WriteInt32(byte[] data, int offset, int value)
        {
            unchecked
            {
                uint bits = (uint)value;
                for (int index = 0; index < 4; ++index)
                    data[offset + index] = (byte)(bits >> (index * 8));
            }
        }

        private static int ReadInt32(byte[] data, int offset)
        {
            return unchecked((int)((uint)data[offset] | ((uint)data[offset + 1] << 8) |
                                   ((uint)data[offset + 2] << 16) | ((uint)data[offset + 3] << 24)));
        }
    }
}
