using System;
using System.Collections.Generic;
using AncientConquest.Simulation;

class ShipFleetMembershipProbe
{
    private static readonly uint[] Local = { 11, 12, 13 };
    private static string Hex(byte[] bytes) => BitConverter.ToString(bytes).Replace("-", "").ToLowerInvariant();
    private static string Snapshot(ShipFleetMembership state, string result = "-")
    {
        var groups = new List<string>();
        for (int group = 0; group < state.GroupCount; group++)
        {
            var members = new List<int>();
            for (int member = 0; member < state.GetGroupMemberCount(group); member++)
                members.Add(state.GetGroupMemberRegistryIndex(group, member));
            groups.Add(state.GetGroupMode(group) + ":" + state.GetGroupSerial(group) + ":" + string.Join(",", members));
        }
        var actors = new List<string>();
        for (int index = 0; index < state.ActorCount; index++)
            actors.Add(state.GetActorId(index) + ":" + state.GetUiGroup(index) + ":" + state.GetSimulationGroup(index) + ":" + state.GetMemberIndex(index));
        var commands = new List<string>();
        for (int index = 0; index < state.CommandCount; index++)
        {
            ShipFleetMembershipCommand command = state.GetCommand(index);
            commands.Add(command.InstanceId + ":" + command.Action + ":" + Hex(command.CapturePayload()));
        }
        return string.Join("\t", new object[] { result, state.CurrentGroup, state.ConsumedCommandCount,
            string.Join(";", groups), string.Join(";", actors), string.Join(";", commands) });
    }

    private static int controls;
    private static void Check(bool value) { if (!value) throw new Exception("API control failed " + controls); controls++; }
    private static void Reject<T>(Action action, ShipFleetMembership state = null) where T : Exception
    {
        string before = state == null ? null : Snapshot(state);
        try { action(); } catch (T) { Check(state == null || before == Snapshot(state)); return; }
        throw new Exception("Expected " + typeof(T).Name);
    }
    private static void Api()
    {
        Reject<ArgumentNullException>(() => new ShipFleetMembership(null));
        Reject<ArgumentOutOfRangeException>(() => new ShipFleetMembership(new uint[0]));
        Reject<ArgumentOutOfRangeException>(() => new ShipFleetMembership(new uint[9]));
        Reject<ArgumentException>(() => new ShipFleetMembership(new uint[] { 11, 11 }));
        var registry = new uint[] { 13, 11, 12 };
        var state = new ShipFleetMembership(registry);
        registry[0] = 999;
        Check(state.GetActorId(0) == 13 && !state.ConsumeNext());
        Check(state.CommitPending(new uint[0]) == 0 && state.GroupCount == 0 && state.CurrentGroup == -1);
        Reject<ArgumentNullException>(() => state.CommitPending(null), state);
        Reject<ArgumentException>(() => state.CommitPending(new uint[] { 11, 99 }), state);
        Reject<ArgumentException>(() => state.CommitPending(new uint[] { 11, 11 }), state);
        Reject<ArgumentException>(() => state.CommitPending(new uint[] { 11, 12, 13, 11 }), state);
        state.CommitPending(new uint[] { 11, 13 });
        Check(state.GetGroupMemberRegistryIndex(0, 0) == 1 && state.GetGroupMemberRegistryIndex(0, 1) == 0);
        Check(state.GetSimulationGroup(0) == -1 && state.GetUiGroup(0) == 0);
        byte[] payload = state.GetCommand(0).CapturePayload(); payload[0] = 0; payload[1] = 99;
        Check(Hex(state.GetCommand(0).CapturePayload()) == "010000000000");
        Reject<ArgumentException>(() => state.CommitPending(new uint[] { 12, 99 }), state);
        Reject<ArgumentException>(() => state.CommitPending(new uint[] { 13, 13 }), state);
        state.CommitPending(new uint[] { 13 });
        Check(state.GetGroupMemberCount(0) == 1 && state.GetMemberIndex(1) == 0);
        Check(state.GetCommand(2).InstanceId == 13 && Hex(state.GetCommand(2).CapturePayload()) == "01ffffffff00");
        Check(state.GetCommand(3).InstanceId == 13 && Hex(state.GetCommand(3).CapturePayload()) == "010100000000");
        Check(state.ConsumeNext() && state.GetSimulationGroup(1) == 0 && state.GetSimulationGroup(0) == -1);
        Check(state.ConsumeNext() && state.GetSimulationGroup(0) == 0);
        Check(state.ConsumeNext() && state.GetSimulationGroup(0) == -1 && state.GetUiGroup(0) == 1);
        Check(state.ConsumeNext() && state.GetSimulationGroup(0) == 1 && !state.ConsumeNext());
        Check(state.CommitPending(new uint[0]) == 0 && state.CurrentGroup == 1 && state.GroupCount == 2);
        Console.WriteLine("API\t" + controls);
    }

    private static void Main(string[] arguments)
    {
        if (arguments.Length != 0) { Api(); return; }
        ShipFleetMembership state = null;
        string line;
        while ((line = Console.ReadLine()) != null)
        {
            string[] fields = line.Split('\t');
            if (fields[0] == "CASE") { state = new ShipFleetMembership(Local); continue; }
            string result = "-";
            if (fields[0] == "C")
            {
                var ids = new List<uint>();
                for (int index = 1; index < fields.Length; index++) ids.Add(uint.Parse(fields[index]));
                result = state.CommitPending(ids).ToString();
            }
            else if (fields[0] == "D") { if (!state.ConsumeNext()) throw new Exception("Missing generated packet"); }
            else throw new Exception("Unknown probe operation");
            Console.WriteLine(Snapshot(state, result));
        }
    }
}
