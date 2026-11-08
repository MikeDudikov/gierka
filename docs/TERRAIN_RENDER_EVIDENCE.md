# Renderer terenu — dowody z oryginału

Stan: 2026-11-02. Analiza niezmienionego `ancient.exe` oraz izolowane wykonanie
jego procedur x86. Potwierdzono indeksy i pokrycie wszystkich **264 klatek
terenu użytych przez miss000**: **87 DIB + 177 sprite’ów RLE**, łącznie
**1584 zgodne porównania buforów pikseli**. Nie jest to uruchomienie misji,
test całej gry ani porównanie gotowego kadru z działającym oryginałem.

Cel remake’u pozostaje **1920×1080, 16:9, pełny ekran**. Siatka źródłowa
1536×1536 px opisuje dane świata; nie wyznacza wielkości viewportu, powiększenia
kamery ani docelowej jakości nowej oprawy.

## Źródła i identyfikacja

Wszystkie adresy VA odnoszą się do ImageBase `0x400000`. SHA-256 EXE:
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Źródła znajdują się w `reference/raw/ancient-conquest/installed`.

| Plik | SHA-256 |
| --- | --- |
| `missions/maplib.dkx` | `05484166ca374630f7c29c26e561656a11941ef331fb014e52f72aed81c23650` |
| `missions/maplib.dkd` | `7fe0623d957e196e5279c6bced55db292648b5c9ebc6f1420fcd293c0685b685` |

Eksporty Ghidra z tej analizy: `artifacts/binary-analysis/terrain-render/export/`
i `export-blit/`. Skrypty `ExportTerrainRender.java` i `ExportTerrainBlit.java`
otwierają istniejący projekt z `-readOnly -noanalysis`. Wywołania loadera i
tablic klatek są też w `artifacts/terrain/code-export/`; wcześniejsze eksporty
mapy w `artifacts/binary-analysis/first-map/`.

## Wybór klatki z mapy

Szczegóły formatu planarnych warstw dokumentuje
[FIRST_MISSION_MAP_EVIDENCE.md](FIRST_MISSION_MAP_EVIDENCE.md).
Procedura `GetCellBitmap 0x545190` przyjmuje mapę, bibliotekę, x, y, warstwę,
wskaźnik bajtu typu oraz flagę błędu. Sprawdza granice x/y i warstwę 0…7.
Adres selektora względem payloadu bez ośmiobajtowego nagłówka runtime:

```text
offset = 2 * ((layer * height + y) * width + x)
selector = payload[offset]
libraryId = payload[offset + 1]
```

Zero w lowbyte oznacza pominięcie warstwy. Niezerowy highbyte nie znosi tej
reguły. `0x544fc0` przekazuje highbyte do `0x544ba0`, który porównuje go
z pierwszym bajtem rekordów biblioteki, co 211 bajtów. Nie jest to indeks
rekordu. Obie strony tego porównania są w oryginale typu `char`; zachowana
jest tożsamość wszystkich ośmiu bitów identyfikatora.

`0x544c10` wybiera `selector − 1` w odbudowanej tablicy klatek przez
`0x55b440` i zwraca typ rysowania z `record+40`. Brak biblioteki, klatki lub
wyjście poza mapę zwraca brak obrazu przy wyłączonym zgłaszaniu błędu.
Nie wolno odczytywać zapisanych w b_ALIB wskaźników jako adresów runtime.

`mfALibLoad 0x5447b0` odbudowuje wskaźnik pod `record+41`. Nazwy są tworzone
przez `0x5443e0` jako prefiks i trzy cyfry od **001**. Lookup zasobu używa
jednocześnie typu i dokładnej nazwy; pierwsza brakująca klatka kończy listę.
`0x544710` pozwala współdzielić wcześniej załadowaną listę dla tej samej nazwy
i typu. To źródłowa podstawa aliasów, nie dowolne przeszukiwanie podobnych nazw.

## Kolejność i położenie

| Procedura | Potwierdzona reguła |
| --- | --- |
| `0x519b50`, diagnostyka `MapaTy::DrawWholeMapa` | Pełny repaint: **X w pętli zewnętrznej, Y w wewnętrznej**. |
| `0x519a30`, `DrawCellMapa` | Przerysowuje komórkę tylko w bieżącym prostokącie widoku. |
| `0x519940`, `DrawCell` | W trybach 1/4 wywołuje `DrawCellBig`; tryby 2/3 mają osobną ścieżkę małej mapy. |
| `0x5196e0`, `DrawCellBig` | Dla jednej komórki rysuje kolejno **warstwy 0…7**, każdą w tym samym punkcie bazowym. |
| `0x51a0b0` | Pętle uzupełniania odsłoniętych obszarów po przesunięciu również używają X zewnętrznego i Y wewnętrznego. |

Nie jest to globalne rysowanie całej warstwy 0, a potem całej warstwy 1.
Kolejność pełnej kompozycji jest **X → Y → warstwa**.

`DrawCellBig` oblicza punkt bazowy:

```text
pixelX = (cellX − viewX) * tileSize + offsetX + frameX
pixelY = (cellY − viewY) * tileSize + offsetY + frameY
```

`InitMapaBig 0x51bcb0` ustawia tileSize=64. Między wyborem klatki a
`MSystemClassTy::AASPut 0x4e9370` nie ma dodatkowego przesunięcia per klatka.
Opcjonalny globalny przełącznik `DAT_005ca530` dodaje krawędzie siatki kolorem
0x14; nie jest to zawartość tekstur terenu.

## Typ 1: nieprzezroczysty DIB

`0x4e9370` dla typu 1 wywołuje `0x562230`, a ten `0x561ed0` z całym DIB-em.
Procedury sprawdzają blokadę powierzchni i przycinają prostokąt. W gałęzi
8-bitowej kopiowanie trafia do `0x562700` i jego surowych helperów
`0x575890` / `0x5758f0`.

Kopiowane są **wszystkie indeksy** w prostokącie, także zero. Nie przekazuje
się koloru klucza ani maski, nie ma testu przezroczystości po RGB. Uwzględnia
się wyrównany stride DIB, znak wysokości, granice źródła i celu. Dodatnia
wysokość DIB oznacza źródłowe wiersze zapisane od dołu; indeksowana płaszczyzna
używana w rekonstrukcji jest od góry.

W gałęzi 8→8 do istniejącej powierzchni kopiowane są indeksy; wpisana w źródłowy
DIB paleta nie zastępuje z tego powodu palety powierzchni. Dla rekonstrukcji
świata należy użyć potwierdzonej bazowej `PALETTE`. Osobna gałąź 16-bitowa
korzysta z tablicy konwersji powierzchni (`surface+0xb8`); jej prezentacja
sprzętowa nie była wykonywana przez poniższy probe.

## Typ 6: płótno, prostokąt i pokrycie RLE

`0x4e9370` przekazuje do `0x562260` pełne wymiary płótna z nagłówka sprite’a
oraz źródłowy prostokąt zaczynający się w (0,0). `0x562260`:

1. Dodaje offset powierzchni (`surface+0x10`, `+0x14`) do celu.
2. Ogranicza źródło do prostokąta `left,top,left+boxWidth,top+boxHeight`
   z signed shortów nagłówka +14,+16,+18,+20.
3. Przesuwa ten prostokąt do współrzędnych celu i przycina do granic
   powierzchni z `surface+0x80`.
4. Dla 8 bitów wywołuje `0x574290` z zerową tablicą translacji kolorów
   i pustą dodatkową maską. Dla 16 bitów używa `0x574f80` i tablicy konwersji.

W efekcie **left/top to położenie zapisanej zawartości w płótnie**, a nie
niezależny pivot, który trzeba drugi raz dodawać po odtworzeniu płótna.
Pełną płaszczyznę `width×height` zwracaną przez `decode_sprite` należy położyć
punktem (0,0) w bazowym punkcie komórki. Jej indeksy i maska zawierają już
przesunięcie `left/top`.

`0x574290` odczytuje `(sprite[0x0d] >> 1) & 0x0e` w celu pominięcia tabeli
pozycji wierszy; dla niższego źródłowego Y używa `0x572d40`. Przy pełnej
szerokości prostokąta, bez translacji i dodatkowej maski, wybiera `0x574d50`;
przy wycięciu poziomym `0x574e40`. W tej ścieżce nie znaleziono lustrzanego
odbicia, tintu ani klucza koloru odczytywanego z flag sprite’a.

Przezroczyste przebiegi RLE **pomijają zapis celu**. Przebiegi literalne
i powtarzane zapisują indeksy, także zero. Rekonstrukcja RGBA powinna więc
brać alfę z pokrycia RLE, niezależnie od indeksu/RGB. Wszystkie 177 użytych
sprite’ów mają flagi z grupy `0x0480/0x0880/0x0c80/0x1080`; nie występuje
w nich nadal nieobjaśniony wariant `0x0100` opisywany w
[SPRITE_FORMAT.md](SPRITE_FORMAT.md).

## Wykonanie niezmienionych instrukcji x86

Oba probe’y sprawdzają hash EXE, maplib i miss000 przed wykonaniem. Ładują oryginalne
instrukcje do Unicorn 2.1.4. Środowisko gospodarza nie wykonuje oryginalnego
programu Windows. Weryfikacja obejmuje wyłącznie jawnie wskazane procedury.

| Probe / entry point | Zakres | Wynik |
| --- | --- | --- |
| `probe_original_rle.py`, `0x574290` | 177 aktywnych klatek; pełne bbox, wycięcie poziome, seek wiersza 1/17, dwa różne wypełnienia celu, stride i bajty ochronne. **Bez przechwyconych callees**. | **1062/1062** zgodnych buforów |
| `probe_original_dib.py`, `0x562700` | 87 aktywnych DIB; cały obraz, wnętrze, przycięcie źródła i celu, orientacja wierszy, dwa wypełnienia, stride i bajty ochronne. Przechwycone tylko Windows `IntersectRect` z udokumentowaną arytmetyką prostokątów. | **522/522** zgodnych buforów |

Dwa różne wypełnienia celu pozwalają rozróżnić pominięcie zapisu od
zapisania piksela o wartości równej jednemu z wypełnień. Porównywany jest
cały bufor z marginesami, a nie wyłącznie widoczny podzbiór. Raporty zawierają
nazwy źródłowych klatek, hash każdego payloadu, prostokąty i hashe buforów:

- `artifacts/binary-analysis/terrain-render/original-rle-validation.json`
- `artifacts/binary-analysis/terrain-render/original-dib-validation.json`

Wśród sprawdzonych sprite’ów **48 klatek zawiera zapisany indeks zero**;
przypadki te potwierdzają jego nieprzezroczystość również wykonaniem x86.

Odtworzenie:

```sh
.venv/bin/python artifacts/binary-analysis/terrain-render/probe_original_rle.py
.venv/bin/python artifacts/binary-analysis/terrain-render/probe_original_dib.py
```

Probe’y potwierdzają dekodowane indeksy i pokrycie. Nie sprawdzają złożenia
wszystkich komórek przez działający renderer, blokowania DirectDraw,
konwersji 16-bitowej ani końcowego RGB wyświetlanego przez Windows.
Wykonane źródła DIB miały dodatnią wysokość 64×64 i osobny cel top-down
96×96. Inne znaki wysokości źródła, niewyrównane szerokości źródłowego DIB
i kopiowanie nakładających się buforów (`0x5758f0`) mają w tej analizie
dowód statyczny; nie były przypadkami wykonanego probe’a.

## Rzeczywisty parser C# a wynik oryginalnego accessora

`tools/validate_terrain_map_data.py` kompiluje rzeczywisty plik
`Runtime/TerrainMapData.cs` przez kompilator C# dołączony do Unity, z włączonym
`/checked+`. Probe to `tests/fixtures/TerrainMapDataProbe.cs`. Wszystkie
**4608 odwołań** (24×24×8) są zgodne z zamrożonym wynikiem wykonania
oryginalnego `GetCellBitmap 0x545190` i jego rzeczywistych callees:
**1007 aktywnych i 3601 pustych**. Generowanie fixture nie przechwytuje
żadnych funkcji; strukturę bibliotek/DArray przygotowuje narzędzie stagingu.
Oryginalny loader `mfALibLoad` nie jest częścią tego wykonania.

Wynik natywny ma format 5 bajtów na rekord: `<HhB`, czyli słowo mapy,
wybrany frameIndex (`−1` dla braku bitmapy) i typ rysowania (`255` dla braku).
Kolejność rekordów to X → Y → warstwa. Walidator sprawdza osobno:

- SHA-256 `terrain_miss000_lookup.bin`:
  `2c26432812ce2c1a4862c0b36f4d5716da972bb5d78e64298469b057ab0d018d`.
- Hash bajtów JSON proweniencji:
  `a7f6558d7ff68f01dad5e096fab5ae53999f298432fa2c1ee2be8f37d3774f44`.
- Hash rzeczywistego planarnego payloadu podanego do C#:
  `931138965e7ff49641ff28e389a48104f113d66666badf6de027c8d6e716cfe3`.
- Zgodność słów między planarnym payloadem a wszystkimi rekordami fixture,
  następnie wyników skompilowanej klasy C# z tym fixture.

Porównywane są słowo, frameIndex, obecność odwołania, bajt biblioteki i bajt
selektora. **Typ rysowania pozostaje wyłącznie informacją natywnego fixture**:
`TerrainMapData` nie rozwiązuje bibliotek ani bitmap, więc zgodność ich typu
nie jest przypisywana implementacji C#.

Osobne **44 sprawdzenia kontraktu C#** obejmują granice współrzędnych, w tym
int.MinValue/MaxValue, nieprawidłowe wymiary i długości payloadu, duże obliczenie
długości, niezmienność danych po mutacji tablicy wejściowej i graniczne bajty
ID/selektora. To defensywne reguły API, nie twierdzenie o równoważności
oryginałowi dla nieistniejących bibliotek lub uszkodzonych map.

Raport: `artifacts/binary-analysis/terrain-render/map-data-validation.json`.
Pięć testów w `tests/test_terrain_map_data.py` przeszło, w tym rzeczywista
kompilacja/wykonanie C# i odmowa akceptacji zmienionych bajtów native fixture,
proweniencji i źródłowej mapy.

```sh
.venv/bin/python tools/validate_terrain_map_data.py \
  --output artifacts/binary-analysis/terrain-render/map-data-validation-new.json
.venv/bin/python -m unittest tests.test_terrain_map_data -v
```

Ten walidator korzysta z zapisanego wyniku x86. Ponowne generowanie natywnego
wyniku i porównanie go z fixture jest osobnym testem w
`tests/test_stage_terrain.py`; nie jest automatycznie wykonywane przez
walidator C#.

## Paleta i granice tego etapu

Łańcuch załadowania bazowej `PALETTE` jest udokumentowany w
[WORLD_ASSET_REFERENCE.md](WORLD_ASSET_REFERENCE.md). Dla dużych kafli typu 1
używanych przez miss000 zapisane kolory użytych indeksów są zgodne z tą
paletą. Nie należy przenosić tego twierdzenia na dowolny mały kafel; wcześniejszy
audyt znalazł 21 małych DIB-ów z różnicą koloru 186.

`InitMapaBig` ładuje też `ANIM_PALETTE`. **Cykle palety, aktualizacje
czasowe, kolejność zmiany klatek i pełne RGB w ruchu nadal wymagają dowodu**.
Statyczny obraz w bazowej palecie nie dowodzi nieruchomej wody w oryginale.
Sekwencja numerów zasobów potwierdza listę klatek w loaderze, nie ich tempo
odtwarzania.

Ten materiał dotyczy b_MAPA i dużych klatek terenu. Nie ustala obiektów
`LIST_OBJ`/`OBJ_*`, sortowania jednostek, ich pivota, cieni, barw graczy,
mgły wojny, warstw efektów ani przebiegu rozgrywki. Pełny runtime oryginału,
gameplay i porównanie ekranu na Windows 11 pozostają osobnymi etapami.
