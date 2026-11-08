using System;
using System.Collections.Generic;
using UnityEngine;

namespace AncientConquest.Presentation
{
    /// <summary>Owned A/H pose atlas;source0b/0c share A and source0d retains its armor layer.</summary>
    internal sealed class SourceShipPoseReference : IDisposable
    {
        private const string ResourceRoot = "ShipMovementGenerated/";
        [Serializable] private sealed class Plane
        {
            public string name = null;
            public int atlas_x = 0, atlas_y = 0, width = 0, height = 0;
        }
        [Serializable] private sealed class Part
        {
            public string name = null;
            public int source_index = 0, offset_x = 0, offset_y = 0, depth = 0;
        }
        [Serializable] private sealed class Pose
        {
            public int frame_index = 0, logical_width = 0, logical_height = 0;
            public int[] inline_draw_order = null;
            public Part[] components = null;
        }
        [Serializable] private sealed class Manifest
        {
            public int schema_version = 0, instance_id = 0, component_mask = 0;
            public int native_canvas_width = 0, native_canvas_height = 0;
            public int pose_count = 0, plane_count = 0, atlas_width = 0, atlas_height = 0;
            public string mission = null, atlas_coordinate_origin = null;
            public Plane[] planes = null;
            public Pose[] poses = null;
        }

        private readonly Dictionary<string, Sprite> sprites = new Dictionary<string, Sprite>(StringComparer.Ordinal);
        private readonly Dictionary<int, SpriteRenderer> renderers;
        private readonly Manifest manifest;
        private Texture2D atlas;
        private bool disposed;
        internal int DrawnFrame { get; private set; } = -1;
        internal int WorldPixelX { get; private set; }
        internal int WorldPixelY { get; private set; }

        internal SourceShipPoseReference(Dictionary<int, SpriteRenderer> sourceRenderers)
            : this(sourceRenderers,false) { }

        internal SourceShipPoseReference(Dictionary<int, SpriteRenderer> sourceRenderers,bool heavy)
        {
            int size=heavy?72:56,planeCount=heavy?224:152;
            int[] expectedIndices=heavy?new[]{0,1,5,7}:new[]{0,1,7};
            int[] expectedDepths=heavy?new[]{-21000,10,5,4}:new[]{-21000,10,4};
            int[] inline=heavy?new[]{1,5,7}:new[]{1,7};
            string root=heavy?"ShipHeavyMovementGenerated/":ResourceRoot;
            string manifestName=heavy?"ShipHeavyMovementManifest":"ShipMovementManifest";
            renderers = new Dictionary<int, SpriteRenderer>(sourceRenderers);
            if (renderers.Count != expectedIndices.Length)
                throw new InvalidOperationException("The source profile needs all selected component renderers.");
            foreach(int index in expectedIndices)
                if(!renderers.ContainsKey(index))throw new InvalidOperationException("A selected source component is missing.");
            foreach (SpriteRenderer renderer in renderers.Values)
                if (renderer == null) throw new InvalidOperationException("A source0b renderer is missing.");
            try
            {
                TextAsset asset = Resources.Load<TextAsset>(root + manifestName);
                if (asset == null) throw new InvalidOperationException("Stage verified source ship poses first.");
                try { manifest = JsonUtility.FromJson<Manifest>(asset.text); }
                finally { Resources.UnloadAsset(asset); }
                if (manifest == null || manifest.schema_version != 1 || manifest.mission != "miss000" ||
                    manifest.instance_id != (heavy?13:11) || manifest.component_mask != (heavy?0xa3:0x83) ||
                    manifest.native_canvas_width != NativeMenuCanvas.Width ||
                    manifest.native_canvas_height != NativeMenuCanvas.Height ||
                    manifest.pose_count != 88 || manifest.plane_count != planeCount ||
                    manifest.atlas_width != (heavy?2304:2128) || manifest.atlas_height != (heavy?504:224) ||
                    manifest.atlas_coordinate_origin != "bottom-left" ||
                    manifest.planes == null || manifest.planes.Length != planeCount ||
                    manifest.poses == null || manifest.poses.Length != 88)
                    throw new InvalidOperationException("Ship pose manifest differs from the bounded source recipe.");
                atlas = RgbaResourceTexture.Load(root + (heavy?"ShipHeavyMovementRgba":"ShipMovementRgba"), manifest.atlas_width,
                                                manifest.atlas_height, FilterMode.Point);
                foreach (Plane plane in manifest.planes)
                {
                    if (plane == null || string.IsNullOrEmpty(plane.name) || sprites.ContainsKey(plane.name) ||
                        plane.width != size || plane.height != size || plane.atlas_x < 0 || plane.atlas_y < 0 ||
                        plane.atlas_x + plane.width > atlas.width || plane.atlas_y + plane.height > atlas.height)
                        throw new InvalidOperationException("A source ship plane extends outside its atlas.");
                    Sprite sprite = Sprite.Create(atlas,
                        new Rect(plane.atlas_x, plane.atlas_y, plane.width, plane.height),
                        new Vector2(0, 1), 1, 0, SpriteMeshType.FullRect);
                    sprite.name = plane.name;
                    sprites.Add(plane.name, sprite);
                }
                for (int index = 0; index < manifest.poses.Length; index++)
                {
                    Pose pose = manifest.poses[index];
                    if (pose == null || pose.frame_index != index || pose.logical_width != size || pose.logical_height != size ||
                        pose.components == null || pose.components.Length != expectedIndices.Length ||
                        pose.inline_draw_order == null || pose.inline_draw_order.Length != inline.Length)
                        throw new InvalidOperationException("Invalid source ship pose geometry or inline order.");
                    for(int i=0;i<inline.Length;i++)
                        if(pose.inline_draw_order[i]!=inline[i])throw new InvalidOperationException("Source inline part order differs.");
                    for (int partIndex = 0; partIndex < expectedIndices.Length; partIndex++)
                    {
                        Part part = pose.components[partIndex];
                        if (part == null || part.source_index != expectedIndices[partIndex] ||
                            part.depth != expectedDepths[partIndex] || part.offset_x != 0 || part.offset_y != 0 ||
                            !sprites.ContainsKey(part.name))
                            throw new InvalidOperationException("Source ship pose component differs from its proven recipe.");
                    }
                }
            }
            catch { Dispose(); throw; }
        }

        internal void Apply(int frame, int worldX, int worldY)
        {
            if (disposed) throw new ObjectDisposedException(nameof(SourceShipPoseReference));
            if (frame < 0 || frame >= manifest.poses.Length)
                throw new ArgumentOutOfRangeException(nameof(frame));
            foreach (Part part in manifest.poses[frame].components)
            {
                SpriteRenderer renderer = renderers[part.source_index];
                renderer.sprite = sprites[part.name];
                renderer.transform.localPosition = new Vector3(worldX + part.offset_x, -worldY - part.offset_y, 0);
            }
            DrawnFrame = frame; WorldPixelX = worldX; WorldPixelY = worldY;
        }

        public void Dispose()
        {
            if (disposed) return;
            disposed = true;
            foreach (SpriteRenderer renderer in renderers.Values)
                if (renderer != null && renderer.sprite != null && renderer.sprite.texture == atlas)
                    renderer.sprite = null;
            foreach (Sprite sprite in sprites.Values)
                if (sprite != null) UnityEngine.Object.Destroy(sprite);
            sprites.Clear();
            if (atlas != null) UnityEngine.Object.Destroy(atlas);
            atlas = null;
        }
    }
}
