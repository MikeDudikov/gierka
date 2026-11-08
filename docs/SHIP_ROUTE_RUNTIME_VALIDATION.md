# Walidacja dłuższych tras statku

Stan: 2026-11-02. Zakres: source0b rozpoczynający w(16,2),heading5,
pełne zdrowie,wiatr0/kierunek5,upgrade0 i pozostałe siedem statków
nieruchomych. Cel obrazu:1920×1080,16:9,pełny ekran i pełny viewport.
To diagnostyka źródłowej nawigacji i ruchu,bez pełnego Life,sterowania OS,
AI,walki,pogody całego świata i finalnej oprawy2026.

## Stan walidacji

Build,pełny zestaw testów,pilot i końcowa seria siedmiu sesji przeszły.
[Końcowy raport](../artifacts/long-routes/runtime-final/report.json) pochodzi
z rzeczywistego Windows x64 Mono playera pod Wine11/Xvfb. Cztery dojazdy,
odmowa nieprzejezdnego celu,zatrzymanie przed zajętym celem i kontrolowane
przerwanie zakończyły się exit0. Wszystkie88 kadrów i264 regiony trzech
statków mają RGBmean/max0 i100% dokładnych pikseli.

Build Unity6000.3.27f2:146250459 bajtów,0 błędów i0 ostrzeżeń.
Assembly-CSharp SHA256:
`a54b9ea4de6db05a458794758e26b27600f5aa56c9b78c091583e45448b10fba`.
Pełny unittest:172 testy,0 pominięć,107,491s. Integralność przed buildem:
41 plików C#,87 meta,bez brakujących meta,błędnych i powtórzonych GUID.

[Raport pilota bend](../artifacts/long-routes/runtime-first-bend/report.json):
16 kadrów i48 pełnych regionów statków mają RGBmean/max0. Zwolniono8 zajęć,
exit0. Pilot jest osobnym przebiegiem i nie jest sumowany do końcowych88 kadrów.

## Końcowe przypadki i harmonogram

Poniższe etapy pochodzą z przypiętego oryginalnego śladu i zostały wszystkie
sprawdzone w końcowym playerze. Nie sumujemy pilota do poniższych wyników.

| Przypadek | Cel | Źródłowa trasa / wynik | Etapy | Oczekiwany cleanup |
| --- | --- | --- | --- | --- |
| straight |14,4|3 punkty,bez początkowego obrotu|9|8|
| bend |18,5|4 punkty,zmiana kierunku w trasie|16|8|
| detour |20,4|5 punktów,wave fallback wokół zajętego19,4|20|8|
| depth-cross |20,6|5 punktów,przejście przez rangi0d i0c|20|8|
| blocked |16,1|brak trasy na nieprzejezdny cel|2|8|
| occupied-goal |19,4|plan przyjęty,ruch kończy się przed zajętym celem|13|8|
| halt-second-reservation |18,5|przerwanie po call46 przy drugiej rezerwacji|8|9|

Łącznie wykonano7 sesji,88 kadrów,264 regiony statków i2992 odczyty
rzeczywistych sortingOrder dla34 rendererów. Wszystkie31 pól stanu,pełne
points_hex,21 rejestracji na sesję oraz wpisy kolejki zgadzają się z danymi
oczekiwanymi. W sześciu sesjach zwolniono8 zajęć,a po przerwaniu drugiej
rezerwacji9. W każdej sesji potwierdzono pełne okno0,0,1920,1080. Pierwszy i ostatni punkt nie
są traktowane jako jedyne waypointy. W bend call46 rezerwuje drugi cel
przed ukończeniem kotwicy pierwszego punktu: równocześnie powstają etapy
reserved-2 i transferred-1 przy wciąż aktywnym PathIndex1. Kotwica1 zostaje
ukończona wcall57. Nazwy etapów zachowują te różne znaczenia.

Sufiksy obrotu i first-pixel odnoszą się do aktywnego indeksu przed krokiem.
reserved-j wynika z nowej rezerwacji,poprzez faktyczny indeks komórki trasy;
transferred-j z nowej komórki właściciela. waypoint-i używa starego aktywnego
indeksu,gdy bieżący indeks wzrasta. Wiele zdarzeń jednego call ma ten sam
licznik i osobne zatrzymania bez dodatkowego kroku symulacji.

Przyjęcie planu i state0 nie oznaczają dotarcia. Dla19,4 oryginalny planer
daje ścieżkę,ale po130 wywołaniach ruch zatrzymuje się na18,3 przy
world(1156,196),counter131,speed21906 iLastStateCounter81. IsComplete jest
false; ending ma nazwę stalled i target_reached=False. Odtworzenie retry
całego oryginalnego Life pozostaje poza tą próbą.

## Niezależne dane oczekiwane

`tools/smoke_ship_route.py` przypina
`tests/fixtures/ship_route_movement.json`,SHA256
`d6252388d37891b24f9a271015cdce9ba931ddad9228c8f7eae4ec832fcfeefc`.
Wybiera dokładnie canonical source_static/pending1 dla sześciu celów.
Oczekiwane stany,pełne5-bajtowe rekordy trasy i kolejność wszystkich
publikacji pochodzą z wykonania oryginalnego planera i MoveShip w x86,
z granicami usług opisanymi w dowodzie kinematyki. C# renderera nie jest
źródłem oczekiwanych pozycji ani klatek.

Porównujemy31 pól stanu,pełny points_hex,nazwy/pozycje/porządek trzech
składników0b i34 rzeczywiste odczyty kolejki. Oczekiwany raster powstaje
z źródłowego TYPE8/RLE,palety i przypiętych88 póz. Kamera9,0/skala2 pokazuje
całe jednostki0b/0c/0d. Pozostałe26 składników statków i pięć raf zachowują
źródłowe pozycje,ale ich ranking może zmieniać się wraz z ruchem0b.

Kolejka zależy od historii remisów. Każda publikacja,również druga w tym
samym call,zasila rzeczywiste55d670/55d960→571eb0 przez
`original_cohort_trace` w `tools/validate_source_sprite_depth_queue.py`.
Te wywołania nie mają hooków. Wynik21 retained node IDs jest spłaszczany
według źródłowego lokalnego porządku TYPE8 do34 rendererów. Nie wykonujemy
zwykłego sortu tylko po końcowymY ani nie korzystamy z nowej kolejki C#
jako wyroczni. Przekroczenie remisu i powrót w jednym call daje inny wynik
niż pozostawienie wyłącznie ostatniego zapisu — sprawdza to osobny test.

## Prezentacja i testy helpera

Globalny maksymalny błąd kanału oraz maksimum każdego ROI muszą wynosić≤4,
przy zachowaniu wcześniejszych progów średnich. Rzeczywisty pilot i wszystkie88 kadrów końcowych mają błąd0.
Cały obraz obejmuje również miejsca poza aktualnym obszarem statku,aby
wykryć pozostawioną starą grafikę. Wewnętrzne framebuffer’y służą wyłącznie QA.

Każdy etap jest zatrzymany na1,25s. Przechwycenie może oczekiwać na zgodną
prezentację najwyżej1s. Przed i po każdej próbie sprawdza niezmienność31 pól,
etapu,3 części oraz34 wpisów kolejki. Złe/spóźnione obrazy nie są akceptowane,
wszystkie odrzucone PNG i metryki są zachowane. Identyczność z wcześniejszym
zapisanym etapem jest raportowana tylko po bezpośrednim porównaniu bajtów.
Końcowy przebieg wykonał128 prób:88 przyjętych i40 odrzuconych przed zgodną
prezentacją. Dokładnie16 odrzuconych było identycznych z wcześniejszym
zarejestrowanym etapem. Pozostałych24 nie nazywamy tak bez osobnego dowodu;
żadnej z tych40 prób nie zaliczono jako poprawny kadr bieżącego etapu.

Sześć testów `tests/test_smoke_ship_route.py` przeszło bez pominięć.
Obejmują natywną macierz88 etapów,26 mutacji logów,przypadek dwóch zapisów
na granicy remisu,błędne nakładanie przy starej kolejności,pozostawiony sprite,
globalne granice4/5,stale→correct retry oraz odrzucenie zmienionej kolejki
i spóźnionego poprawnego obrazu. Jawne odrzucenia:26 logów,3 obrazy i2 fence.
Nie jest to nowy test fizycznej myszy ani pomiar wydajności.

Helper SHA256:
`9e7bce3c14fc816a572a5555d467948dc1ce37f571064435e89d855fcc75b716`.

## Odtwarzanie i granice

```sh
.venv/bin/python tools/smoke_ship_route.py --case bend --output artifacts/long-routes/<nowy-pilot>
.venv/bin/python tools/smoke_ship_route.py --output artifacts/long-routes/<nowy-katalog>
```

Sesje uruchamiać kolejno,własny Xvfb/player i wolne`:79`. Nie budować do
katalogu uruchomionego playera ani kończyć globalnie Wine. Editor/Wine
w tym hoście wymagają IPC poza sandboxem. Nie zmieniano C# po buildzie.

Planner@1 i Step@2… to jawny przygotowany harmonogram,nie pełne source Life.
Zatrzymania harnessu nie potwierdzają tempa całej gry ani oryginalnej pauzy.
Po przybyciu lub stalled stan jest zamrożony bez idle RNG i dalszego retry.
Brak natywnego Windows11,docelowego laptopa,OS-input,walki/AI i całego świata.
Nowe podglądy do prezentacji i ZIP nie są tworzone bez wyraźnej prośby.

Powiązania: [planer](SHIP_ROUTE_PLANNER_EVIDENCE.md),
[ruch trasy](SHIP_ROUTE_MOVEMENT_EVIDENCE.md),
[kolejność planowania](SHIP_ROUTE_ORDER_EVIDENCE.md),
[źródłowa kolejka](SOURCE_SPRITE_DEPTH_QUEUE_EVIDENCE.md),
[bieżąca walidacja](VALIDATION.md).
