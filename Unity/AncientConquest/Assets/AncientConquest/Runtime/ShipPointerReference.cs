using System;
using System.Collections.Generic;
using AncientConquest.Simulation;
using AncientConquest.World;
using UnityEngine;
using UnityEngine.InputSystem;

namespace AncientConquest.Presentation
{
    /// <summary>Explicit single-source0b mouse diagnostic, separate from the unfinished mission.</summary>
    internal sealed class ShipPointerReference : MonoBehaviour
    {
        private const string Prefix = "[ShipPointerReference]";
        private ShipMoveOrder movement;
        private ShipPointerCommands commands;
        private ShipPendingSelection fleet;
        private ShipFleetVisualReference fleetVisuals;
        private ShipFleetMotionReference fleetWorld;
        private ShipFleetMembership membership;
        private ShipWorldStep inputWorld;
        private short[] inputTerrain;
        private short[] inputWaveWords;
        //4ee507:BaseSystem+20 is independent of physical Shift controls and the world clock.
        private SourceRouteKeyVisibility sourceRouteKeys;
        private bool sourceRouteKeyHeld => sourceRouteKeys.Stored != 0;
        private readonly List<ShipWorldStep.Command> outgoing=new List<ShipWorldStep.Command>();
        private readonly List<object> localOwners=new List<object>();
        private bool fleetMoveDispatched;
        private bool Selected => fleet == null ? commands.Current.Selected : fleet.Selected;
        private bool PendingSelection => fleet == null ? commands.Current.PendingSelection : fleet.Pending;
        private ShipPointerHover hover;
        private ShipSelectionProgression selection;
        private PointerCursorProgression cursor;
        private SourceShipPoseReference poses;
        private SourceCohortOrderReference order;
        private ShipPickingReference masks;
        private ShipPointerVisualReference visuals;
        private MissionOccupancyGrid grid;
        private int originX, originY, pointerX, pointerY, eventIndex, previousTickTime, previousCursorLifeTime;
        private readonly ShipBoxGesture box = new ShipBoxGesture();
        private ShipBoxVisualReference boxVisual;
        private object controlledOwner;
        private IDictionary<object, ShipHoverActor> metadata;
        private bool initialized, disposed, inside;
        private bool previousCursorVisible;
        private CursorLockMode previousCursorLock;
        private uint counter;
        private double milliseconds, simulationMilliseconds, previousRealtime;
        internal bool Held { get; set; }
        internal uint Counter => counter;
        internal uint VisualMilliseconds => unchecked((uint)milliseconds);
        internal bool CanRequestMove => movement.CanRequestMove;

        internal void Initialize(MissionOccupancyGrid grid, object owner, MissionShipSeed seed,
            Dictionary<int, SpriteRenderer> renderers, SourceCohortOrderReference order,
            ShipPickingReference.Actor[] actors, IDictionary<object, ShipHoverActor> actorMetadata,
            Transform worldParent, Material material, int originWorldX, int originWorldY,ShipFleetMotionReference liveFleet=null)
        {
            if (initialized || isActiveAndEnabled) throw new InvalidOperationException("Initialize the inactive pointer host once.");
            if(Array.IndexOf(Environment.GetCommandLineArgs(),"--ship-pointer-fleet-world")>=0&&
                (liveFleet==null||Array.IndexOf(Environment.GetCommandLineArgs(),"--ship-pointer-fleet-selection")<0))
                throw new ArgumentException("The input world requires fleet movement and selection.");
            this.grid = grid; this.order = order; controlledOwner = owner; metadata = actorMetadata; originX = originWorldX; originY = originWorldY;
            fleetWorld=liveFleet;movement = fleetWorld==null?new ShipMoveOrder(grid, owner, seed, 0):fleetWorld.FindMotion(owner);
            commands = new ShipPointerCommands(owner);
            selection = new ShipSelectionProgression(); cursor = new PointerCursorProgression();
            masks = new ShipPickingReference(grid, actors, false);
            var localActors = new List<ShipPickingReference.Actor>();
            if (Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-pointer-fleet-selection") >= 0)
            {
                var owners = new List<object>();
                foreach (var actor in actors)
                    if (actorMetadata[actor.Owner].OwnerSide == 1 && actorMetadata[actor.Owner].OwnerPlayer == 1)
                    { localActors.Add(actor); owners.Add(actor.Owner); }
                localActors.Sort((a,b)=>a.Id.CompareTo(b.Id));owners.Clear();
                foreach(var actor in localActors)owners.Add(actor.Owner);
                localOwners.AddRange(owners);
                if(fleetWorld!=null)
                {
                    var ids=new uint[localActors.Count];for(int i=0;i<ids.Length;i++)ids[i]=localActors[i].Id;
                    membership=new ShipFleetMembership(ids);
                    fleet=new ShipPendingSelection(owners.ToArray(),o=>membership.GetUiGroup(localOwners.IndexOf(o)),ReadGroupMembers);
                    string[] args=Environment.GetCommandLineArgs();
                    if(Array.IndexOf(args,"--ship-pointer-fleet-world")>=0)
                    {
                        //542200's complete mission order is not established. Require an explicit controlled vector.
                        int option=Array.IndexOf(args,"--ship-fleet-world-registration");
                        if(option<0||option+1>=args.Length)throw new ArgumentException("The input world requires explicit --ship-fleet-world-registration.");
                        string[] names=args[option+1].Split(',');var registration=new int[names.Length];
                        for(int i=0;i<names.Length;i++)registration[i]=names[i]=="fleet"?-1:int.Parse(names[i])-11;
                        int mailOption=Array.IndexOf(args,"--ship-pointer-fleet-world-mail");byte mailGate=2;
                        if(mailOption>=0&&(mailOption+1>=args.Length||!byte.TryParse(args[mailOption+1],out mailGate)||mailGate>2))
                            throw new ArgumentException("The controlled mail gate must be0,1 or2.");
                        inputWorld=fleetWorld.BindInputWorld(membership,registration,mailGate);
                        //4cebc7 reads wave[-1]. Explicit controlled per-actor words,not a game default.
                        int waveOption=Array.IndexOf(args,"--ship-fleet-wave-prefixes");
                        if(waveOption>=0)
                        {
                            if(waveOption+1>=args.Length)throw new ArgumentException("Missing explicit signed wave prefixes.");
                            string[] values=args[waveOption+1].Split(',');
                            if(values.Length!=localOwners.Count)throw new ArgumentException("One signed wave prefix per actor registry entry is required.");
                            inputWaveWords=new short[values.Length];
                            for(int i=0;i<values.Length;i++)if(!short.TryParse(values[i],out inputWaveWords[i]))
                                throw new ArgumentException("Wave prefixes must be signed16-bit words.");
                        }
                        inputTerrain=new short[576];
                        for(int y=0;y<24;y++)for(int x=0;x<24;x++)inputTerrain[y*24+x]=grid.IsTerrainPassable(x,y,0)?(short)0:(short)-1;
                        Debug.Log("[ShipFleetControl] world-ready: registration="+args[option+1]+"; mail_initial="+mailGate+"; quantum=40; full_life=False");
                    }
                }
                else fleet = new ShipPendingSelection(owners.ToArray());
            }
            hover = new ShipPointerHover(grid, owner, ReadPose,
                o => actorMetadata.TryGetValue(o, out ShipHoverActor actor) ? actor :
                    throw new NotSupportedException("Unknown ship hover metadata."),
                selectedCount: fleet == null ? null : new Func<int>(() => fleet.Count),
                selectedAt: fleet == null ? null : new Func<int,object>(fleet.GetMember));
            if(fleetWorld==null)poses = new SourceShipPoseReference(renderers);
            visuals = new ShipPointerVisualReference(worldParent, material, originX, originY);
            boxVisual = new ShipBoxVisualReference(worldParent, material, originX, originY);
            if (fleet != null)
                fleetVisuals = new ShipFleetVisualReference(worldParent, material, localActors.ToArray(),
                    order.CopyRegisteredDepths(), ReadPose);
            var m = movement.Current.Motion;
            if(fleetWorld==null)ApplyBody(m.DrawnFrame, m.PublishedWorldX, m.PublishedWorldY, Math.Max(10000, 19944 - m.PublishedWorldY));
            gameObject.AddComponent<WorldPointerInput>().Configure(Receive, Cancel,
                inputWaveWords==null?null:new Action<bool>(ReceiveRouteKeyVisibility));
            previousCursorVisible = Cursor.visible; previousCursorLock = Cursor.lockState;
            Cursor.lockState = CursorLockMode.None; Cursor.visible = false;
            previousRealtime = Time.realtimeSinceStartupAsDouble;
            initialized = true;
            Debug.Log(Prefix + " ready: canvas=1920,1080; origin=" + originX + "," + originY +
                "; scale=2; input=InputSystem.onEvent; actor=0000000b; actors=8; fog=False; other_object_slots=empty; " +
                "membership=explicit-ui-and-simulation; planner_membership=bounded-different-group; audio=False; full_game=False");
            order.LogReadiness(Prefix);
            if (fleet != null) Debug.Log("[ShipFleetSelection] ready: local_actors=3; pending_only="+(fleetWorld==null)+"; movement="+(fleetWorld!=null)+"; native_slot_lifecycle=True; source_art=True; full_game=False");
            if(fleetWorld!=null)Debug.Log("[ShipFleetControl] ready: first_normal_move=True; ctrl_recall=True; group_task_scheduler="+(inputWorld!=null)+"; source_art=True; full_game=False");
        }
        //4eff00 stores BaseSystem+20 then forwardsC45D;4a2050 shows/hides CURRENT group points.
        //This is presentation state only;no clock,task,mail,membership or occupancy mutation.
        private void ReceiveRouteKeyVisibility(bool visible)
        {
            sourceRouteKeys.Receive(visible?1u:0u);
            ApplyRouteKeyVisibility();
        }
        //4ee900/540560/4eff00:explicit controlled source context;not a guessed Unity focus hook.
        internal void ReceiveSourceRouteContext(uint applicationGate,uint registrationState)
        {
            if(!Held||inputWaveWords==null)
                throw new InvalidOperationException("Source context replay requires a held explicit fleet-input profile.");
            uint before=sourceRouteKeys.Stored;
            bool emitted=sourceRouteKeys.TryContextReset(applicationGate,registrationState,out uint visibility);
            if(emitted)ApplyRouteKeyVisibility();
            Debug.Log("[ShipFleetWaypoint] context: counter="+counter+"; gate="+applicationGate+
                "; registration="+registrationState+"; before="+before+"; stored="+sourceRouteKeys.Stored+"; emitted="+emitted);
        }
        //49ab30 C45D ->4a2050:only current-group marker graphics observe the forwarded value.
        private void ApplyRouteKeyVisibility()
        {
            if(fleet!=null&&!fleet.Pending&&fleet.CurrentGroup>=0)
            {
                if(sourceRouteKeyHeld)fleetVisuals.SyncQueuedMarkers(membership,fleet.CurrentGroup,0);
                else fleetVisuals.HideQueuedMarkers(fleet.CurrentGroup);
                ApplyVisuals();
            }
            Debug.Log("[ShipFleetWaypoint] key: counter="+counter+"; visible="+sourceRouteKeyHeld+
                "; group="+(fleet==null?-1:fleet.CurrentGroup)+"; pending="+(fleet!=null&&fleet.Pending));
        }
        private object[] ReadGroupMembers(short group)
        {var result=new object[membership.GetGroupMemberCount(group)];for(int i=0;i<result.Length;i++)result[i]=localOwners[membership.GetGroupMemberRegistryIndex(group,i)];return result;}
        private ShipPointerPose ReadPose(object owner)
        {var body=fleetWorld?.FindMotion(owner);return body==null?masks.ReadPose(owner,movement.Current):masks.ReadLivePose(owner,body.Current);}

        internal void AdvanceVisualMilliseconds(uint delta)
        {
            if (!Held) throw new InvalidOperationException("The replay clock can advance only at a held checkpoint.");
            milliseconds += delta;
            // Clock instrumentation does not dispatch an input, select an actor or issue an order.
        }

        private void Update()
        {
            if (!initialized || disposed) return;
            try
            {
                double now = Time.realtimeSinceStartupAsDouble;
                double elapsed = now - previousRealtime; previousRealtime = now;
                if (Held) return;
                milliseconds += Math.Max(0, elapsed * 1000.0);
                simulationMilliseconds += Math.Max(0, elapsed * 1000.0);
                int captured = checked((int)simulationMilliseconds);
                bool advanced;
                if(inputWorld!=null)
                    advanced=fleetWorld.AdvanceInputWorld(inputWorld,captured,ref previousTickTime,ref counter,inputTerrain,outgoing,
                        (o,c,x,y)=>fleetVisuals.AdvanceOwner(o,c,x,y),inputWaveWords);
                else
                {
                    var step=SingleStepClock.Begin(captured,previousTickTime,counter,40);advanced=step.StepRequested;
                    if(advanced)
                    {
                        counter=step.Counter;
                        if(fleetWorld==null){movement.Tick(counter,1);ApplyPublications();}
                        else fleetWorld.TickAll(counter,(o,c,x,y)=>fleetVisuals.AdvanceOwner(o,c,x,y));
                        previousTickTime=SingleStepClock.Complete(captured,previousTickTime,40);
                    }
                }
                if (advanced)
                {
                    var s = selection.Current;
                    var m = movement.Current.Motion;
                    if (fleet != null) fleetVisuals.Advance(counter);
                    else if (s.StoredFrame < 10 || s.SelectionState == 2)
                        AdvanceSelection(m.PublishedWorldX, m.PublishedWorldY);
                    if(inputWaveWords!=null)fleetVisuals.SyncQueuedMarkers(membership);
                    LogMotion();
                }
                //The source cursor belongs to BaseSystem, outside PlaySystem's
                //world-step gate. Prepared speed5 normally paces app Life at40ms.
                //This independent bounded reference clock prevents render-rate
                //Life calls; it does not port RunApp's urgent queue/Sleep policy.
                var cursorLife = SingleStepClock.Begin(captured, previousCursorLifeTime, 0, 40);
                if (cursorLife.StepRequested)
                {
                    box.Life(VisualMilliseconds);
                    hover.Refresh(Selected);
                    //517540 skips its periodic draw if SetGCType already drew.
                    if (!SyncCursor(false)) cursor.Draw(VisualMilliseconds);
                    previousCursorLifeTime = SingleStepClock.Complete(captured, previousCursorLifeTime, 40);
                }
                ApplyVisuals();
            }
            catch (Exception exception) { Fail(exception); }
        }

        private void Receive(int message, int rawX, int rawY)
        {
            if (!initialized || disposed) return;
            int nextPointerX = FloorHalf(rawX), nextPointerY = FloorHalf(rawY);
            bool logicalChanged = nextPointerX != pointerX || nextPointerY != pointerY;
            pointerX = nextPointerX; pointerY = nextPointerY;
            inside = rawX >= 0 && rawX < 1920 && rawY >= 0 && rawY < 1080;
            int worldX = originX + pointerX, worldY = originY + pointerY;
            if (!inside || worldX < 0 || worldX >= 1536 || worldY < 0 || worldY >= 1536)
            {
                inside = false;
                //Leaving the viewport must not turn an active box gesture into
                //a SEA click when the held pointer returns before release.
                if (message == WorldPointerInput.LeftUp) box.Cancel();
                if (message == WorldPointerInput.Move && logicalChanged)
                {
                    hover.InvalidateMap();
                    // Outside Map receives no SetMapXY/GCGameState. The global
                    // cursor still draws at the new screen position; Life resets
                    // its kind later. Buttons outside must not draw again.
                    cursor.Draw(VisualMilliseconds, pointerX, pointerY);
                }
                ApplyVisuals();
                LogEvent(message, rawX, rawY, "outside"); return;
            }
            if (message == WorldPointerInput.Move)
            {
                // One source pixel occupies2x2 display pixels. The source screen gate
                // therefore observes logical-pixel changes, not HD subpixel events.
                if (logicalChanged)
                {
                    hover.Move(pointerX, pointerY, worldX, worldY, worldX / 64, worldY / 64, Selected);
                    box.Move(worldX, worldY, VisualMilliseconds);
                    fleetVisuals?.SetBox(box.Active);
                    SyncCursor(true);
                }
            }
            else if (message == WorldPointerInput.LeftDown)
            { box.Begin(worldX, worldY); }
            else if (message == WorldPointerInput.LeftUp || message == WorldPointerInput.RightUp)
            {
                if (box.Active)
                {
                    // Right-release cannot dispatch a box or a SEA command while
                    // the source rectangle exists. Only LeftUp completes it.
                    if (message == WorldPointerInput.LeftUp) CompleteBox(worldX, worldY);
                    ApplyVisuals(); LogEvent(message, rawX, rawY, "box-handled"); return;
                }
                var h = hover.Current;
                if (fleet != null)
                {
                    ProcessFleetRelease(h, message);
                    if (message == WorldPointerInput.LeftUp) box.Cancel();
                    ApplyVisuals(); LogEvent(message, rawX, rawY, "fleet-handled"); return;
                }
                uint flags = 0;
                if (Keyboard.current != null)
                {
                    if (Keyboard.current.shiftKey.isPressed) flags |= 4;
                    if (Keyboard.current.ctrlKey.isPressed) flags |= 8;
                }
                var result = commands.ProcessRelease(new ShipPointerCommandInput(h.HoveredOwner, h.CellX, h.CellY,
                    h.CursorType, h.ActionMask, h.ActionBit, h.Blocked, h.HasMapPosition), message, flags, movement.CanRequestMove);
                if (result.SelectionClearRequested) selection.Deselect();
                if (result.SelectionRequested)
                {
                    var m = movement.Current.Motion;
                    selection.Select(m.PublishedWorldX, m.PublishedWorldY);
                }
                for (int i = 0; i < commands.LastCommandCount; i++)
                {
                    ShipPointerCommand packet = commands.GetLastCommand(i);
                    Debug.Log(Prefix + " packet: event=" + eventIndex + "; index=" + i + "; action=" + packet.Action +
                        "; payload=" + BitConverter.ToString(packet.CapturePayload()).Replace("-", "").ToLowerInvariant());
                    if (packet.Action == 0x29) commands.ConsumeMembership41(packet.Group);
                    else if (packet.Action == 0x14)
                    {
                        if (commands.Current.SimulationGroup < 0 || commands.Current.SimulationGroup != commands.Current.UiGroup)
                            throw new InvalidOperationException("Source membership must be consumed before its move.");
                        if (!movement.RequestCellMove(packet.X, packet.Y, packet.ByteArgument))
                            throw new InvalidOperationException("An idle source mouse move was refused.");
                        ApplyPublications();
                    }
                    else throw new InvalidOperationException("Unsupported source actor packet.");
                }
                if (result.ConfirmRequested) cursor.Confirm(h.WorldX, h.WorldY);
                hover.ApplyReleaseCursor(checked((ushort)result.CursorType), result.ActionMask, result.ActionBit, result.Blocked);
                SyncCursor(false);
                if (message == WorldPointerInput.LeftUp) box.Cancel();
            }
            ApplyVisuals();
            LogEvent(message, rawX, rawY, "handled");
        }

        private string OwnerIds(object[] owners)
        {
            string result="";
            foreach(object owner in owners) result+=(result.Length==0?"":",")+masks.ReadActor(owner).Id.ToString("x8");
            return result.Length==0?"none":result;
        }
        private void ApplyFleetEvents()
        {
            for(int i=0;i<fleet.EventCount;i++)
            {
                var change=fleet.GetEvent(i);
                //49ab30/49e850->4a2050(0):clear graphics BEFORE actor deselection.
                if(!change.Selected&&membership!=null)
                {
                    short group=membership.GetUiGroup(localOwners.IndexOf(change.Owner));
                    if(group>=0)fleetVisuals.HideQueuedMarkers(group);
                }
                fleetVisuals.ApplyEvent(change);
                Debug.Log("[ShipFleetSelection] selection: id="+masks.ReadActor(change.Owner).Id.ToString("x8")+"; selected="+change.Selected);
            }
        }
        private void ProcessFleetRelease(ShipPointerHover.Snapshot h,int message)
        {
            if(fleetWorld!=null&&message==WorldPointerInput.LeftUp&&h.CursorType==7)
            {DispatchFirstFleetMove(h);return;}
            if(fleetWorld!=null&&message==WorldPointerInput.LeftUp&&!fleet.Pending&&fleet.CurrentGroup>=0&&(Modifiers()&4u)!=0)
            {Debug.Log("[ShipFleetControl] guard: reason=committed-group-edit-needs-task-events");return;}
            if((message==WorldPointerInput.LeftUp&&h.CursorType==7)||
               (message==WorldPointerInput.RightUp&&h.HoveredOwner!=null&&!h.Blocked&&h.CursorType==5&&h.ActionMask!=0))
            {
                Debug.Log("[ShipFleetSelection] guard: reason=command-layer-pending; selected="+Selected);
                return;
            }
            uint flags=Modifiers();
            Debug.Log("[ShipFleetSelection] release: message="+message+"; flags="+flags+"; kind="+h.CursorType+"; mask="+h.ActionMask+"; bit="+h.ActionBit+"; blocked="+h.Blocked);
            var result=fleet.ProcessRelease(new ShipPointerCommandInput(h.HoveredOwner,h.CellX,h.CellY,h.CursorType,
                h.ActionMask,h.ActionBit,h.Blocked,h.HasMapPosition),message,flags);
            ApplyFleetEvents();
            hover.ApplyReleaseCursor((ushort)result.CursorType,result.ActionMask,result.ActionBit,result.Blocked);SyncCursor(false);
        }
        private void DispatchFirstFleetMove(ShipPointerHover.Snapshot h)
        {
            if(inputWorld!=null&&fleetMoveDispatched&&!fleet.Pending&&fleet.CurrentGroup>=0)
            {DispatchExistingFleetMove(h);return;}
            bool queued=(Modifiers()&4u)!=0;
            if(fleetMoveDispatched||!fleet.Pending||!Selected||h.Blocked||!h.HasMapPosition||
                (queued&&(inputWorld==null||inputWaveWords==null)))
            {Debug.Log("[ShipFleetControl] guard: reason=first-normal-idle-command-only");return;}
            var ids=new uint[fleet.Count];var origins=new SourceFleetFormation.Cell[fleet.Count];
            for(int i=0;i<ids.Length;i++)
            {
                object owner=fleet.GetMember(i);var body=fleetWorld.FindMotion(owner);
                if(body==null||!body.CanRequestMove){Debug.Log("[ShipFleetControl] guard: reason=busy-recipient");return;}
                ids[i]=body.InstanceId;var m=body.Current.Motion;origins[i]=new SourceFleetFormation.Cell(m.CellX,m.CellY);
            }
            var terrain=new short[576];for(int y=0;y<24;y++)for(int x=0;x<24;x++)terrain[y*24+x]=grid.IsTerrainPassable(x,y,0)?(short)0:(short)-1;
            ShipFleetMoveCommand[] moves=Array.Empty<ShipFleetMoveCommand>();
            try{if(!queued)moves=ShipFleetMoveCommands.Build(terrain,24,24,ids,origins,h.CellX,h.CellY);}
            catch(NotSupportedException){Debug.Log("[ShipFleetControl] guard: reason=source-formation-approach-unresolved");return;}
            short group=checked((short)membership.CommitPending(ids));fleet.MarkCommitted(group);
            if(inputWorld!=null)
            {
                //49ca60/4ccc30 enqueue41 then task100/1's20. Neither5e nor the inbox changes here.
                for(int i=membership.ConsumedCommandCount;i<membership.CommandCount;i++)
                {
                    var packet=membership.GetCommand(i);outgoing.Add(ShipWorldStep.Command.Membership(counter,packet));
                    Debug.Log("[ShipFleetControl] packet: id="+packet.InstanceId+"; action=41; payload="+BitConverter.ToString(packet.CapturePayload()).Replace("-","").ToLowerInvariant());
                }
                //49e230->49ca60;Shift uses4cf2c0,ordinary movement4ccc30.
                if(queued)membership.RequestQueuedMove(group,fleetWorld.CaptureWorldRegistry(),24,24,h.CellX,h.CellY,counter);
                else membership.RequestNormalMove(group,fleetWorld.CaptureWorldRegistry(),inputTerrain,24,24,h.CellX,h.CellY,counter);
                for(int i=0;i<membership.GetTaskCommandCount(group);i++)
                {
                    var packet=membership.GetTaskCommand(group,i);outgoing.Add(ShipWorldStep.Command.Task(counter,packet));
                    Debug.Log("[ShipFleetControl] packet: id="+packet.InstanceId+"; action="+packet.Action+"; payload="+BitConverter.ToString(packet.CapturePayload()).Replace("-","").ToLowerInvariant());
                }
                if(queued)fleetVisuals.SyncQueuedMarkers(membership,group,0);
                fleetMoveDispatched=true;cursor.Confirm(h.WorldX,h.WorldY);SyncCursor(false);return;
            }
            while(membership.ConsumedCommandCount<membership.CommandCount)
            {
                var packet=membership.GetCommand(membership.ConsumedCommandCount);membership.ConsumeNext();fleetWorld.ReceiveMembership(packet.InstanceId,packet.Group);
                Debug.Log("[ShipFleetControl] packet: id="+packet.InstanceId+"; action=41; payload="+BitConverter.ToString(packet.CapturePayload()).Replace("-","").ToLowerInvariant());
            }
            foreach(var packet in moves)
            {
                object recipient=null;foreach(object owner in localOwners)if(masks.ReadActor(owner).Id==packet.InstanceId){recipient=owner;break;}
                fleetWorld.FindMotion(recipient).ReceiveCellMove(packet.InstanceId,packet.X,packet.Y,packet.ByteArgument);
                Debug.Log("[ShipFleetControl] packet: id="+packet.InstanceId+"; action=20; payload="+BitConverter.ToString(packet.CapturePayload()).Replace("-","").ToLowerInvariant());
            }
            fleetMoveDispatched=true;cursor.Confirm(h.WorldX,h.WorldY);SyncCursor(false);
        }
        //49e230 committed-group20 ->49de70 ->4ccc30 reuses100/1. No49ca60,
        //41,300,age reset or direct ship receipt. Pending20 is delivered by522850.
        private void DispatchExistingFleetMove(ShipPointerHover.Snapshot h)
        {
            short group=fleet.CurrentGroup;
            bool queued=(Modifiers()&4u)!=0;
            if(!Selected||h.Blocked||!h.HasMapPosition||
                (inputWaveWords==null&&(queued||!membership.HasNormalTask(group))))
            {Debug.Log("[ShipFleetControl] guard: reason=normal-committed-replacement-only");return;}
            for(int i=0;i<membership.GetGroupMemberCount(group);i++)
            {
                int index=membership.GetGroupMemberRegistryIndex(group,i);var body=fleetWorld.FindMotion(localOwners[index]);
                //4cf2c0 accepts route appends before the initial41 mail is received.
                //Keep the bounded normal-replacement receiver check out of the Shift branch.
                if(body==null||(!queued&&(!body.HasNormalCellMoveReceiver||membership.GetSimulationGroup(index)!=group)))
                {Debug.Log("[ShipFleetControl] guard: reason=replacement-cohort-not-ready");return;}
            }
            int priorPoints=membership.GetTaskSubtype(group)==2?membership.GetQueuedPointCount(group):0;
            //49e230/49de70:Shift selects4ce6c0/1002;ordinary20 selects4ccc30/1001.
            //No eager522850 delivery,no group Work outside542200's registry position.
            try
            {
                if(queued)membership.RequestQueuedMove(group,fleetWorld.CaptureWorldRegistry(),24,24,h.CellX,h.CellY,counter);
                else membership.RequestNormalMove(group,fleetWorld.CaptureWorldRegistry(),inputTerrain,24,24,h.CellX,h.CellY,counter);
            }
            catch(NotSupportedException){Debug.Log("[ShipFleetControl] guard: reason=source-formation-approach-unresolved");return;}
            for(int i=0;i<membership.GetTaskCommandCount(group);i++)
            {
                var packet=membership.GetTaskCommand(group,i);outgoing.Add(ShipWorldStep.Command.Task(counter,packet));
                Debug.Log("[ShipFleetControl] packet: id="+packet.InstanceId+"; action="+packet.Action+"; payload="+BitConverter.ToString(packet.CapturePayload()).Replace("-","").ToLowerInvariant());
            }
            if(inputWaveWords!=null)
            {
                fleetVisuals.SyncQueuedMarkers(membership,queued?group:-1,priorPoints);
                Debug.Log("[ShipFleetControl] task-input: counter="+counter+"; group="+group+"; goal="+h.CellX+","+h.CellY+
                    "; subtype="+membership.GetTaskSubtype(group)+"; points="+membership.GetQueuedPointCount(group)+"; queued="+outgoing.Count);
            }
            else Debug.Log("[ShipFleetControl] replacement: counter="+counter+"; group="+group+"; goal="+h.CellX+","+h.CellY+
                "; requested="+membership.GetNormalTaskRequestedAt(group)+"; age="+membership.GetGroupWorkAge(group)+"; queued="+outgoing.Count);
            cursor.Confirm(h.WorldX,h.WorldY);SyncCursor(false);
        }
        private uint Modifiers()
        {
            uint flags = 0;
            if (Keyboard.current != null)
            {
                if (Keyboard.current.shiftKey.isPressed) flags |= 4;
                if (Keyboard.current.ctrlKey.isPressed) flags |= 8;
            }
            return flags;
        }
        private void CompleteBox(int releaseX, int releaseY)
        {
            int[] bounds = box.CellBounds(releaseX, releaseY);
            object[] found = ShipBoxSelection.Collect(grid, bounds[0], bounds[1], bounds[2], bounds[3],
                o => metadata[o], o => fleetWorld!=null?(fleetWorld.FindMotion(o)?.Current.Motion.ReservedCellIndex??-1):ReferenceEquals(o, controlledOwner) ? movement.Current.Motion.ReservedCellIndex : -1);
            if (fleet != null)
            {
                // Source removes the callback rectangle before creating selectors.
                box.Cancel(); fleetVisuals.SetBox(false);
                var h = hover.Current;
                uint flags=Modifiers();
                if(fleetWorld!=null&&!fleet.Pending&&fleet.CurrentGroup>=0&&(flags&4u)!=0)
                {Debug.Log("[ShipFleetControl] guard: reason=committed-group-box-needs-task-events");return;}
                Debug.Log("[ShipFleetSelection] box: bounds="+string.Join(",",bounds)+"; candidates="+OwnerIds(found)+"; flags="+flags+"; kind="+h.CursorType);
                fleet.ProcessBox(new ShipPointerCommandInput(h.HoveredOwner,h.CellX,h.CellY,h.CursorType,
                    h.ActionMask,h.ActionBit,h.Blocked,h.HasMapPosition),bounds[2],bounds[3],found,flags);
                ApplyFleetEvents();
                return;
            }
            string outcome;
            if (found.Length > 1 || (found.Length == 1 && !ReferenceEquals(found[0], controlledOwner)))
                outcome = "unsupported-fleet-set";
            else
            {
                var h = hover.Current;
                var result = commands.ProcessBoxSelection(new ShipPointerCommandInput(h.HoveredOwner, h.CellX, h.CellY,
                    h.CursorType, h.ActionMask, h.ActionBit, h.Blocked, h.HasMapPosition),
                    bounds[2], bounds[3], found.Length == 1, Modifiers());
                if (result.SelectionClearRequested) selection.Deselect();
                if (result.SelectionRequested)
                {
                    var m = movement.Current.Motion;
                    selection.Select(m.PublishedWorldX, m.PublishedWorldY);
                }
                outcome = result.SelectionRequested ? "selected-source0b" : "preserved";
                if (commands.LastCommandCount != 0) throw new InvalidOperationException("A box selection issued an actor command.");
            }
            string ids = "";
            foreach (object owner in found) ids += (ids.Length == 0 ? "" : ",") + masks.ReadActor(owner).Id.ToString("x8");
            Debug.Log("[ShipBoxReference] release: bounds=" + string.Join(",", bounds) +
                "; members=" + (ids.Length == 0 ? "none" : ids) + "; outcome=" + outcome);
            box.Cancel();
        }
        private void ApplyVisuals()
        {
            if (fleet != null)
            {
                fleetVisuals.SetBox(box.Active); fleetVisuals.Apply();
                boxVisual.SetSortingOrder(fleetVisuals.BoxOrder);
                visuals.SetConfirmationOrder(fleetVisuals.OverlayEndOrder);
            }
            else visuals.SetBoxActive(box.Active);
            visuals.Apply(selection.Current, cursor.Current); boxVisual.Apply(box);
        }
        private static int FloorHalf(int value) => (int)Math.Floor(value / 2.0);
        private bool SyncCursor(bool moved)
        {
            var h = hover.Current;
            var previous = cursor.Current;
            bool changed = cursor.SetCursor(h.CursorType, false, VisualMilliseconds,
                moved ? previous.ScreenX : pointerX, moved ? previous.ScreenY : pointerY);
            //518d90 always draws after Map forwarding on an actual source-pixel
            //Move, even when SetGCType already drew at the OLD cursor position.
            if (moved) cursor.Draw(VisualMilliseconds, pointerX, pointerY);
            return changed;
        }
        private void AdvanceSelection(int x, int y)
        {
            selection.Advance(counter, 1, x, y);
            if (selection.LastStepDeletesSelector) commands.CompleteSelectionVisualRemoval();
        }
        private void ApplyPublications()
        {
            for (int i = 0; i < movement.LastStepPublicationCount; i++)
            {
                var p = movement.GetLastStepPublication(i);
                if (fleet != null) fleetVisuals.AdvanceOwner(controlledOwner,counter,p.WorldPixelX,p.WorldPixelY);
                else AdvanceSelection(p.WorldPixelX, p.WorldPixelY);
                ApplyBody(p.Frame, p.WorldPixelX, p.WorldPixelY, p.Depth);
            }
            var m = movement.Current.Motion;
            if (poses.DrawnFrame != m.DrawnFrame || poses.WorldPixelX != m.PublishedWorldX || poses.WorldPixelY != m.PublishedWorldY)
                throw new InvalidOperationException("The mouse-driven body differs from its last source publication.");
        }
        private void ApplyBody(int frame, int x, int y, int depth)
        { order.UpdateParent(0xbu, depth); poses.Apply(frame, x, y); }
        private void Cancel()
        {
            if (!initialized || disposed) return;
            inside = false; box.Cancel();
            hover.InvalidateMap(); hover.Refresh(Selected);
            SyncCursor(false); ApplyVisuals();
            Debug.Log(Prefix + " cancel: counter=" + counter + "; selected=" + Selected + "; synthesized_up=False");
        }
        private void LogEvent(int message, int rawX, int rawY, string outcome)
        {
            var h = hover.Current; var c = commands.Current;
            string picked = h.HoveredOwner == null ? "none" : masks.ReadActor(h.HoveredOwner).Id.ToString("x8");
            Debug.Log(Prefix + " event: index=" + eventIndex++ + "; counter=" + counter + "; visual_ms=" + VisualMilliseconds +
                "; message=" + message + "; raw=" + rawX + "," + rawY + "; logical=" + pointerX + "," + pointerY +
                "; world=" + h.WorldX + "," + h.WorldY + "; cell=" + h.CellX + "," + h.CellY +
                "; has_map=" + h.HasMapPosition + "; picked=" + picked + "; cursor=" + h.CursorType +
                "; selected=" + Selected + "; pending=" + PendingSelection + "; ui_group=" + c.UiGroup +
                "; simulation_group=" + c.SimulationGroup + "; rng=" + movement.Current.RandomState + "; outcome=" + outcome);
        }
        private void LogMotion()
        {
            var s = movement.Current; var m = s.Motion;
            Debug.Log(Prefix + " motion: counter=" + counter + "; cell=" + m.CellX + "," + m.CellY +
                "; world=" + m.WorldPixelX + "," + m.WorldPixelY + "; published=" + m.PublishedWorldX + "," + m.PublishedWorldY +
                "; frame=" + m.StoredFrame + "; drawn=" + m.DrawnFrame + "; heading=" + m.Heading +
                "; state=" + m.State + "; pending_flags=" + s.PendingFlags + "; active_flags=" + s.ActiveFlags +
                "; reserved=" + m.ReservedCellIndex + "; rng=" + s.RandomState + "; can_request=" + movement.CanRequestMove);
        }
        internal void LogCheckpoint(string stage)
        {
            var c = commands.Current; var s = selection.Current; var p = cursor.Current;
            Debug.Log(Prefix + " checkpoint: stage=" + stage + "; counter=" + counter + "; visual_ms=" + VisualMilliseconds +
                "; selected=" + Selected + "; pending=" + PendingSelection + "; ui_group=" + c.UiGroup +
                "; simulation_group=" + c.SimulationGroup + "; group_count=" + c.GroupCount +
                "; selection_visual_flag=" + c.SelectionVisualFlag + "; selector_state=" + s.SelectionState +
                "; selector_exists=" + s.Exists + "; selector_frame=" + s.StoredFrame + "; selector_drawn=" + s.DrawnFrame +
                "; selector_visible=" + s.SelectorVisible + "; selector_last_counter=" + s.LastCounter +
                "; health_visible=" + s.HealthVisible + "; health_exists=" + s.HealthExists +
                "; cursor=" + p.CursorType + "; cursor_frame=" + p.CursorFrame + "; cursor_visible=" + p.CursorVisible +
                "; cursor_last_tick=" + p.CursorLastTick + "; cursor_interval=" + p.CursorInterval +
                "; confirm=" + p.ConfirmExists + "; confirm_frame=" + p.ConfirmDrawnFrame +
                "; confirm_stored=" + p.ConfirmFrame + "; confirm_visible=" + p.ConfirmVisible +
                "; confirm_last_tick=" + p.ConfirmLastTick + "; held=" + Held);
            Debug.Log("[ShipBoxReference] checkpoint: stage=" + stage + "; candidate=" + box.Candidate +
                "; active=" + box.Active + "; visible=" + box.Visible + "; start=" + box.StartX + "," + box.StartY +
                "; extent=" + box.Width + "," + box.Height + "; phase=" + box.Phase + "; last_ms=" + box.LastMilliseconds);
            if (fleet != null)
            {
                var owners = new object[fleet.Count];
                for (int i=0;i<owners.Length;i++) owners[i]=fleet.GetMember(i);
                Debug.Log("[ShipFleetSelection] checkpoint: stage="+stage+"; members="+OwnerIds(owners)+"; pending="+fleet.Pending+"; selected="+fleet.Selected+"; counter="+counter);
                fleetVisuals.Log(stage);
                if(fleetWorld!=null)Debug.Log("[ShipFleetControl] selection: stage="+stage+"; group="+fleet.CurrentGroup+"; temporary="+fleet.TemporaryCount+"; dispatched="+fleetMoveDispatched);
            }
            LogMotion(); visuals.LogStage(stage, Prefix); order.LogStage(stage, Prefix);
            fleetWorld?.LogWorld(stage);
            if(inputWorld!=null)
            {
                //Read-only diagnostics of source5c/5e,group+8 and System+3e,not another state owner.
                string ui="",sim="";
                for(int i=0;i<membership.ActorCount;i++)
                {ui+=(i==0?"":",")+membership.GetUiGroup(i);sim+=(i==0?"":",")+membership.GetSimulationGroup(i);}
                Debug.Log("[ShipFleetControl] world: stage="+stage+"; age="+(membership.GroupCount==0?0:membership.GetGroupWorkAge(0))+
                    "; consumed="+membership.ConsumedCommandCount+"; queued="+outgoing.Count+"; prep="+inputWorld.PreparationCounter+"; ui="+ui+"; sim="+sim);
                //4ce6c0 task header/route readout;no second source of task state.
                if(inputWaveWords!=null&&membership.GroupCount>0)
                    Debug.Log("[ShipFleetControl] queued-task: stage="+stage+"; subtype="+membership.GetTaskSubtype(0)+
                        "; points="+membership.GetQueuedPointCount(0)+"; requested="+membership.GetNormalTaskRequestedAt(0)+
                        "; goal="+membership.GetNormalTaskGoalX(0)+","+membership.GetNormalTaskGoalY(0));
                if(membership.GroupCount>0&&membership.HasNormalTask(0))
                    Debug.Log("[ShipFleetControl] task: stage="+stage+"; requested="+membership.GetNormalTaskRequestedAt(0)+
                        "; goal="+membership.GetNormalTaskGoalX(0)+","+membership.GetNormalTaskGoalY(0));
            }
        }
        private void Fail(Exception exception)
        { Debug.LogException(exception, this); enabled = false; Application.Quit(1); }
        internal void Dispose()
        {
            if (disposed) return; disposed = true;
            WorldPointerInput input = GetComponent<WorldPointerInput>();
            if (input != null) input.enabled = false;
            fleetVisuals?.Dispose(); boxVisual?.Dispose(); visuals?.Dispose(); poses?.Dispose(); masks?.Dispose();
            if (initialized) { Cursor.visible = previousCursorVisible; Cursor.lockState = previousCursorLock; }
            Debug.Log(Prefix + " cleanup: input_unsubscribed=True; visual_refs_cleared=True");
        }
        private void OnDestroy() => Dispose();
    }
}
