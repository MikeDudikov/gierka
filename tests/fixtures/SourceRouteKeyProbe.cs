using System;
using System.IO;
using AncientConquest.Simulation;

internal static class SourceRouteKeyProbe
{
    // Inputs encode calls already observed in source4eff00 and source4ee900.
    private static void Main(string[] args)
    {
        SourceRouteKeyVisibility state = default;
        foreach (string line in File.ReadLines(args[0]))
        {
            string[] fields = line.Split('\t');
            if (fields[0] == "R") { state = default; continue; }
            if (fields[0] == "I") { state.Receive(uint.Parse(fields[1])); continue; }
            uint value = 0;
            bool forwarded;
            if (fields[0] == "M")
            {
                if (uint.Parse(fields[1]) == 0xc45d)
                { value = state.Receive(uint.Parse(fields[2])); forwarded = true; }
                else if (uint.Parse(fields[1]) == 0xc45e) forwarded = state.TryReset(out value);
                else throw new InvalidDataException("Unsupported bounded source key message.");
            }
            else if (fields[0] == "C")
                forwarded = state.TryContextReset(uint.Parse(fields[1]), uint.Parse(fields[2]), out value);
            else throw new InvalidDataException("Unknown source probe operation.");
            Console.WriteLine(state.Stored + "\t" + (forwarded ? 1 : 0) + "\t" + value);
        }
    }
}
