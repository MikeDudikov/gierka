using System;
using UnityEngine;

namespace AncientConquest.Presentation
{
    /// <summary>Loads the bounded, bottom-up RGBA layers produced by the staging tools.</summary>
    internal static class RgbaResourceTexture
    {
        internal static Texture2D Load(string resource, int width, int height,
                                       FilterMode sampling = FilterMode.Bilinear)
        {
            if (width <= 0 || height <= 0 || width > 8192 || height > 8192)
                throw new ArgumentOutOfRangeException(nameof(width));
            TextAsset data = Resources.Load<TextAsset>(resource);
            if (data == null) throw new InvalidOperationException("Missing presentation data: " + resource);
            byte[] pixels = data.bytes;
            Resources.UnloadAsset(data);
            if (pixels.Length != checked(width * height * 4))
                throw new InvalidOperationException("Presentation byte count does not match dimensions: " + resource);
            var texture = new Texture2D(width, height, TextureFormat.RGBA32, false, false)
            {
                name = resource,
                filterMode = sampling,
                wrapMode = TextureWrapMode.Clamp
            };
            texture.LoadRawTextureData(pixels);
            texture.Apply(false, true);
            return texture;
        }
    }
}
