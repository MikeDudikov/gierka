using System;
using AncientConquest.World;

namespace AncientConquest.Simulation
{
    /// <summary>
    /// Source0b multi-waypoint MoveShip projection with controlled wind0/5,
    /// upgrade0, full health and eight static source fleet identities.
    /// Consumes native5-byte route records; no full Life or later order loop.
    /// </summary>
    public sealed class ShipRouteMovement
    {
        public readonly struct Publication
        {
            public int Frame { get; }
            public int WorldPixelX { get; }
            public int WorldPixelY { get; }
            public int Depth { get; }
            internal Publication(int frame,int x,int y)
            {
                Frame = frame; WorldPixelX = x; WorldPixelY = y;
                Depth = Math.Max(10000,unchecked(20000-56-y));
            }
        }
        internal readonly struct GridMutation
        {
            internal int CellIndex { get; }
            internal bool Occupied { get; }
            internal GridMutation(int index,bool occupied) { CellIndex = index; Occupied = occupied; }
        }

        public readonly struct Snapshot
        {
            public int CellX { get; }
            public int CellY { get; }
            public int WorldPixelX { get; }
            public int WorldPixelY { get; }
            public sbyte Heading { get; }
            public sbyte TargetHeading { get; }
            public sbyte TurnStep { get; }
            public byte State { get; }
            public bool CenterGate { get; }
            public int Speed { get; }
            public int Remainder { get; }
            public int Deceleration { get; }
            public int ReservedCellIndex { get; }
            public int NextCellIndex { get; }
            public int PathIndex { get; }
            public int PathCount { get; }
            public int StoredFrame { get; }
            public int DrawnFrame { get; }
            public int PublishedWorldX { get; }
            public int PublishedWorldY { get; }
            public uint LastFrameTick { get; }
            public uint LastStateCounter { get; }
            public uint SourceCounter { get; }
            public bool IsComplete { get; }
            public int WaypointX { get; }
            public int WaypointY { get; }
            public int NextWaypointX { get; }
            public int NextWaypointY { get; }
            public int LastStepPublicationCount { get; }

            internal Snapshot(ShipRouteMovement source)
            {
                CellX = source.cellX; CellY = source.cellY;
                WorldPixelX = source.worldX; WorldPixelY = source.worldY;
                Heading = source.heading; TargetHeading = source.targetHeading;
                TurnStep = source.turnStep; State = source.state;
                CenterGate = source.center; Speed = source.speed;
                Remainder = source.remainder; Deceleration = source.deceleration;
                ReservedCellIndex = source.reserved; NextCellIndex = source.next;
                PathIndex = source.pathIndex; PathCount = source.pathCount;
                StoredFrame = source.frame; DrawnFrame = source.drawnFrame;
                PublishedWorldX = source.publishedX; PublishedWorldY = source.publishedY;
                LastFrameTick = source.lastFrameTick;
                LastStateCounter = source.lastStateCounter; SourceCounter = source.counter;
                WaypointX = source.PointX(source.pathIndex); WaypointY = source.PointY(source.pathIndex);
                NextWaypointX = source.PointX(source.pathIndex+1); NextWaypointY = source.PointY(source.pathIndex+1);
                LastStepPublicationCount = source.LastStepPublicationCount;
                IsComplete = source.hasRoute && source.state == 0 &&
                    source.cellX == source.goalX && source.cellY == source.goalY &&
                    source.worldX == source.goalX * 64 + 4 && source.worldY == source.goalY * 64 + 4;
            }
        }



        private static readonly int[] DirectionX = {1,1,0,-1,-1,-1,0,1};
        private static readonly int[] DirectionY = {0,-1,-1,-1,0,1,1,1};
        private static readonly int[,] FleetCells =
        { {16,2},{21,5},{19,4},{11,18},{9,21},{10,22},{6,13},{6,14} };
        private static readonly uint[] FleetClasses = {200,200,207,201,206,206,206,206};
        private readonly MissionOccupancyGrid grid;
        private readonly object owner;
        private readonly object[] fleetOwners = new object[8];
        private byte[] points;
        private int cellX=16,cellY=2,worldX=1028,worldY=132,goalX,goalY,pathIndex,pathCount;
        private sbyte heading=5,targetHeading,turnStep;
        private byte state;
        private bool center,hasRoute,stopped;
        private int speed,remainder,deceleration,reserved=-1,next,baseAcceleration=1200;
        private int frame=20,drawnFrame=20,publishedX=1028,publishedY=132;
        private uint counter,lastFrameTick,lastStateCounter;
        private Publication publication0,publication1;
        private GridMutation mutation0,mutation1;

        public Snapshot Current => new Snapshot(this);
        public bool HasRoute => hasRoute;
        public bool IsStopped => stopped;
        public bool LastStepPublishesPose => LastStepPublicationCount != 0;
        public bool LastStepReachedForwardTail { get; private set; }
        public int LastStepPublicationCount { get; private set; }
        internal int LastStepGridMutationCount { get; private set; }

        public Publication GetLastStepPublication(int index)
        {
            if(index<0 || index>=LastStepPublicationCount) throw new ArgumentOutOfRangeException(nameof(index));
            return index==0 ? publication0 : publication1;
        }
        internal GridMutation GetLastStepGridMutation(int index)
        {
            if(index<0 || index>=LastStepGridMutationCount) throw new ArgumentOutOfRangeException(nameof(index));
            return index==0 ? mutation0 : mutation1;
        }

        public ShipRouteMovement(MissionOccupancyGrid grid,object ownerIdentity,MissionShipSeed source0b)
        {
            if(grid==null) throw new ArgumentNullException(nameof(grid));
            if(ownerIdentity==null) throw new ArgumentNullException(nameof(ownerIdentity));
            if(source0b.InstanceId!=0xbu || source0b.CellX!=16 || source0b.CellY!=2 || source0b.Heading!=5 ||
               source0b.ModelValue!=0 || source0b.OwnerSide!=1 || source0b.OwnerPlayer!=1 ||
               source0b.RequestedHealthPercent!=100 || source0b.SourceEquipmentA!=0 ||
               source0b.SourceEquipmentB!=0 || source0b.SourceOrderCount!=0)
                throw new NotSupportedException("Only the controlled full-health source0b recipe is supported.");
            if(grid.Width!=24 || grid.Height!=24) throw new NotSupportedException("The source24x24 grid is required.");
            this.grid=grid;owner=ownerIdentity;
            for(int i=0;i<8;i++)
            {
                fleetOwners[i]=grid.GetOccupant(FleetCells[i,0],FleetCells[i,1]);
                if(fleetOwners[i]==null) throw new NotSupportedException("All eight static source fleet owners are required.");
                for(int j=0;j<i;j++)
                    if(ReferenceEquals(fleetOwners[i],fleetOwners[j]))
                        throw new NotSupportedException("The source fleet requires distinct owner references.");
            }
            if(!ReferenceEquals(fleetOwners[0],owner)) throw new ArgumentException("Retain source0b's origin owner.",nameof(ownerIdentity));
            int occupied=0;
            for(int y=0;y<24;y++) for(int x=0;x<24;x++) if(grid.GetOccupant(x,y)!=null) occupied++;
            if(occupied!=8) throw new NotSupportedException("Only the initial eight fleet claims are supported.");
        }

        public bool TryBegin(ShipRoutePlan plan,uint plannerCounter=1)
        {
            if(hasRoute) throw new InvalidOperationException("This diagnostic can begin one source route.");
            if(plannerCounter!=1u) throw new NotSupportedException("The verified planner counter is1.");
            counter=plannerCounter;
            if(plan==null) return false;
            if(plan.OriginX!=16 || plan.OriginY!=2 || plan.InitialHeading!=5 || plan.PathCount<2)
                throw new NotSupportedException("A source0b plan is required.");
            if(!ReferenceEquals(grid.GetOccupant(cellX,cellY),owner))
                throw new InvalidOperationException("The source origin owner changed before Begin.");
            points=plan.CapturePoints();pathCount=plan.PathCount;pathIndex=plan.PathIndex;
            goalX=plan.TargetX;goalY=plan.TargetY;targetHeading=plan.TargetHeading;
            state=plan.InitialState;center=plan.CenterGate;hasRoute=true;
            return true;
        }
        public byte[] CaptureRoutePoints() => points==null ? new byte[0] : (byte[])points.Clone();
        private int PointCoordinate(int index,int offset)
        {
            if(points==null || index<0 || index>=pathCount) return -1;
            return unchecked((short)(points[index*5+offset] | points[index*5+offset+1]<<8));
        }
        private int PointX(int index) => PointCoordinate(index,0);
        private int PointY(int index) => PointCoordinate(index,2);
        private sbyte PointHeading(int index) => unchecked((sbyte)points[index*5+4]);

        private ShipNavigationOccupant Describe(object identity)
        {
            if(ReferenceEquals(identity,owner)) return new ShipNavigationOccupant(200,state);
            for(int i=1;i<8;i++)
                if(ReferenceEquals(identity,fleetOwners[i]))
                    return new ShipNavigationOccupant(FleetClasses[i],0);
            throw new NotSupportedException("Unknown corner owners and dynamic linked ships are outside the static fleet.");
        }
        private void RecordMutation(int index,bool occupied)
        {
            if(LastStepGridMutationCount>=2) throw new NotSupportedException("The verified route exceeded two grid mutations in one call.");
            var entry=new GridMutation(index,occupied);
            if(LastStepGridMutationCount++==0) mutation0=entry;else mutation1=entry;
        }
        private void ClearOwned(int index)
        {
            int x=index%24,y=index/24;
            if(grid.Release(x,y,owner)) RecordMutation(index,false);
        }
        private bool TryReserve(int index)
        {
            // Native out-of-path return occurs BEFORE clearing a reservation.
            if(index>=pathCount) return false;
            if(reserved>=0)
            {
                if(reserved!=cellY*24+cellX) ClearOwned(reserved);
                reserved=-1;
            }
            int x=PointX(index),y=PointY(index);sbyte direction=PointHeading(index);
            if(!ShipAdjacentQuery.CanEnter(grid,owner,x,y,unchecked((byte)direction),0,Describe)) return false;
            targetHeading=direction;
            if(grid.GetOccupant(x,y)==null && grid.TryClaim(x,y,owner)) RecordMutation(y*24+x,true);
            int target=y*24+x;
            if(target!=cellY*24+cellX) reserved=target;
            next=target;baseAcceleration=1200;
            return true;
        }
        private void PublishPose()
        {
            if(LastStepPublicationCount>=2) throw new NotSupportedException("The verified source route exceeded two publications in one call.");
            var entry=new Publication(frame,worldX,worldY);
            if(LastStepPublicationCount++==0) publication0=entry;else publication1=entry;
            drawnFrame=frame;publishedX=worldX;publishedY=worldY;
        }
        private static int AngularDistance(sbyte first,sbyte second)
        {
            int distance=Math.Abs(first-second);return distance>4 ? 8-distance : distance;
        }
        private bool BeginPoint()
        {
            targetHeading=PointHeading(pathIndex);
            int distance=AngularDistance(heading,targetHeading);
            if(distance>1 || distance==1 && speed==0) {state=2;turnStep=0;return false;}
            if(!TryReserve(pathIndex))
            {
                if(unchecked(counter-lastStateCounter)>49u)
                {
                    state=0;turnStep=1;
                    if(reserved>=0 && reserved!=cellY*24+cellX) ClearOwned(reserved);
                    reserved=-1;stopped=true;
                }
                return false;
            }
            if(state==0 || state==2 || state==3) center=true;
            state=5;
            if(distance!=0) {frame=targetHeading<<2;lastFrameTick=counter;PublishPose();}
            heading=targetHeading;
            return true;
        }
        private void BeginBraking()
        {
            if(state==4) return;
            int dx,dy,current=cellY*24+cellX;
            if(next==current)
            {
                dx=Math.Abs(worldX+28-cellX*64-32)+64;
                dy=Math.Abs(worldY+28-cellY*64-32)+64;
            }
            else
            {
                // Preserve the source's flat-index reference in its center1
                // branch; do not replace it with an intuitive cell vector.
                int referenceX=center ? unchecked(next*64+32) : cellX*64+32;
                int referenceY=center ? unchecked(next*64+32) : cellY*64+32;
                dx=Math.Abs(worldX+28-referenceX);dy=Math.Abs(worldY+28-referenceY);
            }
            int distance=Math.Max(dx,dy);
            if(unchecked(distance*3000)!=0)
            {
                state=4;deceleration=unchecked(speed*speed)/(unchecked(distance*-6000));return;
            }
            state=0;turnStep=1;
            if(reserved>=0 && reserved!=current) ClearOwned(reserved);
            reserved=-1;state=4;
        }

        public void Step(int pendingSteps,uint sourceCounter)
        {
            if(pendingSteps!=1 && pendingSteps!=2 && pendingSteps!=3 && pendingSteps!=7)
                throw new ArgumentOutOfRangeException(nameof(pendingSteps));
            if(!hasRoute) throw new InvalidOperationException("Begin a native source route first.");
            LastStepPublicationCount=0;LastStepGridMutationCount=0;LastStepReachedForwardTail=false;
            if(stopped) return;
            if(sourceCounter!=unchecked(counter+1u)) throw new ArgumentException("Advance the reference counter once per call.",nameof(sourceCounter));
            counter=sourceCounter;
            unchecked
            {
                if(state==2)
                {
                    lastStateCounter=counter;
                    var turn=ShipTurnProgression.Advance(frame,heading,targetHeading,turnStep,counter,lastFrameTick,2u,true,state,center?(byte)1:(byte)0);
                    frame=turn.Frame;heading=turn.Heading;turnStep=turn.TurnStep;lastFrameTick=turn.LastTick;
                    state=turn.State;center=turn.ChangedMarker!=0;
                    if(turn.PublishesPose) PublishPose();
                    return;
                }
                if(state==3 && !BeginPoint()) return;
                if(state!=4 && state!=5) throw new NotSupportedException("Only source turn, travel and braking states are projected.");
                lastStateCounter=counter;
                int oldX=worldX,oldY=worldY;
                int acceleration=(state==4 ? deceleration : baseAcceleration)*60/100;
                int newSpeed=speed+pendingSteps*acceleration;
                if(newSpeed<=0 && state==4) {newSpeed=0;deceleration=0;}
                if(newSpeed>36000) newSpeed=36000;
                if(newSpeed<=6000 && acceleration<0) newSpeed=speed;
                speed=newSpeed;
                int total=pendingSteps*speed+remainder,q=total/3000;
                remainder=total%3000;
                int dx=DirectionX[heading],dy=DirectionY[heading];
                int divisor=Math.Abs(dx)+Math.Abs(dy)==1 ? 2 : 3;
                int candidateX=oldX+q*dx/divisor,candidateY=oldY+q*dy/divisor;
                remainder+=q%divisor*3000;
                // Native local_2c is decided BEFORE waypoint clamping.
                bool attempted=candidateX!=oldX || candidateY!=oldY;
                int anchorX=PointX(pathIndex)*64+4,anchorY=PointY(pathIndex)*64+4;
                if(dx>0 && candidateX>anchorX || dx<0 && candidateX<anchorX) candidateX=anchorX;
                if(dy==0) {if(dx!=0 && candidateY!=anchorY) candidateY=anchorY;}
                else if(dy>0 && candidateY>anchorY || dy<0 && candidateY<anchorY) candidateY=anchorY;
                if(attempted)
                {
                    worldX=candidateX;worldY=candidateY;
                    int oldCellX=(oldX+28)/64,oldCellY=(oldY+28)/64,oldCell=oldCellY*24+oldCellX;
                    bool skipAnchor=false;
                    if(center && oldCell==next)
                    {
                        ClearOwned(cellY*24+cellX);center=false;
                        cellX=oldCellX;cellY=oldCellY;reserved=-1;
                        if(oldCell==goalY*24+goalX) {BeginBraking();skipAnchor=true;}
                        else if(TryReserve(pathIndex+1)) skipAnchor=true;
                        else BeginBraking();
                    }
                    else if(!center && reserved<0 && !TryReserve(pathIndex+1)) BeginBraking();
                    if(!skipAnchor && worldX==anchorX && worldY==anchorY)
                    {
                        center=true;
                        if(state==4 && oldCell==goalY*24+goalX)
                        {
                            state=0;turnStep=1;
                            if(reserved>=0 && reserved!=cellY*24+cellX) ClearOwned(reserved);
                            reserved=-1;speed=0;stopped=true;
                        }
                        else
                        {
                            if(pathIndex<pathCount-1) pathIndex++;
                            state=3;
                        }
                    }
                }
                LastStepReachedForwardTail=true;
                var forward=ShipFrameProgression.AdvanceForward(frame,heading,counter,lastFrameTick,2u);
                frame=forward.Frame;lastFrameTick=forward.LastTick;
                if(attempted) PublishPose();
            }
        }
    }
}
