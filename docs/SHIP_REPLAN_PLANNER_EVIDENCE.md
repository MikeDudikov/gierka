# Planowanie ponowne z bieżącej komórki statku0b

Stan: 2026-11-03. `ShipReplanPlanner` wydziela surowe źródłowe budowanie
mapy i drogi z `4a5740/GetWayNew` oraz `4a51b0/GetWayNear`. Obsługuje bieżącą
komórkę0b, oddzielny początek nowego planu, siedem nieruchomych referencyjnych
statków, pamiętane przeszkody, radius/mode, retry priority i stempel RNG.
Nie przejmuje własności całej transakcji `ProcPostMove` ani zlecenia Work.

Oryginał `ancient.exe` ma SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
[Oracle](../tools/probe_ship_replan_planner.py) używa zachowanego, przypiętego
SHA bootstrapu source0b z wcześniejszej próby Work. Wykonuje oryginalne
map/query/path/cache funkcje. Nie podmienia ich wyliczonym wynikiem.
Ograniczenia inicjalizacji, heap i usług są odziedziczone jawnie po tym
bootstrapie; nie jest to sesja kompletnego oryginału ani pełny świat AI.

## Mapa bieżącej komórki i pamiętane przeszkody

Pole bazowe49a950 nadal ma0/wolne i−1/zablokowane z nibbli źródłowych flag.
`4a4e20` nakłada7×7 wokół **bieżącej komórki obiektu**, nawet jeżeli nowa
ścieżka jest liczona od jego NextCell. Sam requester jest pomijany w obu
swoich zajęciach: bieżącym i opcjonalnej rezerwacji.

Siedem referencyjnych obiektów zachowuje runtime family200,state0,group0,
bez linków; source0b ma group−1. To te same jawne minimalne obiekty co
w poprzednich dowodach, bez wykonywania pełnych konstruktorów/AI pozostałej
floty. Dla tych danych obce state0 komórki są maskowane.

`4a7230` zapamiętuje takie indeksy w liście `ship+5cd` bez duplikatów,
w kolejności wstawiania. Następne `4a7290` odtwarza je na całej mapie,
również **poza nowym lokalnym7×7**. Nie wolno więc odtwarzać maski wyłącznie
z bieżącego okna ani sortować listy po ID. Przykład: po zmianie komórki na
14,4 wcześniej zapamiętane19,4/index115 nadal blokuje pole.
W zadeklarowanej nieruchomej flocie cache nie usuwa się podczas samego
budowania mapy. Wyczyszczenie go w innych stanach/stopach należy do
wyższej transakcji ruchu, a nie do tej klasy.

## Różnice dwóch surowych builderów

- GetWayNew wybierany jest dla mode0/retry0 i zawsze przywraca bazowy
  teren celu po masce. Jeżeli cel był zablokowany zarówno w bazie, jak
  w mapie roboczej, oryginał dodatkowo wywołuje nearest55b9e0 z range1.
  Ten wewnętrzny fallback nie zmienia pola post-plan radius: pozostaje0.
- GetWayNear wybierany jest przy niezerowym mode albo retry. Przy normalnym
  preserveDestinationMask=true nie odblokowuje zajętego celu po masce.
  Używa [SourceNearestPathfinder](SOURCE_NEAREST_PATHFINDER_EVIDENCE.md).
  Jeśli źródłowy reached-bit jest0, post-plan radius wynosi mode+1;
  inaczej mode pozostaje bez zmian.

`UsedNearest` w API wskazuje wybór buildera4a51b0, nie samą obecność
wewnętrznego wywołania55b9e0. Cel żądany, endpoint ścieżki i reached-bit
pozostają osobne. **ReachedWithinRange nie oznacza osiągnięcia żądanego
pola**: dla18,2/range1 poprawna ścieżka kończy się17,2 z reached=true.
Dwa identyczne rekordy początku również mogą być prawidłowym wynikiem
nearest, lecz nie są instalowalną drogą; ProcPostMove obsługuje je osobno.

Gdy retryPriority>50, `4a4e20` zawsze wykonuje jeden krok RNG:
`seed = seed*0x41c64e6d + 0x3039` z wrapuint32. W zadanej flocie state0
obie gałęzie losowej bramki maskują te same komórki, ale sam nowy seed
jest obserwowalny i wraca do jednego właściciela RNG w koordynatorze.
Nie pominięto go tylko dlatego, że raster mapy się nie zmienia.

## API i własność

`ShipReplanPlanner.Plan(grid,owner,cellX,cellY,originX,originY,goalX,goalY,
radius,retryPriority,preserveDestinationMask,randomState,cachedObstacles)`.

`ShipPlanningResult` udostępnia liczbę punktów, żądany cel, endpoint,
HasInstallableRoute,FirstHeading,UsedNearest,ReachedWithinRange,
RadiusAfterPlan,RandomStateAfter i RandomStateAdvanced. Każdy bufor
punktów/map/cache zwraca jako niezależną kopię. Nie zmienia gridu ani
wejściowej listy cache. Wspiera24×24, source0b w bieżącej komórce z1…2
własnymi zajęciami, siedem znanych różnych tożsamości w oryginalnych
komórkach, radius0…32 i retrybyte0…255. Inne obiekty świata są odrzucane.

Wyższy koordynator odpowiada za:

- pre-gate57b==counter oraz sąsiedni query i already-at-goal;
- wybór origin:4e0b50 zeruje center w stanach0/2/3; jeżeli center pozostaje
  true przy4/5, nowy plan zaczyna się odNextCell, a lokalne okno nadal odCell;
- nowe593,retry591,last-plan57b,goal54e/552 i zapis recheck6100;
- wymianę bufora w ruchu, poprzedzenie go aktualną komórką w gałęzi center,
  zachowanie/rezerwowanie/zwalnianie pól oraz źródłowe stop/cache-clear;
- warunki końca zlecenia i oddzielenie endpointu od pierwotnego celu.

Stary `ShipRoutePlanner` pozostaje bez zmian i zachowuje wcześniejszy
kontrakt startowy. Nowa klasa nie udaje portu wszystkich trybów follow,
linkowanych jednostek, innych metadanych statków i pogodowej inicjalizacji.

## Wykonane porównanie

**228/228 przypadków C#/x86 PASS**,13 kontroli API, `/checked+ /warnaserror+`.
Porównano pełne5-bajtowe rekordy, mapę przed plannerem i po nim, endpoint,
znacznik zasięgu, radius, RNG i kolejność całej listy przeszkód. Zakres:
7 bieżących komórek ×10 celów ×3 warianty mode/retry, retry49/50/51/79/149/
150/255, oba ustawienia destination mask, seedFFFFFFFF, cache poza oknem,
dwa pamiętane statki oraz planowanie od rezerwowanej NextCell.

[Końcowe porównanie](../artifacts/order-lifecycle/planning/csharp-with-fallback.json),
[walidator](../tools/validate_ship_replan_planner.py),
[probe C#](../tests/fixtures/ShipReplanPlannerProbe.cs),
[testy](../tests/test_ship_replan_planner.py).
Fixture `tests/fixtures/ship_replan_planner.json`, SHA256
`0d28739a3703678201572bf8c5373446cb1118540565cc20dcd3d8fac5e4dc64`.

Pierwszy raw-entry bootstrap użył niewłaściwej konwencji wywołania:
4a5740/4a51b0 wymagają explicit self na stosie, nie tylkoECX. Następnie
pierwsze porównanie C# wykryło brak wewnętrznego fallbacku GetWayNew dla
blocked-goal. Poprawiono wywołanie i przeniesiono faktycznie zaobserwowaną
gałąź; nie osłabiono porównania. [Zapis ustaleń i wcześniejszy fixture](../artifacts/order-lifecycle/planning/implementation-findings.json)
pozostają zachowane. Nie zmieniano danych oryginału.

Nie uruchamiano Unity/Wine ani usług, nie generowano podglądów, paczek ZIP
ani publikacji. Player, pełny cykl zlecenia i stan po ruchu mają osobne dowody.
