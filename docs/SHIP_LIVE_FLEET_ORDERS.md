# Odbiór rozkazów, dynamiczne planowanie i ruch trzech statków — 2026-11-03

Etap rdzenia i poprzedniego DLL. Późniejszą integrację z rendererem opisuje
[SHIP_FLEET_RENDERING.md](SHIP_FLEET_RENDERING.md). Poniższe historyczne
stwierdzenie o braku renderowania nie dotyczy najnowszego trybu kontrolnego.

`ShipMoveOrder.CreateLiveLocal` łączy odbiór normalnego rozkazu20, zapis26B,
promocję pending80, pracę rozkazu i fizykę rzeczywistych0b/0c/0d. Statki same
wyznaczają trasy na wspólnej siatce. Zachowano własne parametry kadłubów
z [poprzedniego etapu](SHIP_PREPARED_FLEET_MOTION.md), w tym72×72 i inne
przyspieszenie0d. Wspólny rdzeń nie wymaga trzech kopii algorytmu ruchu.

Nowa gałąź jest zweryfikowana osobno i w rzeczywistym DLL Unity. **Nie została
jeszcze podłączona do renderowania i sterowania floty myszą.** Zwykły Start
pozostaje wyłączony. Pełna gra i oprawa2026 są w budowie. Docelowy format to
1920×1080,16:9,pełny ekran całego widoku na Windows11.

## Reguły przeniesione z oryginału

Źródłowy konsument4dc630 przyjmuje20,4ab720 promuje pending80, a4ab930
wykonuje normalną pracę i ruch. `ReceiveCellMove` sprawdza adres aktora;
przechowuje cel w rekordzie26B pod offsetami4/8 oraz argument pod25. Odbiór
nie porusza statku. `Tick` zachowuje dotychczasowy porządek promocji/pracy/ruchu.
Nowy adapter przyjmuje normalny argument0 lub fallback255 po osiągnięciu idle.
Zastępowanie rozkazu w trakcie ruchu i priorytety inne niż0 są jawnie odrzucone.

`ShipReplanPlanner.PlanLive` przenosi normalną gałąź4a4e20,4a7290 oraz
GetWayNew4a5740/GetWayNear4a51b0, korzystając ze sprawdzonych source pathfinderów.
Odczytuje stan aktualnego właściciela każdej komórki i **grupę symulacji5e**.
Grupa UI5c nie może zastąpić5e. Callback grupy pozwala czytać stan istniejącego
modułu członkostwa po odebraniu41; nie przypisuje grupy przed odbiorem.

Skan7×7 pomija statek z tej samej nieujemnej grupy, dopóki źródłowy test
retry/RNG nie wymusi blokowania. Zwykły skan blokuje stany0/6; wymuszony
blokuje stany poza4/5. Dla retry>50 generator LCG wykonuje dokładnie jeden
krok, a warunek to `((rng >> 16) % 30 + 50) < retry`. Wysoki retry nie oznacza
wysokiego priorytetu własnej trasy: byte5c7 pozostaje0. Gałąź4a5540 dla
wysokiego priorytetu nie należy do tego adaptera.

Pamięć przeszkód przechowuje komórki w kolejności źródłowej. Po skanowaniu
ponownie sprawdza ich aktualnych właścicieli: usuwa puste komórki, własne
zajęcie i statki w stanach4/5. Pozostałe pozycje blokuje bez ponownego testu
grupy. Wcześniej zapamiętany nieruchomy statek może więc nadal blokować
komórkę po przejściu do tej samej grupy. Obiekt spoza rodziny statków blokuje
mapę, ale świeży skan nie dopisuje go do pamięci statków.

Dotychczasowe `Plan` i konstruktor0b zachowują kontrakt siedmiu statycznych
peerów. `CreatePreparedLocal` nadal wykonuje wyłącznie jawne przygotowane
trasy; nowa gałąź nie pozwala instalować takiej trasy zamiast planowania.

## Dowód wykonania

| Sprawdzenie | Wynik |
| --- | --- |
| Pełny odbiór/praca/ruch x86/C# |14 scenariuszy,10827 porównanych stanów,10740 aktualizacji |
| Rozkazy i członkostwo |45 odbiorów20;36 jawnych aktualizacji grupy po rzeczywistym41 |
| Publikacje i zajętość |1997 publikacji frame/world/depth;196 uporządkowanych mutacji komórek |
| Osobny planer |130 przypadków;149760 komórek pełnych pól przed i po wyszukiwaniu |
| Parametry planera |stany0…6;grupa−1/0/1;retry0/51/79;pamięć pusta/własna/poza7×7;nie-statek |
| Kontrakty API |33 kontrole:adresowanie,granice,priorytet,kopiowanie danych i blokady trybów |
| Rzeczywisty DLL |Ten sam zestaw wykonany na hostowym Mono;raport shipping-validation.json |
| Regresje wcześniejszych modułów |przygotowany ruch6795 stanów;stary adapter0b956;statyczny planer228 przypadków |

Przebiegi obejmują pending1/2/3/7 i sekwencję mieszaną, odwróconą kolejność
aktorów, opóźnione41, brak grupy, zablokowane i zajęte cele, własną komórkę
oraz kolejne rozkazy po idle. Użyto seedów0,7,12345678hex i ffffffff.
130 osobnych wejść planera nie jest wliczonych do10827 stanów ruchu.

Sonda konstruuje trzy rzeczywiste kadłuby w jednym emulatorze i wspólnej
siatce. Nie instaluje tras w przebiegach ruchu. Oryginalne funkcje planowania,
obrotu,rezerwacji,zwalniania,hamowania,animacji i RNG wykonują kod x86.
Pięć pozostałych statków to jawne nieruchome rekordy kontrolne, group−1.
Grupa UI wszystkich aktorów pozostaje7, podczas gdy41 zmienia5e na0.

36 obserwacji bezpośrednio po41 zapisano w fixture jako kontekst, lecz nie
wliczono do stanów porównania: C# odbiera słowo grupy przez osobny moduł,
a nie przez aktualizację efektów ruchu. Nowa wartość grupy jest porównywana
w następnym stanie aktora. Sam konsument41 ma wcześniejszy osobny dowód.
Cele45 rozkazów są wejściami scenariuszy; nie jest to nowy dowód generowania
formacji ani cyklu życia zadań grupy.

Pierwszy zestaw13 przebiegów nie wykrył celowego usunięcia reguły czyszczenia
pamięci dla stanów4/5. Dodatkowy przebieg ruchu również nie wymusił tej gałęzi.
Dlatego dodano130 bezpośrednich wykonań planera, w tym jawnie zapamiętany
poruszający się statek. Teraz ten mutant zmienia pełną mapę oraz trasę i jest
wykrywany. Pierwszy nieudany raport testów zachowano. Mutanty pominięcia
reguły grupy i zmiany stałej RNG także są wykrywane; testów nie osłabiono.

Fixture `tests/fixtures/ship_live_fleet.json`, SHA256
`2d8bef03b7b31a033dac7c88e32537dbc8db760d9961ce1af8929c2d483646ed`.
Świeże wykonanie oryginału jest sprawdzane przez test pozytywny. Kompilacja
sondy używa checked+ i warnaserror+. Źródła, raporty, build i testy wiąże
[milestone](evidence/milestone-20261103-live-fleet-orders.json).

## Końcowa walidacja i integralność

10 testów celowanych przeszło bez pominięć w95.599s. Nowy Windows64Mono
Unity6000.3.27f2 ma148068283B,0 błędów i0 ostrzeżeń. DLL:
`53e9d5004246eb790562ab09b9e55f8c4284400e04487482850fe68e709587eb`.
Przygotowaną gałąź ruchu porównano ponownie także z tym DLL:6795 stanów,
1440 publikacji,300 mutacji i22 API. Pełnego discovery nie powtarzano.

Regresje dotychczasowego playera:sterowanie0b z dwoma rozkazami35 etapów,
wybór floty46 etapów/47 zdarzeń/11 operacji.81 par obrazów ponownie
zdekodowano po testach;wszystkie mają identyczne RGB w1920×1080.168 PNG
ma zweryfikowane hashe;35 prób wejścia i52 próby wyboru,z czego6 ostatnich
odrzucono jako niezgodne ujęcia. Obie sesje zakończyły się exit0 i zwolniły
8 zajęć komórek oraz zasoby wejścia/grafiki. Nie testują nowego renderowania
trzech ruchomych ciał;to oddzielny dowód rdzenia i regresji wcześniejszego UI.

Z1658 plików poprzedniego checkpointu zmieniły się wyłącznie oczekiwane
źródła,dokumentacja i DLL. Zmieniono dwa istniejące C#,pozostałe67 zachowano.
69 C#/124 poprawne unikalne meta;219 plików zamrożonych przed buildem jest
nadal zgodnych.73 pliki Resources i9 oryginalnych wejść zachowały hashe.
Scen,prefabów,pakietów,ustawień i stagingów nie zmieniano.
Raporty:[final-audit.json](../artifacts/live-fleet-orders/final-audit.json),
[testy](../artifacts/live-fleet-orders/targeted-tests.log) i[walidacja](VALIDATION.md).
Nie publikowano,nie tworzono ZIP ani podglądu do prezentacji.

## Granice i dalszy krok

Kontrolowana kolejność ticków jest wejściem sondy. Nie odtworzono jeszcze
całego schedulera RunApp/Life, zadań grupy, zastępowania zajętych rozkazów,
połączonych statków,dokowania,ustępowania,uszkodzeń,ulepszeń ani pogody
zmieniającej się w czasie. Granice usług konstruktora,alokacji,widoczności
i publikacji renderera są odziedziczone z jawnego WorkOracle. Oryginalne
zapisy głowy własnego łańcucha błędów w wczesnych powrotach ProcShipsWork
pozostawiono bez naprawiania; harness nie narzuca im stałej z innej funkcji.
Pełny rendering,fog,dźwięk i obsługa błędów całej aplikacji nie są dowiedzione.

Następny etap: uzupełnić pełne klatki ruchu0c/0d i połączyć sprawdzone moduły
membership/formacji/rozkazów/fizyki z kolejnością kursora i zaznaczeń. Oddzielnie
rozstrzygnąć własność zadań grupowych i Ctrl istniejącej grupy, zanim zostaną
odblokowane te ścieżki sterowania. W playerze nadal działa dotychczasowy ruch0b
oraz osobny wybór floty. [Walidacja](VALIDATION.md) podaje bieżący DLL i regresje.
Testy hostowego Mono oraz Wine nie potwierdzają natywnego Windows11 ani
wydajności docelowego laptopa. Oprawa2026 pozostaje odrębną nieukończoną pracą.
