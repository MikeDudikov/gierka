# Zadanie 100/2 w świecie x86 i zgłoszenia dotarcia — 2026-11-04

Wykonano kolejny etap przed integracją zadań100/2 w świecie Unity:
niezależny korpus oryginalnej pętli świata oraz port dwóch miejsc zgłoszenia
dotarcia w istniejącym `ShipMoveOrder`. `ShipWorldStep`, `SingleStepClock`,
`ShipFleetMembership`, `ShipFleetNormalTask` i `MissionOccupancyGrid` nie
zostały zmienione. Nie dodano nowego zegara, ECS, Update lub właściciela grupy.

## Ustalona kolejność

Przykład z faktycznie wykonanych instrukcji oryginalnego PE32:

| Rejestr obiektów | Zgłoszenie statku12 | Work grupy emituje20 | Dostarczenie20 |
| --- | --- | --- | --- |
| Flota,11,12,13 | Krok58 | Krok59 | Krok60 |
|11,12,13,flota | Krok58 | Krok58 | Krok59 |

`521500 PrepareMail` i `522850 SendMail` poprzedzają `542320/542200`.
Zdarzenie310 jest dopisywane do wektora grupy przez4a1700, w trakcie Work
statku. Grupa za statkiem odczytuje je w tym samym kroku; grupa przed nim
dopiero w następnym. Wygenerowany20 pozostaje w kontrolnej kolejce2e do
następnej fazy poczty. Nie ma drugiego flush ani natychmiastowego odbioru20.

W kroku58 statek12 podaje cel162, chociaż jego zapisana komórka to163.
Oryginał zgłasza również bliskość przy nieudanej rezerwacji, nie tylko
osiągnięcie dokładnego celu. Powiadomienie może powtórzyć się w kolejnym
kroku; nie wolno go deduplikować. Filtr grupy jednoosobowej w4a0230/4cf0b0
nadal odrzuca odpowiednie zdarzenia z innej komórki.

## Zakotwiczenie i granice próbnika

Oryginalny EXE SHA256:
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Ghidra readOnly/noanalysis wyeksportowała10funkcji z C i assemblerem:
4a3f40,5573d0,4a2f60,4a1700,4cc590,4cf0b0,4cf550,49ab30,4c4f40,542200.
Eksporty i log zakończenia są w `artifacts/fleet-queued-world-evidence`.

Nowy `QueuedWorldOracle` rozszerza dotychczasowy próbnik świata. Wykonuje
rzeczywistą gałąź520352, pocztę, rejestr, zadanie100/2 oraz oryginalne
Promote4ab720 i Work4ab930 trzech skonstruowanych statków. Zamiast pomijać
4a1700, pozwala mu zbudować i dopisać całe zdarzenie32B. Globalny wskaźnik
floty5c7504 otrzymuje jawnie istniejącego właściciela tego świata.

Granica `Ship::Life` pozostaje udokumentowanym trampolinem Promote/Work;
nie uruchamiano pełnego4dec40 lub całej aplikacji. Tworzenie/usuwanie
graficznych markerów i backend alokacji pozostają granicami próbnika.
Nie zastąpiono algorytmu grup, ruchu, kolejek lub serializatora.

Trzy osobne uruchomienia źródłowego UI518070 sprawdzają początkowe pakiety,
nagłówki i logiczną trasę względem wejścia floty w drugim silniku x86.
Dalsza ewolucja świata odbywa się w jednym silniku. To jawna granica
UI/świat, nie dowód pełnego startu aplikacji oryginału.

## Korpus

Fixture `tests/fixtures/fleet_queued_world.json`, SHA256:
`5d36373f7cf9e95fd2f66e338af1cdc6c0c6ad6526cd58610bf3217cfe98d885`.

- 46 scenariuszy, 5416 klatek, 5368 przyjętych kroków;
- 24 permutacje rejestru, zimna/ciepła poczta i grupa jednoosobowa;
- 16386 stanów aktorów z inicjalizacją;
- 258 wywołań dotarcia: 62 dokładne i 196 z sąsiedniej komórki;
- 5368 wywołań Work grupy, 382 odebrane i 174 wygenerowane pakiety;
- 8458 publikacji oraz 48 odczytów wave[-1].

Wiek101 oraz rozłączne wyspy są oznaczonymi, syntetycznymi wejściami
pamięci, nie twierdzeniem o ich naturalnej historii w misji. Słowa signed16
0,117,32767 i−32768 są przekazywane jawnie dla każdego aktora.117 pozostaje
wartością zmierzonego wcześniej, ograniczonego profilu Wine CRT, nie stałą
Windows lub ogólną gwarancją sterty gry. Nie wykonywano nowego próbnika CRT.
Na wyspach kandydat0 daje20 dla słowa0, a dla117 blokuje emisję. Signed−32768
i dodatnie32767 zachowują oryginalne przeciwne wyniki porównania.

## Port do istniejącego aktora

Zmieniono wyłącznie runtime `ShipMoveOrder.cs`:

- `Arrival` przechowuje licznik i komórkę przekazane do4a1700;
- `LastStepArrivalCount` i `GetLastStepArrival` udostępniają wynik kroku,
  analogicznie do istniejących publikacji pozycji;
- `4a49af`: zgłoszenie po zmianie komórki, przed hamowaniem;
- `4a4a67`: zgłoszenie po nieudanej rezerwacji/hamowaniu, gdy5573d0 zwraca1.

5573d0 używa `max(dx,dy)+min(dx,dy)/2`, z całkowitym dzieleniem i starymi
komórkami wyliczonymi z pozycji sprite’a sprzed ruchu. Nie zastępujemy tego
sprawdzeniem `RequestedTargetReached`, stanem idle lub współrzędnymi nowej
pozycji. Do wyniku zawsze trafia zapisany cel5b2. W bounded Move oba miejsca
wywołania są rozłączne; po jednym kroku może być najwyżej jedna obserwacja.

To obserwacja wywołania, nie gotowe zdarzenie grupy ani pakiet poczty.
4a1700 może wrócić bez dopisania rekordu, jeżeli grupa/wektor nie istnieje.
Tożsamość grupy, indeks członka i bufor zdarzeń nadal należą do
`ShipFleetMembership`. Bieżący `ShipWorldStep` jeszcze nie odbiera nowego
wyniku; jego guard100/2 pozostaje aktywny.

W następnym etapie wynik trzeba odebrać po każdym Tick aktora, w kolejności
rejestru, przed ewentualnym Work floty. Odczyt dopiero po całej pętli utraciłby
udowodnione zachowanie. Nie tworzyć drugiej kopii składu grupy ani dodatkowej
globalnej fazy zadań. Kontekst każdej fali musi być jawnym wejściem świata.

## Jak sprawdzono C#

Istniejący testowy `ShipWorldStepProbe` otrzymał tryb odtwarzania wejść
aktora. Dostarcza niezmienne pakiety z x86 w źródłowym FIFO, synchronizuje41
przez istniejące członkostwo i wywołuje aktorów w zarejestrowanym porządku.
Nie wykonuje C#zadań grup lub nowego harmonogramu świata. Porównuje cały
dotychczasowy odczyt ciała, rezerwacje, zajętość, publikacje i nowe obserwacje
ze16386stanami oryginału. Są2dodatkowe kontrole granic API.

Trzy mutacje rzeczywistego C# są odrzucane: aktualna komórka zamiast celu,
błędny próg bliskości i tłumienie powtórzeń. Trzy osobne mutacje instrukcji
x86 pomijają każde z wywołań4a1700 albo zmieniają SETL na SETB. Skutki
sprawdzono w stanie zadania/poczty, nie tylko w liście wywołań debuggera.
Plik EXE i kod produkcyjny nie są zmieniane przez mutacje.

Pierwszy pełny test odtworzył poprawnie wszystkie klatki, lecz odrzucił
metadane terenu: Python zwrócił tuple, a JSON list. Poprawiono normalizację
walidatora, bez zmiany fixture, oryginału lub C#. Zachowano pierwszy log
`tests-metadata-tuple-failed.log`; końcowy wynik jest w `tests.log`.

Końcowo6testów PASS,0skip,208.196s:5nowych i regresja1287przypadków zegara.
Ponownie wykonano wszystkie46scenariuszy x86. Discovery324testów;pełnego
zestawu nie uruchamiano. `validation-final.json` wiąże podsumowanie z logiem.

Build Windows64Mono w Unity6000.3.27f2:152975915B,0warnings/0errors,
1920×1080,16:9,ExclusiveFullScreen. Wynikowa DLL:
`b7247a256195d67d51bb91c8db3c8aa02b0270e8147127ae1e7c906d8ea53d55`.
`shipping-validation.json` obejmuje nowy port16386stanów i regresje
task100/2,100/1,world5388,busyworld5088,busyactor9984,live10827+130planowań,
restore7704 iUIreplace7248.275plików projektu zamrożono przed buildem.

PlayerQA przez Wine11/Xvfb jest regresją dotychczasowego normalnego sterowania,
nie demonstracją100/2 w świecie Unity. Warianty floty przed i po statkach
mają po30checkpointów,90stanów aktorów,300części,1020odczytów kolejki,
229publikacji i12pakietów;exit0. Sprawdzają również blokadę Shift, Ctrl-recall
i odbiór dwóch rozkazów z25 w26. Raporty: `player-first/last/report.json`.
Znany ComputeBufferGC przy zamknięciu i komunikaty headlessALSA/debuggera
pozostają oddzielne od0warnings/0errors w BuildReport. Nie mierzono wydajności.

Runtime nadal ma73C# i131unikalnych meta:1C# zmieniony,72pozostałe bez zmian.
78plików Resources,10stagingów i9oryginalnych wejść pozostają zachowane.
Brak nowych PNG, ZIP, podglądów, publikacji, aplikacji konfiguracji lub agentów.

W zweryfikowanym zakresie kod jest zgodny z istniejącym `SingleStepClock`
i nie narusza deterministycznego stanu. Nowe wyniki są odtwarzalne z jawnych
wejść i porównane z x86. Nie jest to potwierdzenie pełnego remake’u,
oprawy2026, pełnegoLife/AI, natywnegoWindows11 lub docelowego laptopa.
Shift, queuedWorld,300/311,raport40 i zwykły Start pozostają kolejnymi etapami.
