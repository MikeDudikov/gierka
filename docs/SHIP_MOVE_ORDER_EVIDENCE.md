# Normal MOVE order coordinator evidence

This stage projects the healthy source `OBJ_0000000b` request, promotion, normal work and movement chain. The source actor starts at cell `(16,2)`, heading5, at full health, with controlled wind force0/heading5, owner upgrade0 and seven stationary fleet peers. It is separate from the historical initial-route and adjacent-route diagnostics.

The source executable remains read-only. Its SHA-256 is `cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`. Fresh proof and final checked-C# results are recorded under `artifacts/order-cycle/lifecycle/`. The canonical native fixture is [ship_move_order.json](../tests/fixtures/ship_move_order.json), SHA-256 `5a11bf625ea6d3a5a4f7b3e6d037b2eafb348eb1f5c7a9b5075e62586a3409ac`.

## Source chain and schedule

The bounded counter input begins at0. The first explicit tick at1 invokes `ProcShipsAppMessage` (`004ab720`), then `ProcShipsWork` (`004ab930`) at the same source counter. The latter calls normal move work (`004a5f30`), planning/rechecking (`004a6330`/`004a6150`) and `MoveShip` (`004a3f40`) without an artificial extra movement tick. The outer application loop, real-time game cadence, full `Life`, damage, combat, AI, linked actors and equipment work are excluded.

A cell-move request is the original `GetMessage` message `0x280f`, action20, and dispatcher opcode `0x80`. The pending26-byte record resides at actor+`858`; the pending mask is+`7d6`. Promotion `004ab250` copies the target to+`54e/552`, clears the retry snapshot, sets `firstNavigation`+`593`, resets retry+`591`, sets the planning interval+`57f` to25 and sets active bit`80` at+`25d`.

Normal `ProcShipsWork` also retains active bit`400`, including after move bit`80` clears. `MoveShip` therefore continues through its original idle branch. Idle updates the same actor RNG at+`18` on every idle call. The initial RNG is exactly `unchecked(sessionSeed * instanceId)`, so the controlled sessionSeed0 gives this actor RNG0; this is not asserted as the full mission default. Idle publication can differ from the stored animation phase. See [SHIP_IDLE_ANIMATION_EVIDENCE.md](SHIP_IDLE_ANIMATION_EVIDENCE.md).

## Mutable navigation transaction

`ShipReplanPlanner` owns the source map/route algorithms and returns owned raw5-byte records. `ShipMoveOrder` owns the source stamps, retry state, route replacement and live physics. The source plan origin is the current cell with center gate0, or the reserved next cell with center gate1. A moving replacement with center gate1 prepends the current cell and physical heading to the raw route; the next record's heading is retained exactly even when it is not the incoming heading from that prepended cell.

The source blocker cache at+`5cd` is ordered and persists across planning operations. For example, the initial local window discovers occupied cell115 `(19,4)`; later windows may discover additional static owners. Cached cells are reapplied outside the new local window. A normal moving stop can clear this cache; a stop from state0/2/3 does not necessarily do so. The shared planner RNG also advances on source retries greater than50. See [SHIP_REPLAN_PLANNER_EVIDENCE.md](SHIP_REPLAN_PLANNER_EVIDENCE.md).

The source recheck gate requires25 counter steps since the last actual plan, excludes turning state2 and compares the cached retry/current-cell/target snapshot. Logical current-cell equality can queue pending stop bit8 before the sprite reaches its exact pixel anchor. `004aa540` consumes that stop at the following promotion pass, clears active bit80 and asks `ProcPostMove(mode1)` to stop physical navigation. State1 then follows the original braking/truncation helper `004a38f0`.

## Completion and operation effects

Path endpoint, requested target and active-bit clearance are different observations. `Current.Motion.IsComplete` means the current installed path endpoint has been reached in state0 at its exact sprite anchor. `RequestedTargetReached` separately compares state0/cell/pixel anchor with the active requested target. A nearest path ending at `(17,2)` for requested `(18,2)` must not be reported as reaching `(18,2)`.

`CanRequestMove` is the supported adapter boundary: physical state0, move bit80 clear, and neither pending move80 nor pending stop8. It excludes busy replacement. A request in the current cell is retained as source behavior; it is not converted into synthetic immediate completion. Adjacent blocked requests can leave `firstNavigation` set and repeat the first-planning branch on every tick while the actor idles.

Each request and tick is a separate operation. A request clears that operation's publication/grid-write/forward-tail effects, retaining the last visible pose, stored phase, timestamps and RNG. This prevents a second request made at the same source counter as an idle publication from applying that old publication twice. The native trace uses a separate monotonically increasing sample index and records the operation type; source counters can repeat across a tick and following request.

The coordinator returns every source pose publication in order. The presentation layer applies every corresponding depth update so that the known cohort's ordering history is preserved. No renderer publication is inferred merely from a stored animation phase change.

## Validation status

[csharp-validation-final.json](../artifacts/order-cycle/lifecycle/csharp-validation-final.json) records a fresh native replay equal to the pinned fixture, followed by actual C# compilation with `/checked+` and full differential comparison. All65 snapshot columns match across7 cases,956 samples (7 initial,8 request and941 tick operations),446 ordered publications and62 ordered ownership-grid writes. The35 API/identity/effect guards pass. The maximum observed publications per operation is2; the API rejects an unsupported overflow rather than truncating it. Historical movement/adjacent/route adapters and their fixtures remain unchanged.

| Case | Tick calls | Outcome at final sample |
| --- | ---: | --- |
| `(18,5)`, sessionSeed0 | 101 | Exact requested anchor, active80 clear, first idle publication |
| `(20,4)`, sessionSeed0 | 122 | Exact requested anchor, active80 clear, first idle publication |
| Requested `(18,2)` | 180 | Observation bound; path ends `(17,2)`, move80 remains active |
| Blocked adjacent `(16,1)` | 180 | Observation bound; no route, firstNavigation remains1, original idle runs |
| `(18,5)` then `(16,4)` after readiness and idle publication | 197 | Both requested anchors reached in sequence; no busy replacement |
| `(18,5)`, sessionSeed`FFFFFFFF` | 103 | Exact requested anchor; source RNG/wrap preserved |
| `(18,5)`, pendingSteps3 | 58 | Exact requested anchor with the declared source pending-step input |

The `(20,4)` source case demonstrates the completion distinction: stop is queued at counter102 while state4 is still at `(1267,243)`; counter103 clears active80 while state4 remains at `(1270,246)` and clears the cached blocker list. A consumer must not treat that flag change alone as exact physical arrival or next-command readiness. The `(18,5)` case reaches state0 at87, queues stop98, clears active80 at99 and publishes its first idle pose at101. The second request is issued immediately after this idle publication as sample103 at the same source counter101; it has no new publications.

The new [ShipMoveOrder.cs](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipMoveOrder.cs) SHA-256 is `caa73d42265622175b3b9d44c4125972beae0d682c768d8ca263dbc1b9561cd9`. The native probe SHA-256 is `88f41138618240c905d403c73348633cb5976d041a056b198da3f5fdecfdd1c1`. The raw planner and idle integrations also received independent read-only source reviews; no supported-branch discrepancy was found. [native-consistency-verification.json](../artifacts/order-cycle/lifecycle/native-consistency-verification.json) separately verifies fresh native equality, source hashes,956 operation indices,5777 recorded source-entry events, request counter preservation, same-counter promotion/work/motion, the second-request readiness boundary, all446 publication commits and62 grid writes.

No Windows11, user input, completed full mission or hardware performance test is implied by this pure simulation proof. The180-tick blocked/nearest observations do not establish full retry exhaustion. Busy replacement and the full actor/application loop remain excluded.
