namespace AncientConquest.Simulation
{
    /// <summary>BaseSystem route visibility word; separate from physical keyboard and world state.</summary>
    public struct SourceRouteKeyVisibility
    {
        // 4ee507 initializes BaseSystem+20 to zero; default(struct) preserves that state.
        public uint Stored { get; private set; }

        // Matches 4f0066..4f008c: store the complete C45D parameter before forwarding.
        public uint Receive(uint value)
        {
            Stored = value;
            return value;
        }

        // 4f004b..4f0061, vptr59b5e4+20=4eff00: C45E re-enters C45D(0).
        // A zero stored word emits nothing; nonzero values remain raw uint until reset.
        public bool TryReset(out uint visibility)
        {
            visibility = 0;
            if (Stored == 0) return false;
            Receive(0);
            return true;
        }

        // Projection of 4ee900 ->540540/540560 ->540d20/540cc0 ->4eff00.
        // App+20 is a separate input. Route0 delivers only to registration state exactly1.
        // Rectangle17 and message14A are outside this route-visibility projection.
        public bool TryContextReset(uint applicationGate, uint registrationState, out uint visibility)
        {
            visibility = 0;
            return applicationGate == 0 && registrationState == 1 && TryReset(out visibility);
        }
    }
}
