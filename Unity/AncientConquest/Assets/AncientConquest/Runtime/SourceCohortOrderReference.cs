using System;
using System.Collections.Generic;
using AncientConquest.World;
using UnityEngine;

namespace AncientConquest.Presentation
{
    /// <summary>Source depth updates for the retained21-node diagnostic cohort, not the full world.</summary>
    internal sealed class SourceCohortOrderReference : IDisposable
    {
        internal enum GroupKind { InlineParent, SeparateShadow, Reef }

        internal sealed class Group
        {
            internal readonly uint InstanceId;
            internal readonly GroupKind Kind;
            internal readonly int InitialDepth;
            internal readonly SpriteRenderer[] Renderers;
            internal readonly int[] SourceIndices;

            internal Group(uint instanceId, GroupKind kind, int depth,
                           SpriteRenderer[] renderers, int[] sourceIndices)
            {
                if (renderers == null || sourceIndices == null || renderers.Length == 0 ||
                    renderers.Length != sourceIndices.Length)
                    throw new ArgumentException("A source group needs matching renderer and component bindings.");
                InstanceId = instanceId; Kind = kind; InitialDepth = depth;
                Renderers = (SpriteRenderer[])renderers.Clone();
                SourceIndices = (int[])sourceIndices.Clone();
                var indices = new HashSet<int>();
                for (int index = 0; index < Renderers.Length; index++)
                    if (Renderers[index] == null || !indices.Add(SourceIndices[index]))
                        throw new ArgumentException("A source group has a missing or repeated component binding.");
            }
        }

        private readonly SourceSpriteDepthQueue queue = new SourceSpriteDepthQueue();
        private readonly Dictionary<uint, int> parentNodes = new Dictionary<uint, int>();
        private readonly Group[] groups;
        private bool disposed;
        internal int[] CopyRegisteredDepths()
        {
            var depths = new int[groups.Length];
            for (int i = 0; i < depths.Length; i++) depths[i] = groups[i].InitialDepth;
            return depths;
        }


        internal SourceCohortOrderReference(IEnumerable<Group> sourceGroups)
        {
            if (sourceGroups == null) throw new ArgumentNullException(nameof(sourceGroups));
            var registration = new List<Group>(sourceGroups);
            foreach (Group group in registration)
                if (group == null) throw new ArgumentException("A source draw group is missing.", nameof(sourceGroups));
            // Relative original object enumeration, then parent before its
            // separately registered negative-depth child. IDs remain retained.
            registration.Sort((left, right) => left.InstanceId != right.InstanceId ?
                left.InstanceId.CompareTo(right.InstanceId) : left.Kind.CompareTo(right.Kind));
            if (registration.Count != 21)
                throw new InvalidOperationException("The verified draw cohort contains21 source groups.");
            groups = new Group[registration.Count];
            int parents = 0, shadows = 0, reefs = 0, components = 0;
            var renderers = new HashSet<SpriteRenderer>();
            var groupKeys = new HashSet<string>(StringComparer.Ordinal);
            foreach (Group group in registration)
            {
                if (group == null || !groupKeys.Add(group.InstanceId + ":" + group.Kind))
                    throw new InvalidOperationException("Duplicate or missing diagnostic draw group.");
                int node = queue.Register(group.InitialDepth);
                groups[node] = group;
                components += group.Renderers.Length;
                foreach (SpriteRenderer renderer in group.Renderers)
                    if (!renderers.Add(renderer))
                        throw new InvalidOperationException("A renderer belongs to multiple source groups.");
                switch (group.Kind)
                {
                    case GroupKind.InlineParent:
                        parents++;
                        parentNodes.Add(group.InstanceId, node);
                        foreach (int index in group.SourceIndices)
                            if (index <= 0) throw new InvalidOperationException("A parent group contains a non-inline component.");
                        break;
                    case GroupKind.SeparateShadow:
                        shadows++;
                        if (group.InitialDepth != 21000 || group.SourceIndices.Length != 1 || group.SourceIndices[0] != 0)
                            throw new InvalidOperationException("The source shadow recipe differs from its verified group.");
                        break;
                    case GroupKind.Reef:
                        reefs++;
                        if (group.InitialDepth != 20200 || group.SourceIndices.Length != 1 || group.SourceIndices[0] != -1)
                            throw new InvalidOperationException("The source reef recipe differs from its verified group.");
                        break;
                    default: throw new InvalidOperationException("Unsupported source group kind.");
                }
            }
            if (parents != 8 || shadows != 8 || reefs != 5 || components != 34)
                throw new InvalidOperationException("The known draw cohort is incomplete.");
            ApplyOrders();
        }

        internal void UpdateParent(uint instanceId, int depth)
        {
            if (disposed) throw new ObjectDisposedException(nameof(SourceCohortOrderReference));
            if (!parentNodes.TryGetValue(instanceId, out int node))
                throw new ArgumentOutOfRangeException(nameof(instanceId));
            // Same-depth writes also reach the source queue; it preserves the
            // current side of equal-depth ties instead of re-registering IDs.
            queue.UpdateDepth(node, depth);
            ApplyOrders();
        }

        private void ApplyOrders()
        {
            int order = 10;
            for (int draw = 0; draw < queue.Count; draw++)
            {
                Group group = groups[queue.GetDrawNode(draw)];
                foreach (SpriteRenderer renderer in group.Renderers)
                {
                    if (renderer.sortingOrder != order) renderer.sortingOrder = order;
                    order++;
                }
            }
            if (order != 44) throw new InvalidOperationException("The flattened cohort must contain34 renderers.");
        }

        internal void LogReadiness(string prefix = "[ShipRouteReference]")
        {
            for (int node = 0; node < queue.Count; node++)
            {
                Group group = groups[node];
                Debug.Log(prefix + " registration: node=" + node + "; kind=" + KindName(group.Kind) +
                          "; id=" + group.InstanceId.ToString("x8") + "; depth=" + group.InitialDepth +
                          "; components=" + group.Renderers.Length);
            }
        }

        internal void LogStage(string stage, string prefix = "[ShipRouteReference]")
        {
            if (disposed) throw new ObjectDisposedException(nameof(SourceCohortOrderReference));
            for (int draw = 0; draw < queue.Count; draw++)
            {
                int node = queue.GetDrawNode(draw);
                Group group = groups[node];
                for (int index = 0; index < group.Renderers.Length; index++)
                    Debug.Log(prefix + " queue: stage=" + stage + "; node=" + node +
                              "; kind=" + KindName(group.Kind) + "; id=" + group.InstanceId.ToString("x8") +
                              "; part=" + group.SourceIndices[index] + "; depth=" + queue.GetDepth(node) +
                              "; order=" + group.Renderers[index].sortingOrder);
            }
        }

        private static string KindName(GroupKind kind)
        {
            return kind == GroupKind.InlineParent ? "inline_parent" :
                   kind == GroupKind.SeparateShadow ? "separate_shadow" : "reef";
        }

        public void Dispose()
        {
            if (disposed) return;
            disposed = true;
            parentNodes.Clear();
            Array.Clear(groups, 0, groups.Length);
        }
    }
}
