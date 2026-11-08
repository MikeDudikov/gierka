using System;
using System.Collections;
using System.Globalization;
using AncientConquest.World;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace AncientConquest.Presentation
{
    /// <summary>Explicit diagnostic source-terrain view; not a playable mission or its final camera.</summary>
    public sealed class TerrainReferenceFrame : MonoBehaviour
    {
        private const int DisplayScale = 2;
        [Serializable]
        private sealed class Manifest
        {
            public int schema_version = 0;
            public string mission = null;
            public int native_canvas_width = 0;
            public int native_canvas_height = 0;
            public int map_width_cells = 0;
            public int map_height_cells = 0;
            public int tile_width = 0;
            public int tile_height = 0;
            public int layer_count = 0;
            public int world_width_px = 0;
            public int world_height_px = 0;
            public int source_rgba_width = 0;
            public int source_rgba_height = 0;
        }

        private TerrainMapData map;
        private Texture2D texture;
        private Sprite sprite;
        private Material material;
        private SpriteRenderer terrainRenderer;
        private MissionObjectReference objectReference;
        private int requestedX;
        private int requestedY;
        private int exitAfterSeconds;

        private static bool IncludeFleetMotion =>
            Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-fleet-motion-reference") >= 0;
        private static bool IncludePicking =>
            Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-picking-reference") >= 0;
        private static bool IncludePointer =>
            Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-pointer-reference") >= 0;
        private static bool IncludeOrders =>
            Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-order-reference") >= 0;
        private static bool IncludeRoute =>
            Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-route-reference") >= 0;
        private static bool IncludeAdjacent =>
            Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-adjacent-reference") >= 0;
        private static bool IncludeMovement => IncludeFleetMotion || IncludePointer || IncludePicking || IncludeOrders || IncludeRoute || IncludeAdjacent ||
            Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-movement-reference") >= 0;
        private static bool IncludeShips => IncludeMovement ||
            Array.IndexOf(Environment.GetCommandLineArgs(), "--mission-unit-reference") >= 0;
        private static bool IncludeObjects => IncludeShips ||
            Array.IndexOf(Environment.GetCommandLineArgs(), "--mission-object-reference") >= 0;
        internal static bool IsRequested => IncludeObjects ||
            Array.IndexOf(Environment.GetCommandLineArgs(), "--terrain-reference") >= 0;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        private static void CreateWhenRequested()
        {
            //Managed diagnostic precondition;world registry order is explicit,not inferred from rendering.
            if(Array.IndexOf(Environment.GetCommandLineArgs(),"--ship-fleet-world-step")>=0&&!IncludeFleetMotion)
            {Debug.LogError("The world step requires --ship-fleet-motion-reference.");Application.Quit(1);return;}
            if ((Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-pointer-input-replay") >= 0 ||
                 Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-pointer-box-replay") >= 0) && !IncludePointer)
            {
                Debug.LogError("The ship pointer replay requires --ship-pointer-reference.");
                Application.Quit(1); return;
            }
            if (Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-pointer-input-replay") >= 0 &&
                Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-pointer-box-replay") >= 0)
            { Debug.LogError("Select one pointer replay at a time."); Application.Quit(1); return; }
            bool fleetSelection = Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-pointer-fleet-selection") >= 0;
            bool fleetReplay = Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-pointer-fleet-replay") >= 0;
            bool fleetMovement=Array.IndexOf(Environment.GetCommandLineArgs(),"--ship-pointer-fleet-movement")>=0;
            bool movementReplay=Array.IndexOf(Environment.GetCommandLineArgs(),"--ship-pointer-fleet-movement-replay")>=0;
            if((fleetMovement&&!fleetSelection)||(movementReplay&&!fleetMovement)||(fleetMovement&&fleetReplay))
            {Debug.LogError("Fleet movement needs pointer/fleet selection and its own replay.");Application.Quit(1);return;}
            if ((fleetSelection && !IncludePointer) || (fleetReplay && !fleetSelection) ||
                (fleetSelection && (Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-pointer-input-replay") >= 0 ||
                                   Array.IndexOf(Environment.GetCommandLineArgs(), "--ship-pointer-box-replay") >= 0)))
            { Debug.LogError("Fleet selection/replay requires its pointer mode and a separate replay."); Application.Quit(1); return; }
            if (!IsRequested) return;
            string[] arguments = Environment.GetCommandLineArgs();
            int movementModes = (IncludeFleetMotion ? 1 : 0) + (IncludePointer ? 1 : 0) + (IncludePicking ? 1 : 0) + (IncludeOrders ? 1 : 0) + (IncludeRoute ? 1 : 0) + (IncludeAdjacent ? 1 : 0) +
                                (Array.IndexOf(arguments, "--ship-movement-reference") >= 0 ? 1 : 0);
            if (movementModes > 1)
            {
                Debug.LogError("Select one ship movement diagnostic at a time.");
                Application.Quit(1);
                return;
            }
            if (Array.IndexOf(arguments, "--menu-input-replay") >= 0 ||
                Array.IndexOf(arguments, "--briefing-input-replay") >= 0)
            {
                Debug.LogError("Terrain reference cannot run with a menu/briefing input replay.");
                Application.Quit(1);
                return;
            }
            var frame = new GameObject("Source terrain reference (explicit diagnostic)");
            DontDestroyOnLoad(frame);
            frame.AddComponent<TerrainReferenceFrame>();
        }

        private void Awake()
        {
#if UNITY_STANDALONE_WIN && !UNITY_EDITOR
            Screen.SetResolution(NativeMenuCanvas.Width, NativeMenuCanvas.Height,
                                 FullScreenMode.ExclusiveFullScreen);
#endif
            try
            {
                requestedX = ReadArgument("--terrain-origin-x", 0);
                requestedY = ReadArgument("--terrain-origin-y", 0);
                exitAfterSeconds = ReadArgument("--terrain-reference-exit-after", 0);
                if (exitAfterSeconds < 0 || exitAfterSeconds > 60)
                    throw new ArgumentOutOfRangeException(nameof(exitAfterSeconds));
                Manifest info = LoadManifest();
                TextAsset payload = Resources.Load<TextAsset>("TerrainGenerated/MapPlanar");
                if (payload == null) throw new InvalidOperationException("Terrain planar data is missing.");
                try
                {
                    map = new TerrainMapData(info.map_width_cells, info.map_height_cells,
                                             info.tile_width, info.tile_height, payload.bytes);
                }
                finally { Resources.UnloadAsset(payload); }
                if (info.world_width_px != map.WidthCells * map.TileWidth ||
                    info.world_height_px != map.HeightCells * map.TileHeight ||
                    info.source_rgba_width != info.world_width_px ||
                    info.source_rgba_height != info.world_height_px ||
                    info.world_width_px < NativeMenuCanvas.Width / DisplayScale ||
                    info.world_height_px < NativeMenuCanvas.Height / DisplayScale)
                    throw new InvalidOperationException("Terrain dimensions do not fit this diagnostic view.");
                texture = RgbaResourceTexture.Load("TerrainGenerated/TerrainRgba",
                    info.source_rgba_width, info.source_rgba_height, FilterMode.Point);
                material = Resources.Load<Material>("TerrainReferenceMaterial");
                if (material == null || material.shader == null || !material.shader.isSupported)
                    throw new InvalidOperationException("The staged URP2D terrain material is missing or unsupported.");
                sprite = Sprite.Create(texture, new Rect(0, 0, texture.width, texture.height),
                                       new Vector2(0, 1), 1, 0, SpriteMeshType.FullRect);
                terrainRenderer = gameObject.AddComponent<SpriteRenderer>();
                terrainRenderer.sharedMaterial = material;
                terrainRenderer.color = Color.white;
                terrainRenderer.sprite = sprite;
                if (IncludeObjects) objectReference = new MissionObjectReference(transform, material, IncludeShips);
            }
            catch (Exception exception) { Fail(exception); }
        }

        private static int ReadArgument(string name, int fallback)
        {
            string[] arguments = Environment.GetCommandLineArgs();
            int index = Array.IndexOf(arguments, name);
            if (index < 0) return fallback;
            if (index + 1 >= arguments.Length ||
                !int.TryParse(arguments[index + 1], NumberStyles.Integer, CultureInfo.InvariantCulture, out int value))
                throw new ArgumentException("Expected an integer after " + name);
            return value;
        }

        private static Manifest LoadManifest()
        {
            TextAsset asset = Resources.Load<TextAsset>("TerrainGenerated/TerrainManifest");
            if (asset == null) throw new InvalidOperationException("Terrain manifest is missing; stage miss000 first.");
            Manifest info;
            try { info = JsonUtility.FromJson<Manifest>(asset.text); }
            finally { Resources.UnloadAsset(asset); }
            if (info == null || info.schema_version != 1 || info.mission != "miss000" ||
                info.native_canvas_width != NativeMenuCanvas.Width ||
                info.native_canvas_height != NativeMenuCanvas.Height || info.layer_count != TerrainMapData.LayerCount)
                throw new InvalidOperationException("Terrain manifest does not match the reference contract.");
            return info;
        }

        private IEnumerator Start()
        {
            float started = Time.realtimeSinceStartup;
            while (Screen.width != NativeMenuCanvas.Width || Screen.height != NativeMenuCanvas.Height)
            {
                if (Time.realtimeSinceStartup - started > 10f)
                {
                    Fail(new InvalidOperationException("Terrain reference did not obtain the requested display."));
                    yield break;
                }
                yield return null;
            }
            Camera camera = Camera.main;
            if (camera == null)
            {
                Fail(new InvalidOperationException("Terrain reference camera is missing."));
                yield break;
            }
            int viewWidth = NativeMenuCanvas.Width / DisplayScale;
            int viewHeight = NativeMenuCanvas.Height / DisplayScale;
            int columns = (viewWidth + map.TileWidth - 1) / map.TileWidth;
            int rows = (viewHeight + map.TileHeight - 1) / map.TileHeight;
            int x = TerrainViewport.ClampAxis(requestedX, map.WidthCells, columns);
            int y = TerrainViewport.ClampAxis(requestedY, map.HeightCells, rows);
            int sourceX = x * map.TileWidth;
            int sourceY = y * map.TileHeight;
            camera.rect = new Rect(0, 0, 1, 1);
            camera.orthographic = true;
            camera.orthographicSize = viewHeight * .5f;
            camera.aspect = (float)NativeMenuCanvas.Width / NativeMenuCanvas.Height;
            camera.transform.SetPositionAndRotation(new Vector3(sourceX + viewWidth * .5f,
                -sourceY - viewHeight * .5f, -10), Quaternion.identity);
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = Color.black;
            camera.allowHDR = false;
            camera.allowMSAA = false;
            if (camera.TryGetComponent(out UniversalAdditionalCameraData urp))
            {
                urp.renderPostProcessing = false;
                urp.antialiasing = AntialiasingMode.None;
            }
            yield return new WaitForEndOfFrame();
            Debug.Log("Terrain reference display: " + Screen.width + "x" + Screen.height +
                      "; fullscreen=" + Screen.fullScreen + "; mode=" + Screen.fullScreenMode);
            Debug.Log("Terrain reference view: origin_cells=" + x + "," + y +
                      "; source_rect=" + sourceX + "," + sourceY + "," + viewWidth + "," + viewHeight +
                      "; scale=" + DisplayScale + "; world=" + map.WidthCells * map.TileWidth + "x" +
                      map.HeightCells * map.TileHeight + "; layers=" + TerrainMapData.LayerCount);
            Debug.Log("Terrain reference ready: mission=miss000; rendering=SpriteRenderer; diagnostic-only=True");
            objectReference?.LogReadiness();
            if (IncludeMovement)
            {
                // Drive the single enumerator explicitly so a diagnostic
                // failure quits with evidence instead of silently hanging.
                IEnumerator movement = null;
                Exception failure = null;
                try { movement = IncludeFleetMotion ? objectReference.CreateFleetMotionReference() :
                    IncludePointer ? objectReference.CreatePointerReference(sourceX, sourceY) :
                    IncludePicking ? objectReference.CreatePickingReference() :
                    IncludeOrders ? objectReference.CreateOrderReference() :
                    IncludeRoute ? objectReference.CreateRouteReference() :
                    IncludeAdjacent ? objectReference.CreateAdjacentReference() : objectReference.CreateMovementReference(); }
                catch (Exception exception) { failure = exception; }
                if (failure != null) { Fail(failure); yield break; }
                while (true)
                {
                    bool next = false;
                    object instruction = null;
                    try { next = movement.MoveNext(); if (next) instruction = movement.Current; }
                    catch (Exception exception) { failure = exception; }
                    if (failure != null) { Fail(failure); yield break; }
                    if (!next) break;
                    yield return instruction;
                }
            }
            if (exitAfterSeconds > 0)
            {
                yield return new WaitForSecondsRealtime(exitAfterSeconds);
                Debug.Log("Terrain reference diagnostic exit: requested_seconds=" + exitAfterSeconds + "; code=0");
                Application.Quit(0);
            }
        }

        private void Fail(Exception exception)
        {
            Debug.LogException(exception, this);
            enabled = false;
            Application.Quit(1);
        }

        private void OnDestroy()
        {
            objectReference?.Dispose();
            if (terrainRenderer != null)
            {
                terrainRenderer.sprite = null;
                terrainRenderer.sharedMaterial = null;
            }
            if (sprite != null) Destroy(sprite);
            if (texture != null) Destroy(texture);
            if (material != null) Resources.UnloadAsset(material);
        }
    }
}
