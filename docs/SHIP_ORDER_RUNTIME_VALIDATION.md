# Obieg rozkazów ruchu — zakres i walidacja

Stan: 2026-11-03. Docelowa prezentacja całej gry pozostaje
1920×1080,16:9,pełny ekran na Windows11. Normalny Start jest nadal wyłączony.
Ten etap rozszerza kontrolowany statek0b o przyjęcie polecenia,promocję,
normalne Work,ponowne planowanie,zatrzymanie i dalszą bezczynność.
Nie jest kompletnym Life,sterowaniem gracza ani gotową misją.

## Kontrakt diagnostyki

`--ship-order-reference` uruchamia osobny tryb na tej samej mapie,flocie
oraz21-węzłowej kolejce co poprzednia diagnostyka tras. Cel wskazują
`--ship-order-target-x/y` (domyślnie18,5). Oba argumenty
`--ship-order-next-x/y` zlecają drugi ruch po zakończeniu pierwszego.
`--ship-order-session-seed` jest jawnym uint32,domyślnie0. To kontrolowane
wejście porównawcze,nie deklaracja domyślnego seeda nowej misji.

Licznik początkowy wynosi0. Request nie wykonuje kroku symulacji; pierwszy
Tick1 wykonuje promocję,Work i MoveShip przy tym samym liczniku.
Każda operacja ma osobny sample_index. Drugi request może mieć ten sam
counter co poprzedni Tick; jego publikacje i efekty nie są powtórzeniem
poprzedniego Tick. Kwant40ms daje najwyżej jeden krok. Holdy QA1,25s są
wyłączane z czasu diagnostycznego i nie dowodzą tempa całej gry.

`--ship-order-stop-at N` ogranicza liczbę Tick do0…4096. Po końcowym Tick
może zalogować jego etapy,lecz zatrzymuje diagnostykę przed następnym
request i przed zwykłym zakończeniem. Bez limitu obowiązuje bezpiecznik4096.
Tryb wyklucza pozostałe trzy diagnostyki ruchu i menu/briefing replay.

Żądany cel,aktywny target i endpoint aktualnej ścieżki są osobnymi polami.
`complete` dotyczy fizycznego dojścia do endpointu. `requested_reached`
sprawdza fizyczny target. Samo state0 ani usunięcie active80 nie są dowodem
obu tych zdarzeń. Źródłowy Work może zlecić stop podczas wyhamowywania.
Następny request tej diagnostyki wymaga CanRequestMove oraz faktycznej
publikacji idle56…87; zastępowanie rozkazu podczas ruchu pozostaje poza zakresem.

Każda publikacja frame/world/depth trafia kolejno do istniejącej kolejki,
a następnie do trzech rendererów statku. Każdy checkpoint odczytuje także
wszystkie34 rzeczywiste sortingOrder,w tym pięć raf. Stored frame jest
odróżniony od drawn frame,także przy publikacji idle przed zmianą klatki.

## Dowody czystego kodu

- [Idle i RNG](SHIP_IDLE_ANIMATION_EVIDENCE.md):4232 porównania C#/x86,
  77 inicjalizacji seeda,96 całych wywołań MoveShip,456 publikacji i56 zwolnień.
- [Nearest pathfinder](SOURCE_NEAREST_PATHFINDER_EVIDENCE.md):1380 przypadków,
  pełne rekordy5-bajtowe,pola,wynik zakresu i liczniki fali;9 kontroli API.
- [Planer bieżącej pozycji](SHIP_REPLAN_PLANNER_EVIDENCE.md):228 porównań mapy,cache,RNG i ścieżek,
  13 kontroli API. Obejmuje istniejącą rezerwację i przeszkody pamiętane
  poza lokalnym obszarem7×7. Transakcję Work sprawdza osobny koordynator.

[Koordynator](SHIP_MOVE_ORDER_EVIDENCE.md) zgadza się w7 przypadkach,
956 stanach,941 Tick,446 publikacjach i62 mutacjach;35 kontroli API.
Fresh native musi być równe przypiętej fixture przed wykonaniem C#.
Pełny discovery zakończył182 testy bez pominięć w151,698s. Osobno7 testów
helpera QA przeszło w6,221s,łącznie z granicą stop-at przy pierwszym idle.

## Rzeczywisty player Windows Mono

[Końcowy raport](../artifacts/order-cycle/runtime-final-resumed/report.json):
4 sesje,53 pełne kadry1920×1080 i159 ROI;wszystkie RGBmean/max0.
Każdy etap porównuje54 pola,pełne pathhex i cache,3 części statku oraz
34 rzeczywiste wpisy kolejki (łącznie1802),z21 rejestracjami na sesję.
Wszystkie sesje zakończyły się exit0. Cleanup8/8/8/9 obejmuje dodatkową
rezerwację przy przerwaniu. Zachowano63 próby obrazu,10 odrzuconych.

| Scenariusz | Kadry | Wynik |
| --- | --- | --- |
|18,5|12|Fizyczny dojazd87,stop98,clear99,publikacja idle101|
|Nearest18,2;limit180|10|Endpoint17,2,żądany target nieosiągnięty;active1152 pozostaje|
|18,5→16,4|23|Drugi request po idle przy tym samym counter101,bez resetu RNG;idle drugiego ruchu197|
|18,5;limit46|8|Przerwanie przy dodatkowej rezerwacji;cleanup9|

Osobny [pilot](../artifacts/order-cycle/runtime-first-normal/report.json)
ma12 kadrów/36 ROI RGB0;nie dodaje się ich do53.
Unity6000.3.27f2 zbudował146287259 bajtów,0 błędów/ostrzeżeń BuildReport.
DLL SHA256 `6c646f8c6313ff0005d51dffda7596e986dad0101f6a2432f831474229bc4773`.
46 C#/92 poprawne meta;bez zmian C# po buildzie.

Pierwsza próba końcowego zestawu została przerwana przez restart maszyny.
Nieukończone artefakty zachowano w runtime-final. Świeży runtime-final-resumed
użył tego samego DLL i źródeł;[zapis wznowienia](../artifacts/order-cycle/resume-status.json)
potwierdza ponowne sprawdzenie hashy. Nie uznaje się przerwanej próby za PASS.

## Regresje i helper QA

Na tym samym DLL:[dwie wcześniejsze trasy](../artifacts/order-cycle/route-regression/report.json)
mają28 kadrów/84 ROI RGB0,a [stary odcinek](../artifacts/order-cycle/movement-regression/report.json)
9 kadrów/27 ROI RGB0. Cleanup8/9 i exit0 obu par sesji.
[Briefing](../artifacts/order-cycle/briefing-regression/report.json) ma39 etapów/11 kadrów,
[menu](../artifacts/order-cycle/menu-regression/report.json)27/5/6 komend;normalne Quit0.
To cztery wybrane grupy,nie powtórzenie wszystkich historycznych QA.

[Niezależna kontrola QA](SHIP_ORDER_QA_EVIDENCE.md) sprawdziła hashe obrazów,
stany i kolejkę. Z10 odrzuconych prób6 jest dokładnie zgodnych z wcześniejszym
checkpointem,4 nie sklasyfikowano. Po runtime poprawiono tylko selektor
stop-at poza czterema kanonicznymi przypadkami. Każdy z czterech planów
pozostał identyczny;nowe granice mają osobny test. Zachowano dokładną wersję
helpera wykorzystaną do rzeczywistych sesji. C# i DLL pozostają bez zmian.

## Granice

Kontrolowane wejścia to zdrowy source0b,wind0/heading5,upgrade0 i siedem
nieruchomych jednostek. Nie odtworzono pozostałych gałęzi Life/AI,walki,
połączonych jednostek,save/load,pogody świata ani swobodnych rozkazów.
Źródłowa grafika służy jako wzorzec zgodności;nie jest finalną oprawą2026.
Wine/Xvfb nie zastępuje testów natywnego Windows11 ani docelowego laptopa.

Zgodnie z preferencją użytkownika nie przygotowuje się ZIP,podglądu do
prezentacji ani publikacji. Wewnętrzne framebuffery są dowodami QA.
