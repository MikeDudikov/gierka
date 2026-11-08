using System;
using System.Collections.Generic;
using AncientConquest.World;

namespace AncientConquest.Simulation
{
    /// <summary>
    /// Bounded520352 world branch:521500 PrepareMail,522850 SendMail,542320
    /// System Life. Normal speed5/non-demo context only. Registration is an
    /// explicit source-system vector,NOT sprite order or an assumed groups-first pass.
    /// </summary>
    public sealed class ShipWorldStep
    {
        public readonly struct Command
        {
            public uint InstanceId { get; }
            public uint Counter { get; }
            public byte Action { get; }
            private readonly byte[] payload;
            // Matches520c50:copy addressed action data and source counter at enqueue.
            private Command(uint id,uint counter,byte action,byte[] data)
            {InstanceId=id;Counter=counter;Action=action;payload=data;}
            // Source520c50/50c970 subtype1,not immediate41 delivery.
            public static Command Membership(uint counter,ShipFleetMembershipCommand packet) =>
                new Command(packet.InstanceId,counter,41,packet.CapturePayload());
            // Source4cf070/4cc650/4c42f0 emissions,not immediate actor requests.
            public static Command Task(uint counter,ShipFleetNormalTask.Command packet) =>
                new Command(packet.InstanceId,counter,packet.Action,packet.CapturePayload());
            // Normalized520c50 payload;the17B linked-list header/pointers are not Unity state.
            public byte[] CapturePayload() => (byte[])payload.Clone();
            // Source little-endian32-bit fields at20 offsets0/4 or41 offset1.
            internal int Read32(int offset) => unchecked((int)((uint)payload[offset]|
                (uint)payload[offset+1]<<8|(uint)payload[offset+2]<<16|(uint)payload[offset+3]<<24));
            // Source action20's ninth byte.
            internal byte MoveArgument => payload[8];
        }

        public readonly struct ActorPublication
        {
            public int RegistryIndex { get; }
            public ShipMoveOrder.Publication Value { get; }
            // Source50d5f0 publication order within each542200 registered actor callback.
            internal ActorPublication(int index,ShipMoveOrder.Publication value)
            {RegistryIndex=index;Value=value;}
        }

        private readonly ShipFleetMembership membership;
        private readonly ShipMoveOrder[] actors;
        private readonly int[] registration;
        private readonly List<Command> ready=new List<Command>();
        private readonly List<Command> received=new List<Command>();
        private readonly List<Command> emitted=new List<Command>();
        private readonly List<ActorPublication> publications=new List<ActorPublication>();
        private readonly List<int> visits=new List<int>();
        public byte PreparationCounter {get;private set;}
        public int ReceivedCount => received.Count;
        public int EmittedCount => emitted.Count;
        public int PublicationCount => publications.Count;
        public int VisitCount => visits.Count;

        /// <summary>
        /// Source542200 vector order is input. -1 denotes its fleet object;
        /// other entries are local actor registry ordinals. No creation/deletion
        /// during iteration,AI,other owner cohorts or full Ship::Life is represented.
        /// Actor group readers MUST use membership.GetSimulationGroup,as documented.
        /// </summary>
        public ShipWorldStep(ShipFleetMembership membership,MissionOccupancyGrid grid,
            ShipMoveOrder[] actors,int[] registrationOrder,byte initialPreparationCounter)
        {
            if(membership==null)throw new ArgumentNullException(nameof(membership));
            if(grid==null)throw new ArgumentNullException(nameof(grid));
            if(actors==null)throw new ArgumentNullException(nameof(actors));
            if(registrationOrder==null)throw new ArgumentNullException(nameof(registrationOrder));
            if(grid.Width!=24||grid.Height!=24||actors.Length!=membership.ActorCount||registrationOrder.Length!=actors.Length+1)
                throw new NotSupportedException("A complete initialized local24x24 cohort and one fleet registration are required.");
            var seen=new bool[actors.Length+1];
            foreach(int entry in registrationOrder)
            {
                if(entry< -1||entry>=actors.Length||seen[entry+1])throw new ArgumentException("Source registration must contain each actor and the fleet once.",nameof(registrationOrder));
                seen[entry+1]=true;
            }
            for(int i=0;i<actors.Length;i++)
                if(actors[i]==null||actors[i].InstanceId!=membership.GetActorId(i))throw new ArgumentException("Actor registry order differs from membership.",nameof(actors));
            this.membership=membership;this.actors=(ShipMoveOrder[])actors.Clone();registration=(int[])registrationOrder.Clone();
            PreparationCounter=initialPreparationCounter;
        }

        // Read-only normalized522850 delivery observation for differential tests/adapters.
        public Command GetReceived(int index)=>received[index];
        // Read-only520c50 emissions from this accepted step,still queued for a later mail phase.
        public Command GetEmitted(int index)=>emitted[index];
        // Source-ordered50d5f0 outputs;render adapters consume these after simulation.
        public ActorPublication GetPublication(int index)=>publications[index];
        // Observes542200's actual visit order,not a second scheduling policy.
        public int GetVisit(int index)=>visits[index];

        /// <summary>
        /// Controlled4e12e0/4e2180 cohort boundary outside Life. Existing context
        /// is retained;this is not full world save/load or a new source tick.
        /// Source actor registry ordinals determine record order. All records
        /// and in-place claims/poses/counters are preflighted before any actor.
        /// No mail,task,membership,phase or registration vector is changed.
        /// </summary>
        public void RestoreCohortInPlace(byte[][] records,uint sourceCounter)
        {
            if(records==null)throw new ArgumentNullException(nameof(records));
            if(records.Length!=actors.Length)throw new ArgumentException("Complete actor registry records are required.",nameof(records));
            var owned=new byte[records.Length][];
            for(int i=0;i<owned.Length;i++)
            {
                if(records[i]==null)throw new ArgumentException("A cohort record is missing.",nameof(records));
                owned[i]=(byte[])records[i].Clone();
            }
            for(int i=0;i<actors.Length;i++)actors[i].ValidateInPlaceSourceMovementState(owned[i],sourceCounter);
            for(int i=0;i<actors.Length;i++)actors[i].RestoreSourceMovementState(owned[i],sourceCounter);
        }

        /// <summary>
        /// Matches520352..5203ec for the selected40ms branch. No Unity time
        /// source. References remain caller-owned. Outgoing is the source2e
        /// control queue;it is captured ONCE before objects,never drained again
        /// after a group callback. Valid supported packets promote before ship Work.
        /// </summary>
        public bool TryAdvance(int capturedTime,ref int previousTime,ref uint counter,
            short[] terrain,List<Command> outgoing)
            => TryAdvanceCore(capturedTime,ref previousTime,ref counter,terrain,null,outgoing);

        /// <summary>
        /// Matches the same520352 branch with4cf550/4ceab0 memory made explicit.
        /// One signed prefix word per actor REGISTRY ordinal for this accepted
        /// step;the group maps these to its member order at its actual Life visit.
        /// No Windows heap default,extra clock or second mail phase is implied.
        /// </summary>
        public bool TryAdvance(int capturedTime,ref int previousTime,ref uint counter,
            short[] terrain,IReadOnlyList<short> wavePrefixWords,List<Command> outgoing)
        {
            if(wavePrefixWords==null)throw new ArgumentNullException(nameof(wavePrefixWords));
            if(wavePrefixWords.Count!=actors.Length)throw new ArgumentException("A complete registry-ordered wave memory context is required.",nameof(wavePrefixWords));
            var words=new short[actors.Length];
            for(int i=0;i<words.Length;i++)words[i]=wavePrefixWords[i];
            return TryAdvanceCore(capturedTime,ref previousTime,ref counter,terrain,words,outgoing);
        }

        // Matches520352..5203ec,521500,522850,542200;all accepted profiles now
        // execute4a1700 notifications,including100/1 (formerly a probe boundary).
        private bool TryAdvanceCore(int capturedTime,ref int previousTime,ref uint counter,
            short[] terrain,IReadOnlyList<short> wavePrefixWords,List<Command> outgoing)
        {
            if(outgoing==null)throw new ArgumentNullException(nameof(outgoing));
            var step=SingleStepClock.Begin(capturedTime,previousTime,counter,40);
            if(!step.StepRequested)
            {received.Clear();emitted.Clear();publications.Clear();visits.Clear();return false;}
            ValidateTaskInputs(terrain,wavePrefixWords);
            // Projection preflight,not an original gameplay rule. Only normal20/41
            // in the healthy normal80 profile are implemented;other families/35 excluded.
            for(int i=0;i<actors.Length;i++)
                if(actors[i].Current.SourceCounter!=counter)throw new InvalidOperationException("Actor and world counters differ.");
            if(PreparationCounter>=2)ValidateDelivery(outgoing);
            //Observation buffers follow the accepted source branch;invalid
            //projection inputs preserve the previous completed observation too.
            received.Clear();emitted.Clear();publications.Clear();visits.Clear();
            counter=step.Counter;
            ExecuteAccepted(counter,1,terrain,wavePrefixWords,outgoing);
            previousTime=SingleStepClock.Complete(capturedTime,previousTime,40);
            return true;
        }

        // Managed projection checks for4c4f40 ->4cf550. Unsupported context or
        //queued300/311 must fail before ANY counter/mail/actor changes.
        private void ValidateTaskInputs(short[] terrain,IReadOnlyList<short> wavePrefixWords)
        {
            if(wavePrefixWords==null)membership.ValidateNormalTaskScheduling();
            for(int group=0;group<membership.GroupCount;group++)
            {
                if(membership.GetTaskSubtype(group)!=2)continue;
                if(terrain==null)throw new ArgumentNullException(nameof(terrain));
                if(terrain.Length!=24*24)throw new ArgumentException("A complete source navigation field is required.",nameof(terrain));
                foreach(short value in terrain)if(value!=0&&value!=-1)
                    throw new NotSupportedException("Queued navigation requires the represented zero/minus-one field.");
                for(int i=0;i<membership.GetGroupEventCount(group);i++)
                    if(membership.GetGroupEvent(group,i).Code!=310)
                        throw new NotSupportedException("Queued membership edit/report events are outside this world profile.");
            }
        }

        // Matches521500 normal non-demo speed5:table5bed74+5*24+14 is2.
        // Below2 increment3e and keep2e queued;once ready,capture FIFO and clear2e.
        // The normal non-demo return does NOT reset3e after capture.
        private void PrepareMail(List<Command> outgoing)
        {
            ready.Clear();
            if(PreparationCounter<2){PreparationCounter++;return;}
            ready.AddRange(outgoing);outgoing.Clear();
        }

        // Matches522850 then542320/542200;fleet visits owner5's groups in order.
        private void ExecuteAccepted(uint counter,uint pendingSteps,short[] terrain,
            IReadOnlyList<short> wavePrefixWords,List<Command> outgoing)
        {
            PrepareMail(outgoing);
            foreach(Command packet in ready)
            {
                int index=Find(packet.InstanceId);
                if(packet.Action==41)membership.ConsumeNext(); //Documented50c970 synchronization boundary.
                else if(!actors[index].ReceiveNormalCellMove(packet.InstanceId,packet.Read32(0),packet.Read32(4),packet.MoveArgument))
                    throw new InvalidOperationException("Source normal move capability was rejected.");
                received.Add(packet);
            }
            ready.Clear();
            foreach(int entry in registration)
            {
                visits.Add(entry);
                if(entry<0)
                {
                    var registry=CaptureRegistry();int count=membership.GroupCount;
                    for(int group=0;group<count;group++)
                    {
                        if(membership.GetTaskSubtype(group)==2)
                        {
                            var words=new short[membership.GetGroupMemberCount(group)];
                            for(int i=0;i<words.Length;i++)
                                words[i]=wavePrefixWords[membership.GetGroupMemberRegistryIndex(group,i)];
                            membership.WorkQueuedTask(group,registry,terrain,24,24,words,counter,pendingSteps);
                        }
                        else membership.WorkNormalTask(group,registry,terrain,24,24,pendingSteps);
                        for(int i=0;i<membership.GetTaskCommandCount(group);i++)
                        {
                            Command packet=Command.Task(counter,membership.GetTaskCommand(group,i));
                            outgoing.Add(packet);emitted.Add(packet);
                        }
                    }
                }
                else
                {
                    actors[entry].Tick(counter,(int)pendingSteps);
                    //4a49af/4a4a67 ->4a1700:append at this registry position,
                    //before a later fleet visit,not after the whole object loop.
                    int group=membership.GetUiGroup(entry);
                    if(group>=0)for(int i=0;i<actors[entry].LastStepArrivalCount;i++)
                    {
                        var arrival=actors[entry].GetLastStepArrival(i);
                        membership.NotifyMemberArrived(group,actors[entry].InstanceId,arrival.CellIndex,arrival.Counter);
                    }
                    for(int i=0;i<actors[entry].LastStepPublicationCount;i++)
                        publications.Add(new ActorPublication(entry,actors[entry].GetLastStepPublication(i)));
                }
            }
        }

        // Matches4cc970/4ccd80 reads through local member ordinals at the fleet's visit.
        private ShipFleetNormalTask.Member[] CaptureRegistry()
        {
            var result=new ShipFleetNormalTask.Member[actors.Length];
            for(int i=0;i<result.Length;i++)
            {var m=actors[i].Current.Motion;result[i]=new ShipFleetNormalTask.Member(actors[i].InstanceId,m.CellX,m.CellY,m.State);}
            return result;
        }

        // Source51f1e0 routes addressed280f to the existing actor registry.
        private int Find(uint id)
        {
            for(int i=0;i<actors.Length;i++)if(actors[i].InstanceId==id)return i;
            throw new ArgumentException("Packet target is outside this local cohort.",nameof(id));
        }

        // Managed guard of the verified normal nonblocking ShipMoveOrder receiver.
        // Never silently execute an unsupported packet or change source delivery timing.
        private void ValidateDelivery(List<Command> packets)
        {
            int next41=membership.ConsumedCommandCount;
            foreach(Command p in packets)
            {
                int index=Find(p.InstanceId);
                if(p.Action==41)
                {
                    if(next41>=membership.CommandCount)throw new InvalidOperationException("Unexpected41 packet.");
                    var expected=membership.GetCommand(next41++);
                    if(expected.InstanceId!=p.InstanceId||expected.Group!=p.Read32(1))throw new InvalidOperationException("Membership FIFO differs from world FIFO.");
                }
                else if(p.Action==20)
                {
                    if(!actors[index].HasNormalCellMoveReceiver||(p.MoveArgument!=0&&p.MoveArgument!=255))
                        throw new NotSupportedException("Only the normal live-local20 profile is verified.");
                }
                else throw new NotSupportedException("Only normal41/20 receipt is implemented in this world cohort.");
            }
        }
    }
}
