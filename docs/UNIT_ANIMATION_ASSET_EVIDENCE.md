# Grafika ośmiu statków miss000 — wybór klatek i kompozyt typu 8

Stan: 2026-11-02. Badanie danych i wybranych instrukcji niezmienionego oryginału.
Tag 200 jest wejściem fabryki `ShipClassTy`, a nie dowodem modelu lub nazwy
każdego statku. Pozycje i inicjalizację modelu opisuje
[MISSION_UNIT_INITIALIZATION_EVIDENCE.md](MISSION_UNIT_INITIALIZATION_EVIDENCE.md).
Niniejszy etap dotyczy zamrożonej referencji grafik, bez symulacji i czasu animacji.
Nie jest to finalna oprawa 2026 ani nagrana klatka działającej gry.

## Źródła i ścieżka wyboru

Źródła pod `reference/raw/ancient-conquest`:

| Plik | SHA-256 |
| --- | --- |
| `installed/ancient.exe` | `cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021` |
| `files/DATA/OBJECTS.DKX` | `67aa31b7e7728a1c4f215c63932b55ea66f3ac1ecdb732bfd368bae2a8375f60` |
| `files/DATA/OBJECTS.DKD` | `01474065782a7170d54f564df2205572f8a0675411bef0f350dab55c3fd20e50` |
| `installed/missions/miss000.dkx` | `b4b2fda60bb38e837b6d0548caa86229e1fbebf8cb9fd806c4f39c9bd75835ce` |
| `installed/missions/miss000.dkd` | `a77e801a93baafd6942db9087d7541f8c85ed2f3c88d440b9f9e81b45ba9a0d1` |

Zasoby statków korzystają z **typu 8**, nie z prostych sekwencji typu 7 użytych
przez rafy. `Ship::GetMessage0x4dc630`, komunikat 2 i tryb 0, tworzy rejestr
SpriteClass typu 8, potem przez stan uszkodzenia wywołuje `LoadImages0x4e1bb0`.
Dla badanych ośmiu seedów żądane zdrowie wynosi 100%, a stan uszkodzenia to 1.
W tej gałęzi oryginał wywołuje `0x4e0120` z modelem, grupą pochodzenia,
grupą właściciela, slotem właściciela i zerowym ostatnim parametrem.
Rzeczywisty format to `SHIP_%C%1d%1d%1d%1d`.

Maskę części wybiera `0x4e5da0`. Dla stanu 1 podstawą jest `0x83`.
Wyposażenie pod `object+0x27a` dodaje dla wartości 1 bit `0x20`, dla wartości 2
bit `0x40`; pod `+0x27b` odpowiednio `0x08` lub `0x10`. Specjalna gałąź `+0x259`
nie jest aktywna w tych ośmiu seedach. Nie utożsamiono tych pól z nazwami
wyposażenia na podstawie pamięci ani wyglądu grafiki.

| Źródłowe ID | Deskryptor typu 8 | Maska | Klatka referencji | Logiczne wymiary |
| --- | --- | --- | --- | --- |
| `0b` | `SHIP_A1110` | `0x83` | 20 | 56×56 |
| `0c` | `SHIP_A1110` | `0x83` | 16 | 56×56 |
| `0d` | `SHIP_H1110` | `0xa3` | 16 | 72×72 |
| `10` | `SHIP_B4400` | `0x83` | 0 | 64×64 |
| `27,28,29,2a` | `SHIP_G4400` | `0x8b` | 4 | 72×72 |

`0x4e0160` ustawia indeks jako `signed_byte(direction) << 2`. Stan klatek jest
referencją inicjalizacji; dalszy kod może zmieniać indeks i skład grafiki.
Wybór nazw i masek wykonano oryginalnym `0x4e1bb0`, wraz z `0x4e0120` oraz
`0x4e5da0`, dla wszystkich **8 autentycznych seedów**. Hooki zastępują jedynie
standardowy `wsprintfA` oraz rejestrują żądanie `SetImagesReg0x50d010`.
Nie zastępują wyboru gałęzi, maski ani danych wejściowych. Raport:
`artifacts/units/animation/ship-graphics-selection.json`.

## Format deskryptora i części

Metadane DKX typu 8 mają 12 bajtów. Pierwsze cztery signed short little-endian
opisują liczbę części, liczbę klatek oraz logiczną szerokość i wysokość.
Payload jest tablicą **frame-major**: po wszystkich częściach klatki 0 są
wszystkie części klatki 1. Każdy rekord ma 44 bajty:

```text
+0  int32 little-endian: offset X
+4  int32 little-endian: offset Y
+8  int32 little-endian: depth
+12 char[32]: nazwa zasobu typu 6, zakończona NUL
```

`mfMSprLoad0x554d50` wybiera części według bitów maski i dla każdej wczytuje
wszystkie klatki. Runtime zapisuje `x, y, depth` jako **signed 16-bit**, biorąc
dolne słowa z wartości 32-bitowych. Za nimi zapisuje aktualny wskaźnik bitmapy.
Rekord runtime ma 10 bajtów; nie należy dereferencjonować wskaźników z pliku.

Badany loader rezerwuje stride według `min(popcount(mask), sourceParts)`,
a następnie w nagłówku zapisuje faktyczną liczbę wybranych części. Maska
łącząca tylko część dostępnych bitów z bitami spoza zakresu może więc dać
rzadszy układ pamięci. Adapter świadomie odrzuca taki niezweryfikowany wariant.
Maska wszystkich bitów dla wszystkich dostępnych części, używana m.in. przez
jednoczęściowe budynki, pozostaje obsługiwana. Odrzucenie jest kontraktem
adaptera, nie twierdzeniem o naprawianiu uszkodzonego stanu przez oryginał.

## Kolejność lokalna i osobny cień

Ujemny depth **nie oznacza braku bitmapy**. `0x55e0e0` tworzy dla takiej części
osobny sprite z priorytetem równym `-depth`. Wszystkie badane części `BLB*`
mają depth `-21000`, zatem osobny priorytet 21000. W ich pikselach nie dodajemy
umownej półprzezroczystości ani nowego koloru cienia. To zwykłe źródłowe
bitmapy RLE w palecie świata. Efekty widoczności i palety są osobnym problemem.

Nieujemne części wewnątrz kompozytu są porządkowane malejąco po depth.
Oryginalna procedura wykonuje **niestabilne zamiany parami**, a nie stabilny
sort biblioteczny. Równe depth mogą zmienić kolejność po zamianie z późniejszą
częścią o większej wartości. Decoder odtwarza te zamiany i zachowuje osobno
części odłączone; nie zgaduje globalnego porządku świata.

Pełny globalny priorytet rodzica, części odłączonych i przypadki równych
priorytetów opisuje [UNIT_WORLD_ORDER_EVIDENCE.md](UNIT_WORLD_ORDER_EVIDENCE.md).
Pozycja odłączonej części wynika z pozycji rodzica i offsetu części; nie jest
niezależnym położeniem komórki. Docelowe włączenie do świata wymaga również
potwierdzenia kolizji, widoczności i warunków tworzenia.

## Kotwice oraz kolory

Dla statku pełna płaszczyzna jest centrowana względem komórki 64×64 według
**logicznych wymiarów kompozytu**, a nie wymiarów dowolnej części:

```text
parentX = cellX*64 + (64-logicalWidth)/2
parentY = cellY*64 + (64-logicalHeight)/2
partX = parentX + offsetX
partY = parentY + offsetY
```

Instrukcje `0x4e0160` zawijają działania do 32 bitów i dzielą ze znakiem
z zaokrągleniem do zera. Dla szerokości 65 poprawne przesunięcie to 0, nie −1.
Dla rzeczywistych 56/64/72 wyniki to 4/0/−4. Odrębny dowód C# i arytmetyki
jest w MISSION_UNIT_INITIALIZATION_EVIDENCE.md.

Wszystkie części pięciu unikalnych klatek mają w badanej próbce te same wymiary
co ich kompozyt, ale decoder zachowuje ich własne wymiary i pełne płaszczyzny.
`left/top` RLE określa położenie zawartości wewnątrz płaszczyzny; nie dodajemy
tego offsetu ponownie do pozycji komponentu. Części pochodzą z zasobów:

- A/20: `BLB1A020`, `CORP_1A0015`, `PARUS11A10015`.
- A/16: `BLB1A016`, `CORP_1A0012`, `PARUS11A10012`.
- H/16: `BLB1H016`, `CORP_1H0016`, `ARMOR_1H0012`, `PARUS11H10012`.
- B/0: `BLB4B000`, `CORP_4B0000`, `PARUS40B40000`.
- G/4: `BLB4G004`, `CORP_4G0004`, `TARAN_4G0003`, `PARUS40G40003`.

Grupa i slot wpływają na wybór nazw grafik, np. `CORP_1*`/`CORP_4*` i
`PARUS11*`/`PARUS40*`. Nie zastąpiono ich arbitralnym tintem Unity. Piksele
referencji wykorzystują odzyskaną bazową PALETTE; RGB nie jest wywnioskowane
z koloru podglądu. To nie dowód wszystkich dynamicznych efektów gracza.

## Wdrożony decoder i sprawdzenie

`tools/decode_composite_sprite.py` udostępnia
`decode_composite_frame(entry,data,entries,frame_index,mask)`. Wynik zawiera
logiczne wymiary, części w źródłowej kolejności, osobne `inline_components`
w kolejności rysowania oraz `detached_components`. Każda część zachowuje nazwę,
źródłowy indeks, offsety, depth, hash payloadu i pełne indeksy/pokrycie RLE.
Decoder nie wykonuje animacji, nie stosuje palety, nie tworzy świata i nie
scala części ujemnych ze zgadywaną kolejnością globalną.

Oracle `artifacts/units/animation/validate_composite_original.py` wykonał
kompletny `0x554d50` z rzeczywistymi helperami metadanych w **12 przypadkach**:
cztery deskryptory statków, pięć zmienionych masek A oraz trzy deskryptory
budynków wspierających. Wykonał 3195 odczytów klatek przez hook zasobów;
z decoderem porównano 18 wybranych klatek oraz ich kolejność po oryginalnym
sortowaniu. Zewnętrzne hooki obejmują I/O metadanych/payloadów, alokację,
zwalnianie i normalny setjmp. Nie przechwytują wyboru części ani transpozycji.

Ten sam oracle wykonał zakres sortowania `0x55e56b..0x55e658` na **340**
syntetycznych tablicach zawierających części ujemne, zero i równe depth,
**bez hooków**. Wszystkie wyniki są zgodne z decoderem. Pierwsza próba setupu
zakresu miała błąd uchwytu/rejestru narzędzia: unmapped read pod 0x55e5a7.
Notatka o zaobserwowanym błędzie: `first-sort-harness-failure-note.json` w katalogu
dowodów; nie jest to surowy log uruchomienia. Skorygowano rejestr wejściowy EDX
i lokalny uchwyt rodzica, bez zmiany oryginalnego kodu.

`validate_ship_pixels.py` porównał wszystkie **17 unikalnych komponentów**
początkowych grafik z oryginalnym dispatcherem `0x574290`: **96 dokładnie
zgodnych buforów indeksów**, z maską, clippingiem, stride i bajtami ochronnymi.
Uwzględniono również wszystkie pięć unikalnych bitmap `BLB*`. Żaden callee
blittera nie jest przechwytywany. Raport:
`artifacts/units/animation/ship-component-rle-validation.json`.
To nie porównanie całego framebufferu gry ani reguł animacji w czasie.

Siedem testów `tests/test_decode_composite_sprite.py` przeszło bez pominięć.
Sprawdzają format frame-major, bity maski, zwężanie signed16, odłączone części,
niestabilny sort, oryginalny fixture, maskę bitu 31, granice, błędne metadane,
truncation, duplikaty, nazwy, typ bitmapy oraz nieobsługiwany flagę 0x100.
Fixture `tests/fixtures/composite_original_selection.json` ma SHA256
`25e59c7365666e669edb6705b9c85fd5947cae5ba9c016a3563411a6d0818e50`.
Źródłowe EXE, DKX i DKD są chronione hashami przed porównaniami.

Nie edytowano Unity ani nie uruchamiano usług w ramach tego badania. Braki:
pełne konstruktory w docelowym runtime, świat, AI, ruch, walka, animacja,
widoczność, dźwięk, nowa oprawa i testy docelowego Windows 11/laptopa.
