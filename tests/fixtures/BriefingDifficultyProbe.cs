using System;
using AncientConquest.Presentation;

internal static class BriefingDifficultyProbe
{
    private static int[][] Rectangles()
    {
        return new[] { new[] {660,440,23,23}, new[] {660,470,23,23}, new[] {660,500,23,23} };
    }

    private static void Reject(Action action)
    {
        try { action(); }
        catch (ArgumentException) { return; }
        throw new Exception("Invalid difficulty configuration was accepted.");
    }

    private static void CheckConfigurationBoundary()
    {
        Reject(() => new BriefingDifficultySelection(-1, Rectangles()));
        Reject(() => new BriefingDifficultySelection(3, Rectangles()));
        Reject(() => new BriefingDifficultySelection(0, null));
        Reject(() => new BriefingDifficultySelection(0, new[] {new[] {0,0,1,1}}));
        int[][] rects = Rectangles(); rects[0] = null;
        Reject(() => new BriefingDifficultySelection(0, rects));
        rects = Rectangles(); rects[0] = new[] {0,0,1};
        Reject(() => new BriefingDifficultySelection(0, rects));
        rects = Rectangles(); rects[0][0] = -1;
        Reject(() => new BriefingDifficultySelection(0, rects));
        rects = Rectangles(); rects[0][2] = 0;
        Reject(() => new BriefingDifficultySelection(0, rects));
        rects = Rectangles(); rects[0][0] = int.MaxValue;
        Reject(() => new BriefingDifficultySelection(0, rects));
        rects = Rectangles();
        var selection = new BriefingDifficultySelection(0, rects);
        rects[1][0] = 100;
        if (!selection.Process(0x61,670,480) || selection.SelectedDifficulty != 1)
            throw new Exception("Caller mutation changed owned icon geometry.");
        Console.Error.WriteLine("10 C# configuration-boundary checks passed");
    }

    private static void Main()
    {
        CheckConfigurationBoundary();
        BriefingDifficultySelection selection = null;
        string line;
        while ((line = Console.ReadLine()) != null)
        {
            if (line.Length == 0) continue;
            string[] fields = line.Split('\t');
            if (fields.Length != 17) throw new Exception("Invalid probe row.");
            int[] values = Array.ConvertAll(fields, int.Parse);
            if (values[0] != 0)
            {
                var rects = new int[3][];
                for (int index = 0; index < 3; index++)
                    rects[index] = new[] {values[2+index*4], values[3+index*4],
                                          values[4+index*4], values[5+index*4]};
                selection = new BriefingDifficultySelection(values[1], rects);
            }
            if (selection == null) throw new Exception("Probe must begin with a reset.");
            bool changed = selection.Process(values[14], values[15], values[16]);
            Console.WriteLine(selection.SelectedDifficulty + "\t" + (changed ? "1" : "0"));
        }
    }
}
