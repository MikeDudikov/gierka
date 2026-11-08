using System;
using System.Collections;
using System.Collections.Generic;
using AncientConquest.World;
using UnityEngine;

namespace AncientConquest.Presentation
{
    /// <summary>Frozen source ship parts and a partial occupancy grid; no simulation or source constructors.</summary>
    internal sealed class MissionShipReference : IDisposable
    {
        private const string ResourceRoot = "MissionUnitsGenerated/";
        [Serializable]
        private sealed class Frame
        {
            public string name = null;
            public int atlas_x = 0;
            public int atlas_y = 0;
            public int width = 0;
            public int height = 0;
        }
        [Serializable]
        private sealed class Part
        {
            public string name = null;
            public int source_index = 0;
            public int offset_x = 0;
            public int offset_y = 0;
            public int depth = 0;
        }
        [Serializable]
        private sealed class Ship
        {
            public uint instance_id = 0;
            public string descriptor_resource = null;
            public int owner_side = 0;
            public int owner_player = 0;
            public uint model_value = 0;
            public int cell_x = 0;
            public int cell_y = 0;
            public int heading = 0;
            public int reference_state = 0;
            public int reference_frame_index = 0;
            public int component_mask = 0;
            public int logical_width = 0;
            public int logical_height = 0;
            public int world_pixel_x = 0;
            public int world_pixel_y = 0;
            public int reference_depth = 0;
            public Part[] components = null;
        }
        [Serializable]
        private sealed class DrawPart
        {
            public uint instance_id = 0;
            public int source_index = 0;
            public int depth = 0;
        }
        [Serializable]
        private sealed class Manifest
        {
            public int schema_version = 0;
            public string mission = null;
            public int native_canvas_width = 0;
            public int native_canvas_height = 0;
            public int map_width_cells = 0;
            public int map_height_cells = 0;
            public int ship_count = 0;
            public int component_instance_count = 0;
            public int atlas_width = 0;
            public int atlas_height = 0;
            public Ship[] ships = null;
            public Frame[] frames = null;
            public DrawPart[] draw_order = null;
        }
        private sealed class BoundShip
        {
            internal readonly MissionShipSeed seed;
            internal readonly Ship info;
            internal readonly object owner = new object();
            internal bool claimed;
            internal readonly Dictionary<int, SpriteRenderer> renderers = new Dictionary<int, SpriteRenderer>();
            internal readonly List<int> inlineOrder = new List<int>();
            internal BoundShip(MissionShipSeed seed, Ship info) { this.seed = seed; this.info = info; }
        }

        private readonly List<GameObject> visuals = new List<GameObject>();
        private readonly Dictionary<string, Sprite> sprites = new Dictionary<string, Sprite>(StringComparer.Ordinal);
        private readonly Dictionary<uint, BoundShip> ships = new Dictionary<uint, BoundShip>();
        private readonly List<string> drawEvidence = new List<string>();
        private Texture2D atlas;
        private MissionOccupancyGrid grid;
        private bool disposed;
        private ShipMovementReference movementReference;
        private ShipAdjacentReference adjacentReference;
        private ShipRouteReference routeReference;
        private ShipOrderReference commandReference;
        private ShipPickingReference pickingReference;
        private ShipPointerReference pointerReference;
        private ShipFleetMotionReference fleetMotionReference;
        private readonly Transform parent;
        private readonly Material material;
        private SourceCohortOrderReference routeOrder;
        private readonly Dictionary<uint, SpriteRenderer> reefRenderers;

        internal MissionShipReference(Transform parent, Material material, IEnumerable<MissionObjectSeed> selectedSeeds,
                                      int reefCount, IDictionary<uint, SpriteRenderer> reefBindings)
        {
            if (reefBindings == null) throw new ArgumentNullException(nameof(reefBindings));
            this.parent = parent; this.material = material;
            reefRenderers = new Dictionary<uint, SpriteRenderer>(reefBindings);
            try
            {
                Manifest info = LoadManifest();
                if (reefCount != 5) throw new InvalidOperationException("Source reference ordering requires the five verified reefs.");
                if (reefRenderers.Count != reefCount)
                    throw new InvalidOperationException("The source cohort needs five actual reef renderer bindings.");
                byte[] flags = LoadBytes("CellFlags");
                if (flags.Length != (long)info.map_width_cells * info.map_height_cells * 4)
                    throw new InvalidOperationException("Source cell flags do not match the diagnostic grid.");
                uint[] values = new uint[flags.Length / 4];
                for (int index = 0; index < values.Length; index++)
                {
                    int offset = index * 4;
                    values[index] = (uint)flags[offset] | (uint)flags[offset + 1] << 8 |
                                    (uint)flags[offset + 2] << 16 | (uint)flags[offset + 3] << 24;
                }
                grid = new MissionOccupancyGrid(info.map_width_cells, info.map_height_cells, values);
                var source = new Dictionary<uint, Ship>();
                foreach (Ship ship in info.ships)
                {
                    if (ship == null || source.ContainsKey(ship.instance_id))
                        throw new InvalidOperationException("Duplicate or missing staged ship recipe.");
                    source.Add(ship.instance_id, ship);
                }
                int componentCount = 0;
                foreach (MissionObjectSeed seed in selectedSeeds)
                {
                    if (!MissionShipSeed.TryRead(seed, out MissionShipSeed ship)) continue;
                    if (!source.TryGetValue(ship.InstanceId, out Ship staged))
                        throw new InvalidOperationException("A selected source ship has no verified visual recipe.");
                    ValidateRecipe(ship, staged);
                    var bound = new BoundShip(ship, staged);
                    ships.Add(ship.InstanceId, bound);
                    bound.claimed = grid.TryClaim(ship.CellX, ship.CellY, bound.owner);
                    if (!bound.claimed) throw new InvalidOperationException("Source reference ship cells overlap.");
                    componentCount += staged.components.Length;
                }
                if (ships.Count != info.ship_count || componentCount != info.component_instance_count)
                    throw new InvalidOperationException("Selected ship cohort differs from the verified reference.");
                atlas = RgbaResourceTexture.Load(ResourceRoot + "ShipComponentsRgba", info.atlas_width,
                                                 info.atlas_height, FilterMode.Point);
                foreach (Frame frame in info.frames)
                {
                    if (frame == null || string.IsNullOrEmpty(frame.name) || sprites.ContainsKey(frame.name) ||
                        frame.width <= 0 || frame.height <= 0 || frame.atlas_x < 0 || frame.atlas_y < 0 ||
                        (long)frame.atlas_x + frame.width > atlas.width || (long)frame.atlas_y + frame.height > atlas.height)
                        throw new InvalidOperationException("A staged component extends outside the source atlas.");
                    sprites.Add(frame.name, Sprite.Create(atlas,
                        new Rect(frame.atlas_x, atlas.height - frame.atlas_y - frame.height, frame.width, frame.height),
                        new Vector2(0, 1), 1, 0, SpriteMeshType.FullRect));
                }
                var drawn = new HashSet<string>(StringComparer.Ordinal);
                for (int order = 0; order < info.draw_order.Length; order++)
                {
                    DrawPart draw = info.draw_order[order];
                    if (draw == null || !ships.TryGetValue(draw.instance_id, out BoundShip bound))
                        throw new InvalidOperationException("Draw order references an unknown source ship.");
                    Part part = null;
                    foreach (Part candidate in bound.info.components)
                        if (candidate.source_index == draw.source_index) { part = candidate; break; }
                    if (part == null || !sprites.TryGetValue(part.name, out Sprite sprite) ||
                        !drawn.Add(draw.instance_id + ":" + draw.source_index) ||
                        draw.depth != (part.depth < 0 ? -part.depth : bound.info.reference_depth))
                        throw new InvalidOperationException("Draw order does not match selected source components.");
                    if (sprite.rect.width != bound.info.logical_width || sprite.rect.height != bound.info.logical_height)
                        throw new InvalidOperationException("Component dimensions are outside this verified full-plane recipe.");
                    var visual = new GameObject("Frozen ship " + bound.seed.InstanceId.ToString("x8") + " / " + part.name);
                    visuals.Add(visual);
                    visual.transform.SetParent(parent, false);
                    visual.transform.localPosition = new Vector3(bound.info.world_pixel_x + part.offset_x,
                                                               -bound.info.world_pixel_y - part.offset_y, 0);
                    SpriteRenderer renderer = visual.AddComponent<SpriteRenderer>();
                    renderer.sharedMaterial = material;
                    renderer.sprite = sprite;
                    renderer.color = Color.white;
                    bound.renderers.Add(part.source_index, renderer);
                    if (part.depth >= 0) bound.inlineOrder.Add(part.source_index);
                    // Flatten the proven ship-sprite/group traversal. Other source
                    // classes, fog and the complete world lifecycle remain excluded.
                    renderer.sortingOrder = 10 + order + (part.depth >= 0 ? reefCount : 0);
                    drawEvidence.Add("Mission unit reference draw: order=" + renderer.sortingOrder +
                                     "; id=" + bound.seed.InstanceId.ToString("x8") + "; part=" + part.source_index + "; depth=" + draw.depth);
                }
            }
            catch { Dispose(); throw; }
        }

        private static void ValidateRecipe(MissionShipSeed ship, Ship info)
        {
            int equipmentB = unchecked((byte)ship.SourceEquipmentB);
            int mask = 0x83 | (ship.SourceEquipmentA == 1 ? 0x20 : ship.SourceEquipmentA == 2 ? 0x40 : 0) |
                       (equipmentB == 1 ? 8 : equipmentB == 2 ? 0x10 : 0);
            if (ship.RequestedHealthPercent != 100 || ship.SourceOrderCount != 0 || info.reference_state != 1 ||
                info.logical_width <= 0 || info.logical_width > 8192 || info.logical_height <= 0 || info.logical_height > 8192 ||
                info.owner_side != ship.OwnerSide || info.owner_player != ship.OwnerPlayer || info.model_value != ship.ModelValue ||
                info.cell_x != ship.CellX || info.cell_y != ship.CellY || info.heading != ship.Heading ||
                info.reference_frame_index != ship.ReferenceFrameIndex || info.component_mask != mask ||
                info.world_pixel_x != ship.GetWorldPixelX(info.logical_width) ||
                info.world_pixel_y != ship.GetWorldPixelY(info.logical_height) ||
                info.reference_depth != Math.Max(10000, unchecked(20000 - info.logical_height - info.world_pixel_y)) ||
                info.components == null || info.components.Length < 1 || info.components.Length > 32)
                throw new InvalidOperationException("Frozen ship recipe does not match source seed fields.");
            uint selectedMask = 0;
            foreach (Part part in info.components)
            {
                if (part == null || part.source_index < 0 || part.source_index >= 32 ||
                    (selectedMask & 1u << part.source_index) != 0)
                    throw new InvalidOperationException("Invalid or repeated source component index.");
                selectedMask |= 1u << part.source_index;
            }
            if (selectedMask != (uint)mask)
                throw new InvalidOperationException("Selected source component mask differs from the seed recipe.");
        }

        private static byte[] LoadBytes(string name)
        {
            TextAsset asset = Resources.Load<TextAsset>(ResourceRoot + name);
            if (asset == null) throw new InvalidOperationException("Missing staged unit resource: " + name);
            try { return asset.bytes; }
            finally { Resources.UnloadAsset(asset); }
        }

        private static Manifest LoadManifest()
        {
            TextAsset asset = Resources.Load<TextAsset>(ResourceRoot + "MissionUnitsManifest");
            if (asset == null) throw new InvalidOperationException("Stage source ship references first.");
            Manifest info;
            try { info = JsonUtility.FromJson<Manifest>(asset.text); }
            finally { Resources.UnloadAsset(asset); }
            if (info == null || info.schema_version != 1 || info.mission != "miss000" ||
                info.native_canvas_width != NativeMenuCanvas.Width || info.native_canvas_height != NativeMenuCanvas.Height ||
                info.map_width_cells != 24 || info.map_height_cells != 24 || info.ship_count != 8 ||
                info.component_instance_count != 29 || info.ships == null || info.ships.Length != 8 ||
                info.frames == null || info.frames.Length != 17 || info.draw_order == null || info.draw_order.Length != 29)
                throw new InvalidOperationException("Unit manifest does not match the bounded miss000 recipe.");
            return info;
        }

        internal void LogReadiness()
        {
            Debug.Log("Mission unit reference seeds: ships=" + ships.Count + "; components=" + visuals.Count +
                      "; source_constructors_executed=0");
            Debug.Log("Mission unit reference grid: cells=" + grid.Width * grid.Height +
                      "; claimed=" + ships.Count + "; pending_orders=0; simulation=False");
            foreach (BoundShip ship in ships.Values)
                Debug.Log("Mission unit reference ship: id=" + ship.seed.InstanceId.ToString("x8") +
                          "; cell=" + ship.seed.CellX + "," + ship.seed.CellY + "; model=" + ship.seed.ModelVariant +
                          "; heading=" + ship.seed.Heading + "; frame=" + ship.seed.ReferenceFrameIndex +
                          "; mask=" + ship.info.component_mask + "; anchor=" + ship.info.world_pixel_x + "," + ship.info.world_pixel_y +
                          "; depth=" + ship.info.reference_depth);
            foreach (string draw in drawEvidence) Debug.Log(draw);
            Debug.Log("Mission unit reference ready: state=1; frozen=True; renderers=29; full_world_order=False");
        }

        internal IEnumerator CreateMovementReference()
        {
            if (movementReference != null || adjacentReference != null || routeReference != null || commandReference != null || !ships.TryGetValue(0xbu, out BoundShip ship) ||
                ship.info.reference_depth != 19812)
                throw new InvalidOperationException("The source0b movement reference cannot be created.");
            // This bounded route's body depth19812..19748 never crosses the
            // next body19676. Its three existing queue slots therefore remain
            // valid; this does not implement dynamic full-world sorting.
            foreach (BoundShip other in ships.Values)
                if (other != ship && other.info.reference_depth >= 19748)
                    throw new InvalidOperationException("The reference move would cross a static body rank.");
            movementReference = new ShipMovementReference(grid, ship.owner, ship.seed, ship.renderers);
            return movementReference.Run();
        }

        internal IEnumerator CreateAdjacentReference()
        {
            if (movementReference != null || adjacentReference != null || routeReference != null || commandReference != null || !ships.TryGetValue(0xbu, out BoundShip ship) ||
                ship.info.reference_depth != 19812)
                throw new InvalidOperationException("The source0b adjacent reference cannot be created.");
            foreach (BoundShip other in ships.Values)
                if (other != ship && other.info.reference_depth >= 19748)
                    throw new InvalidOperationException("The adjacent source routes would cross a static body rank.");
            adjacentReference = new ShipAdjacentReference(grid, ship.owner, ship.seed, ship.renderers);
            return adjacentReference.Run();
        }

        internal IEnumerator CreateRouteReference()
        {
            if (movementReference != null || adjacentReference != null || routeReference != null || commandReference != null ||
                !ships.TryGetValue(0xbu, out BoundShip moving))
                throw new InvalidOperationException("The source0b route reference cannot be created.");
            routeOrder = CreateCohortOrder();
            routeReference = new ShipRouteReference(grid, moving.owner, moving.seed, moving.renderers, routeOrder);
            return routeReference.Run();
        }

        internal IEnumerator CreateOrderReference()
        {
            if (movementReference != null || adjacentReference != null || routeReference != null || commandReference != null ||
                !ships.TryGetValue(0xbu, out BoundShip moving))
                throw new InvalidOperationException("The source0b order reference cannot be created.");
            routeOrder = CreateCohortOrder();
            commandReference = new ShipOrderReference(grid, moving.owner, moving.seed, moving.renderers, routeOrder);
            return commandReference.Run();
        }

        internal IEnumerator CreatePickingReference()
        {
            if (movementReference != null || adjacentReference != null || routeReference != null || commandReference != null ||
                !ships.TryGetValue(0xbu, out BoundShip moving))
                throw new InvalidOperationException("The source ship-picking reference cannot be created.");
            var actors = new ShipPickingReference.Actor[ships.Count];
            int index = 0;
            foreach (BoundShip ship in ships.Values)
                actors[index++] = new ShipPickingReference.Actor(ship.seed.InstanceId, ship.owner,
                    ship.info.descriptor_resource, ship.seed.RuntimeClassTag, ship.info.logical_width,
                    ship.info.logical_height, ship.info.world_pixel_x, ship.info.world_pixel_y,
                    ship.info.reference_frame_index, ship.seed.Heading);
            pickingReference = new ShipPickingReference(grid, actors);
            routeOrder = CreateCohortOrder();
            commandReference = new ShipOrderReference(grid, moving.owner, moving.seed, moving.renderers,
                                                     routeOrder, pickingReference.LogCheckpoint);
            return commandReference.Run();
        }

        internal IEnumerator CreateFleetMotionReference()
        {
            if(movementReference!=null||adjacentReference!=null||routeReference!=null||commandReference!=null||pointerReference!=null||fleetMotionReference!=null)
                throw new InvalidOperationException("Select one source motion diagnostic.");
            var actors=new List<ShipFleetMotionReference.Binding>();
            foreach(BoundShip ship in ships.Values)actors.Add(new ShipFleetMotionReference.Binding(ship.seed,ship.owner,ship.renderers));
            routeOrder=CreateCohortOrder();
            fleetMotionReference=new ShipFleetMotionReference(grid,actors.ToArray(),routeOrder);
            return fleetMotionReference.Run();
        }

        private SourceCohortOrderReference CreateCohortOrder()
        {
            var groups = new List<SourceCohortOrderReference.Group>();
            foreach (BoundShip ship in ships.Values)
            {
                var parts = new SpriteRenderer[ship.inlineOrder.Count];
                for (int index = 0; index < parts.Length; index++) parts[index] = ship.renderers[ship.inlineOrder[index]];
                groups.Add(new SourceCohortOrderReference.Group(ship.seed.InstanceId,
                    SourceCohortOrderReference.GroupKind.InlineParent, ship.info.reference_depth,
                    parts, ship.inlineOrder.ToArray()));
                groups.Add(new SourceCohortOrderReference.Group(ship.seed.InstanceId,
                    SourceCohortOrderReference.GroupKind.SeparateShadow, 21000,
                    new[] { ship.renderers[0] }, new[] { 0 }));
            }
            foreach (KeyValuePair<uint, SpriteRenderer> reef in reefRenderers)
                groups.Add(new SourceCohortOrderReference.Group(reef.Key,
                    SourceCohortOrderReference.GroupKind.Reef, 20200, new[] { reef.Value }, new[] { -1 }));
            return new SourceCohortOrderReference(groups);
        }

        internal IEnumerator CreatePointerReference(int originWorldX, int originWorldY)
        {
            if (movementReference != null || adjacentReference != null || routeReference != null || commandReference != null ||
                pointerReference != null || !ships.TryGetValue(0xbu, out BoundShip moving))
                throw new InvalidOperationException("The source mouse diagnostic cannot be created.");
            var actors = new ShipPickingReference.Actor[ships.Count];
            var metadata = new Dictionary<object, AncientConquest.Simulation.ShipHoverActor>();
            int index = 0;
            foreach (BoundShip ship in ships.Values)
            {
                actors[index++] = new ShipPickingReference.Actor(ship.seed.InstanceId, ship.owner,
                    ship.info.descriptor_resource, ship.seed.RuntimeClassTag, ship.info.logical_width,
                    ship.info.logical_height, ship.info.world_pixel_x, ship.info.world_pixel_y,
                    ship.info.reference_frame_index, ship.seed.Heading);
                uint capabilities = ship.seed.InstanceId == 0xbu || ship.seed.InstanceId == 0xcu || ship.seed.InstanceId == 0x10u
                    ? 0xfffff7ffu : 0xfffffeffu;
                metadata.Add(ship.owner, new AncientConquest.Simulation.ShipHoverActor(
                    checked((byte)ship.info.owner_side), checked((byte)ship.info.owner_player), capabilities, ship.seed.RuntimeClassTag));
            }
            routeOrder = CreateCohortOrder();
            var host = new GameObject("Source mouse reference (explicit diagnostic)");
            host.SetActive(false); host.transform.SetParent(parent, false);
            try
            {
                pointerReference = host.AddComponent<ShipPointerReference>();
                if(Array.IndexOf(Environment.GetCommandLineArgs(),"--ship-pointer-fleet-movement")>=0)
                {
                    var bindings=new List<ShipFleetMotionReference.Binding>();
                    foreach(BoundShip ship in ships.Values)bindings.Add(new ShipFleetMotionReference.Binding(ship.seed,ship.owner,ship.renderers));
                    fleetMotionReference=new ShipFleetMotionReference(grid,bindings.ToArray(),routeOrder);
                }
                pointerReference.Initialize(grid, moving.owner, moving.seed, moving.renderers, routeOrder,
                    actors, metadata, parent, material, originWorldX, originWorldY,fleetMotionReference);
                if (Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-pointer-input-replay") >= 0)
                    host.AddComponent<ShipPointerInputReplay>().Configure(pointerReference);
                if (Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-pointer-box-replay") >= 0)
                    host.AddComponent<ShipBoxInputReplay>().Configure(pointerReference);
                if (Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-pointer-fleet-replay") >= 0)
                    host.AddComponent<ShipFleetInputReplay>().Configure(pointerReference);
                if(Array.IndexOf(Environment.GetCommandLineArgs(),"--ship-pointer-fleet-movement-replay")>=0)
                    host.AddComponent<ShipFleetMoveInputReplay>().Configure(pointerReference);
                host.SetActive(true);
            }
            catch
            {
                //Unity need not send OnDestroy to a GameObject that never became
                //active. Release partially initialized owned resources explicitly.
                pointerReference?.Dispose();
                UnityEngine.Object.Destroy(host);
                throw;
            }
            yield break;
        }

        public void Dispose()
        {
            if (disposed) return;
            disposed = true;
            fleetMotionReference?.Dispose();
            if (pointerReference != null)
            {
                pointerReference.Dispose();
                UnityEngine.Object.Destroy(pointerReference.gameObject);
                pointerReference = null;
            }
            foreach (GameObject visual in visuals)
            {
                if (visual == null) continue;
                SpriteRenderer renderer = visual.GetComponent<SpriteRenderer>();
                if (renderer != null) { renderer.sprite = null; renderer.sharedMaterial = null; }
                UnityEngine.Object.Destroy(visual);
            }
            visuals.Clear();
            movementReference?.Dispose();
            adjacentReference?.Dispose();
            routeReference?.Dispose();
            commandReference?.Dispose();
            pickingReference?.Dispose();
            routeOrder?.Dispose();
            reefRenderers.Clear();
            foreach (Sprite sprite in sprites.Values)
                if (sprite != null) UnityEngine.Object.Destroy(sprite);
            sprites.Clear();
            if (atlas != null) UnityEngine.Object.Destroy(atlas);
            atlas = null;
            int released = 0;
            foreach (BoundShip ship in ships.Values)
                if (ship.claimed)
                    for (int y = 0; y < grid.Height; y++)
                        for (int x = 0; x < grid.Width; x++)
                            if (ReferenceEquals(grid.GetOccupant(x, y), ship.owner) && grid.Release(x, y, ship.owner))
                                released++;
            ships.Clear();
            if (released > 0)
                Debug.Log("Mission unit reference cleanup: claimed_released=" + released + "; visual_refs_cleared=True");
        }
    }
}
