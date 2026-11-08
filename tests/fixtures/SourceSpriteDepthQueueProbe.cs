using System;
using System.Collections.Generic;
using System.Globalization;
using AncientConquest.World;

internal static class SourceSpriteDepthQueueProbe
{
    private static int Parse(string value) { return int.Parse(value, CultureInfo.InvariantCulture); }
    private static string Join(int[] values) { return string.Join(",", values); }
    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
    private static void Guard(string name, Action action)
    {
        bool caught = false;
        try { action(); }
        catch (ArgumentOutOfRangeException) { caught = true; }
        Require(caught, "Missing guard " + name);
        Console.WriteLine("GUARD\t" + name);
    }
    private static void Guards()
    {
        var q = new SourceSpriteDepthQueue();
        Require(q.Count == 0 && q.CopyAscendingOrder().Length == 0 && q.CopyDrawOrder().Length == 0, "empty queue");
        Console.WriteLine("GUARD\tempty-copies");
        Guard("empty-update", () => q.UpdateDepth(0, 1));
        Guard("empty-get", () => q.GetDepth(0));
        Guard("empty-draw", () => q.GetDrawNode(0));
        q.Register(20); q.Register(30); q.Register(20);
        Guard("negative-update", () => q.UpdateDepth(-1, 1));
        Guard("past-end-update", () => q.UpdateDepth(3, 1));
        Guard("max-update", () => q.UpdateDepth(int.MaxValue, 1));
        Guard("min-get", () => q.GetDepth(int.MinValue));
        Guard("past-end-get", () => q.GetDepth(3));
        Guard("negative-draw", () => q.GetDrawNode(-1));
        Guard("past-end-draw", () => q.GetDrawNode(3));
        Guard("max-draw", () => q.GetDrawNode(int.MaxValue));
        int[] a = q.CopyAscendingOrder(), b = q.CopyDrawOrder();
        a[0] = -100; b[0] = -101;
        Require(Join(q.CopyAscendingOrder()) == "0,2,1" && Join(q.CopyDrawOrder()) == "1,2,0", "copy mutation changed queue");
        Console.WriteLine("GUARD\tcopy-isolation");
        Require(q.GetDepth(0) == 20 && q.GetDepth(1) == 30 && q.GetDepth(2) == 20, "invalid operation changed depths");
        Console.WriteLine("GUARD\tinvalid-operation-immutability");
    }
    public static void Main()
    {
        Guards();
        SourceSpriteDepthQueue queue = null;
        string label = null, line;
        int operation = 0;
        while ((line = Console.ReadLine()) != null)
        {
            string[] fields = line.Split('\t');
            if (fields[0] == "CASE")
            {
                label = fields[1]; queue = new SourceSpriteDepthQueue(); operation = 0; continue;
            }
            Require(queue != null, "command before CASE");
            int id;
            if (fields[0] == "R") id = queue.Register(Parse(fields[1]));
            else if (fields[0] == "U")
            {
                id = Parse(fields[1]); queue.UpdateDepth(id, Parse(fields[2]));
            }
            else throw new InvalidOperationException("Unknown input command");
            var depths = new int[queue.Count];
            for (int index = 0; index < depths.Length; ++index) depths[index] = queue.GetDepth(index);
            int[] draw = queue.CopyDrawOrder();
            for (int index = 0; index < draw.Length; ++index)
                Require(queue.GetDrawNode(index) == draw[index], "nonalloc draw getter differs");
            Console.WriteLine("ROW\t" + label + "\t" + operation++ + "\t" + id + "\t" +
                              Join(depths) + "\t" + Join(queue.CopyAscendingOrder()) + "\t" + Join(queue.CopyDrawOrder()));
        }
    }
}
