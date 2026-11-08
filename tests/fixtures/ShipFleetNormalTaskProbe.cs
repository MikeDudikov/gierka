using System;
using System.Collections.Generic;
using AncientConquest.Simulation;

class ShipFleetNormalTaskProbe
{
    private static string Hex(byte[] data) => BitConverter.ToString(data).Replace("-", "").ToLowerInvariant();
    private static ShipFleetNormalTask.Member[] Members(string text)
    {
        if (text == "-") return new ShipFleetNormalTask.Member[0];
        string[] rows = text.Split(';'); var result = new ShipFleetNormalTask.Member[rows.Length];
        for (int i = 0; i < rows.Length; i++)
        {
            string[] f = rows[i].Split(',');
            result[i] = new ShipFleetNormalTask.Member(uint.Parse(f[0]), int.Parse(f[1]), int.Parse(f[2]), byte.Parse(f[3]));
        }
        return result;
    }
    private static uint[] Slots(string text)
    {
        if (text == "-") return new uint[0]; string[] fields = text.Split(','); var result = new uint[fields.Length];
        for (int i = 0; i < result.Length; i++) result[i] = uint.Parse(fields[i]); return result;
    }
    private static string Snapshot(ShipFleetNormalTask task, uint age, bool emitted)
    {
        var assignments = new List<string>(); var events = new List<string>(); var commands = new List<string>();
        for (int i = 0; i < task.AssignmentCount; i++)
        { var a = task.GetAssignment(i); assignments.Add(a.InstanceId + ":" + a.X + ":" + a.Y); }
        for (int i = 0; i < task.EventCount; i++) events.Add(Hex(task.GetEvent(i).CaptureRecord()));
        if (emitted) for (int i = 0; i < task.CommandCount; i++)
        { var c = task.GetCommand(i); commands.Add(c.InstanceId + ":" + c.Action + ":" + Hex(c.CapturePayload())); }
        string header = task.HasTask ? string.Join(",", new object[] { 100, 1, task.RequestedAt,
            unchecked((uint)task.GoalX), unchecked((uint)task.GoalY), 1, 0 }) : "-";
        return string.Join("\t", new object[] { age, header, string.Join(";", assignments), string.Join(";", events), string.Join(";", commands) });
    }
    private static int controls;
    private static void Check(bool value) { if (!value) throw new Exception("API failed " + controls); controls++; }
    private static void Reject<T>(Action action, ShipFleetNormalTask task) where T : Exception
    {
        string before = Snapshot(task, 0, true);
        try { action(); } catch (T) { Check(before == Snapshot(task, 0, true)); return; }
        throw new Exception("Expected " + typeof(T).Name);
    }
    private static void Api()
    {
        var task = new ShipFleetNormalTask(); var one = new[] { new ShipFleetNormalTask.Member(11, 16, 2) };
        Check(!task.HasTask && !task.MemberAdded(0, 0, 11) && !task.MemberRemoved(0, 0, 11, 16, 2));
        Check(task.Work(null, 0, 0, one, null, 77, 3) == 77 && task.CommandCount == 0);
        Reject<ArgumentNullException>(() => task.Request(null, 0, 0, null, 1, 2, 0), task);
        Reject<ArgumentOutOfRangeException>(() => task.Request(null, 0, 0, new ShipFleetNormalTask.Member[9], 1, 2, 0), task);
        Reject<ArgumentException>(() => task.Request(null, 0, 0, new[] { one[0], one[0] }, 1, 2, 0), task);
        Reject<ArgumentOutOfRangeException>(() => task.MemberAdded(0, -1, 11), task);
        task.Request(null, 0, 0, one, 18, 5, uint.MaxValue);
        Check(task.HasTask && task.RequestedAt == uint.MaxValue && task.AssignmentCount == 1 && task.CommandCount == 1);
        byte[] payload = task.GetCommand(0).CapturePayload(); payload[0] = 0;
        Check(Hex(task.GetCommand(0).CapturePayload()) == "120000000500000000");
        Reject<ArgumentNullException>(() => task.Work(null, 0, 0, one, null, 101, 1), task);
        Reject<ArgumentException>(() => task.Work(null, 0, 0, one, new uint[0], 101, 1), task);
        Reject<ArgumentException>(() => task.Work(null, 0, 0, one, new uint[] { 13 }, 101, 1), task);
        Check(task.MemberAdded(12, 2, 11));
        Reject<ArgumentException>(() => task.Work(null, 0, 0, one, new uint[] { 11 }, 101, 1), task);
        byte[] item = task.GetEvent(0).CaptureRecord(); item[0] = 0;
        Check(task.GetEvent(0).CaptureRecord()[0] == 44);
        Check(task.Work(null, 0, 0, one, new uint[] { 11, 12, 11 }, 101, 1) == 102 && task.EventCount == 0);
        var interrupted = new[] { new ShipFleetNormalTask.Member(11, 16, 2, 0, true) };
        Reject<NotSupportedException>(() => task.Work(null, 0, 0, interrupted, new uint[] { 11 }, 101, 1), task);
        var bad = new[] { one[0], new ShipFleetNormalTask.Member(12, 21, 5) };
        Reject<ArgumentNullException>(() => task.Request(null, 24, 24, bad, 18, 5, 0), task);
        Check(task.Work(null, 0, 0, one, new uint[] { 11 }, uint.MaxValue, uint.MaxValue) == uint.MaxValue);
        task.Clear(); Check(!task.HasTask && task.EventCount == 0 && task.AssignmentCount == 0 && task.CommandCount == 0);
        task.Request(null, 0, 0, new ShipFleetNormalTask.Member[0], 18, 5, 3);
        Check(task.HasTask && task.CommandCount == 0 && task.Work(null, 0, 0, new ShipFleetNormalTask.Member[0], new uint[0], 101, 7) == 7);
        Console.WriteLine("API\t" + controls);
    }
    private static void Main(string[] arguments)
    {
        if (arguments.Length != 0) { Api(); return; }
        var maps = new Dictionary<string, short[]>(); ShipFleetNormalTask task = null; uint age = 0; string line;
        while ((line = Console.ReadLine()) != null)
        {
            string[] f = line.Split('\t');
            if (f[0] == "MAP")
            { byte[] raw = Convert.FromBase64String(f[2]); var map = new short[raw.Length / 2]; Buffer.BlockCopy(raw, 0, map, 0, raw.Length); maps.Add(f[1], map); continue; }
            if (f[0] == "CASE") { task = new ShipFleetNormalTask(); age = 0; continue; }
            bool emitted = false;
            if (f[0] == "R")
            { task.Request(maps[f[1]], 24, 24, Members(f[5]), int.Parse(f[2]), int.Parse(f[3]), uint.Parse(f[4])); emitted = true; }
            else if (f[0] == "T")
            { age = task.Work(maps[f[1]], 24, 24, Members(f[3]), Slots(f[4]), age, uint.Parse(f[2])); emitted = true; }
            else if (f[0] == "E")
            {
                if (f[1] == "300") task.MemberAdded(uint.Parse(f[2]), int.Parse(f[3]), uint.Parse(f[4]));
                else task.MemberRemoved(uint.Parse(f[2]), int.Parse(f[3]), uint.Parse(f[4]), int.Parse(f[5]), int.Parse(f[6]));
            }
            else if (f[0] == "A") age = uint.Parse(f[1]);
            else if (f[0] == "X") task.Clear();
            else if (f[0] != "N") throw new Exception(line);
            Console.WriteLine(Snapshot(task, age, emitted));
        }
    }
}
