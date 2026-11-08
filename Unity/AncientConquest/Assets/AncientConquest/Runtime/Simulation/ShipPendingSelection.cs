using System;
using System.Collections.Generic;

namespace AncientConquest.Simulation
{
    public readonly struct ShipSelectionEvent
    {
        public object Owner { get; }
        public bool Selected { get; }
        internal ShipSelectionEvent(object owner, bool selected) { Owner = owner; Selected = selected; }
    }

    /// <summary>Normal C453/C455/C457 temporary fleet. Committed groups and commands are separate.</summary>
    public sealed class ShipPendingSelection
    {
        private readonly object[] local;
        private readonly List<object> members = new List<object>();
        private readonly List<ShipSelectionEvent> events = new List<ShipSelectionEvent>();
        private readonly Func<object,short> uiGroup;
        private readonly Func<short,object[]> groupMembers;
        public int Count => members.Count;
        public int TemporaryCount => Pending ? members.Count : 0;
        public short CurrentGroup { get; private set; } = -1;
        public bool Selected { get; private set; }
        public bool Pending { get; private set; }
        public int EventCount => events.Count;
        public ShipPendingSelection(object[] localOwners) : this(localOwners,null,null) { }
        public ShipPendingSelection(object[] localOwners,Func<object,short> readUiGroup,Func<short,object[]> readGroupMembers)
        {
            if((readUiGroup==null)!=(readGroupMembers==null))throw new ArgumentException("Both group readers are required together.");
            uiGroup=readUiGroup;groupMembers=readGroupMembers;
            if (localOwners == null) throw new ArgumentNullException(nameof(localOwners));
            if (localOwners.Length < 1 || localOwners.Length > 8) throw new ArgumentOutOfRangeException(nameof(localOwners));
            local = (object[])localOwners.Clone();
            for (int i = 0; i < local.Length; i++)
            {
                if (local[i] == null) throw new ArgumentException("A local actor owner is missing.");
                for (int j = 0; j < i; j++) if (ReferenceEquals(local[i], local[j]))
                    throw new ArgumentException("Local actors must have unique reference identities.");
            }
        }
        public object GetMember(int index) => members[index];
        public ShipSelectionEvent GetEvent(int index) => events[index];
        public bool Contains(object owner) => Find(owner) >= 0;
        private int Find(object owner)
        { for (int i = 0; i < members.Count; i++) if (ReferenceEquals(members[i], owner)) return i; return -1; }
        private bool Local(object owner)
        { foreach (object actor in local) if (ReferenceEquals(actor, owner)) return true; return false; }
        private void Clear()
        {
            foreach (object owner in members) events.Add(new ShipSelectionEvent(owner, false));
            members.Clear(); Pending = Selected = false; CurrentGroup = -1;
        }
        /// <summary>49e230 clears the temporary vector after committing,without deselection.</summary>
        public void MarkCommitted(short group)
        {
            if(groupMembers==null)throw new NotSupportedException("Committed groups require their actual member registry.");
            if(group<0)throw new ArgumentOutOfRangeException(nameof(group));
            object[] actual=groupMembers(group);
            if(!Pending||actual.Length!=members.Count)throw new InvalidOperationException("Commit must retain the ordered temporary members.");
            for(int i=0;i<actual.Length;i++)if(!ReferenceEquals(actual[i],members[i]))throw new InvalidOperationException("Committed member order differs.");
            events.Clear();CurrentGroup=group;Pending=false;
        }
        private void Append(object owner)
        { if (!Contains(owner)) members.Add(owner); }
        private static ShipPointerCommands.Result Same(ShipPointerCommandInput input) =>
            new ShipPointerCommands.Result(input.CursorType, input.ActionMask, input.ActionBit, input.Blocked);

        public ShipPointerCommands.Result ProcessRelease(ShipPointerCommandInput input, int message, uint flags)
        {
            events.Clear();
            if (!input.Enabled || (message != 0x62 && message != 0x64)) return Same(input);
            if (message == 0x64)
            {
                if (input.HoveredOwner == null)
                {
                    if (Selected) Clear();
                    return new ShipPointerCommands.Result(0, input.CursorType == 0 ? input.ActionMask : (ushort)0, input.ActionBit, false);
                }
                // Contextual action cycling is intentionally outside selection-only mode.
                if (input.CursorType == 5 && input.ActionMask == 0 && !input.Blocked) return Same(input);
                if (input.CursorType == 6 || input.Blocked)
                    return new ShipPointerCommands.Result(0, 0, input.ActionBit, false);
                throw new NotSupportedException("Contextual right-release actions need the command layer.");
            }
            if (input.Blocked || input.CursorType != 5 || !Local(input.HoveredOwner)) return Same(input);
            if ((flags & 4u) != 0)
            {
                if(!Pending&&CurrentGroup>=0)throw new NotSupportedException("Shift editing a committed group needs task-event ownership.");
                int index = Find(input.HoveredOwner);
                if (index >= 0)
                {
                    members.RemoveAt(index); events.Add(new ShipSelectionEvent(input.HoveredOwner, false));
                    Selected = members.Count != 0;
                    // Source leaves its pending byte set when the last member is toggled off.
                }
                else
                {
                    Append(input.HoveredOwner); Pending = Selected = true;
                    events.Add(new ShipSelectionEvent(input.HoveredOwner, true));
                }
            }
            else
            {
                short group=(flags&8u)!=0&&uiGroup!=null?uiGroup(input.HoveredOwner):(short)-1;
                if(group< -1)throw new NotSupportedException("Wrapped source groups are outside this projection.");
                object[] committed=group>=0?groupMembers(group):null;
                if(committed!=null)
                {
                    foreach(object owner in committed)if(!Local(owner))throw new NotSupportedException("A committed group contains a nonlocal actor.");
                    Clear();CurrentGroup=group;
                    foreach(object owner in committed){Append(owner);events.Add(new ShipSelectionEvent(owner,true));}
                    Selected=members.Count!=0;
                }
                else
                {
                    Clear(); Append(input.HoveredOwner); Pending = Selected = true;
                    events.Add(new ShipSelectionEvent(input.HoveredOwner, true));
                }
            }
            return new ShipPointerCommands.Result((flags & 4u) != 0 ? input.CursorType : 0, input.ActionMask, input.ActionBit, false);
        }
        public ShipPointerCommands.Result ProcessBox(ShipPointerCommandInput input, int width, int height,
            object[] candidates, uint flags)
        {
            events.Clear();
            if (candidates == null) throw new ArgumentNullException(nameof(candidates));
            if (width < 1 || width > 24 || height < 1 || height > 24) throw new ArgumentOutOfRangeException(nameof(width));
            foreach (object owner in candidates) if (!Local(owner)) throw new NotSupportedException("Only initialized local normal ships may enter the temporary fleet.");
            if (!input.Enabled || candidates.Length == 0 ||
                ((input.CursorType == 5 || input.CursorType == 6) && width == 1 && height == 1)) return Same(input);
            if((flags&4u)!=0&&!Pending&&CurrentGroup>=0)throw new NotSupportedException("Shift box editing a committed group needs task-event ownership.");
            if ((flags & 4u) == 0) Clear();
            foreach (object owner in candidates) Append(owner);
            Pending = Selected = true;
            // Adding a rectangle re-sends C453 to the entire temporary vector.
            foreach (object owner in members) events.Add(new ShipSelectionEvent(owner, true));
            return Same(input);
        }
    }
}
