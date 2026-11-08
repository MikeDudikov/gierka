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
    internal sealed class ShipBoxInputReplay : MonoBehaviour
    {
        private const string Prefix = "[ShipBoxReplay]";
        private const float HoldSeconds = 1.25f;
        private const float TimeoutSeconds = 120f;
        private ShipPointerReference host;
        private Mouse previousMouse, replayMouse;
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
            Debug.Log(Prefix + " starting: input=synthetic-InputSystem-QueueStateEvent; os_input=False");
            while (!Application.isFocused || Screen.width != 1920 || Screen.height != 1080)
            {
                if (Time.realtimeSinceStartup - started > 10f) throw new InvalidOperationException("Box replay needs focused1920x1080.");
                yield return null;
            }
            previousMouse = Mouse.current; CreateMouse();
            yield return SendWorld("initial", 800, 100);
            yield return SendWorld("box-down", 1000, 100, true);
            yield return SendWorld("threshold-one-axis", 1008, 200, true);
            yield return SendWorld("activated-zero", 1010, 110, true);
            yield return SendWorld("extent-unpublished", 1110, 210, true);
            yield return Pulse("visible-forward");
            yield return Send("box-right-down", new Vector2(1068, 420), left: true, right: true);
            yield return Send("box-right-release", new Vector2(1068, 420), left: true);
            yield return SendWorld("selected-box", 1110, 210);
            yield return SendWorld("empty-down", 800, 300, true);
            yield return SendWorld("empty-activate", 820, 320, true);
            yield return SendWorld("empty-extent", 900, 400, true);
            yield return SendWorld("empty-preserved", 900, 400);
            yield return SendWorld("reverse-down", 1110, 210, true);
            yield return SendWorld("reverse-activate", 1098, 198, true);
            yield return SendWorld("reverse-extent", 1000, 100, true);
            yield return Pulse("visible-reverse");
            yield return SendWorld("reverse-selected", 1000, 100);
            yield return SendWorld("fleet-down", 1002, 102, true);
            yield return SendWorld("fleet-activate", 1014, 114, true);
            yield return SendWorld("fleet-extent", 1500, 500, true);
            yield return SendWorld("fleet-guarded", 1500, 500);
            yield return SendWorld("cancel-down", 800, 300, true);
            yield return SendWorld("cancel-active", 820, 320, true);
            InputSystem.RemoveDevice(replayMouse); replayMouse = null;
            yield return Observe("device-cancelled");
            CreateMouse(); yield return SendWorld("recovered", 822, 320);
            yield return SendWorld("one-cell-down", 1024, 128, true);
            yield return SendWorld("one-cell-activate", 1040, 144, true);
            yield return SendWorld("one-cell-extent", 1056, 160, true);
            yield return SendWorld("one-cell-preserved", 1056, 160);
            completed = true; running = false;
            Debug.Log(Prefix + " complete: counter=" + host.Counter + "; input=synthetic-InputSystem-QueueStateEvent; os_input=False");
            CleanupMouse(); Application.Quit(0);
        }
        private IEnumerator SendWorld(string stage, int x, int y, bool left = false)
        { yield return Send(stage, new Vector2((x - 576) * 2, y * 2), left); }
        private IEnumerator Pulse(string stage)
        {
            uint target = host.Counter + 1;
            host.AdvanceVisualMilliseconds(50); host.Held = false;
            while (host.Counter < target) yield return null;
            host.Held = true;
            if (host.Counter != target) throw new InvalidOperationException("Box replay skipped a source counter.");
            yield return Observe(stage);
        }
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
