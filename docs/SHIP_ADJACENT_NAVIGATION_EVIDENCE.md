# Źródłowe planowanie ośmiu sąsiednich kierunków

Stan: 2026-11-02. `ShipAdjacentQuery` odtwarza konkretny predykat komórki
`0x499aa0`. `ShipAdjacentPlanner` wydziela osobno zamkniętą początkową gałąź
dla `OBJ_0000000b`, `(16,2)`, heading5, restriction0 i ośmiu referencyjnych
statków na mapie 24×24. Nie jest to ogólny pathfinder ani port całego Life.
Istniejące `PreparedShipMovement` i wcześniejsze fixture pozostały bez zmian.

Oryginał `ancient.exe`, SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`,
oraz `miss000.dkx/dkd` są chronione pełnymi SHA przed wykonaniem.
Boot ID `02fd04eb-5227-4429-806a-a173a569004f` i marker
`root-new-environment-cb830790-marker-20261102` ponownie potwierdzono.
Nie zapisywano do oryginałów, nie uruchamiano Unity/Wine/Xvfb w tym dowodzie.

## Wynik rzeczywistego planera

Oracle wykonuje źródłowe `ShipClassTy::ProcPostMove` `0x4a6330`,
`ShipClassTy::GetWayNew` `0x4a5740` oraz `0x55c9a0` na rzeczywistych flagach
misji. Nazwy dwóch pierwszych funkcji pochodzą z napisów błędów w EXE.
Konstruktor/LoadDateBase dostarczają pól source0b, a siedem pozostałych
statków to jawne referencyjne tożsamości i komórki; nie wykonuje się ich AI.

| Heading / kierunek | Cel | Flagi celu | Path | Stan / center po planie |
| --- | --- | --- | --- | --- |
| 0 / E | 17,2 | `0x1` | 2 punkty | 2 / 0 |
| 1 / NE | 17,1 | `0x1` | 2 punkty | 2 / 0 |
| 2 / N | 16,1 | `0x8` | brak | 0 / 0 |
| 3 / NW | 15,1 | `0x308` | brak | 0 / 0 |
| 4 / W | 15,2 | `0x1` | 2 punkty | 2 / 0 |
| 5 / SW | 15,3 | `0x7` | 2 punkty | 3 / 1 |
| 6 / S | 16,3 | `0x7` | 2 punkty | 2 / 0 |
| 7 / SE | 17,3 | `0x1` | 2 punkty | 2 / 0 |

Każda udana ścieżka zawiera dokładnie `[[16,2,h],[goalX,goalY,h]]`,
z indeksowaniem bieżącego punktu 1. W pięciobajtowym rekordzie są dwa
int16 little-endian i bajt heading. Heading pierwszego punktu opisuje
kierunek odcinka, **nie** bieżącą orientację kadłuba, która nadal wynosi 5.
Stan 2 rozpoczyna obrót; SW zachowuje zgodny kierunek i rozpoczyna stan 3.
Sam planner nie wykonuje obrotu ani przesunięcia.

**Niski bajt wyniku `0x4a6330` wynosi 0 we wszystkich ośmiu przypadkach**,
również przy sześciu sukcesach. O powodzeniu świadczy zainstalowany bufor
ścieżki/count2. Nie wolno mapować `EAX != 0` na powodzenie planowania.

Trwały fixture: `tests/fixtures/ship_adjacent_planner.json`, SHA256
`73295e933946ffab36abb7282f4b51c280995f6a85aa29c37e448dffd3cf3c0a`.
Zawiera oryginalne hashe, 3×3 flagi, osiem komórek floty, binarne rekordy
ścieżek i ich rzeczywiste wyniki. Flag2304B ma SHA
`eb8c22b2dc3a3d6de5be5c5a28560701333cbc8610e8dd687052f4f93b260283`.

## Dokładny predykat `0x499aa0`

Pola komórki źródłowej to flags `grid+8+index*24` i pojedynczy owner
`grid+12+index*24`. Najpierw predykat sprawdza tylko flagi **celu**:
low nibble < 8, upper nibble różny od 4/5/6, a przy niezerowym restriction
także różny od 3. `0x499990(index,restriction)` i
`0x4999e0(x,y,restriction)` są równoległymi flagqueries, nie callees
`0x499aa0`. Predykat powiela ich warunki.

Następnie target owner musi być zerowy albo identyczny z requesterem.
Równe ID, wartości `Equals`, side czy player nie zastępują pointer identity.
Dla heading parzystego jest to koniec predykatu. Dla heading nieparzystego
sprawdzane są dwa rogi, w następującej kolejności:

| Heading | Róg A względem celu | Róg B względem celu |
| --- | --- | --- |
| 1 / NE | x−1,y | x,y+1 |
| 3 / NW | x,y+1 | x+1,y |
| 5 / SW | x+1,y | x,y−1 |
| 7 / SE | x,y−1 | x−1,y |

Jeśli jeden z tych rogów wychodzi poza mapę, źródło zwraca true po
wcześniejszych bramkach celu. Dla ważnego targetu i heading0…7 odtworzono
te wczesne powroty. Flagi terenu bocznych komórek **nie są sprawdzane**.
Dlatego NE jest rzeczywiście planowany mimo niedostępnej północnej
komórki `(16,1)`. Nie dodano konwencjonalnego zakazu corner cutting.

Wyjątek blokujący jest asymetryczny i dotyczy wyłącznie ownera rogu A:

1. Kategoria zwrócona przez rzeczywiste `0x50e590` wynosi 200,
   co dla tej klasy oznacza runtime tag 200…211.
2. `owner+0x58c` ma stan 6, a `owner+0x8e6` wskazuje rekord.
3. Pierwszy dword rekordu ma literalnie 200.
4. Wskaźnik celu linku znajduje się pod niewyrównanym `record+5`.
   Jego `cellY*width+cellX` jest indeksem rogu B.

Spełnienie tych warunków daje false nawet przy pustym B albo gdy A jest
samym requesterem. Klasa obiektu wskazanego przez link nie jest sprawdzana.
Link wyłącznie w rogu B jest ignorowany. Na końcu predykat odrzuca dwa
niezerowe **identyczne** pointery w A i B; dwa różne foreign ownery są
dopuszczane. Źródło nie stosuje prostego warunku „oba rogi puste”.

## API C# i granice kontekstu

`AncientConquest.Simulation.ShipNavigationOccupant` jest readonly projekcją
sześciu wartości: RuntimeClassTag, MovementState, HasLink, LinkRecordType,
LinkedCellX/Y. Nie tworzy źródłowych obiektów ani linków.

```csharp
ShipAdjacentQuery.CanEnter(grid, requester, targetX, targetY,
                          heading, restriction, describeOccupant)
```

Resolver `Func<object,ShipNavigationOccupant>` odczytywany jest tylko dla
niepustego A, po bramkach flags/target/even/boundary. `ReferenceEquals`
zachowuje tożsamość. Wyliczanie indeksu linked cell jest unchecked tak jak
x86. API odrzuca null dependencies, heading spoza0…7 i invalid target
przez wyjątek; to polityka adaptera, nie odtworzenie niebezpiecznych
odczytów źródła. Wadliwy natywny wskaźnik link target nie ma źródłowego
nullguard i pozostaje poza dziedziną projekcji wartości.

```csharp
ShipAdjacentPlanner.TryPlan(grid, owner, originX, originY, heading,
                            goalX, goalY, restriction, out ShipAdjacentPlan plan)
```

Planner waliduje `(16,2)`, heading5, restriction0, map24×24, dokładnie
lokalne dziewięć flag, osiem distinct owner identities we właściwych
source cells i brak dodatkowych claimów. Wtedy wszystkie rogi celów są
puste; jego throwing resolver nie zgaduje metadanych zajętej komórki.
N/NW zwracają false i pusty plan. Inne konteksty dają jawny wyjątek
unsupported. To ograniczenie zamkniętego adaptera.

`ShipAdjacentPlan` udostępnia OriginX/Y, TargetX/Y, TargetHeading,
InitialState, CenterGate, PathIndex/PathCount i `CapturePoints()` zwracające
niezależną kopię10B. Po failed plan out nie zachowuje poprzedniej ścieżki.
Odczyt planu nie zmienia żadnego ownera ani flags w gridzie.

Pełny generic planner jest możliwym kolejnym etapem analizy, lecz obejmuje
dodatkowe źródłowe procedury: `0x571880` wybiera/sprawdza segmenty,
`0x5578a0` jest fallback map propagation, `0x4a4e20` modyfikuje lokalną
mapę7×7 zależnie od obiektów, grup, stanów, route priority i RNG.
Ma także osobne mapy restriction i link/shore cases. Nie zastąpiono tego
przez wymyślone A* ani nie nazwano ograniczonego adaptera pełnym portem.
Udany sąsiedni przypadek oryginału używa sprawdzonej krótkiej gałęzi
dwupunktowej; mapa i fleet są tu jawną granicą dowodu.

## Walidacja i odtwarzanie

- `tools/validate_ship_adjacent_query.py`: **7120/7120 actual x86/C#**,
  bez hooków w native queries, z `/checked+` i **23 kontrolami kontraktu**.
  Obejmuje 48 source-neighbor variants, 2304 flag/owner/restriction,
  64 corner identities, 28 corner-terrain, 68 linked-state i 4608
  valid-target/boundary. Sprawdzono także niezmienność gridów po odczycie.
- `tools/validate_ship_adjacent_planner.py`: **8/8 actual native planner/C#**,
  sześć route i dwie source failures oraz **18 kontroli kontraktu**.
  Testowane są clone/metadane, usunięcie starego out, pointer identities
  pomimo równych `Equals`, brak mutation grid i jawne unsupported contexts.
- Oba nowe unittest przeszły. Systemowy Python bez opcjonalnych pefile/
  unicorn prawidłowo je pomija, bez błędu importu.
- Niezależny read-only review query/plannera nie znalazł rozbieżności
  w zadeklarowanym zamkniętym zakresie. C# zamrożono przed buildem roota.

Raporty:
`artifacts/navigation/query-review/csharp-validation.json` i
`artifacts/navigation/adjacent/csharp-validation.json`.
Query fixture `ship_adjacent_query.json` ma SHA
`98cefc9c6544f52e929943ad22fe511b5abac23a7f5e1332ffa18b76ed761d3e`.
Query C# ma SHA `cefdc73085476fd738a55b2feed8c8586cc1b741bcc1cdaff2a5f7b5b3278721`,
planner C# `0849f2906628c2023283f405ed8dd5c6ca09988c65ceea82bbcd3959597f5b76`.

```sh
.venv/bin/python tools/validate_ship_adjacent_query.py --output artifacts/navigation/query-review/fresh.json
.venv/bin/python tools/validate_ship_adjacent_planner.py --output artifacts/navigation/adjacent/fresh.json
.venv/bin/python -m unittest tests.test_ship_adjacent_query tests.test_ship_adjacent_planner -v
```

Query nie przechwytuje żadnej procedury. Planner wykonuje całą ścieżkę
`0x4a6330→0x4a5740→0x55c9a0`; jawne granice przygotowania to normalny
setjmp, pochodna inicjalizacja/komunikaty oraz bounded heap. Użyto
źródłowego passability-map prefix `0x49a950…0x49a9cd`, bez hooków.
Native early failure bezpośredniego entry pozostawia wskaźnik exception
chain powiązany ze stosem; oracle zapisuje to i nie wykonuje potem ruchu
w takim przypadku. Sukces musi odtworzyć chain. Nie modyfikuje się
oryginału, aby ukryć tę różnicę bezpośredniego wywołania.

Plan jest wywoływany przy jawnym source counter1. Oddzielny
[dowód ruchu](SHIP_ADJACENT_MOVEMENT_EVIDENCE.md) zaczyna MoveShip przy2.
To nie dowód pełnego globalnego Life: źródłowe `0x4ab930` może po
`0x4a5f30` wywołać MoveShip w tym samym counter przy swoich bramkach.
Flagi i granice publikacji opisuje też
[niezależny dowód świata](SHIP_ADJACENT_WORLD_EVIDENCE.md).
Unity driver, player/build/QA, Windows11 i docelowy laptop wymagają
osobnych wyników. Ta dokumentacja nie przewiduje ich rezultatu.
