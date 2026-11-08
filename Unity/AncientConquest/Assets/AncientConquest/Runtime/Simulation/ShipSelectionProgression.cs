using System;

namespace AncientConquest.Simulation
{
    /// <summary>Normal source0b RAM_056X056 selection/IL visibility branch of4e0d00.</summary>
    public sealed class ShipSelectionProgression
    {
        public readonly struct Snapshot
        {
            public byte SelectionState { get; }
            public bool Exists { get; }
            public int StoredFrame { get; }
            public int DrawnFrame { get; }
            public uint LastCounter { get; }
            public bool SelectorVisible { get; }
            public int WorldPixelX { get; }
            public int WorldPixelY { get; }
            public bool HealthVisible { get; }
            public bool HealthExists { get; }
            public int HealthWorldX { get; }
            public int HealthWorldY { get; }
            internal Snapshot(ShipSelectionProgression s)
            {
                SelectionState=s.selection;Exists=s.exists;StoredFrame=s.frame;DrawnFrame=s.drawn;
                LastCounter=s.last;SelectorVisible=s.visible;WorldPixelX=s.x;WorldPixelY=s.y;
                HealthVisible=s.health;HealthExists=s.healthExists;HealthWorldX=s.healthX;HealthWorldY=s.healthY;
            }
        }
        public int LogicalSize { get; }
        public int SelectorSize => LogicalSize + 4;
        public int HealthWidth => SelectorSize - 26;
        public ShipSelectionProgression(int logicalSize = 56)
        {
            if (logicalSize != 56 && logicalSize != 64 && logicalSize != 72)
                throw new NotSupportedException("Only source56/64/72-square normal ships are verified.");
            LogicalSize = logicalSize;
        }
        private byte selection;
        private bool exists,visible,health,healthExists;
        private int frame,drawn=-1,x,y,healthX,healthY;
        private uint last;
        public Snapshot Current => new Snapshot(this);
        public bool LastStepPublishesPose { get; private set; }
        public bool LastStepDeletesSelector { get; private set; }
        public bool LastStepHidesHealth { get; private set; }
        public void Select(int mainWorldX,int mainWorldY)
        {
            ResetEffects();
            if(!exists)
            {
                exists=true;visible=false;health=false;healthExists=true;frame=0;drawn=-1;last=0;
                x=unchecked(mainWorldX-2);y=unchecked(mainWorldY-2);
            }
            selection=1;
        }
        public void Deselect()
        {
            ResetEffects();
            if(selection!=0)selection=2;
        }
        public void Advance(uint counter,int pendingSteps,int mainWorldX,int mainWorldY)
        {
            if(pendingSteps<1 || pendingSteps>255)throw new ArgumentOutOfRangeException(nameof(pendingSteps));
            ResetEffects();
            if(!exists || unchecked(counter-last)<=0u)return;
            last=counter;
            if(frame>=10)frame=9;
            x=unchecked(mainWorldX-2);y=unchecked(mainWorldY-2);
            drawn=frame;visible=true;LastStepPublishesPose=true;
            if(selection==1)
            {
                frame=unchecked(frame+pendingSteps);
                if(frame>=10 && healthExists)
                {
                    health=true;healthX=unchecked(x+14);healthY=y;
                }
            }
            else
            {
                if(healthExists){health=false;healthExists=false;LastStepHidesHealth=true;}
                if(selection==2 && --frame<0)
                {
                    exists=false;visible=false;selection=0;LastStepDeletesSelector=true;
                }
            }
        }
        private void ResetEffects()
        {
            LastStepPublishesPose=false;LastStepDeletesSelector=false;LastStepHidesHealth=false;
        }
    }
}
