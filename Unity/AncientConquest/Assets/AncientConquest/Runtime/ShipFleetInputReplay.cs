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
    internal sealed class ShipFleetInputReplay : MonoBehaviour
    {
        private const string Prefix = "[ShipFleetReplay]";
        private const float HoldSeconds = 1.25f;
        private const float TimeoutSeconds = 180f;
        private ShipPointerReference host;
        private Mouse previousMouse, replayMouse;
        private Keyboard previousKeyboard, replayKeyboard;
        private bool shift, control;
        private float started;
        private bool running, completed, disposed;

        internal void Configure(ShipPointerReference reference)
        {
            if (host != null || isActiveAndEnabled)
                throw new InvalidOperationException("Configure the inactive source pointer replay once.");
            host = reference ?? throw new ArgumentNullException(nameof(reference));
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
            Debug.Log(Prefix + " starting: input=synthetic-InputSystem-QueueStateEvent; os_input=False; movement=False");
            while (!Application.isFocused || Screen.width != 1920 || Screen.height != 1080)
            { if (Time.realtimeSinceStartup-started>10f) throw new InvalidOperationException("Fleet replay needs focused1920x1080."); yield return null; }
            previousMouse=Mouse.current;previousKeyboard=Keyboard.current;CreateMouse();
            replayKeyboard=InputSystem.AddDevice<Keyboard>("AncientConquestFleetReplayKeyboard");replayKeyboard.MakeCurrent();
            yield return SendWorld("initial",800,100);
            yield return Click("b",1056,160);
            shift=true;yield return Click("add-c",1376,352);
            yield return Motion("bc-phase0",1);
            yield return Click("toggle-b",1056,160);
            yield return Motion("b-reversing",2);
            yield return Click("add-d",1248,288);shift=false;
            yield return Motion("b-removed",3);
            yield return Motion("cd-healthy",12);
            yield return Box("all",1000,100,1500,500);
            yield return Motion("all-phase0",13);
            yield return Motion("all-healthy",22);
            yield return Box("empty",800,300,900,400);
            shift=true;yield return Click("remove-d",1248,288);
            yield return Box("add-d-box",1160,200,1320,360);shift=false;
            yield return Click("guard-move",1184,352);
            yield return SendWorld("cancel-down",800,300,true);
            yield return SendWorld("cancel-active",820,320,true);
            InputSystem.RemoveDevice(replayMouse);replayMouse=null;yield return Observe("device-cancelled");
            CreateMouse();yield return SendWorld("recovered",822,320);
            yield return Send("clear-right-down",new Vector2(448,600),right:true);
            yield return Send("clear-right-up",new Vector2(448,600));
            yield return Motion("bars-removed",23);
            yield return Motion("selectors-removed",32);
            yield return Click("d-again",1248,288);
            yield return Motion("d-recreated",33);
            yield return Motion("d-healthy",42);
            control=true;yield return Click("ctrl-b",1056,160);control=false;
            yield return Motion("ctrl-b-phase0",43);
            completed=true;running=false;
            Debug.Log(Prefix+" complete: counter="+host.Counter+"; input=synthetic-InputSystem-QueueStateEvent; os_input=False; movement=False");
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
            InputSystem.QueueStateEvent(replayKeyboard,new KeyboardState(shift?new[]{Key.LeftShift}:control?new[]{Key.LeftCtrl}:Array.Empty<Key>()));
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
