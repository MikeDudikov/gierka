using System;
using AncientConquest.World;

public static class MissionInitialSetupProbe
{
    private static void Check(string name, bool condition)
    {
        if (!condition) throw new Exception("Mission setup contract failed: " + name);
        Console.WriteLine("CHECK\t" + name);
    }

    private static bool Throws<T>(Action action) where T : Exception
    {
        try { action(); }
        catch (T) { return true; }
        return false;
    }

    private static void Write32(byte[] input, int offset, int value)
    {
        for (int part = 0; part < 4; part++) input[offset + part] = unchecked((byte)(value >> (part * 8)));
    }

    private static byte[] Descriptor()
    {
        byte[] result = new byte[124];
        Write32(result, 16, 1);
        Write32(result, 28, 1);
        Write32(result, 32, 1);
        return result;
    }

    private static void Guards()
    {
        byte[] descriptor = Descriptor();
        byte[] views = new byte[80];
        Check("descriptor_null", Throws<ArgumentException>(() => new MissionInitialSetup(null, views)));
        Check("descriptor_short", Throws<ArgumentException>(() => new MissionInitialSetup(new byte[19], views)));
        foreach (int count in new[] { -1, 0, int.MaxValue, 2 })
        {
            byte[] changed = (byte[])descriptor.Clone();
            Write32(changed, 16, count);
            Check("descriptor_count_" + count, Throws<ArgumentException>(() => new MissionInitialSetup(changed, views)));
        }
        foreach (int side in new[] { -1, 5, int.MaxValue })
        {
            byte[] changed = (byte[])descriptor.Clone();
            Write32(changed, 28, side);
            Check("side_" + side, Throws<ArgumentException>(() => new MissionInitialSetup(changed, views)));
        }
        foreach (int player in new[] { -1, 4, int.MaxValue })
        {
            byte[] changed = (byte[])descriptor.Clone();
            Write32(changed, 32, player);
            Check("player_" + player, Throws<ArgumentException>(() => new MissionInitialSetup(changed, views)));
        }
        Check("views_null", Throws<ArgumentException>(() => new MissionInitialSetup(descriptor, null)));
        Check("views_short", Throws<ArgumentException>(() => new MissionInitialSetup(descriptor, new byte[79])));
        Check("views_long", Throws<ArgumentException>(() => new MissionInitialSetup(descriptor, new byte[81])));
        foreach (int campaign in new[] { -1, 4, int.MinValue, int.MaxValue })
            Check("campaign_" + campaign, Throws<ArgumentOutOfRangeException>(() => new MissionInitialSetup(descriptor, views, campaign)));
        Check("missing_selected_pair", Throws<ArgumentException>(() => new MissionInitialSetup(descriptor, views, 1)));

        for (int part = 0; part < 4; part++) views[20 + part] = 0xff;
        byte[] descriptorBefore = (byte[])descriptor.Clone();
        byte[] viewsBefore = (byte[])views.Clone();
        MissionInitialSetup retained = new MissionInitialSetup(descriptor, views);
        Check("sources_unchanged", Convert.ToBase64String(descriptor) == Convert.ToBase64String(descriptorBefore) &&
              Convert.ToBase64String(views) == Convert.ToBase64String(viewsBefore));
        Check("unsigned_saved_origin", retained.SavedOriginX == 65535 && retained.SavedOriginY == 65535);
        Check("source_extent", retained.SourceViewWidthCells == 9 && retained.SourceViewHeightCells == 8);
        byte[] copy = retained.CopyPlayersDescriptor();
        copy[5] = 0xff;
        Check("copy_isolation", retained.CopyPlayersDescriptor()[5] == 1);
        for (int index = 0; index < descriptor.Length; index++) descriptor[index] = 0;
        for (int index = 0; index < views.Length; index++) views[index] = 0;
        Check("input_lifetime_isolation", retained.SelectedSide == 1 && retained.SelectedPlayer == 1 &&
              retained.SavedOriginX == 65535 && retained.SavedOriginY == 65535 && retained.CopyPlayersDescriptor()[5] == 1);
    }

    public static int Main()
    {
        Guards();
        string line;
        while ((line = Console.ReadLine()) != null)
        {
            string[] fields = line.Split('\t');
            if (fields.Length != 3) throw new ArgumentException("Expected descriptor, views, campaign.");
            byte[] descriptor = Convert.FromBase64String(fields[0]);
            byte[] views = Convert.FromBase64String(fields[1]);
            MissionInitialSetup setup = new MissionInitialSetup(descriptor, views, int.Parse(fields[2]));
            Console.WriteLine("ROW\t" + setup.SelectedSide + "\t" + setup.SelectedPlayer + "\t" +
                setup.SavedOriginX + "\t" + setup.SavedOriginY + "\t" + setup.SourceViewWidthCells + "\t" +
                setup.SourceViewHeightCells + "\t" + Convert.ToBase64String(setup.CopyPlayersDescriptor()));
        }
        return 0;
    }
}
