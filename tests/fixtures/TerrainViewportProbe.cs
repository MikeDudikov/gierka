using System;
using AncientConquest;

public static class TerrainViewportProbe
{
    public static int Main()
    {
        string line;
        while ((line = Console.ReadLine()) != null)
        {
            string[] fields = line.Split('\t');
            if (fields[0] == "C" && fields.Length == 7)
            {
                Console.WriteLine(TerrainViewport.ClampAxis(int.Parse(fields[1]),
                    int.Parse(fields[2]), int.Parse(fields[3])) + "\t" +
                    TerrainViewport.ClampAxis(int.Parse(fields[4]),
                    int.Parse(fields[5]), int.Parse(fields[6])));
            }
            else if (fields[0] == "P" && fields.Length == 10)
            {
                int tile = int.Parse(fields[5]);
                Console.WriteLine(TerrainViewport.CellToScreen(int.Parse(fields[1]),
                    int.Parse(fields[3]), tile, int.Parse(fields[6]), int.Parse(fields[8])) + "\t" +
                    TerrainViewport.CellToScreen(int.Parse(fields[2]),
                    int.Parse(fields[4]), tile, int.Parse(fields[7]), int.Parse(fields[9])));
            }
            else throw new Exception("Invalid terrain geometry probe input.");
        }
        return 0;
    }
}
