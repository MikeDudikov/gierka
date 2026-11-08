using System;
using System.Collections.Generic;
using AncientConquest.World;

namespace AncientConquest.Simulation
{
    /// <summary>Live fields consumed by normal4a4e20;group is simulation5e,not UI5c.</summary>
    public readonly struct ShipPlanningOccupant
    {
        public uint RuntimeClassTag { get; }
        public byte MovementState { get; }
        public short SimulationGroup { get; }
        public ShipPlanningOccupant(uint runtimeClassTag,byte movementState,short simulationGroup)
        {RuntimeClassTag=runtimeClassTag;MovementState=movementState;SimulationGroup=simulationGroup;}
        internal bool IsShip=>RuntimeClassTag>=200 && RuntimeClassTag<=211;
    }
    /// <summary>
    /// Owned result of GetWayNew/GetWayNear's normal source0b branch.
    /// Requested goal and the installed path endpoint are deliberately separate.
    /// ProcPostMove's stamps, retry count and live route transaction belong
    /// to the caller, not to this map/route adapter.
    /// </summary>
    public sealed class ShipPlanningResult
    {
        private readonly byte[] points;
        private readonly short[] planningField, workingField;
        private readonly int[] cachedObstacles;
        public int RequestedGoalX { get; }
        public int RequestedGoalY { get; }
        public int PointCount => points.Length / 5;
        public int EndpointX => PointCount == 0 ? -1 : Coordinate(PointCount - 1, 0);
        public int EndpointY => PointCount == 0 ? -1 : Coordinate(PointCount - 1, 2);
        public bool UsedNearest { get; }
        public bool ReachedWithinRange { get; }
        public bool HasInstallableRoute => PointCount >= 2 &&
            !(PointCount == 2 && Coordinate(0, 0) == Coordinate(1, 0) && Coordinate(0, 2) == Coordinate(1, 2));
        public sbyte FirstHeading { get; }
        public int RadiusAfterPlan { get; }
        public uint RandomStateAfter { get; }
        public bool RandomStateAdvanced { get; }

        internal ShipPlanningResult(byte[] points, short[] planningField, short[] workingField,
                                    int goalX, int goalY, bool nearest, bool reached, int radius,
                                    uint randomState, bool randomAdvanced, int[] cachedObstacles)
        {
            this.points = (byte[])points.Clone();
            this.planningField = (short[])planningField.Clone(); this.workingField = (short[])workingField.Clone();
            this.cachedObstacles = (int[])cachedObstacles.Clone();
            RequestedGoalX = goalX; RequestedGoalY = goalY; UsedNearest = nearest;
            ReachedWithinRange = reached; RadiusAfterPlan = nearest && !reached ? radius + 1 : radius;
            RandomStateAfter = randomState; RandomStateAdvanced = randomAdvanced;
            FirstHeading = -1;
            if (HasInstallableRoute)
                FirstHeading = ShipReplanPlanner.Direction(Coordinate(1, 0) - Coordinate(0, 0),
                                                           Coordinate(1, 2) - Coordinate(0, 2));
        }
        private int Coordinate(int index, int offset) =>
            unchecked((short)(points[index * 5 + offset] | points[index * 5 + offset + 1] << 8));
        public byte[] CapturePoints() => (byte[])points.Clone();
        public short[] CapturePlanningField() => (short[])planningField.Clone();
        public short[] CaptureWorkingField() => (short[])workingField.Clone();
        public int[] CaptureCachedObstacles() => (int[])cachedObstacles.Clone();
    }

    /// <summary>
    /// Current-origin water planning with restriction0 and route-byte0. Plan
    /// retains the stationary source0b projection; PlanLive reads current peer
    /// state and simulation-group membership, including cached reservations.
    /// </summary>
    public static class ShipReplanPlanner
    {
        private static readonly int[,] StaticCells =
        { {21,5}, {19,4}, {11,18}, {9,21}, {10,22}, {6,13}, {6,14} };

        public static ShipPlanningResult Plan(MissionOccupancyGrid grid, object owner,
                                               int cellX, int cellY, int originX, int originY,
                                               int goalX, int goalY, int radius, byte retryPriority,
                                               bool preserveDestinationMask, uint randomState = 0,
                                               int[] cachedObstacles = null)
        {
            Validate(grid, owner, cellX, cellY, originX, originY, goalX, goalY, radius);
            var cache = new List<int>();
            if (cachedObstacles != null)
                foreach (int index in cachedObstacles)
                {
                    bool known = false;
                    for (int i = 0; i < 7; i++)
                        if (index == StaticCells[i, 1] * 24 + StaticCells[i, 0]) { known = true; break; }
                    if (!known || cache.Contains(index))
                        throw new NotSupportedException("Cached blockers must be unique stationary source cells.");
                    cache.Add(index);
                }
            var field = new short[grid.Width * grid.Height];
            for (int y = 0; y < grid.Height; y++)
                for (int x = 0; x < grid.Width; x++)
                    field[y * grid.Width + x] = grid.IsTerrainPassable(x, y, 0) ? (short)0 : (short)-1;
            short destination = field[goalY * grid.Width + goalX];
            for (int y = Math.Max(0, cellY - 3); y < Math.Min(grid.Height, cellY + 4); y++)
                for (int x = Math.Max(0, cellX - 3); x < Math.Min(grid.Width, cellX + 4); x++)
                {
                    object occupant = grid.GetOccupant(x, y);
                    if (occupant != null && !ReferenceEquals(occupant, owner))
                    {
                        int index = y * grid.Width + x;
                        field[index] = -1;
                        if (!cache.Contains(index)) cache.Add(index);
                    }
                }
            foreach (int index in cache) field[index] = -1;
            return Solve(field,grid.Width,grid.Height,originX,originY,goalX,goalY,radius,retryPriority,
                         preserveDestinationMask,destination,randomState,retryPriority>50,cache);
        }

        /// <summary>
        /// Normal route-byte0 planning against live actors/reservations. Source
        /// retry controls its RNG gate;own route priority remains0,so the
        /// high-priority candidate-cost branch4a5540 is outside this entry.
        /// </summary>
        public static ShipPlanningResult PlanLive(MissionOccupancyGrid grid,object owner,
            int cellX,int cellY,int originX,int originY,int goalX,int goalY,int radius,byte retryPriority,
            bool preserveDestinationMask,short simulationGroup,Func<object,ShipPlanningOccupant> describe,
            uint randomState=0,int[] cachedObstacles=null)
        {
            if(grid==null)throw new ArgumentNullException(nameof(grid));
            if(owner==null)throw new ArgumentNullException(nameof(owner));
            if(describe==null)throw new ArgumentNullException(nameof(describe));
            if(grid.Width!=24 || grid.Height!=24)throw new NotSupportedException("Live local planning requires the24x24 water world.");
            if(cellX<0 || cellY<0 || originX<0 || originY<0 || goalX<0 || goalY<0 ||
               cellX>=24 || cellY>=24 || originX>=24 || originY>=24 || goalX>=24 || goalY>=24)
                throw new ArgumentOutOfRangeException(nameof(goalX));
            if(radius<0 || radius>32)throw new ArgumentOutOfRangeException(nameof(radius));
            if(simulationGroup< -1)throw new ArgumentOutOfRangeException(nameof(simulationGroup));
            if(!ReferenceEquals(grid.GetOccupant(cellX,cellY),owner))throw new ArgumentException("The current actor must retain its actual cell owner.");
            var cache=new List<int>();
            if(cachedObstacles!=null)foreach(int cell in cachedObstacles)
            {
                if(cell<0 || cell>=576 || cache.Contains(cell))throw new ArgumentException("Cached cells must be bounded and unique.");
                cache.Add(cell);
            }
            var field=new short[576];
            for(int y=0;y<24;y++)for(int x=0;x<24;x++)field[y*24+x]=grid.IsTerrainPassable(x,y,0)?(short)0:(short)-1;
            short destination=field[goalY*24+goalX];
            bool advanced=retryPriority>50,force=false;
            if(advanced)
            {
                randomState=unchecked(randomState*0x41c64e6du+0x3039u);
                force=(randomState>>16)%30u+50u<retryPriority;
            }
            for(int y=Math.Max(0,cellY-3);y<Math.Min(24,cellY+4);y++)
                for(int x=Math.Max(0,cellX-3);x<Math.Min(24,cellX+4);x++)
                {
                    object other=grid.GetOccupant(x,y);
                    if(other==null || ReferenceEquals(other,owner))continue;
                    ShipPlanningOccupant actor=describe(other);
                    if(actor.SimulationGroup< -1)throw new NotSupportedException("Wrapped source group words are outside this projection.");
                    if(actor.SimulationGroup!=-1 && actor.SimulationGroup==simulationGroup && !force)continue;
                    int cell=y*24+x;
                    if(!actor.IsShip) {field[cell]=-1;continue;}
                    bool block=force ? actor.MovementState!=4 && actor.MovementState!=5 : actor.MovementState==0 || actor.MovementState==6;
                    if(block){field[cell]=-1;if(!cache.Contains(cell))cache.Add(cell);}
                }
            //4a7290 revalidates cached positions after scanning,without another
            // group check. Empty/self and travelling4/5 entries are removed.
            for(int i=0;i<cache.Count;)
            {
                int cell=cache[i];object other=grid.GetOccupant(cell%24,cell/24);
                if(other==null || ReferenceEquals(other,owner)){cache.RemoveAt(i);continue;}
                ShipPlanningOccupant actor=describe(other);
                if(actor.IsShip && (actor.MovementState==4 || actor.MovementState==5)){cache.RemoveAt(i);continue;}
                field[cell]=-1;i++;
            }
            return Solve(field,24,24,originX,originY,goalX,goalY,radius,retryPriority,
                         preserveDestinationMask,destination,randomState,advanced,cache,true);
        }

        private static ShipPlanningResult Solve(short[] field,int width,int height,int originX,int originY,
            int goalX,int goalY,int radius,byte retryPriority,bool preserveDestinationMask,short destination,
            uint randomState,bool randomAdvanced,List<int> cache,bool randomAlreadyAdvanced=false)
        {
            bool nearest=radius!=0 || retryPriority!=0;
            if (!nearest || !preserveDestinationMask) field[goalY * width + goalX] = destination;
            if(randomAdvanced && !randomAlreadyAdvanced) randomState=unchecked(randomState*0x41c64e6du+0x3039u);
            // Plan's stationary state0 projection advances here. PlanLive has
            // already advanced once before its occupancy scan and RNG gate.
            if (nearest)
            {
                if (field[originY * width + originX] == -1)
                    return new ShipPlanningResult(new byte[0], field, field, goalX, goalY, true, false,
                                                  radius, randomState, randomAdvanced, cache.ToArray());
                SourceNearestPathfinder.Result result = SourceNearestPathfinder.Find(field, width, height,
                    originX, originY, goalX, goalY, radius, 0);
                return new ShipPlanningResult(result.CapturePoints(), field, result.CaptureWorkingField(),
                    goalX, goalY, true, result.ReachedWithinRange, radius, randomState, randomAdvanced, cache.ToArray());
            }
            // GetWayNew itself falls back to the range1 nearest routine when
            // both the base and working destination cells are blocked. This
            // does not change ProcPostMove's separate mode0 result radius.
            if (field[goalY * width + goalX] == -1 && destination == -1)
            {
                SourceNearestPathfinder.Result nearby = SourceNearestPathfinder.Find(field, width, height,
                    originX, originY, goalX, goalY, 1, 0);
                return new ShipPlanningResult(nearby.CapturePoints(), field, nearby.CaptureWorkingField(),
                    goalX, goalY, false, nearby.ReachedWithinRange, 0, randomState, randomAdvanced, cache.ToArray());
            }
            SourcePathfinder.Result direct = SourcePathfinder.Find(field, width, height,
                                                                  originX, originY, goalX, goalY, 0);
            return new ShipPlanningResult(direct.CapturePoints(), field, direct.CaptureWorkingField(),
                goalX, goalY, false, direct.Succeeded, 0, randomState, randomAdvanced, cache.ToArray());
        }

        private static void Validate(MissionOccupancyGrid grid, object owner, int cellX, int cellY,
                                     int originX, int originY, int goalX, int goalY, int radius)
        {
            if (grid == null) throw new ArgumentNullException(nameof(grid));
            if (owner == null) throw new ArgumentNullException(nameof(owner));
            if (grid.Width != 24 || grid.Height != 24)
                throw new NotSupportedException("Normal source0b planning requires the24x24 reference world.");
            if (cellX < 0 || cellX >= 24 || cellY < 0 || cellY >= 24 ||
                originX < 0 || originX >= 24 || originY < 0 || originY >= 24 ||
                goalX < 0 || goalX >= 24 || goalY < 0 || goalY >= 24)
                throw new ArgumentOutOfRangeException(nameof(goalX));
            if (radius < 0 || radius > 32) throw new ArgumentOutOfRangeException(nameof(radius));
            if (!ReferenceEquals(grid.GetOccupant(cellX, cellY), owner))
                throw new ArgumentException("The current source0b cell must retain its owner reference.", nameof(owner));
            var known = new object[7];
            for (int i = 0; i < 7; i++)
            {
                known[i] = grid.GetOccupant(StaticCells[i, 0], StaticCells[i, 1]);
                if (known[i] == null || ReferenceEquals(known[i], owner))
                    throw new NotSupportedException("The seven stationary source occupants are required.");
                for (int j = 0; j < i; j++)
                    if (ReferenceEquals(known[i], known[j]))
                        throw new NotSupportedException("The stationary source identities must be distinct.");
            }
            int ownClaims = 0;
            for (int y = 0; y < 24; y++)
                for (int x = 0; x < 24; x++)
                {
                    object occupant = grid.GetOccupant(x, y);
                    if (occupant == null) continue;
                    if (ReferenceEquals(occupant, owner)) { ownClaims++; continue; }
                    bool found = false;
                    for (int i = 0; i < known.Length; i++)
                        if (ReferenceEquals(occupant, known[i]) && x == StaticCells[i, 0] && y == StaticCells[i, 1])
                        { found = true; break; }
                    if (!found) throw new NotSupportedException("Dynamic foreign occupants are outside this source projection.");
                }
            if (ownClaims < 1 || ownClaims > 2)
                throw new NotSupportedException("The source ship may own its cell and at most one reservation.");
        }

        internal static sbyte Direction(int x, int y)
        {
            if (x < -1 || x > 1 || y < -1 || y > 1 || x == 0 && y == 0)
                throw new NotSupportedException("The source route must begin with one adjacent segment.");
            if (x > 0) return y < 0 ? (sbyte)1 : y > 0 ? (sbyte)7 : (sbyte)0;
            if (x < 0) return y < 0 ? (sbyte)3 : y > 0 ? (sbyte)5 : (sbyte)4;
            return y < 0 ? (sbyte)2 : (sbyte)6;
        }
    }
}
