using System;
using System.Collections.Generic;
using System.Security.Cryptography;
using AncientConquest.Simulation;
using AncientConquest.World;
using UnityEngine;

namespace AncientConquest.Presentation
{
    /// <summary>
    /// Source0b's bounded selector/healthy bar, normal cursor and command confirmation.
    /// The retained34 world renderers have source depths at least10000; these two
    /// separate depth1020 nodes therefore follow that entire cohort. This adapter
    /// does not describe ordering against any other source object classes.
    /// </summary>
    internal sealed class ShipPointerVisualReference : IDisposable
    {
        private const string Root = "ShipPointerVisualsGenerated/";
        private const string PayloadHash = "051580f543da9e3b448036c67706d80e3c1185d4c10aa7e73cfe94e4fe9020a0";
        [Serializable] private sealed class Frame
        {
            public string name = null, rgba_sha256 = null;
            public int atlas_x = 0, atlas_y = 0, width = 0, height = 0;
        }
        [Serializable] private sealed class Sequence
        {
            public string id = null;
            public int[] frames = null;
        }
        [Serializable] private sealed class Health
        {
            public int frame = 0, width = 0, height = 0, depth = 0, health_percent = 0;
        }
        [Serializable] private sealed class Manifest
        {
            public int schema_version = 0, native_canvas_width = 0, native_canvas_height = 0;
            public int atlas_width = 0, atlas_height = 0, frame_count = 0;
            public Frame[] frames = null;
            public Sequence[] sequences = null;
            public Health healthbar = null;
        }

        private readonly Dictionary<string, int[]> sequences = new Dictionary<string, int[]>(StringComparer.Ordinal);
        private readonly List<GameObject> objects = new List<GameObject>();
        private Sprite[] sprites;
        private Frame[] frames;
        private Texture2D atlas;
        private SpriteRenderer selector, health, confirm, pointer;
        private SourceSpriteDepthQueue overlay;
        private int selectorNode = -1, healthNode = -1;
        private bool selectorExists, healthExists, disposed;
        private PointerCursorProgression.Snapshot cursorState;
        private int cursorIndex = -1;
        private readonly int originX, originY;

        internal ShipPointerVisualReference(Transform parent, Material material, int originX, int originY)
        {
            if (parent == null || material == null) throw new ArgumentNullException(nameof(parent));
            this.originX = originX; this.originY = originY;
            try
            {
                TextAsset descriptor = Resources.Load<TextAsset>(Root + "ShipPointerVisualsManifest");
                if (descriptor == null) throw new InvalidOperationException("The staged pointer visual manifest is missing.");
                Manifest manifest;
                try { manifest = JsonUtility.FromJson<Manifest>(descriptor.text); }
                finally { Resources.UnloadAsset(descriptor); }
                if (manifest == null || manifest.schema_version != 1 || manifest.native_canvas_width != 1920 ||
                    manifest.native_canvas_height != 1080 || manifest.atlas_width != 1024 || manifest.atlas_height != 128 ||
                    manifest.frame_count != 29 || manifest.frames == null || manifest.frames.Length != 29 ||
                    manifest.sequences == null || manifest.sequences.Length != 10 || manifest.healthbar == null ||
                    manifest.healthbar.frame != 28 || manifest.healthbar.width != 34 || manifest.healthbar.height != 4 ||
                    manifest.healthbar.depth != 1020 || manifest.healthbar.health_percent != 100)
                    throw new InvalidOperationException("The staged pointer visual recipe differs from the source0b subset.");
                TextAsset payload = Resources.Load<TextAsset>(Root + "ShipPointerVisualsRgba");
                if (payload == null) throw new InvalidOperationException("The staged pointer visual atlas is missing.");
                byte[] pixels;
                try { pixels = payload.bytes; }
                finally { Resources.UnloadAsset(payload); }
                if (pixels.Length != 524288 || Hash(pixels) != PayloadHash)
                    throw new InvalidOperationException("The source pointer atlas payload differs.");
                frames = manifest.frames;
                var names = new HashSet<string>(StringComparer.Ordinal);
                foreach (Frame frame in frames)
                {
                    if (frame == null || string.IsNullOrEmpty(frame.name) || !names.Add(frame.name) ||
                        frame.width < 1 || frame.height < 1 || frame.atlas_x < 0 || frame.atlas_y < 0 ||
                        (long)frame.atlas_x + frame.width > 1024 || (long)frame.atlas_y + frame.height > 128)
                        throw new InvalidOperationException("A staged pointer visual frame extends outside its atlas.");
                    // These manifest coordinates are already bottom-origin. The per-frame
                    // source hash uses top-down rows, unlike the stored atlas payload.
                    byte[] plane = new byte[checked(frame.width * frame.height * 4)];
                    for (int row = 0; row < frame.height; row++)
                        Buffer.BlockCopy(pixels, ((frame.atlas_y + frame.height - 1 - row) * 1024 + frame.atlas_x) * 4,
                                         plane, row * frame.width * 4, frame.width * 4);
                    if (Hash(plane) != frame.rgba_sha256)
                        throw new InvalidOperationException("A source pointer visual plane hash differs.");
                }
                foreach (Sequence sequence in manifest.sequences)
                {
                    if (sequence == null || string.IsNullOrEmpty(sequence.id) || sequence.frames == null ||
                        sequence.frames.Length == 0 || sequences.ContainsKey(sequence.id))
                        throw new InvalidOperationException("A pointer visual sequence is invalid or duplicated.");
                    foreach (int index in sequence.frames)
                        if (index < 0 || index >= frames.Length) throw new InvalidOperationException("A pointer sequence frame is missing.");
                    sequences.Add(sequence.id, (int[])sequence.frames.Clone());
                }
                RequireSequence("selector", 10);
                RequireSequence("confirm", 4);
                foreach (string kind in new[] { "std", "own", "select", "sea" })
                    foreach (string variant in new[] { "n", "g" })
                        RequireSequence("cursor_" + kind + "_" + variant, kind == "sea" ? 4 : 1);
                atlas = RgbaResourceTexture.Load(Root + "ShipPointerVisualsRgba", 1024, 128, FilterMode.Point);
                sprites = new Sprite[frames.Length];
                for (int index = 0; index < sprites.Length; index++)
                {
                    Frame frame = frames[index];
                    sprites[index] = Sprite.Create(atlas, new Rect(frame.atlas_x, frame.atlas_y, frame.width, frame.height),
                                                   new Vector2(0, 1), 1, 0, SpriteMeshType.FullRect);
                    sprites[index].name = frame.name;
                }
                selector = Create(parent, material, "Source0b selector (separate depth1020 node)");
                health = Create(parent, material, "Source0b healthy bar (separate depth1020 node)");
                confirm = Create(parent, material, "Source command confirmation (late world draw)");
                confirm.sortingOrder = 46;
                // Use the same point-sampled URP path as the source world planes.
                // IMGUI's color conversion quantizes low cursor RGB channels.
                pointer = Create(parent, material, "Source software cursor (last point-sampled world draw)");
                pointer.sortingOrder = 32767;
            }
            catch { Dispose(); throw; }
        }

        private static string Hash(byte[] bytes)
        {
            using (SHA256 sha = SHA256.Create())
                return BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-", "").ToLowerInvariant();
        }
        private void RequireSequence(string id, int count)
        {
            if (!sequences.TryGetValue(id, out int[] values) || values.Length != count)
                throw new InvalidOperationException("The staged source pointer sequence differs: " + id);
        }
        private SpriteRenderer Create(Transform parent, Material material, string name)
        {
            var go = new GameObject(name);
            objects.Add(go);
            go.transform.SetParent(parent, false);
            var renderer = go.AddComponent<SpriteRenderer>();
            renderer.sharedMaterial = material;
            renderer.color = Color.white;
            renderer.enabled = false;
            return renderer;
        }
        private int Index(string id, int frame)
        {
            int[] sequence = sequences[id];
            if (frame < 0 || frame >= sequence.Length) throw new InvalidOperationException("A source visual frame is outside its sequence.");
            return sequence[frame];
        }
        private static void Place(SpriteRenderer renderer, Sprite sprite, bool visible, int x, int y)
        {
            renderer.sprite = sprite;
            renderer.transform.localPosition = new Vector3(x, -y, 0);
            renderer.enabled = visible;
        }
        private void RebuildOverlay(bool selectorPresent, bool healthPresent)
        {
            if (healthPresent && !selectorPresent) throw new InvalidOperationException("The source health node has no selector owner.");
            selectorExists = selectorPresent; healthExists = healthPresent;
            overlay = new SourceSpriteDepthQueue();
            selectorNode = selectorPresent ? overlay.Register(1020) : -1;
            healthNode = healthPresent ? overlay.Register(1020) : -1;
            for (int rank = 0; rank < overlay.Count; rank++)
            {
                int node = overlay.GetDrawNode(rank);
                if (node != selectorNode && node != healthNode)
                    throw new InvalidOperationException("An unexpected node entered the bounded pointer overlay.");
                (node == selectorNode ? selector : health).sortingOrder = 44 + rank;
            }
        }
        internal void SetConfirmationOrder(int value) { confirm.sortingOrder = value; }
        internal void SetBoxActive(bool active) { confirm.sortingOrder = active ? 47 : 46; }
        internal void Apply(ShipSelectionProgression.Snapshot selection, PointerCursorProgression.Snapshot cursor)
        {
            if (disposed) throw new ObjectDisposedException(nameof(ShipPointerVisualReference));
            if (overlay == null || selectorExists != selection.Exists || healthExists != selection.HealthExists)
                RebuildOverlay(selection.Exists, selection.HealthExists);
            Place(selector, selection.DrawnFrame >= 0 ? sprites[Index("selector", selection.DrawnFrame)] : null,
                  selection.Exists && selection.SelectorVisible, selection.WorldPixelX, selection.WorldPixelY);
            Place(health, sprites[28], selection.HealthExists && selection.HealthVisible, selection.HealthWorldX, selection.HealthWorldY);
            Place(confirm, cursor.ConfirmDrawnFrame >= 0 ? sprites[Index("confirm", cursor.ConfirmDrawnFrame)] : null,
                  cursor.ConfirmExists && cursor.ConfirmVisible, cursor.ConfirmWorldX, cursor.ConfirmWorldY);
            cursorState = cursor;
            cursorIndex = -1;
            if (cursor.CursorVisible)
            {
                string id;
                switch (cursor.CursorType)
                {
                    case 0: id = cursor.GreenVariant ? "cursor_std_g" : "cursor_std_n"; break;
                    case 5: id = cursor.GreenVariant ? "cursor_own_g" : "cursor_own_n"; break;
                    case 6: id = cursor.GreenVariant ? "cursor_select_g" : "cursor_select_n"; break;
                    case 7: id = cursor.GreenVariant ? "cursor_sea_g" : "cursor_sea_n"; break;
                    default: throw new NotSupportedException("The pointer renderer received an unsupported cursor type.");
                }
                cursorIndex = Index(id, cursor.CursorFrame);
            }
            Place(pointer, cursorIndex >= 0 ? sprites[cursorIndex] : null,
                  cursorIndex >= 0 && cursor.CursorVisible,
                  unchecked(originX + cursor.CursorWorldX), unchecked(originY + cursor.CursorWorldY));
        }

        internal void LogStage(string stage, string prefix = "[ShipPointerReference]")
        {
            if (disposed) throw new ObjectDisposedException(nameof(ShipPointerVisualReference));
            Debug.Log(prefix + " visual_queue: stage=" + stage + "; nodes=" + (overlay == null ? 0 : overlay.Count) +
                      "; source_depth=1020; base_renderers=34; confirm_late=True; cursor_gui=False");
            LogRenderer(prefix, stage, "selector", selector, selectorExists);
            LogRenderer(prefix, stage, "health", health, healthExists);
            LogRenderer(prefix, stage, "confirm", confirm, cursorState.ConfirmExists);
            Debug.Log(prefix + " visual: stage=" + stage + "; kind=cursor; exists=" + (cursorIndex >= 0) +
                      "; visible=" + pointer.enabled +
                      "; sprite=" + (pointer.sprite == null ? "none" : pointer.sprite.name) +
                      "; position=" + ((int)pointer.transform.localPosition.x - originX) + "," +
                      ((int)-pointer.transform.localPosition.y - originY) +
                      "; order=" + pointer.sortingOrder + "; scale=2; sampling=Point");
        }
        private static void LogRenderer(string prefix, string stage, string kind, SpriteRenderer renderer, bool exists)
        {
            Debug.Log(prefix + " visual: stage=" + stage + "; kind=" + kind + "; exists=" + exists +
                      "; visible=" + renderer.enabled + "; sprite=" + (renderer.sprite == null ? "none" : renderer.sprite.name) +
                      "; position=" + (int)renderer.transform.localPosition.x + "," + (int)-renderer.transform.localPosition.y +
                      "; order=" + renderer.sortingOrder + "; sampling=Point");
        }
        public void Dispose()
        {
            if (disposed) return;
            disposed = true;
            foreach (GameObject go in objects)
            {
                if (go == null) continue;
                SpriteRenderer renderer = go.GetComponent<SpriteRenderer>();
                if (renderer != null) { renderer.sprite = null; renderer.sharedMaterial = null; }
                UnityEngine.Object.Destroy(go);
            }
            objects.Clear();
            if (sprites != null) foreach (Sprite sprite in sprites) if (sprite != null) UnityEngine.Object.Destroy(sprite);
            if (atlas != null) UnityEngine.Object.Destroy(atlas);
            sequences.Clear(); sprites = null; atlas = null; overlay = null;
        }
    }
}
