# Grupy1/2 po ponownym wyborze a zweryfikowany ruch

Stan: 2026-11-03. Uzupełnienie
[dowodu membership0](WORLD_MEMBERSHIP_MOVEMENT_EVIDENCE.md) i
[modelu wyboru/poleceń](WORLD_POINTER_COMMANDS.md).
Nowe testy wykonują instrukcje oryginalnego EXE, bez zmian zamrożonego C#
ani wcześniejszego native WorkOracle.

## Sprzężona konsumpcja komendy i ruch

[Probe](../artifacts/world-input/commands/group-positive-motion/probe_clear_reselect.py)
wykonuje bazowy handler ShipGetMessage/action41, następnie normalne action20,
promocję, Work, planery, MoveShip i idle. Grupa UI+5c jest jawnym wejściem
z osobno potwierdzonego producenta Fleet. Grupa symulacji+5e zmienia się
przez rzeczywisty konsument41, instrukcją50ca16.

[Raport](../artifacts/world-input/commands/group-positive-motion/native-positive-groups-clear-reselect.json)
zawiera8 przypadków,1309 stanów i1288 Tick.
Porównano requester−1/7 statycznych peerów0/byte255 ze źródłowymi
grupami1 albo2 przy7 peerach−1/byte0. Wykonane trasy to pojedynczy rozkaz18,5
oraz dwa kolejne rozkazy18,5→16,4 po dojściu i pierwszej publikacji idle.

Wszystkie6 porównań daje identyczne raportowane pola symulacji, pełne ścieżki,
cache, RNG, uporządkowane publikacje sprite'a, zapisy siatki i każdą komórkę
map wejściowych wszystkich wywołań planera. Pojedynczy rozkaz ma103 stany,
101 Tick i3 wejścia planera; dwa rozkazy mają200 stanów,197 Tick i5 wejść.
Pola UI/simulation group różnią się zgodnie z deklarowanym kontekstem.
Wyłączono je z porównania, podobnie jak dodatkowe obserwacje handlera41.

Najsilniejszy wariant odtwarza także kolejność po anulowaniu i ponownym wyborze:

1. Counter0: rzeczywiste41 zapisuje5e FFFF→0001.
2. Counter101, po pierwszym idle:41 usuwa grupę0001→FFFF.
3. Ten sam counter101: następne41 ustawiaFFFF→0002.
4. Ten sam counter101: action20 żąda16,4. Nie ma Tick pomiędzy trzema pakietami.

Wynik nadal odpowiada referencji we wszystkich porównanych polach i mapach.
[Niezależny verifier](../artifacts/world-input/commands/group-positive-motion/verify_clear_reselect.py)
oraz jego [raport](../artifacts/world-input/commands/group-positive-motion/clear-reselect-independent-verification.json)
sprawdzają identyczność danych, priorytet0 we wszystkich1309 stanach,
adres50ca16, rozmiar word i offset+5e rzeczywistych zapisów członkostwa.

## Wszystkie576 początkowych celów

[Osobny probe](../artifacts/world-input/commands/group-map-equivalence/probe_positive_groups_bounded_hooks.py)
uruchamia rzeczywiste normalne planery dla każdej komórki24×24, od16,2,
w trzech kontekstach: requester−1/peerzy0, requester1/peerzy−1,
requester2/peerzy−1. Peerów jest7 i pozostają nieruchomi.
Promień celu wynosi0 dla przechodniego albo1 dla blokowanego pola,
zgodnie z rzeczywistym4999e0. Heap i cache izolowanego oracla są resetowane
przed każdym celem; normalne instrukcje planera pozostają wykonane.

[Raport](../artifacts/world-input/commands/group-map-equivalence/native-positive-groups-all576-bounded-hooks.json)
potwierdza wszystkie1152 porównania grup dodatnich z referencją.
Równość obejmuje9 pól: wybór planera nearest, liczbę punktów, cały pathhex,
całe input/working mapy, rezultat zasięgu, RNG po planowaniu,
cache przeszkód oraz kolejność wejść planera.
Nowo wykonana referencja−1/0 jest również identyczna dla wszystkich576 celów
z wcześniejszą referencją
[raportu grupy0](../artifacts/world-input/commands/group-map-equivalence/native-all576.json).

W tym teście usuwany jest wyłącznie nowy hook obserwacyjny dodany dla danego
celu przez istniejący `planner.run_case`, po skopiowaniu jego rezultatu.
Zapobiega to akumulacji callbacków przy ponownym użyciu oracla.
Żaden hook pierwotnej inicjalizacji/heap/renderowania ani instrukcja
oryginału nie są zmieniane. [Niezależny raport porównania](../artifacts/world-input/commands/group-map-equivalence/positive-groups-independent-verification.json)
i [manifest](../artifacts/world-input/commands/group-map-equivalence/positive-groups-evidence-manifest.json)
wiążą wynik z niezmienionym planerem, bootstrapem, flagami mapy i referencją0.
Pierwotny, wolniejszy test z akumulującymi się observerami również ukończył
wszystkie576 celów. [Porównanie obu harnessów](../artifacts/world-input/commands/group-map-equivalence/observer-harness-comparison.json)
potwierdza identyczność pełnych rekordów każdego celu, obu grup i promienia.
[Dodatkowy manifest](../artifacts/world-input/commands/group-map-equivalence/completed-observer-comparison-manifest.json)
zachowuje jego oryginalny skrypt, log i wynik; usuwanie observerów nie zmieniło
otrzymanych danych.

## Granice

Dowód dotyczy zdrowego source0b, opisanych dwóch tras i7 nieruchomych peerów
o grupie−1. Zachowuje wcześniejsze jawne granice inicjalizacji, heap,
renderowania, visibility i arrival notification. Nie potwierdza pełnej misji,
Life/FleetLife/AI, współbieżnego ruchu innych statków ani wspólnej grupy
requestera i peera. Nie uzasadnia traktowania requester0/peer0 jako profilu
różnych grup: poprzedni dowód wykazał tam inne mapy i cache.

Komendy i model domeny mogą zachować rosnący indeks grupy, ale przedstawiony
tu bezpośredni replay i porównania planowania obejmują wyłącznie grupy0/1/2.
Pełny replay Work dotyczy dwóch opisanych tras; macierz576 celów dotyczy
planowania początkowego, bez twierdzenia o wszystkich późniejszych fazach Life.
Wcześniejsze raporty pozostają osobnymi, niezmienionymi dowodami.
