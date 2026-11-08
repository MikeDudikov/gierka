using System;
using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;

namespace AncientConquest.Diagnostics
{
    /// <summary>
    /// Explicit opt-in integration probe. Queues ordinary Input System events;
    /// it never calls the menu domain, command dispatch or Application.Quit.
    /// </summary>
    public sealed class MenuInputReplay : MonoBehaviour
    {
        [Serializable]
        private sealed class Manifest
        {
            public int native_canvas_width = 0;
            public int native_canvas_height = 0;
            public MenuUi ui = null;
        }
        [Serializable]
        private sealed class BriefingManifest
        {
            public int native_canvas_width = 0;
            public int native_canvas_height = 0;
            public Control[] controls = null;
        }
        [Serializable]
        private sealed class MenuUi { public Control[] controls = null; }
        [Serializable]
        private sealed class Control
        {
            public int resource_id = 0;
            public int[] native_rect = null;
        }

        private const float CapturePauseSeconds = 0.75f;
        private const float TimeoutSeconds = 60f;
        private Mouse previousMouse;
        private Mouse replayMouse;
        private Manifest manifest;
        private Control briefingCancel;
        private bool running;
        private bool quitReleaseQueued;
        private float startedAt;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void CreateReplayWhenRequested()
        {
            if (Array.IndexOf(Environment.GetCommandLineArgs(), "--menu-input-replay") < 0) return;
            var replay = new GameObject("Menu input replay (explicit diagnostic)");
            DontDestroyOnLoad(replay);
            replay.AddComponent<MenuInputReplay>();
        }

        private IEnumerator Start()
        {
            startedAt = Time.realtimeSinceStartup;
            running = true;
            Debug.Log("Menu input replay: starting; synthetic Input System device; not OS input validation.");
            TextAsset resource = Resources.Load<TextAsset>("ReferenceGenerated/MenuRgbaManifest");
            if (resource == null)
            {
                Debug.LogError("Menu input replay: manifest missing.");
                running = false;
                yield break;
            }
            try { manifest = JsonUtility.FromJson<Manifest>(resource.text); }
            finally { Resources.UnloadAsset(resource); }
            if (!ValidManifest())
            {
                Debug.LogError("Menu input replay: invalid native canvas or button geometry.");
                running = false;
                yield break;
            }
            TextAsset briefingResource = Resources.Load<TextAsset>("BriefingGenerated/BriefingManifest");
            if (briefingResource == null)
                throw new InvalidOperationException("Menu input replay: briefing manifest missing.");
            BriefingManifest briefing;
            try { briefing = JsonUtility.FromJson<BriefingManifest>(briefingResource.text); }
            finally { Resources.UnloadAsset(briefingResource); }
            if (briefing == null || briefing.native_canvas_width != manifest.native_canvas_width ||
                briefing.native_canvas_height != manifest.native_canvas_height || briefing.controls == null)
                throw new InvalidOperationException("Menu input replay: briefing canvas invalid.");
            foreach (Control control in briefing.controls)
                if (control != null && control.resource_id == 1002) briefingCancel = control;
            if (briefingCancel == null || !ValidRect(briefingCancel.native_rect))
                throw new InvalidOperationException("Menu input replay: briefing Cancel geometry invalid.");
            while (!Application.isFocused || Screen.width <= 0 || Screen.height <= 0)
            {
                if (Time.realtimeSinceStartup - startedAt > 10f)
                {
                    Debug.LogError("Menu input replay: player did not obtain focus in 10 seconds.");
                    running = false;
                    yield break;
                }
                yield return null;
            }
            // Allow fullscreen setup and the regular menu input subscription to settle.
            yield return new WaitForSecondsRealtime(1f);
            previousMouse = Mouse.current;
            replayMouse = InputSystem.AddDevice<Mouse>("AncientConquestMenuReplayMouse");
            replayMouse.MakeCurrent();
            Vector2 outside = FindOutsidePoint();
            Control first = manifest.ui.controls[0];
            Control quit = null;
            try
            {
                yield return Send("idle", outside, false);
                yield return Send("hover-first", Center(first), false);
                yield return Send("pressed-first", Center(first), true);
                yield return Send("drag-outside-cancel", outside, true);
                yield return Send("reenter-while-held", Center(first), true);
                yield return Send("release-after-cancel", Center(first), false);
                foreach (Control control in manifest.ui.controls)
                {
                    if (control.resource_id == 103) { quit = control; continue; }
                    yield return Send("hover-" + control.resource_id, Center(control), false);
                    yield return Send("pressed-" + control.resource_id, Center(control), true);
                    yield return Send("release-" + control.resource_id, Center(control), false);
                    if (control.resource_id == 101)
                    {
                        // Start scenario now opens the real first-mission briefing.
                        // Return through its ordinary Cancel event before testing later menu entries.
                        yield return Send("briefing-cancel-hover", Center(briefingCancel), false);
                        yield return Send("briefing-cancel-pressed", Center(briefingCancel), true);
                        yield return Send("briefing-cancel-release", Center(briefingCancel), false);
                    }
                }
                yield return Send("hover-quit", Center(quit), false);
                yield return Send("pressed-quit", Center(quit), true);
                // A successful exit must come from the normal menu event callback.
                quitReleaseQueued = true;
                yield return Send("release-quit", Center(quit), false);
                Debug.Log("Menu input replay: Quit release queued; waiting for normal application exit.");
                yield return new WaitForSecondsRealtime(3f);
                Debug.LogError("Menu input replay: player remained alive after Quit release; integration failed.");
            }
            finally
            {
                running = false;
                CleanupDevice();
            }
        }

        private bool ValidManifest()
        {
            if (manifest == null || manifest.native_canvas_width <= 0 || manifest.native_canvas_height <= 0 ||
                manifest.ui == null || manifest.ui.controls == null || manifest.ui.controls.Length != 6) return false;
            int quitCount = 0;
            foreach (Control control in manifest.ui.controls)
            {
                if (control == null || !ValidRect(control.native_rect)) return false;
                if (control.resource_id == 103) quitCount++;
            }
            return quitCount == 1;
        }

        private bool ValidRect(int[] rect)
        {
            return rect != null && rect.Length == 4 && rect[0] >= 0 && rect[1] >= 0 &&
                   rect[2] > 0 && rect[3] > 0 && rect[2] <= manifest.native_canvas_width &&
                   rect[3] <= manifest.native_canvas_height &&
                   rect[0] <= manifest.native_canvas_width - rect[2] &&
                   rect[1] <= manifest.native_canvas_height - rect[3];
        }

        private Vector2 Center(Control control)
        {
            int[] rect = control.native_rect;
            return new Vector2(rect[0] + rect[2] * 0.5f, rect[1] + rect[3] * 0.5f);
        }

        private Vector2 FindOutsidePoint()
        {
            var candidates = new[] { new Vector2(1, 1), new Vector2(manifest.native_canvas_width - 1, 1),
                new Vector2(1, manifest.native_canvas_height - 1),
                new Vector2(manifest.native_canvas_width - 1, manifest.native_canvas_height - 1) };
            foreach (Vector2 candidate in candidates)
            {
                bool hit = false;
                foreach (Control control in manifest.ui.controls)
                {
                    int[] rect = control.native_rect;
                    if (candidate.x >= rect[0] && candidate.x <= rect[0] + rect[2] &&
                        candidate.y >= rect[1] && candidate.y <= rect[1] + rect[3]) { hit = true; break; }
                }
                if (!hit) return candidate;
            }
            throw new InvalidOperationException("Menu input replay: no outside corner available.");
        }

        private IEnumerator Send(string stage, Vector2 nativePosition, bool held)
        {
            if (!Application.isFocused)
                throw new InvalidOperationException("Menu input replay: player lost focus during " + stage);
            Vector2 position = new Vector2(nativePosition.x * Screen.width / manifest.native_canvas_width,
                Screen.height - nativePosition.y * Screen.height / manifest.native_canvas_height);
            var state = new MouseState { position = position };
            if (held) state = state.WithButton(MouseButton.Left);
            InputSystem.QueueStateEvent(replayMouse, state);
            // Input System processes the queued event on its next regular update.
            yield return null;
            // Signal capture readiness only after the new GUI state was rendered.
            yield return new WaitForEndOfFrame();
            Debug.Log("Menu input replay stage: " + stage + "; native=" + nativePosition +
                      "; held=" + held + "; screen=" + Screen.width + "x" + Screen.height);
            yield return new WaitForSecondsRealtime(CapturePauseSeconds);
        }

        private void Update()
        {
            if (running && Time.realtimeSinceStartup - startedAt > TimeoutSeconds)
            {
                Debug.LogError("Menu input replay: 60-second timeout; no pass claimed.");
                running = false;
                StopAllCoroutines();
                CleanupDevice();
            }
        }

        private void OnApplicationQuit()
        {
            if (running)
                Debug.Log("Menu input replay: application quit observed; Quit release queued=" + quitReleaseQueued);
            CleanupDevice();
        }

        private void OnDestroy() { CleanupDevice(); }

        private void CleanupDevice()
        {
            if (replayMouse != null && replayMouse.added) InputSystem.RemoveDevice(replayMouse);
            replayMouse = null;
            if (previousMouse != null && previousMouse.added) previousMouse.MakeCurrent();
            previousMouse = null;
        }
    }
}
