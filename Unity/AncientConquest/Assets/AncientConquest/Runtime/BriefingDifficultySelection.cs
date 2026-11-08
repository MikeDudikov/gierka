using System;

namespace AncientConquest.Presentation
{
    /// <summary>
    /// Pointer selection subset of the original type-5 TabClassTy at 0x550ba0.
    /// The briefing selects an icon on left down; labels and release do not select.
    /// </summary>
    public sealed class BriefingDifficultySelection
    {
        private readonly int[] rectangles = new int[12];
        public int SelectedDifficulty { get; private set; }

        public BriefingDifficultySelection(int selectedDifficulty, int[][] nativeRects)
        {
            if (selectedDifficulty < 0 || selectedDifficulty > 2)
                throw new ArgumentOutOfRangeException(nameof(selectedDifficulty));
            if (nativeRects == null || nativeRects.Length != 3)
                throw new ArgumentException("Three difficulty icon rectangles are required.", nameof(nativeRects));
            for (int index = 0; index < 3; index++)
            {
                int[] rect = nativeRects[index];
                if (rect == null || rect.Length != 4 || rect[0] < 0 || rect[1] < 0 ||
                    rect[2] <= 0 || rect[3] <= 0 ||
                    rect[0] > int.MaxValue - rect[2] || rect[1] > int.MaxValue - rect[3])
                    throw new ArgumentException("Difficulty icon geometry is invalid.", nameof(nativeRects));
                Array.Copy(rect, 0, rectangles, index * 4, 4);
            }
            SelectedDifficulty = selectedDifficulty;
        }

        /// <returns>True only when a different icon is selected on left down.</returns>
        public bool Process(int message, int x, int y)
        {
            if (message != 0x61) return false;
            for (int index = 0; index < 3; index++)
            {
                int offset = index * 4;
                if (index != SelectedDifficulty && x >= rectangles[offset] &&
                    x < rectangles[offset] + rectangles[offset + 2] &&
                    y >= rectangles[offset + 1] &&
                    y < rectangles[offset + 1] + rectangles[offset + 3])
                {
                    SelectedDifficulty = index;
                    return true;
                }
            }
            return false;
        }
    }
}
