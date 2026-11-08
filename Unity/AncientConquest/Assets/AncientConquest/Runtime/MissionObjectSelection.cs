using System;

namespace AncientConquest.World
{
    /// <summary>Source CreateSystemObjects filter and factory-code dispatch only; no constructors run.</summary>
    public static class MissionObjectSelection
    {
        public static bool TrySelect(MissionObjectSeed seed, byte[] players, out int factoryType)
        {
            if (seed == null) throw new ArgumentNullException(nameof(seed));
            if (players == null || players.Length != 20)
                throw new ArgumentException("PLAYERS_DESC needs five rows of four bytes.", nameof(players));
            factoryType = 0;
            if (seed.Kind == 1)
            {
                // Malformed source indices are rejected at this adapter boundary.
                // The original indexes raw memory; those inputs are not gameplay cases.
                if (seed.SideIndex >= 5 || seed.PlayerIndex >= 4)
                    throw new ArgumentOutOfRangeException(nameof(seed), "Player-owned seed has an invalid slot.");
                if (players[seed.SideIndex * 4 + seed.PlayerIndex] == 0) return false;
            }
            uint tag = seed.ClassTag;
            if (tag >= 200 && tag <= 211) { factoryType = 5256; return true; }
            switch (tag)
            {
                case 50: case 51: factoryType = 5265; break;
                case 52: case 53: case 54: factoryType = 5268; break;
                case 55: factoryType = 5266; break;
                case 56: factoryType = 5267; break;
                case 57: factoryType = 5275; break;
                case 58: case 59: factoryType = 5276; break;
                case 60: factoryType = 5277; break;
                case 61: factoryType = 5278; break;
                case 62: factoryType = 5279; break;
                case 63: case 64: case 65: factoryType = 6763; break;
                case 66: case 67: factoryType = 6764; break;
                case 68: case 69: factoryType = 6762; break;
                case 70: factoryType = 5270; break;
                case 71: factoryType = 5274; break;
                case 72: factoryType = 5775; break;
                case 73: factoryType = 6765; break;
                case 300: factoryType = 5306; break;
                case 400: factoryType = 5758; break;
                case 401: factoryType = 5756; break;
                case 402: factoryType = 5757; break;
                case 500: case 501: case 502: factoryType = 5271; break;
                case 503: factoryType = 5272; break;
                case 504: case 505: factoryType = 6761; break;
                case 506: factoryType = 5856; break;
                case 507: factoryType = 5760; break;
                case 508: factoryType = 6759; break;
                case 509: factoryType = 5860; break;
                case 600: factoryType = 6755; break;
                case 601: case 602: factoryType = 6756; break;
                case 603: factoryType = 6758; break;
                case 604: factoryType = 6760; break;
                case 605: factoryType = 5857; break;
                case 606: factoryType = 6165; break;
                case 700: factoryType = 5859; break;
                case 702: factoryType = 5855; break;
                case 703: factoryType = 5776; break;
                case 705: factoryType = 5858; break;
                default: return false;
            }
            return true;
        }
    }
}
