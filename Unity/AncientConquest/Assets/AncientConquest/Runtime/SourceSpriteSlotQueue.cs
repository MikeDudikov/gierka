using System;
using System.Collections.Generic;

namespace AncientConquest.World
{
    /// <summary>55d670/55d960/55ed60 slots, including callback ties and retained inactive positions.</summary>
    public sealed class SourceSpriteSlotQueue
    {
        private sealed class Node { internal int Depth = int.MaxValue, Position; internal bool Alive, Callback; }
        private readonly List<Node> nodes = new List<Node>();
        private readonly List<int> ascending = new List<int>();
        public int AllocatedCount => nodes.Count;
        public int LiveCount { get; private set; }
        public int Register(int depth, bool callback)
        {
            int id = 0;
            while (id < nodes.Count && nodes[id].Alive) id++;
            if (id == nodes.Count) { nodes.Add(new Node { Position = id }); ascending.Add(id); }
            Node node = nodes[id]; node.Alive = true; node.Callback = false; LiveCount++;
            if (depth >= 0) UpdateDepth(id, depth);
            // 55dc20 marks callback AFTER the normal registration/depth insertion.
            node.Callback = callback;
            return id;
        }
        public void Release(int id)
        {
            Node node = Require(id);
            if (!node.Alive) throw new InvalidOperationException("The source slot is already inactive.");
            node.Alive = false; LiveCount--;
        }
        public bool IsAlive(int id) => Require(id).Alive;
        public int GetDepth(int id) => Require(id).Depth;
        public int GetAllocatedDrawNode(int rank)
        {
            if (rank < 0 || rank >= nodes.Count) throw new ArgumentOutOfRangeException(nameof(rank));
            return ascending[nodes.Count - 1 - rank];
        }
        public void UpdateDepth(int id, int depth)
        {
            Node node = Require(id);
            if (!node.Alive) throw new InvalidOperationException("Only a live slot may change its depth.");
            int old = node.Depth, position = node.Position;
            node.Depth = depth;
            if (depth < old && position > 0 && depth < nodes[ascending[position - 1]].Depth)
            {
                int p = position - 1;
                while (p >= 0)
                {
                    Node other = nodes[ascending[p]];
                    if (other.Depth < depth || (other.Depth == depth && (node.Callback || !other.Callback))) break;
                    ascending[p + 1] = ascending[p]; other.Position = p + 1; p--;
                }
                ascending[p + 1] = id; node.Position = p + 1;
            }
            else if (old < depth && position + 1 < nodes.Count && nodes[ascending[position + 1]].Depth < depth)
            {
                int p = position + 1;
                while (p < nodes.Count)
                {
                    Node other = nodes[ascending[p]];
                    if (depth < other.Depth || (depth == other.Depth && (node.Callback || !other.Callback))) break;
                    ascending[p - 1] = ascending[p]; other.Position = p - 1; p++;
                }
                ascending[p - 1] = id; node.Position = p - 1;
            }
        }
        private Node Require(int id)
        {
            if (id < 0 || id >= nodes.Count) throw new ArgumentOutOfRangeException(nameof(id));
            return nodes[id];
        }
    }
}
