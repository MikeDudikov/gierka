using System;
using AncientConquest.World;

namespace AncientConquest.Simulation
{
    /// <summary>
    /// Source0b's one adjacent route, native turning and MoveShip arithmetic.
    /// Conditions: source fleet8 stationary owners, full health, upgrade0,
    /// wind force0/heading5,56x56 logical sprite and planner counter1.
    /// The plan adapter projects verified two-point native routes; this is
    /// not a general pathfinder, full Life, combat or weather simulation.
    /// </summary>
    public sealed class ShipAdjacentMovement
    {
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

            internal Snapshot(ShipAdjacentMovement source)
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
                IsComplete = source.hasRoute && source.state == 0 &&
                    source.cellX == source.goalX && source.cellY == source.goalY &&
                    source.worldX == source.goalX * 64 + 4 && source.worldY == source.goalY * 64 + 4;
            }
        }

        private static readonly int[] DirectionX = { 1, 1, 0, -1, -1, -1, 0, 1 };
        private static readonly int[] DirectionY = { 0, -1, -1, -1, 0, 1, 1, 1 };
        private readonly MissionOccupancyGrid grid;
        private readonly object owner;
        private int cellX = 16, cellY = 2, worldX = 1028, worldY = 132;
        private sbyte heading = 5, targetHeading, turnStep;
        private byte state;
        private bool center, hasRoute, stopped;
        private int goalX, goalY, pathIndex, pathCount;
        private int speed, remainder, deceleration, reserved = -1, next;
        private int frame = 20, drawnFrame = 20, publishedX = 1028, publishedY = 132;
        private uint counter, lastFrameTick, lastStateCounter;
        private byte[] routePoints;

        public Snapshot Current => new Snapshot(this);
        public bool HasRoute => hasRoute;
        public bool IsStopped => stopped;
        public bool LastStepPublishesPose { get; private set; }
        public bool LastStepReachedForwardTail { get; private set; }

        public ShipAdjacentMovement(MissionOccupancyGrid grid, object ownerIdentity, MissionShipSeed source0b)
        {
            if (grid == null) throw new ArgumentNullException(nameof(grid));
            if (ownerIdentity == null) throw new ArgumentNullException(nameof(ownerIdentity));
            if (source0b.InstanceId != 0xbu || source0b.CellX != 16 || source0b.CellY != 2 ||
                source0b.Heading != 5 || source0b.ModelValue != 0 ||
                source0b.OwnerSide != 1 || source0b.OwnerPlayer != 1 ||
                source0b.RequestedHealthPercent != 100 || source0b.SourceEquipmentA != 0 ||
                source0b.SourceEquipmentB != 0 || source0b.SourceOrderCount != 0)
                throw new NotSupportedException("Only the full-health source0b reference recipe is supported.");
            if (grid.Width != 24 || grid.Height != 24)
                throw new NotSupportedException("The source adjacent reference requires its24x24 grid.");
            if (!ReferenceEquals(grid.GetOccupant(16, 2), ownerIdentity))
                throw new ArgumentException("Retain the original source0b owner reference.", nameof(ownerIdentity));
            this.grid = grid; owner = ownerIdentity;
        }

        public byte[] CaptureRoutePoints() => routePoints == null ? new byte[0] : (byte[])routePoints.Clone();

        public bool TryBeginAdjacentReferenceMove(int targetX, int targetY, uint plannerCounter = 1)
        {
            if (hasRoute) throw new InvalidOperationException("The adjacent reference may begin one route.");
            if (plannerCounter != 1u)
                throw new NotSupportedException("The verified native planner starts at source counter1.");
            counter = plannerCounter;
            if (!ShipAdjacentPlanner.TryPlan(grid, owner, cellX, cellY, heading,
                                             targetX, targetY, 0, out ShipAdjacentPlan plan))
                return false;
            goalX = targetX; goalY = targetY; targetHeading = plan.TargetHeading;
            state = plan.InitialState; center = plan.CenterGate;
            pathIndex = plan.PathIndex; pathCount = plan.PathCount;
            routePoints = plan.CapturePoints(); hasRoute = true;
            return true;
        }

        private static ShipNavigationOccupant UnknownCorner(object occupied)
        {
            throw new NotSupportedException("The bounded stationary fleet has no occupied adjacent corner; linked movement is not projected.");
        }

        private bool TargetAvailable() => ShipAdjacentQuery.CanEnter(grid, owner, goalX, goalY,
                                        (byte)targetHeading, 0, UnknownCorner);

        private void PublishPose()
        {
            drawnFrame = frame; publishedX = worldX; publishedY = worldY;
            LastStepPublishesPose = true;
        }

        /// <summary>
        /// One source MoveShip call. This class owns turn and forward phases.
        /// Apply only Current.DrawnFrame/PublishedWorldX/Y when publication is
        /// reported; a stored turn/forward frame can change without drawing.
        /// The stopped diagnostic freezes and does not run native idle RNG.
        /// </summary>
        public void Step(int pendingSteps, uint sourceCounter)
        {
            if (pendingSteps != 1 && pendingSteps != 2 && pendingSteps != 3 && pendingSteps != 7)
                throw new ArgumentOutOfRangeException(nameof(pendingSteps));
            if (!hasRoute) throw new InvalidOperationException("Begin a verified adjacent route before stepping.");
            LastStepPublishesPose = false; LastStepReachedForwardTail = false;
            if (stopped) return;
            if (sourceCounter != unchecked(counter + 1u))
                throw new ArgumentException("Advance the reference source counter once per MoveShip call.", nameof(sourceCounter));
            counter = sourceCounter;
            unchecked
            {
                if (state == 2)
                {
                    lastStateCounter = counter;
                    ShipTurnProgression.Result turn = ShipTurnProgression.Advance(frame, heading, targetHeading,
                        turnStep, counter, lastFrameTick, 2u, true, state, center ? (byte)1 : (byte)0);
                    frame = turn.Frame; heading = turn.Heading; turnStep = turn.TurnStep;
                    lastFrameTick = turn.LastTick; state = turn.State; center = turn.ChangedMarker != 0;
                    if (turn.PublishesPose) PublishPose();
                    // Original3320 returns0 even when it finishes the turn.
                    // This complete call returns before reservation/forward.
                    return;
                }

                if (state == 3)
                {
                    if (!TargetAvailable())
                    {
                        if (counter - lastStateCounter > 49u)
                        {
                            state = 0; turnStep = 1; reserved = -1; stopped = true;
                        }
                        return;
                    }
                    object existing = grid.GetOccupant(goalX, goalY);
                    if (existing == null && !grid.TryClaim(goalX, goalY, owner))
                        throw new InvalidOperationException("The adjacent target changed during reservation.");
                    next = goalY * grid.Width + goalX; reserved = next;
                    state = 5; center = true;
                }
                if (!ReferenceEquals(grid.GetOccupant(goalX, goalY), owner))
                    throw new InvalidOperationException("The reserved adjacent target owner changed.");

                lastStateCounter = counter;
                int oldWorldX = worldX, oldWorldY = worldY;
                int acceleration = state == 4 ? deceleration * 60 / 100 : 720;
                int newSpeed = speed + pendingSteps * acceleration;
                if (newSpeed <= 0 && state == 4) { newSpeed = 0; deceleration = 0; }
                if (newSpeed > 36000) newSpeed = 36000;
                if (newSpeed <= 6000 && acceleration < 0) newSpeed = speed;
                speed = newSpeed;
                int total = pendingSteps * speed + remainder;
                int quotient = total / 3000; remainder = total % 3000;
                int dx = DirectionX[heading], dy = DirectionY[heading];
                int divisor = Math.Abs(dx) + Math.Abs(dy) == 1 ? 2 : 3;
                int candidateX = oldWorldX + quotient * dx / divisor;
                int candidateY = oldWorldY + quotient * dy / divisor;
                remainder += quotient % divisor * 3000;
                int targetWorldX = goalX * 64 + 4, targetWorldY = goalY * 64 + 4;
                if (dx > 0 && candidateX > targetWorldX || dx < 0 && candidateX < targetWorldX)
                    candidateX = targetWorldX;
                if (dy > 0 && candidateY > targetWorldY || dy < 0 && candidateY < targetWorldY)
                    candidateY = targetWorldY;
                bool moved = candidateX != oldWorldX || candidateY != oldWorldY;
                worldX = candidateX; worldY = candidateY;
                if (moved)
                {
                    int previousCellX = (oldWorldX + 28) / 64;
                    int previousCellY = (oldWorldY + 28) / 64;
                    bool transferred = center && previousCellY * grid.Width + previousCellX == next;
                    if (transferred)
                    {
                        if (!grid.Release(cellX, cellY, owner))
                            throw new InvalidOperationException("The source owner changed before adjacent transfer.");
                        cellX = previousCellX; cellY = previousCellY; reserved = -1; center = false;
                        state = 4;
                        int distance = Math.Max(Math.Abs(worldX + 28 - cellX * 64 - 32) + 64,
                                                Math.Abs(worldY + 28 - cellY * 64 - 32) + 64);
                        deceleration = speed * speed / (distance * -6000);
                    }
                    else if (worldX == targetWorldX && worldY == targetWorldY)
                    {
                        state = 0; center = true; turnStep = 1;
                        speed = 0; reserved = -1; stopped = true;
                    }
                }
                LastStepReachedForwardTail = true;
                ShipFrameProgression.Result forward = ShipFrameProgression.AdvanceForward(frame, heading,
                                                counter, lastFrameTick, 2u);
                frame = forward.Frame; lastFrameTick = forward.LastTick;
                if (moved) PublishPose();
            }
        }
    }
}
