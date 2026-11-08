using System;

namespace AncientConquest.Presentation
{
    /// <summary>The game UI is authored on the requested full native 16:9 canvas.</summary>
    public readonly struct NativeMenuCanvas
    {
        public const int Width = 1920;
        public const int Height = 1080;
        public double X => 0;
        public double Y => 0;
        public double ScreenWidth { get; }
        public double ScreenHeight { get; }
        private NativeMenuCanvas(int width, int height)
        {
            ScreenWidth = width;
            ScreenHeight = height;
        }
        public static NativeMenuCanvas FullScreen(int width, int height)
        {
            if (width <= 0) throw new ArgumentOutOfRangeException(nameof(width));
            if (height <= 0) throw new ArgumentOutOfRangeException(nameof(height));
            return new NativeMenuCanvas(width, height);
        }
    }
}
