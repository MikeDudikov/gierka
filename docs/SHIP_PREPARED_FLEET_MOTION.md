# Wspólny ruch trzech kadłubów na przygotowanych trasach — 2026-11-03

Etap historyczny. Dalsze połączenie rozkazów i planera opisuje
[SHIP_LIVE_FLEET_ORDERS.md](SHIP_LIVE_FLEET_ORDERS.md). Poniższe ograniczenia
odnoszą się do przygotowanej gałęzi i poprzedniego DLL.

Rozszerzono istniejący rdzeń`ShipMoveOrder` o fizykę rzeczywistych lokalnych
statków0b,0c,0d na wspólnej siatce. Nowa fabryka`CreatePreparedLocal` używa
własnych parametrów kadłuba i żywego opisu pozostałych właścicieli komórek.
Nie powielono niezmienionej projekcji0b dla innych statków. Dotychczasowy
konstruktor0b nadal korzysta ze swojego sprawdzonego adaptera rozkazów.

**Przygotowane trasy są jawnym wejściem tego etapu.** Nie podłączono jeszcze
przyjętych pakietów20,promocji,zadań grupowych ani dynamicznego planera do
fizyki wszystkich trzech statków. Tryb wyboru floty nadal blokuje wspólny ruch
myszą;normalny Start pozostaje wyłączony. Pełna gra i oprawa2026 są w budowie.
Format pozostaje1920×1080,16:9,pełny ekran całego widoku.

## Własne parametry statków

Wykonano rzeczywiste konstruktory4dc3f0,loader4dfa90 i przeliczenie4bece0
dla każdego aktora. Parametry dotyczą źródłowych,pełnozdrowych lokalnych
statków,ulepszenia właściciela0 i kontrolowanej pogody siła0/kierunek5.

| Pole |0b |0c |0d |
| --- | --- | --- | --- |
| Model/runtime class |0/200 |0/200 |7/207 |
| Komórka początkowa |16,2 |21,5 |19,4 |
| Heading |5 |4 |4 |
| Logiczny sprite |56×56 |56×56 |72×72 |
| Kotwica w komórce |+4,+4 |+4,+4 |−4,−4 |
| Środek sprite’a |+28,+28 |+28,+28 |+36,+36 |
| Początek świata |1028,132 |1348,324 |1212,252 |
| Limit prędkości59f |60000 |60000 |52000 |
| Pole prędkości bazowej27c |60000 |60000 |49400 |
| Przyspieszenie po4bece0 |1200 |1200 |884 |
| Przyspieszenie po rezerwacji4a3a70 |1200 |1200 |1040 |
| SourceEquipmentA |0 |0 |1 |
| Capabilities |fffff7ff |fffff7ff |fffffeff |

W0d inicjalizacja z wyposażeniemA1 zmniejsza pole bazowe27c i przyspieszenie,
ale pozostawia limit59f52000. Rezerwacja pobiera1040 z rzeczywistego4ac110,
zamiast zachowywać884. Obie źródłowe gałęzie tablicy wiatru dają60% przy
kontrolowanej sile0. Hamowanie zachowuje próg limit59f/10,czyli5200 dla0d.
Nie stosuje się do niego parametrów60000/1200/progu6000 statku0b.

Rozmiar sprite’a wpływa na kotwicę,przekroczenie granicy komórki,hamowanie,
test ukończenia oraz publikowaną głębokość. Klatki,obroty,idle RNG,kolejność
publikacji i arytmetyka całkowita używają dotychczasowego rdzenia.

## Wspólna siatka i granice

Każde wywołanie widzi aktualne zajęcia i rezerwacje pozostałych statków.
Testy zmieniają kolejność wywołań,przecinają trasy oraz zostawiają końcowy
cel zajęty przez nieruchomego członka. Oryginalne499aa0 i4a3a70 rozstrzygają
wejście i rezerwację w sondzie;C# stosuje istniejący`ShipAdjacentQuery`
z dynamicznym opisem właściciela. Przy udanej rezerwacji zerowany jest
licznik prób591. Szerszy test wykrył brak tego resetu w pierwszej wersji
nowej gałęzi;poprawiono go przed końcową walidacją i buildem.

`InstallPreparedRoute` kopiuje i sprawdza kompletną trasę złożoną z rekordów
5B(int16X/Y,heading),przed pierwszym tickiem. Jest to jawna granica testu,
a nie dowód wykonania planera lub promocji. Nowa gałąź odrzuca wywołanie
`RequestCellMove`,aby nie uruchomić wyspecjalizowanego planera0b dla0c/0d.
W zwykłym konstruktorze0b dotychczasowa ścieżka rozkazów pozostaje dostępna.

Nie obsłużono tu statków połączonych,dokowania,rozkazów ustępowania,
innych kadłubów,zmian zdrowia/ulepszeń ani pogody w czasie. Sprawdzana
kolejność wywołań jest wejściem kontrolowanym;nie stanowi dowodu całego
RunApp/Life ani schedulera. Pięciu pozostałych aktorów jest nieruchomych.
Pola snapshotu dotyczące pełnej kolejki rozkazów nie opisują nowej gałęzi;
jej dowód obejmuje motion,RNG,publikacje,rezerwacje i zajętość.

## Walidacja źródłowa

| Sprawdzenie | Wynik |
| --- | --- |
| Wspólny ruch C#/x86 |15 scenariuszy/6795 stanów;6750 rzeczywistych wywołań MoveShip |
| Publikacje i komórki |1440 publikacji frame/world/depth;300 uporządkowanych zmian właściciela |
| Przypadki |pending1/2/3/7,mieszana sekwencja,odwrócona kolejność aktorów,skręty,przecięcia,blokowany cel i idle |
| RNG |seedy0,7,12345678hex,ffffffff;osobny stan każdego aktora |
| Kontrakty API |22 kontrole;identity,profile,kopiowanie trasy,granice punktów,liczniki i blokada starego planera |
| Dawny pełny adapter0b |956 stanów/446 publikacji/62 mutacje/35 kontroli;ponownie zgodny z oryginałem |
| Testy celowane |7PASS,0 pominięć,26.234s;3 nowe i4 powiązane |
| Negatywne mutacje |Wykryto błędną kotwicę0d,przyspieszenie1200 oraz brak resetu retry |
| Rzeczywisty DLL Unity |Te same6795 stanów,1440 publikacji i300 mutacji oraz22 API na hostowym Mono |

Sonda konstruuje wszystkich trzech aktorów w jednym emulatorze. Wstępne
placeholdery zajętości0c/0d z WorkOracle zastępuje podczas inicjalizacji
rzeczywistymi aktorami,po czym wywołuje oryginalne499830. W czasie ruchu
nie wpisuje oczekiwanych pozycji ani komórek. Oryginalne MoveShip4a3f40,
obrót,rezerwacje,zwolnienia,hamowanie,animacje i RNG wykonują kod x86.
Granice usług konstruktora,alokacji,publikacji renderowania i widoczności
pochodzą z wcześniejszego WorkOracle;nie ma zastąpionej funkcji ruchu.
Widoczność,fog,dźwięk i pełny rendering nie są przedmiotem tego dowodu.

Fixture:`tests/fixtures/ship_prepared_fleet_motion.json`,SHA256
`cbb6e4307dde096b121644bb34d1119a83405bc7017d02e9716bbc9574a159d5`.
Raporty:`artifacts/fleet-motion/csharp-validation.json` i`shipping-validation.json`.
Kompilacja kontrolna używa`checked+` i`warnaserror+`. Wykonanie DLL na hostowym
Mono nie jest testem natywnego Windows11 ani laptopa docelowego.

Zmienił się jeden dotychczasowy plik C#;pozostałe68 są niezmienione.
Scena,prefaby,pakiety,ustawienia,124 meta oraz9 stagingów nie wymagają zmian.
Nowy kod nie jest jeszcze podłączony do renderowania trzech ruchomych kadłubów.
Końcowy build i regresje:[VALIDATION.md](VALIDATION.md).
Punkt wznowienia:[milestone](evidence/milestone-20261103-prepared-fleet-motion.json).

## Następny krok

Połączyć odbiór26B z promocją i przygotowaniem tras dla każdego kadłuba.
Przenieść dynamiczny planner współdzielonej grupy oraz własność zadań,
zachowując znaczenie grup UI/symulacji i źródłową kolejność operacji.
Następnie przygotować pełne klatki ruchu0c/0d do playera i połączyć cały
obieg z kursorem,zaznaczaniem oraz Ctrl istniejącej grupy.
