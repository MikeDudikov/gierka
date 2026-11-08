using System;
using System.Collections;
using System.Collections.Generic;
using AncientConquest.World;
using UnityEngine;

namespace AncientConquest.Presentation
{
    /// <summary>Explicit diagnostic seeds and frozen reefs; no original object constructors or simulation.</summary>
    internal sealed class MissionObjectReference : IDisposable
    {
        private const string ResourceRoot = "MissionObjectsGenerated/";
        [Serializable]
        private sealed class Record
        {
            public string resource_name = null;
            public int payload_offset = 0;
            public int payload_length = 0;
        }
        [Serializable]
        private sealed class Frame
        {
            public int variant = 0;
            public int reference_state = 0;
            public int reference_frame_index = 0;
            public int atlas_x = 0;
            public int atlas_y = 0;
            public int width = 0;
            public int height = 0;
        }
        [Serializable]
        private sealed class Manifest
        {
            public int schema_version = 0;
            public string mission = null;
            public int native_canvas_width = 0;
            public int native_canvas_height = 0;
            public int record_count = 0;
            public int reef_atlas_width = 0;
            public int reef_atlas_height = 0;
            public Record[] records = null;
            public Frame[] reef_frames = null;
        }

        private readonly List<GameObject> visuals = new List<GameObject>();
        private readonly Dictionary<byte, Sprite> sprites = new Dictionary<byte, Sprite>();
        private readonly List<MissionReefSeed> reefs = new List<MissionReefSeed>();
        private readonly Dictionary<uint, SpriteRenderer> reefRenderers = new Dictionary<uint, SpriteRenderer>();
        private Texture2D atlas;
        private MissionInitialSetup setup;
        private int selectedCount;
        private int seedCount;
        private MissionShipReference shipReference;
        private readonly bool includesShips;

        internal MissionObjectReference(Transform parent, Material material, bool includeShips = false)
        {
            includesShips = includeShips;
            try
            {
                Manifest info = LoadManifest();
                setup = new MissionInitialSetup(LoadBytes("MissionDescriptor"), LoadBytes("SavedViews"));
                byte[] players = setup.CopyPlayersDescriptor();
                byte[] blob = LoadBytes("ObjectSeeds");
                var identifiers = new HashSet<uint>();
                int expectedOffset = 0;
                var selectedSeeds = new List<MissionObjectSeed>();
                foreach (Record record in info.records)
                {
                    if (record == null || record.payload_offset != expectedOffset || record.payload_length < 16 ||
                        expectedOffset > blob.Length || record.payload_length > blob.Length - expectedOffset)
                        throw new InvalidOperationException("Object record extends outside its contiguous source payload.");
                    byte[] payload = new byte[record.payload_length];
                    Buffer.BlockCopy(blob, expectedOffset, payload, 0, payload.Length);
                    expectedOffset += payload.Length;
                    var seed = new MissionObjectSeed(record.resource_name, payload);
                    if (!identifiers.Add(seed.InstanceId))
                        throw new InvalidOperationException("Duplicate source object instance ID.");
                    seedCount++;
                    if (!MissionObjectSelection.TrySelect(seed, players, out _)) continue;
                    selectedCount++;
                    if (includeShips) selectedSeeds.Add(seed);
                    if (MissionReefSeed.TryRead(seed, out MissionReefSeed reef)) reefs.Add(reef);
                }
                if (expectedOffset != blob.Length)
                    throw new InvalidOperationException("Object seed data contains an unreferenced tail.");
                atlas = RgbaResourceTexture.Load(ResourceRoot + "ReefFramesRgba",
                    info.reef_atlas_width, info.reef_atlas_height, FilterMode.Point);
                foreach (Frame frame in info.reef_frames)
                {
                    if (frame == null || (frame.variant != 2 && frame.variant != 3) ||
                        frame.reference_state != 1 || frame.reference_frame_index != 0 ||
                        frame.width != 64 || frame.height != 64 || frame.atlas_y != 0 ||
                        frame.atlas_x != (frame.variant - 2) * 64 || sprites.ContainsKey((byte)frame.variant))
                        throw new InvalidOperationException("Reef atlas does not match the frozen reference contract.");
                    sprites.Add((byte)frame.variant, Sprite.Create(atlas,
                        new Rect(frame.atlas_x, 0, frame.width, frame.height), new Vector2(0, 1),
                        1, 0, SpriteMeshType.FullRect));
                }
                int reefIndex = 0;
                foreach (MissionReefSeed reef in reefs)
                {
                    if (!sprites.TryGetValue(reef.Variant, out Sprite sprite))
                        throw new InvalidOperationException("A source reef variant has no staged reference frame.");
                    var visual = new GameObject("Frozen source reef " + reef.InstanceId.ToString("x8"));
                    visuals.Add(visual);
                    visual.transform.SetParent(parent, false);
                    visual.transform.localPosition = new Vector3(reef.WorldPixelX, -reef.WorldPixelY, 0);
                    SpriteRenderer renderer = visual.AddComponent<SpriteRenderer>();
                    renderer.sharedMaterial = material;
                    renderer.sprite = sprite;
                    renderer.color = Color.white;
                    reefRenderers.Add(reef.InstanceId, renderer);
                    // Reference overlay only; original world ordering/fog are not simulated.
                    renderer.sortingOrder = includeShips ? 18 + reefs.Count - 1 - reefIndex : 1;
                    reefIndex++;
                }
                if (includeShips) shipReference = new MissionShipReference(parent, material, selectedSeeds, reefs.Count, reefRenderers);
            }
            catch { Dispose(); throw; }
        }

        private static byte[] LoadBytes(string name)
        {
            TextAsset asset = Resources.Load<TextAsset>(ResourceRoot + name);
            if (asset == null) throw new InvalidOperationException("Missing staged object resource: " + name);
            try { return asset.bytes; }
            finally { Resources.UnloadAsset(asset); }
        }

        private static Manifest LoadManifest()
        {
            TextAsset asset = Resources.Load<TextAsset>(ResourceRoot + "MissionObjectsManifest");
            if (asset == null) throw new InvalidOperationException("Stage mission object references first.");
            Manifest info;
            try { info = JsonUtility.FromJson<Manifest>(asset.text); }
            finally { Resources.UnloadAsset(asset); }
            if (info == null || info.schema_version != 1 || info.mission != "miss000" ||
                info.native_canvas_width != NativeMenuCanvas.Width || info.native_canvas_height != NativeMenuCanvas.Height ||
                info.record_count != 45 || info.records == null || info.records.Length != info.record_count ||
                info.reef_atlas_width != 128 || info.reef_atlas_height != 64 ||
                info.reef_frames == null || info.reef_frames.Length != 2)
                throw new InvalidOperationException("Object manifest does not match this miss000 reference.");
            return info;
        }

        internal void LogReadiness()
        {
            Debug.Log("Mission object reference seeds: source=" + seedCount + "; selected=" + selectedCount +
                      "; source_constructors_executed=0");
            Debug.Log("Mission object reference setup: player=" + setup.SelectedSide + "," + setup.SelectedPlayer +
                      "; source_saved_origin=" + setup.SavedOriginX + "," + setup.SavedOriginY +
                      "; source_view_cells=" + setup.SourceViewWidthCells + "," + setup.SourceViewHeightCells +
                      "; diagnostic_camera_unchanged=True");
            foreach (MissionReefSeed reef in reefs)
                Debug.Log("Mission object reference reef: id=" + reef.InstanceId.ToString("x8") +
                          "; cell=" + reef.CellX + "," + reef.CellY + "; variant=" + reef.Variant);
            if (includesShips)
                for (int index = 0; index < reefs.Count; index++)
                    Debug.Log("Mission unit reference reef draw: order=" + (18 + reefs.Count - 1 - index) +
                              "; id=" + reefs[index].InstanceId.ToString("x8") + "; depth=20200");
            Debug.Log("Mission object reference ready: reefs=" + reefs.Count +
                      "; reference_state=1; frame=0; empty_collision_reference=True; simulation=False");
            shipReference?.LogReadiness();
        }

        public void Dispose()
        {
            shipReference?.Dispose();
            foreach (GameObject visual in visuals)
            {
                if (visual == null) continue;
                SpriteRenderer renderer = visual.GetComponent<SpriteRenderer>();
                if (renderer != null) { renderer.sprite = null; renderer.sharedMaterial = null; }
                UnityEngine.Object.Destroy(visual);
            }
            visuals.Clear();
            reefRenderers.Clear();
            foreach (Sprite sprite in sprites.Values)
                if (sprite != null) UnityEngine.Object.Destroy(sprite);
            sprites.Clear();
            if (atlas != null) UnityEngine.Object.Destroy(atlas);
            atlas = null;
        }

        internal IEnumerator CreateMovementReference()
        {
            if (shipReference == null) throw new InvalidOperationException("A ship overlay is required for movement.");
            return shipReference.CreateMovementReference();
        }

        internal IEnumerator CreateAdjacentReference()
        {
            if (shipReference == null) throw new InvalidOperationException("A ship overlay is required for adjacent movement.");
            return shipReference.CreateAdjacentReference();
        }

        internal IEnumerator CreateRouteReference()
        {
            if (shipReference == null) throw new InvalidOperationException("A ship overlay is required for a route.");
            return shipReference.CreateRouteReference();
        }

        internal IEnumerator CreateOrderReference()
        {
            if (shipReference == null) throw new InvalidOperationException("A ship overlay is required for move orders.");
            return shipReference.CreateOrderReference();
        }

        internal IEnumerator CreatePickingReference()
        {
            if (shipReference == null) throw new InvalidOperationException("A ship overlay is required for picking.");
            return shipReference.CreatePickingReference();
        }

        internal IEnumerator CreateFleetMotionReference()
        {
            if(shipReference==null)throw new InvalidOperationException("A ship overlay is required for fleet motion.");
            return shipReference.CreateFleetMotionReference();
        }

        internal IEnumerator CreatePointerReference(int originWorldX, int originWorldY)
        {
            if (shipReference == null) throw new InvalidOperationException("A ship overlay is required for mouse input.");
            return shipReference.CreatePointerReference(originWorldX, originWorldY);
        }
    }
}
