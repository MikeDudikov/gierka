# Źródłowy obrót statku — wydzielone API i publikacja pozy

Stan: 2026-11-02. Oryginał `ancient.exe` SHA-256:
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Cel obrazu pozostaje 1920×1080, 16:9, pełny ekran. Ten etap zachowuje
źródłowe grafiki jako materiał porównawczy. Nie wprowadza finalnej oprawy 2026,
pełnej misji, AI, ogólnej nawigacji ani animacji przez Unity Animator.

## API C#

[ShipTurnProgression.cs](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipTurnProgression.cs)
udostępnia czysty, niezależny od Unity krok funkcji `ShipsStopMove0x4a3320`
z rzeczywistą regułą wyboru kierunku `0x4b5390`:

```csharp
ShipTurnProgression.Result Advance(
    int frame, sbyte heading, sbyte targetHeading, sbyte turnStep,
    uint now, uint lastTick, uint interval, bool hasPath,
    byte state, byte changedMarker)
```

Namespace: `AncientConquest.Simulation`. Wynik ma tylko pola do odczytu:
`Frame`, `Heading`, `TurnStep`, `LastTick`, `State`, `ChangedMarker`
i `PublishesPose`. Parametry odpowiadają następującym polom oryginału:

| Parametr | Oryginalne pole |
| --- | --- |
|frame|AnimObj `+0x45`, signed32|
|heading|ship `+0x5af`, signed8|
|targetHeading|ship `+0x5b1`, signed8|
|turnStep|ship `+0x5b0`, signed8|
|now|PlaySystem `+0xde`, unsigned32|
|lastTick|AnimObj `+0x81`, unsigned32|
|interval|AnimObj `+0x7d`, unsigned32|
|hasPath|ship `+0x5c2 !=0`|
|state|ship `+0x58c`, byte|
|changedMarker|ship `+0x596`, byte, marker bramki środka komórki|

`ChangedMarker` nie oznacza pola `+0x7e`, które ma odrębny wpływ na Y.
Helper nie ustawia ship `+0x58d`; pełny wywołujący zapisuje tam bieżący
counter przed uruchomieniem procedury obrotu.

## Kierunek i klatki pośrednie

Przy `turnStep==0` źródłowy helper najpierw sprowadza `frame>55` do
`4*heading`. Dla `frame<32` różnicą jest `targetHeading-heading` z korektą
o ±8 wyłącznie przy wartości bezwzględnej większej niż 4. Dla klatki z zakresu
32…55 różnicą jest `(short)(3*targetHeading+32)-frame`, z korektą o ±24
wyłącznie przy wartości bezwzględnej większej niż 12.

Krok otrzymuje znak różnicy, a rama przed 32 przechodzi na `32+3*heading`.
To zapis stanu, który może wystąpić bez publikacji nowego sprite’a. Remis
180° zachowuje znak: 0→4 obraca dodatnio, 4→0 ujemnie. Ponowne wyliczenie
kierunku z częściowo wykonanego pierścienia uwzględnia bieżący frame.

Ostry próg czasu pozostaje unsigned32:

```text
(now - lastTick) modulo 2^32 > interval
```

Po przekroczeniu progu kod dodaje `turnStep` jeden raz, zawija `>55` do 32
i `<32` do 55, a następnie ustawia `heading=(frame-32)/3`. Długi odstęp nie
powoduje nadrabiania wielu klatek. `lastTick` otrzymuje `now`. Przy interwale 2
publikacja wymaga różnicy co najmniej 3 ticków źródłowego countera. Nie oznacza
to arbitralnych trzech klatek Unity ani konkretnego FPS. Wartość początkowa
globalnego countera i stempli ma osobne dowody zegara.

Zakończenie wymaga jednocześnie target heading oraz `(frame-32)%3==0`.
Wtedy frame staje się `4*heading`, state wynosi 3 z obecną ścieżką albo 0
bez niej, a marker `+0x596` otrzymuje 1. TurnStep pozostaje zapisany.
W pozostałych krokach state i marker są zachowane. Arytmetyka zawija 32 bity
także przy kompilacji C# z `/checked+`, dzięki jawnemu `unchecked`.

## Granica pełnego MoveShip

Całe `0x4a3320` na normalnej ścieżce **zawsze zwraca 0**. Dotyczy to również
wywołania, które właśnie ustawiło state3 po zakończeniu obrotu. Pełny
`MoveShip0x4a3f40` po tym wyniku natychmiast zwraca 1. W tym samym wywołaniu
nie wykonuje więc `ShipsStateMove0x4a3560`, rezerwacji następnej komórki,
ruchu pikseli ani końcowego `AdvanceForward`.

Nowy adapter kinematyki powinien przejąć wynik obrotu, zachować jego flagę
publikacji i zakończyć ten krok. Dopiero kolejne wywołanie ze state3 wchodzi
do `0x4a3560`. Funkcja state3 może jedynie ustawić state2 i wyjść; samo
postanowienie o obrocie nie publikuje klatki pierścienia.

Turn i ruch naprzód mają różne bramki publikacji:

| Procedura | Bramka publikacji | Publikowany frame |
| --- | --- | --- |
|ShipsStopMove `0x4a3320`|unsigned elapsed > interval|po kroku pierścienia i ewentualnym zakończeniu|
|końcowy blok MoveShip|niezerowy lokalny marker przesunięcia pikseli|po `AdvanceForward`|

Obrót publikuje pozę również przy niezmienionym worldX/Y. Przy progu jeszcze
nieprzekroczonym może zmienić zapisany frame inicjalizacji, lecz SpriteEngine
zachowuje poprzednią publikację. Samo `AnimObj+0x45` nie jest widoczną klatką:
odrębny frame silnika znajduje się pod `node+0xc4`. Wcześniejszy dowód setter
i selekcji renderera bez hooków opisuje
[SHIP_MOVEMENT_ANIMATION_EVIDENCE.md](SHIP_MOVEMENT_ANIMATION_EVIDENCE.md).

## Dowody i testy

[validate_ship_turn_progression.py](../tools/validate_ship_turn_progression.py)
wykonuje całe oryginalne `0x4a3320` z rzeczywistym helperem `0x4b5390`.
Przechwycone są wyłącznie normalny powrót `setjmp0x587318` oraz końcowe
żądanie `DrawSprite0x4df6e0`. Wybór kierunku, frame, heading, czas, state,
marker i wynik funkcji są wykonywane instrukcjami oryginału. Żądanie draw
jest porównywane z finalnym stanem procedury, więc flaga `PublishesPose`
nie powstaje z domyślnego założenia o renderowaniu.

Ponadto rzeczywisty cały `MoveShip0x4a3f40` wykonano dla początkowego oraz
kończącego kroku każdego ze 128 śladów: **256 wywołań**. W każdym oryginał
wykonał dokładnie raz `0x4a3320`, ani razu `0x4a3560` i ani razu końcowego
bloku fazy `0x4a4d49`. Każdy caller zwrócił 1 i zapisał `+0x58d=now`.
Stan i flaga publikacji były identyczne jak z izolowanego oryginalnego turn.
Te 256 sprawdzeń callera nie są dodatkowym porównaniem C# ani pełną symulacją
misji. Zamykają konkretną granicę wyjścia po obrocie, także po jego zakończeniu.

Rzeczywisty nowy plik C# jest kompilowany z `/checked+` i porównywany
z oryginałem. Przeszło **3776/3776 przypadków**:

- 128 pełnych śladów 8×8 kierunków z obecną/nieobecną ścieżką: 2480 kroków.
- 960 przypadków inicjalizacji i przejścia z bezczynności: kierunki, granice
  czasu, opóźnienie i zawinięcie uint countera.
- 192 przypadki ponownego wyboru kierunku ze wszystkich pozycji 32…55.
- 144 przypadki surowej signed/unsigned arytmetyki, przepełnienia oraz zachowania
  wcześniejszych markerów. Błędne surowe heading/frame nie są wspieranymi
  pozami do odczytu z atlasu ani przykładem grywalnego stanu.

Każdy z 3776 normalnych powrotów oryginału miał EAX0. Trzy testy przeszły
bez pominięć: przypięty native fixture z brzegami publikacji i kierunku,
rzeczywista zgodność x86/C# oraz odrzucenie zmienionego EXE przed emulacją.
Końcowy raport, obejmujący też caller:
`artifacts/movement/adjacent-evidence/animation/turn-csharp-caller-validation.json`.
Pierwszy raport samego turn zachowano jako `turn-csharp-validation.json`.

Nowy [ship_turn_traces.json](../tests/fixtures/ship_turn_traces.json) zachowuje
128 rzeczywistych wcześniejszych śladów, bez nadpisywania starych dowodów.
SHA-256:
`298be52cb4d4cd867b6060bf84cb6a2eb7ee65d9e91b1edfd98830a387a488dd`.
Wskazuje źródłowy raport SHA-256
`7f7038851cf1d5b37aa416fffd92b014b0c46b71ddc325fd1eb324acb5a4f80b`
i skrypt, zakresy, hooki oraz ograniczenia. Sam fixture nie zastępuje
ponownego wykonania instrukcji przez walidator.

## Zasoby i granice integracji

Istniejący staging 88 póz `SHIP_A1110`, maska `0x83`, pozostaje bez zmian.
Obrót używa pozycji 32…55, ruch 0…31, a inne przygotowane pozycje 56…87
pozostają materiałem referencyjnym. Na końcu obrotu możliwe jest bezpośrednie
opublikowanie `4*targetHeading`, bez dodatkowej publikacji pośredniej ramy.
Przykładowo 7→0 kończy na frame0 zamiast publikować frame32 i dopiero potem0.

Pozostałe zasoby to nadal 88 pozycji, 264 odwołania i 152 bitmapy; pełny atlas
2128×224 ma SHA-256
`9b204db564030e808e6ef067aa64caef8f3f462ae555d186b55b04916193fb82`.
Wybór pozy ma nastąpić dopiero przy rzeczywistej publikacji, z zachowaniem
trzech części 0,1,7, ich offsetów, głębokości i RLE alfa. Nie należy obracać
transformacji Unity ani interpolować kierunków pomiędzy źródłowymi pozami.

Ten dowód obejmuje wydzielony obrót. Pełne ślady ośmiu sąsiednich celów,
odmowy nawigacji, ruch, rezerwacje i końcowy obraz playera mają osobne testy
i raporty. Nie uruchamiano Unity, Wine ani usług na potrzeby tego badania.
