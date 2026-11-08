using System;
using System.Collections.Generic;

namespace AncientConquest.World
{
    /// <summary>
    /// Original fresh normal-node depth insertion and update order.
    /// IDs are retained; draw order is the reverse of the ascending queue.
    /// Callback nodes, removed/recycled slots and renderer layers are outside this adapter.
    /// </summary>
    public sealed class SourceSpriteDepthQueue
    {
        private readonly List<int> depths = new List<int>();
        private readonly List<int> positions = new List<int>();
        private readonly List<int> ascending = new List<int>();

        public int Count { get { return depths.Count; } }

        /// <summary>
        /// Registers a fresh normal node. Source 55d670 leaves negative initial
        /// depths at int.MaxValue; later UpdateDepth accepts signed depths.
        /// </summary>
        public int Register(int depth)
        {
            int id = depths.Count;
            depths.Add(int.MaxValue);
            positions.Add(id);
            ascending.Add(id);
            if (depth >= 0) UpdateDepth(id, depth);
            return id;
        }

        /// <summary>Source 55d960 normal-node insertion loops, without callback bit 0x4000.</summary>
        public void UpdateDepth(int nodeId, int depth)
        {
            RequireNode(nodeId);
            int oldDepth = depths[nodeId];
            int position = positions[nodeId];
            depths[nodeId] = depth;
            if (depth < oldDepth)
            {
                // The strict neighboring comparison also preserves the current
                // side of a tie when no intervening node is crossed.
                if (position > 0 && depth < depths[ascending[position - 1]])
                {
                    int previous = position - 1;
                    while (previous >= 0)
                    {
                        int other = ascending[previous];
                        if (depths[other] <= depth) break;
                        ascending[previous + 1] = other;
                        positions[other] = previous + 1;
                        --previous;
                    }
                    ascending[previous + 1] = nodeId;
                    positions[nodeId] = previous + 1;
                }
            }
            else if (oldDepth < depth)
            {
                int next = position + 1;
                if (next < Count && depths[ascending[next]] < depth)
                {
                    while (next < Count)
                    {
                        int other = ascending[next];
                        if (depth <= depths[other]) break;
                        ascending[next - 1] = other;
                        positions[other] = next - 1;
                        ++next;
                    }
                    ascending[next - 1] = nodeId;
                    positions[nodeId] = next - 1;
                }
            }
        }

        public int GetDepth(int nodeId)
        {
            RequireNode(nodeId);
            return depths[nodeId];
        }

        public int[] CopyAscendingOrder()
        {
            return ascending.ToArray();
        }

        /// <summary>Returns one back-to-front node ID without allocating.</summary>
        public int GetDrawNode(int backToFrontIndex)
        {
            if (backToFrontIndex < 0 || backToFrontIndex >= Count)
                throw new ArgumentOutOfRangeException(nameof(backToFrontIndex));
            return ascending[Count - 1 - backToFrontIndex];
        }

        public int[] CopyDrawOrder()
        {
            int[] result = new int[Count];
            for (int index = 0; index < result.Length; ++index)
                result[index] = ascending[result.Length - 1 - index];
            return result;
        }

        private void RequireNode(int nodeId)
        {
            if (nodeId < 0 || nodeId >= Count)
                throw new ArgumentOutOfRangeException(nameof(nodeId));
        }
    }
}
