using System;
using System.Collections.Generic;
using System.IO;
using AncientConquest.Presentation;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;

namespace AncientConquest.Editor
{
    /// <summary>Exercise actual Input System queue merging before domain dispatch.</summary>
    public static class ValidateMenuInput
    {
        [Serializable]
        private sealed class PointerSample
        {
            public int x;
            public int y;
            public bool held;
            public int state;
            public bool pressed;
            public bool hovered;
            public bool inside;
        }

        [Serializable]
        private sealed class CaseEvidence
        {
            public bool disableRedundantEventsMerging;
            public string deviceType;
            public string updateType;
            public int queuedEvents;
            public int inputUpdateCalls;
            public int receivedEvents;
            public int commandCount;
            public PointerSample[] received;
        }

        [Serializable]
        private sealed class InputEvidence
        {
            public string editorVersion;
            public string inputSystemAssemblyVersion;
            public string sequence;
            public string scope;
            public bool passed;
            public bool settingsRestored;
            public string failure;
            public CaseEvidence mergingEnabled;
            public CaseEvidence mergingDisabled;
        }

        public static void ValidateAndBuild()
        {
            Validate();
            BuildReferenceWindows.Build();
        }

        public static void Validate()
        {
            string output = Path.GetFullPath(Path.Combine(Application.dataPath,
                "../../../artifacts/unity-reference/input-system-validation.json"));
            if (File.Exists(output))
                throw new InvalidOperationException("Input validation report already exists; preserve it before rerunning: " + output);

            InputSettings settings = InputSystem.settings;
            bool previousMerging = settings.disableRedundantEventsMerging;
            InputSettings.UpdateMode previousMode = settings.updateMode;
            var report = new InputEvidence
            {
                editorVersion = Application.unityVersion,
                inputSystemAssemblyVersion = typeof(InputSystem).Assembly.GetName().Version.ToString(),
                sequence = "left down inside -> move outside held -> move inside held -> left up inside; all queued before one InputSystem.Update",
                scope = "Actual Editor Input System MouseState queue and MainMenuButton domain; no NativeMenuFrame focus or OS/hardware validation"
            };
            Exception failure = null;
            try
            {
                settings.updateMode = InputSettings.UpdateMode.ProcessEventsManually;
                report.mergingEnabled = RunCase(false);
                report.mergingDisabled = RunCase(true);
                if (report.mergingEnabled.queuedEvents != 4 ||
                    report.mergingEnabled.inputUpdateCalls != 1 ||
                    report.mergingEnabled.receivedEvents != 2 ||
                    report.mergingEnabled.commandCount != 1)
                    throw new InvalidOperationException("Negative control did not reproduce the merged excursion and unintended command.");
                if (report.mergingDisabled.queuedEvents != 4 ||
                    report.mergingDisabled.inputUpdateCalls != 1 ||
                    report.mergingDisabled.receivedEvents != 4 ||
                    report.mergingDisabled.commandCount != 0)
                    throw new InvalidOperationException("Disabling merging did not preserve the excursion and cancel the command.");
            }
            catch (Exception exception)
            {
                failure = exception;
                report.failure = exception.ToString();
            }
            finally
            {
                settings.disableRedundantEventsMerging = previousMerging;
                settings.updateMode = previousMode;
                report.settingsRestored = settings.disableRedundantEventsMerging == previousMerging &&
                                          settings.updateMode == previousMode &&
                                          ReferenceEquals(InputSystem.settings, settings);
            }
            report.passed = failure == null && report.settingsRestored;
            Directory.CreateDirectory(Path.GetDirectoryName(output));
            using (var stream = new FileStream(output, FileMode.CreateNew, FileAccess.Write))
            using (var writer = new StreamWriter(stream))
                writer.WriteLine(JsonUtility.ToJson(report, true));
            if (!report.passed)
                throw new InvalidOperationException("Actual Input System menu validation failed; see " + output, failure);
            Debug.Log("Menu Input System validation passed: merging control emitted 1 command; unmerged excursion emitted 0; " + output);
        }

        private static CaseEvidence RunCase(bool disableMerging)
        {
            InputSystem.settings.disableRedundantEventsMerging = disableMerging;
            Mouse previousMouse = Mouse.current;
            Mouse mouse = null;
            Action<InputEventPtr, InputDevice> listener = null;
            var samples = new List<PointerSample>();
            var evidence = new CaseEvidence { disableRedundantEventsMerging = disableMerging };
            var button = new MainMenuButton(112, 398, 278, 64);
            bool pointerKnown = false;
            bool heldPreviously = false;
            int lastX = 0;
            int lastY = 0;
            try
            {
                mouse = InputSystem.AddDevice<Mouse>("MenuInputValidationMouse");
                evidence.deviceType = mouse.GetType().FullName;
                listener = (inputEvent, device) =>
                {
                    if (device != mouse ||
                        (!inputEvent.IsA<StateEvent>() && !inputEvent.IsA<DeltaStateEvent>())) return;
                    evidence.receivedEvents++;
                    evidence.updateType = InputState.currentUpdateType.ToString();
                    if (mouse.position.ReadValueFromEvent(inputEvent, out Vector2 position))
                    {
                        int x = Mathf.FloorToInt(position.x);
                        int y = Mathf.FloorToInt(NativeMenuCanvas.Height - position.y);
                        if (!pointerKnown || x != lastX || y != lastY)
                        {
                            pointerKnown = true;
                            lastX = x;
                            lastY = y;
                            button.Process(MainMenuButton.Move, x, y);
                        }
                    }
                    if (pointerKnown && mouse.leftButton.ReadValueFromEvent(inputEvent, out float value))
                    {
                        bool held = value >= mouse.leftButton.pressPointOrDefault;
                        if (held != heldPreviously)
                        {
                            heldPreviously = held;
                            if (button.Process(held ? MainMenuButton.LeftDown : MainMenuButton.LeftUp, lastX, lastY))
                                evidence.commandCount++;
                        }
                    }
                    samples.Add(new PointerSample
                    {
                        x = lastX, y = lastY, held = heldPreviously,
                        state = button.State, pressed = button.Pressed,
                        hovered = button.Hovered, inside = button.Inside
                    });
                };
                InputSystem.onEvent += listener;
                // MouseState positions are bottom-left; native menu points use top-left.
                QueuePointer(mouse, 140, 424, true);
                QueuePointer(mouse, 40, 424, true);
                QueuePointer(mouse, 140, 424, true);
                QueuePointer(mouse, 140, 424, false);
                evidence.queuedEvents = 4;
                InputSystem.Update();
                evidence.inputUpdateCalls = 1;
                evidence.received = samples.ToArray();
                return evidence;
            }
            finally
            {
                if (listener != null) InputSystem.onEvent -= listener;
                if (mouse != null && mouse.added) InputSystem.RemoveDevice(mouse);
                if (previousMouse != null && previousMouse.added) previousMouse.MakeCurrent();
            }
        }

        private static void QueuePointer(Mouse mouse, int x, int y, bool held)
        {
            var state = new MouseState
            {
                position = new Vector2(x, NativeMenuCanvas.Height - y)
            }.WithButton(MouseButton.Left, held);
            InputSystem.QueueStateEvent<MouseState>(mouse, state);
        }
    }
}
