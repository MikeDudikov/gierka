using System;
using AncientConquest.Simulation;

public static class ShipTurnProgressionProbe
{
    public static int Main()
    {
        string line;
        while ((line = Console.ReadLine()) != null)
        {
            string[] fields = line.Split('\t');
            if (fields.Length != 10)
                throw new Exception("Invalid ship turn progression input.");
            ShipTurnProgression.Result result = ShipTurnProgression.Advance(
                int.Parse(fields[0]), sbyte.Parse(fields[1]), sbyte.Parse(fields[2]), sbyte.Parse(fields[3]),
                uint.Parse(fields[4]), uint.Parse(fields[5]), uint.Parse(fields[6]), fields[7] == "1",
                byte.Parse(fields[8]), byte.Parse(fields[9]));
            Console.WriteLine(result.Frame + "\t" + result.Heading + "\t" + result.TurnStep + "\t" +
                result.LastTick + "\t" + result.State + "\t" + result.ChangedMarker + "\t" +
                (result.PublishesPose ? "1" : "0"));
        }
        return 0;
    }
}
