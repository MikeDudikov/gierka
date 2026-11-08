using System;
using System.Collections.Generic;

namespace AncientConquest.Simulation
{
    /// <summary>Source action41 payload, addressed by instance ID rather than registry ordinal.</summary>
    public readonly struct ShipFleetMembershipCommand
    {
        public uint InstanceId { get; }
        public byte Action => 41;
        public short Group { get; }
        internal ShipFleetMembershipCommand(uint instanceId, short group)
        { InstanceId = instanceId; Group = group; }

        public byte[] CapturePayload()
        {
            var bytes = new byte[6];
            bytes[0] = 1;
            uint value = unchecked((uint)(int)Group);
            for (int index = 0; index < 4; index++)
                bytes[index + 1] = unchecked((byte)(value >> (index * 8)));
            return bytes;
        }
    }

    /// <summary>
    /// Normal49ca60/49bd60 Mode10 membership for initialized local ships.
    /// Empty-group deletion is disabled, as in the local reference owner.
    /// Each group owns one100/1 or100/2 task,32-byte events and retained member slots.
    /// Cursor policy, physical Work and world scheduling remain separate.
    /// </summary>
    public sealed class ShipFleetMembership
    {
        private sealed class Actor
        {
            internal readonly uint Id;
            internal short UiGroup = -1, SimulationGroup = -1;
            internal int MemberIndex;
            internal Actor(uint id) { Id = id; }
        }

        // Matches49b990:packed61-byte group,age+8,task+25,events+2d,members+31.
        private sealed class Group
        {
            internal readonly List<int> Slots = new List<int>();
            internal readonly ShipFleetNormalTask Task = new ShipFleetNormalTask();
            internal int Count;
            internal uint Age;

            // Matches557760:write at logical Count,overwriting a retained tail slot.
            internal void Append(int registryIndex)
            {
                if (Count == Slots.Count) Slots.Add(registryIndex); else Slots[Count] = registryIndex;
                Count++;
            }
            // Matches55b490:shift logical entries left;DO NOT erase the old tail.
            internal void RemoveAt(int index)
            {
                for (int i = index; i < Count - 1; i++) Slots[i] = Slots[i + 1];
                Count--;
            }
        }

        private readonly Actor[] actors;
        private readonly List<Group> groups = new List<Group>();
        private readonly List<ShipFleetMembershipCommand> commands = new List<ShipFleetMembershipCommand>();
        public int ActorCount => actors.Length;
        public int GroupCount => groups.Count;
        public int CurrentGroup { get; private set; } = -1;
        public int CommandCount => commands.Count;
        public int ConsumedCommandCount { get; private set; }

        /// <param name="registryInstanceIds">Source actor registry order for this local owner.</param>
        public ShipFleetMembership(uint[] registryInstanceIds)
        {
            if (registryInstanceIds == null) throw new ArgumentNullException(nameof(registryInstanceIds));
            if (registryInstanceIds.Length < 1 || registryInstanceIds.Length > 8)
                throw new ArgumentOutOfRangeException(nameof(registryInstanceIds));
            actors = new Actor[registryInstanceIds.Length];
            for (int index = 0; index < actors.Length; index++)
            {
                for (int previous = 0; previous < index; previous++)
                    if (registryInstanceIds[index] == registryInstanceIds[previous])
                        throw new ArgumentException("Actor instance IDs must be unique.", nameof(registryInstanceIds));
                actors[index] = new Actor(registryInstanceIds[index]);
            }
        }

        public uint GetActorId(int registryIndex) => actors[registryIndex].Id;
        public short GetUiGroup(int registryIndex) => actors[registryIndex].UiGroup;
        public short GetSimulationGroup(int registryIndex) => actors[registryIndex].SimulationGroup;
        public int GetMemberIndex(int registryIndex) => actors[registryIndex].MemberIndex;
        public int GetGroupMode(int groupIndex) { GetGroup(groupIndex); return 10; }
        public int GetGroupSerial(int groupIndex) { GetGroup(groupIndex); return groupIndex + 1; }
        public int GetGroupMemberCount(int groupIndex) => GetGroup(groupIndex).Count;
        // Matches49c050:logical member lookup,distinct from4cc590's retained-slot read.
        public int GetGroupMemberRegistryIndex(int groupIndex, int memberIndex)
        {
            Group group = GetGroup(groupIndex);
            if (memberIndex < 0 || memberIndex >= group.Count) throw new ArgumentOutOfRangeException(nameof(memberIndex));
            return group.Slots[memberIndex];
        }
        public ShipFleetMembershipCommand GetCommand(int index) => commands[index];
        // Matches49c020 group lookup;managed bounds reject an invalid projection.
        private Group GetGroup(int index) => groups[index];
        // Source55b490 retained backing slots,including entries beyond logical Count.
        public int GetGroupRetainedSlotCount(int groupIndex) => GetGroup(groupIndex).Slots.Count;
        // Source4cc590 dereferences these retained registry ordinals before an ID scan.
        public int GetGroupRetainedSlotRegistryIndex(int groupIndex, int slot) => GetGroup(groupIndex).Slots[slot];
        // Source group+8,advanced only by explicit4ccd80 Work.
        public uint GetGroupWorkAge(int groupIndex) => GetGroup(groupIndex).Age;
        // Source group+25!=null for the represented normal100/1 task.
        public bool HasNormalTask(int groupIndex) => GetGroup(groupIndex).Task.Subtype == 1;
        // Source task+4 distinguishes100/1 and100/2 within the same group+25 owner.
        public int GetTaskSubtype(int groupIndex) => GetGroup(groupIndex).Task.Subtype;
        // Source route+4 and route+8 logical vectors;no duplicate membership authority.
        public int GetQueuedPointCount(int groupIndex) => GetGroup(groupIndex).Task.QueuedPointCount;
        public ShipFleetNormalTask.QueuedPoint GetQueuedPoint(int groupIndex, int index) => GetGroup(groupIndex).Task.GetQueuedPoint(index);
        public int GetQueuedMemberCount(int groupIndex) => GetGroup(groupIndex).Task.QueuedMemberCount;
        public ShipFleetNormalTask.QueuedMember GetQueuedMember(int groupIndex, int index) => GetGroup(groupIndex).Task.GetQueuedMember(index);
        // Source520c50 packet projection for either subtype;mail delivery stays caller-owned.
        public int GetTaskCommandCount(int groupIndex) => GetGroup(groupIndex).Task.CommandCount;
        public ShipFleetNormalTask.Command GetTaskCommand(int groupIndex, int index) => GetGroup(groupIndex).Task.GetCommand(index);
        // Source task+8 counter recorded by4cc500/4ccc30.
        public uint GetNormalTaskRequestedAt(int groupIndex) => GetGroup(groupIndex).Task.RequestedAt;
        // Source task+c goalX,read by4ccd80/4cc6a0.
        public int GetNormalTaskGoalX(int groupIndex) => GetGroup(groupIndex).Task.GoalX;
        // Source task+10 goalY,read by4ccd80/4cc6a0.
        public int GetNormalTaskGoalY(int groupIndex) => GetGroup(groupIndex).Task.GoalY;
        // Source task+24 vector count and4cc7d0 assignment values.
        public int GetNormalTaskAssignmentCount(int groupIndex) => GetGroup(groupIndex).Task.AssignmentCount;
        // Source4cc760/4cc7d0 lookup of a20-byte assignment,normalized by instance ID.
        public ShipFleetNormalTask.Assignment GetNormalTaskAssignment(int groupIndex, int index) => GetGroup(groupIndex).Task.GetAssignment(index);
        // Source group+2d vector count,filled by4a1340/4a1770.
        public int GetGroupEventCount(int groupIndex) => GetGroup(groupIndex).Task.EventCount;
        // Source32-byte record copied by55b440;the task returns an immutable value.
        public ShipFleetNormalTask.GroupEvent GetGroupEvent(int groupIndex, int index) => GetGroup(groupIndex).Task.GetEvent(index);
        // Source4ccc30/4ccd80 emissions;caller delivers only after an explicit phase.
        public int GetNormalTaskCommandCount(int groupIndex) => GetGroup(groupIndex).Task.CommandCount;
        // Source520c50 addressed20/35 emissions from the last Request/Work of this group.
        public ShipFleetNormalTask.Command GetNormalTaskCommand(int groupIndex, int index) => GetGroup(groupIndex).Task.GetCommand(index);

        /// <summary>
        /// Commit normal source ships, retaining empty older groups. UI membership
        /// changes immediately; generated41 packets do not update simulation words.
        /// Like49ca60, empty input returns0 without creating/changing a group.
        /// </summary>
        public int CommitPending(IReadOnlyList<uint> orderedInstanceIds)
            => CommitPending(orderedInstanceIds, 0, null);

        /// <summary>
        /// Matches49ca60/49bd60 with explicit system+de and actor-registry input.
        /// Reassigning out of an active task needs current cells for4a1770.
        /// No300 is generated for the new taskless group by this conversion.
        /// </summary>
        public int CommitPending(IReadOnlyList<uint> orderedInstanceIds, uint sourceCounter,
            IReadOnlyList<ShipFleetNormalTask.Member> registry)
        {
            if (orderedInstanceIds == null) throw new ArgumentNullException(nameof(orderedInstanceIds));
            if (orderedInstanceIds.Count == 0) return 0;
            if (orderedInstanceIds.Count > actors.Length)
                throw new ArgumentException("Selection exceeds this local actor registry.", nameof(orderedInstanceIds));
            // Validate the bounded projection before mutating any source state.
            var registryIndices = new int[orderedInstanceIds.Count];
            for (int index = 0; index < registryIndices.Length; index++)
            {
                int actor = Find(orderedInstanceIds[index]);
                for (int previous = 0; previous < index; previous++)
                    if (registryIndices[previous] == actor)
                        throw new ArgumentException("Temporary selection must be unique.", nameof(orderedInstanceIds));
                registryIndices[index] = actor;
                RequireRemovalContext(actor, registry);
            }
            if (groups.Count > short.MaxValue)
                throw new NotSupportedException("Wrapped source16-bit group indices are outside this projection.");

            int next = groups.Count;
            groups.Add(new Group());
            CurrentGroup = next;
            foreach (int registryIndex in registryIndices)
                AddUnchecked(registryIndex, next, sourceCounter, registry);
            return next;
        }

        /// <summary>Matches49bd60 only;4a1340 notification is a separate source call.</summary>
        public int AddToGroup(uint instanceId, int groupIndex, uint sourceCounter,
            IReadOnlyList<ShipFleetNormalTask.Member> registry)
        {
            GetGroup(groupIndex); int index = Find(instanceId);
            if (actors[index].UiGroup == groupIndex) return actors[index].MemberIndex;
            if (GetGroup(groupIndex).Task.Subtype == 2)
                throw new NotSupportedException("Queued membership edits require the300/311 source corpus.");
            RequireRemovalContext(index, registry);
            return AddUnchecked(index, groupIndex, sourceCounter, registry);
        }

        // Matches49bd60:old311/41(-1),then new UI word/41(group),then append/index.
        private int AddUnchecked(int registryIndex, int next, uint sourceCounter,
            IReadOnlyList<ShipFleetNormalTask.Member> registry)
        {
            Actor actor = actors[registryIndex];
            if (actor.UiGroup >= 0) RemoveUnchecked(registryIndex, sourceCounter, registry);
            Group group = groups[next];
            actor.UiGroup = checked((short)next);
            commands.Add(new ShipFleetMembershipCommand(actor.Id, actor.UiGroup));
            actor.MemberIndex = group.Count; group.Append(registryIndex);
            return actor.MemberIndex;
        }

        /// <summary>
        /// Matches49bef0 for local auto-delete-off. Its return is0 EVEN AFTER a
        /// successful removal;1 means deleted group in an excluded source branch.
        /// </summary>
        public int RemoveFromGroup(uint instanceId, uint sourceCounter,
            IReadOnlyList<ShipFleetNormalTask.Member> registry)
        {
            int index = Find(instanceId);
            if (actors[index].UiGroup < 0) return 0;
            RequireRemovalContext(index, registry);
            RemoveUnchecked(index, sourceCounter, registry); return 0;
        }

        // Matches49bef0 ->4a1770 BEFORE UI/index reset ->41(-1) ->55b490 ->index repair.
        private void RemoveUnchecked(int registryIndex, uint sourceCounter,
            IReadOnlyList<ShipFleetNormalTask.Member> registry)
        {
            Actor actor = actors[registryIndex]; Group old = groups[actor.UiGroup]; int removedIndex = actor.MemberIndex;
            if (removedIndex < 0 || removedIndex >= old.Count || old.Slots[removedIndex] != registryIndex)
                throw new InvalidOperationException("Source actor membership invariant was broken.");
            if (old.Task.HasTask)
                old.Task.MemberRemoved(sourceCounter, removedIndex, actor.Id, registry[registryIndex].X, registry[registryIndex].Y);
            actor.MemberIndex = 0; actor.UiGroup = -1;
            commands.Add(new ShipFleetMembershipCommand(actor.Id, -1));
            old.RemoveAt(removedIndex);
            for (int member = removedIndex; member < old.Count; member++) actors[old.Slots[member]].MemberIndex--;
        }

        /// <summary>Matches4a1340;does not add membership or synthesize41.</summary>
        public bool NotifyMemberAdded(int groupIndex, uint instanceId, uint sourceCounter)
        {
            Group group = GetGroup(groupIndex); Actor actor = actors[Find(instanceId)];
            return group.Task.MemberAdded(sourceCounter, actor.MemberIndex, actor.Id);
        }

        /// <summary>Matches4ccc30;the existing normal task owns formation/assignment/emissions.</summary>
        public void RequestNormalMove(int groupIndex, IReadOnlyList<ShipFleetNormalTask.Member> registry,
            short[] terrain, int width, int height, int x, int y, uint sourceCounter)
        {
            Group group = GetGroup(groupIndex);
            group.Task.Request(terrain, width, height, SelectMembers(group, registry), x, y, sourceCounter);
        }

        /// <summary>Matches4c4f40 ->4ccd80;no implicit tick,receipt or actor Work.</summary>
        public void WorkNormalTask(int groupIndex, IReadOnlyList<ShipFleetNormalTask.Member> registry,
            short[] terrain, int width, int height, uint pendingSteps)
        {
            Group group = GetGroup(groupIndex);
            if (!group.Task.HasTask) return; //4c4f40 returns before any task/actor access.
            ShipFleetNormalTask.Member[] members = SelectMembers(group, registry);
            var slots = new uint[group.Slots.Count];
            for (int i = 0; i < slots.Length; i++) slots[i] = actors[group.Slots[i]].Id;
            group.Age = group.Task.Work(terrain, width, height, members, slots, group.Age, pendingSteps);
        }

        // Matches4cf2c0;single-point100/2 in existing group owner,without an implicit tick.
        public void RequestQueuedMove(int groupIndex, IReadOnlyList<ShipFleetNormalTask.Member> registry,
            int width, int height, int x, int y, uint sourceCounter)
        {
            Group group = GetGroup(groupIndex);
            group.Task.RequestQueued(width, height, SelectMembers(group, registry), x, y, sourceCounter);
        }

        // Matches4a1700;explicit source cell index,not a position synthesized by rendering.
        public bool NotifyMemberArrived(int groupIndex, uint instanceId, int cellIndex, uint sourceCounter)
        {
            Group group = GetGroup(groupIndex); Actor actor = actors[Find(instanceId)];
            if (actor.UiGroup != groupIndex) throw new ArgumentException("Arrival actor differs from the source group.");
            return group.Task.MemberArrived(sourceCounter, actor.MemberIndex, actor.Id, cellIndex);
        }

        // Matches4ce7c0;read-only route query (including original end flags).
        public int NextQueuedCell(int groupIndex, int width, int x, int y, sbyte mode, out bool end) =>
            GetGroup(groupIndex).Task.NextQueuedCell(width, x, y, mode, out end);

        // Matches4c4f40 ->4cf550;prefix words follow CURRENT GROUP order,not registry order.
        public void WorkQueuedTask(int groupIndex, IReadOnlyList<ShipFleetNormalTask.Member> registry,
            short[] terrain, int width, int height, IReadOnlyList<short> wavePrefixWords,
            uint sourceCounter, uint pendingSteps)
        {
            Group group = GetGroup(groupIndex);
            if (!group.Task.HasTask) return; //4c4f40 returns before registry/task access.
            ShipFleetNormalTask.Member[] members = SelectMembers(group, registry);
            var slots = new uint[group.Slots.Count];
            for (int i = 0; i < slots.Length; i++) slots[i] = actors[group.Slots[i]].Id;
            group.Age = group.Task.WorkQueued(terrain, width, height, members, slots,
                wavePrefixWords, sourceCounter, group.Age, pendingSteps);
        }

        // Projection guard for4c4f40 subtype dispatch. World has no allocation-prefix
        // input yet;reject BEFORE Begin's accepted step changes counter/mail/actors.
        public void ValidateNormalTaskScheduling()
        {
            foreach (Group group in groups)
                if (group.Task.Subtype == 2)
                    throw new NotSupportedException("World queued scheduling requires explicit wave allocation context.");
        }

        /// <summary>Matches4a1c60/4cc4c0;group+8 and member backing storage survive.</summary>
        public void ClearNormalTask(int groupIndex) => GetGroup(groupIndex).Task.Clear();

        // Managed boundary for49bef0/4a1770:never invent position for a task's removal.
        private void RequireRemovalContext(int index, IReadOnlyList<ShipFleetNormalTask.Member> registry)
        {
            Actor actor = actors[index];
            if (actor.UiGroup < 0 || !groups[actor.UiGroup].Task.HasTask) return;
            if (groups[actor.UiGroup].Task.Subtype == 2)
                throw new NotSupportedException("Queued membership edits require the300/311 source corpus.");
            if (registry == null) throw new NotSupportedException("Active-task reassignment requires explicit registry cells and source counter.");
            ValidateRegistry(registry);
        }
        // Matches4cc970/4ccd80 member-ordinal lookup in PLAYERS[owner].actor registry.
        private ShipFleetNormalTask.Member[] SelectMembers(Group group, IReadOnlyList<ShipFleetNormalTask.Member> registry)
        {
            ValidateRegistry(registry); var result = new ShipFleetNormalTask.Member[group.Count];
            for (int i = 0; i < result.Length; i++) result[i] = registry[group.Slots[i]];
            return result;
        }
        // Managed projection guard for the source registry at player+3000;no gameplay rule.
        private void ValidateRegistry(IReadOnlyList<ShipFleetNormalTask.Member> registry)
        {
            if (registry == null) throw new ArgumentNullException(nameof(registry));
            if (registry.Count != actors.Length) throw new ArgumentException("A complete ordered actor registry is required.", nameof(registry));
            for (int i = 0; i < actors.Length; i++)
                if (registry[i].InstanceId != actors[i].Id) throw new ArgumentException("Registry ordinals and instance IDs differ.", nameof(registry));
        }

        /// <summary>
        /// Deliver the next generated41 packet to its actor (50c970, subtype1).
        /// Ordered delivery is explicit, so UI can be ahead of the simulation.
        /// No Work, movement or temporary-selection transition is implied.
        /// </summary>
        public bool ConsumeNext()
        {
            if (ConsumedCommandCount == commands.Count) return false;
            ShipFleetMembershipCommand command = commands[ConsumedCommandCount++];
            actors[Find(command.InstanceId)].SimulationGroup = command.Group;
            return true;
        }

        private int Find(uint instanceId)
        {
            for (int index = 0; index < actors.Length; index++)
                if (actors[index].Id == instanceId) return index;
            throw new ArgumentException("Actor is outside this local normal-ship registry.", nameof(instanceId));
        }
    }
}
