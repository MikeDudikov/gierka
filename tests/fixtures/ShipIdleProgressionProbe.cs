using System;
using System.Globalization;
using AncientConquest.Simulation;

internal static class ShipIdleProgressionProbe
{
    private static int I(string s) { return int.Parse(s, CultureInfo.InvariantCulture); }
    private static uint U(string s) { return uint.Parse(s, CultureInfo.InvariantCulture); }
    public static void Main()
    {
        string line;
        while ((line = Console.ReadLine()) != null)
        {
            string[] f = line.Split('\t');
            if (f[0] == "SEED")
            {
                Console.WriteLine("SEED\t" + ShipIdleProgression.InitialRandomState(U(f[1]), U(f[2])));
                continue;
            }
            var r = ShipIdleProgression.Advance(I(f[0]), (sbyte)I(f[1]), (sbyte)I(f[2]),
                U(f[3]), U(f[4]), U(f[5]), U(f[6]), I(f[7]), I(f[8]), I(f[9]));
            Console.WriteLine(string.Join("\t", r.Frame, r.FrameStep, r.LastTick, r.Interval,
                r.RandomState, r.Speed, r.ReservedCellIndex, r.ReleasedCellIndex,
                r.PublishesPose ? 1 : 0, r.PublishesPose ? r.PublishedFrame : 0));
        }
    }
}
