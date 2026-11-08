using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;

namespace AncientConquest.Presentation
{
    /// <summary>
    /// Opt-in real InputSystem event replay. Gameplay interactions are only queued
    /// MouseState packets; host access is restricted to diagnostic clock/observations.
    /// </summary>
    internal sealed class ShipFleetMoveInputReplay : MonoBehaviour
    {
        private const string Prefix = "[ShipFleetMoveReplay]";
        private const float HoldSeconds = 1.25f;
        private const float TimeoutSeconds = 180f;
        private ShipPointerReference host;
        private Mouse previousMouse, replayMouse;
        private Keyboard previousKeyboard, replayKeyboard;
        private bool shift, control;
        private Key replayShiftKey=Key.LeftShift;
        private float started;
        private bool running, completed, disposed;

        internal void Configure(ShipPointerReference reference)
        {
            if (host != null || isActiveAndEnabled)
                throw new InvalidOperationException("Configure the inactive source pointer replay once.");
            host = reference ?? throw new ArgumentNullException(nameof(reference));
            //4e9710 source bindings42/54 shareC45D;exercise actual RightShift independently.
            replayShiftKey=Array.IndexOf(Environment.GetCommandLineArgs(),"--ship-pointer-right-shift-replay")>=0?Key.RightShift:Key.LeftShift;
            // Configure runs before the host GameObject activates, so neither clock
            // can advance before the first queued pointer observation.
            host.Held = true;
        }

        private IEnumerator Start()
        {
            if (host == null) { Fail(new InvalidOperationException("The pointer replay host is missing.")); yield break; }
            started = Time.realtimeSinceStartup; running = true;
            var routines = new Stack<IEnumerator>(); routines.Push(Run());
            while (routines.Count != 0 && running)
            {
                object current = null; bool advanced = false;
                try
                {
                    advanced = routines.Peek().MoveNext();
                    if (advanced) current = routines.Peek().Current;
                    else { (routines.Pop() as IDisposable)?.Dispose(); }
                }
                catch (Exception exception) { Fail(exception); }
                if (!running) yield break;
                if (!advanced) continue;
                if (current is IEnumerator nested) routines.Push(nested);
                else yield return current;
            }
        }

        private IEnumerator Run()
        {
            Debug.Log(Prefix + " starting: input=synthetic-InputSystem-QueueStateEvent; os_input=False; movement=first-normal-order");
            while (!Application.isFocused || Screen.width != 1920 || Screen.height != 1080)
            { if (Time.realtimeSinceStartup-started>10f) throw new InvalidOperationException("Fleet replay needs focused1920x1080."); yield return null; }
            previousMouse=Mouse.current;previousKeyboard=Keyboard.current;CreateMouse();
            replayKeyboard=InputSystem.AddDevice<Keyboard>("AncientConquestFleetReplayKeyboard");replayKeyboard.MakeCurrent();
            yield return SendWorld("initial",800,100);
            yield return Click("b",1056,160);
            shift=true;yield return Click("add-c",1376,352);yield return Click("add-d",1248,288);shift=false;
            //518070/49ca60/4cf2c0:opt-in first Shift commits pending selection.
            bool pendingQueued=Array.IndexOf(Environment.GetCommandLineArgs(),"--ship-pointer-fleet-pending-queued-replay")>=0;
            bool sourceContext=Array.IndexOf(Environment.GetCommandLineArgs(),"--ship-pointer-source-context-replay")>=0;
            if(sourceContext&&!pendingQueued)throw new ArgumentException("Source context replay requires the pending queued sequence.");
            shift=pendingQueued;yield return Click("dispatch",1184,pendingQueued?416:352);
            if(pendingQueued)
            {
                yield return Click("pending-append",1056,288);
                yield return Click("pending-duplicate",1184,416);
            }
            shift=false;
            //Diagnostic source49e230/4ccc30 input sequence;only MouseState emits orders.
            //Two releases at held25 exercise FIFO normal20 overwrite before the next Life.
            bool replacements=Array.IndexOf(Environment.GetCommandLineArgs(),"--ship-pointer-fleet-replace-replay")>=0;
            //518070/49e230 source queued-ui-*-25:three Shift releases25,normal20 at85.
            bool queued=Array.IndexOf(Environment.GetCommandLineArgs(),"--ship-pointer-fleet-queued-replay")>=0;
            if((queued&&replacements)||(pendingQueued&&(queued||replacements)))throw new ArgumentException("Choose one source replay sequence.");
            foreach(uint tick in pendingQueued?new uint[]{1,3,10,25,50,51,80,120,160,200}:queued?new uint[]{1,3,10,25,26,50,85,86,120,160,200}:new uint[]{1,3,10,25,26,50,80,120,160,200})
            {
                if(!replacements&&!queued&&tick==26)continue;
                yield return Motion("tick-"+tick,tick);
                if(pendingQueued&&tick==50)
                {
                    if(sourceContext)
                    {
                        //4ee900 gate,540560 registration and4eff00 recursiveC45D0;no world step between calls.
                        host.ReceiveSourceRouteContext(1,1);yield return Observe("context-blocked");
                        host.ReceiveSourceRouteContext(0,0);yield return Observe("context-inactive");
                        host.ReceiveSourceRouteContext(0,1);yield return Observe("context-reset");
                        host.ReceiveSourceRouteContext(0,1);yield return Observe("context-repeat");
                    }
                    //49ab30/4a2050(0):clear marker graphics while route/task continue.
                    yield return SendWorld("route-clear-point",800,300);
                    yield return Send("route-clear-right-down",new Vector2(448,600),right:true);
                    yield return Send("route-clear-right-up",new Vector2(448,600));
                    //Pinned source pending_queued_input:0c origin1279,388 at50.
                    control=true;yield return Click("route-recall-c",1307,416);control=false;
                }
                if(queued&&tick==25)
                {
                    shift=true;yield return Click("queue-first",1184,416);
                    yield return Click("queue-append",1056,288);
                    yield return Click("queue-duplicate",1184,416);shift=false;
                }
                if(queued&&tick==85)yield return Click("queue-normal",1312,352);
                if(replacements&&tick==25)
                {
                    shift=true;yield return Click("queued-guard",1184,416);shift=false;
                    yield return Click("replace-first",1184,416);
                    yield return Click("replace-last",1056,288);
                }
            }
            //At50 the first route cell is reserved;at200 it is free in the pinned x86 grid.
            if(pendingQueued){shift=true;yield return Click("hidden-duplicate",1184,416);shift=false;}
            yield return SendWorld("clear-point",800,300);
            yield return Send("clear-right-down",new Vector2(448,600),right:true);
            yield return Send("clear-right-up",new Vector2(448,600));
            //Pinned x86 ui-replace:0c origin1156,324;queued_input_world:1284,388.
            control=true;yield return Click("recall-c",pendingQueued?1056:queued?1312:replacements?1184:1312,pendingQueued?288:queued?416:replacements?352:416);control=false;
            completed=true;running=false;
            Debug.Log(Prefix+" complete: counter="+host.Counter+"; input=synthetic-InputSystem-QueueStateEvent; os_input=False; movement=first-normal-order");
            CleanupMouse();Application.Quit(0);
        }
        private IEnumerator Click(string stage,int x,int y)
        { yield return SendWorld(stage+"-down",x,y,true);yield return SendWorld(stage+"-up",x,y); }
        private IEnumerator Box(string stage,int x,int y,int endX,int endY)
        {
            yield return SendWorld(stage+"-down",x,y,true);
            yield return SendWorld(stage+"-activate",x+10,y+10,true);
            yield return SendWorld(stage+"-extent",endX,endY,true);
            yield return SendWorld(stage+"-up",endX,endY);
        }
        private IEnumerator Motion(string stage,uint target)
        {
            host.AdvanceVisualMilliseconds(50);host.Held=false;
            while(host.Counter<target)yield return null;
            host.Held=true;
            if(host.Counter!=target)throw new InvalidOperationException("Fleet replay skipped a source counter.");
            yield return Observe(stage);
        }
        private IEnumerator SendWorld(string stage, int x, int y, bool left = false)
        { yield return Send(stage, new Vector2((x - 576) * 2, y * 2), left); }
        private IEnumerator Send(string stage, Vector2 position, bool left = false, bool right = false)
        {
            Queue(position, left, right);
            yield return Observe(stage);
        }
        private void Queue(Vector2 nativePosition, bool left, bool right)
        {
            if (!Application.isFocused || replayMouse == null)
                throw new InvalidOperationException("The pointer replay lost its focused synthetic mouse.");
            var state = new MouseState
            {
                position = new Vector2(nativePosition.x * Screen.width / 1920f,
                                       Screen.height - nativePosition.y * Screen.height / 1080f)
            };
            if (left) state = state.WithButton(MouseButton.Left);
            if (right) state = state.WithButton(MouseButton.Right);
            InputSystem.QueueStateEvent(replayKeyboard,new KeyboardState(shift?new[]{replayShiftKey}:control?new[]{Key.LeftCtrl}:Array.Empty<Key>()));
            InputSystem.QueueStateEvent(replayMouse, state);
        }
        private IEnumerator Observe(string stage)
        {
            yield return null;
            yield return new WaitForEndOfFrame();
            if (!host.Held) throw new InvalidOperationException("A replay checkpoint did not freeze both source clocks.");
            host.LogCheckpoint(stage);
            Debug.Log(Prefix + " stage: " + stage + "; counter=" + host.Counter + "; visual_ms=" + host.VisualMilliseconds);
            yield return new WaitForSecondsRealtime(HoldSeconds);
        }
        private void CreateMouse()
        {
            replayMouse = InputSystem.AddDevice<Mouse>("AncientConquestWorldPointerReplayMouse");
            replayMouse.MakeCurrent();
        }
        private void CleanupMouse()
        {
            if (replayMouse != null && replayMouse.added) InputSystem.RemoveDevice(replayMouse);
            replayMouse = null;
            if (previousMouse != null && previousMouse.added) previousMouse.MakeCurrent();
            previousMouse = null;
            if(replayKeyboard!=null&&replayKeyboard.added)InputSystem.RemoveDevice(replayKeyboard);
            replayKeyboard=null;
            if(previousKeyboard!=null&&previousKeyboard.added)previousKeyboard.MakeCurrent();previousKeyboard=null;
        }
        private void Update()
        {
            if (running && Time.realtimeSinceStartup - started > TimeoutSeconds)
                Fail(new InvalidOperationException("The source pointer replay exceeded120seconds."));
        }
        private void Fail(Exception exception)
        {
            running = false;
            if (host != null) host.Held = true;
            Debug.LogException(exception, this);
            CleanupMouse();
            Application.Quit(1);
        }
        private void OnDisable()
        {
            if (!completed) running = false;
            CleanupMouse();
        }
        private void OnDestroy()
        {
            if (disposed) return;
            disposed = true; CleanupMouse();
        }
    }
}
