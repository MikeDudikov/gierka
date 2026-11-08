using System;
using System.Collections.Generic;

namespace AncientConquest.Simulation
{
    /// <summary>
    /// Bounded100/1 and100/2 fleet task owner:4ccc30/4ccd80 and4cf2c0/4cf550. The caller owns
    /// membership, group+8 elapsed steps, packet delivery and world scheduling.
    /// Local normal water ships only, patrol off and watch fields zero.
    /// Queued300/311, interrupted-task reports and AI remain excluded branches.
    /// </summary>
    public sealed class ShipFleetNormalTask
    {
        public readonly struct Member
        {
            public uint InstanceId { get; }
            public int X { get; }
            public int Y { get; }
            public byte MotionState { get; }
            public bool InterruptedTask { get; }
            public Member(uint id, int x, int y, byte state = 0, bool interruptedTask = false)
            { InstanceId = id; X = x; Y = y; MotionState = state; InterruptedTask = interruptedTask; }
        }

        public readonly struct Assignment
        {
            public uint InstanceId { get; }
            public int X { get; }
            public int Y { get; }
            internal Assignment(uint id, int x, int y) { InstanceId = id; X = x; Y = y; }
        }

        //4ce6c0:logical projection of the12-byte point; renderer owns marker+8.
        public readonly struct QueuedPoint
        {
            public int X { get; }
            public int Y { get; }
            // Matches4ce6c0 point coordinates, without graphical allocation.
            internal QueuedPoint(int x, int y) { X = x; Y = y; }
        }

        //4ce8a0:17-byte record;identity normalized from ptr+0/id+4,mode+8,xy+9/+d.
        public readonly struct QueuedMember
        {
            public uint InstanceId { get; }
            public sbyte Mode { get; }
            public int X { get; }
            public int Y { get; }
            // Matches4ce8a0 logical member fields (no managed pointer identity).
            internal QueuedMember(uint id, sbyte mode, int x, int y)
            { InstanceId = id; Mode = mode; X = x; Y = y; }
        }

        public readonly struct GroupEvent
        {
            public int Code { get; }
            public uint Counter { get; }
            public int MemberIndex { get; }
            public uint InstanceId { get; }
            public int X { get; }
            public int Y { get; }
            internal GroupEvent(int code, uint counter, int memberIndex, uint id, int x, int y)
            { Code = code; Counter = counter; MemberIndex = memberIndex; InstanceId = id; X = x; Y = y; }
            public byte[] CaptureRecord()
            {
                var bytes = new byte[32];
                Put32(bytes, 0, unchecked((uint)Code)); Put32(bytes, 4, Counter);
                Put32(bytes, 8, unchecked((uint)MemberIndex)); Put32(bytes, 12, InstanceId);
                Put32(bytes, 16, unchecked((uint)X)); Put32(bytes, 20, unchecked((uint)Y));
                return bytes;
            }
        }

        public readonly struct Command
        {
            public uint InstanceId { get; }
            public byte Action { get; }
            public int X { get; }
            public int Y { get; }
            public byte ByteArgument { get; }
            internal Command(uint id, byte action, int x = 0, int y = 0, byte argument = 0)
            { InstanceId = id; Action = action; X = x; Y = y; ByteArgument = argument; }
            public byte[] CapturePayload()
            {
                if (Action == 20)
                {
                    var bytes = new byte[9]; Put32(bytes, 0, unchecked((uint)X));
                    Put32(bytes, 4, unchecked((uint)Y)); bytes[8] = ByteArgument; return bytes;
                }
                //4c42f0(1,0,0,0,id),22-byte action35, for a failed add-event
                //formation in a newly initialized non-patrol local group.
                var watch = new byte[22]; watch[0] = 1; watch[21] = 255; return watch;
            }
        }

        private readonly List<GroupEvent> events = new List<GroupEvent>();
        private List<Assignment> assignments = new List<Assignment>();
        private List<Command> commands = new List<Command>();
        private readonly List<QueuedPoint> queuedPoints = new List<QueuedPoint>();
        private List<QueuedMember> queuedMembers = new List<QueuedMember>();
        public bool HasTask { get; private set; }
        // Matches task+4;0 denotes absent group+25, not a source task subtype.
        public int Subtype { get; private set; }
        // Matches route+4 vector count and route+0 registered count/route+8 vector.
        public int QueuedPointCount => queuedPoints.Count;
        public int QueuedMemberCount => queuedMembers.Count;
        // Matches4ce6c0/4ce8a0 immutable logical records.
        public QueuedPoint GetQueuedPoint(int index) => queuedPoints[index];
        public QueuedMember GetQueuedMember(int index) => queuedMembers[index];
        public uint RequestedAt { get; private set; }
        public int GoalX { get; private set; }
        public int GoalY { get; private set; }
        public int AssignmentCount => assignments.Count;
        public int EventCount => events.Count;
        /// <summary>Emissions of the most recent Request/Work; enqueueing does not deliver or clear them.</summary>
        public int CommandCount => commands.Count;
        public Assignment GetAssignment(int index) => assignments[index];
        public GroupEvent GetEvent(int index) => events[index];
        public Command GetCommand(int index) => commands[index];

        public bool MemberAdded(uint counter, int memberIndex, uint id) =>
            Enqueue(new GroupEvent(300, counter, memberIndex, id, 0, 0));
        /// <summary>4a1770 records the old member index and CELL coordinates, before removal.</summary>
        public bool MemberRemoved(uint counter, int memberIndex, uint id, int x, int y) =>
            Enqueue(new GroupEvent(311, counter, memberIndex, id, x, y));
        private bool Enqueue(GroupEvent item)
        {
            if (item.MemberIndex < 0) throw new ArgumentOutOfRangeException(nameof(item));
            if (!HasTask) return false;
            events.Add(item); return true;
        }

        /// <summary>Replace/reuse100/1 without resetting group elapsed steps or old assignments.</summary>
        public void Request(short[] terrain, int width, int height, Member[] members, int x, int y, uint counter)
        {
            ValidateMembers(members);
            var nextAssignments = Subtype == 2 ? new List<Assignment>() : new List<Assignment>(assignments);
            var nextCommands = new List<Command>();
            if (Form(terrain, width, height, members, x, y, nextAssignments, nextCommands) == 0)
                foreach (Member member in members) nextCommands.Add(new Command(member.InstanceId, 20, x, y, 255));
            //4ccc30 clears a different subtype via4a1c60 before replacement.
            if (Subtype == 2) Clear();
            HasTask = true; Subtype = 1; RequestedAt = counter; GoalX = x; GoalY = y;
            assignments = nextAssignments; commands = nextCommands;
        }

        /// <summary>
        /// Return group+8 after original Work. Events are consumed last-to-first;
        /// successful add processing suppresses the periodic pass. The >100
        /// check precedes addition of pending steps. Arrival never deletes100/1.
        /// Unsupported formation/report contexts fail before changing this task.
        /// </summary>
        /// <param name="eventSlots">Actor IDs at the source member vector slots,
        /// including retained tail slots addressed by queued300 events.4cc590
        /// reads the recorded slot before scanning the current logical members.</param>
        public uint Work(short[] terrain, int width, int height, Member[] members, uint[] eventSlots,
            uint elapsedSteps, uint pendingSteps)
        {
            ValidateMembers(members);
            if (!HasTask) { commands.Clear(); return elapsedSteps; }
            if (Subtype != 1) throw new NotSupportedException("Queued Work requires explicit memory context and source counter.");
            ValidateSlots(members, eventSlots);
            var nextAssignments = new List<Assignment>(assignments);
            var nextCommands = new List<Command>();
            int eventResult = 0;
            for (int index = events.Count - 1; index >= 0; index--)
            {
                GroupEvent item = events[index];
                if (item.Code != 300) continue; //311 is discarded by this task subtype.
                if (!ResolveEvent(members, eventSlots, item)) continue;
                eventResult = Form(terrain, width, height, members, GoalX, GoalY, nextAssignments, nextCommands);
                if (eventResult != 0) continue;
                uint id = item.InstanceId;
                nextCommands.Add(new Command(id, 20, GoalX, GoalY, 255));
                nextCommands.Add(new Command(id, 35)); eventResult++;
            }
            if (eventResult == 0 && elapsedSteps > 100)
            {
                elapsedSteps = 0;
                foreach (Member member in members)
                {
                    if (member.InterruptedTask)
                        throw new NotSupportedException("Interrupted-task report/action40 is outside normal local task Work.");
                    if (member.MotionState != 0) continue;
                    int x = GoalX, y = GoalY;
                    foreach (Assignment assignment in nextAssignments)
                        if (assignment.InstanceId == member.InstanceId) { x = assignment.X; y = assignment.Y; break; }
                    if (SourceDistance(member.X, x) > 1 || SourceDistance(member.Y, y) > 1)
                        nextCommands.Add(new Command(member.InstanceId, 20, x, y));
                }
            }
            events.Clear(); assignments = nextAssignments; commands = nextCommands;
            return unchecked(elapsedSteps + pendingSteps);
        }

        /// <summary>Explicit4a1c60/4cc4c0 cleanup. Group elapsed steps remain caller-owned.</summary>
        public void Clear()
        {
            HasTask = false; Subtype = 0; RequestedAt = 0; GoalX = 0; GoalY = 0;
            events.Clear(); assignments.Clear(); commands.Clear();
            queuedPoints.Clear(); queuedMembers.Clear();
        }

        /// <summary>Matches4cf2c0/4cef80 single-point,local,non-patrol request.
        /// First request sends the same goal to all members; append sends nothing.
        /// Global duplicate suppression is4ce6c0,not bulk4ce610.</summary>
        public void RequestQueued(int width, int height, Member[] members, int x, int y, uint counter)
        {
            ValidateMembers(members); ValidateQueuedCells(width, height, members, x, y);
            bool created = Subtype != 2;
            var output = new List<Command>();
            var registered = created ? new List<QueuedMember>() : new List<QueuedMember>(queuedMembers);
            if (created)
            {
                foreach (Member member in members)
                {
                    //4ce8a0 may enqueue310 even for(-1,-1); that creation edge
                    //needs its own source corpus rather than silent omission.
                    if (NearQueuedTarget(member, -1, -1))
                        throw new NotSupportedException("Initial near-sentinel arrival is outside the queued corpus.");
                    output.Add(new Command(member.InstanceId, 20, x, y));
                    registered.Add(new QueuedMember(member.InstanceId, 1, -1, -1));
                }
                Clear();
            }
            bool duplicate = false;
            foreach (QueuedPoint point in queuedPoints) if (point.X == x && point.Y == y) { duplicate = true; break; }
            if (!duplicate) queuedPoints.Add(new QueuedPoint(x, y));
            HasTask = true; Subtype = 2; RequestedAt = counter; GoalX = x; GoalY = y;
            queuedMembers = registered; commands = output;
        }

        // Matches4a1700 event136:offset+10 is a CELL INDEX,not cellX.
        public bool MemberArrived(uint counter, int memberIndex, uint id, int cellIndex) =>
            Enqueue(new GroupEvent(310, counter, memberIndex, id, cellIndex, 0));

        /// <summary>Matches4ce7c0;end=1 is retained even for wrapping +/-2.</summary>
        public int NextQueuedCell(int width, int x, int y, sbyte mode, out bool end)
        {
            if (Subtype != 2) throw new InvalidOperationException("Queued task required.");
            if (width < 1 || width > 128) throw new ArgumentOutOfRangeException(nameof(width));
            end = false;
            for (int i = 0; i < queuedPoints.Count; i++)
            {
                if (queuedPoints[i].X != x || queuedPoints[i].Y != y) continue;
                int at = mode > 0 ? i + 1 : i - 1;
                if (at < 0 || at >= queuedPoints.Count)
                {
                    end = true;
                    if (mode == 2) at = 0;
                    else if (mode == -2) at = queuedPoints.Count - 1;
                    else return -1;
                }
                return unchecked(queuedPoints[at].Y * width + queuedPoints[at].X);
            }
            return -1;
        }

        /// <summary>
        /// Matches4cf550/4cf0b0 for stable local membership. Prefix words are
        /// signed16 memory immediately preceding EACH member's wave allocation,
        /// in current member order, supplied explicitly even when unused.
        /// No elapsed clock,world mail,occupancy or actor state is mutated here.
        /// </summary>
        public uint WorkQueued(short[] terrain, int width, int height, Member[] members, uint[] eventSlots,
            IReadOnlyList<short> wavePrefixWords, uint sourceCounter, uint elapsedSteps, uint pendingSteps)
        {
            ValidateMembers(members);
            if (Subtype != 2) throw new InvalidOperationException("Queued task required.");
            ValidateQueuedCells(width, height, members, GoalX, GoalY); ValidateSlots(members, eventSlots);
            if (wavePrefixWords == null) throw new ArgumentNullException(nameof(wavePrefixWords));
            if (wavePrefixWords.Count != members.Length) throw new ArgumentException("One explicit allocation-prefix word per current member is required.");
            foreach (GroupEvent item in events)
            {
                if (item.Code != 310) throw new NotSupportedException("Queued300/311 membership changes require a separate source corpus.");
                bool current = false;
                foreach (Member member in members) if (member.InstanceId == item.InstanceId) { current = true; break; }
                if (!current && ResolveEvent(members, eventSlots, item))
                    throw new NotSupportedException("Queued retained-only actor events require the membership-edit corpus.");
            }
            if (elapsedSteps > 100)
            {
                if (terrain == null) throw new ArgumentNullException(nameof(terrain));
                if (terrain.Length != width * height) throw new ArgumentException("Complete navigation field required.");
                foreach (short value in terrain)
                    if (value != 0 && value != -1) throw new NotSupportedException("Unrepresented queued navigation value.");
                foreach (Member member in members)
                    if (member.InterruptedTask) throw new NotSupportedException("Queued report/action40 is outside this corpus.");
            }
            var nextMembers = new List<QueuedMember>(queuedMembers);
            var nextEvents = new List<GroupEvent>(events);
            var output = new List<Command>();
            //4cf0b0 uses a captured last index; arrival never suppresses periodic Work.
            for (int i = events.Count - 1; i >= 0; i--)
            {
                GroupEvent item = nextEvents[i];
                int ordinal = -1;
                if (ResolveEvent(members, eventSlots, item))
                    for (int j = 0; j < members.Length; j++)
                        if (members[j].InstanceId == item.InstanceId) { ordinal = j; break; }
                if (ordinal >= 0)
                {
                    Member member = members[ordinal];
                    //4a0230 local,non-temporary group:single member filters stale cell.
                    if (members.Length != 1 || item.X == member.Y * width + member.X)
                    {
                        QueuedTarget(nextMembers, member.InstanceId, width, out sbyte mode);
                        int cell = NextQueuedCell(width, item.X % width, item.X / width, mode, out bool end);
                        if (cell > 0 && cell < width * height)
                        {
                            output.Add(new Command(member.InstanceId, 20, cell % width, cell / width));
                            UpdateQueuedMember(nextMembers, nextEvents, member, ordinal, cell % width, cell / width,
                                width, end, sourceCounter);
                        }
                    }
                }
                nextEvents.RemoveAt(i);
            }
            if (elapsedSteps > 100)
            {
                elapsedSteps = 0;
                for (int i = 0; i < members.Length; i++)
                {
                    Member member = members[i]; if (member.MotionState != 0) continue;
                    int cell = QueuedTarget(nextMembers, member.InstanceId, width, out sbyte mode);
                    if (cell < 0) continue;
                    bool end;
                    if (cell == 0) cell = NearestQueuedCell(terrain, width, height, member, wavePrefixWords[i], out end);
                    else cell = NextQueuedCell(width, cell % width, cell / width, mode, out end);
                    if (end || cell <= 0 || cell >= width * height) continue;
                    output.Add(new Command(member.InstanceId, 20, cell % width, cell / width));
                    //4cf6f3..4cf72c:DO NOT store target after every emission;only if at this cell.
                    if (member.X == cell % width && member.Y == cell / width)
                        UpdateQueuedMember(nextMembers, nextEvents, member, i, cell % width, cell / width,
                            width, false, sourceCounter);
                }
            }
            queuedMembers = nextMembers; events.Clear(); events.AddRange(nextEvents); commands = output;
            return unchecked(elapsedSteps + pendingSteps);
        }

        // Matches4cea20:registered(-1,-1) =>0;missing actor =>-1.
        private static int QueuedTarget(List<QueuedMember> members, uint id, int width, out sbyte mode)
        {
            mode = 0;
            foreach (QueuedMember member in members)
                if (member.InstanceId == id)
                { mode = member.Mode; return member.X == -1 && member.Y == -1 ? 0 : unchecked(member.Y * width + member.X); }
            return -1;
        }

        // Matches4ceab0/4cebc7 with param3=-1;strict signed max,first tie wins.
        private int NearestQueuedCell(short[] terrain, int width, int height, Member member, short prefix, out bool end)
        {
            var wave = (short[])terrain.Clone(); SourceWaveField.FillQueuedRoute(wave, width, height, member.X, member.Y);
            int selected = -1; short best = 0;
            foreach (QueuedPoint point in queuedPoints)
            {
                if (point.X == member.X && point.Y == member.Y) continue;
                int cell = point.Y * width + point.X;
                if (selected >= 0 && wave[cell] <= best) continue;
                best = wave[cell]; selected = cell;
            }
            // Original OR admits-1; its adjacent word must not be replaced with0.
            end = selected >= 0 && best < prefix; return selected;
        }

        // Matches4ce8a0 update/remove ordering and its4a1700 near-target event.
        private static void UpdateQueuedMember(List<QueuedMember> registered, List<GroupEvent> output,
            Member member, int ordinal, int x, int y, int width, bool end, uint counter)
        {
            int found = -1;
            for (int i = 0; i < registered.Count; i++)
                if (registered[i].InstanceId == member.InstanceId) { found = i; break; }
            if (found >= 0 && end && registered[found].Mode != 2 && registered[found].Mode != -2)
            { registered.RemoveAt(found); return; }
            if (NearQueuedTarget(member, x, y)) output.Add(new GroupEvent(310, counter, ordinal, member.InstanceId, y * width + x, 0));
            var next = new QueuedMember(member.InstanceId, found < 0 ? (sbyte)0 : registered[found].Mode, x, y);
            if (found < 0) registered.Add(next); else registered[found] = next;
        }

        // Matches557410 for bounded cells: max(dx,dy)+min(dx,dy)/2,including(2,2) exception.
        private static bool NearQueuedTarget(Member member, int x, int y)
        {
            int dx = SourceDistance(member.X, x), dy = SourceDistance(member.Y, y);
            int distance = dx == 2 && dy == 2 ? 2 : dx >= dy ? dx + dy / 2 : dy + dx / 2;
            return distance < 2;
        }

        // Managed guards for4ce6c0/4a1e90 bounded map;not new gameplay policy.
        private static void ValidateQueuedCells(int width, int height, Member[] members, int x, int y)
        {
            if (width < 1 || height < 1 || width > 128 || height > 128) throw new ArgumentOutOfRangeException(nameof(width));
            if (x < 0 || y < 0 || x >= width || y >= height) throw new ArgumentOutOfRangeException(nameof(x));
            foreach (Member member in members)
                if (member.X < 0 || member.Y < 0 || member.X >= width || member.Y >= height)
                    throw new ArgumentOutOfRangeException(nameof(members));
        }

        private static int SourceDistance(int a, int b)
        { int delta = unchecked(a - b); return delta < 0 ? unchecked(-delta) : delta; }
        private static bool ResolveEvent(Member[] members, uint[] slots, GroupEvent item)
        {
            //55b490 shifts the vector but does not erase its tail. Preserve
            //4cc590's fast lookup even when a recorded slot is beyond Count.
            if (slots[item.MemberIndex] == item.InstanceId) return true;
            for (int index = 0; index < members.Length; index++)
                if (members[index].InstanceId == item.InstanceId) return true;
            return false;
        }
        private void ValidateSlots(Member[] members, uint[] slots)
        {
            if (slots == null) throw new ArgumentNullException(nameof(slots));
            if (slots.Length < members.Length) throw new ArgumentException("Current source slots are incomplete.", nameof(slots));
            for (int i = 0; i < members.Length; i++)
                if (slots[i] != members[i].InstanceId) throw new ArgumentException("Source slot prefix differs from membership.", nameof(slots));
            foreach (GroupEvent item in events)
                if ((item.Code == 300 || (Subtype == 2 && item.Code == 310)) && item.MemberIndex >= slots.Length)
                    throw new ArgumentException("A retained source event slot is missing.", nameof(slots));
        }
        private static void ValidateMembers(Member[] members)
        {
            if (members == null) throw new ArgumentNullException(nameof(members));
            if (members.Length > 8) throw new ArgumentOutOfRangeException(nameof(members));
            for (int i = 0; i < members.Length; i++)
                for (int j = 0; j < i; j++)
                    if (members[i].InstanceId == members[j].InstanceId)
                        throw new ArgumentException("Ordered group members must be unique.", nameof(members));
        }
        private static int Form(short[] terrain, int width, int height, Member[] members, int x, int y,
            List<Assignment> targetAssignments, List<Command> output)
        {
            if (members.Length == 0) return 0;
            var ids = new uint[members.Length]; var origins = new SourceFleetFormation.Cell[members.Length];
            for (int i = 0; i < members.Length; i++)
            { ids[i] = members[i].InstanceId; origins[i] = new SourceFleetFormation.Cell(members[i].X, members[i].Y); }
            ShipFleetMoveCommand[] moves = ShipFleetMoveCommands.Build(terrain, width, height, ids, origins, x, y);
            if (moves[0].ByteArgument == 255) return 0;
            foreach (ShipFleetMoveCommand move in moves)
            {
                var assignment = new Assignment(move.InstanceId, move.X, move.Y); int found = -1;
                for (int i = 0; i < targetAssignments.Count; i++)
                    if (targetAssignments[i].InstanceId == move.InstanceId) { found = i; break; }
                if (found < 0) targetAssignments.Add(assignment); else targetAssignments[found] = assignment;
                output.Add(new Command(move.InstanceId, 20, move.X, move.Y));
            }
            return moves.Length;
        }
        private static void Put32(byte[] bytes, int offset, uint value)
        { for (int i = 0; i < 4; i++) bytes[offset + i] = unchecked((byte)(value >> (i * 8))); }
    }
}
