using System;
using AncientConquest.Simulation;

public static class SingleStepClockProbe
{
    private static void RequiresPositiveQuantum(Action operation)
    {
        try { operation(); }
        catch (ArgumentOutOfRangeException) { return; }
        throw new Exception("Expected ArgumentOutOfRangeException for a nonpositive quantum.");
    }

    public static int Main()
    {
        RequiresPositiveQuantum(() => SingleStepClock.Begin(0, 0, 0, 0));
        RequiresPositiveQuantum(() => SingleStepClock.Begin(0, 0, 0, -1));
        RequiresPositiveQuantum(() => SingleStepClock.Complete(0, 0, 0));
        RequiresPositiveQuantum(() => SingleStepClock.Complete(0, 0, -1));
        string line;
        while ((line = Console.ReadLine()) != null)
        {
            string[] fields = line.Split('\t');
            if (fields.Length != 6) throw new Exception("Invalid clock probe input.");
            int now = int.Parse(fields[0]);
            int previous = int.Parse(fields[1]);
            uint counter = uint.Parse(fields[2]);
            int quantum = int.Parse(fields[3]);
            int phaseAfterCallbacks = int.Parse(fields[4]);
            int quantumAfterCallbacks = int.Parse(fields[5]);
            SingleStepClock.StartResult start = SingleStepClock.Begin(now, previous, counter, quantum);
            int phase = start.StepRequested
                ? SingleStepClock.Complete(now, phaseAfterCallbacks, quantumAfterCallbacks)
                : previous;
            Console.WriteLine((start.StepRequested ? 1 : 0) + "\t" + start.Counter + "\t" + phase);
        }
        return 0;
    }
}
