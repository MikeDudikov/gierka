using System;
using AncientConquest.World;

namespace AncientConquest.Simulation
{
    /// <summary>Normal ship ownership/capabilities used by the bounded hover branch.</summary>
    public readonly struct ShipHoverActor
    {
        public byte OwnerSide { get; }
        public byte OwnerPlayer { get; }
        public uint Capabilities { get; }
        public uint RuntimeClassTag { get; }
        public ShipHoverActor(byte ownerSide, byte ownerPlayer, uint capabilities, uint runtimeClassTag = 200u)
        {
            if (runtimeClassTag < 200u || runtimeClassTag > 211u)
                throw new NotSupportedException("Only normal ship hover metadata is supported.");
            OwnerSide = ownerSide; OwnerPlayer = ownerPlayer;
            Capabilities = capabilities; RuntimeClassTag = runtimeClassTag;
        }
    }

    /// <summary>
    /// Normal source Cursor517a60/517540 projection for no selection or selected0b.
    /// No fog, no modal UI, normal cursor context0, normal ship slots only.
    /// The caller maps display coordinates and invokes Refresh on Cursor Life.
    /// Move includes the normal global-screen gate and map-position invalidation.
    /// </summary>
    public sealed class ShipPointerHover
    {
        public readonly struct Snapshot
        {
            public bool HasMapPosition { get; }
            public int ScreenX { get; }
            public int ScreenY { get; }
            public int WorldX { get; }
            public int WorldY { get; }
            public int CellX { get; }
            public int CellY { get; }
            public object HoveredOwner { get; }
            public ushort CursorType { get; }
            public ushort ActionMask { get; }
            public ushort ActionBit { get; }
            public bool Blocked { get; }
            public ushort Selector { get; }
            public bool LastQueryPerformed { get; }
            internal Snapshot(ShipPointerHover s)
            {
                HasMapPosition=s.hasMap;ScreenX=s.screenX;ScreenY=s.screenY;
                WorldX=s.worldX;WorldY=s.worldY;CellX=s.cellX;CellY=s.cellY;
                HoveredOwner=s.hovered;CursorType=s.cursorType;ActionMask=s.actionMask;
                ActionBit=s.actionBit;Blocked=s.blocked;Selector=s.selector;
                LastQueryPerformed=s.lastQuery;
            }
        }
        private readonly MissionOccupancyGrid grid;
        private readonly object controlled;
        private readonly Func<object, ShipPointerPose> poses;
        private readonly Func<object, ShipHoverActor> actors;
        private readonly byte localSide,localPlayer;
        private readonly ushort selector;
        private readonly Func<int> selectedCount;
        private readonly Func<int, object> selectedAt;
        private int screenX,screenY,worldX,worldY,cellX,cellY;
        private object hovered;
        private ushort cursorType,actionMask,actionBit;
        private bool hasMap,blocked,lastQuery;
        public Snapshot Current => new Snapshot(this);

        public ShipPointerHover(MissionOccupancyGrid grid, object controlledOwner,
                                Func<object, ShipPointerPose> poses,
                                Func<object, ShipHoverActor> actors,
                                byte localSide=1, byte localPlayer=1, ushort selector=0,
                                Func<int> selectedCount=null, Func<int, object> selectedAt=null)
        {
            if(grid==null)throw new ArgumentNullException(nameof(grid));
            if(grid.Width!=24||grid.Height!=24)throw new NotSupportedException("The24x24 reference world is required.");
            if(controlledOwner==null)throw new ArgumentNullException(nameof(controlledOwner));
            this.poses=poses??throw new ArgumentNullException(nameof(poses));
            this.actors=actors??throw new ArgumentNullException(nameof(actors));
            this.grid=grid;controlled=controlledOwner;this.localSide=localSide;
            this.localPlayer=localPlayer;this.selector=selector;
            if ((selectedCount == null) != (selectedAt == null)) throw new ArgumentException("Both temporary-fleet accessors are required.");
            this.selectedCount=selectedCount;this.selectedAt=selectedAt;
        }
        public bool Move(int screenX,int screenY,int worldX,int worldY,int cellX,int cellY,bool source0bSelected)
        {
            if(cellX<0||cellX>=24||cellY<0||cellY>=24)throw new ArgumentOutOfRangeException(nameof(cellX));
            lastQuery=false;
            if(this.screenX==screenX&&this.screenY==screenY)return false;
            hasMap=false;blocked=false;
            if(this.worldX==worldX&&this.worldY==worldY)
            {this.screenX=screenX;this.screenY=screenY;return false;}
            this.screenX=screenX;this.screenY=screenY;this.worldX=worldX;this.worldY=worldY;
            this.cellX=cellX;this.cellY=cellY;hasMap=true;blocked=false;
            Refresh(source0bSelected);
            return true;
        }
        public void InvalidateMap()
        {
            // Global cursor move invalidates map coordinates before forwarding.
            // Cached coordinates and picked pointer are deliberately retained.
            hasMap=false;blocked=false;lastQuery=false;
        }
        public void ApplyReleaseCursor(ushort type,ushort mask,ushort bit,bool blocked)
        {
            cursorType=type;actionMask=mask;actionBit=bit;this.blocked=blocked;lastQuery=false;
        }
        public void Refresh(bool source0bSelected)
        {
            lastQuery=false;
            if(!hasMap){cursorType=0;actionMask=0;return;}
            object picked=ShipWorldPicker.Pick(grid,worldX,worldY,cellX,cellY,true,poses);
            lastQuery=true;
            if(!ReferenceEquals(picked,hovered))actionMask=0;
            hovered=picked;
            if(!source0bSelected)
            {
                if(picked==null){cursorType=0;actionMask=0;return;}
                ShipHoverActor actor=actors(picked);
                if(Friendly(actor)){cursorType=5;actionMask=0;}
                // Source has no SetGCType in the unselected foreign-ship branch.
                return;
            }
            if(picked==null)
            {
                ShipHoverActor actor=actors(selectedAt == null ? controlled : selectedAt(0));
                if(!Friendly(actor))throw new NotSupportedException("Only local source0b selection is supported.");
                cursorType=(ushort)((actor.Capabilities&0x400u)!=0&&grid.CanEnter(cellX,cellY,0)?7:0);
                actionMask=0;blocked=false;return;
            }
            int count = selectedCount == null ? 1 : selectedCount();
            if(count == 1 && ReferenceEquals(picked,selectedAt == null ? controlled : selectedAt(0)))
            {cursorType=6;actionMask=0;blocked=false;return;}
            ShipHoverActor target=actors(picked);
            if (selectedCount != null && !Friendly(target))
            {
                // The selection-only diagnostic cannot dispatch combat. Keep that
                // unsupported context inert instead of issuing a friendly command.
                cursorType=0;actionMask=0;blocked=true;return;
            }
            if(!Friendly(target))throw new NotSupportedException("Selected foreign hover/combat is outside this normal branch.");
            blocked=false;
            if((target.Capabilities&4u)==0){cursorType=5;actionMask=0;return;}
            // C452 friendly ship returns type100/mask101. GCGameState resolves
            // its lowest action bit to visual type5 and preserves an unchanged
            // mask's current cycle bit/type. E4 is not cleared when E2 becomes0.
            ushort mask = count > 1 ? (ushort)1 : (ushort)0x101;
            if(actionMask!=mask){actionMask=mask;actionBit=1;cursorType=5;}
        }
        private bool Friendly(ShipHoverActor actor)
        {
            if(actor.RuntimeClassTag<200u||actor.RuntimeClassTag>211u)
                throw new InvalidOperationException("Initialized normal ship hover metadata is required.");
            return actor.OwnerSide==localSide&&actor.OwnerPlayer==localPlayer;
        }
    }
}
