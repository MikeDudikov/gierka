# Źródłowa bezczynność statku i generator losowy

Stan:2026-11-03. `ShipIdleProgression` przenosi normalny idle statku0b:
sprite mode `+0x25b=0`, zdrowa grafika, bez dodatkowej obsługi brzegu i bez
połączenia z drugim statkiem. **4232 wywołania rzeczywistego C# zgadzają się
z oryginalnym x86**. Obejmują32 ciągłe ślady po120 wywołań i392 granice/raw;
456 publikacji obrazu oraz56 rzeczywistych zwolnień komórki. Dodatkowo77
wykonań bloku inicjalizacji RNG i96 całych wywołań MoveShip potwierdza
kolejność oraz powrót z gałęzi state0. Cztery testy venv przeszły bez pominięć.

Źródła i pliki:

- [Czysty helper C#](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipIdleProgression.cs),
  [probe](../tests/fixtures/ShipIdleProgressionProbe.cs),
  [walidator](../tools/validate_ship_idle_progression.py),
  [testy](../tests/test_ship_idle_progression.py).
- [Fixture native](../tests/fixtures/ship_idle_progression.json):1461141 bajtów,
  SHA256 `4487780fd8cfd3367c7af2e920a41d3be7e4a2534f4e22837d773327d4df1fd4`.
- [Końcowy raport](../artifacts/order-cycle/idle/csharp-validation-frozen.json),
  [4 testy venv](../artifacts/order-cycle/idle/unittest-final.log),
  [kontrola systemowego Pythona](../artifacts/order-cycle/idle/system-python-tests-final.log).
- Oryginalny [idle4a3150](../artifacts/movement/animation/export-core/004a3150.c),
  [MoveShip](../artifacts/movement/kinematics/export-step/004a3f40.c),
  [message2](../artifacts/objects/position/export-human-messages/004dc630.c),
  [release](../artifacts/movement/kinematics/export-core/004a3970.c),
  [owner guard](../artifacts/movement/kinematics/export-core/004998a0.c).

## RNG od inicjalizacji do kolejnych wywołań

GameObj ctor `0x50b8f0` zeruje `ship+0x18`. Message2 handler statku nadpisuje
je w bloku `0x4dc6d9…0x4dc6ec`, przed wyborem trybu payloadu:

```text
shipRandomState = (sessionSeed * sourceInstanceId) modulo 2^32
sessionSeed = *(ship.app + 0x2ee5)
```

Dla `OBJ_0000000b` ID wynosi11. Oryginalne instrukcje pobrania wskaźnika,
odczytu i IMUL/store wykonano bez hooków dla77 par seed/ID, także z
przepełnieniem. Wynik porównano z faktycznym C# `InitialRandomState`.
To dowód konkretnego zapisu message2, nie wykonanie kompletnego Init
wszystkich obiektów świata. Tryb zapisu1 może następnie odtworzyć RNG z
payloadu `+0x2c` w `0x4e2180`; zapis/wczytywanie nie jest portowane tym helperem.

Sesyjny seed nie jest stałą. `miss000` nie zawiera `RND_INIT`; wcześniejszy
[proof pogody](SHIP_MOVEMENT_WEATHER_EVIDENCE.md) wykonał loader i wykazał
fallback z cached time aplikacji. [Proof zegara](SHIP_MOVEMENT_CLOCK_EVIDENCE.md)
odróżnia ten cached time od licznika kroków symulacji. Pole `app+0x18`,
`app+0x2ee5`, `weather+0x18` i `ship+0x18` mają różne role.

Jawny sessionSeed0 daje początkowy RNG0 dla0b zgodnie z tym wzorem. Jest
poprawnym kontrolowanym wejściem diagnostyki, nie uniwersalnym defaultem
nowej misji. Takie wejście musi być opisane osobno od kontrolowanego
wind0/heading5. Inne procedury statku także mogą zużywać jego RNG; helper
nie zastępuje ich i nie zeruje generatora po dojeździe lub nowym poleceniu.

## Każde state0 wykonuje krok RNG

Normalny `MoveShip0x4a3f40` przy state0 zapisuje `ship+0x58d=now`, wywołuje
`0x4a3150`, a po jego wyniku0 natychmiast zwraca1. W96 wykonanych kontrolach
callera osiągnięto dokładnie jeden idle, bez obrotu, state3 i forward-tail.
Nie wolno ponownie wykonać ogona ruchu po tym powrocie.

Idle wykonuje **jeden** krok PRNG przy każdym wywołaniu, również bez publikacji:

```text
randomState = randomState * 0x41c64e6d + 0x3039  (wrap uint32)
temporaryInterval = (randomState >> 16) % 7 + 15
publishes = uint32(now - lastTick) > temporaryInterval
```

Próg15…21 jest losowany ponownie na następnym wywołaniu. Nie jest czasem
wylosowanym raz po zakończeniu ruchu. Oryginalny interval sprite’a jest
zachowany i przywracany po procedurze; w scenie źródłowej wynosi2. Długi
odstęp czasu nadal daje najwyżej jedną publikację, bez nadrabiania klatek.
RNG nie jest wielokrotnie wywoływany według pendingSteps ani FPS Unity.

`ProcShipsWork` przy capability4000 ponownie dodaje active400. Usunięcie
rozkazu active80 nie wyłącza więc normalnych kolejnych wywołań MoveShip.
Pełny obieg poleceń ma osobny adapter; wcześniejsze zamrożenie po dojeździe
było granicą diagnostyki trasy, a nie zachowaniem źródłowej bezczynności.

## Publikacja poprzedza zmianę stored frame

Dla normalnej rodziny początek wynosi `byte((heading+14)*4)`, czyli dla
poprawnych heading0…7 zakresy56…59,60…63,…,84…87.
Po przekroczeniu progu procedura:

1. Dzieli dodatnią prędkość przez2 ze źródłowym integer division.
2. Jeżeli reservation≥0, żąda zwolnienia innej komórki niż bieżąca i ustawia
   reservation na−1. Dla bieżącej komórki nie wywołuje release.
3. Poprawia frame poniżej początku; dla frame powyżej końca odejmuje jeden
   i ustawia krok−1. Surowy błędny frame nie jest ogólnie clampowany do końca.
4. **Publikuje tę pozę.** W tym momencie lastTick ma jeszcze poprzednią wartość.
5. Zapisuje lastTick=now, dodaje signed frameStep do stored frame, następnie
   stosuje źródłowe reguły skrajnych pozycji i kierunku.
6. Przywraca wcześniejszy interval.

Skrajne obrazy powtarzają się:76,77,78,79,79,78,77,76,76. Przy heading5,
kontrolowanym RNG0 i kolejnych now0…119 oryginalne publikacje to:

| Counter | Published frame | Stored frame po powrocie |
| --- | --- | --- |
|16|76|77|
|34|77|78|
|52|78|79|
|70|79|79|
|87|79|78|
|105|78|77|

Już przy now0 RNG zmienia się0→12345 bez publikacji. Przy pierwszej
publikacji speed21907 zmienia się na10953, a reservation87 zostaje
zwolnione. Test sprawdza te wartości oraz old lastTick przy faktycznym draw.
Samo stored frame po powrocie nie jest poprawną wyrocznią widocznej klatki.

## Własność komórek i API

```csharp
uint rng = ShipIdleProgression.InitialRandomState(sessionSeed, sourceInstanceId);
var result = ShipIdleProgression.Advance(frame, heading, frameStep,
    now, lastTick, interval, rng, speed, reservedCellIndex, currentCellIndex);
```

Result udostępnia `Frame`(stored), `FrameStep`, `LastTick`, `Interval`,
`RandomState`, `Speed`, `ReservedCellIndex`, `ReleasedCellIndex`,
`PublishesPose` i `PublishedFrame`. Ostatnia właściwość jest znacząca
wyłącznie przy `PublishesPose=true`; caller zachowuje poprzednio widoczną
klatkę, gdy publikacji nie było. Nowy RNG należy zapisać zawsze.

`ReleasedCellIndex` oznacza **żądanie** źródłowego `4a3970`, nie gwarancję
wyczyszczenia cudzej komórki. `4998a0` porównuje identyczność właściciela
przed zapisaniem zera. Dodatkowa natywna kontrola z cudzym ownerem potwierdza
brak grid write, zachowanie cudzej komórki i bieżącego pola, mimo resetu
reservation do−1. Helper jest czysty; właściwy adapter wywołuje istniejący
release po referencji ownera i rejestruje tylko faktyczne mutacje siatki.
Połączenie z drugim statkiem `+0x8e6` wymaga osobnej obsługi i jest wykluczone.

`4a3800` to osobne sprzątanie sąsiednich zajęć, a nie krok RNG/idle. Nie jest
wywoływane zamiast warunkowego release powyżej. Koordynator poleceń powinien
zachować własne źródłowe wywołania cleanupu przy zatrzymaniu i zmianie stanu.

## Zakres wykonania i granice

Oryginalne `4a3150`, `4df6e0`, `4ba790`, `4a3970` i `4998a0` wykonują się
w całości. Bez hooków query/grid; pole wsparcia `+0x483=0` i link0 są jawnymi
warunkami normalnego statku referencyjnego. Hooki przechwytują normalny
setjmp oraz granice graficzne50d130/50d5f0. Draw depth/world/frame pochodzą
z oryginału, ale nie wykonano tu prawdziwego renderera i powierzchni pikseli.
Normalny atlas88 póz został sprawdzony w poprzednim etapie; te testy go nie
zmieniają i nie potwierdzają samodzielnie integracji Unity.

32 ślady obejmują wszystkie8 headingów i4 jawne seedy.192 pojedyncze
przypadki badają próg, wrap czasu, interval, rezerwacje i prędkość;200 raw
przypadków bada signed heading/frameStep i skrajne frame. Te surowe błędne
pozy nie są obsługiwanymi obrazami do wyświetlenia. Damaged/special mode5
ma inną rodzinę92+8*heading i pozostaje poza helperem oraz atlasem88.

Weryfikacja jest kompilowana z `/checked+`; źródłowe wrapy są jawnie
`unchecked`. Zmieniony EXE lub fixture jest odrzucany przed wykonaniem.
W systemowym Pythonie bez pefile dwa testy wykonania są poprawnie pomijane,
a dwa testy fixture/guard przechodzą. W przypiętym venv wszystkie4 przeszły.
Oryginał jest sprawdzany SHA256 przed i po analizie. Nie uruchamiano Unity,
Wine ani innych usług, nie tworzono podglądów lub ZIP i niczego nie publikowano.

Poprzedni [dowód animacji](SHIP_MOVEMENT_ANIMATION_EVIDENCE.md) miał8 śladów
idle po120 kroków;128 dotyczyło tam śladów obrotu. Nowy dowód rozszerza idle
na32 ślady, dodatkowe granice, init RNG i cały caller. Pełne Life, inne użycia
RNG, wejście OS, AI, walka i rzeczywisty czas gry wymagają osobnej integracji.
