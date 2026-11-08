using System;
using System.Collections.Generic;
using AncientConquest.Simulation;

class SourceFleetFormationProbe
{
    private static short[] Decode(string value)
    {
        byte[] bytes = Convert.FromBase64String(value);
        var words = new short[bytes.Length / 2];
        Buffer.BlockCopy(bytes, 0, words, 0, bytes.Length);
        return words;
    }
    private static string Encode(short[] words)
    {
        var bytes = new byte[words.Length * 2];
        Buffer.BlockCopy(words, 0, bytes, 0, bytes.Length);
        return Convert.ToBase64String(bytes);
    }
    private static int controls;
    private static void Check(bool value) { if (!value) throw new Exception("API control failed " + controls); controls++; }
    private static void Reject<T>(Action action) where T : Exception
    {
        try { action(); } catch (T) { controls++; return; }
        throw new Exception("Expected " + typeof(T).Name);
    }
    private static void Api()
    {
        var cells = new[] { new SourceFleetFormation.Cell(0, 0), new SourceFleetFormation.Cell(2, 0) };
        var map = new short[9];
        Reject<ArgumentNullException>(() => SourceFleetFormation.Assign(null, 3, 3, cells, 1, 1));
        Reject<ArgumentNullException>(() => SourceFleetFormation.Assign(map, 3, 3, null, 1, 1));
        Reject<ArgumentException>(() => SourceFleetFormation.Assign(map, 0, 3, cells, 1, 1));
        Reject<ArgumentException>(() => SourceFleetFormation.Assign(map, 2, 3, cells, 1, 1));
        Reject<ArgumentOutOfRangeException>(() => SourceFleetFormation.Assign(map, 3, 3, new SourceFleetFormation.Cell[1], 1, 1));
        Reject<ArgumentOutOfRangeException>(() => SourceFleetFormation.Assign(map, 3, 3, new SourceFleetFormation.Cell[9], 1, 1));
        var invalidCells = new[] { new SourceFleetFormation.Cell(-1, 0), cells[1] };
        Reject<ArgumentOutOfRangeException>(() => SourceFleetFormation.Assign(map, 3, 3, invalidCells, 1, 1));
        map[4] = 2;
        Reject<NotSupportedException>(() => SourceFleetFormation.Assign(map, 3, 3, cells, 1, 1));
        map[4] = 0;
        var result = SourceFleetFormation.Assign(map, 3, 3, cells, 1, 1);
        Check(result.Succeeded && result.Count == 2 && result.FieldCount == 3);
        Check(Array.TrueForAll(map, value => value == 0));
        string reserved = Encode(result.CaptureReservedField()), field = Encode(result.CaptureField(0));
        short[] capture = result.CaptureReservedField(); capture[0] = 123;
        Check(reserved == Encode(result.CaptureReservedField()));
        capture = result.CaptureField(0); capture[0] = 123;
        Check(field == Encode(result.CaptureField(0)));
        var target = result.GetTarget(0);
        cells[0] = new SourceFleetFormation.Cell(2, 2); map[0] = -1;
        Check(result.GetTarget(0).X == target.X && result.GetTarget(0).Y == target.Y && reserved == Encode(result.CaptureReservedField()));
        result = SourceFleetFormation.Assign(new short[9], 3, 3, cells, -1, 0);
        Check(!result.Succeeded && result.SourceCode == -4 && result.FieldCount == 0);
        Reject<ArgumentNullException>(() => SourceWaveField.FillAll(null, 1, 1, 0, 0));
        Reject<ArgumentException>(() => SourceWaveField.FillAll(new short[2], 1, 1, 0, 0));
        Reject<ArgumentOutOfRangeException>(() => SourceWaveField.FillAll(new short[1], 1, 1, 1, 0));
        Reject<NotSupportedException>(() => SourceWaveField.FillAll(new short[] { 2 }, 1, 1, 0, 0));
        var blocked = new short[] { -1 }; SourceWaveField.FillAll(blocked, 1, 1, 0, 0);
        Check(blocked[0] == 1);
        Console.WriteLine("API\t" + controls);
    }

    private static void Main(string[] arguments)
    {
        if (arguments.Length != 0) { Api(); return; }
        var maps = new Dictionary<string, short[]>();
        string line;
        while ((line = Console.ReadLine()) != null)
        {
            string[] values = line.Split('\t');
            if (values[0] == "MAP") { maps.Add(values[1], Decode(values[2])); continue; }
            int width = int.Parse(values[2]), height = int.Parse(values[3]);
            if (values[0] == "W")
            {
                short[] field = (short[])maps[values[1]].Clone();
                int code = SourceWaveField.FillAll(field, width, height, int.Parse(values[4]), int.Parse(values[5]));
                Console.WriteLine(code + "\t" + Encode(field)); continue;
            }
            var origins = new SourceFleetFormation.Cell[(values.Length - 6) / 2];
            for (int i = 0; i < origins.Length; i++)
                origins[i] = new SourceFleetFormation.Cell(int.Parse(values[6 + 2 * i]), int.Parse(values[7 + 2 * i]));
            try
            {
                var result = SourceFleetFormation.Assign(maps[values[1]], width, height, origins,
                                                        int.Parse(values[4]), int.Parse(values[5]));
                var targets = new List<string>();
                for (int i = 0; i < result.Count; i++)
                    targets.Add(result.GetTarget(i).X + "," + result.GetTarget(i).Y + "," + result.GetBand(i));
                var fields = new List<string>();
                for (int i = 0; i < result.FieldCount; i++) fields.Add(Encode(result.CaptureField(i)));
                Console.WriteLine(string.Join("\t", new object[] { result.SourceCode, result.UsedMatching ? 1 : 0,
                    string.Join(";", targets), Encode(result.CaptureReservedField()), string.Join(";", fields) }));
            }
            catch (NotSupportedException exception)
            { Console.WriteLine("UNSUPPORTED\t" + exception.Message); }
        }
    }
}
