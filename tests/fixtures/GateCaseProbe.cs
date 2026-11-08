using System;
using AncientConquest.Simulation;

public static class GateCaseProbe
{
    public static int Main()
    {
        uint[] counters = {0u, 1u, 249u, 250u, 251u, 500u, uint.MaxValue};
        uint[] messages = {0u, BossAiMessageGate.ForcedEvaluationMessage, 2u, 1u, uint.MaxValue};
        foreach (uint counter in counters)
            foreach (uint message in messages)
                Console.WriteLine(message + "\t" + counter + "\t" +
                    (BossAiMessageGate.RequestsEvaluation(message, counter) ? 1 : 0) + "\t" +
                    (BossAiMessageGate.ClearsSharedFlag(message) ? 1 : 0));
        return 0;
    }
}
