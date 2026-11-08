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
    internal sealed class ShipPointerInputReplay : MonoBehaviour
    {
        private const string Prefix = "[ShipPointerReplay]";
        private const float HoldSeconds = 1.25f;
        private const float TimeoutSeconds = 120f;
        private static readonly Vector2 Friendly = new Vector2(960, 320);
        private static readonly Vector2 Destination = new Vector2(1216, 704);
        private static readonly Vector2 BeforeDestination = new Vector2(1216, 576);
        private static readonly Vector2 SecondDestination = new Vector2(960, 576);
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
            bool two = Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-pointer-replay-two-orders") >= 0;
            Debug.Log(Prefix + " starting: input=synthetic-InputSystem-QueueStateEvent; os_input=False; two_orders=" + two);
            while (!Application.isFocused || Screen.width != 1920 || Screen.height != 1080)
            {
                if (Time.realtimeSinceStartup - started > 10f)
                    throw new InvalidOperationException("The source pointer replay did not obtain1920x1080 focus.");
                yield return null;
            }
            previousMouse = Mouse.current;
            CreateMouse();
            yield return Send("initial", new Vector2(1, 1));
            yield return Send("hover-friendly", Friendly);
            yield return Send("select-down", Friendly, left: true);
            yield return Send("selected", Friendly);
            yield return Send("sea-before-right", Destination);
            yield return Send("right-down", Destination, right: true);
            yield return Send("wrong-right-release", Destination);
            // Right-release on blank SEA clears the source selection. Select again;
            // the two opposite button edges below share a single InputSystem update.
            yield return Send("rehover-friendly", Friendly);
            Queue(Friendly, true, false); Queue(Friendly, false, false);
            yield return Observe("reselected-same-frame");

            yield return Send("cancel-hover", Destination);
            yield return Send("cancel-down", Destination, left: true);
            InputSystem.RemoveDevice(replayMouse); replayMouse = null;
            yield return Observe("device-cancelled");
            CreateMouse();
            // Source global/map gates require a changed logical pixel after the
            // invalidation. A fresh neutral packet must never manufacture Up.
            yield return Send("device-recovered", Destination + new Vector2(2, 0));
            yield return Send("move-down", BeforeDestination, left: true);
            // This one packet changes position AND releases Left. The receiver must
            // refresh cached hover/cell before source LeftUp dispatches action20.
            yield return Send("request-1", Destination);
            host.AdvanceVisualMilliseconds(750);
            // One HD pixel is not a source-pixel move. Neither cursor nor
            // confirmation may draw merely because the cached clock is later.
            yield return Send("subpixel-same-logical", Destination + new Vector2(1, 0));
            yield return Motion(new uint[] {1, 3, 19, 23, 47, 87, 98, 99, 101}, 1);
            if (!host.CanRequestMove) throw new InvalidOperationException("The first queued source move did not clear.");
            if (two)
            {
                yield return Send("second-down", SecondDestination, left: true);
                yield return Send("request-2", SecondDestination);
                yield return Motion(new uint[] {102, 104, 120, 124, 150, 175, 185, 197}, 2);
                if (!host.CanRequestMove) throw new InvalidOperationException("The second queued source move did not clear.");
            }
            host.Held = true;
            completed = true; running = false;
            Debug.Log(Prefix + " complete: counter=" + host.Counter + "; visual_ms=" + host.VisualMilliseconds +
                      "; two_orders=" + two + "; input=synthetic-InputSystem-QueueStateEvent; os_input=False");
            CleanupMouse();
            Application.Quit(0);
        }

        private IEnumerator Motion(uint[] checkpoints, int epoch)
        {
            foreach (uint target in checkpoints)
            {
                host.Held = false;
                while (host.Counter < target) yield return null;
                host.Held = true;
                if (host.Counter != target)
                    throw new InvalidOperationException("The source pointer replay skipped its single-step counter.");
                yield return Observe("motion-" + epoch + "-" + target);
            }
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
