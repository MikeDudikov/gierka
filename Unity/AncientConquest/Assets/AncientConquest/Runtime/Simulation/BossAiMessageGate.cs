namespace AncientConquest.Simulation
{
    // Isolated dispatch rule extracted from original ancient.exe 0x00448d40.
    // Counter units and parent/decision side effects are not modeled here.
    public static class BossAiMessageGate
    {
        public const uint ForcedEvaluationMessage = 0x000d8fd7u;
        public const uint CounterDivisor = 250u;

        public static bool RequestsEvaluation(uint messageId, uint sourceCounter)
        {
            return messageId == ForcedEvaluationMessage ||
                   (messageId == 0u && sourceCounter % CounterDivisor == 0u);
        }

        public static bool ClearsSharedFlag(uint messageId)
        {
            return messageId == 2u;
        }
    }
}
