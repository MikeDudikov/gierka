using System;
using System.Collections.Generic;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using AncientConquest.Simulation;
using AncientConquest.World;
using UnityEngine;

namespace AncientConquest.Presentation
{
    /// <summary>Actual ship-grid queries at held order checkpoints; no mouse or selection.</summary>
    internal sealed class ShipPickingReference : IDisposable
    {
        private const string Prefix = "[ShipPickingReference]";
        private const string PayloadHash = "60f3696904880fa4c4a51da2094f96145b30859013463369d1b953aebf3ba240";
        internal readonly struct Actor
        {
            internal readonly uint Id, ClassTag;
            internal readonly object Owner;
            internal readonly string Descriptor;
            internal readonly int Width, Height, X, Y, Frame;
            internal readonly sbyte Heading;
            internal Actor(uint id, object owner, string descriptor, uint classTag, int width, int height,
                           int x, int y, int frame, sbyte heading)
            {
                Id = id; Owner = owner; Descriptor = descriptor; ClassTag = classTag;
                Width = width; Height = height; X = x; Y = y; Frame = frame; Heading = heading;
            }
        }
        [Serializable] private sealed class MaskRecord
        {
            public int index = 0, offset = 0, length = 0;
            public string sha256 = null;
        }
        [Serializable] private sealed class Family
        {
            public string geometry_resource = null;
            public int width = 0, height = 0, row_bytes = 0;
            public MaskRecord[] masks = null;
        }
        [Serializable] private sealed class Manifest
        {
            public int schema_version = 0, native_canvas_width = 0, native_canvas_height = 0;
            public int family_count = 0, mask_count = 0;
            public Family[] families = null;
        }

        private readonly MissionOccupancyGrid grid;
        private readonly Actor[] actors;
        private readonly Dictionary<string, ShipPointerMask> masks = new Dictionary<string, ShipPointerMask>(StringComparer.Ordinal);
        private readonly List<uint> visited = new List<uint>(9);
        private readonly object[] beforeOwners = new object[576];
        private readonly Func<object, ShipPointerPose> describe;
        private ShipMoveOrder.Snapshot snapshot;
        private string stage;
        private int sample, queryIndex;
        private bool disposed;

        internal ShipPickingReference(MissionOccupancyGrid grid, Actor[] sourceActors, bool logReadiness = true)
        {
            this.grid = grid ?? throw new ArgumentNullException(nameof(grid));
            if (grid.Width != 24 || grid.Height != 24 || sourceActors == null || sourceActors.Length != 8)
                throw new NotSupportedException("The eight-ship reference24x24 world is required.");
            actors = (Actor[])sourceActors.Clone();
            Array.Sort(actors, (a, b) => a.Id.CompareTo(b.Id));
            LoadMasks();
            bool movingFound = false;
            for (int i = 0; i < actors.Length; i++)
            {
                Actor a = actors[i];
                if (a.Owner == null || string.IsNullOrEmpty(a.Descriptor) ||
                    !masks.TryGetValue(a.Descriptor, out ShipPointerMask mask) ||
                    mask.Width != a.Width || mask.Height != a.Height)
                    throw new InvalidOperationException("A source ship has no matching mask geometry.");
                for (int j = 0; j < i; j++)
                    if (a.Id == actors[j].Id || ReferenceEquals(a.Owner, actors[j].Owner))
                        throw new InvalidOperationException("Source ship identities must be distinct.");
                _ = new ShipPointerPose(mask, a.X, a.Y, a.Frame, a.Heading, a.ClassTag);
                if (a.Id == 0xbu) movingFound = true;
            }
            if (!movingFound) throw new InvalidOperationException("The source0b binding is missing.");
            describe = Describe;
            if (logReadiness)
                Debug.Log(Prefix + " ready: families=4; masks=96; payload_bytes=52800; payload_sha256=" + PayloadHash +
                          "; actors=8; fog=False; other_object_slots=empty; selection=False; mouse=False");
        }

        private static byte[] LoadBytes(string resource)
        {
            TextAsset asset = Resources.Load<TextAsset>("ShipPickingGenerated/" + resource);
            if (asset == null) throw new InvalidOperationException("The staged ship-picking resource is missing: " + resource);
            try { return asset.bytes; }
            finally { Resources.UnloadAsset(asset); }
        }
        private static string Hash(byte[] bytes)
        {
            using (SHA256 sha = SHA256.Create())
                return BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-", "").ToLowerInvariant();
        }
        private void LoadMasks()
        {
            Manifest manifest = JsonUtility.FromJson<Manifest>(Encoding.UTF8.GetString(LoadBytes("ShipPickingManifest")));
            byte[] payload = LoadBytes("ShipHitMasks");
            if (manifest == null || manifest.schema_version != 1 || manifest.native_canvas_width != 1920 ||
                manifest.native_canvas_height != 1080 || manifest.family_count != 4 || manifest.mask_count != 96 ||
                manifest.families == null || manifest.families.Length != 4 || payload.Length != 52800 || Hash(payload) != PayloadHash)
                throw new InvalidOperationException("The staged source mask manifest or payload differs.");
            int expectedOffset = 0;
            foreach (Family family in manifest.families)
            {
                if (family == null || string.IsNullOrEmpty(family.geometry_resource) ||
                    family.width < 1 || family.width > 2048 || family.height < 1 || family.height > 2048 ||
                    family.row_bytes != (family.width + 7) / 8 || family.masks == null || family.masks.Length != 24 ||
                    masks.ContainsKey(family.geometry_resource))
                    throw new InvalidOperationException("A staged mask family is invalid.");
                var planes = new byte[24][];
                for (int index = 0; index < planes.Length; index++)
                {
                    MaskRecord record = family.masks[index];
                    int length = family.row_bytes * family.height;
                    if (record == null || record.index != index || record.offset != expectedOffset ||
                        record.length != length || expectedOffset > payload.Length || length > payload.Length - expectedOffset)
                        throw new InvalidOperationException("A staged source mask extends outside its contiguous payload.");
                    planes[index] = new byte[length];
                    Buffer.BlockCopy(payload, expectedOffset, planes[index], 0, length);
                    if (Hash(planes[index]) != record.sha256)
                        throw new InvalidOperationException("A staged mask plane hash differs.");
                    expectedOffset += length;
                }
                masks.Add(family.geometry_resource, new ShipPointerMask(family.width, family.height, planes));
            }
            if (expectedOffset != payload.Length) throw new InvalidOperationException("Mask payload has an unreferenced tail.");
        }

        private Actor Find(object owner)
        {
            foreach (Actor actor in actors) if (ReferenceEquals(actor.Owner, owner)) return actor;
            throw new NotSupportedException("A query visited an owner outside the eight source ships.");
        }
        internal Actor ReadActor(object owner) => Find(owner);
        internal ShipPointerPose ReadPose(object owner, ShipMoveOrder.Snapshot state) => Pose(Find(owner), state);
        internal ShipPointerPose ReadLivePose(object owner,ShipMoveOrder.Snapshot state)
        {
            Actor actor=Find(owner);var m=state.Motion;
            return new ShipPointerPose(masks[actor.Descriptor],m.PublishedWorldX,m.PublishedWorldY,m.StoredFrame,m.Heading,actor.ClassTag);
        }
        private ShipPointerPose Pose(Actor actor) => Pose(actor, snapshot);
        private ShipPointerPose Pose(Actor actor, ShipMoveOrder.Snapshot state)
        {
            if (actor.Id == 0xbu)
            {
                var m = state.Motion;
                return new ShipPointerPose(masks[actor.Descriptor], m.PublishedWorldX, m.PublishedWorldY,
                                           m.StoredFrame, m.Heading, actor.ClassTag);
            }
            return new ShipPointerPose(masks[actor.Descriptor], actor.X, actor.Y, actor.Frame, actor.Heading, actor.ClassTag);
        }
        private ShipPointerPose Describe(object owner)
        {
            Actor actor = Find(owner);
            visited.Add(actor.Id);
            return Pose(actor);
        }
        private string Claims(object owner)
        {
            var text = new StringBuilder();
            for (int index = 0; index < beforeOwners.Length; index++)
                if (ReferenceEquals(beforeOwners[index], owner))
                {
                    if (text.Length != 0) text.Append(',');
                    text.Append(index.ToString(CultureInfo.InvariantCulture));
                }
            return text.ToString();
        }
        private void Query(string label, int x, int y, bool precise)
        {
            visited.Clear();
            int cellX = x / 64, cellY = y / 64;
            object picked = ShipWorldPicker.Pick(grid, x, y, cellX, cellY, precise, describe);
            var trace = new StringBuilder();
            foreach (uint id in visited)
            {
                if (trace.Length != 0) trace.Append(',');
                trace.Append(id.ToString("x8", CultureInfo.InvariantCulture));
            }
            string selected = picked == null ? "none" : Find(picked).Id.ToString("x8", CultureInfo.InvariantCulture);
            Debug.Log(Prefix + " query: stage=" + stage + "; sample=" + sample + "; index=" + queryIndex++ +
                      "; label=" + label + "; world=" + x + "," + y + "; cell=" + cellX + "," + cellY +
                      "; precise=" + precise + "; picked=" + selected + "; visited=" + trace);
        }
        internal void LogCheckpoint(string name, int sampleIndex, ShipMoveOrder.Snapshot state)
        {
            if (disposed) throw new ObjectDisposedException(nameof(ShipPickingReference));
            stage = name; sample = sampleIndex; snapshot = state; queryIndex = 0;
            for (int index = 0; index < beforeOwners.Length; index++)
                beforeOwners[index] = grid.GetOccupant(index % 24, index / 24);
            Actor moving = default;
            foreach (Actor actor in actors)
            {
                ShipPointerPose p = Pose(actor);
                Debug.Log(Prefix + " actor: stage=" + stage + "; id=" + actor.Id.ToString("x8", CultureInfo.InvariantCulture) +
                          "; descriptor=" + actor.Descriptor + "; class=" + actor.ClassTag + "; heading=" + p.Heading +
                          "; stored_frame=" + p.StoredFrame + "; sprite=" + p.PublishedWorldX + "," + p.PublishedWorldY +
                          "; claims=" + Claims(actor.Owner));
                string prefix = "actor-" + actor.Id.ToString("x8", CultureInfo.InvariantCulture) + "-center-";
                Query(prefix + "coarse", p.PublishedWorldX + actor.Width / 2, p.PublishedWorldY + actor.Height / 2, false);
                Query(prefix + "precise", p.PublishedWorldX + actor.Width / 2, p.PublishedWorldY + actor.Height / 2, true);
                if (actor.Id == 0xbu) moving = actor;
            }
            ShipPointerPose current = Pose(moving);
            Query("source0b-published-origin", current.PublishedWorldX, current.PublishedWorldY, true);
            Query("source0b-right-edge", current.PublishedWorldX + moving.Width, current.PublishedWorldY + moving.Height / 2, true);
            Query("source0b-bottom-edge", current.PublishedWorldX + moving.Width / 2, current.PublishedWorldY + moving.Height, true);
            Query("source0b-current-center-coarse", state.Motion.CellX * 64 + 32, state.Motion.CellY * 64 + 32, false);
            Query("source0b-current-center-precise", state.Motion.CellX * 64 + 32, state.Motion.CellY * 64 + 32, true);
            int reserved = state.Motion.ReservedCellIndex;
            if (reserved >= 0)
            {
                Query("source0b-reservation-center-coarse", reserved % 24 * 64 + 32, reserved / 24 * 64 + 32, false);
                Query("source0b-reservation-center-precise", reserved % 24 * 64 + 32, reserved / 24 * 64 + 32, true);
            }
            Query("map-top-left", 0, 0, true); Query("map-top-right", 1535, 0, true);
            Query("map-bottom-left", 0, 1535, true); Query("map-bottom-right", 1535, 1535, true);
            for (int index = 0; index < beforeOwners.Length; index++)
                if (!ReferenceEquals(beforeOwners[index], grid.GetOccupant(index % 24, index / 24)))
                    throw new InvalidOperationException("A source query mutated the occupancy grid.");
            Debug.Log(Prefix + " checkpoint_complete: stage=" + stage + "; sample=" + sample +
                      "; query_count=" + queryIndex + "; grid_unchanged=True");
        }
        public void Dispose()
        {
            if (disposed) return;
            disposed = true; masks.Clear(); visited.Clear();
            Array.Clear(beforeOwners, 0, beforeOwners.Length);
        }
    }
}
