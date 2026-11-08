using System;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;

namespace AncientConquest.Presentation
{
    /// <summary>Ordered mouse-event bridge. World rules belong to its configured receiver.</summary>
    internal sealed class WorldPointerInput : MonoBehaviour
    {
        internal const int Move = 0x60, LeftDown = 0x61, LeftUp = 0x62, RightDown = 0x63, RightUp = 0x64;
        private Action<int, int, int> dispatch;
        private Action cancel;
        private Action<bool> routeVisibility;
        private Keyboard routeKeyboard;
        private bool leftShiftHeld,rightShiftHeld;
        private Mouse pointer;
        private bool known, leftHeld, rightHeld, requireLeftRelease, requireRightRelease;
        private bool subscribed, previousMerging;
        private int x, y;

        internal void Configure(Action<int, int, int> receiver, Action cancelled,Action<bool> sourceRouteVisibility=null)
        {
            if (isActiveAndEnabled || dispatch != null)
                throw new InvalidOperationException("Configure the inactive pointer bridge exactly once.");
            dispatch = receiver ?? throw new ArgumentNullException(nameof(receiver));
            cancel = cancelled ?? throw new ArgumentNullException(nameof(cancelled));
            routeVisibility=sourceRouteVisibility;
        }
        private void OnEnable()
        {
            if (dispatch == null)
            {
                Debug.LogError("World pointer bridge enabled without its receiver.");
                enabled = false;
                return;
            }
            previousMerging = InputSystem.settings.disableRedundantEventsMerging;
            InputSystem.settings.disableRedundantEventsMerging = true;
            InputSystem.onEvent += OnInputEvent;
            InputSystem.onDeviceChange += OnDeviceChange;
            subscribed = true;
        }
        private void OnDisable()
        {
            if (subscribed)
            {
                InputSystem.onEvent -= OnInputEvent;
                InputSystem.onDeviceChange -= OnDeviceChange;
                InputSystem.settings.disableRedundantEventsMerging = previousMerging;
                subscribed = false;
            }
            routeKeyboard=null;leftShiftHeld=rightShiftHeld=false;
            CancelPointer();
        }
        private void OnApplicationFocus(bool focused)
        {
            if (!focused) CancelPointer();
        }
        private void OnDeviceChange(InputDevice device, InputDeviceChange change)
        {
            if (device == pointer && (change == InputDeviceChange.Removed ||
                change == InputDeviceChange.Disconnected || change == InputDeviceChange.Disabled))
                CancelPointer();
        }
        private void CancelPointer()
        {
            pointer = null; known = false; leftHeld = rightHeld = false;
            requireLeftRelease = requireRightRelease = true;
            // Cancellation must never manufacture an Up event: source Up can issue a command.
            cancel?.Invoke();
        }
        //4e9710 records DIK42/54 ->C45D1 on press,C45D0 on release;4eff00 forwards each.
        //A two-transition snapshot has no original event order,so this bounded bridge rejects it.
        private void OnRouteKeyEvent(InputEventPtr inputEvent,Keyboard keyboard)
        {
            bool previousLeft=routeKeyboard==keyboard&&leftShiftHeld,previousRight=routeKeyboard==keyboard&&rightShiftHeld;
            bool hasLeft=keyboard.leftShiftKey.ReadValueFromEvent(inputEvent,out float left);
            bool hasRight=keyboard.rightShiftKey.ReadValueFromEvent(inputEvent,out float right);
            bool nextLeft=hasLeft?left>=keyboard.leftShiftKey.pressPointOrDefault:previousLeft;
            bool nextRight=hasRight?right>=keyboard.rightShiftKey.pressPointOrDefault:previousRight;
            bool changedLeft=hasLeft&&nextLeft!=previousLeft,changedRight=hasRight&&nextRight!=previousRight;
            if(changedLeft&&changedRight)throw new NotSupportedException("Ordered source Shift transitions are required;the snapshot loses their order.");
            routeKeyboard=keyboard;leftShiftHeld=nextLeft;rightShiftHeld=nextRight;
            if(changedLeft)
            {
                Debug.Log("[ShipFleetWaypoint] key-control: name="+keyboard.leftShiftKey.keyCode+"; visible="+nextLeft);
                routeVisibility(nextLeft);
            }
            if(changedRight)
            {
                Debug.Log("[ShipFleetWaypoint] key-control: name="+keyboard.rightShiftKey.keyCode+"; visible="+nextRight);
                routeVisibility(nextRight);
            }
        }
        private void OnInputEvent(InputEventPtr inputEvent, InputDevice device)
        {
            if (!Application.isFocused || dispatch == null ||
                Screen.width <= 0 || Screen.height <= 0 ||
                (!inputEvent.IsA<StateEvent>() && !inputEvent.IsA<DeltaStateEvent>())) return;
            try
            {
                if(routeVisibility!=null&&device is Keyboard keyboard){OnRouteKeyEvent(inputEvent,keyboard);return;}
                if(!(device is Mouse mouse))return;
                if (pointer != null && pointer != mouse) CancelPointer();
                pointer = mouse;
                if (mouse.position.ReadValueFromEvent(inputEvent, out Vector2 position))
                {
                    if (float.IsNaN(position.x) || float.IsNaN(position.y) ||
                        float.IsInfinity(position.x) || float.IsInfinity(position.y))
                    { CancelPointer(); return; }
                    int nextX = Mathf.FloorToInt(position.x * NativeMenuCanvas.Width / Screen.width);
                    int nextY = Mathf.FloorToInt((Screen.height - position.y) * NativeMenuCanvas.Height / Screen.height);
                    if (!known || nextX != x || nextY != y)
                    {
                        x = nextX; y = nextY; known = true;
                        dispatch(Move, x, y);
                    }
                }
                if (!known) return;
                if (mouse.leftButton.ReadValueFromEvent(inputEvent, out float left))
                {
                    bool held = left >= mouse.leftButton.pressPointOrDefault;
                    if (requireLeftRelease)
                    {
                        leftHeld = held;
                        if (!held) requireLeftRelease = false;
                    }
                    else if (held != leftHeld)
                    {
                        leftHeld = held; dispatch(held ? LeftDown : LeftUp, x, y);
                    }
                }
                if (mouse.rightButton.ReadValueFromEvent(inputEvent, out float right))
                {
                    bool held = right >= mouse.rightButton.pressPointOrDefault;
                    if (requireRightRelease)
                    {
                        rightHeld = held;
                        if (!held) requireRightRelease = false;
                    }
                    else if (held != rightHeld)
                    {
                        rightHeld = held; dispatch(held ? RightDown : RightUp, x, y);
                    }
                }
            }
            catch (Exception exception)
            {
                Debug.LogException(exception, this);
                enabled = false;
                Application.Quit(1);
            }
        }
    }
}
