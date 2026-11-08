using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;
using AncientConquest.Presentation;

namespace AncientConquest.Editor
{
    public static class BuildReferenceWindows
    {
        [Serializable]
        private sealed class BuildEvidence
        {
            public string result;
            public string platform;
            public string output;
            public string editorVersion;
            public int warnings;
            public int errors;
            public long bytes;
            public string resolution;
            public bool development;
        }
        [Serializable]
        private sealed class StagedCanvas
        {
            public int schema_version = 0;
            public int native_canvas_width = 0;
            public int native_canvas_height = 0;
        }

        private static void RequireStage(string directory, string manifestName,
                                         int schema, params string[] payloads)
        {
            string manifest = Path.Combine(directory, manifestName);
            if (!File.Exists(manifest))
                throw new FileNotFoundException("Stage required presentation data before building", manifest);
            StagedCanvas canvas = JsonUtility.FromJson<StagedCanvas>(File.ReadAllText(manifest));
            if (canvas == null || canvas.schema_version != schema ||
                canvas.native_canvas_width != NativeMenuCanvas.Width ||
                canvas.native_canvas_height != NativeMenuCanvas.Height)
                throw new InvalidOperationException("Restage presentation data for the current native canvas: " + manifest);
            foreach (string payload in payloads)
            {
                string path = Path.Combine(directory, payload);
                if (!File.Exists(path))
                    throw new FileNotFoundException("Required presentation payload is missing", path);
            }
        }

        private static void EnsureTerrainMaterial()
        {
            const string path = "Assets/Resources/TerrainReferenceMaterial.mat";
            const string shaderName = "Universal Render Pipeline/2D/Sprite-Unlit-Default";
            Material material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material != null)
            {
                if (material.shader == null || material.shader.name != shaderName ||
                    material.color != Color.white)
                    throw new InvalidOperationException("Terrain reference material no longer matches its source-pixel contract: " + path);
                return;
            }
            if (File.Exists(path))
                throw new InvalidOperationException("An unreadable terrain material already exists: " + path);
            Shader shader = Shader.Find(shaderName);
            if (shader == null)
                throw new InvalidOperationException("The installed URP2D package is missing " + shaderName);
            material = new Material(shader) { name = "TerrainReferenceMaterial", color = Color.white };
            AssetDatabase.CreateAsset(material, path);
            AssetDatabase.SaveAssets();
        }

        // Invoke only after the project imports successfully in a licensed Editor.
        public static void Build()
        {
            const string scene = "Assets/Scenes/SampleScene.unity";
            if (!File.Exists(scene))
                throw new FileNotFoundException("Official template scene is missing", scene);
            RequireStage("Assets/Resources/ReferenceGenerated", "MenuRgbaManifest.json", 3,
                         "MenuRgba.bytes", "MenuButtonsRgba.bytes");
            RequireStage("Assets/Resources/BriefingGenerated", "BriefingManifest.json", 1,
                         "BackgroundRgba.bytes", "StaticUiRgba.bytes", "ButtonsRgba.bytes", "DifficultyRgba.bytes");
            RequireStage("Assets/Resources/TerrainGenerated", "TerrainManifest.json", 1,
                         "TerrainRgba.bytes", "MapPlanar.bytes");
            RequireStage("Assets/Resources/MissionObjectsGenerated", "MissionObjectsManifest.json", 1,
                         "ObjectSeeds.bytes", "ReefFramesRgba.bytes", "MissionDescriptor.bytes", "SavedViews.bytes");
            RequireStage("Assets/Resources/MissionUnitsGenerated", "MissionUnitsManifest.json", 1,
                         "CellFlags.bytes", "ShipComponentsRgba.bytes");
            RequireStage("Assets/Resources/ShipMovementGenerated", "ShipMovementManifest.json", 1,
                         "ShipMovementRgba.bytes");
            RequireStage("Assets/Resources/ShipPickingGenerated", "ShipPickingManifest.json", 1,
                         "ShipHitMasks.bytes");
            RequireStage("Assets/Resources/ShipPointerVisualsGenerated", "ShipPointerVisualsManifest.json", 1,
                         "ShipPointerVisualsRgba.bytes");
            RequireStage("Assets/Resources/ShipFleetVisualsGenerated", "ShipFleetVisualsManifest.json", 1,
                         "ShipFleetVisualsRgba.bytes", "WpMoveRgba.bytes");
            RequireStage("Assets/Resources/ShipHeavyMovementGenerated", "ShipHeavyMovementManifest.json", 1,
                         "ShipHeavyMovementRgba.bytes");
            EnsureTerrainMaterial();

            PlayerSettings.fullScreenMode = FullScreenMode.ExclusiveFullScreen;
            PlayerSettings.defaultScreenWidth = NativeMenuCanvas.Width;
            PlayerSettings.defaultScreenHeight = NativeMenuCanvas.Height;
            PlayerSettings.defaultIsNativeResolution = false;
            PlayerSettings.resizableWindow = false;
            PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.Standalone,
                                               ScriptingImplementation.Mono2x);

            string output = Path.GetFullPath(Path.Combine(Application.dataPath,
                "../../../artifacts/unity-reference/Windows/AncientConquestReference.exe"));
            Directory.CreateDirectory(Path.GetDirectoryName(output));
            BuildReport report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { scene },
                locationPathName = output,
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.None
            });
            File.WriteAllText(Path.Combine(Path.GetDirectoryName(output), "build-report.json"),
                JsonUtility.ToJson(new BuildEvidence
                {
                    result = report.summary.result.ToString(),
                    platform = report.summary.platform.ToString(),
                    output = output,
                    editorVersion = Application.unityVersion,
                    warnings = (int)report.summary.totalWarnings,
                    errors = (int)report.summary.totalErrors,
                    bytes = (long)report.summary.totalSize,
                    resolution = NativeMenuCanvas.Width + "x" + NativeMenuCanvas.Height,
                    development = false
                }, true));
            if (report.summary.result != BuildResult.Succeeded)
                throw new InvalidOperationException("Windows reference build failed: " + report.summary.result);
            Debug.Log("Windows reference build succeeded: " + output);
        }
    }
}
