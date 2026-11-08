using System;
using System.Collections;
using System.Collections.Generic;
using AncientConquest.Simulation;
using AncientConquest.World;
using UnityEngine;

namespace AncientConquest.Presentation
{
    /// <summary>Explicit three-body order/work/render replay;no player input or full Life clock.</summary>
    internal sealed class ShipFleetMotionReference : IDisposable
    {
        internal sealed class Binding
        {
            internal readonly MissionShipSeed Seed;
            internal readonly object Owner;
            internal readonly Dictionary<int,SpriteRenderer> Renderers;
            internal Binding(MissionShipSeed seed,object owner,Dictionary<int,SpriteRenderer> renderers)
            {Seed=seed;Owner=owner;Renderers=renderers;}
        }
        private const string Prefix="[ShipFleetMotion] ";
        private static readonly int[] Checkpoints={1,3,6,10,16,25,35,50,60,80,100,125,150,200,250};
        private readonly MissionOccupancyGrid grid;
        private readonly SourceCohortOrderReference order;
        private readonly Binding[] bindings;
        private readonly ShipMoveOrder[] Motion=new ShipMoveOrder[3];
        private readonly SourceShipPoseReference[] poses=new SourceShipPoseReference[3];
        private readonly object[] Owners=new object[8];
        private readonly int[] Ids=new int[8];
        private readonly uint[] classes=new uint[8];
        private readonly short[] Groups=new short[8];
        private readonly int pending;
        private readonly bool reverse;
        private uint counter;
        private bool disposed,ran;
        private ShipFleetMembership worldMembership;

        internal ShipFleetMotionReference(MissionOccupancyGrid grid,Binding[] actors,SourceCohortOrderReference order)
        {
            this.grid=grid;this.order=order;bindings=(Binding[])actors.Clone();
            Array.Sort(bindings,(a,b)=>a.Seed.InstanceId.CompareTo(b.Seed.InstanceId));
            if(bindings.Length!=8)throw new InvalidOperationException("All eight actor bindings are required.");
            string[] args=Environment.GetCommandLineArgs();int p=Array.IndexOf(args,"--ship-fleet-motion-pending");pending=1;
            if(p>=0 && (p+1>=args.Length || !int.TryParse(args[p+1],out pending)))throw new ArgumentException("Invalid fleet pending count.");
            if(pending!=1&&pending!=2&&pending!=3&&pending!=7)throw new ArgumentException("Unsupported fleet pending count.");
            reverse=Array.IndexOf(args,"--ship-fleet-motion-reverse")>=0;
            for(int i=0;i<8;i++){Owners[i]=bindings[i].Owner;Ids[i]=checked((int)bindings[i].Seed.InstanceId);classes[i]=bindings[i].Seed.RuntimeClassTag;Groups[i]=-1;}
            try
            {
                for(int i=0;i<3;i++)
                {
                    if(Ids[i]!=11+i)throw new InvalidOperationException("The three actual local recipes are required.");
                    int index=i;Motion[i]=ShipMoveOrder.CreateLiveLocal(grid,Owners[i],bindings[i].Seed,Describe,()=>ReadGroup(index),DescribePlanning,0);
                    poses[i]=new SourceShipPoseReference(bindings[i].Renderers,i==2);
                    var m=Motion[i].Current.Motion;poses[i].Apply(m.DrawnFrame,m.PublishedWorldX,m.PublishedWorldY);
                }
            }
            catch{Dispose();throw;}
        }
        private ShipNavigationOccupant Describe(object owner)
        {for(int i=0;i<8;i++)if(ReferenceEquals(owner,Owners[i]))return new ShipNavigationOccupant(classes[i],i<3?Motion[i].Current.Motion.State:(byte)0);throw new InvalidOperationException("Unknown grid owner.");}
        private ShipPlanningOccupant DescribePlanning(object owner)
        {for(int i=0;i<8;i++)if(ReferenceEquals(owner,Owners[i]))return new ShipPlanningOccupant(classes[i],i<3?Motion[i].Current.Motion.State:(byte)0,ReadGroup(i));throw new InvalidOperationException("Unknown planning owner.");}
        //50c970:world mode has one authoritative5e word in membership;legacy replay retains explicit words.
        private short ReadGroup(int index)=>worldMembership!=null&&index<3?worldMembership.GetSimulationGroup(index):Groups[index];
        private static string Hex(byte[] bytes)=>BitConverter.ToString(bytes).Replace("-","").ToLowerInvariant();
        internal string ActorRow(int index)
        {
            var body=Motion[index];var s=body.Current;var m=s.Motion;var pubs=new List<string>();
            for(int i=0;i<body.LastStepPublicationCount;i++){var p=body.GetLastStepPublication(i);pubs.Add(string.Join(",",p.Frame,p.WorldPixelX,p.WorldPixelY,p.Depth));}
            var changes=new List<string>();
            for(int i=0;i<body.LastStepGridMutationCount;i++){var p=body.GetLastStepGridMutation(i);changes.Add(p.CellIndex+","+(p.Occupied?Ids[index]:0));}
            var claims=new List<string>();
            for(int y=0;y<24;y++)for(int x=0;x<24;x++)
            {object owner=grid.GetOccupant(x,y);if(owner==null)continue;int id=-1;for(int i=0;i<8;i++)if(ReferenceEquals(owner,Owners[i]))id=Ids[i];claims.Add((y*24+x)+","+id);}
            return string.Join("\t",new object[]{Ids[index],m.CellX,m.CellY,m.WorldPixelX,m.WorldPixelY,m.State,m.CenterGate?1:0,m.Heading,m.TargetHeading,m.TurnStep,
                m.Speed,m.Remainder,m.Deceleration,m.ReservedCellIndex,m.NextCellIndex,m.LastCellIndex,m.PathIndex,m.PathCount,m.StoredFrame,m.LastFrameTick,m.LastStateCounter,s.RandomState,
                body.CurrentAcceleration,s.Retry,body.LastStepReachedForwardTail?1:0,m.DrawnFrame,m.PublishedWorldX,m.PublishedWorldY,string.Join(";",pubs),string.Join(";",changes),string.Join(";",claims),s.PendingFlags,s.ActiveFlags,s.DeferredFlags,s.StopMask,s.ReadyMask,s.Capabilities,s.RequestedGoalX,s.RequestedGoalY,s.TargetX,s.TargetY,s.FirstNavigation?1:0,s.LastPlanCounter,s.RetryInterval,s.NavigationRadius,s.SnapshotRetry,s.SnapshotTargetX,s.SnapshotTargetY,s.SnapshotCellX,s.SnapshotCellY,Hex(body.CaptureRoutePoints()),string.Join(",",body.CaptureCachedObstacles()),Hex(body.CapturePendingMoveRecord()),ReadGroup(index)});
        }
        private void LogStage(string stage)
        {
            Debug.Log(Prefix+"stage: "+stage+"; counter="+counter);
            for(int i=0;i<3;i++)
            {
                Debug.Log(Prefix+"actor: "+stage+"\t"+ActorRow(i));
                foreach(var part in bindings[i].Renderers)
                    Debug.Log(Prefix+"part: "+stage+"; id="+Ids[i]+"; index="+part.Key+"; sprite="+part.Value.sprite.name+"; order="+part.Value.sortingOrder+
                        "; world="+(int)part.Value.transform.localPosition.x+","+(int)-part.Value.transform.localPosition.y);
            }
            order.LogStage(stage,"[ShipFleetMotion]");
            Debug.Log(Prefix+"end: "+stage);
        }
        private void ApplyPublications(int i,Action<object,uint,int,int> beforePose=null)
        {
            for(int j=0;j<Motion[i].LastStepPublicationCount;j++)
            {
                var p=Motion[i].GetLastStepPublication(j);beforePose?.Invoke(Owners[i],counter,p.WorldPixelX,p.WorldPixelY);
                poses[i].Apply(p.Frame,p.WorldPixelX,p.WorldPixelY);order.UpdateParent((uint)Ids[i],p.Depth);
                Debug.Log(Prefix+"publication: "+counter+"; id="+Ids[i]+"; index="+j+"; frame="+p.Frame+"; world="+p.WorldPixelX+","+p.WorldPixelY+"; depth="+p.Depth);
            }
        }
        internal ShipMoveOrder FindMotion(object owner)
        {for(int i=0;i<3;i++)if(ReferenceEquals(owner,Owners[i]))return Motion[i];return null;}
        internal void ReceiveMembership(uint id,short group)
        {for(int i=0;i<3;i++)if(Ids[i]==id){Groups[i]=group;return;}throw new ArgumentException("Unknown local group recipient.");}
        internal void TickAll(uint sourceCounter,Action<object,uint,int,int> beforePose)
        {
            if(disposed)throw new ObjectDisposedException(nameof(ShipFleetMotionReference));
            counter=sourceCounter;
            for(int i=0;i<3;i++){Motion[i].Tick(counter,1);ApplyPublications(i,beforePose);}
        }
        internal void LogWorld(string stage)=>LogStage(stage);
        //542200 registration is an explicit diagnostic input,not inferred from sprite/ID order.
        //50c970:the UI and the live planner share the same authoritative membership words.
        internal ShipWorldStep BindInputWorld(ShipFleetMembership membership,int[] registration,byte mailGate)
        {
            if(disposed)throw new ObjectDisposedException(nameof(ShipFleetMotionReference));
            if(worldMembership!=null||ran)throw new InvalidOperationException("The fleet already has a world lifecycle.");
            var world=new ShipWorldStep(membership,grid,Motion,registration,mailGate);
            worldMembership=membership;
            return world;
        }
        //520352..5203ec owns Begin/Complete;the adapter only consumes50d5f0 publications.
        internal bool AdvanceInputWorld(ShipWorldStep world,int captured,ref int phase,ref uint sourceCounter,
            short[] terrain,List<ShipWorldStep.Command> outgoing,Action<object,uint,int,int> beforePose,
            IReadOnlyList<short> wavePrefixWords=null)
        {
            if(disposed)throw new ObjectDisposedException(nameof(ShipFleetMotionReference));
            if(worldMembership==null)throw new InvalidOperationException("Bind the input world before advancing it.");
            //4cebc7's signed prefix is explicit diagnostic input,never an implicit CRT default.
            bool advanced=wavePrefixWords==null?world.TryAdvance(captured,ref phase,ref sourceCounter,terrain,outgoing):
                world.TryAdvance(captured,ref phase,ref sourceCounter,terrain,wavePrefixWords,outgoing);
            if(!advanced)return false;
            counter=sourceCounter;ApplyWorldPublications(world,beforePose);
            for(int i=0;i<world.ReceivedCount;i++)Debug.Log("[ShipWorldStep] received: at="+counter+"; packet="+WorldPacket(world.GetReceived(i)));
            for(int i=0;i<world.EmittedCount;i++)Debug.Log("[ShipWorldStep] emitted: at="+counter+"; packet="+WorldPacket(world.GetEmitted(i)));
            return true;
        }
        internal IEnumerator Run()
        {
            if(ran||disposed)throw new InvalidOperationException("Fleet replay runs once.");ran=true;
            if(Array.IndexOf(Environment.GetCommandLineArgs(),"--ship-fleet-world-step")>=0)
            {yield return RunWorld();yield break;}
            Debug.Log(Prefix+"conditions: pending="+pending+"; reverse="+reverse+"; seed=0; wind=0,5; simulation_group_input=0; scheduler=controlled; input=False; final_art=False");
            order.LogReadiness("[ShipFleetMotion]");
            yield return new WaitForEndOfFrame();LogStage("initial");yield return new WaitForSecondsRealtime(1.25f);
            int[,] goals={{18,5},{20,6},{18,4}};
            //Explicit received41 words,as in the pinned native normal scenario.
            for(int i=0;i<3;i++)Groups[i]=0;
            for(int i=0;i<3;i++)Motion[i].ReceiveCellMove((uint)Ids[i],goals[i,0],goals[i,1],0);
            yield return new WaitForEndOfFrame();LogStage("requests");yield return new WaitForSecondsRealtime(1.25f);
            double start=Time.realtimeSinceStartupAsDouble;int accumulated=0,previous=0;
            while(counter<250)
            {
                int captured=accumulated+(int)((Time.realtimeSinceStartupAsDouble-start)*1000.0);
                var tick=SingleStepClock.Begin(captured,previous,counter,40);
                if(!tick.StepRequested){yield return null;continue;}
                counter=tick.Counter;
                for(int n=0;n<3;n++){int i=reverse?2-n:n;Motion[i].Tick(counter,pending);ApplyPublications(i);}
                previous=SingleStepClock.Complete(captured,previous,40);
                if(Array.IndexOf(Checkpoints,(int)counter)>=0)
                {
                    yield return new WaitForEndOfFrame();LogStage("tick-"+counter);yield return new WaitForSecondsRealtime(1.25f);
                    accumulated=captured;start=Time.realtimeSinceStartupAsDouble;
                }
                else yield return null;
            }
            Debug.Log(Prefix+"complete: counter=250; actors=3; routes=live; input=False");
        }

        //4cc970/4ccd80 read actual logical cells/state through source member ordinals.
        internal ShipFleetNormalTask.Member[] CaptureWorldRegistry()
        {
            var result=new ShipFleetNormalTask.Member[3];
            for(int i=0;i<3;i++){var m=Motion[i].Current.Motion;result[i]=new ShipFleetNormalTask.Member((uint)Ids[i],m.CellX,m.CellY,m.State);}
            return result;
        }
        //Presentation consumes immutable50d5f0 outputs in542200 order;never drives grid/physics.
        private void ApplyWorldPublications(ShipWorldStep world,Action<object,uint,int,int> beforePose=null)
        {
            var counts=new int[3];
            for(int n=0;n<world.PublicationCount;n++)
            {
                var item=world.GetPublication(n);int i=item.RegistryIndex;var p=item.Value;
                beforePose?.Invoke(Owners[i],counter,p.WorldPixelX,p.WorldPixelY);
                poses[i].Apply(p.Frame,p.WorldPixelX,p.WorldPixelY);order.UpdateParent((uint)Ids[i],p.Depth);
                Debug.Log(Prefix+"publication: "+counter+"; id="+Ids[i]+"; index="+(counts[i]++)+"; frame="+p.Frame+"; world="+p.WorldPixelX+","+p.WorldPixelY+"; depth="+p.Depth);
            }
        }
        //Read-only normalized520c50 record for source/world QA;not a game resource path.
        private static string WorldPacket(ShipWorldStep.Command packet)=>packet.InstanceId+":"+packet.Action+":"+packet.Counter+":"+Hex(packet.CapturePayload());
        //4e2180 restores sprite fields after actor state. This controlled in-place
        //adapter reuses verified poses/registration:world coordinates and hence
        //parent depths are preflighted unchanged,so no equal-depth reinsertion.
        private void RestoreWorldCohort(ShipWorldStep world,string directory,int phase,List<ShipWorldStep.Command> outgoing)
        {
            var records=new byte[Motion.Length][];
            for(int i=0;i<records.Length;i++)records[i]=System.IO.File.ReadAllBytes(System.IO.Path.Combine(directory,
                Ids[i].ToString("x8",System.Globalization.CultureInfo.InvariantCulture)+".bin"));
            world.RestoreCohortInPlace(records,counter);
            for(int i=0;i<Motion.Length;i++)
            {
                var m=Motion[i].Current.Motion;poses[i].Apply(m.DrawnFrame,m.PublishedWorldX,m.PublishedWorldY);
            }
            Debug.Log("[ShipWorldRestore] context: counter="+counter+"; phase="+phase+"; queued="+outgoing.Count+
                "; age="+worldMembership.GetGroupWorkAge(0)+"; prep="+world.PreparationCounter);
        }
        //40ms selected branch replay,with EXPLICIT controlled registry order and warm mail state.
        private IEnumerator RunWorld()
        {
            string[] args=Environment.GetCommandLineArgs();int option=Array.IndexOf(args,"--ship-fleet-world-registration");
            if(pending!=1||reverse||option<0||option+1>=args.Length)throw new ArgumentException("World step requires pending1,no reverse shortcut,and explicit --ship-fleet-world-registration.");
            string[] names=args[option+1].Split(',');var registration=new int[names.Length];
            for(int i=0;i<names.Length;i++)registration[i]=names[i]=="fleet"?-1:int.Parse(names[i])-11;
            bool busyReplay=Array.IndexOf(args,"--ship-fleet-world-busy")>=0;
            int restoreOption=Array.IndexOf(args,"--ship-fleet-world-restore-dir");string restoreDirectory=null;
            if(restoreOption>=0)
            {
                if(!busyReplay||restoreOption+1>=args.Length)throw new ArgumentException("Cohort restore requires busy replay and an explicit record directory.");
                restoreDirectory=args[restoreOption+1];
            }
            int notifyBefore=busyReplay?10:201;
            worldMembership=new ShipFleetMembership(new uint[]{11,12,13});
            var world=new ShipWorldStep(worldMembership,grid,Motion,registration,2);
            var outgoing=new List<ShipWorldStep.Command>();var terrain=new short[576];
            for(int y=0;y<24;y++)for(int x=0;x<24;x++)terrain[y*24+x]=grid.IsTerrainPassable(x,y,0)?(short)0:(short)-1;
            worldMembership.CommitPending(busyReplay?new uint[]{11,12,13}:new uint[]{11});
            for(int i=0;i<worldMembership.CommandCount;i++)outgoing.Add(ShipWorldStep.Command.Membership(counter,worldMembership.GetCommand(i)));
            worldMembership.RequestNormalMove(0,CaptureWorldRegistry(),terrain,24,24,18,5,counter);
            for(int i=0;i<worldMembership.GetNormalTaskCommandCount(0);i++)outgoing.Add(ShipWorldStep.Command.Task(counter,worldMembership.GetNormalTaskCommand(0,i)));
            Debug.Log("[ShipWorldStep] conditions: registration="+args[option+1]+"; mail_initial=2; quantum=40; members="+(busyReplay?"11,12,13":"11")+"; notify_before="+notifyBefore+"; source_branch=controlled; full_game=False");
            order.LogReadiness("[ShipFleetMotion]");
            yield return new WaitForEndOfFrame();LogStage("initial");yield return new WaitForSecondsRealtime(1.25f);
            int phase=0,accumulated=0;bool notified=false;double start=Time.realtimeSinceStartupAsDouble;
            int[] holds=busyReplay?new int[]{1,3,10,11,25,50,80,100,125,150,200,201,202,212}:new int[]{1,3,10,25,50,80,100,125,150,200,201,202,212};
            while(counter<212)
            {
                //Exact40*n captured-time inputs from the source record replay;
                //host rendering jitter is outside this diagnostic simulation input.
                int captured=restoreDirectory!=null?unchecked(((int)counter+1)*40):
                    accumulated+(int)((Time.realtimeSinceStartupAsDouble-start)*1000.0);
                if(counter==notifyBefore-1&&!notified)
                {worldMembership.AddToGroup(11,0,counter,CaptureWorldRegistry());worldMembership.NotifyMemberAdded(0,11,counter);notified=true;}
                if(!world.TryAdvance(captured,ref phase,ref counter,terrain,outgoing)){yield return null;continue;}
                ApplyWorldPublications(world);
                for(int i=0;i<world.ReceivedCount;i++)Debug.Log("[ShipWorldStep] received: at="+counter+"; packet="+WorldPacket(world.GetReceived(i)));
                for(int i=0;i<world.EmittedCount;i++)Debug.Log("[ShipWorldStep] emitted: at="+counter+"; packet="+WorldPacket(world.GetEmitted(i)));
                if(Array.IndexOf(holds,(int)counter)>=0)
                {
                    yield return new WaitForEndOfFrame();LogStage("tick-"+counter);
                    Debug.Log("[ShipWorldStep] checkpoint: counter="+counter+"; age="+worldMembership.GetGroupWorkAge(0)+"; consumed="+worldMembership.ConsumedCommandCount+"; queued="+outgoing.Count+"; prep="+world.PreparationCounter);
                    yield return new WaitForSecondsRealtime(1.25f);
                    if(restoreDirectory!=null&&(counter==1||counter==10))
                    {
                        RestoreWorldCohort(world,System.IO.Path.Combine(restoreDirectory,counter.ToString(System.Globalization.CultureInfo.InvariantCulture)),phase,outgoing);
                        yield return new WaitForEndOfFrame();LogStage("restore-"+counter);yield return new WaitForSecondsRealtime(1.25f);
                    }
                    accumulated=captured;start=Time.realtimeSinceStartupAsDouble;
                }
                else yield return null;
            }
            Debug.Log("[ShipWorldStep] complete: counter=212; full_game=False");
        }
        public void Dispose()
        {
            if(disposed)return;disposed=true;
            foreach(var pose in poses)pose?.Dispose();
            Debug.Log(Prefix+"cleanup: pose_owners=3; visual_refs_cleared=True");
        }
    }
}
