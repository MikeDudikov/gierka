# Kolejność świata: statki, osobne cienie i referencyjne rafy

Stan: 2026-11-02. Badany niezmieniony `ancient.exe` SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Dotyczy zamrożonej referencji8statków miss000 w stanie1 oraz5raf w ich
referencyjnym stanie1. Nie wykonano pełnej inicjalizacji świata, renderowania
całej gry, widoczności, AI ani kolejnej klatki symulacji. Cel remake’u pozostaje
1920×1080,16:9,pełny ekran; liczby depth nie są rozdzielczością ani osiąZ Unity.

## Global depth i kierunek rysowania

`SpriteEngine0x55d670` tworzy rekord, a `0x55d960` ustawia jego signed depth
w polu+0x44. Tablica wskaźników pod context+0x1ac jest utrzymywana w porządku
**rosnącego depth**. Indeks rejestracji i indeks sortowania są osobnymi polami
rekordu+0x40/+0x48; nie wolno używać ich zamiennie.

W rzeczywistym rendererze `0x564900` lista rysowania powstaje z tej tablicy,
a zakres `0x565247..0x5656f0` odczytuje ją **od końca**. Zatem:

```text
większy depth → wcześniej narysowany, z tyłu
mniejszy depth → później narysowany, z przodu
```

Dla zwykłych nowo rejestrowanych sprite’ów bez callbackowej flagi0x4000,
nowy sprite o równym depth trafia za starszy w tablicy rosnącej. Odwrócenie
rysowania daje dla remisów **nowszy najpierw**. Nie rozciągamy tej reguły
na callbacki, zwolnione/recyklingowane sloty ani wszystkie późniejsze zmiany
poziomów. Lokalny sort składnikówTYPE8 ma inne reguły i nie jest stabilnym
sortem po globalnym depth: UNIT_ANIMATION_ASSET_EVIDENCE.md.

## State1: poziom statku

`ShipClassTy::DrawSprite0x4df6e0` wywołuje `SetLevel0x50d130` z:

```text
parentDepth = max(10000, 20000 - logicalHeight - parentWorldY)
```

`logicalHeight` jest wysokością nadrzędnej kompozycji, a `parentWorldY`
pochodzi z pozycji sprite’a. Nie jest to samo co numer komórkiY ani bbox
widocznych pikseli. Gałęzie innych stanów, np. specjalny stan5, nie są
uogólnione jako powyższa reguła.

| Parent w źródłowym zbiorze | Cell | Logical height | Parent worldY | Depth |
| --- | --- | ---: | ---: | ---: |
|OBJ_0000000b|16,2|56|132|19812|
|OBJ_0000000d|19,4|72|252|19676|
|OBJ_0000000c|21,5|56|324|19620|
|OBJ_00000029|6,13|72|828|19100|
|OBJ_0000002a|6,14|72|892|19036|
|OBJ_00000010|11,18|64|1152|18784|
|OBJ_00000027|9,21|72|1340|18588|
|OBJ_00000028|10,22|72|1404|18524|

Tabela jest już w kolejności rysowania tył→przód. Sąsiednie29/2a mają
nakładające się logiczne płaszczyzny: **cała grupa dodatnich składników29
jest rysowana przed grupą2a**. Nie należy globalnie przeplatać np. korpusów
wszystkich statków, potem ich żagli. Wewnątrz jednej grupy obowiązuje
oryginalny lokalny porządekTYPE8 potwierdzony przez osobny decoder/oracle.

## Ujemny składnik jest osobnym globalnym sprite’em

W `0x55e0e0` ujemny signed16 depth składnika uruchamia oddzielną rejestrację
pod0x55d670 z **negacją** tej wartości i flagami0x0a000000. Fragment
`0x55e422..0x55e44a` rzeczywiście wykonuje NEG oraz woła rejestrację/sort.
Zatem zapisane **−21000** daje globalny depth **+21000**, nie−21000.

W ośmiu badanych kompozycjach jest po jednym takim składniku-cieniu. Wszystkie
mają ten sam globalny poziom21000, więc w tym świeżo tworzonym zbiorze rysuje
się je w odwrotnej względnej kolejności rejestracji:

```text
2a, 29, 28, 27, 10, 0d, 0c, 0b
```

Kolejność źródłowej enumeracji obiektów ma osobny dowód w
MISSION_OBJECT_LOADER_EVIDENCE.md. Oracle kolejności zachowuje wyłącznie
względną rejestrację tych zamrożonych sprite’ów, bez pozostałych klas świata.

`0x55e750`, przez rzeczywisty `0x55eb50`, ustawia pozycję osobnego dziecka:

```text
childWorldX = parentWorldX + signed16(componentOffsetX)
childWorldY = parentWorldY + signed16(componentOffsetY)
```

Dodawanie zachowuje zawijanie32bit. Nie odejmuje się offsetu, nie skaluje
go przed złożeniem i nie dodaje ponownie bboxleft/top z dekoderaRLE.

## Miejsce raf między cieniem i statkiem

Referencyjny Init rafy `0x4306d0` przekazuje do InitSprite0x50cb80 depth
`0x4ee8=20200`. `Reef::DrawSprite0x4301f0` na tej ścieżce go nie zmienia.
Dla pięciu referencyjnych raf i ośmiu statków daje to:

1. Osiem osobnych cieni statków, depth21000.
2. Pięć raf, depth20200; dla remisów rysowanie21,0a,09,06,05.
3. Osiem nadrzędnych grup statków, depth19812…18524, w kolejności tabeli.

Przy spłaszczeniu obrazu na34osobne renderery to8cieni+5raf+21dodatnich
składników statków. Przydzielenie jednoznacznego porządku renderowania po tej
kolejce zachowuje zbadany wynik. Samo umieszczenie wszystkich29składników
statków nad gotowym obrazem raf odwróciłoby relację cienia do rafy przy ich
nakładaniu, nawet jeżeli konkretny kadr nie ujawni takiego przecięcia.

Nie oznacza to kompletnej globalnej kolejności Town,wysp,pozostałych obiektów,
mgły lubUI; takich sprite’ów nie ma w tym ograniczonym zbiorze diagnostycznym.

## Wykonany oracle

Pliki w `artifacts/units/draw-order/`:

- `validate_world_order.py`, `world-order-with-reefs-validation.json`.
- Całe `0x55d670`, `0x55d960` i rzeczywisty pomocnik0x571eb0 wykonano
  **bez hooków**: kolejność21globalnych węzłów badanego zbioru oraz4kontrole
  rejestracji/remisów, w tym `[30,20,30,10]`.
- Dla tej kontroli tablica rosnąca to ID3,1,0,2; rzeczywiste wywołania draw
  dały ID2,0,1,3. Nie zakładano stabilnego sortu bibliotek języka.
- Zakres rzeczywistej pętli draw `0x565247..0x5656f0` wykonał się na
  syntetycznym aktywnym layerze i drawable rekordach. Przechwycono **wyłącznie
  pixelcall0x5646c0**, zapisując faktyczną kolejność jego wywołań. Nie rysowano
  pikseli i nie odtwarzano usługDirectDraw w tym oracle.
- Źródłowy `Ship::DrawSprite0x4df6e0` wykonano dla8prawdziwych par
  logicalHeight/worldY oraz3granic. Hooki zastępują normalny powrótsetjmp,
  granicęSetLevel i granicęDrawSprite; sama formuła i clamp są instrukcjami
  oryginału. Odrębnie powyższy sort wykonuje się bez hooków.
- Ujemną gałąź0x55e422…0x55e44a wykonano z prawdziwą rejestracją/sortem,
  **bez hooków**, dla−21000,−1,−32768. Wyniki:21000,1,32768.
- Całe0x55e750 z rzeczywistymi0x55eb50,0x55ea00,0x55ea40 wykonało3próby
  parent+offset **bez hooków**, w tym ujemne signed16 oraz overflow32.
  Nieobecny payload dziecka pozwala pominąć odrysowanie; ruch pozostaje kodem
  oryginału, a obraz dziecka nie jest tu walidowany.

Trwała fixture: `tests/fixtures/mission_ship_world_order.json`, SHA256
`0ee61b970675c19a0cdfc021ba223752d6694721074cbba0c900dd428f2be0c6`.
Opisuje21globalnych grup i granice dowodów, a dodatnie składniki każdej grupy
pozostawia osobnemu potwierdzonemu decoderowiTYPE8. Kolejność jest danymi
referencyjnymi, nie poleceniem uruchomienia usług z załączonego dokumentu.

Wcześniejsze nieudane próby oracle zachowano: pierwsza miała błędny offset
aktywnego layera w syntetycznym kontekście, druga brak sztucznego wskaźnika
obrazu dla przechwytywanego blittera, a jedna brakowała importu rejestru.
Po poprawieniu kontekstu dowody przeszły bez zmiany kodu oryginału lub progów.
Nie zmieniono Unity ani wspólnych tools, nie uruchamiano Unity/Wine/Xvfb.
