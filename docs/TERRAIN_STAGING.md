# Statyczny teren miss000 — odtworzenie ze źródłowych danych

Stan: 2026-11-02. Narzędzie `tools/stage_terrain.py` składa teren pierwszej
misji z oryginalnych danych `b_MAPA`, `b_ALIB` i `maplib`. Wynik jest
**referencją terenu**, bez rozgrywki, jednostek, UI, AI ani obiektów `OBJ_*`.
Pozostaje źródłowa grafika 64×64; nie jest to jeszcze oprawa jakości 2026.
Docelowy obraz remake’u to **1920×1080, 16:9, pełny ekran**. Świat terenu ma
1536×1536 pikseli; ta liczba nie ustala proporcji ekranu ani pola widzenia.

## Powtarzalny eksport

Z katalogu repozytorium:

```bash
.venv/bin/python tools/stage_terrain.py \
  --preview artifacts/terrain/reference \
  --lookup-proof artifacts/terrain/original-lookup
.venv/bin/python -m unittest tests.test_stage_terrain -v
```

Prywatne oryginalne wejścia znajdują się w
`reference/raw/ancient-conquest`. Pięć pełnych SHA-256 w narzędziu obejmuje
`ancient.exe`, parę `miss000` i parę `maplib`. Zmienione źródło przerywa
pracę. Oryginałów się nie modyfikuje; system operacyjny nie uruchamia EXE.
Opcjonalny dowód lookupu wykonuje wyłącznie wybrane instrukcje x86 w Unicorn.

Eksport identycznych danych nie zmienia plików ani ich czasu modyfikacji.
Zastąpienie zmienionego wygenerowanego wyniku wymaga jawnego
`--replace-generated` i poprawnych hashy wszystkich poprzednich payloadów.
Zmodyfikowany ręcznie payload lub symlink zostaje odrzucony. PNG warstw i
kopie raportów diagnostycznych w `artifacts/terrain` są odtwarzalnymi
podglądami. Pliki prywatnej grafiki w Resources są ignorowane przez Git.

## Kontrakt Unity Resources

Katalog: `Unity/AncientConquest/Assets/Resources/TerrainGenerated`.

| Plik | Kontrakt |
| --- | --- |
| `TerrainRgba.bytes` | 1536×1536, RGBA32, 9437184 bajty, wiersze od dołu do góry; kolor świata w bazowym stanie PALETTE |
| `MapPlanar.bytes` | Dokładne 9216 bajtów zdekompresowanego `b_MAPA`; 8 planarnych warstw uint16 little-endian |
| `TerrainManifest.json` | Geometria, źródła i hashe, paleta, 17 bibliotek, 264 klatki i ślad 1007 operacji rysowania |

Manifest ma `schema_version=1`, `mission=miss000`,
`native_canvas_width=1920`, `native_canvas_height=1080`,
`world_width_px=world_height_px=1536`,
`source_rgba_width=source_rgba_height=1536`,
`map_width_cells=map_height_cells=24`,
`tile_width=tile_height=64`, `layer_count=8`,
`format=RGBA32`, `row_order=bottom-to-top`.
`native_canvas_*` opisują kontrakt obrazu wynikowego, a nie źródłowe FOV.
`payloads` zawiera rozmiar i SHA-256 obu plików bytes.

SHA-256 `TerrainRgba.bytes`:
`f6606a33654577a9e19ec1a2e1f79d9ee6d3454cc49849d87d02d24ca43fde04`.
SHA-256 `MapPlanar.bytes`:
`931138965e7ff49641ff28e389a48104f113d66666badf6de027c8d6e716cfe3`.
Bufor RGBA w porządku górny→dolny, używany do PNG i śladu klatek, ma SHA
`fc3d2a19db9dabc77e9883dfdf5e86a96edc55233fe02c3d9501831e4ec71ee1`.

## Potwierdzone reguły

`0x5447b0` odbudowuje bibliotekę typu 16. Metadane mówią o 103 rekordach
po 211 bajtów. ID leży na +0, flagi na +1, prefiks NUL ASCII na +8,
typ rysowania na +40. Flaga ≥128 wyłącza ładowanie. Wskaźniki z pliku nie są
adresami zasobów w aktualnej pamięci. Oryginał nie zawiera zapisanych
wskaźników z flagą właściciela, które mogłyby zmienić wyszukiwanie aliasów.

Loader `0x544710` współdzieli tablicę wcześniej załadowanego właściciela
o **tym samym prefiksie i typie**. Formatter `0x5443e0` tworzy `%s%03d`,
czyli prefiks + `001`, `002`, …; pierwsza brakująca nazwa kończy tablicę.
Nie używa się zgadywanego sufiksu, nazwy deskryptora animacji typu 7 ani
zasobu o innym typie. Przykładowo prefiks `b_AMBER` nie ma podkreślenia.
Żadna z 17 aktywnych bibliotek miss000 nie wymaga aliasu, ale port obsługuje
regułę aliasów i testuje ją oddzielnie.

Odczyt mapy potwierdza `0x545190` i jego rzeczywisty łańcuch wywołań:

```text
offset = 2 * ((layer * height + y) * width + x)
word = uint16_le(map + offset)
selector = word & 255
selector == 0: nie rysuj, nawet gdy highbyte !=0
library_id = word >> 8     # ID, nie pozycja rekordu b_ALIB
frame_index = selector - 1
```

`MapaTy::DrawWholeMapa` pod 0x519b50 oraz redraw `0x51a0b0` iterują najpierw X,
potem Y. `DrawCellBig` pod 0x5196e0 rysuje warstwy 0…7 wewnątrz każdej komórki.
Eksport zachowuje tę kolejność. Aktywne liczby kolejnych warstw wynoszą
`576, 9, 132, 70, 85, 12, 41, 82`. Z 264 unikalnych wybranych klatek 87 to DIB
typu 1, 177 to sprite typu 6; wszystkie mają 64×64 piksele.

Typ 1 w dispatcherze `0x4e9370` trafia przez `0x562230` i `0x561ed0`
do `0x562700`: kopiuje indeksy **nieprzezroczyście**, również indeksy 0 i 6.
Kolor pochodzi z zainstalowanej palety świata, a nie z dowolnie wybranej
palety podglądu. W 264 klatkach zastosowano bazową `maplib:PALETTE`;
u wszystkich 87 DIB-ów każdy faktycznie użyty wpis ich własnej palety
także zgadza się z PALETTE. SHA RGB 256×3:
`41a0675766dab4d042bd802796139ed06259699033e0a5f8fdcc394971cd5270`.

Typ 6 trafia przez `0x562260` do `0x574290`/`0x574d50`. Pomija jedynie
przezroczyste przebiegi RLE. Zapisany indeks 0 jest nieprzezroczysty.
`left,top,width,height` sprite’a oznaczają wycinek zawartości, a nie pivot:
zdekodowaną pełną płaszczyznę 64×64 nakłada się na `(cellX*64,cellY*64)`
bez ponownego dodawania left/top. Użyte flagi 0x0480/0x0880/0x0c80/0x1080
określają tablice skoków wierszy; w tej ścieżce nie dodają tintu ani flipu.
Nieobsłużony wariant 0x0100 przerywa eksport zamiast zgadywać jego wygląd.

## Dowody i sprawdzenie

- `artifacts/terrain/code-export/`: eksport funkcji loadera, aliasów,
  formattera nazw i dostępu do mapy z Ghidra; wejściowy EXE jest hash-guarded.
- `artifacts/terrain/reference/terrain-static-base-palette.png`: pełny
  teren 1536×1536, obejrzany po wygenerowaniu. Brzegi, wyspy, lasy i ruiny
  składają się bez przesunięcia masek. `layer-0.png`…`layer-7.png`
  zachowują przezroczystość każdej warstwy. Manifest zawiera per-cell
  współrzędne, warstwę, ID, selektor, klatkę, pozycję i hash RGBA;
  metadane klatki zachowują źródłowy offset/hash payloadu i maski.
- `tests/fixtures/terrain_miss000_lookup.bin` oraz `.json`:
  **4608 odczytów + 6 granic** rzeczywistego `0x545190`, z wykonaniem
  `0x544fc0`, `0x544ba0`, `0x544c10`, `0x55b440`. Żadna funkcja lookupu
  nie jest przechwytywana. Runtime mapy i tablic klatek buduje narzędzie;
  sam loader nie jest wykonywany przez ten oracle. Każdy 5-bajtowy wiersz
  `<HhB` oznacza word, frameIndex (-1 pusto), drawingType (255 pusto), w kolejności
  X/Y/warstwa. Hash 23040 bajtów:
  `2c26432812ce2c1a4862c0b36f4d5716da972bb5d78e64298469b057ab0d018d`.
- Osobna walidacja renderera w
  `artifacts/binary-analysis/terrain-render/original-rle-validation.json`
  porównała 177 klatek × 6 = 1062 bufory z wykonywanym oryginalnym blitterem,
  bez hooków. `original-dib-validation.json` potwierdza 87 DIB-ów × 6 = 522 bufory;
  przechwycony jest wyłącznie systemowy IntersectRect. Obejmuje clipping,
  fragmenty wierszy, seeki i różne kolory początkowego bufora.
- Osiem testów stagingu sprawdza układ planarny, pomijanie pustego selektora,
  ID niezależne od ordinalu, dokładne nazwy/typy/luki/aliasy, nieprzezroczysty
  indeks 0, anchor sprite’a, paletę świata, hashe, orientację wierszy,
  idempotencję, guard zastępowania, wszystkie placements i fixture x86.

Referencja ustala statyczny skład terenu. Nie ustala animowanej palety,
oświetlenia, mgły, dynamicznego redraw, kamery gry ani setupu obiektów.
Nie porównano jej jeszcze ze zrzutem działającego oryginału. Wyświetlenie
w Unity przy 1920×1080 służy diagnostyce; nie oznacza gotowej pierwszej misji.


## Zweryfikowane wyświetlenie w Unity

Windows64 Mono z Unity6000.3.27f2 zbudowano bez błędów i ostrzeżeń:
`artifacts/terrain/build-report-final.json`, 143660987 bajtów. Jawny tryb
`--terrain-reference` wyświetla **jedną gotową kompozycję** TerrainRgba przez
SpriteRenderer i materiał URP2D Sprite-Unlit. Nie odtwarza rysowania ośmiu
warstw w runtime. Planarny parser C# jest sprawdzony osobno i w tym widoku
służy geometrii mapy; dowód dostępu do klatek nie oznacza podłączonego
resolvera bitmap ani symulacji.

Trzy osobne sesje pod Wine11/Xvfb potwierdziły pełny ekran 1920×1080 i trzy
wycinki gotowej referencji w diagnostycznej skali2×. Wszystkie zaakceptowane
obrazy mają błąd RGB0 i100% identycznych pikseli. Pierwszy blank capture w
origin0,0 został odrzucony przed dopasowaniem kolejnej klatki; zachowano obie
próby. Wszystkie sesje zakończyły się diagnostycznym wyjściem po8s z kodem0.
Raport: `artifacts/terrain/runtime-final/report.json`.

Pełny zestaw94testów przeszedł bez skip:
`artifacts/terrain/full-tests-terrain.txt`. Regresje na tym samym DLL również
przeszły: menu 27 etapów/5 obrazów/6 komend, briefing 39 etapów/11 obrazów,
normalny Quit0 w obu sesjach. Raporty:
`artifacts/terrain/menu-regression-final/report.json` oraz
`artifacts/terrain/briefing-regression-final/report.json`. Ten wynik potwierdza wyświetlenie statycznej
kompozycji. Nie zmienia ograniczeń kamery, gameplayu, oprawy2026 ani braku
sprawdzenia natywnego Windows11 i docelowego laptopa.


Sesje UI nadal logują znane ostrzeżenie `GarbageCollector disposing of ComputeBuffer`.
Identyczny komunikat występuje w logach poprzedniego etapu briefingu/menu;
nie jest nową regresją terenu. Jego przyczyna pozostaje do wyjaśnienia,
oddzielnie od przechodzącego buildu bez ostrzeżeń kompilacji.
