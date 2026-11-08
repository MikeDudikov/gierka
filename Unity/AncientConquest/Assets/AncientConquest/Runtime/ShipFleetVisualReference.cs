using System;
using System.Collections.Generic;
using System.Security.Cryptography;
using AncientConquest.Simulation;
using AncientConquest.World;
using UnityEngine;

namespace AncientConquest.Presentation
{
    /// <summary>Temporary-fleet selectors, healthy bars and retained source overlay slots.</summary>
    internal sealed class ShipFleetVisualReference : IDisposable
    {
        private const string Root = "ShipFleetVisualsGenerated/";
        private const string ManifestHash = "eeecb0962e8e3df778a41b0ba92fef45e66200c01936d34d4b057a4ce3f389d3";
        private const string PayloadHash = "441afbc4aad4297550bba5a455271d2e2bf69b7774122a8a3578f03bfe881e25";
        [Serializable] private sealed class Frame { public string name=null; public int atlas_x=0,atlas_y=0,width=0,height=0; }
        [Serializable] private sealed class Family { public int logical_size=0,selector_size=0,health_frame=0,health_width=0; public int[] frames=null; }
        [Serializable] private sealed class Manifest
        {
            public int schema_version=0,native_canvas_width=0,native_canvas_height=0,atlas_width=0,atlas_height=0,frame_count=0;
            public Frame[] frames=null; public Family[] families=null; public Waypoints wp_move=null;
        }
        [Serializable] private sealed class Waypoints
        {
            public string resource=null,payload_sha256=null;
            public int width=0,height=0,cell_size=0,world_offset_x=0,world_offset_y=0,depth=0;
            public Frame[] frames=null; public int[] ordinal_frames=null;
        }
        private sealed class Marker
        {
            internal int Group, Ordinal, Node;
            internal SpriteRenderer Renderer;
        }
        private readonly List<Marker> markers=new List<Marker>();
        private Transform visualParent;
        private Material visualMaterial;
        private Waypoints waypointTable;
        private Texture2D waypointAtlas;
        private Sprite[] waypointSprites;
        private sealed class Entry
        {
            internal ShipPickingReference.Actor Actor;
            internal ShipSelectionProgression Progress;
            internal Family Family;
            internal SpriteRenderer Selector, Health;
            internal int SelectorNode=-1, HealthNode=-1;
        }
        private readonly SourceSpriteSlotQueue queue = new SourceSpriteSlotQueue();
        private readonly Dictionary<object,Entry> entries = new Dictionary<object,Entry>();
        private readonly Dictionary<int,SpriteRenderer> renderers = new Dictionary<int,SpriteRenderer>();
        private readonly List<Entry> ordered = new List<Entry>();
        private readonly List<GameObject> objects = new List<GameObject>();
        private readonly Func<object,ShipPointerPose> poses;
        private Texture2D atlas;
        private Sprite[] sprites;
        private int baseCount, boxNode=-1;
        private bool disposed;
        internal int BoxOrder { get; private set; } = 46;
        internal int OverlayEndOrder => 44 + queue.LiveCount - baseCount;
        internal ShipFleetVisualReference(Transform parent, Material material, ShipPickingReference.Actor[] local,
            int[] sourceDepths, Func<object,ShipPointerPose> poses)
        {
            this.poses = poses; visualParent=parent; visualMaterial=material;
            try
            {
                foreach (int depth in sourceDepths) queue.Register(depth,false);
                baseCount=queue.AllocatedCount;
                if (baseCount!=21) throw new InvalidOperationException("The21 source world nodes are required.");
                TextAsset raw=Resources.Load<TextAsset>(Root+"ShipFleetVisualsManifest");
                if(raw==null)throw new InvalidOperationException("Missing fleet selector manifest.");
                Manifest manifest;
                try { if(Hash(raw.bytes)!=ManifestHash)throw new InvalidOperationException("Fleet manifest differs."); manifest=JsonUtility.FromJson<Manifest>(raw.text); }
                finally { Resources.UnloadAsset(raw); }
                raw=Resources.Load<TextAsset>(Root+"ShipFleetVisualsRgba");
                if(raw==null)throw new InvalidOperationException("Missing fleet selector atlas.");
                try { if(Hash(raw.bytes)!=PayloadHash)throw new InvalidOperationException("Fleet atlas differs."); }
                finally { Resources.UnloadAsset(raw); }
                if(manifest.schema_version!=1||manifest.native_canvas_width!=1920||manifest.native_canvas_height!=1080||manifest.atlas_width!=640||manifest.atlas_height!=400||manifest.frame_count!=33||manifest.frames.Length!=33||manifest.families.Length!=3)
                    throw new InvalidOperationException("Unsupported fleet selector geometry.");
                atlas=RgbaResourceTexture.Load(Root+"ShipFleetVisualsRgba",640,400,FilterMode.Point);sprites=new Sprite[33];
                for(int i=0;i<33;i++)
                {
                    Frame f=manifest.frames[i];
                    sprites[i]=Sprite.Create(atlas,new Rect(f.atlas_x,f.atlas_y,f.width,f.height),new Vector2(0,1),1,0,SpriteMeshType.FullRect);sprites[i].name=f.name;
                }
                //4ced80/546160:WPMOVE type8/mask table,isolated from simulation ownership.
                waypointTable=manifest.wp_move;
                if(waypointTable==null||waypointTable.ordinal_frames==null||waypointTable.ordinal_frames.Length!=256)
                    throw new InvalidOperationException("Missing original WPMOVE ordinal table.");
                raw=Resources.Load<TextAsset>(waypointTable.resource);
                if(raw==null)throw new InvalidOperationException("Missing original WPMOVE atlas.");
                try { if(Hash(raw.bytes)!=waypointTable.payload_sha256)throw new InvalidOperationException("WPMOVE atlas differs."); }
                finally { Resources.UnloadAsset(raw); }
                waypointAtlas=RgbaResourceTexture.Load(waypointTable.resource,waypointTable.width,waypointTable.height,FilterMode.Point);
                waypointSprites=new Sprite[waypointTable.frames.Length];
                for(int i=0;i<waypointSprites.Length;i++)
                {
                    Frame f=waypointTable.frames[i];
                    waypointSprites[i]=Sprite.Create(waypointAtlas,new Rect(f.atlas_x,f.atlas_y,f.width,f.height),new Vector2(0,1),1,0,SpriteMeshType.FullRect);
                    waypointSprites[i].name=f.name;
                }
                foreach(var actor in local)
                {
                    Family family=Array.Find(manifest.families,f=>f.logical_size==actor.Width);
                    if(family==null||actor.Width!=actor.Height||family.frames.Length!=10||family.selector_size!=actor.Width+4||family.health_width!=actor.Width-22)
                        throw new InvalidOperationException("Unknown source selector family.");
                    var entry=new Entry{Actor=actor,Family=family,Progress=new ShipSelectionProgression(actor.Width),
                        Selector=Create(parent,material,"Source selector "+actor.Id.ToString("x8")),Health=Create(parent,material,"Source healthy bar "+actor.Id.ToString("x8"))};
                    entries.Add(actor.Owner,entry);ordered.Add(entry);
                }
                ordered.Sort((a,b)=>a.Actor.Id.CompareTo(b.Actor.Id));
            }
            catch { Dispose(); throw; }
        }
        private static string Hash(byte[] bytes)
        { using(SHA256 sha=SHA256.Create())return BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-","").ToLowerInvariant(); }
        private SpriteRenderer Create(Transform parent,Material material,string name)
        {
            var go=new GameObject(name);objects.Add(go);go.transform.SetParent(parent,false);
            var renderer=go.AddComponent<SpriteRenderer>();renderer.sharedMaterial=material;renderer.color=Color.white;renderer.enabled=false;return renderer;
        }
        internal void SetBox(bool active)
        {
            if(active&&boxNode<0)boxNode=queue.Register(5,true);
            else if(!active&&boxNode>=0){queue.Release(boxNode);boxNode=-1;}
        }
        internal void ApplyEvent(ShipSelectionEvent change)
        {
            Entry entry=entries[change.Owner];
            if(change.Selected)
            {
                bool created=!entry.Progress.Current.Exists;var pose=poses(change.Owner);
                entry.Progress.Select(pose.PublishedWorldX,pose.PublishedWorldY);
                if(created)
                {
                    entry.SelectorNode=queue.Register(1020,false);entry.HealthNode=queue.Register(1020,true);
                    renderers.Add(entry.SelectorNode,entry.Selector);renderers.Add(entry.HealthNode,entry.Health);
                }
            }
            else entry.Progress.Deselect();
        }
        internal void AdvanceOwner(object owner,uint counter,int x,int y)
        {
            Entry entry=entries[owner];Advance(entry,counter,x,y);
        }
        private void Advance(Entry entry,uint counter,int x,int y)
        {
            entry.Progress.Advance(counter,1,x,y);
            if(entry.Progress.LastStepHidesHealth){Release(entry.HealthNode);entry.HealthNode=-1;}
            if(entry.Progress.LastStepDeletesSelector){Release(entry.SelectorNode);entry.SelectorNode=-1;}
        }
        private void Release(int node){queue.Release(node);renderers.Remove(node);}
        internal void Advance(uint counter)
        {
            foreach(Entry entry in ordered)
            {
                var s=entry.Progress.Current;
                if(s.StoredFrame<10||s.SelectionState==2)
                {var p=poses(entry.Actor.Owner);Advance(entry,counter,p.PublishedWorldX,p.PublishedWorldY);}
            }
        }
        //4ce6c0/4ced80/4ced10:read the existing owner's points;never change task/grid/membership.
        //545e80->55db50 registers non-callback sprites at the resource-table source depth.
        internal void SyncQueuedMarkers(ShipFleetMembership membership,int addedGroup=-1,int firstAddedOrdinal=int.MaxValue)
        {
            if(disposed)throw new ObjectDisposedException(nameof(ShipFleetVisualReference));
            for(int i=markers.Count-1;i>=0;i--)
            {
                Marker m=markers[i];
                if(m.Group<membership.GroupCount&&membership.GetTaskSubtype(m.Group)==2&&
                    m.Ordinal<membership.GetQueuedPointCount(m.Group))continue;
                Release(m.Node);m.Renderer.enabled=false;objects.Remove(m.Renderer.gameObject);
                m.Renderer.sprite=null;m.Renderer.sharedMaterial=null;UnityEngine.Object.Destroy(m.Renderer.gameObject);markers.RemoveAt(i);
            }
            for(int group=0;group<membership.GroupCount;group++)
            {
                if(membership.GetTaskSubtype(group)!=2)continue;
                for(int ordinal=0;ordinal<membership.GetQueuedPointCount(group);ordinal++)
                {
                    Marker marker=null;
                    foreach(Marker candidate in markers)if(candidate.Group==group&&candidate.Ordinal==ordinal){marker=candidate;break;}
                    if(marker==null)
                    {
                        //4ce6c0 creates ONLY newly appended points;4a2050/4cef10 removal
                        //does not change the logical route or imply recreation on next Work.
                        if(group!=addedGroup||ordinal<firstAddedOrdinal)continue;
                        marker=new Marker{Group=group,Ordinal=ordinal,Node=queue.Register(waypointTable.depth,false),
                            Renderer=Create(visualParent,visualMaterial,"Source WPMOVE "+group+":"+ordinal)};
                        markers.Add(marker);renderers.Add(marker.Node,marker.Renderer);
                    }
                    var point=membership.GetQueuedPoint(group,ordinal);
                    marker.Renderer.sprite=waypointSprites[waypointTable.ordinal_frames[ordinal&255]];
                    marker.Renderer.transform.localPosition=new Vector3(point.X*waypointTable.cell_size+waypointTable.world_offset_x,
                        -(point.Y*waypointTable.cell_size+waypointTable.world_offset_y),0);
                    marker.Renderer.enabled=true;
                }
            }
        }
        //4a2050(param2=0)->4cef10:delete graphics only,retain route and task.
        internal void HideQueuedMarkers(int group)
        {
            for(int i=markers.Count-1;i>=0;i--)
            {
                Marker marker=markers[i];if(marker.Group!=group)continue;
                Release(marker.Node);marker.Renderer.enabled=false;objects.Remove(marker.Renderer.gameObject);
                marker.Renderer.sprite=null;marker.Renderer.sharedMaterial=null;
                UnityEngine.Object.Destroy(marker.Renderer.gameObject);markers.RemoveAt(i);
            }
        }
        internal void Apply()
        {
            if(disposed)throw new ObjectDisposedException(nameof(ShipFleetVisualReference));
            int rank=44;
            for(int i=0;i<queue.AllocatedCount;i++)
            {
                int node=queue.GetAllocatedDrawNode(i);
                if(node<baseCount||!queue.IsAlive(node))continue;
                if(node==boxNode)BoxOrder=rank++;
                else renderers[node].sortingOrder=rank++;
            }
            foreach(Entry entry in ordered)
            {
                var s=entry.Progress.Current;
                entry.Selector.sprite=s.DrawnFrame<0?null:sprites[entry.Family.frames[s.DrawnFrame]];
                entry.Selector.transform.localPosition=new Vector3(s.WorldPixelX,-s.WorldPixelY,0);
                entry.Selector.enabled=s.Exists&&s.SelectorVisible;
                entry.Health.sprite=sprites[entry.Family.health_frame];
                entry.Health.transform.localPosition=new Vector3(s.HealthWorldX,-s.HealthWorldY,0);
                entry.Health.enabled=s.HealthExists&&s.HealthVisible;
            }
        }
        internal void Log(string stage)
        {
            foreach(Entry entry in ordered)
            {
                var s=entry.Progress.Current;
                Debug.Log("[ShipFleetSelection] visual: stage="+stage+"; id="+entry.Actor.Id.ToString("x8")+"; size="+entry.Actor.Width+
                    "; flag="+s.SelectionState+"; exists="+s.Exists+"; frame="+s.StoredFrame+"; drawn="+s.DrawnFrame+"; last="+s.LastCounter+
                    "; visible="+entry.Selector.enabled+"; position="+(int)entry.Selector.transform.localPosition.x+","+(int)-entry.Selector.transform.localPosition.y+
                    "; sprite="+(entry.Selector.sprite==null?"none":entry.Selector.sprite.name)+"; node="+entry.SelectorNode+"; order="+entry.Selector.sortingOrder+
                    "; health_exists="+s.HealthExists+"; health_visible="+entry.Health.enabled+"; health_position="+(int)entry.Health.transform.localPosition.x+","+(int)-entry.Health.transform.localPosition.y+
                    "; health_sprite="+entry.Health.sprite.name+"; health_node="+entry.HealthNode+"; health_order="+entry.Health.sortingOrder);
            }
            foreach(Marker marker in markers)
                Debug.Log("[ShipFleetWaypoint] visual: stage="+stage+"; group="+marker.Group+"; ordinal="+marker.Ordinal+
                    "; position="+(int)marker.Renderer.transform.localPosition.x+","+(int)-marker.Renderer.transform.localPosition.y+
                    "; sprite="+marker.Renderer.sprite.name+"; node="+marker.Node+"; order="+marker.Renderer.sortingOrder+"; visible="+marker.Renderer.enabled);
            Debug.Log("[ShipFleetSelection] slots: stage="+stage+"; allocated="+queue.AllocatedCount+"; live="+queue.LiveCount+"; box_node="+boxNode+"; box_order="+BoxOrder);
        }
        public void Dispose()
        {
            if(disposed)return;disposed=true;
            foreach(GameObject go in objects)if(go!=null){var renderer=go.GetComponent<SpriteRenderer>();renderer.sprite=null;renderer.sharedMaterial=null;UnityEngine.Object.Destroy(go);}
            if(sprites!=null)foreach(Sprite sprite in sprites)if(sprite!=null)UnityEngine.Object.Destroy(sprite);
            if(atlas!=null)UnityEngine.Object.Destroy(atlas);
            if(waypointSprites!=null)foreach(Sprite sprite in waypointSprites)if(sprite!=null)UnityEngine.Object.Destroy(sprite);
            if(waypointAtlas!=null)UnityEngine.Object.Destroy(waypointAtlas);
            markers.Clear();waypointSprites=null;waypointAtlas=null;visualParent=null;visualMaterial=null;waypointTable=null;
            objects.Clear();entries.Clear();ordered.Clear();renderers.Clear();sprites=null;atlas=null;
            Debug.Log("[ShipFleetSelection] cleanup: selectors_owned=3; visual_refs_cleared=True");
        }
    }
}
