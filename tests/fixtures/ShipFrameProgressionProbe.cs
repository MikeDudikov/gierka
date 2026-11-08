using System;
using AncientConquest.Simulation;

public static class ShipFrameProgressionProbe
{
    public static int Main()
    {
        string line;
        while ((line = Console.ReadLine()) != null)
        {
            string[] fields = line.Split('\t');
            if (fields.Length != 5)
                throw new Exception("Invalid ship frame progression input.");
            ShipFrameProgression.Result result = ShipFrameProgression.AdvanceForward(
                int.Parse(fields[0]), sbyte.Parse(fields[1]), uint.Parse(fields[2]),
                uint.Parse(fields[3]), uint.Parse(fields[4]));
            Console.WriteLine(result.Frame + "\t" + result.LastTick);
        }
        return 0;
    }
}
