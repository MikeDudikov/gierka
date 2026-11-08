# Port punktów i Work zadania 100/2 — 2026-11-04

Zaimplementowano ograniczony, czysty C# port100/2 w istniejącym właścicielu
zadania grupy. `ShipFleetMembership.Group` nadal ma dokładnie jeden obiekt
`ShipFleetNormalTask`; pole `Subtype` rozróżnia100/1 i100/2. Historyczna nazwa
klasy nie oznacza drugiego systemu zadań. Nie dodano komponentów Unity,
Update, zegara, ECS ani osobnego źródła członkostwa lub zajętości.

## Zakotwiczenie w oryginale

| Element portu | Funkcje oryginalnego PE32 |
| --- | --- |
| Utworzenie/zastąpienie i dopisanie pojedynczego punktu |4cf2c0,4cef80,4a1c60 |
| Deduplikacja w całej liście punktów |4ce6c0 |
| Rekord członka17B i jego cel/tryb |4ce8a0,4cea20 |
| Następny punkt oraz flaga końca, także dla trybów±2 |4ce7c0 |
| Zdarzenie310, indeks komórki w+10 |4a1700 |
| LIFO310 i filtr pojedynczego członka |4cf0b0,4cc590,4a0230 |
| Przebieg okresowy i cel pozostawiony po pierwszym rozkazie |4cf550 |
| Wybór pierwszego maksimum signed16 i porównanie z wave[-1] |4ceab0,4cebc7 |
| Malejąca fala, odrębna od dotychczasowego5578a0 |4a1e90,545db0,545960 |
| Pakiet20,9B z argumentem0 |4cf070,520c50 |

Oryginalny EXE ma SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Dotychczasowe65eksportów pozostają bez zmian. Dodatkowo wyeksportowano545960
i545db0 z istniejącego projektu Ghidra, readOnly/noanalysis. C i assembler
są w `artifacts/fleet-queued-port/source`, log zawiera
`QUEUED_WAVE_EXPORT_COMPLETE`. Komentarze portu wskazują odpowiednie adresy.

## Granice danych i kolejności

Pierwszy Shift zastępuje100/1, tworzy100/2 i emituje20 do tego samego celu
dla wszystkich statków. Dopisanie lub duplikat zmienia nagłówek, ale nie
emituje20. Zastąpienie i czyszczenie nie zerują wieku grupy. Nowa grupa
zaczyna od0 niezależnie od testowego zapisu do nieaktywnego slotu wektora.

`WorkQueuedTask` przyjmuje pełny rejestr, teren, licznik źródłowy, pending
i osobne słowo signed16 dla każdej alokacji fali, w kolejności członków grupy.
Nie ma domyślnego0 lub117.0 w korpusie55 odpowiada jawnie wyzerowanemu
izolowanemu backendowi próbnika.117 jest wejściem z ograniczonego pomiaru CRT,
nie stałą gry; ograniczenia pomiaru opisuje[QUEUED_CRT_CONTEXT.md](QUEUED_CRT_CONTEXT.md).

Zdarzenia310 są obsługiwane LIFO. Ich obsługa nie blokuje przebiegu
okresowego przy wieku>100, sprawdzanym przed dodaniem pending. Zachowano
przepełnienie uint32 oraz możliwość dwóch20 dla jednego statku w jednym Work,
z celem członka pozostawionym przy pierwszym rozkazie. Nie poprawiono OR
dopuszczającego indeks−1 ani signed16 w porównaniu.

`SourceWaveField.FillQueuedRoute` odwzorowuje545960: seed30006, kardynalne−6,
diagonalne−9, kolejnośćR/U/L/D/RU/LU/LD/RD, zapis tylko do zera, pierwszy
odwiedzający wygrywa. To osobne źródłowe jądro w istniejącym module, nie
zamiana algorytmu5578a0, nowy pathfinder lub współczesne wygładzanie trasy.

`ShipWorldStep` ma wyłącznie dodatkowy preflight dla nieobsługiwanego jeszcze
planowania100/2. Działa po niezmieniającym stanu `SingleStepClock.Begin`,
przed zmianą licznika i poczty. Rzeczywista kolejnośćPrepareMail/SendMail/
SystemLife, pozycja floty w rejestrze, pending1 iComplete40 pozostają bez zmian.
Kontrola odrzucenia porównuje cały obserwowany stan świata, aktorów i gridu.
Nie wywołujemy wszystkich grup przed statkami ani nie dodajemy drugiego flush.

## Walidacja i ograniczenia

`tools/validate_fleet_queued_port.py` oraz
`tests/fixtures/ShipFleetQueuedPortProbe.cs` porównują logiczną projekcję
korpusów55+5+4:64przypadki i1121stanów, dodatkowo36wierszy przygotowania
oddzielnych prób pamięci. Nagłówki, wiek, punkty, rekordy członków, całe
zdarzenia32B, członkostwoUI/symulacji, pakiety i wyniki600zapytań trasy
pochodzą z niezmienionych fixture x86. Testowy zapis wieku jest wyłącznie
odpowiednikiem oznaczonego wejścia pamięci próbnika; nie dodano settera gry.

Pomijane są nieprzenośne adresy/tokeny alokacji zadania i markerów, ich
tworzenie graficzne i renderowanie. Nie jest to dowód wyglądu znaczników.
Rejestracja100/2 jest informacją zadania, nie drugim członkostwem grupy.

Ponadto porównano20pełnych pól fali,11520signedwords, ze świeżym4a1e90:
mapa misji, otwarta, zablokowana i rozłączne wyspy, po5startów każda.
19kontroli API sprawdza jawny kontekst, odrzucenia bez zmiany stanu,
zastąpienie podtypów i różne słowa pamięci dla różnych statków.
Pięć mutacji rzeczywistego C# sprawdza deduplikację, LIFO, próg100,
signed16 i pozostawiony cel. Zmiany istnieją wyłącznie w plikach tymczasowych.

Build Windows64Mono w Unity6000.3.27f2:152975403B,0warnings/0errors,
1920×1080,16:9,ExclusiveFullScreen. Wynikowa Assembly-CSharp.dll:
`8ca1c3b4ccf48ac651a1f3662bc50da32004a0aae2406d1bfe5632e3e367d001`.
Wyniki porównań tej biblioteki są w
`artifacts/fleet-queued-port/shipping-validation.json`: nowy port/pola/bramka,
100/1(778stanów), własność grup(2486stanów), świat(5388stanów aktorów),
busyworld(5088), UIreplace(7248), restore(7704), livefleet(10827+130planowań).
275plików projektu zamrożono przed buildem i sprawdzono po nim.

4testyPASS/0skip w132.663s:3nowe testy portu i regresja1287przypadków
`SingleStepClock`. Świeże wykonania x86 odtwarzają wszystkie55+5+4fixture.
Discovery319testów;pełnego zestawu nie uruchamiano.

PlayerQA przez Wine11/Xvfb sprawdza zwykłe rozkazy zatwierdzonej grupy
podczas ruchu, FIFO odbioru w26 po dwóch żądaniach w25, odczyty renderowania,
Ctrl-recall oraz blokadę Shift. Każdy wariant po30checkpointów/90stanów
aktorów/300części/1020odczytów kolejki/229publikacji/12pakietów,exit0.
Nie uruchamia on nowego100/2 w świecie;to regresja dotychczasowej integracji.
Raporty końcowej DLL są w `player-final-first` i `player-final-last`;
wcześniejsze `player-fleet-first/last` dotyczą pierwszego builda.
Geometria okna1920×1080,x0/y0. Znany komunikat ComputeBufferGC przy zamknięciu
pozostaje;nie jest nowym ostrzeżeniem kompilacji. Brak urządzenia ALSA
w headless buildzie również odnotowano oddzielnie od wyniku BuildReport.

Zachowano logi początkowych błędów narzędzi: adapter nie pokazywał testowego
wieku25 z nieaktywnego slotu, a pierwszy mutant deduplikacji kończył się
ostrzeżeniem kompilatora o nieużytej zmiennej zamiast różnicą zachowania.
Poprawiono adapter i mutanta; nie zmieniano oczekiwań fixture ani oryginału.
Końcowy audyt skorygował wyłącznie komentarz4cf6f2 na dokładny zakres instrukcji
4cf6f3..4cf72c. Zachowanie C# pozostało identyczne, ale nowa kompilacja zmieniła
identyfikator DLL; dlatego ponowiono porównania wynikowej biblioteki i player QA.
Poprzednie raporty i logi zachowano jako first-build, a korektę wraz z SHA
przed/po zapisano w `source-comment-correction.json`.

UI Shift nadal zablokowane. World nie wykonuje100/2 bez jawnego kontekstu.
Edytowanie składu100/2,300/311, raport40, near-sentinel przy tworzeniu,
retained-only actor events, pełnyShip::Life/AI/Start pozostają poza zakresem.
Nie dowodzi to pełnego remake’u, oprawy2026, natywnegoWindows11, obsługi
docelowego laptopa lub jego wydajności. Bez nowych PNG, ZIP i podglądów.

W zweryfikowanym zakresie kod jest zgodny z istniejącym `SingleStepClock`
i nie narusza deterministycznego stanu: wejścia, kolejność i rezultaty
pozostają porównywalne z x86. To stwierdzenie dotyczy powyższych korpusów,
nie całej gry lub wszystkich możliwych historii sterty.

Następnie: dowód100/2 w świecie z rzeczywistą kolejnością rejestru/poczty,
jawnym kontekstem każdej fali i publikacją310 przez statki; dopiero potem
integracja i odblokowanie Shift. Nie publikować ani nie aplikować środowiska.
