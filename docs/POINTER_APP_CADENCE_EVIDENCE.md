# Cadence of source cursor Life

Read-only source inspection, 2026-11-03. The cursor belongs to the generic
**BaseSystem**, so its message 0 is sent per application iteration independently
of PlaySystem's world-step gate. The application iteration itself is paced.
For configured gameplay speed 5 the normal quiet-loop period is **40 ms**.
This does not establish an unrestricted render-rate cursor Life or an exact
40 ms timer in every operating condition.

The original executable is unchanged, SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Address, table, import and disassembly evidence is recorded in
[source-cadence.json](../artifacts/world-input/cadence/source-cadence.json).
New [decompilations](../artifacts/world-input/cadence/export/references.txt)
come from the existing Ghidra project opened read-only without analysis.

## Cursor ownership and message routing

1. AncientApp initialization at `4ee4dd…4ee52b` creates BaseSystem at
   `app+0xd70`, assigns vtable `0x59b5e4`, calls its Init and activates it
   through `540da0`. Activation appends a record with state 1, this system
   pointer and child-vector pointer to the application's system vector.
2. `System::Init` (`541810`) allocates its object vector at system+0x10,
   then invokes virtual slot +0x14 at `541875`. BaseSystem's slot contains
   `BaseSystemTy::CreateSystemObject` (`4efe60`, named by its diagnostic string).
3. That routine calls virtual +0x10 with `(1,1)` and `(0x100,1)`.
   The short wrapper `541c90` forwards to virtual +8 (`541ba0`).
   `541ba0 → 541ad0 → 53ffc0` creates and initializes the object. The factory
   record at `5c0d98` is `(0x100,0x515ad0)`, the cursor constructor.
   `541ad0` writes object+0x0c = this system and inserts it into system+0x10.
4. BaseSystem's vtable +0x1c is `542320` (`SystemClassTy::Life`), not Play Life.
   Each `App` iteration `541520` invokes `5413c0`, which visits active systems'
   +0x1c slots and their active child systems. Generic Life clears a 32-byte
   message and calls `542200` (`GetToAllObjects`) with message+0x10 = 0.
5. That broadcaster calls each object's vtable slot 0. The cursor table
   `59b808` points to `518d90`; its case 0 calls `517540(1,-1,-1)`.
   This is separate from PlaySystem's accepted simulation-step counter.

The existing [ship clock evidence](SHIP_MOVEMENT_CLOCK_EVIDENCE.md) describes
Play `51fdb0` gating its own `System::Life` call. That gate does not wrap the
BaseSystem call. This note does not establish the relative ordering of all
active system registrations during a complete loaded mission.

## RunApp pacing

`AppClassTy::RunApp` (`541600`) processes Win32 messages when present. On the
normal idle branch it computes, using cached app+0x18 and current `timeGetTime`:

```text
remaining = cachedTime + appPeriod - now
if remaining > 0 and urgentQueue(app+0x2c).count == 0:
    virtual Wait(remaining)
if remaining >= 0 or remaining <= -(appPeriod / 2):
    adjustment = 0
else:
    adjustment = remaining
cachedTime = timeGetTime() + adjustment
one application iteration 541520
```

AncientApp's virtual Wait is `4ee8f0 → 5415e0 → KERNEL32!Sleep` (IAT `594158`).
The shared cached-time getter is `5417d0`; `WINMM!timeGetTime` is IAT `5942d8`.
There is no catch-up loop inside this application-iteration branch.

The base App constructor `53fcf0`, instruction `53fd2a`, initially writes
**20 ms** to app+0x34. Gameplay configuration `4ed410` reads SPEED_GAME and
writes the second dword of the selected record at `5bed74 + index*24`.
For index 5, both world quantum and app period are 40 ms. Default game-speed
variable 5 comes from `5016a0`; configuration/save choices remain inputs.
Therefore 40 ms here means the prepared gameplay speed-5 context, not a
universal startup/menu constant.

An urgent queued application message skips Sleep, while still performing a
Life iteration. Lateness correction can also alter exact spacing. The source
supports a separate normal 40 ms application/UI pacing gate; it does not prove
that copying Play's SingleStepClock arithmetic reproduces all of RunApp.
Immediate mouse Move also invokes the cursor drawing path directly and must
remain distinct from periodic message 0.

## Confirmation animation consequence and limits

The source TAKE_CMD terminal-frame cleanup happens on its next actual cursor
draw transaction. Running periodic Cursor Life every Unity render frame can
make that next transaction earlier than the prepared original quiet loop.
Its animation interval and terminal-frame rules remain independently proven
in [SHIP_POINTER_VISUAL_EVIDENCE.md](SHIP_POINTER_VISUAL_EVIDENCE.md).

This work inspected source routing and recorded exact binary ranges. It did
not execute the complete application loop, emulate Win32 timing or urgent
queue traffic, change C#, start Unity/Wine/services, or claim full application
scheduler parity. Normal UI pacing is independent of whether ShipLife accepts
a world step; the world counter must not be used as the cursor-Life clock.
