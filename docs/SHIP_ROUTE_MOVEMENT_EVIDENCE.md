# Wielopunktowe trasy źródłowego statku0b

`ShipRouteMovement` rozszerza sprawdzony odcinek sąsiedni o dłuższe trasy,
lookahead zajętości, kontynuację przez waypointy i zmiany kierunku przy
zachowanej prędkości. Rzeczywisty pipeline C# `ShipRoutePlanner→MoveShip`
zgadza się z **1593/1593 stanów** z32 śladów x86:1561 wywołań całego
`004a3f40`,1046 uporządkowanych publikacji obrazu i248 uporządkowanych
zapisów zajętości. Probe kompilowany z `/checked+` sprawdza57 kontraktów API.
Stary `ShipAdjacentMovement` i jego dowody pozostają bez zmian.

Dowody:

- [Fixture](../tests/fixtures/ship_route_movement.json),2733018 bajtów,
  SHA-256 `d6252388d37891b24f9a271015cdce9ba931ddad9228c8f7eae4ec832fcfeefc`.
- [Raport różnicowy](../artifacts/long-routes/kinematics/ship-route-csharp-validation.json),
  [pełny wynik x86](../artifacts/long-routes/kinematics/native-ship-route.json).
- [Oracle](../tools/probe_ship_route_movement.py),
  [walidator](../tools/validate_ship_route_movement.py),
  [probe C#](../tests/fixtures/ShipRouteMovementProbe.cs),
  [testy](../tests/test_ship_route_movement.py).
- [ShipRouteMovement](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipRouteMovement.cs),
  [ShipRoutePlan](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipRoutePlan.cs),
  [ShipRoutePlanner](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipRoutePlanner.cs).
- [Niezależny audyt gałęzi](../artifacts/routes/motion-review/MULTI_WAYPOINT_BRANCH_AUDIT.md),
  [review gotowego rdzenia](../artifacts/routes/motion-review/core-review.json).

## Zakres i dane wejściowe

Warunki są jawne:0b z `(16,2)`, heading5, pełne zdrowie, poziom ulepszeń0,
wiatr0/5, logiczny sprite56×56, zerowe dodatkowe rozkazy i osiem różnych
ownerów na źródłowych polach floty. Pozostałych siedem obiektów to minimalna
statyczna reprezentacja użyta również w oracle planowania: źródłowy tag
klasy, ID i pozycja; pozostałe pola są zerowe, w tym stan/grupa/link.
Nie twierdzimy, że wykonano pełne konstruktory lub AI tych siedmiu statków.
To odrębny warunek od rzeczywistego początkowego świata z wszystkimi klasami.

Native wykonuje źródłowy ctor/LoadDateBase statku0b, wyliczenie prędkości,
576 pól mapy, `004a6330→004a5740→0055c9a0` i całe kolejne wywołania
`004a3f40`, wraz z helperami obrotu, rezerwacji i hamowania. Jawne granice
obejmują jedynie normalny setjmp, pamięć, publikację renderera, widoczność
i powiadomienia systemowe. Oryginał jest tylko odczytywany; EXE, miss000
i zamrożone flagi mają sprawdzane SHA-256 przed i po porównaniu.

Harmonogram diagnostyczny pozostaje: planner przy counter1, następnie
MoveShip przy2,3,... . Nie jest to port pełnego `Life`: oryginalny caller
może planować i poruszać statek w jednym counter. Nie odtwarzamy też
ogólnego retry rozkazów. Przykładowo rzeczywisty Work może dla celu18,2
zaproponować częściowy odcinek17,2; użyty tu bezpośredni planner w trybie0
odmawia nieprzejezdnego celu. Zbadane dojazdy mają pełne plany do celu.

32 przypadki to osiem celów przy pending1/2/3/7:24 dojazdy,4 odmowy celu
16,1 oraz4 trasy do obsadzonego19,4 zakończone oczekiwaniem/timeoutem.

| Cel | Charakter | Call końcowy przy pending1 | Wynik fizyczny |
| --- | --- | --- | --- |
| 14,4 | prostaSW,3 rekordy | 59 | dojazd900,260 |
| 16,4 | prostaS po obrocie,3 rekordy | 56 | dojazd1028,260 |
| 17,4 | SE→S,3 rekordy | 70 | dojazd1092,260 |
| 18,5 | SE→SE→S,4 rekordy | 86 | dojazd1156,324 |
| 20,4 | trasa falowa,5 rekordów | 107 | dojazd1284,260 |
| 20,6 | dłuższaSE,5 rekordów | 108 | dojazd1284,388 |
| 16,1 | nieprzejezdne pole | 0 | brak trasy i ruchu |
| 19,4 | cel zajęty przez statyczny0d | 130 | zatrzymanie na18,3/1156,196 |

W ostatnim przypadku planner przywraca bazową wartość celu po nałożeniu
lokalnej zajętości, więc tworzy trasę. Fizyczny predykat później odmawia
wejścia. Przy counter131 ostatni aktywny timestamp wynosi81, czyli
strict unsigned elapsed50. State przechodzi0, lecz prędkość **pozostaje21906**;
nie zerowano jej intuicyjnie. To nie jest dojazd. Diagnoza zamraża stan
przed dalszym idle/RNG i kolejnymi próbami pełnego Work.

## Rekordy oraz rezerwacje waypointów

Rekord ma5 bajtów: int16LE X/Y i byte heading. Dla punktów i>=1 heading
opisuje segment przychodzący z i−1. Pierwszy rekord generatora falowego
może zawierać0 mimo innego pierwszego segmentu. `ShipRoutePlan` zachowuje
surowe rekordy i wylicza początkowy targetHeading z różnicy punkt1−punkt0,
tak jak `004a6330`. Wszystkie eksportowane tablice są kopiami.

`PathIndex` wskazuje aktualną docelową kotwicę, a `CellX/Y` komórkę
zajętą logicznie. To nie zawsze ten sam etap trasy. Gdy środek sprite
sprzed aktualizacji osiąga waypoint_i, źródło:

1. Zwalnia stary owner slot i przepisuje logical Cell na i.
2. Czyści reserved, ustawia centerGate0.
3. Próbuje zarezerwować i+1 **przed dojściem do kotwicy_i**.
4. Przy sukcesie przechodzi do forward-tail; PathIndex nadal wynosi i.

Dopiero dokładna kotwica_i daje centerGate1, PathIndex++ i state3.
Następny call odczytuje incoming heading nowego punktu. Rezerwacja
`004a3a70` najpierw zwalnia dawny reserved, a następnie pyta i zajmuje pole.
Dlatego ponowne wejście state3 może zwolnić i od razu ponownie zająć to
samo przyszłe pole. Oracle i C# porównują obie operacje, a nie wyłącznie
końcowy snapshot. Wyjście index>=count następuje przed czyszczeniem reserved.

Sama udana rezerwacja lookahead nie kończy hamowania4 ani nie ustawia5.
Robi to dopiero `004a3560` w state3. Prędkość jest zachowana między
segmentami; pojedyncza zmiana kierunku o45° przy dodatniej prędkości
nie wymusza pełnego postoju i pierścienia obrotu. Większa zmiana kierunku
przechodzi do state2; helper obrotu kończy cały call także przy osiągnięciu3.
Żadna z362 natywnych tras początkowego planowania tej mapy nie ma wewnętrznej
zmiany większej niż45°; osobny helper obrotu ma szerszy dowód wejść.

## Clamp, hamowanie i dwie publikacje

Arytmetyka prędkości zachowuje źródłowe32-bitowe zawijanie, signed division
w kierunku zera i resztę/3000. Osie używają dzielnika2, diagonale3, zgodnie
z [poprzednim dowodem](SHIP_ADJACENT_MOVEMENT_EVIDENCE.md).

Flaga wykonania ruchu/publikacji `local_2c` jest wyliczana **przed clampem**
do kotwicy. Może być true, choć końcowy World pozostał bez zmian: poprzedni
call osiągnął kotwicę i zrobił lookahead/goto-tail, a dopiero nowa próba
przesunięcia przeprowadza źródłową obsługę tej kotwicy i indeksu.
Nie zastosowano uproszczenia `finalWorld != oldWorld` z krótkiego adaptera.
Nadmiar pełnego przesunięcia nie przechodzi płynnie do kolejnego segmentu;
pozostaje tylko źródłowa reszta arytmetyczna.

Zmiana headingu o1 w `004a3560` publikuje nową klatkę w starej pozycji
przed matematyką kolejnego odcinka. Po przesunięciu może nastąpić druga
publikacja w tym samym call. Każdy rekord zawiera aktualny frame, WorldX/Y
i body depth `max(10000,20000-56-Y)`, zgodnie z kolejnością
`0050d130→0050d5f0`. Wszystkie1046 rekordów porównano z wykonanym C#.
Nie redukowano ich do ostatniej pozycji: pośrednia aktualizacja głębokości
może wpływać na historię remisów kolejki renderera.

Rdzeń ma dwa stałe sloty `Publication`, bez alokacji w Step.
`LastStepPublicationCount` i `GetLastStepPublication(index)` udostępniają
każdy rekord po kolei. Przekroczenie zbadanej pojemności jest jawnym błędem,
bez cichego obcięcia. `Current.DrawnFrame/PublishedWorldX/Y` oznacza ostatnią
publikację. `StoredFrame` nadal osobno przechowuje fazę, która może zmieniać
się bez rysowania. Wewnętrzny analogiczny bufor zmian siatki służy probe
248 rzeczywistych zapisów cell+4 i nie zastępuje operacji na grid.

## API i granice dowodu

```csharp
ShipRoutePlanner.TryPlan(grid, owner, source0b, goalX, goalY, out ShipRoutePlan plan);
var motion = new ShipRouteMovement(grid, owner, source0b);
bool accepted = motion.TryBegin(plan, plannerCounter: 1); // null oznacza brak trasy
motion.Step(pendingSteps: 1, sourceCounter: 2);            // po accepted
for (int i = 0; i < motion.LastStepPublicationCount; i++)
{
    ShipRouteMovement.Publication publication = motion.GetLastStepPublication(i);
    // Odbiorca stosuje każdą publikację i zmianę kolejki we właściwej kolejności.
}
```

Snapshot zachowuje pola wcześniejszego aktora oraz `WaypointX/Y`,
`NextWaypointX/Y` i `LastStepPublicationCount`. Waypoint dotyczy aktualnego
PathIndex; poza trasą para wynosi−1,−1 jako obronna polityka API.
`IsComplete` wymaga stanu0 i dokładnej komórki/kotwicy końcowego celu.
`IsStopped` zamraża zakończoną diagnozę, a kolejny Step nie odtwarza
starych publikacji ani zapisów. Wymaganie sekwencyjnego counter i pending
wyłącznie1/2/3/7 jest ograniczeniem adaptera, nie wyjątkiem oryginalnego C++.

Core SHA-256 `e5abd93a0e5792739dbda684d8309564e373b79fdffa47820a7c2f2dccd2a076`;
plan SHA-256 `fc51279b1219c6a34370813fdde82a3dc87423dd995ccfa6c1f52850397e127f`.
Niezależne review nie znalazło blokad i nie zmieniało kodu.
Walidator obejmuje rzeczywisty C# planner, a następnie cały stan fizyki,
animacji, publikacji i tożsamości zajętości. Ogólne planowanie w ruchomym
świecie, kolejne rozkazy i częściowe retry, AI, walka, dynamiczne połączenia,
pogoda oraz pełny harmonogram Life pozostają poza zakresem. Ten probe nie
uruchamia Unity, Wine, usług ani testu natywnego Windows11/laptopa.
