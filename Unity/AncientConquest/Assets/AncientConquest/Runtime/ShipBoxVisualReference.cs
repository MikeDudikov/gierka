using System;
using System.Collections.Generic;
using AncientConquest.Simulation;
using UnityEngine;

namespace AncientConquest.Presentation
{
    /// <summary>Point-sampled source palette201 rectangle, clipped to the normal map view.</summary>
    internal sealed class ShipBoxVisualReference : IDisposable
    {
        private readonly List<ShipBoxSpan> spans = new List<ShipBoxSpan>();
        private readonly List<Vector3> vertices = new List<Vector3>();
        private readonly List<Vector2> uv = new List<Vector2>();
        private readonly List<Color32> colors = new List<Color32>();
        private readonly List<int> indices = new List<int>();
        private readonly int originX, originY;
        private GameObject root;
        private Mesh mesh;
        private MeshRenderer renderer;
        private Material material;
        private Texture2D texture;
        private bool disposed;
        private int x, y, width, height, phase = -1;
        internal ShipBoxVisualReference(Transform parent, Material source, int originX, int originY)
        {
            this.originX = originX; this.originY = originY;
            try
            {
                root = new GameObject("Source normal-map box outline (depth5)");
                root.transform.SetParent(parent, false);
                mesh = new Mesh { name = "Source clipped box spans" }; mesh.MarkDynamic();
                root.AddComponent<MeshFilter>().sharedMesh = mesh;
                texture = new Texture2D(1, 1, TextureFormat.RGBA32, false, false)
                    { name = "Source palette201", filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp };
                texture.SetPixel(0, 0, new Color32(0, 174, 0, 255)); texture.Apply(false, true);
                material = new Material(source) { name = "Source box point material" };
                material.mainTexture = texture;
                renderer = root.AddComponent<MeshRenderer>(); renderer.sharedMaterial = material;
                renderer.sortingOrder = 46; renderer.enabled = false;
            }
            catch { Dispose(); throw; }
        }
        internal void SetSortingOrder(int value) { renderer.sortingOrder = value; }
        internal void Apply(ShipBoxGesture box)
        {
            if (disposed) throw new ObjectDisposedException(nameof(ShipBoxVisualReference));
            renderer.enabled = box.Visible;
            if (!box.Visible || (phase == box.Phase && x == box.StartX && y == box.StartY &&
                width == box.Width && height == box.Height)) return;
            x = box.StartX; y = box.StartY; width = box.Width; height = box.Height; phase = box.Phase;
            ShipBoxOutline.Build(spans, x, y, width, height, phase, originX, originY, 960, 540);
            vertices.Clear(); uv.Clear(); colors.Clear(); indices.Clear();
            foreach (ShipBoxSpan span in spans)
            {
                int n = vertices.Count;
                vertices.Add(new Vector3(span.X, -span.Y, 0));
                vertices.Add(new Vector3(span.X + span.Width, -span.Y, 0));
                vertices.Add(new Vector3(span.X + span.Width, -span.Y - span.Height, 0));
                vertices.Add(new Vector3(span.X, -span.Y - span.Height, 0));
                for (int i = 0; i < 4; i++) { uv.Add(new Vector2(.5f, .5f)); colors.Add(new Color32(255,255,255,255)); }
                indices.Add(n); indices.Add(n + 1); indices.Add(n + 2);
                indices.Add(n); indices.Add(n + 2); indices.Add(n + 3);
            }
            mesh.Clear(); mesh.SetVertices(vertices); mesh.SetUVs(0, uv); mesh.SetColors(colors);
            mesh.SetTriangles(indices, 0); mesh.RecalculateBounds();
        }
        public void Dispose()
        {
            if (disposed) return; disposed = true;
            if (renderer != null) renderer.sharedMaterial = null;
            if (root != null) UnityEngine.Object.Destroy(root);
            if (mesh != null) UnityEngine.Object.Destroy(mesh);
            if (material != null) UnityEngine.Object.Destroy(material);
            if (texture != null) UnityEngine.Object.Destroy(texture);
        }
    }
}
