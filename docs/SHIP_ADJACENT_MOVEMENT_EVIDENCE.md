# Osiem sąsiednich celów statku0b

Nowy `ShipAdjacentMovement` odtwarza obrót i ruch statku `OBJ_0000000b`
z `(16,2)`, kierunek5, do ośmiu sąsiednich pól. W oryginalnej mapie
**sześć celów dopuszcza ruch, a północ i północny zachód są nieprzejezdne**.
To zachowanie oryginalnych procedur, potwierdzone wykonaniem x86;
nie zmieniono flag mapy, żeby umożliwić wszystkie osiem przejazdów.

Rzeczywisty C# z `/checked+` zgadza się z **1271/1271 stanów** z38 śladów:
1233 wywołań całego `MoveShip`,38 oryginalnych planowań i587 publikacji
sprite. Dodatkowo probe sprawdza42 kontrakty adaptera. Poprzedni
`PreparedShipMovement` i jego fixture pozostają bez zmian.

Dowody:

- [Zamrożony fixture x86](../tests/fixtures/ship_adjacent_movement.json),1651816 bajtów,
  SHA-256 `2ffc6d70e131770dc065b252e88818e02aca203f681ea1ff373875883f8e9075`.
- [Raport C#/x86](../artifacts/adjacent/kinematics/ship-adjacent-csharp-validation.json),
  [pełny natywny wynik](../artifacts/adjacent/kinematics/native-ship-adjacent.json).
- [Oryginalny oracle](../tools/probe_ship_adjacent.py),
  [walidator](../tools/validate_ship_adjacent_movement.py),
  [probe C#](../tests/fixtures/ShipAdjacentMovementProbe.cs),
  [testy](../tests/test_ship_adjacent_movement.py).
- [Nowy rdzeń](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipAdjacentMovement.cs),
  [plan](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipAdjacentPlanner.cs),
  [predykat](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipAdjacentQuery.cs),
  [obrót](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipTurnProgression.cs).

## Jawne warunki i planowanie

Zachowano oryginalny payload0b, pełne zdrowie, zerowe wyposażenie dodatkowe,
poziom ulepszenia0, logiczny sprite56×56 i ośmiu różnych właścicieli
na źródłowych pozycjach floty. Siedem pozostałych statków jest nieruchomymi,
minimalnymi obiektami zajętości. Ich pełna inicjalizacja i AI nie działają.
Wiatr `(siła0,kierunek5)` jest jawnym warunkiem referencyjnym, a nie
deklaracją domyślnej pogody każdej nowej misji. Dla modelu0 daje60%
oryginalnej tabeli: limit36000 i przyspieszenie720.

Oracle uruchamia oryginalny konstruktor, `LoadDateBase`, wyliczenie
prędkości `004bece0`, prefiks budowy576 pól mapy przejścia
`0049a950..0049a9ce`, następnie oryginalne
`004a6330→004a5740→0055c9a0`. Każdy dopuszczony cel zwraca dwie rekordy
po5 bajtów: `(int16LE x,int16LE y,byte heading)`. Pierwszy jest początkiem,
drugi celem; oba mają docelowy kierunek. To źródłowy wynik, nie własny A*.
Adapter C# ma zamkniętą projekcję tej konkretnej gałęzi i jawnie odrzuca
inne mapy, pozycje i cele.

Planner wykonuje się przy source counter1, a kolejne wywołania ruchu przy
counter2,3,... . Jest to **jawny harmonogram diagnostyczny**. Nie twierdzimy,
że odtwarza cały `Life`: oryginalny caller może planować i uruchomić
`MoveShip` w tym samym counter. `sprite+81` zaczyna od0, interwał animacji
wynosi2. Nie ustawiano sztucznego `ship+57b=-1`, żeby ominąć oryginalną
blokadę ponownego planowania w tym samym counter.

| Kierunek | Cel | Flagi źródłowe | Wynik |
| --- | --- | --- | --- |
| 0, E | 17,2 | `0x1` | trasa2 rekordy, obrót |
| 1, NE | 17,1 | `0x1` | trasa2 rekordy, obrót |
| 2, N | 16,1 | `0x8` | odmowa, bez trasy i ruchu |
| 3, NW | 15,1 | `0x308` | odmowa, bez trasy i ruchu |
| 4, W | 15,2 | `0x1` | trasa2 rekordy, obrót |
| 5, SW | 15,3 | `0x7` | trasa2 rekordy, kierunek już zgodny |
| 6, S | 16,3 | `0x7` | trasa2 rekordy, obrót |
| 7, SE | 17,3 | `0x1` | trasa2 rekordy, obrót |

NE działa mimo nieprzejezdnego terenu na północnym polu bocznym.
`00499aa0` nie wymaga przejezdnego terenu obu boków diagonali. Bada
zajętość celu, tożsamość właścicieli boków i szczególny przypadek
sprzężonego statku state6. Tego predykatu nie zastąpiono regułą
„oba pola boczne muszą być puste/przejezdne”. Gdy podczas ruchu pojawi się
nieznany zajęty narożnik, rdzeń jawnie odmawia projekcji jego metadanych;
nie zgaduje stanu/class/link. Początkowa flota nie zajmuje żadnego z boków.

N i NW mają pusty path/count0, a źródłowa funkcja zwraca EAXlow0.
Ten sam EAXlow0 występuje przy sukcesie, więc wynikiem planowania jest
zainstalowana trasa, nie bool wyprowadzony z EAX. Przy bezpośrednim
odrzuconym wywołaniu natywny planner pozostawia swój lokalny łańcuch
setjmp; stan ten zapisano w fixture, ale mechanizmu wyjątków nie przenosi
się do C#. Dla takiego przypadku oracle nie wykonuje dalszego `MoveShip`.

## Obrót oraz publikowanie obrazu

Planner ustawia `targetHeading+5b1`, `pathIndex+5be=1`, `pathCount+5ba=2`.
Dla nowego kierunku: `state+58c=2`, `centerGate+596=0`, `turnStep+5b0=0`.
Dla SW: state3 i centerGate1. Frame w obu przypadkach nadal wynosi20.

`004a3320`, `ShipsStopMove`, korzysta z `004b5390`: wybiera znak obrotu,
przechodzi na24-pozycyjny pierścień klatek32..55 i aktualizuje go tylko
przy ścisłym unsigned `now-lastTick >2`. Nowy heading to `(frame-32)/3`.
Wyrównanie do docelowego headingu następuje dopiero na pełnej pozycji
tego pierścienia; wtedy zapisuje `frame=heading*4`, state3 i centerGate1.

**Cały ten call kończy się bez ruchu**, również gdy zakończono obrót.
Oryginalne `004a3320` zwraca0 i caller natychmiast wraca. Rezerwacja
i forward-tail następują dopiero w następnym call. Nie ma tu dowolnego
Unity interpolation ani obrotu modeli w czasie rzeczywistym.
[Osobny dowód helpera obrotu](SHIP_TURN_ANIMATION_EVIDENCE.md) obejmuje
także inne headingi i brzegowe wejścia.

W pierwszym kroku obrotu, counter2, frame zmienia się20→47 bez publikacji;
na ekranie nadal pozostaje klatka20. Pierwsza publikacja następuje przy
counter3, w drugim call. Rdzeń osobno przechowuje `StoredFrame`,
`DrawnFrame` i `PublishedWorldX/Y`. Wywołujący publikuje jedynie ostatnią
parę potwierdzoną natywnym `0050d5f0`; sam wzrost fazy nie oznacza nowego
obrazu. W obrocie publikację wywołuje helper, a podczas ruchu rzeczywista
zmiana pozycji, po forward-tail. To rozszerza zachowaną
[granicę publikacji poprzedniego odcinka](SHIP_MOVEMENT_EVIDENCE.md).

## Kinematyka i zajętość

Natywny `004a3f40` wykonuje w każdym kroku arytmetykę32-bitową ze znakiem.
Po aktualizacji i ograniczeniu prędkości:

```text
total = pending*speed + remainder
q = total / 3000
remainder = total % 3000
```

Dla osi ruch przesuwa o `q/2` piksela i zachowuje `(q%2)*3000` w reszcie;
dla diagonali używa `q/3` i `(q%3)*3000`. Wektory kierunków są odczytane
z `005c4f44`: `(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1),(0,1),(1,1)`.
Docelowa kotwica to `(goalX*64+4,goalY*64+4)`. Wszystkie kierunki są
porównane przez osiągalne źródłowe trasy; dla zablokowanych N/NW nie
twierdzimy, że wykonano ruch na zmienionej mapie.

Cel jest rezerwowany przez `004a3a70→00499830` przed pierwszą zmianą
piksela. Origin pozostaje zajęty. Transfer wykorzystuje środek sprite
**sprzed** aktualizacji świata: `(oldWorld+28)/64`. Dopiero wejście tego
środka w komórkę celu zwalnia64, zmienia logical CellX/Y i rozpoczyna
hamowanie4. To powoduje źródłową asymetrię czasów diagonali. Dokładne
dojście do kotwicy kończy state0/speed0/turnStep1.

Poniższe wartości to numery wywołań, przy pending1; source counter jest
zawsze o1 większy.

| Cel | Koniec obrotu | Rezerwacja | Pierwszy piksel | Transfer origin | Dokładny cel |
| --- | --- | --- | --- | --- | --- |
| E | 26 | 27 | 30 | 50 | 61 |
| NE | 35 | 36 | 40 | 65 | 79 |
| W | 8 | 9 | 12 | 32 | 43 |
| SW | już wyrównany | 1 | 5 | 30 | 44 |
| S | 8 | 9 | 12 | 32 | 43 |
| SE | 17 | 18 | 22 | 46 | 62 |

Zajętość wynosi8 przed rezerwacją,9 między rezerwacją a transferem i8
po transferze. To referencje ownerów; ID0 nie jest pustym polem. Probe
używa ośmiu różnych obiektów o równych ID0, aby sprawdzić tę zasadę.
Po ruchu nowy równy owner nie może uwolnić komórki poprzedniego ownera.

## Zakres porównania i API

32 ślady obejmują osiem celów i pending1/2/3/7:24 dojazdy i8 odrzuceń.
Sześć dodatkowych kontroli najpierw wykonuje udany planner, następnie
umieszcza obcego właściciela na celu. Obrót nadal działa, ale rezerwacja
i przesunięcie nie następują. Gdy `counter-lastStateCounter >49`, state3
przechodzi0; własna komórka64 i cudza rezerwacja pozostają nietknięte.
Przykładowo NE kończy kontrolę przy counter86 po ostatnim obrocie36,
bez opuszczenia `(1028,132)`. Jest to kontrolowana zmiana zajętości,
nie twierdzenie, że wykonano AI lub ruch drugiego statku.

Każdy z1271 stanów porównuje plan/pozycję/path, heading/target/turnStep,
state/center, prędkość/resztę/hamowanie, rezerwacje, wszystkie liczniki,
fazę, opublikowaną klatkę/pozycję, forward-tail, publikację oraz dokładne
komórki i całkowitą zajętość. Hooki nie zastępują plannerów, obrotu,
matematyki ani grid. Ich lista jest jawna: normalny setjmp, pamięć,
publikacja renderera, widoczność i powiadomienia systemowe.

Publiczne API:

```csharp
var movement = new ShipAdjacentMovement(grid, owner, source0b);
bool accepted = movement.TryBeginAdjacentReferenceMove(goalX, goalY, plannerCounter: 1);
movement.Step(pendingSteps: 1, sourceCounter: 2); // tylko po accepted
ShipAdjacentMovement.Snapshot state = movement.Current;
```

`Step` sam prowadzi obie fazy animacji; zewnętrzny driver nie wywołuje
ponownie `AdvanceForward`. `LastStepPublishesPose` steruje publikacją,
`LastStepReachedForwardTail` służy dowodom i diagnostyce. `IsComplete`
wymaga dokładnej pozycji i komórki celu; samo state0 po timeout nie jest
dojazdem. `IsStopped` zamraża zakończoną diagnozę przed idle RNG.
Wymaganie kolejnych counterów, wyjątki po utracie ownera i ograniczenie
pending do zweryfikowanych1/2/3/7 są zasadami adaptera, a nie deklaracją
identycznych wyjątków oryginalnego C++.

Core SHA-256: `b9c8fe2c2b062b6dc2281fd4f2225ae6ee3a759f94ef2502597a392383f2c55f`.
Źródłowe EXE i miss000 są tylko odczytywane oraz sprawdzane hashami
przed wykonaniem i po porównaniu. Nie zmieniono starego odcinka SW ani
jego fixture. Ten dowód nie uruchamia Unity, Wine, usług ani Windows11;
integrację playera, obraz1920×1080 i cleanup sprawdza odrębny etap.
Pełne Life, swobodne rozkazy, dalsze trasy, pathfinding całej mapy,
dynamiczne połączenia statków, AI, walka i pogoda pozostają poza zakresem.
