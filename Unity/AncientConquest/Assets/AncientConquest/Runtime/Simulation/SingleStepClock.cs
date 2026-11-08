using System;

namespace AncientConquest.Simulation
{
    /// <summary>
    /// The isolated time-quantum branch at ancient.exe 0x00520352, not the
    /// complete game clock. The caller must establish the original branch's
    /// mode conditions before using it; this class has no Unity time source.
    /// </summary>
    public static class SingleStepClock
    {
        public readonly struct StartResult
        {
            public bool StepRequested { get; }
            public uint Counter { get; }

            internal StartResult(bool stepRequested, uint counter)
            {
                StepRequested = stepRequested;
                Counter = counter;
            }
        }

        /// <summary>
        /// Begin one branch iteration. A nonzero signed quotient requests
        /// exactly one step, including a negative quotient: the original
        /// clamps through an unsigned comparison after signed IDIV.
        /// </summary>
        public static StartResult Begin(int capturedTime, int previousTime,
                                        uint counter, int quantum)
        {
            if (quantum <= 0) throw new ArgumentOutOfRangeException(nameof(quantum));
            unchecked
            {
                int elapsed = capturedTime - previousTime;
                bool requested = elapsed / quantum != 0;
                return new StartResult(requested, requested ? counter + 1u : counter);
            }
        }

        /// <summary>
        /// Complete only a requested step, after the original world/base
        /// callbacks. Pass their current phase and quantum, since x86 reads
        /// them again here. Signed remainder and 32-bit wrapping are intentional.
        /// </summary>
        public static int Complete(int capturedTime, int currentPreviousTime,
                                   int currentQuantum)
        {
            if (currentQuantum <= 0)
                throw new ArgumentOutOfRangeException(nameof(currentQuantum));
            unchecked
            {
                int remainder = (capturedTime - currentPreviousTime - currentQuantum) % currentQuantum;
                return capturedTime - remainder;
            }
        }
    }
}
