using System;

namespace AncientConquest.Presentation
{
    /// <summary>
    /// Pointer subset of the original type-1 ButtonClassTy (0x54aab0).
    /// Coordinates are integers on the native canvas; no gameplay state lives here.
    /// </summary>
    public sealed class MainMenuButton
    {
        public const int Move = 0x60;
        public const int LeftDown = 0x61;
        public const int LeftUp = 0x62;
        public int State { get; private set; }
        public bool Pressed { get; private set; }
        public bool Hovered { get; private set; }
        public bool Inside { get; private set; }
        public int X { get; }
        public int Y { get; }
        public int Width { get; }
        public int Height { get; }

        public MainMenuButton(int x, int y, int width, int height, bool enabled = true)
        {
            if (x < 0 || y < 0 || width <= 0 || height <= 0 ||
                x > int.MaxValue - width || y > int.MaxValue - height)
                throw new ArgumentOutOfRangeException(nameof(width));
            X = x;
            Y = y;
            Width = width;
            Height = height;
            State = enabled ? 1 : 0;
        }

        /// <returns>True only when the original release rule emits a command.</returns>
        public bool Process(int message, int x, int y)
        {
            bool inside = x >= X && x < X + Width && y >= Y && y < Y + Height;
            if (message == Move) Inside = inside;
            if (State == 0) return false;
            switch (message)
            {
                case Move:
                    if (inside)
                    {
                        if (!Hovered)
                        {
                            State = 3;
                            Hovered = true;
                        }
                        Inside = true;
                    }
                    else if (Pressed || Hovered || Inside)
                    {
                        State = 1;
                        Hovered = false;
                        Pressed = false;
                        Inside = false;
                    }
                    // The original pre-pass updates Inside before the branch.
                    // A previous Inside without hover/press requires no redraw.
                    break;
                case LeftDown:
                    if (inside)
                    {
                        Inside = true;
                        if (!Pressed)
                        {
                            State = 2;
                            Pressed = true;
                        }
                    }
                    break;
                case LeftUp:
                    // Deliberately inclusive: the original differs from down/move.
                    if (Pressed && x >= X && x <= X + Width && y >= Y && y <= Y + Height)
                    {
                        State = Inside ? 3 : 1;
                        Pressed = false;
                        return true;
                    }
                    break;
            }
            return false;
        }

        /// <summary>Host adapter policy: focus loss must not leave a held click.</summary>
        public void CancelPointer()
        {
            if (State != 0) State = 1;
            Pressed = false;
            Hovered = false;
            Inside = false;
        }
    }
}
