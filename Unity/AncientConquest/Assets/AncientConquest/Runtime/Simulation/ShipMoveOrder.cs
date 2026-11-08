using System;
using AncientConquest.World;

namespace AncientConquest.Simulation
{
    /// <summary>
    /// Bounded healthy local request, promotion, normal work and MoveShip chain.
    /// Controlled wind0/5 and upgrade0; this projects the source counter schedule,
    /// not the complete Life loop. The original constructor retains source0b's
    /// stationary-peer contract. CreatePreparedLocal uses explicit routes for
    /// actual0b/0c/0d; CreateLiveLocal adds normal idle requests and live planning.
    /// </summary>
    public sealed class ShipMoveOrder
    {
        /// <summary>
        /// Immutable4a49af/4a4a67 ->4a1700 call observation. The source event's
        /// counter+4 and cell+10 are captured here;fleet/member identity remains
        /// owned by ShipFleetMembership. This is NOT a task update or mail packet.
        /// </summary>
        public readonly struct Arrival
        {
            public uint Counter { get; }
            public int CellIndex { get; }
            // Matches4a1700's source-counter and param4 cell fields only.
            internal Arrival(uint counter, int cellIndex) { Counter = counter; CellIndex = cellIndex; }
        }

        public readonly struct Publication
        {
            public int Frame { get; }
            public int WorldPixelX { get; }
            public int WorldPixelY { get; }
            public int Depth { get; }
            internal Publication(int frame,int x,int y,int logicalSize=56)
            {
                Frame = frame; WorldPixelX = x; WorldPixelY = y;
                Depth = Math.Max(10000,unchecked(20000-logicalSize-y));
            }
        }
        internal readonly struct GridMutation
        {
            internal int CellIndex { get; }
            internal bool Occupied { get; }
            internal GridMutation(int index,bool occupied) { CellIndex = index; Occupied = occupied; }
        }

        public readonly struct MotionSnapshot
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
            public int PathEndpointX { get; }
            public int PathEndpointY { get; }
            public int LastCellIndex { get; }

            internal MotionSnapshot(ShipMoveOrder source)
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
                LastCellIndex = source.lastCell;
                PathEndpointX = source.hasRoute ? source.lastCell%24 : -1;
                PathEndpointY = source.hasRoute ? source.lastCell/24 : -1;
                IsComplete = source.hasRoute && source.state == 0 &&
                    source.cellX == source.lastCell%24 && source.cellY == source.lastCell/24 &&
                    source.worldX == source.lastCell%24 * 64 + source.anchorOffset && source.worldY == source.lastCell/24 * 64 + source.anchorOffset;
            }
        }



        public readonly struct Snapshot
        {
            public MotionSnapshot Motion { get; }
            public uint SourceCounter { get; }
            public uint PendingFlags { get; }
            public uint ActiveFlags { get; }
            public uint DeferredFlags { get; }
            public uint StopMask { get; }
            public uint ReadyMask { get; }
            public uint Capabilities { get; }
            public int RequestedGoalX { get; }
            public int RequestedGoalY { get; }
            public int TargetX { get; }
            public int TargetY { get; }
            public bool FirstNavigation { get; }
            public byte Retry { get; }
            public uint LastPlanCounter { get; }
            public uint RetryInterval { get; }
            public uint SnapshotRetry { get; }
            public int SnapshotTargetX { get; }
            public int SnapshotTargetY { get; }
            public int SnapshotCellX { get; }
            public int SnapshotCellY { get; }
            public uint RandomState { get; }
            public int CachedObstacleCount { get; }
            public bool RequestedTargetReached { get; }
            public bool CanRequestMove { get; }
            public int NavigationRadius { get; }
            internal Snapshot(ShipMoveOrder s)
            {
                Motion=new MotionSnapshot(s);SourceCounter=s.counter;
                PendingFlags=s.pendingFlags;ActiveFlags=s.activeFlags;DeferredFlags=s.deferredFlags;
                StopMask=s.stopMask;ReadyMask=s.readyMask;Capabilities=s.capabilities;
                RequestedGoalX=s.requestedX;RequestedGoalY=s.requestedY;TargetX=s.targetX;TargetY=s.targetY;
                FirstNavigation=s.firstNavigation;Retry=s.retry;LastPlanCounter=s.lastPlan;
                RetryInterval=s.retryInterval;SnapshotRetry=s.snapshotRetry;
                SnapshotTargetX=s.snapshotTargetX;SnapshotTargetY=s.snapshotTargetY;
                SnapshotCellX=s.snapshotCellX;SnapshotCellY=s.snapshotCellY;
                RandomState=s.randomState;CachedObstacleCount=s.cachedObstacles.Length;
                RequestedTargetReached=s.cellX==s.targetX && s.cellY==s.targetY && s.state==0 &&
                    s.worldX==s.targetX*64+s.anchorOffset && s.worldY==s.targetY*64+s.anchorOffset;
                CanRequestMove=s.CanRequestMove;NavigationRadius=s.navigationRadius;
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
        private int cellX=16,cellY=2,worldX=1028,worldY=132,pathIndex,pathCount;
        private sbyte heading=5,targetHeading,turnStep;
        private byte state;
        private bool center,hasRoute;
        private int lastCell;
        private uint pendingFlags,activeFlags,deferredFlags=0,stopMask,readyMask=0xffffffffu;
        private readonly uint capabilities=0xfffff7ffu;
        private readonly int logicalSize=56,halfSize=28,anchorOffset=4,maximumSpeed=60000,reservationAcceleration=1200;
        private readonly bool preparedLocal;
        private readonly Func<object,ShipNavigationOccupant> liveDescribe;
        private bool liveOrders;
        private Func<short> readSimulationGroup;
        private Func<object,ShipPlanningOccupant> planningDescribe;
        private uint instanceId=11;
        private readonly byte[] pendingMoveRecord=new byte[26];
        private int requestedX,requestedY,targetX,targetY;
        private byte priority,retry;
        private byte moveBlockingGate; //actor+58b;4dc53a initializes0,4e2180 restores it.
        private bool firstNavigation;
        private uint lastPlan,retryInterval,snapshotRetry,randomState,interval=2;
        private int snapshotTargetX,snapshotTargetY,snapshotCellX,snapshotCellY,navigationRadius;
        private int[] cachedObstacles=new int[0];
        private int speed,remainder,deceleration,reserved=-1,next,baseAcceleration=1200;
        private int frame=20,drawnFrame=20,publishedX=1028,publishedY=132;
        private uint counter,lastFrameTick,lastStateCounter;
        private Publication publication0,publication1;
        private Arrival arrival;
        private readonly GridMutation[] mutations=new GridMutation[8];

        public Snapshot Current => new Snapshot(this);
        public bool HasRoute => hasRoute;
        public bool CanRequestMove => (!preparedLocal || liveOrders) && state==0 && (activeFlags&0x80u)==0 && (pendingFlags&0x88u)==0;
        public uint InstanceId=>instanceId;
        public int CurrentAcceleration => baseAcceleration;
        public int LogicalSize => logicalSize;
        public int MaximumSpeed => maximumSpeed;
        public bool IsPreparedLocal => preparedLocal;
        //Managed admission for4e2ba0's verified live-local normal20 projection.
        public bool HasNormalCellMoveReceiver => liveOrders;
        //4abe87 reads this byte;not physical state58c or center596.
        public byte MoveBlockingGate => moveBlockingGate;
        public bool LastStepPublishesPose => LastStepPublicationCount != 0;
        public bool LastStepReachedForwardTail { get; private set; }
        public int LastStepPublicationCount { get; private set; }
        //4a3f40's two arrival sites are mutually exclusive within one bounded Move.
        public int LastStepArrivalCount { get; private set; }
        internal int LastStepGridMutationCount { get; private set; }

        // Read-only4a1700 call observation;world integration must preserve registry order.
        public Arrival GetLastStepArrival(int index)
        {
            if(index<0 || index>=LastStepArrivalCount) throw new ArgumentOutOfRangeException(nameof(index));
            return arrival;
        }

        public Publication GetLastStepPublication(int index)
        {
            if(index<0 || index>=LastStepPublicationCount) throw new ArgumentOutOfRangeException(nameof(index));
            return index==0 ? publication0 : publication1;
        }
        internal GridMutation GetLastStepGridMutation(int index)
        {
            if(index<0 || index>=LastStepGridMutationCount) throw new ArgumentOutOfRangeException(nameof(index));
            return mutations[index];
        }

        public ShipMoveOrder(MissionOccupancyGrid grid,object ownerIdentity,MissionShipSeed source0b,uint sessionSeed=0)
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
            randomState=ShipIdleProgression.InitialRandomState(sessionSeed,source0b.InstanceId);
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

        /// <summary>
        /// Reuse the verified motion/animation/reservation kernel with the actual
        /// initial0b/0c/0d recipe and a live shared-grid occupant view. Prepared
        /// routes are explicit; this does not generalize the source0b planner.
        /// </summary>
        public static ShipMoveOrder CreatePreparedLocal(MissionOccupancyGrid grid, object ownerIdentity,
            MissionShipSeed seed, Func<object,ShipNavigationOccupant> describeOccupant, uint sessionSeed=0) =>
            new ShipMoveOrder(grid, ownerIdentity, seed, describeOccupant, sessionSeed);

        private ShipMoveOrder(MissionOccupancyGrid grid, object ownerIdentity, MissionShipSeed seed,
            Func<object,ShipNavigationOccupant> describeOccupant, uint sessionSeed)
        {
            if(grid==null) throw new ArgumentNullException(nameof(grid));
            if(ownerIdentity==null) throw new ArgumentNullException(nameof(ownerIdentity));
            if(describeOccupant==null) throw new ArgumentNullException(nameof(describeOccupant));
            bool b=seed.InstanceId==11, c=seed.InstanceId==12, d=seed.InstanceId==13;
            if((!b&&!c&&!d) || seed.OwnerSide!=1 || seed.OwnerPlayer!=1 || seed.RequestedHealthPercent!=100 ||
               seed.SourceEquipmentB!=0 || seed.SourceOrderCount!=0 || seed.ModelValue!=(d?7u:0u) ||
               seed.SourceEquipmentA!=(d?1:0) || seed.Heading!=(b?5:4) ||
               seed.CellX!=(b?16:c?21:19) || seed.CellY!=(b?2:c?5:4))
                throw new NotSupportedException("Only the actual initialized local0b/0c/0d recipes at upgrade0/full health are projected.");
            if(grid.Width!=24 || grid.Height!=24) throw new NotSupportedException("The source24x24 grid is required.");
            if(!ReferenceEquals(grid.GetOccupant(seed.CellX,seed.CellY),ownerIdentity))
                throw new ArgumentException("Retain the actual initial actor's owner reference.",nameof(ownerIdentity));
            this.grid=grid;owner=ownerIdentity;liveDescribe=describeOccupant;preparedLocal=true;
            instanceId=seed.InstanceId;
            logicalSize=d?72:56;halfSize=logicalSize/2;anchorOffset=(64-logicalSize)/2;
            maximumSpeed=d?52000:60000;reservationAcceleration=d?1040:1200;
            // Original4bece0 applies equipmentA1 to0d's initial acceleration,
            // while4a3a70 later resets it from4ac110's unmodified model table.
            baseAcceleration=d?884:1200;capabilities=d?0xfffffeffu:0xfffff7ffu;
            cellX=seed.CellX;cellY=seed.CellY;worldX=seed.GetWorldPixelX(logicalSize);worldY=seed.GetWorldPixelY(logicalSize);
            publishedX=worldX;publishedY=worldY;heading=seed.Heading;
            frame=seed.ReferenceFrameIndex;drawnFrame=frame;
            randomState=ShipIdleProgression.InitialRandomState(sessionSeed,seed.InstanceId);
        }

        /// <summary>Normal idle20 receipt, promotion, live planning and shared-grid motion.</summary>
        public static ShipMoveOrder CreateLiveLocal(MissionOccupancyGrid grid,object ownerIdentity,MissionShipSeed seed,
            Func<object,ShipNavigationOccupant> describeOccupant,Func<short> simulationGroup,
            Func<object,ShipPlanningOccupant> describePlanningOccupant,uint sessionSeed=0)
        {
            if(simulationGroup==null)throw new ArgumentNullException(nameof(simulationGroup));
            if(describePlanningOccupant==null)throw new ArgumentNullException(nameof(describePlanningOccupant));
            var result=new ShipMoveOrder(grid,ownerIdentity,seed,describeOccupant,sessionSeed);
            result.liveOrders=true;result.readSimulationGroup=simulationGroup;result.planningDescribe=describePlanningOccupant;
            return result;
        }
        public byte[] CapturePendingMoveRecord()=>(byte[])pendingMoveRecord.Clone();
        public bool ReceiveCellMove(uint addressedInstanceId,int x,int y,byte argument=0)
        {
            if(addressedInstanceId!=instanceId)throw new ArgumentException("Actor routing must match the addressed instance ID.");
            return RequestCellMove(x,y,argument);
        }

        /// <summary>
        /// Matches4e2ba0(action20)->4a9e30(80):one26B pending record,last write wins.
        /// Normal healthy live-local profile;58b defaults0 or comes from source state.
        /// Unlike the legacy idle/UI admission guard,this accepts during motion.
        /// Other task families remain excluded;imported normal blocking gates are supported.
        /// </summary>
        public bool ReceiveNormalCellMove(uint addressedInstanceId,int x,int y,byte argument=0)
        {
            if(addressedInstanceId!=instanceId)throw new ArgumentException("Actor routing must match the addressed instance ID.");
            if(!liveOrders)throw new NotSupportedException("Normal repeated receipt requires the live local profile.");
            if(x<0||x>=24||y<0||y>=24)throw new ArgumentOutOfRangeException(nameof(x));
            if(argument!=0&&argument!=255)throw new NotSupportedException("Only normal0/255 metadata is verified.");
            return StoreCellMove(x,y,argument);
        }

        /// <summary>Explicit normal initial route boundary, before any motion/idle tick.</summary>
        public void InstallPreparedRoute(byte[] route)
        {
            if(!preparedLocal || liveOrders) throw new NotSupportedException("Prepared routes belong to the prepared-only local-motion factory.");
            if(route==null) throw new ArgumentNullException(nameof(route));
            if(counter!=0 || hasRoute) throw new InvalidOperationException("Install the initial prepared route once before ticking.");
            if(route.Length<10 || route.Length%5!=0 || route.Length>576*5)
                throw new ArgumentException("A complete bounded adjacent source route is required.",nameof(route));
            int count=route.Length/5;
            int Read(int index,int offset)=>unchecked((short)(route[index*5+offset]|route[index*5+offset+1]<<8));
            for(int i=0;i<count;i++)
            {
                int x=Read(i,0),y=Read(i,2);
                if(x<0 || y<0 || x>=24 || y>=24 || route[i*5+4]>7)
                    throw new ArgumentException("The prepared route has an invalid source point.",nameof(route));
                if(i==0 && (x!=cellX || y!=cellY)) throw new ArgumentException("The route must start at the actor's actual cell.",nameof(route));
                if(i>0 && ShipReplanPlanner.Direction(x-Read(i-1,0),y-Read(i-1,2))!=route[i*5+4])
                    throw new ArgumentException("Each route heading must describe its incoming adjacent segment.",nameof(route));
            }
            points=(byte[])route.Clone();pathCount=count;pathIndex=1;lastCell=Read(count-1,2)*24+Read(count-1,0);hasRoute=true;
            targetHeading=PointHeading(1);bool aligned=heading==targetHeading;
            state=aligned?(byte)3:(byte)2;center=aligned;turnStep=0;interval=2;
        }

        public bool RequestCellMove(int x,int y,byte opaqueByte=255)
        {
            if(preparedLocal && !liveOrders) throw new NotSupportedException("Prepared-only motion has no request/promotion/planning adapter.");
            if(x<0 || x>=24 || y<0 || y>=24) throw new ArgumentOutOfRangeException(nameof(x));
            if(opaqueByte!=255 && opaqueByte!=0)
                throw new NotSupportedException("Only the normal source priority0 request is supported.");
            if(!CanRequestMove) throw new NotSupportedException("Busy replacement is outside this bounded order adapter.");
            return StoreCellMove(x,y,opaqueByte);
        }
        //4e2ba0 zeroes26B and fills coordinates/metadata;4a9e30 copies to858 and ORs7d6.
        private bool StoreCellMove(int x,int y,byte opaqueByte)
        {
            ResetEffects();requestedX=x;requestedY=y;pendingFlags|=0x80u;
            Array.Clear(pendingMoveRecord,0,pendingMoveRecord.Length);
            for(int i=0;i<4;i++)
            {
                pendingMoveRecord[4+i]=unchecked((byte)((uint)x>>(8*i)));
                pendingMoveRecord[8+i]=unchecked((byte)((uint)y>>(8*i)));
            }
            pendingMoveRecord[25]=opaqueByte;
            return true;
        }
        public int[] CaptureCachedObstacles() => (int[])cachedObstacles.Clone();
        private void ResetEffects()
        {
            LastStepPublicationCount=0;LastStepGridMutationCount=0;LastStepReachedForwardTail=false;
            LastStepArrivalCount=0;
        }
        public void Tick(uint sourceCounter,int pendingSteps=1)
        {
            if(pendingSteps!=1 && pendingSteps!=2 && pendingSteps!=3 && pendingSteps!=7)
                throw new ArgumentOutOfRangeException(nameof(pendingSteps));
            if(sourceCounter!=unchecked(counter+1u))
                throw new ArgumentException("Advance the source counter once per tick.",nameof(sourceCounter));
            ResetEffects();counter=sourceCounter;
            if(preparedLocal && !liveOrders) {Move(pendingSteps);return;}
            if((pendingFlags&8u)!=0 && (readyMask&8u)!=0)
            {
                if(stopMask==0)
                {
                    //4aa540 zero-mask cancellation:discard pending/deferred task bits.
                    activeFlags&=~0x80u;StopNavigation();deferredFlags=0;pendingFlags&=0xfffffe07u;
                }
                else if((stopMask&0x480u)!=0)
                {
                    activeFlags&=~0x80u;StopNavigation();stopMask&=~0x80u;
                }
                pendingFlags&=~8u;
            }
            if((pendingFlags&0x1f0u)!=0 || deferredFlags!=0)ArbitrateNormalMove();
            if((pendingFlags&0x80u)!=0 && (readyMask&0x80u)!=0)
            {
                targetX=requestedX;targetY=requestedY;
                snapshotRetry=0;snapshotTargetX=0;snapshotTargetY=0;snapshotCellX=0;snapshotCellY=0;
                lastPlan=0;retryInterval=25;firstNavigation=true;retry=0;
                //4ab250 applies metadata at promotion;255 preserves current priority.
                if(pendingMoveRecord[25]!=255)priority=pendingMoveRecord[25];
                pendingFlags&=~0xf0u;activeFlags|=0x80u;
            }
            // ProcShipsWork's normal capability4000 branch keeps400 active.
            activeFlags|=0x400u;
            if((activeFlags&0x80u)!=0) WorkMoveOrder();
            if((activeFlags&0x400u)!=0) Move(pendingSteps);
        }
        //4abe50->4abc60->4a6330,normal80 only;other active task families excluded.
        private void ArbitrateNormalMove()
        {
            if((activeFlags&0x80u)==0 || moveBlockingGate==0)
            {
                if((pendingFlags&0x1f0u)==0)
                {if((deferredFlags&0x1f0u)==0)return;pendingFlags=deferredFlags;}
                deferredFlags=0;activeFlags&=0xffffff0fu;return;
            }
            if((pendingFlags&0x80u)!=0)deferredFlags=0x80u;
            activeFlags&=~0x80u;StopNavigation();
            //Source quirk:nonzero pending after cancellation discards the candidate.
            if(pendingFlags!=0)deferredFlags=0;
            pendingFlags&=0xfffffe0fu;
        }

        //4e12e0/4e2180 native layout projection;no native pointer is dereferenced.
        private sealed class SourceRecord
        {
            internal readonly byte[] Data,Route;
            internal readonly int[] Cache;
            internal readonly int Sprite;
            //4e2180 restores route5B records,55f2e0 vector payload,and sprite21B tail.
            internal SourceRecord(byte[] bytes)
            {
                if(bytes==null)throw new ArgumentNullException(nameof(bytes));
                Data=(byte[])bytes.Clone();if(Data.Length<0x89d)throw new ArgumentException("Incomplete source record.");
                int count=A(0x5ba);if(count<0||count>576)throw new NotSupportedException("Route count outside local profile.");
                int at=0x89d;int length=A(0x5c2)==0?0:count*5;
                Need(at,length);Route=new byte[length];Array.Copy(Data,at,Route,0,length);at+=length;
                for(int i=0;i<Route.Length;i+=5)
                {
                    int x=Route[i]|Route[i+1]<<8,y=Route[i+2]|Route[i+3]<<8;
                    if(x>=24||y>=24||Route[i+4]>7)throw new NotSupportedException("Route point outside source local map.");
                }
                Cache=new int[0];
                if(A(0x5cd)!=0)
                {
                    int size=I(at);at+=4;Need(at,size);int stride=I(at+8),n=I(at+12);
                    if(size<28||stride!=4||n<0||n>576||size!=28+4*n)throw new NotSupportedException("Unsupported source cache vector.");
                    Cache=new int[n];for(int i=0;i<n;i++)Cache[i]=I(at+28+i*4);at+=size;
                }
                foreach(int p in new[]{0x6df,0x766,0x7a9})if(A(p)!=0)throw new NotSupportedException("Other task arrays excluded.");
                foreach(int p in new[]{0x875,0x879,0x87d,0x881,0x885,0x88d,0x891,0x899})
                    if(I(p)!=0)throw new NotSupportedException("Other visual/object records excluded.");
                Sprite=at;Need(at,21);
                if(I(0x871)==0||Data[at]!=1||at+21!=Data.Length)throw new NotSupportedException("One source body sprite is required.");
            }
            //Managed bounds on the source byte projection,not a gameplay rule.
            internal void Need(int at,int length)
            {if(at<0||length<0||(long)at+length>Data.Length)throw new ArgumentException("Truncated source state.");}
            //Source little-endian unaligned32-bit accesses.
            internal int I(int at)
            {Need(at,4);return unchecked((int)((uint)Data[at]|(uint)Data[at+1]<<8|(uint)Data[at+2]<<16|(uint)Data[at+3]<<24));}
            //4e12e0/4e2180 offset correspondence for the supported actor regions.
            internal static int Offset(int actor)
            {
                if(actor>=0x269&&actor<=0x54b)return actor-0x49;
                if(actor>=0x54c&&actor<=0x5d0)return actor-0x49;
                if(actor>=0x5d1&&actor<=0x695)return actor-0x49;
                if(actor>=0x696&&actor<=0x7d5)return actor-0x49;
                if(actor>=0x7d6&&actor<=0x8bd)return actor-0x4d;
                if(actor==0x25d)return 0x214;if(actor==0x261)return 0x218;
                throw new NotSupportedException("Actor offset outside source projection.");
            }
            //Read an actor field through the documented source snapshot layout.
            internal int A(int actor)=>I(Offset(actor));
            //Source byte fields within the copied movement block.
            internal byte B(int actor)=>Data[Offset(actor)];
        }

        /// <summary>
        /// Bounded4e2180 normal local movement restore,with explicit source counter.
        /// Caller restores cohort clock/membership/grid context;no Unity objects or
        /// native pointers are imported. Other task families/graphics are excluded.
        /// Deferred265 is NOT serialized by4e12e0 and survives,as in4e2180.
        /// </summary>
        private SourceRecord PrepareSourceMovementState(byte[] sourceRecord)
        {
            if(!liveOrders)throw new NotSupportedException("Live local state is required.");
            var r=new SourceRecord(sourceRecord);
            int x=r.A(0x5a3),y=r.A(0x5a7),reservation=r.A(0x5ab),nextCell=r.A(0x5b6);
            short group=unchecked((short)(r.Data[0x26]|r.Data[0x27]<<8));
            if(unchecked((uint)r.I(0x18))!=instanceId||r.I(0x14)!=(instanceId==13?207:200)||
                r.Data[0x1c]!=1||r.Data[0x1d]!=1||r.Data[0x1e]!=1||r.Data[0x1f]!=1||
                unchecked((uint)r.A(0x261))!=capabilities||r.A(0x59f)!=maximumSpeed||r.Data[0x208]!=0||
                (unchecked((uint)r.A(0x25d))&~0x480u)!=0||(unchecked((uint)r.A(0x7d6))&~0x88u)!=0||
                (deferredFlags&~0x80u)!=0||(unchecked((uint)r.A(0x818))&~0x480u)!=0||r.B(0x592)!=0||r.B(0x54c)!=0||r.B(0x54d)!=0||r.B(0x858)!=0||r.B(0x864)!=0||
                (r.B(0x871)!=0&&r.B(0x871)!=255)||r.B(0x5c7)!=0||r.B(0x58c)>5||
                r.B(0x5af)>7||r.B(0x5b1)>7||r.I(r.Sprite+1)<0||r.I(r.Sprite+1)>=88||
                x<0||x>=24||y<0||y>=24||reservation< -1||reservation>=576||nextCell< -1||nextCell>=576)
                throw new NotSupportedException("State is outside the verified healthy normal movement profile.");
            if(group!=readSimulationGroup())throw new InvalidOperationException("Restore membership through its documented41 boundary first.");
            //4e2180 reclaims current/reserved cells without clearing unrelated slots.
            //Projection guard:cohort grid must already contain matching owner context.
            for(int cy=0;cy<24;cy++)for(int cx=0;cx<24;cx++)
            {
                int cell=cy*24+cx;object occupant=grid.GetOccupant(cx,cy);
                if(ReferenceEquals(occupant,owner)&&cell!=y*24+x&&cell!=reservation&&cell!=nextCell)
                    throw new InvalidOperationException("Restore cohort occupancy before actor state.");
                if((cell==y*24+x||cell==reservation)&&occupant!=null&&!ReferenceEquals(occupant,owner))
                    throw new InvalidOperationException("Imported claim conflicts with cohort occupancy.");
            }
            //All bounded reads/allocations complete before mutation.
            r.Need(SourceRecord.Offset(0x858),26);
            return r;
        }

        //Managed in-place cohort guard around4e2180:clock/claims/pose context
        //must match before the caller refreshes existing render bindings.
        public void ValidateInPlaceSourceMovementState(byte[] sourceRecord,uint sourceCounter)
        {
            var r=PrepareSourceMovementState(sourceRecord);
            if(sourceCounter!=counter||r.A(0x5a3)!=cellX||r.A(0x5a7)!=cellY||r.A(0x5ab)!=reserved||r.A(0x5b6)!=next||
                r.I(r.Sprite+5)!=publishedX||r.I(r.Sprite+9)!=publishedY||
                !ReferenceEquals(grid.GetOccupant(cellX,cellY),owner)||
                (reserved>=0&&!ReferenceEquals(grid.GetOccupant(reserved%24,reserved/24),owner)))
                throw new InvalidOperationException("In-place source context differs from the live cohort.");
        }

        //4e2180 normal movement projection;the source counter is explicit context.
        public void RestoreSourceMovementState(byte[] sourceRecord,uint sourceCounter)
        {
            var r=PrepareSourceMovementState(sourceRecord);
            int x=r.A(0x5a3),y=r.A(0x5a7),reservation=r.A(0x5ab),nextCell=r.A(0x5b6);
            ResetEffects();counter=sourceCounter;randomState=unchecked((uint)r.I(0x2c));
            activeFlags=unchecked((uint)r.A(0x25d));pendingFlags=unchecked((uint)r.A(0x7d6));
            readyMask=unchecked((uint)r.A(0x7da));stopMask=unchecked((uint)r.A(0x818));
            cellX=x;cellY=y;reserved=reservation;next=nextCell;lastCell=r.A(0x5b2);
            state=r.B(0x58c);moveBlockingGate=r.B(0x58b);center=r.B(0x596)!=0;
            heading=unchecked((sbyte)r.B(0x5af));targetHeading=unchecked((sbyte)r.B(0x5b1));turnStep=unchecked((sbyte)r.B(0x5b0));
            speed=r.A(0x59b);remainder=r.A(0x597);deceleration=r.A(0x284);baseAcceleration=r.A(0x280);
            pathCount=r.A(0x5ba);pathIndex=r.A(0x5be);points=r.Route;hasRoute=r.Route.Length!=0;cachedObstacles=r.Cache;
            targetX=r.A(0x54e);targetY=r.A(0x552);requestedX=r.A(0x85c);requestedY=r.A(0x860);
            retry=r.B(0x591);firstNavigation=r.B(0x593)!=0;priority=r.B(0x5c7);
            lastPlan=unchecked((uint)r.A(0x57b));retryInterval=unchecked((uint)r.A(0x57f));navigationRadius=r.A(0x5c9);
            snapshotRetry=unchecked((uint)r.A(0x562));snapshotTargetX=r.A(0x56b);snapshotTargetY=r.A(0x56f);snapshotCellX=r.A(0x573);snapshotCellY=r.A(0x577);
            lastStateCounter=unchecked((uint)r.A(0x58d));
            Array.Copy(r.Data,SourceRecord.Offset(0x858),pendingMoveRecord,0,26);
            frame=r.I(r.Sprite+1);drawnFrame=frame;worldX=r.I(r.Sprite+5);worldY=r.I(r.Sprite+9);publishedX=worldX;publishedY=worldY;
            interval=unchecked((uint)r.I(r.Sprite+13));lastFrameTick=unchecked((uint)r.I(r.Sprite+17));
            grid.TryClaim(x,y,owner);if(reservation>=0)grid.TryClaim(reservation%24,reservation/24,owner);
        }
        private void QueueStop() { pendingFlags|=8u;stopMask|=0x80u; }
        private void SaveRetryInputs()
        {
            snapshotRetry=retry;snapshotTargetX=targetX;snapshotTargetY=targetY;
            snapshotCellX=cellX;snapshotCellY=cellY;
        }
        private void WorkMoveOrder()
        {
            int radius=grid.IsTerrainPassable(targetX,targetY,0) ? 0 : 1;
            if(firstNavigation)
            {
                retry=0;byte result=PlanNavigation(radius);SaveRetryInputs();
                if(result==2 && priority==50) QueueStop();
                return;
            }
            if((retry!=snapshotRetry || cellX!=snapshotCellX || cellY!=snapshotCellY ||
                targetX!=snapshotTargetX || targetY!=snapshotTargetY || state==0) && state!=2 &&
                unchecked(counter-lastPlan)>=retryInterval)
            {
                if(retry==150 || cellX==targetX && cellY==targetY)
                { QueueStop();retry=0;return; }
                byte result=PlanNavigation(radius);
                if(result==2 && priority!=50) result=0;
                SaveRetryInputs();
                if(result==2) {QueueStop();retry=0;}
            }
        }
        private void StopNavigation()
        {
            if(lastPlan==counter) return;
            priority=0;
            if(state==0) return;
            if(state==2 || state==3) {state=0;return;}
            state=1;cachedObstacles=new int[0];
        }
        private byte PlanNavigation(int radius)
        {
            if(lastPlan==counter) return 0;
            int dx=Math.Abs(targetX-cellX),dy=Math.Abs(targetY-cellY);
            int distance=Math.Max(dx,dy)+Math.Min(dx,dy)/2;
            if(distance==1 && priority<51)
            {
                sbyte direction=ShipReplanPlanner.Direction(targetX-cellX,targetY-cellY);
                if(!ShipAdjacentQuery.CanEnter(grid,owner,targetX,targetY,(byte)direction,0,Describe)) return 0;
            }
            if(cellX==targetX && cellY==targetY) return 1;
            if(!grid.IsTerrainPassable(targetX,targetY,0) && radius==0) return 0;
            if(state==0 || state==2 || state==3) center=false;
            bool originCurrent=!center;
            int originX=originCurrent ? cellX : next%24,originY=originCurrent ? cellY : next/24;
            ShipPlanningResult result=liveOrders ?
                ShipReplanPlanner.PlanLive(grid,owner,cellX,cellY,originX,originY,targetX,targetY,radius,retry,true,
                    readSimulationGroup(),planningDescribe,randomState,cachedObstacles) :
                ShipReplanPlanner.Plan(grid,owner,cellX,cellY,originX,originY,targetX,targetY,radius,retry,true,randomState,cachedObstacles);
            randomState=result.RandomStateAfter;cachedObstacles=result.CaptureCachedObstacles();
            navigationRadius=result.RadiusAfterPlan;firstNavigation=false;lastPlan=counter;
            if(result.PointCount==0) {retry=unchecked((byte)(retry+1));return 255;}
            if(!result.HasInstallableRoute)
            {
                byte answer=(byte)(result.PointCount>=2 && result.EndpointX==cellX && result.EndpointY==cellY ? 2 : 0);
                retry=unchecked((byte)(retry+1));return answer;
            }
            byte[] raw=result.CapturePoints();int count=result.PointCount;
            targetHeading=result.FirstHeading;int difference=AngularDistance(heading,targetHeading);
            if(state!=4 && state!=5 || originCurrent)
            { points=raw;pathCount=count;lastCell=result.EndpointY*24+result.EndpointX;hasRoute=true; }
            switch(state)
            {
                case 0:case 3:
                    if(difference==0) {center=true;state=3;} else {turnStep=0;state=2;}
                    interval=2;break;
                case 2:
                    if(difference==0) state=3;else {turnStep=0;state=2;}
                    break;
                case 1:case 4:case 5:
                    if(!originCurrent)
                    {
                        var combined=new byte[raw.Length+5];
                        combined[0]=(byte)cellX;combined[1]=(byte)(cellX>>8);
                        combined[2]=(byte)cellY;combined[3]=(byte)(cellY>>8);combined[4]=unchecked((byte)heading);
                        Buffer.BlockCopy(raw,0,combined,5,raw.Length);
                        points=combined;pathCount=count+1;pathIndex=1;
                        lastCell=result.EndpointY*24+result.EndpointX;hasRoute=true;state=5;return 0;
                    }
                    pathIndex=0;
                    if(difference<2 || TryReserve(1)) {state=5;return 0;}
                    if(state!=4) BeginBraking();
                    return 0;
            }
            pathIndex=1;return 0;
        }
        public byte[] CaptureRoutePoints()
        {
            if(points==null || pathCount==0) return new byte[0];
            var copy=new byte[pathCount*5];Buffer.BlockCopy(points,0,copy,0,copy.Length);return copy;
        }
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
            if(liveDescribe!=null) return liveDescribe(identity);
            if(ReferenceEquals(identity,owner)) return new ShipNavigationOccupant(200,state);
            for(int i=1;i<8;i++)
                if(ReferenceEquals(identity,fleetOwners[i]))
                    return new ShipNavigationOccupant(FleetClasses[i],0);
            throw new NotSupportedException("Unknown corner owners and dynamic linked ships are outside the static fleet.");
        }
        private void RecordMutation(int index,bool occupied)
        {
            if(LastStepGridMutationCount>=mutations.Length) throw new NotSupportedException("The bounded order exceeded its grid mutation capacity.");
            var entry=new GridMutation(index,occupied);
            mutations[LastStepGridMutationCount++]=entry;
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
            if(!ShipAdjacentQuery.CanEnter(grid,owner,x,y,unchecked((byte)direction),0,Describe))
            {
                if(preparedLocal)
                {
                    object blocked=grid.GetOccupant(x,y);
                    if(blocked!=null)
                    {
                        ShipNavigationOccupant view=Describe(blocked);
                        if(view.HasLink) throw new NotSupportedException("Linked/docking/yield orders are outside prepared local motion.");
                        if(view.RuntimeClassTag<200 || view.RuntimeClassTag>211 || view.MovementState==0 || view.MovementState==3 || view.MovementState==6)
                            if(retry<150) retry++;
                    }
                    if(y*24+x!=lastCell && retry<150) retry++;
                }
                return false;
            }
            if(preparedLocal) retry=0;
            targetHeading=direction;
            if(grid.GetOccupant(x,y)==null && grid.TryClaim(x,y,owner)) RecordMutation(y*24+x,true);
            int target=y*24+x;
            if(target!=cellY*24+cellX) reserved=target;
            next=target;baseAcceleration=reservationAcceleration;
            return true;
        }
        private void PublishPose()
        {
            if(LastStepPublicationCount>=2) throw new NotSupportedException("The verified source route exceeded two publications in one call.");
            var entry=new Publication(frame,worldX,worldY,logicalSize);
            if(LastStepPublicationCount++==0) publication0=entry;else publication1=entry;
            drawnFrame=frame;publishedX=worldX;publishedY=worldY;
        }
        // Matches4a49af/4a4a67:stored5b2 passed to4a1700 at each respective source site.
        // Exposes an effect like PublishPose;does not mutate membership,task events or grid.
        private void RecordArrival()
        {
            if(LastStepArrivalCount!=0) throw new NotSupportedException("More than one source arrival per bounded Move is outside the proven branch.");
            arrival=new Arrival(counter,lastCell);LastStepArrivalCount=1;
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
                    reserved=-1;
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
                dx=Math.Abs(worldX+halfSize-cellX*64-32)+64;
                dy=Math.Abs(worldY+halfSize-cellY*64-32)+64;
            }
            else
            {
                // Preserve the source's flat-index reference in its center1
                // branch; do not replace it with an intuitive cell vector.
                int referenceX=center ? unchecked(next*64+32) : cellX*64+32;
                int referenceY=center ? unchecked(next*64+32) : cellY*64+32;
                dx=Math.Abs(worldX+halfSize-referenceX);dy=Math.Abs(worldY+halfSize-referenceY);
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

        private void Move(int pendingSteps)
        {
            unchecked
            {
                if(state==0)
                {
                    lastStateCounter=counter;
                    var idle=ShipIdleProgression.Advance(frame,heading,turnStep,counter,lastFrameTick,interval,
                        randomState,speed,reserved,cellY*24+cellX);
                    randomState=idle.RandomState;speed=idle.Speed;reserved=idle.ReservedCellIndex;
                    turnStep=idle.FrameStep;lastFrameTick=idle.LastTick;interval=idle.Interval;
                    if(idle.ReleasedCellIndex>=0) ClearOwned(idle.ReleasedCellIndex);
                    if(idle.PublishesPose) {frame=idle.PublishedFrame;PublishPose();}
                    frame=idle.Frame;return;
                }
                if(state==1)
                {
                    lastStateCounter=counter;
                    if(!center)
                    {
                        BeginBraking();lastCell=cellY*24+cellX;pathCount=pathIndex+1;
                        if(reserved>=0 && reserved!=lastCell) {ClearOwned(reserved);reserved=-1;}
                    }
                }
                if(state==2)
                {
                    lastStateCounter=counter;
                    var turn=ShipTurnProgression.Advance(frame,heading,targetHeading,turnStep,counter,lastFrameTick,interval,hasRoute,state,center?(byte)1:(byte)0);
                    frame=turn.Frame;heading=turn.Heading;turnStep=turn.TurnStep;lastFrameTick=turn.LastTick;
                    state=turn.State;center=turn.ChangedMarker!=0;
                    if(turn.PublishesPose) PublishPose();
                    return;
                }
                if(state==3 && !BeginPoint()) return;
                if(state!=1 && state!=4 && state!=5) throw new NotSupportedException("Only source turn, travel and braking states are projected.");
                lastStateCounter=counter;
                int oldX=worldX,oldY=worldY;
                int acceleration=(state==4 ? deceleration : baseAcceleration)*60/100;
                int newSpeed=speed+pendingSteps*acceleration;
                if(newSpeed<=0 && state==4) {newSpeed=0;deceleration=0;}
                if(newSpeed>maximumSpeed*60/100) newSpeed=maximumSpeed*60/100;
                if(newSpeed<=maximumSpeed/10 && acceleration<0) newSpeed=speed;
                speed=newSpeed;
                int total=pendingSteps*speed+remainder,q=total/3000;
                remainder=total%3000;
                int dx=DirectionX[heading],dy=DirectionY[heading];
                int divisor=Math.Abs(dx)+Math.Abs(dy)==1 ? 2 : 3;
                int candidateX=oldX+q*dx/divisor,candidateY=oldY+q*dy/divisor;
                remainder+=q%divisor*3000;
                // Native local_2c is decided BEFORE waypoint clamping.
                bool attempted=candidateX!=oldX || candidateY!=oldY;
                int anchorX=PointX(pathIndex)*64+anchorOffset,anchorY=PointY(pathIndex)*64+anchorOffset;
                if(dx>0 && candidateX>anchorX || dx<0 && candidateX<anchorX) candidateX=anchorX;
                if(dy==0) {if(dx!=0 && candidateY!=anchorY) candidateY=anchorY;}
                else if(dy>0 && candidateY>anchorY || dy<0 && candidateY<anchorY) candidateY=anchorY;
                if(attempted)
                {
                    worldX=candidateX;worldY=candidateY;
                    int oldCellX=(oldX+halfSize)/64,oldCellY=(oldY+halfSize)/64,oldCell=oldCellY*24+oldCellX;
                    bool skipAnchor=false;
                    if(center && oldCell==next)
                    {
                        ClearOwned(cellY*24+cellX);center=false;
                        cellX=oldCellX;cellY=oldCellY;reserved=-1;
                        //4a4976..4a49c8:arrival uses the stored goal,BEFORE braking.
                        if(oldCell==lastCell) {RecordArrival();BeginBraking();skipAnchor=true;}
                        else if(TryReserve(pathIndex+1)) skipAnchor=true;
                        else BeginBraking();
                    }
                    else if(!center && reserved<0 && !TryReserve(pathIndex+1))
                    {
                        BeginBraking();
                        //4a4a27..4a4a67:5573d0 reads OLD sprite-derived cells,
                        //not the clamped candidate or a requested-target-reached flag.
                        int ax=Math.Abs(lastCell%24-oldCellX),ay=Math.Abs(lastCell/24-oldCellY);
                        int distance=ax>=ay ? (ay+ax*2)/2 : (ax+ay*2)/2;
                        if(distance==1) RecordArrival();
                    }
                    if(!skipAnchor && worldX==anchorX && worldY==anchorY)
                    {
                        center=true;
                        if(state==4 && oldCell==lastCell)
                        {
                            state=0;turnStep=1;
                            if(reserved>=0 && reserved!=cellY*24+cellX) ClearOwned(reserved);
                            reserved=-1;speed=0;
                        }
                        else
                        {
                            if(pathIndex<pathCount-1) pathIndex++;
                            state=3;
                        }
                    }
                }
                LastStepReachedForwardTail=true;
                var forward=ShipFrameProgression.AdvanceForward(frame,heading,counter,lastFrameTick,interval);
                frame=forward.Frame;lastFrameTick=forward.LastTick;
                if(attempted) PublishPose();
            }
        }
    }
}
