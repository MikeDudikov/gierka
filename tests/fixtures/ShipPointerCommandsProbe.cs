using System;
using System.Globalization;
using AncientConquest.Simulation;

internal static class ShipPointerCommandsProbe
{
    private static int Number(string value) => int.Parse(value, CultureInfo.InvariantCulture);
    private static string Hex(byte[] bytes) => BitConverter.ToString(bytes).Replace("-", "").ToLowerInvariant();
    private static int Bit(bool value) => value ? 1 : 0;
    private static int guards;
    private static void Check(string name, bool condition)
    {
        if (!condition) throw new InvalidOperationException(name);
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
        object owner = new object(); var c = new ShipPointerCommands(owner);
        var own = new ShipPointerCommandInput(owner, 16, 2, 5);
        var sea = new ShipPointerCommandInput(null, 18, 5, 7);
        Throws<ArgumentNullException>("null-owner", () => new ShipPointerCommands(null));
        Throws<ArgumentOutOfRangeException>("missing-command", () => c.GetLastCommand(0));
        Throws<NotSupportedException>("other-actor", () => c.ProcessRelease(new ShipPointerCommandInput(new object(), 16, 2, 5), 0x62, 0));
        Throws<NotSupportedException>("other-cursor", () => c.ProcessRelease(new ShipPointerCommandInput(null, 18, 5, 8), 0x62, 0));
        Throws<NotSupportedException>("shift", () => c.ProcessRelease(own, 0x62, 4));
        Throws<NotSupportedException>("control", () => c.ProcessRelease(own, 0x62, 8));
        Throws<NotSupportedException>("unselected-sea", () => c.ProcessRelease(sea, 0x62, 0));
        Throws<InvalidOperationException>("no-visual-to-remove", () => c.CompleteSelectionVisualRemoval());
        c.ProcessRelease(own, 0x62, 0);
        Throws<InvalidOperationException>("selected-visual-cannot-remove", () => c.CompleteSelectionVisualRemoval());
        Throws<NotSupportedException>("busy-replacement", () => c.ProcessRelease(sea, 0x62, 0, false));
        Throws<ArgumentOutOfRangeException>("outside-map", () => c.ProcessRelease(new ShipPointerCommandInput(null, 24, 5, 7), 0x62, 0));
        Throws<NotSupportedException>("contextual-right-cycle", () => c.ProcessRelease(new ShipPointerCommandInput(owner, 16, 2, 5, 0x101, 1), 0x64, 0));
        c.ProcessRelease(sea, 0x62, 0);
        Throws<InvalidOperationException>("membership-order", () => c.ConsumeMembership41(1));
        c.ConsumeMembership41(0);
        Throws<InvalidOperationException>("membership-once", () => c.ConsumeMembership41(0));
        Throws<ArgumentOutOfRangeException>("negative-command-index", () => c.GetLastCommand(-1));
        Throws<ArgumentOutOfRangeException>("past-command-index", () => c.GetLastCommand(c.LastCommandCount));
        byte[] payload = c.GetLastCommand(1).CapturePayload(); payload[0] = 255;
        Check("owned-payload", c.GetLastCommand(1).CapturePayload()[0] == 18);
        c.ProcessRelease(sea, 0x64, 0);
        c.CompleteSelectionVisualRemoval();
        Check("reverse-removal-ack", c.Current.SelectionVisualFlag == 0 && !c.Current.Selected);
        Throws<InvalidOperationException>("visual-ack-once", () => c.CompleteSelectionVisualRemoval());
        Console.WriteLine("GUARDS\t" + guards);
    }
    private static void Main()
    {
        object owner = new object(); ShipPointerCommands commands = null;
        ShipPointerCommands.Result result = default(ShipPointerCommands.Result);
        string label = null; int index = 0; string line;
        while ((line = Console.ReadLine()) != null)
        {
            string[] f = line.Split('\t');
            if (f[0] == "CASE")
            { commands = new ShipPointerCommands(owner); label = f[1]; index = 0; continue; }
            if (f[0] == "R")
                result = commands.ProcessRelease(new ShipPointerCommandInput(f[2] == "1" ? owner : null,
                    Number(f[3]), Number(f[4]), Number(f[1]), (ushort)Number(f[5]), (ushort)Number(f[6]),
                    f[7] == "1", f[8] == "1"), Number(f[9]), (uint)Number(f[10]));
            else if (f[0] == "C") commands.ConsumeMembership41((short)Number(f[1]));
            else throw new InvalidOperationException("Unknown pointer probe operation.");
            var s = commands.Current;
            string packets = "";
            for (int i = 0; i < commands.LastCommandCount; i++)
            {
                var packet = commands.GetLastCommand(i);
                if (i != 0) packets += ",";
                packets += packet.InstanceId + ":" + packet.Action + ":" + Hex(packet.CapturePayload());
            }
            Console.WriteLine(string.Join("\t", new object[] { "ROW", label, index++, s.GroupCount,
                Bit(s.Selected), Bit(s.PendingSelection), s.CurrentGroupIndex, s.UiGroup, s.SimulationGroup,
                s.SelectionVisualFlag, result.CursorType, result.ActionMask, result.ActionBit, Bit(result.Blocked),
                Bit(result.SelectionClearRequested), Bit(result.SelectionRequested), Bit(result.ConfirmRequested), packets }));
        }
        Guards();
    }
}
