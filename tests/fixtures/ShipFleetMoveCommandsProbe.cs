using System;
using System.Collections.Generic;
using AncientConquest.Simulation;

class ShipFleetMoveCommandsProbe
{
    private static readonly uint[] Local = { 11, 12, 13 };
    private static readonly SourceFleetFormation.Cell[] Positions = {
        new SourceFleetFormation.Cell(16, 2), new SourceFleetFormation.Cell(21, 5), new SourceFleetFormation.Cell(19, 4) };
    private static string Hex(byte[] data) => BitConverter.ToString(data).Replace("-", "").ToLowerInvariant();
    private static string Snapshot(ShipFleetMembership members, ShipMoveRequestInbox[] inboxes)
    {
        var rows = new List<string>();
        for (int i = 0; i < 3; i++) rows.Add(string.Join(",", new object[] {
            Local[i], members.GetUiGroup(i), members.GetSimulationGroup(i), inboxes[i].PendingFlags,
            Hex(inboxes[i].CapturePendingRecord()) }));
        return string.Join(";", rows);
    }
    private static int controls;
    private static void Check(bool value) { if (!value) throw new Exception("API failed " + controls); controls++; }
    private static void Reject<T>(Action action) where T : Exception
    { try { action(); } catch (T) { controls++; return; } throw new Exception("Expected " + typeof(T).Name); }
    private static void Api()
    {
        Reject<ArgumentNullException>(() => ShipFleetMoveCommands.Build(null, 0, 0, null, Positions, 1, 1));
        Reject<ArgumentNullException>(() => ShipFleetMoveCommands.Build(null, 0, 0, Local, null, 1, 1));
        Reject<ArgumentException>(() => ShipFleetMoveCommands.Build(null, 0, 0, new uint[0], Positions, 1, 1));
        Reject<ArgumentException>(() => ShipFleetMoveCommands.Build(null, 0, 0, new uint[] { 11 }, Positions, 1, 1));
        Reject<ArgumentException>(() => ShipFleetMoveCommands.Build(null, 0, 0, new uint[] { 11, 11 }, new SourceFleetFormation.Cell[2], 1, 1));
        Reject<ArgumentException>(() => ShipFleetMoveCommands.Build(null, 0, 0, new uint[9], new SourceFleetFormation.Cell[9], 1, 1));
        var one = ShipFleetMoveCommands.Build(null, 0, 0, new uint[] { 13 }, new[] { Positions[2] }, -1, 0)[0];
        Check(one.InstanceId == 13 && one.Action == 20 && Hex(one.CapturePayload()) == "ffffffff0000000000");
        byte[] payload = one.CapturePayload(); payload[0] = 0;
        Check(Hex(one.CapturePayload()) == "ffffffff0000000000");
        Reject<ArgumentNullException>(() => one.CopyTo(null));
        var denied = new ShipMoveRequestInbox(0);
        Check(!one.CopyTo(denied) && !denied.HasPendingMove);
        var allowed = new ShipMoveRequestInbox(0x400);
        Check(one.CopyTo(allowed) && allowed.HasPendingMove && allowed.ActiveFlags == 0 && allowed.CapturePendingRecord()[25] == 0);
        var blocked = new short[576]; for (int i = 0; i < blocked.Length; i++) blocked[i] = -1;
        var fallback = ShipFleetMoveCommands.Build(blocked, 24, 24, Local, Positions, 18, 5);
        Check(fallback.Length == 3 && fallback[0].ByteArgument == 255 && fallback[2].X == 18 && fallback[2].Y == 5);
        Check(fallback[0].CopyTo(allowed) && allowed.CapturePendingRecord()[25] == 255 && allowed.ActiveFlags == 0);
        Console.WriteLine("API\t" + controls);
    }
    private static void Main(string[] arguments)
    {
        if (arguments.Length != 0) { Api(); return; }
        var maps = new Dictionary<string, short[]>(); string line;
        while ((line = Console.ReadLine()) != null)
        {
            string[] fields = line.Split('\t');
            if (fields[0] == "MAP")
            {
                byte[] raw = Convert.FromBase64String(fields[2]); var map = new short[raw.Length / 2];
                Buffer.BlockCopy(raw, 0, map, 0, raw.Length); maps.Add(fields[1], map); continue;
            }
            string[] selected = fields[2].Split(','); var ids = new uint[selected.Length];
            var origins = new SourceFleetFormation.Cell[ids.Length];
            for (int i = 0; i < ids.Length; i++) { ids[i] = uint.Parse(selected[i]); origins[i] = Positions[(int)ids[i] - 11]; }
            var members = new ShipFleetMembership(Local); members.CommitPending(ids);
            var moves = ShipFleetMoveCommands.Build(maps[fields[1]], 24, 24, ids, origins, int.Parse(fields[3]), int.Parse(fields[4]));
            var inboxes = new[] { new ShipMoveRequestInbox(0xfffff7ff), new ShipMoveRequestInbox(0xfffff7ff), new ShipMoveRequestInbox(0xfffffeff) };
            var commands = new List<string>(); var states = new List<string> { Snapshot(members, inboxes) };
            for (int i = 0; i < members.CommandCount; i++)
            {
                var command = members.GetCommand(i); commands.Add(command.InstanceId + ":41:" + Hex(command.CapturePayload()));
                if (!members.ConsumeNext()) throw new Exception("Missing41"); states.Add(Snapshot(members, inboxes));
            }
            foreach (var command in moves)
            {
                commands.Add(command.InstanceId + ":20:" + Hex(command.CapturePayload()));
                if (!command.CopyTo(inboxes[(int)command.InstanceId - 11])) throw new Exception("Rejected20");
                states.Add(Snapshot(members, inboxes));
            }
            Console.WriteLine(string.Join(";", commands) + "\t" + string.Join("|", states));
        }
    }
}
