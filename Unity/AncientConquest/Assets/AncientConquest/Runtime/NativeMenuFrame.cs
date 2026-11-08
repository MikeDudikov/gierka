using System;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;

namespace AncientConquest.Presentation
{
    /// <summary>Native full-frame HD background and independently authored UI layer.</summary>
    public sealed class NativeMenuFrame : MonoBehaviour
    {
        [Serializable]
        private sealed class StageInfo
        {
            public int schema_version = 0;
            public int width = 0;
            public int height = 0;
            public bool background_upscale_draft = false;
            public int native_canvas_width = 0;
            public int native_canvas_height = 0;
            public int button_atlas_width = 0;
            public int button_atlas_height = 0;
            public int button_count = 0;
            public int button_states = 0;
            public MenuUi ui = null;
        }
        [Serializable]
        private sealed class MenuUi { public MenuControl[] controls = null; }
        [Serializable]
        private sealed class MenuControl
        {
            public int resource_id = 0;
            public string label = null;
            public int[] native_rect = null;
        }
        private Texture2D background;
        private Texture2D buttonAtlas;
        private BriefingPanel briefing;
        private bool briefingOpen;
        private MainMenuButton[] buttons;
        private MenuControl[] controls;
        private Mouse pointerDevice;
        private bool pointerKnown;
        private bool leftHeld;
        private bool requireLeftRelease;
        private int pointerX;
        private int pointerY;
        private bool previousDisableEventMerging;
        private bool inputDiagnostics;
        private int diagnosticEvents;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        private static void CreateNativeMenu()
        {
            if (TerrainReferenceFrame.IsRequested) return;
            var frame = new GameObject("Native menu frame");
            DontDestroyOnLoad(frame);
            frame.AddComponent<NativeMenuFrame>();
        }
        private void Awake()
        {
            inputDiagnostics = Array.IndexOf(Environment.GetCommandLineArgs(), "--menu-input-diagnostics") >= 0;
#if UNITY_STANDALONE_WIN && !UNITY_EDITOR
            Screen.SetResolution(NativeMenuCanvas.Width, NativeMenuCanvas.Height,
                                 FullScreenMode.ExclusiveFullScreen);
#endif
            try
            {
                TextAsset manifest = Resources.Load<TextAsset>("ReferenceGenerated/MenuRgbaManifest");
                if (manifest == null) throw new InvalidOperationException("Native menu manifest is missing.");
                StageInfo info = JsonUtility.FromJson<StageInfo>(manifest.text);
                Resources.UnloadAsset(manifest);
                if (info == null || info.schema_version != 3 ||
                    info.width < (info.background_upscale_draft ? 1280 : NativeMenuCanvas.Width) ||
                    info.height < (info.background_upscale_draft ? 720 : NativeMenuCanvas.Height) ||
                    info.width > 8192 || info.height > 8192 ||
                    Math.Abs((double)info.width / info.height - (double)NativeMenuCanvas.Width / NativeMenuCanvas.Height) > 0.01 ||
                    info.native_canvas_width != NativeMenuCanvas.Width ||
                    info.native_canvas_height != NativeMenuCanvas.Height ||
                    info.button_count != 6 || info.button_states != 4 ||
                    info.button_atlas_width != 6 * 313 || info.button_atlas_height != 4 * 72 ||
                    info.ui == null || info.ui.controls == null || info.ui.controls.Length != 6)
                    throw new InvalidOperationException("Native menu dimensions are invalid; legacy 800x600 data is not accepted.");
                controls = info.ui.controls;
                buttons = new MainMenuButton[controls.Length];
                for (int i = 0; i < controls.Length; i++)
                {
                    int[] rect = controls[i].native_rect;
                    if (rect == null || rect.Length != 4 || rect[2] != 313 || rect[3] != 72 ||
                        rect[0] < 0 || rect[1] < 0 || rect[0] > NativeMenuCanvas.Width - rect[2] ||
                        rect[1] > NativeMenuCanvas.Height - rect[3])
                        throw new InvalidOperationException("Native menu button geometry is invalid.");
                    buttons[i] = new MainMenuButton(rect[0], rect[1], rect[2], rect[3]);
                }
                background = RgbaResourceTexture.Load("ReferenceGenerated/MenuRgba", info.width, info.height);
                buttonAtlas = RgbaResourceTexture.Load("ReferenceGenerated/MenuButtonsRgba", info.button_atlas_width, info.button_atlas_height, FilterMode.Point);
            }
            catch (Exception exception)
            {
                Debug.LogException(exception, this);
                enabled = false;
            }
        }
        private void OnEnable()
        {
            previousDisableEventMerging = InputSystem.settings.disableRedundantEventsMerging;
            // A merged out-and-back motion would lose the original drag cancellation.
            InputSystem.settings.disableRedundantEventsMerging = true;
            InputSystem.onEvent += OnInputEvent;
            InputSystem.onDeviceChange += OnDeviceChange;
        }
        private void OnDisable()
        {
            InputSystem.onEvent -= OnInputEvent;
            InputSystem.onDeviceChange -= OnDeviceChange;
            InputSystem.settings.disableRedundantEventsMerging = previousDisableEventMerging;
            CancelPointer();
        }
        private void OnApplicationFocus(bool focused)
        {
            if (inputDiagnostics) Debug.Log("Menu input focus: " + focused);
            if (!focused) CancelPointer();
        }
        private void OnDeviceChange(InputDevice device, InputDeviceChange change)
        {
            if (device == pointerDevice && (change == InputDeviceChange.Removed ||
                change == InputDeviceChange.Disconnected || change == InputDeviceChange.Disabled)) CancelPointer();
        }
        private void CancelPointer()
        {
            if (buttons != null)
                foreach (MainMenuButton button in buttons) button?.CancelPointer();
            briefing?.CancelPointer();
            pointerKnown = false;
            leftHeld = false;
            requireLeftRelease = true;
            pointerDevice = null;
        }
        private void OnInputEvent(InputEventPtr inputEvent, InputDevice device)
        {
            if (inputDiagnostics && diagnosticEvents++ < 12)
                Debug.Log("Menu input event: " + inputEvent.type + "; device=" + device.layout +
                          "; focused=" + Application.isFocused);
            if (!(device is Mouse mouse) || !Application.isFocused || buttons == null ||
                Screen.width <= 0 || Screen.height <= 0 ||
                (!inputEvent.IsA<StateEvent>() && !inputEvent.IsA<DeltaStateEvent>())) return;
            if (pointerDevice != null && pointerDevice != mouse) CancelPointer();
            pointerDevice = mouse;
            // Process each input event in order, including down+up within one render frame.
            if (mouse.position.ReadValueFromEvent(inputEvent, out Vector2 position))
            {
                int x = Mathf.FloorToInt(position.x * NativeMenuCanvas.Width / Screen.width);
                int y = Mathf.FloorToInt((Screen.height - position.y) * NativeMenuCanvas.Height / Screen.height);
                if (inputDiagnostics && diagnosticEvents <= 12)
                    Debug.Log("Menu input position: " + position + "; native=" + x + "," + y);
                if (!pointerKnown || x != pointerX || y != pointerY)
                {
                    pointerX = x;
                    pointerY = y;
                    pointerKnown = true;
                    DispatchPointer(MainMenuButton.Move);
                }
            }
            if (pointerKnown && mouse.leftButton.ReadValueFromEvent(inputEvent, out float value))
            {
                bool held = value >= mouse.leftButton.pressPointOrDefault;
                if (inputDiagnostics && diagnosticEvents <= 12)
                    Debug.Log("Menu input left: " + held + "; waitRelease=" + requireLeftRelease);
                if (requireLeftRelease)
                {
                    leftHeld = held;
                    if (!held) requireLeftRelease = false;
                    return;
                }
                if (held != leftHeld)
                {
                    leftHeld = held;
                    DispatchPointer(held ? MainMenuButton.LeftDown : MainMenuButton.LeftUp);
                }
            }
        }
        private void DispatchPointer(int message)
        {
            if (briefingOpen)
            {
                if (briefing.ProcessPointer(message, pointerX, pointerY) == 1002)
                {
                    briefingOpen = false;
                    CancelPointer();
                    Debug.Log("Native screen: menu");
                }
                return;
            }
            for (int i = 0; i < buttons.Length; i++)
                if (buttons[i].Process(message, pointerX, pointerY))
                {
                    Debug.Log("Native menu command: " + controls[i].resource_id + " (" + controls[i].label + ")");
                    if (controls[i].resource_id == 103) Application.Quit();
                    else if (controls[i].resource_id == 101) OpenBriefing();
                    break;
                }
        }
        private void OpenBriefing()
        {
            try
            {
                if (briefing == null) briefing = new BriefingPanel();
                CancelPointer();
                briefingOpen = true;
                Debug.Log("Native screen: briefing; mission=miss000; difficulty=" + briefing.SelectedDifficulty);
            }
            catch (Exception exception)
            {
                Debug.LogException(exception, this);
            }
        }
        private void Start()
        {
            Camera worldCamera = Camera.main;
            if (worldCamera != null) worldCamera.rect = new Rect(0, 0, 1, 1);
            Debug.Log("Native menu display: " + Screen.width + "x" + Screen.height +
                      "; fullscreen=" + Screen.fullScreen + "; mode=" + Screen.fullScreenMode);
            if (inputDiagnostics)
                foreach (InputDevice device in InputSystem.devices)
                    Debug.Log("Menu input device: " + device.layout + "; enabled=" + device.enabled);
        }
        private void OnGUI()
        {
            if (Event.current.type != EventType.Repaint || background == null || buttonAtlas == null ||
                Screen.width <= 0 || Screen.height <= 0) return;
            NativeMenuCanvas canvas = NativeMenuCanvas.FullScreen(Screen.width, Screen.height);
            var fullFrame = new Rect(0, 0, (float)canvas.ScreenWidth, (float)canvas.ScreenHeight);
            Color oldColor = GUI.color;
            Matrix4x4 oldMatrix = GUI.matrix;
            int oldDepth = GUI.depth;
            try
            {
                GUI.color = Color.white;
                GUI.matrix = Matrix4x4.identity;
                GUI.depth = int.MinValue;
                if (briefingOpen)
                {
                    briefing.Draw(fullFrame);
                    return;
                }
                GUI.DrawTexture(fullFrame, background, ScaleMode.ScaleAndCrop, false);
                for (int i = 0; i < buttons.Length; i++)
                {
                    MainMenuButton button = buttons[i];
                    var destination = new Rect(button.X * fullFrame.width / NativeMenuCanvas.Width,
                        button.Y * fullFrame.height / NativeMenuCanvas.Height,
                        button.Width * fullFrame.width / NativeMenuCanvas.Width,
                        button.Height * fullFrame.height / NativeMenuCanvas.Height);
                    GUI.DrawTextureWithTexCoords(destination, buttonAtlas,
                        new Rect(i / 6f, 1 - (button.State + 1) / 4f, 1 / 6f, 1 / 4f), true);
                }
            }
            finally
            {
                GUI.color = oldColor;
                GUI.matrix = oldMatrix;
                GUI.depth = oldDepth;
            }
        }
        private void OnDestroy()
        {
            if (background != null) Destroy(background);
            if (buttonAtlas != null) Destroy(buttonAtlas);
            briefing?.Dispose();
        }
    }
}
