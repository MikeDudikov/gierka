using System;
using AncientConquest.Presentation;

public static class MenuButtonProbe
{
    public static void Main()
    {
        MainMenuButton button = null;
        string line;
        while ((line = Console.ReadLine()) != null)
        {
            string[] values = line.Split('\t');
            if (values.Length != 5) throw new ArgumentException("Expected five input columns.");
            if (values[0] == "1") button = new MainMenuButton(112, 398, 278, 64, values[1] == "1");
            if (button == null) throw new InvalidOperationException("Trace must create its button.");
            bool emitted = button.Process(int.Parse(values[2]), int.Parse(values[3]), int.Parse(values[4]));
            Console.WriteLine(button.State + "\t" + (button.Pressed ? 1 : 0) + "\t" +
                              (button.Hovered ? 1 : 0) + "\t" + (button.Inside ? 1 : 0) + "\t" + (emitted ? 1 : 0));
        }
    }
}
