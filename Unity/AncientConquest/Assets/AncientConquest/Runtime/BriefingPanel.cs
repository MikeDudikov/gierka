using System;
using UnityEngine;

namespace AncientConquest.Presentation
{
    /// <summary>Owns the staged miss000 briefing layers and its local UI state.</summary>
    internal sealed class BriefingPanel : IDisposable
    {
        [Serializable]
        private sealed class Control
        {
            public int resource_id = 0;
            public string label = null;
            public int[] native_rect = null;
        }
        [Serializable]
        private sealed class DifficultyControl
        {
            public int value = 0;
            public string label = null;
            public int[] native_rect = null;
        }
        [Serializable]
        private sealed class Manifest
        {
            public int schema_version = 0;
            public int native_canvas_width = 0;
            public int native_canvas_height = 0;
            public int background_width = 0;
            public int background_height = 0;
            public bool background_upscale_draft = false;
            public int button_atlas_width = 0;
            public int button_atlas_height = 0;
            public int difficulty_atlas_width = 0;
            public int difficulty_atlas_height = 0;
            public int[] difficulty_rect = null;
            public Control[] controls = null;
            public DifficultyControl[] difficulty_controls = null;
            public int default_difficulty = 0;
            public string mission_title = null;
        }

        private readonly Manifest info;
        private readonly MainMenuButton[] buttons;
        private readonly BriefingDifficultySelection difficulty;
        private Texture2D background;
        private Texture2D staticUi;
        private Texture2D buttonAtlas;
        private Texture2D difficultyAtlas;

        internal int SelectedDifficulty => difficulty.SelectedDifficulty;
        internal string MissionTitle => info.mission_title;

        internal BriefingPanel()
        {
            TextAsset resource = Resources.Load<TextAsset>("BriefingGenerated/BriefingManifest");
            if (resource == null) throw new InvalidOperationException("Briefing manifest is missing; stage miss000 first.");
            try { info = JsonUtility.FromJson<Manifest>(resource.text); }
            finally { Resources.UnloadAsset(resource); }
            if (info == null || info.schema_version != 1 ||
                info.native_canvas_width != NativeMenuCanvas.Width ||
                info.native_canvas_height != NativeMenuCanvas.Height ||
                info.background_width < (info.background_upscale_draft ? 1280 : NativeMenuCanvas.Width) ||
                info.background_height < (info.background_upscale_draft ? 720 : NativeMenuCanvas.Height) ||
                Math.Abs((double)info.background_width / info.background_height - 16.0 / 9.0) > 0.01 ||
                info.controls == null || info.controls.Length != 2 ||
                info.controls[0] == null || info.controls[0].resource_id != 1010 ||
                info.controls[1] == null || info.controls[1].resource_id != 1002 ||
                info.button_atlas_width != 418 || info.button_atlas_height != 288 ||
                info.difficulty_atlas_width != 504 || info.difficulty_atlas_height != 149 ||
                info.difficulty_controls == null || info.difficulty_controls.Length != 3 ||
                string.IsNullOrEmpty(info.mission_title))
                throw new InvalidOperationException("Briefing manifest does not match the native miss000 contract.");
            ValidateRect(info.difficulty_rect, 168, 149);
            buttons = new MainMenuButton[2];
            for (int i = 0; i < buttons.Length; i++)
            {
                int[] rect = info.controls[i].native_rect;
                ValidateRect(rect, 209, 72);
                // The world simulation is not ready: Start remains visibly disabled.
                buttons[i] = new MainMenuButton(rect[0], rect[1], rect[2], rect[3], i != 0);
            }
            var radioRects = new int[3][];
            for (int i = 0; i < radioRects.Length; i++)
            {
                DifficultyControl control = info.difficulty_controls[i];
                if (control == null || control.value != i)
                    throw new InvalidOperationException("Briefing difficulty order is invalid.");
                ValidateRect(control.native_rect, 41, 41);
                radioRects[i] = control.native_rect;
            }
            difficulty = new BriefingDifficultySelection(info.default_difficulty, radioRects);
            try
            {
                background = RgbaResourceTexture.Load("BriefingGenerated/BackgroundRgba", info.background_width, info.background_height);
                // UI already has authored native antialiasing. Point sampling avoids
                // another interpolation of glyph edges in the full-frame GUI pass.
                staticUi = RgbaResourceTexture.Load("BriefingGenerated/StaticUiRgba", NativeMenuCanvas.Width, NativeMenuCanvas.Height, FilterMode.Point);
                buttonAtlas = RgbaResourceTexture.Load("BriefingGenerated/ButtonsRgba", info.button_atlas_width, info.button_atlas_height, FilterMode.Point);
                difficultyAtlas = RgbaResourceTexture.Load("BriefingGenerated/DifficultyRgba", info.difficulty_atlas_width, info.difficulty_atlas_height, FilterMode.Point);
            }
            catch
            {
                Dispose();
                throw;
            }
        }

        private static void ValidateRect(int[] rect, int width, int height)
        {
            if (rect == null || rect.Length != 4 || rect[2] != width || rect[3] != height ||
                rect[0] < 0 || rect[1] < 0 || rect[0] > NativeMenuCanvas.Width - width ||
                rect[1] > NativeMenuCanvas.Height - height)
                throw new InvalidOperationException("Briefing control rectangle is invalid.");
        }

        internal int ProcessPointer(int message, int x, int y)
        {
            if (difficulty.Process(message, x, y))
                Debug.Log("Briefing difficulty: " + SelectedDifficulty);
            for (int i = 0; i < buttons.Length; i++)
                if (buttons[i].Process(message, x, y))
                {
                    Debug.Log("Briefing command: " + info.controls[i].resource_id + " (" + info.controls[i].label + ")");
                    return info.controls[i].resource_id;
                }
            return 0;
        }

        internal void CancelPointer()
        {
            foreach (MainMenuButton button in buttons) button.CancelPointer();
        }

        private static Rect Destination(int x, int y, int width, int height, Rect frame)
        {
            return new Rect(x * frame.width / NativeMenuCanvas.Width, y * frame.height / NativeMenuCanvas.Height,
                            width * frame.width / NativeMenuCanvas.Width, height * frame.height / NativeMenuCanvas.Height);
        }

        internal void Draw(Rect frame)
        {
            GUI.DrawTexture(frame, background, ScaleMode.ScaleAndCrop, false);
            GUI.DrawTexture(frame, staticUi, ScaleMode.StretchToFill, true);
            int[] radio = info.difficulty_rect;
            GUI.DrawTextureWithTexCoords(Destination(radio[0], radio[1], radio[2], radio[3], frame),
                difficultyAtlas, new Rect(SelectedDifficulty / 3f, 0, 1 / 3f, 1), true);
            for (int i = 0; i < buttons.Length; i++)
            {
                MainMenuButton button = buttons[i];
                GUI.DrawTextureWithTexCoords(Destination(button.X, button.Y, button.Width, button.Height, frame),
                    buttonAtlas, new Rect(i / 2f, 1 - (button.State + 1) / 4f, 1 / 2f, 1 / 4f), true);
            }
        }

        public void Dispose()
        {
            Release(ref background);
            Release(ref staticUi);
            Release(ref buttonAtlas);
            Release(ref difficultyAtlas);
        }

        private static void Release(ref Texture2D texture)
        {
            if (texture != null) UnityEngine.Object.Destroy(texture);
            texture = null;
        }
    }
}
