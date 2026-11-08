using System;
using System.Globalization;
using System.Security.Cryptography;
using AncientConquest.Simulation;

internal static class ShipPointerMaskProbe
{
    private static int Number(string value) => int.Parse(value, CultureInfo.InvariantCulture);
    private static byte[] Hex(string value)
    {
        byte[] raw = new byte[value.Length / 2];
        for (int i = 0; i < raw.Length; i++) raw[i] = Convert.ToByte(value.Substring(i * 2, 2), 16);
        return raw;
    }
    private static byte[][] Planes(int width, int height, byte[] raw)
    {
        int length = (width + 7) / 8 * height;
        if (raw.Length != length * 24) throw new InvalidOperationException("Probe mask input length differs.");
        byte[][] planes = new byte[24][];
        for (int i = 0; i < planes.Length; i++)
        {
            planes[i] = new byte[length];
            Buffer.BlockCopy(raw, i * length, planes[i], 0, length);
        }
        return planes;
    }
    private static string Hash(byte[] raw)
    {
        using (SHA256 sha = SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(raw)).Replace("-", "").ToLowerInvariant();
    }
    private static int guards;
    private static void Check(string name, bool value)
    {
        if (!value) throw new InvalidOperationException(name);
        guards++; Console.WriteLine("GUARD\t" + name);
    }
    private static void Throws<T>(string name, Action call) where T : Exception
    {
        bool caught = false;
        try { call(); } catch (T) { caught = true; }
        Check(name, caught);
    }
    private static void Guards()
    {
        byte[][] p = Planes(1, 1, new byte[24]);
        Throws<ArgumentOutOfRangeException>("zero-width", () => new ShipPointerMask(0, 1, p));
        Throws<ArgumentOutOfRangeException>("zero-height", () => new ShipPointerMask(1, 0, p));
        Throws<ArgumentOutOfRangeException>("oversize-width", () => new ShipPointerMask(2049, 1, p));
        Throws<ArgumentOutOfRangeException>("oversize-height", () => new ShipPointerMask(1, 2049, p));
        Throws<ArgumentNullException>("null-sequence", () => new ShipPointerMask(1, 1, null));
        Throws<ArgumentException>("wrong-count", () => new ShipPointerMask(1, 1, new byte[23][]));
        Throws<ArgumentException>("null-plane", () => new ShipPointerMask(1, 1, new byte[24][]));
        p[0] = new byte[2];
        Throws<ArgumentException>("wrong-plane-length", () => new ShipPointerMask(1, 1, p));
        p = Planes(1, 1, new byte[24]); p[0][0] = 0x80;
        ShipPointerMask mask = new ShipPointerMask(1, 1, p);
        p[0][0] = 0; p[0] = new byte[] { 0 };
        Check("owned-planes", mask.Contains(0, 0, 0, 0, 32, 0, true));
        Throws<NotSupportedException>("invalid-heading", () => mask.Contains(0, 0, 0, 0, 20, -1, true));
        Check("coarse-before-heading", mask.Contains(int.MinValue, int.MaxValue, 0, 0, 20, -1, false));
        Check("rectangle-before-heading", !mask.Contains(-1, 0, 0, 0, 20, -1, true));
        Check("turn-before-heading", ShipPointerMask.SelectMaskIndex(32, -1) == 0);
        Console.WriteLine("GUARDS\t" + guards);
    }
    private static void Main()
    {
        ShipPointerMask mask = null; string family = null; string line; int point = 0;
        while ((line = Console.ReadLine()) != null)
        {
            string[] f = line.Split('\t');
            if (f[0] == "F")
            {
                family = f[1]; int width = Number(f[2]), height = Number(f[3]);
                mask = new ShipPointerMask(width, height, Planes(width, height, Hex(f[4]))); point = 0;
            }
            else if (f[0] == "M")
            {
                int index = Number(f[1]); byte[] coverage = new byte[mask.Width * mask.Height]; int count = 0;
                for (int y = 0; y < mask.Height; y++) for (int x = 0; x < mask.Width; x++)
                    if (mask.Contains(x + 1028, y + 132, 1028, 132, 32 + index, (sbyte)(index % 8), true))
                    { coverage[y * mask.Width + x] = 1; count++; }
                Console.WriteLine("PLANE\t" + family + "\t" + index + "\t" + Hash(coverage) + "\t" + count);
            }
            else if (f[0] == "P")
            {
                bool result = mask.Contains(Number(f[3]), Number(f[4]), Number(f[5]), Number(f[6]),
                                            Number(f[1]), (sbyte)Number(f[2]), f[7] == "1");
                Console.WriteLine("POINT\t" + family + "\t" + point++ + "\t" + (result ? 1 : 0));
            }
            else throw new InvalidOperationException("Unknown probe operation.");
        }
        Guards();
    }
}
