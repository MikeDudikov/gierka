using System;
using System.Globalization;
using AncientConquest.Simulation;

internal static class ShipMoveRequestProbe
{
    private static int guards;
    private static string Hex(byte[] value) => BitConverter.ToString(value).Replace("-", "").ToLowerInvariant();
    private static uint UInt(string value) => uint.Parse(value, CultureInfo.InvariantCulture);
    private static byte Byte(string value) => byte.Parse(value, CultureInfo.InvariantCulture);
    private static int Int(string value) => int.Parse(value, CultureInfo.InvariantCulture);

    private static string State(ShipMoveRequestInbox inbox)
    {
        return string.Join("\t", inbox.PendingFlags, inbox.ActiveFlags, inbox.HasPendingMove ? 1 : 0,
                           inbox.TargetX, inbox.TargetY, inbox.RouteByte, inbox.FirstMove ? 1 : 0,
                           Hex(inbox.CapturePendingRecord()));
    }

    private static void Reject<T>(Action action) where T : Exception
    {
        try { action(); }
        catch (T) { ++guards; return; }
        throw new InvalidOperationException("Expected move-request domain rejection did not occur.");
    }

    private static void Contracts()
    {
        Reject<NotSupportedException>(() => new ShipMoveRequestInbox(uint.MaxValue, status: 3));
        Reject<NotSupportedException>(() => new ShipMoveRequestInbox(uint.MaxValue, status: 255));
        var inbox = new ShipMoveRequestInbox(uint.MaxValue);
        string before = State(inbox);
        Reject<NotSupportedException>(() => inbox.ConsumeInitialIdleMove(true));
        if (State(inbox) != before) throw new InvalidOperationException("Busy rejection changed an empty inbox.");
        ++guards;
        inbox.RequestCellMove(int.MinValue, int.MaxValue);
        before = State(inbox);
        Reject<NotSupportedException>(() => inbox.UpdateContext(0, 0, 3));
        Reject<NotSupportedException>(() => inbox.ConsumeInitialIdleMove(true));
        if (State(inbox) != before) throw new InvalidOperationException("Rejected context changed a pending request.");
        ++guards;
        byte[] first = inbox.CapturePendingRecord(), second = inbox.CapturePendingRecord();
        if (ReferenceEquals(first, second) || first.Length != 26) throw new InvalidOperationException("Pending capture was not independent.");
        ++guards;
        first[0] = 99; first[25] = 12;
        if (State(inbox) != before) throw new InvalidOperationException("Capture exposed the internal pending bytes.");
        ++guards;
        // An invalid context must preserve the original capability context too.
        if (!inbox.RequestCellMove(15, 3)) throw new InvalidOperationException("Invalid context partially changed capabilities.");
        ++guards;
    }

    private static void Main()
    {
        string line; int caseIndex = 0;
        while ((line = Console.ReadLine()) != null)
        {
            string[] fields = line.Split('\t');
            var inbox = new ShipMoveRequestInbox(UInt(fields[0]), UInt(fields[1]), Byte(fields[2]), Byte(fields[3]));
            Console.WriteLine(caseIndex + "\t0\t-1\t" + State(inbox));
            int step = 0;
            foreach (string operation in fields[4].Split(';'))
            {
                string[] part = operation.Split(','); int result = -1;
                if (part[0] == "r") result = inbox.RequestCellMove(Int(part[1]), Int(part[2]), Byte(part[3])) ? 1 : 0;
                else if (part[0] == "c") inbox.UpdateContext(UInt(part[1]), UInt(part[2]), Byte(part[3]));
                else if (part[0] == "p") result = (int)inbox.ConsumeInitialIdleMove();
                else throw new InvalidOperationException("Unknown probe operation.");
                Console.WriteLine(caseIndex + "\t" + (++step) + "\t" + result + "\t" + State(inbox));
            }
            ++caseIndex;
        }
        Contracts();
        Console.WriteLine("GUARDS\t" + guards);
    }
}
