namespace AncientConquest
{
    /// <summary>
    /// Isolated integer geometry from ancient.exe, not a camera controller.
    /// The caller supplies the viewport size and presentation scale.
    /// </summary>
    public static class TerrainViewport
    {
        /// <summary>
        /// DrawMapaXY (0x00519f3d..0x00519f92): lower bound first, then
        /// mapCells - viewCells. mapCells is the sign-extended original map
        /// header word. An oversized view can intentionally return a negative
        /// origin. This excludes the routine's unchanged-position early return,
        /// redraw, and other state changes.
        /// </summary>
        public static int ClampAxis(int requested, int mapCells, int viewCells)
        {
            unchecked
            {
                if (requested < 0) requested = 0;
                int maximum = mapCells - viewCells;
                return requested > maximum ? maximum : requested;
            }
        }

        /// <summary>
        /// DrawCellBig (0x005196e0..0x0051972c): map-cell coordinate to original
        /// screen pixels on either axis. Subtraction, multiplication, and both
        /// additions wrap to 32 bits, as in x86. Display scaling is separate.
        /// </summary>
        public static int CellToScreen(int cell, int origin, int tilePixels,
                                       int subOffset, int frameOffset)
        {
            unchecked
            {
                return (cell - origin) * tilePixels + subOffset + frameOffset;
            }
        }
    }
}
