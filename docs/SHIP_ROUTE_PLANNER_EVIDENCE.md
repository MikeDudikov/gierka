# Źródłowy adapter dłuższych tras statku0b

Stan: 2026-11-02. `ShipRoutePlanner` łączy źródłową mapę przechodniości,
lokalną maskę ośmiu referencyjnych statków oraz [planer55c9a0](SOURCE_PATHFINDER_EVIDENCE.md).
Przestaje ograniczać cel do sąsiada, lecz zachowuje jawny początkowy świat
source0b(16,2),heading5,pełne zdrowie,wyposażenie0,mode0/restriction0/priority0.
Nie jest pełnym Work/Life,przeplanowywaniem ruchomych obiektów ani shore mode.

## Co wykonuje oryginalny oracle

`tools/probe_ship_route_navigation.py` wykonuje konstruktor/LoadDateBase
source0b oraz inicjalizację prędkości, następnie natywny prefix mapy
`49a950…49a9ce`, `ProcPostMove4a6330`, `GetWayNew4a5740`, `4a4e20` i
rzeczywisty `55c9a0` z linią oraz falą. Alokatory i granice inicjalizacji są
opisane w raporcie. Nie zastępuje żadnego planera ani query jego wynikiem.

Siedem pozostałych obiektów to minimalne statyczne rekordy zajętości z
ID,komórką i runtime tagiem. Ich pełne konstruktory i AI nie wykonują się.
[Osobny odczyt metadanych](../artifacts/long-routes/navigation/actor-metadata-proof.json)
potwierdza: source0b group−1,state0,maxSpeed60000,priority0,link0;
pozostałe siedem group0,state0,maxSpeed0,priority0,link0. Tagi wynoszą
200/200/207/201/206/206/206/206. To jawny świat referencyjny,nie dowód
pełnej inicjalizacji pierwszej misji.

## Mapa i źródłowe wyjątki

Mapa bazowa ma0, gdy przechodzi źródłowy predykat nibbli flag, oraz−1
w przeciwnym razie. Porównano wszystkie576 komórek z oryginalnym prefixem.
Dla tego source0b `4a4e20` przegląda7×7: X13…19,Y0…5; pomija samego0b.
Przy zadanych metadanych lokalny state0/foreign-owner blocker to wyłącznie
0d w(19,4). Pozostałe statki są poza tym oknem i nie zostają automatycznie
zablokowane na całej mapie. Nie dodajemy globalnej maski, której tu nie ma.

Następnie `4a5740` **przywraca wartość terenu celu** po lokalnej masce.
Dlatego odległy cel(19,4) zajmowany przez0d może uzyskać trasę. Jego ruch
musi osobno obsłużyć oczekiwanie/timeout; samo planowanie nie dowodzi
dojazdu. Dla sąsiada `4a6330` wcześniej wykonuje pełny predykat499aa0,
więc te dwa przypadki mają różną kolejność bramek.

Wejściowa preferencja `55c9a0` jest tu literalnie0 z `GetWayNew`,nie bieżący
heading5 statku. Pierwszy target-heading i stan obrotu wyznacza się z różnicy
pierwszych dwóch punktów,a nie z heading pierwszego rekordu fali.

| Cel | Natywne rekordy [X Y heading] | Zakres |
| --- | --- | --- |
|14,4|16 2 5 →15 3 5 →14 4 5|dwa proste odcinki bez wstępnego obrotu|
|16,4|16 2 6 →16 3 6 →16 4 6|obrót i ruch na południe|
|17,4|16 2 7 →17 3 7 →17 4 6|zmiana kierunku przy kolejnym punkcie|
|18,5|16 2 7 →17 3 7 →18 4 7 →18 5 6|dłuższa linia i narożnik|
|20,4|16 2 0 →17 2 0 →18 3 7 →19 3 0 →20 4 7|fala omija maskę19,4|
|16,1|brak|nieprzejezdny teren|

Dla blokowanego terenu(18,2) bezpośredni ProcPostMove nie instaluje trasy.
Pełny Work może wybrać cel pośredni17,2; jego polityka nie jest podmieniana
na wynik tego adaptera. Dalsze retry i zmiana trybu pozostają poza nim.

## Kontrakt C# i wynik

`TryPlan(grid,owner,sourceSeed,goalX,goalY,out ShipRoutePlan)` obsługuje cele
wewnątrz24×24 i sprawdza source0b oraz osiem różnych referencji właścicieli
we właściwych komórkach,bez dodatkowych zajęć. Tożsamość jest referencyjna,
nie `Equals` lub magiczne ID0. `CapturePlanningField` zwraca niezależną kopię.
`ShipRoutePlan` jest niemutowalny i zachowuje pełny bufor5B rekordów.
Świat po wykonanym ruchu,inny state/priority/group/link lub inne klasy
wymagają osobnego rozszerzenia. Nie obiecujemy obsługi mutacji spoza kontraktu.

**576/576 celów C#/x86 PASS**:362 z zainstalowaną trasą i214 bez niej.
Ta ostatnia liczba obejmuje również aktualną komórkę16,2, dla której źródło
zwraca1 bez instalacji ruchu. Pozostałe sukcesy i odmowy terenu mają low-byte0;
`EAX!=0` nie jest testem powodzenia. Porównano raw5B,liczbę/indeks punktów,
stan i marker center,kierunek pierwszego odcinka oraz cały input-map55c9a0.
Dziewięć kontroli API i własność kopii również przeszły w `/checked+`.

Trwały fixture: `tests/fixtures/ship_route_planner.json`, SHA256
`b291068ee191a53826436ca8fe8e92c88c2a7e76fc7cd779f2c59b737564caa7`.
Dwa testy `tests/test_ship_route_planner.py`: pełne oryginalne porównanie i
odrzucenie zmienionego fixture przed wykonaniem źródła.
[Końcowy raport](../artifacts/long-routes/navigation/ship-route-planner-csharp-validation-frozen.json).
Wcześniejsze raporty i pełne natywne mapy zachowano.

Nie uruchamiano Unity/Wine ani renderowania w tych testach; runtime ruchu,
pełny świat,AI,sterowanie OS,natywny Windows11 oraz sprzęt docelowy muszą
mieć osobne dowody. Nie generowano podglądów ani ZIP-ów. Istniejące
`ShipAdjacentPlanner` i jego fixture pozostały bez zmian.
