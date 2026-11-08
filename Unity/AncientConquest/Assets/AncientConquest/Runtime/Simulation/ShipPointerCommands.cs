using System;

namespace AncientConquest.Simulation
{
    /// <summary>Source cursor fields already computed by hover; no release-position recalculation.</summary>
    public readonly struct ShipPointerCommandInput
    {
        public object HoveredOwner { get; }
        public int CellX { get; }
        public int CellY { get; }
        public int CursorType { get; }
        public ushort ActionMask { get; }
        public ushort ActionBit { get; }
        public bool Blocked { get; }
        public bool Enabled { get; }
        public ShipPointerCommandInput(object hoveredOwner, int cellX, int cellY, int cursorType,
                                       ushort actionMask = 0, ushort actionBit = 0,
                                       bool blocked = false, bool enabled = true)
        {
            HoveredOwner = hoveredOwner; CellX = cellX; CellY = cellY; CursorType = cursorType;
            ActionMask = actionMask; ActionBit = actionBit; Blocked = blocked; Enabled = enabled;
        }
    }

    /// <summary>One source serialized actor action, separate from its fleet envelope and ship pending record.</summary>
    public readonly struct ShipPointerCommand
    {
        public byte Action { get; }
        public uint InstanceId => 0xbu;
        public int X { get; }
        public int Y { get; }
        public short Group { get; }
        public byte ByteArgument => 0;
        internal ShipPointerCommand(byte action, int x, int y, short group)
        { Action = action; X = x; Y = y; Group = group; }
        public byte[] CapturePayload()
        {
            if (Action == 0x29)
            {
                var bytes = new byte[6]; bytes[0] = 1; Put32(bytes, 1, Group); return bytes;
            }
            if (Action == 0x14)
            {
                var bytes = new byte[9]; Put32(bytes, 0, X); Put32(bytes, 4, Y); return bytes;
            }
            throw new InvalidOperationException("Unknown bounded actor command.");
        }
        private static void Put32(byte[] bytes, int offset, int value)
        {
            uint bits = unchecked((uint)value);
            for (int i = 0; i < 4; i++) bytes[offset + i] = unchecked((byte)(bits >> (i * 8)));
        }
    }

    /// <summary>
    /// Normal unmodified single-source0b selection and release subset. Source membership
    /// words are explicit. Other actors, modified commands and busy replacement are excluded.
    /// </summary>
    public sealed class ShipPointerCommands
    {
        public readonly struct Snapshot
        {
            public bool Selected { get; }
            public bool PendingSelection { get; }
            public short CurrentGroupIndex { get; }
            public short UiGroup { get; }
            public short SimulationGroup { get; }
            public byte SelectionVisualFlag { get; }
            public int GroupCount { get; }
            public int LastCommandCount { get; }
            internal Snapshot(ShipPointerCommands s)
            {
                Selected = s.selected; PendingSelection = s.pending;
                CurrentGroupIndex = s.currentGroup; UiGroup = s.uiGroup; SimulationGroup = s.simulationGroup;
                SelectionVisualFlag = s.visual; LastCommandCount = s.LastCommandCount;
                GroupCount = s.nextGroup;
            }
        }
        public readonly struct Result
        {
            public int CursorType { get; }
            public ushort ActionMask { get; }
            public ushort ActionBit { get; }
            public bool Blocked { get; }
            public bool SelectionRequested { get; }
            public bool SelectionClearRequested { get; }
            public bool ConfirmRequested { get; }
            public int SelectionAudioCode => SelectionRequested ? 0x142 : -1;
            public int SelectionEnvelopeCount => (SelectionRequested ? 1 : 0) + (SelectionClearRequested ? 1 : 0);
            internal Result(int type, ushort mask, ushort bit, bool blocked,
                            bool select = false, bool clear = false, bool confirm = false)
            {
                CursorType = type; ActionMask = mask; ActionBit = bit; Blocked = blocked;
                SelectionRequested = select; SelectionClearRequested = clear; ConfirmRequested = confirm;
            }
        }

        private readonly object source0b;
        private bool selected, pending;
        private short currentGroup = -1, uiGroup = -1, simulationGroup = -1;
        private byte visual;
        private ShipPointerCommand first, second, third;
        private int nextGroup, membershipReadIndex;
        public Snapshot Current => new Snapshot(this);
        public int LastCommandCount { get; private set; }
        public ShipPointerCommands(object source0bOwner)
        { source0b = source0bOwner ?? throw new ArgumentNullException(nameof(source0bOwner)); }
        public ShipPointerCommand GetLastCommand(int index)
        {
            if (index < 0 || index >= LastCommandCount) throw new ArgumentOutOfRangeException(nameof(index));
            return index == 0 ? first : index == 1 ? second : third;
        }

        /// <summary>Normal517b90/C457 subset when the candidate set is empty or only0b.</summary>
        public Result ProcessBoxSelection(ShipPointerCommandInput input, int width, int height,
            bool containsControlled, uint flags)
        {
            LastCommandCount = 0; membershipReadIndex = 0;
            if (width < 1 || width > 24 || height < 1 || height > 24)
                throw new ArgumentOutOfRangeException(nameof(width));
            if (!input.Enabled || !containsControlled ||
                ((input.CursorType == 5 || input.CursorType == 6) && width == 1 && height == 1)) return Unchanged(input);
            bool replace = (flags & 4u) == 0;
            // Adding the already selected sole actor to its committed group leaves
            // that group committed. No new membership or move is serialized.
            if (!replace && selected && !pending && currentGroup >= 0)
                return new Result(input.CursorType, input.ActionMask, input.ActionBit, input.Blocked, select: true);
            bool clear = replace && ClearSelection();
            selected = true; pending = true; currentGroup = -1; visual = 1;
            return new Result(input.CursorType, input.ActionMask, input.ActionBit, input.Blocked, select: true, clear: clear);
        }

        /// <summary>
        /// No pressed latch: the original map release is authoritative. Host must reject
        /// drag/unsupported UI contexts before entering this bounded single-actor model.
        /// </summary>
        public Result ProcessRelease(ShipPointerCommandInput input, int sourceMessage, uint flags,
                                     bool canRequestMove = true)
        {
            LastCommandCount = 0;
            membershipReadIndex = 0;
            if (!input.Enabled || sourceMessage != 0x62 && sourceMessage != 0x64)
                return Unchanged(input);
            if (input.HoveredOwner != null && !ReferenceEquals(input.HoveredOwner, source0b))
                throw new NotSupportedException("Other hovered actors are outside the single-source0b command reference.");
            if (input.CursorType != 0 && input.CursorType != 5 && input.CursorType != 6 && input.CursorType != 7)
                throw new NotSupportedException("Only normal cursor kinds0,5,6,7 are verified here.");
            if (sourceMessage == 0x64)
            {
                if (input.HoveredOwner == null)
                {
                    bool clear = ClearSelection();
                    return new Result(0, input.CursorType == 0 ? input.ActionMask : (ushort)0,
                                      input.ActionBit, false, clear: clear);
                }
                if (input.Blocked) return new Result(0, 0, input.ActionBit, false);
                if (input.CursorType == 5 && input.ActionMask == 0) return Unchanged(input);
                if (input.CursorType == 5 || input.CursorType == 7)
                    throw new NotSupportedException("Contextual right-release cycling is outside the normal self/blank reference.");
                return new Result(0, 0, input.ActionBit, false);
            }
            if ((flags & 0xcu) != 0)
                throw new NotSupportedException("Shift/control selection and queued group commands are not ported.");
            if (input.Blocked) return Unchanged(input);
            if (input.CursorType == 5 && ReferenceEquals(input.HoveredOwner, source0b))
            {
                bool clear = ClearSelection();
                selected = true; pending = true; currentGroup = -1; visual = 1;
                return new Result(0, input.ActionMask, input.ActionBit, false, select: true, clear: clear);
            }
            if (input.CursorType != 7) return Unchanged(input);
            if (!selected)
                throw new NotSupportedException("A SEA move without the verified selected0b context is outside this adapter.");
            if (!canRequestMove)
                throw new NotSupportedException("Moving-command replacement is not implemented by the diagnostic movement core.");
            if (input.CellX < 0 || input.CellX >= 24 || input.CellY < 0 || input.CellY >= 24)
                throw new ArgumentOutOfRangeException(nameof(input));
            if (pending)
            {
                if (nextGroup > short.MaxValue)
                    throw new NotSupportedException("The temporary group index left the verified signed16 range.");
                short group = (short)nextGroup++;
                // Empty previous groups remain in the source vector. Reassignment
                // serializes removal from the previous group before the new one.
                if (uiGroup >= 0) Append(new ShipPointerCommand(0x29, 0, 0, -1));
                pending = false; currentGroup = group; uiGroup = group;
                Append(new ShipPointerCommand(0x29, 0, 0, group));
            }
            var move = new ShipPointerCommand(0x14, input.CellX, input.CellY, 0);
            Append(move);
            return new Result(input.CursorType, input.ActionMask, input.ActionBit, input.Blocked, confirm: true);
        }
        /// <summary>Consumer-side membership acknowledgement; the host drains41 before20 exactly once.</summary>
        public void ConsumeMembership41(short group)
        {
            if (membershipReadIndex >= LastCommandCount ||
                GetLastCommand(membershipReadIndex).Action != 0x29 ||
                GetLastCommand(membershipReadIndex).Group != group)
                throw new InvalidOperationException("Consume source membership commands in their serialized order.");
            simulationGroup = group;
            membershipReadIndex++;
        }
        /// <summary>Acknowledge the separately verified reverse-selection animation's final deletion.</summary>
        public void CompleteSelectionVisualRemoval()
        {
            if (selected || visual != 2)
                throw new InvalidOperationException("Only a deselected reverse animation may remove its selector.");
            visual = 0;
        }
        private bool ClearSelection()
        {
            bool clear = selected;
            if (clear && visual != 0) visual = 2;
            selected = false; pending = false; currentGroup = -1;
            return clear;
        }
        private void Append(ShipPointerCommand command)
        {
            if (LastCommandCount == 0) first = command;
            else if (LastCommandCount == 1) second = command;
            else if (LastCommandCount == 2) third = command;
            else throw new InvalidOperationException("The single-actor command buffer exceeded its source bound.");
            LastCommandCount++;
        }
        private static Result Unchanged(ShipPointerCommandInput input) =>
            new Result(input.CursorType, input.ActionMask, input.ActionBit, input.Blocked);
    }
}
