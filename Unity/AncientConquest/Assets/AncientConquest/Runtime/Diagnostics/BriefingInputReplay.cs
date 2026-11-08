using System;
using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;

namespace AncientConquest.Diagnostics
{
    /// <summary>
    /// Opt-in first-briefing integration probe. All interactions are ordinary
    /// queued MouseState events; no domain/navigation methods are called.
    /// </summary>
    public sealed class BriefingInputReplay : MonoBehaviour
    {
        [Serializable]
        private sealed class MenuManifest
        {
            public int native_canvas_width = 0;
            public int native_canvas_height = 0;
            public MenuUi ui = null;
        }
        [Serializable]
        private sealed class MenuUi { public Control[] controls = null; }
        [Serializable]
        private sealed class BriefingManifest
        {
            public int native_canvas_width = 0;
            public int native_canvas_height = 0;
            public int default_difficulty = 0;
            public Control[] controls = null;
            public DifficultyControl[] difficulty_controls = null;
        }
        [Serializable]
        private sealed class Control
        {
            public int resource_id = 0;
            public int[] native_rect = null;
        }
        [Serializable]
        private sealed class DifficultyControl
        {
            public int value = 0;
            public int[] native_rect = null;
        }

        private const float StageHoldSeconds = 1f;
        private const float TimeoutSeconds = 90f;
        private Mouse previousMouse;
        private Mouse replayMouse;
        private MenuManifest menu;
        private BriefingManifest briefing;
        private Control open;
        private Control quit;
        private Control start;
        private Control cancel;
        private DifficultyControl hard;
        private DifficultyControl normal;
        private bool running;
        private bool quitReleaseQueued;
        private float startedAt;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void CreateReplayWhenRequested()
        {
            if (Array.IndexOf(Environment.GetCommandLineArgs(), "--briefing-input-replay") < 0) return;
            if (Array.IndexOf(Environment.GetCommandLineArgs(), "--menu-input-replay") >= 0)
            {
                Debug.LogError("Briefing input replay: menu and briefing replay flags are mutually exclusive.");
                return;
            }
            var probe = new GameObject("Briefing input replay (explicit diagnostic)");
            DontDestroyOnLoad(probe);
            probe.AddComponent<BriefingInputReplay>();
        }

        private IEnumerator Start()
        {
            startedAt = Time.realtimeSinceStartup;
            running = true;
            Debug.Log("Briefing input replay: starting; synthetic Input System device; not OS input validation.");
            menu = LoadManifest<MenuManifest>("ReferenceGenerated/MenuRgbaManifest");
            briefing = LoadManifest<BriefingManifest>("BriefingGenerated/BriefingManifest");
            ValidateManifests();
            while (!Application.isFocused || Screen.width <= 0 || Screen.height <= 0)
            {
                if (Time.realtimeSinceStartup - startedAt > 10f)
                    throw new InvalidOperationException("Briefing input replay: player did not obtain focus in 10 seconds.");
                yield return null;
            }
            yield return new WaitForSecondsRealtime(1f);
            previousMouse = Mouse.current;
            replayMouse = InputSystem.AddDevice<Mouse>("AncientConquestBriefingReplayMouse");
            replayMouse.MakeCurrent();
            Vector2 outside = new Vector2(1, 1);
            try
            {
                yield return Send("menu-idle", outside, false);
                yield return Send("open-hover", Center(open.native_rect), false);
                yield return Send("open-down", Center(open.native_rect), true);
                yield return Send("open-release", Center(open.native_rect), false);
                yield return Send("briefing-easy", outside, false);

                yield return Send("disabled-start-hover", Center(start.native_rect), false);
                yield return Send("disabled-start-down", Center(start.native_rect), true);
                yield return Send("disabled-start-release", Center(start.native_rect), false);

                yield return Send("hard-hover", Center(hard.native_rect), false);
                yield return Send("hard-down", Center(hard.native_rect), true);
                yield return Send("hard-release", Center(hard.native_rect), false);
                yield return Send("hard-current-down", Center(hard.native_rect), true);
                yield return Send("hard-current-release", Center(hard.native_rect), false);

                // The original TabClass hit area is the icon, not its painted label.
                Vector2 normalLabel = Center(normal.native_rect) + new Vector2(65f, 0f);
                yield return Send("normal-label-hover", normalLabel, false);
                yield return Send("normal-label-down", normalLabel, true);
                yield return Send("normal-label-release", normalLabel, false);

                yield return Send("cancel-hover", Center(cancel.native_rect), false);
                yield return Send("cancel-down", Center(cancel.native_rect), true);
                yield return Send("cancel-drag-outside", outside, true);
                yield return Send("cancel-outside-release", outside, false);
                yield return Send("briefing-after-cancelled-drag", outside, false);

                yield return Send("valid-cancel-hover", Center(cancel.native_rect), false);
                yield return Send("valid-cancel-down", Center(cancel.native_rect), true);
                yield return Send("valid-cancel-release", Center(cancel.native_rect), false);
                yield return Send("menu-after-cancel", outside, false);

                yield return Send("reopen-hover", Center(open.native_rect), false);
                yield return Send("reopen-down", Center(open.native_rect), true);
                yield return Send("reopen-release", Center(open.native_rect), false);
                yield return Send("briefing-retained-hard", outside, false);
                yield return Send("normal-hover", Center(normal.native_rect), false);
                yield return Send("normal-down", Center(normal.native_rect), true);
                yield return Send("normal-release", Center(normal.native_rect), false);

                yield return Send("second-cancel-hover", Center(cancel.native_rect), false);
                yield return Send("second-cancel-down", Center(cancel.native_rect), true);
                yield return Send("second-cancel-release", Center(cancel.native_rect), false);
                yield return Send("final-menu", outside, false);
                yield return Send("quit-hover", Center(quit.native_rect), false);
                yield return Send("quit-down", Center(quit.native_rect), true);
                quitReleaseQueued = true;
                yield return Send("quit-release", Center(quit.native_rect), false);
                yield return new WaitForSecondsRealtime(3f);
                Debug.LogError("Briefing input replay: player remained alive after Quit release; integration failed.");
            }
            finally
            {
                running = false;
                CleanupDevice();
            }
        }

        private static T LoadManifest<T>(string resource) where T : class
        {
            TextAsset data = Resources.Load<TextAsset>(resource);
            if (data == null) throw new InvalidOperationException("Briefing input replay: manifest missing: " + resource);
            try { return JsonUtility.FromJson<T>(data.text); }
            finally { Resources.UnloadAsset(data); }
        }

        private void ValidateManifests()
        {
            if (menu == null || briefing == null || menu.native_canvas_width <= 0 || menu.native_canvas_height <= 0 ||
                menu.native_canvas_width != briefing.native_canvas_width ||
                menu.native_canvas_height != briefing.native_canvas_height ||
                menu.ui == null || menu.ui.controls == null || briefing.controls == null ||
                briefing.difficulty_controls == null || briefing.difficulty_controls.Length != 3 ||
                briefing.default_difficulty != 0)
                throw new InvalidOperationException("Briefing input replay: invalid canvas or default difficulty.");
            foreach (Control control in menu.ui.controls)
            {
                if (control == null || !ValidRect(control.native_rect)) throw new InvalidOperationException("Briefing input replay: invalid menu control.");
                if (control.resource_id == 101) open = control;
                if (control.resource_id == 103) quit = control;
            }
            foreach (Control control in briefing.controls)
            {
                if (control == null || !ValidRect(control.native_rect)) throw new InvalidOperationException("Briefing input replay: invalid briefing control.");
                if (control.resource_id == 1010) start = control;
                if (control.resource_id == 1002) cancel = control;
            }
            foreach (DifficultyControl control in briefing.difficulty_controls)
            {
                if (control == null || !ValidRect(control.native_rect)) throw new InvalidOperationException("Briefing input replay: invalid difficulty control.");
                if (control.value == 1) normal = control;
                if (control.value == 2) hard = control;
            }
            if (open == null || quit == null || start == null || cancel == null || normal == null || hard == null)
                throw new InvalidOperationException("Briefing input replay: required controls missing.");
        }

        private bool ValidRect(int[] rect)
        {
            return rect != null && rect.Length == 4 && rect[0] >= 0 && rect[1] >= 0 &&
                   rect[2] > 0 && rect[3] > 0 && rect[2] <= menu.native_canvas_width && rect[3] <= menu.native_canvas_height &&
                   rect[0] <= menu.native_canvas_width - rect[2] && rect[1] <= menu.native_canvas_height - rect[3];
        }

        private static Vector2 Center(int[] rect)
        {
            return new Vector2(rect[0] + rect[2] * .5f, rect[1] + rect[3] * .5f);
        }

        private IEnumerator Send(string stage, Vector2 nativePosition, bool held)
        {
            if (!Application.isFocused)
                throw new InvalidOperationException("Briefing input replay: player lost focus during " + stage);
            var state = new MouseState
            {
                position = new Vector2(nativePosition.x * Screen.width / menu.native_canvas_width,
                    Screen.height - nativePosition.y * Screen.height / menu.native_canvas_height)
            };
            if (held) state = state.WithButton(MouseButton.Left);
            InputSystem.QueueStateEvent(replayMouse, state);
            yield return null;
            yield return new WaitForEndOfFrame();
            Debug.Log("Briefing input replay stage: " + stage + "; native=" + nativePosition +
                      "; held=" + held + "; screen=" + Screen.width + "x" + Screen.height);
            yield return new WaitForSecondsRealtime(StageHoldSeconds);
        }

        private void Update()
        {
            if (running && Time.realtimeSinceStartup - startedAt > TimeoutSeconds)
            {
                Debug.LogError("Briefing input replay: 90-second timeout; no pass claimed.");
                running = false;
                StopAllCoroutines();
                CleanupDevice();
            }
        }

        private void OnApplicationQuit()
        {
            if (running)
                Debug.Log("Briefing input replay: application quit observed; Quit release queued=" + quitReleaseQueued);
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
