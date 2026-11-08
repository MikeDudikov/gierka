# Animacja ruchu i obrotu statku — wydzielone dowody

Stan: 2026-11-02. Oryginał `ancient.exe` SHA-256:
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Badanie obejmuje wybrane funkcje `ShipClassTy`, bez uruchomienia pełnej gry.
Nie odtwarza całego sterowania, pathfindingu, kolizji ani zegara świata.
Cel remake’u pozostaje 1920×1080, 16:9, pełny ekran.

Wydzielony helper C# obrotu i późniejsze sprawdzenie 3776 przypadków opisuje
[SHIP_TURN_ANIMATION_EVIDENCE.md](SHIP_TURN_ANIMATION_EVIDENCE.md). Poniższy
zapis zachowuje wcześniejszy zakres badań animacji i ruchu w ustalonym kierunku.

## Zakresy klatek

Dane `SHIP_A1110` mają 152 klatki. Dla pełnego zdrowia i normalnej ścieżki
animacji statku badane funkcje korzystają z trzech różnych zakresów:

| Sytuacja | Źródło x86 | Klatki |
| --- | --- | --- |
| Ruch w ustalonym kierunku | `0x4a3f40`, końcowy blok `0x4a4d49` | `4*heading + phase`, phase 0…3, czyli 0…31 |
| Obrót do nowego kierunku | `ShipsStopMove0x4a3320` | pierścień 32…55, trzy pozycje na kierunek |
| Normalna bezczynność | `0x4a3150`, `object+0x25b !=5` | `56+4*heading`…`59+4*heading`, ping-pong |

**Samo 0…31 nie wystarcza do wiernego obrotu.** Ruch z obrotem wymaga 0…55,
a z normalną bezczynnością 0…87. Odrębne warianty animacji, m.in. dla
`object+0x25b ==5`, wychodzą poza ten podzbiór i nie są tu odtworzone.
Nazwa `ShipsStopMove` pochodzi z diagnostyki oryginału; funkcja rzeczywiście
zmienia heading i po zakończeniu wybiera stan zależny od obecności ścieżki.

## Faza ruchu i tempo

Niezmieniony blok `0x4a4d49..0x4a4d9f` sprawdza unsigned32:

```text
(now - lastStamp) modulo 2^32 > sprite.interval
```

Porównanie jest ostre. Źródłowe `interval=2` z `0x4e0160` daje przy kolejnych
tickach co 1 zmianę po 3 tickach, nie po 2. Wtedy frame zwiększa się raz,
po końcu czterech faz wraca do `4*heading`, a lastStamp otrzymuje now.
Opóźnienie o 100 ticków nadal daje jeden krok w jednym wywołaniu. Nie ma
nadrabiania klatek przez elapsed/interval ani zachowania reszty czasu.

`now` pochodzi z `game+0xde`, nie z czasu renderowania Unity. Powiązanie
wywołań Life z zegarem opisuje `SHIP_MOVEMENT_CLOCK_EVIDENCE.md`; ten zakres
nie ustanawia arbitralnego FPS lub FixedUpdate. Pozycja i zajętość komórek
muszą być odtworzone niezależnie od tego małego kroku animacji.

## Obrót

`0x4a3320` używa target heading pod `object+0x5b1`, bieżącego pod `+0x5af`
i znaku kroku pod `+0x5b0`. Przy zerowym kroku oryginalny helper `0x4b5390`
wybiera jego znak. Dla głównych kierunków skraca różnicę przez dodanie lub
odjęcie 8 tylko wtedy, gdy jej wartość bezwzględna przekracza 4. Remis 180°
zachowuje znak: 0→4 idzie dodatnio, 4→0 ujemnie. Przy trwającym obrocie helper
uwzględnia aktualny frame pierścienia, a nie sam zaokrąglony heading.
Jeśli frame był większy niż 55, helper najpierw przywraca `4*currentHeading`.

Z frame <32 funkcja wybiera `32+3*currentHeading`. Po spełnieniu ostrego progu
czasu dodaje ±1, zawija 55→32 lub 32→55 i ustawia `heading=(frame-32)/3`.
Zakończenie wymaga target heading oraz `(frame-32)%3 ==0`. Wtedy frame staje
się `4*targetHeading`, stan ruchu `+0x58c` wynosi 0 bez ścieżki albo 3 z nią,
a znacznik `+0x596` otrzymuje 1. Następnie lastStamp=now i kod żąda rysowania.
Nie zastępujemy klatki przejściowej głównym sprite’em po każdej zmianie heading.

Dla obrotu 5→4, interval 2 i lastStamp 0 procedura żąda rysowania:

| Tick | Frame | Heading | Stan przy obecnej ścieżce |
| --- | ---: | ---: | ---: |
|3|46|4|2|
|6|45|4|2|
|9|16|4|3|

To wynik izolowanego wywołania z jawnymi wejściami, nie zapis czasu pierwszej
misji w uruchomionym oryginale.

## Bezczynność i RNG

`0x4a3150` przy każdym wywołaniu aktualizuje RNG statku jako
`state=state*0x41c64e6d+0x3039`, z zawijaniem 32 bitów. Z górnych 16 bitów
wybiera tymczasowy próg `(upper16%7)+15`, czyli 15…21 ticków. RNG zmienia się
również wtedy, gdy próg animacji jeszcze nie minął. Funkcja na końcu przywraca
wcześniejszy interval sprite’a.

Zwykły zakres to `56+4*heading`…`59+4*heading`. Kod żąda rysowania przed
inkrementacją lub dekrementacją zapisanego frame. Skrajne pozycje są powtarzane,
np. 76,77,78,79,79,78,77,76,76. Wierny adapter musi rozróżniać drawnFrame
od stanu frame po zakończeniu procedury.

Dla heading 5 i jawnego RNG 0 ślad żądał: tick 16→76, 34→77, 52→78, 70→79,
87→79, 105→78. RNG 0 jest wejściem syntetycznym, nie ustalonym seedem startu
gry. Przy niezerowej prędkości pod `+0x59b` kod może też dzielić ją przez 2;
pełne hamowanie pozostaje osobnym zakresem kinematyki.

## Minimalne zasoby źródłowego statku 0b

Zestaw zachowuje type8 `SHIP_A1110`, pełne zdrowie, origin/owner (1,1)
i maskę `0x83`. W badanych funkcjach normalnego obrotu/ruchu zmienia się frame,
bez przeładowania deskryptora i bez nowej maski zależnej od heading. Nie dowodzi
to stałości maski po uszkodzeniu, zmianie wyposażenia, właściciela lub efektów.

Każda pozycja wybiera części 0,1,7: `BLB*` o depth −21000, kadłub o depth 10
i żagiel o depth 4. Wszystkie płaszczyzny oraz logiczne wymiary mają 56×56,
a offsety części 0,0. Globalny sort i pozycje: `UNIT_WORLD_ORDER_EVIDENCE.md`.
Nie dodajemy umownej alfy ani nowej barwy cienia.

| Pozycje | Unikalne bitmapy RLE | Bajty płaszczyzn RGBA |
| --- | ---: | ---: |
|0…31|48|602112|
|0…55|104|1304576|
|0…87|152|1906688|

Jednorzędowy atlas ostatniego zestawu miałby szerokość 8512 i przekroczyłby
obecny limit 8192. Wybrana siatka 38×4 pól zajmuje 2128×224 i mieści się w limicie.
Nie trzeba dodawać grafik pozostałych modeli. Nazwy, hashe i wybór części:
`artifacts/movement/animation/ship-a-poses-0-87.json`.

## Wykonane sprawdzenia

`artifacts/movement/animation/validate_ship_animation.py` wykonuje oryginalny kod:

- 128 pełnych śladów obrotu: 8×8 par heading, z obecną/nieobecną ścieżką.
  Wykonano `0x4a3320` i `0x4b5390`; hooki: normalny setjmp i zapis żądania
  DrawSprite. Nie przechwycono wyboru klatki, heading ani zakończenia.
- 224 przypadki fazy ruchu, bez hooków, `0x4a4d49..0x4a4d9f`: osiem kierunków,
  cztery fazy, granice czasu, opóźnione wywołanie i unsigned wrap licznika.
- 8 śladów bezczynności po 120 ticków: pełny `0x4a3150`, w tym LCG, próg,
  ping-pong i przywrócenie interwału. Hook DrawSprite zapisuje żądaną klatkę;
  zapytanie pomocnicze `0x4ba790` zwraca 0, aby wyłączyć odrębną obsługę
  komórki/rafy. Nie jest to pełna bezczynność w zapełnionym świecie.

Wszystkie przeszły. Raport: `ship-animation-validation.json` w tym katalogu.

`validate_ship_a_poses.py` wykonał cały oryginalny loader type8 i jego sort:
88 pozycji /264 wpisy komponentów zgadzają się z decoderem. Loader wykonał
456 wywołań źródłowego I/O dla pełnego deskryptora 152 pozycji; porównany
podzbiór obejmuje 0…87. Hooki opisano w `ship-a-poses-original-validation.json`;
sort pozostaje bez hooków.

`validate_ship_a_pose_pixels.py` wykonał oryginalny dispatcher RLE `0x574290`
dla wszystkich 152 unikalnych bitmap tego podzbioru. 868 buforów pikseli jest
dokładnie zgodnych: pełne bbox, fragmenty, seek wierszy, dwie wartości bufora
początkowego, stride i bajty ochronne. Nie przechwycono żadnej procedury
blittera. Raport: `ship-a-poses-rle-validation.json`. To porównanie indeksów
i pokrycia, nie framebuffer całej działającej gry.

EXE i OBJECTS.DKX/DKD są chronione pełnymi SHA-256 przed analizą zasobów.
Nie zmieniono oryginałów, Unity, wcześniejszego dekodera ani jego fixture.
Nie uruchamiano Wine, Editora lub usług. Kontroler Unity, pełny krok komórki,
wejście gracza, powiązanie czasu rzeczywistego i QA playera wymagają osobnych
dowodów. Grafika pozostaje źródłową referencją, nie finalną oprawą 2026.

## Wydzielone API C# i zasoby diagnostyczne

[ShipFrameProgression.cs](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipFrameProgression.cs)
udostępnia czyste API `AncientConquest.Simulation.ShipFrameProgression`:

```csharp
Result AdvanceForward(int frame, sbyte heading, uint now, uint lastTick, uint interval)
// Result.Frame : int; Result.LastTick : uint
```

Odwzorowuje wyłącznie blok fazy ruchu `0x4a4d49..0x4a4d9f`. Odejmowanie ticków,
inkrementacja frame i przesunięcia są jawnie `unchecked`. Porównanie elapsed
jest unsigned, a granicy frame signed. Przekroczenie `int.MaxValue` daje
`int.MinValue`; helper nie dopisuje ograniczeń dla błędnych surowych klatek.
Nie uruchamia bezczynności, obrotu ani logiki końca ruchu. Wywołujący musi
zachować źródłowy moment wywołania i rozróżnienie klatki żądanej do narysowania
od frame zapisanego na końcu kroku.

[validate_ship_frame_progression.py](../tools/validate_ship_frame_progression.py)
kompiluje rzeczywisty plik C# z `/checked+`, wykonuje oryginalny zakres x86 bez
hooków i porównuje oba wyniki. Przeszło 224 przypadków źródłowych faz oraz
64 przypadki surowej arytmetyki signed/unsigned, łącznie **288/288**. Dodatkowy
test odrzuca zmieniony EXE przed analizą. Raport:
`artifacts/movement/animation/ship-frame-progression-csharp-validation.json`.

[stage_ship_movement.py](../tools/stage_ship_movement.py) chroni pełnym SHA-256
siedem oryginalnych plików. Wybiera wyłącznie deskryptor `SHIP_A1110`, maskę
`0x83` i pozycje 0…87: **88 pozycji, 264 odniesienia, 152 unikalne bitmapy**.
Deskryptor ma dziewięć części źródłowych, z których maska wybiera 0,1,7.
Nazwy są odczytane z każdego rekordu, bez syntetyzowania przyrostków.
Wszystkie trzy części zachowują źródłowe offsety i depth; negative depth nie
jest łączony z kadłubem ani przeliczany na umowny cień.

Wygenerowany `Assets/Resources/ShipMovementGenerated/ShipMovementManifest.json`
zawiera pozycje, nazwy, source_index, logiczne rozmiary, bbox, flagi i hashe
każdej płaszczyzny oraz położenie na atlasie. `atlas_x/y` ma początek w lewym
dolnym rogu, zgodny z `Texture2D`; pierwszy rząd ma `atlas_y=168`, ostatni 0.
RGBA32 jest zapisane wierszami od dołu. `ShipMovementRgba.bytes` ma
**1 906 688 bajtów**, SHA-256
`9b204db564030e808e6ef067aa64caef8f3f462ae555d186b55b04916193fb82`.
Alfa wynika wyłącznie z pokrycia RLE. W tych zasobach 22 kryte piksele mają
indeks palety 6; nie mogą zostać usunięte przez kolorkey. Nie stwierdzono
krytych pikseli indeksu 0 w tym podzbiorze.

Nowy [ship_a_pose_selection.json](../tests/fixtures/ship_a_pose_selection.json)
przechowuje wyciąg rzeczywistych wyników oryginalnego loadera i metadanych
testu RLE, wraz z zakresami, hookami, ograniczeniami i hashami raportów.
Osobne Resources nie nadpisują poprzednich statycznych zasobów ośmiu statków.
Writer zachowuje domyślną nazwę manifestu wcześniejszego etapu; nowy etap
przekazuje jawnie `manifest_name="ShipMovementManifest.json"`.

Osiem testów stagingu przeszło bez pominięć: wszystkie pozycje i części wobec
natywnego fixture, bbox i flagi 152 bitmap, każdy wycinek atlasu wobec osobno
zdekodowanej bitmapy i palety, 22 kryte piksele indeksu 6, dokładne hashe oraz
orientacja wierszy. Sprawdzono też siedem blokad hashów źródeł, zachowanie
niezmienionych plików, jawne zastąpienie, kontrolę poprzednich hashów i odmowę
zapisu przez symlink. Łącznie nowy zakres ma **10 testów PASS**: dwa helpera
fazy i osiem stagingu. Dowody 288 porównań x86/C# są częścią pierwszego testu,
nie 288 osobnymi testami jednostkowymi.

Jest to materiał do wydzielonego, kontrolowanego kroku ruchu źródłowego statku
0b. Kinematyka, zegar, pogoda diagnostyczna i renderowanie playera mają osobne
dowody; sam atlas nie dowodzi grywalnej misji ani finalnej oprawy 2026.

## Publikacja klatki do SpriteEngine

W `MoveShip` inkrementacja fazy `0x4a4d49..0x4a4d9f` występuje **przed**
wywołaniem `DrawSprite` pod `0x4a4da9`. Wywołanie jest warunkowe: zmienna
`local_2c` musi być niezerowa. Samo przejście czasu i zmiana `AnimObj+0x45`
nie gwarantują publikacji nowej pozy do SpriteEngine.

`Ship::DrawSprite0x4df6e0` przekazuje aktualne frame i worldX/Y do
`0x50d5f0`, które wywołuje `0x55ec00`. Setter zapisuje frame w **oddzielnym**
rekordzie silnika `node+0xc4`. W tym rekordzie `+0xc0` to liczba trzech
wybranych części, `+0xc8` to 152 pozycje, a `+0xcc` wskazuje ich dane.
Rzeczywisty renderer pod `0x565686..0x5656c3` wybiera dane jako
`data + engineFrame * selectedParts * 10`. Nie odczytuje wtedy pola
`AnimObj+0x45`. Zatem widoczna poza zachowuje ostatnią opublikowaną klatkę,
gdy krok bez przesunięcia pikseli nie wywołał DrawSprite.

Dla kontrolowanej trasy `southwest_pending1`:

| Wywołanie | Zapisany frame | Poza wybrana przez renderer | Publikacja w tym kroku |
| --- | ---: | ---: | --- |
|0|20|20|stan początkowy|
|1|20|20|nie|
|3|21|20|nie|
|4|21|20|nie|
|5|21|21|tak|
|6|22|21|nie|
|29|21|21|tak|
|30|22|22|tak|
|44|22|22|tak|

Adapter rysowania ma więc zachować ostatnią publikację, a przy nowej
publikacji użyć fazy **po** AdvanceForward. Nie należy zawsze rysować fazy
sprzed inkrementacji ani bezwarunkowo podmieniać sprite’a po każdym ticku.
Pozostałe procedury, w szczególności bezczynność, mają osobny porządek
wywołań i nie przejmują tej reguły automatycznie.

[validate_ship_forward_publication.py](../tools/validate_ship_forward_publication.py)
odtwarza 45 wejść z przypiętego rzeczywistego śladu ruchu. Cały oryginalny
setter `0x55ec00` oraz wskazany fragment renderera wykonano **bez hooków**.
Węzeł jest syntetycznym aktywnym rekordem kompozycji bez flag natychmiastowego
rysowania; zakres kończy się przed pixelcall. To dowód wybranej pozy silnika,
nie screenshot ani pełny framebuffer oryginału. Native ślad ruchu ma nadal
własne opisane granice projekcji, widoczności i powiadomień.

Nowy [ship_forward_publication.json](../tests/fixtures/ship_forward_publication.json)
zawiera 45 wierszy z `stored_frame`, `drawn_frame`, flagą publikacji i pozycją
renderera. SHA-256:
`9567c1a18cd894892af9a97841ff5c73399a0b0030847a7a562a064b2f42b666`.
Źródłowy ślad `prepared_ship_movement.json` ma SHA-256
`28931c2849e05f46c7fd005c0f7b923f1d19bf26c045148a1a2388191cf2d374`.
Siedem oryginalnych plików jest chronionych hashami przed tym badaniem.
Jeden nowy test wykonuje cały porównany zakres 45 przypadków; przeszedł.
Raport: `artifacts/movement/animation/ship-forward-publication-tracked-validation.json`.

Przegląd integracji atlasu potwierdził zgodność kolejności: bajty bottom-up,
`Texture2D.LoadRawTextureData`, `Sprite.Create` z dolnym `atlas_y`, pełny rect
56×56, pivot `(0,1)` i pozycja świata `(x,-y)`. Nie ma ponownego dodania bbox
ani pionowego odwrócenia wybranego sprite’a. To przegląd kodu; końcowy obraz
playera pozostaje w zakresie osobnego QA.
