# Geometria terenu i granice dowodu dotyczącego kamery

Źródło: lokalny `ancient.exe` SHA-256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`
oraz para `installed/missions/miss000.dkx/.dkd`. Oryginalnego programu nie
uruchamiano w systemie gospodarza. Adresy poniżej są adresami VA dla obrazu
z bazą `0x00400000`.

## Co zostało ustalone

`GameSystem` (`0x0050ee70`) tworzy pola origin `+0x17b6/+0x17ba` z wartościami
`0,0`, szerokość widoku `+0x17be = 9` i wysokość `+0x17c2 = 8` komórek.
`InitMapaBig` (`0x0051bcb0`, zwykły tryb `Mapa+0x58 == 1`) kopiuje te pola do
`Mapa+0x2c/+0x30` i `Mapa+0x3c/+0x40`, ustawia bok komórki `+0x54 = 64`
oraz zeruje dodatkowe przesunięcia `+0x4c/+0x50`. Są to wartości inicjalizacji
kodu, a nie potwierdzenie pierwszej wyświetlonej klatki misji.

| Wartość | Dowód i ograniczenie |
| --- | --- |
| Mapa `miss000`: 24×24 komórki po 64×64 piksele | Nagłówek `b_MAPA` i `InitMapaBig`; daje 1536×1536 pikseli źródłowego terenu, nie rozdzielczość ekranu. |
| Domyślny obszar 9×8 komórek | Konstruktor; odpowiada 576×512 pikselom źródłowym, dopóki późniejszy kod go nie zmieni. |
| Obszar może mieć 12×8 komórek | `Mapa::GetMessage` (`0x0051cd60`), komunikat `0xcc3`, ustawia szerokość na `9 + (app+0x328d != 0 ? 3 : 0)`. Nie jest to stałe FOV wszystkich trybów. |
| Offset X jest zależny od trybu | `GameSystem::GetPos` (`0x00511100`), ID `0x67`, parametr 8 lub 16, oraz globalna flaga `0x005ca54a`. Dla `app+0x328d == 0`, flagi 0 i parametru 8 wynik to 8; dla niezerowej flagi wynik to 216. |
| Offset Y wynosi 8 w inicjalizacji dużej mapy | `InitMapaBig`, zapis `Mapa+0x28 = 8`; nie utożsamiać tego z pełną nowoczesną ramką HUD. |

## Początkowy origin nie jest jeszcze potwierdzony

`GameSystem::GetMessage` (`0x0050f8a0`) po komunikacie `0x101` zeruje origin,
ale później, gdy `app+0x3212 != 0xff`, wysyła do obiektu `0x2f4` komunikat
`0xcba`. Argument bierze z `app+0x2ef5` pod indeksem
`4 * byte(app+0x3212) + byte(app+0x3213)`.

`Mapa::GetMessage` dla `0xcba` w trybach 1 i 4 rozpakowuje argument jako dwa
bez znaku słowa 16-bitowe i wywołuje `DrawMapaXY`. `GameSystem` przy zapisie
(`0x00511510`) zapisuje bieżący origin w tej samej tablicy jako
`(originY << 16) | ushort(originX)`, a tablicę serializuje jako rekord typu 12
`WIN_VIEW`, 80 bajtów.

W `miss000/WIN_VIEW` indeksy 0, 1, 4 i 5 mają wartość 15, czyli parę `(15,0)`;
pozostałe indeksy mają `(0,0)`. To konkretne wejście dla gałęzi przywracania
widoku. Nie zweryfikowano całej ścieżki wczytania tablicy i wyboru początkowego
gracza/podgracza. Ani `(0,0)`, ani `(15,0)` nie jest więc oznaczone jako
potwierdzony pierwszy kadr gry. Sam `DESCRIPTOR` ma 1788 bajtów; bez dowodu
znaczenia poszczególnych pól jego liczby nie są traktowane jako parametry kamery.

Surowe wejścia, hashe i odnośniki do eksportów zapisano w lokalnym raporcie
`artifacts/binary-analysis/terrain-camera/source-camera-inputs.json`.

## Wdrożony, mały fragment geometrii

`Runtime/TerrainViewport.cs` udostępnia dwie czyste funkcje. Nie wybierają
rozdzielczości, kadru ani skali wyświetlania i nie sterują kamerą.

`ClampAxis(requested, mapCells, viewCells)` odwzorowuje instrukcje
`0x00519f3d..0x00519f91`: najpierw ujemne żądanie staje się zerem, następnie
wynik jest ograniczany od góry przez `mapCells - viewCells`. W oryginale
`mapCells` pochodzi z rozszerzanego ze znakiem słowa nagłówka mapy.
Kolejność jest zachowana, również gdy widok jest większy od mapy: dla
`requested=0, mapCells=24, viewCells=25` wynikiem jest **-1**. Nie dodano
korekty do zera. C# używa jawnego `unchecked`, także dla odejmowania granicy.

Funkcja ta nie przenosi wcześniejszego sprawdzania „żądanie równe aktualnemu
origin”, obsługi wyjątków, odrysowania i skutków ubocznych `DrawMapaXY`.
Zachowany zakres x86 zapisuje origin zarówno w `Mapa`, jak i `GameSystem`;
validator dodatkowo sprawdza zgodność obu zapisów.

`CellToScreen(cell, origin, tilePixels, subOffset, frameOffset)` odwzorowuje
początek `DrawCellBig` (`0x005196e0..0x0051972b`):

```text
screen = (cell - origin) * tilePixels + subOffset + frameOffset
```

Wszystkie działania mają 32-bitowe zawijanie jak `SUB/IMUL/ADD` x86. Wynik
jest w pikselach źródłowego układu współrzędnych; skala prezentacji pozostaje
osobną decyzją diagnostycznego widoku. Widoczność komórki w `DrawCellMapa`
(`0x00519a30`) używa przedziałów półotwartych
`origin <= cell < origin + viewCells` dla obu osi.

`ScrollMapaBig` (`0x0051a0b0`) zawiera ruch o jedną komórkę na wywołanie dla
kierunków 1, 2, 4, 8 i przekątnych oraz sprawdza granice mapy. Nie ustalono
pełnego wyzwalania wejścia ani częstotliwości tych wywołań. Nie dodano na tej
podstawie sterowania, prędkości przewijania ani zoomu.

## Walidacja

```bash
.venv/bin/python tools/validate_terrain_viewport.py
.venv/bin/python -m unittest tests.test_terrain_viewport -v
```

Validator wykonuje rzeczywiste instrukcje x86 w Unicorn i porównuje wynik z
rzeczywistym plikiem Unity C# skompilowanym lokalnym Mono z `/checked+`.
Nie porównuje dwóch implementacji wzoru w Pythonie. Wynik: **1080 przypadków,
2160 porównań osi, wszystkie zgodne**: 702 przypadki clamp i 378 transformacji.
Uwzględniono zwykłe komórki, wartości ujemne, `view > map`, granice signed16
nagłówka i przepełnienia signed32. Niepoprawne rozmiary map/widoków to wektory
arytmetyczne, nie obsługiwane scenariusze rozgrywki.

Raport `artifacts/binary-analysis/terrain-camera/geometry-validation.json`
zawiera każdy przypadek, hashe źródeł C#/probe, narzędzia i dokładne granice
wykonywania. Wyciągi instrukcji są obok w `clamp-instructions.asm` i
`position-instructions.asm`. Sekwencje nie wywołują żadnej funkcji zewnętrznej;
nie użyto hooków. Clamp rozpoczyna się po obsłudze `setjmp` i kończy przed
odrysowaniem; transformacja kończy się przed `setjmp`/wyszukiwaniem bitmap.

Te wyniki nie weryfikują całej kamery, rysowania, ładowania misji, AI ani
rozgrywki. **1920×1080 jest wymaganiem współczesnego wydania**, a nie
rozdzielczością/FOV udowodnioną powyższymi funkcjami. Jawny widok referencyjny
może wypełniać cały taki ekran, lecz jego origin i skala muszą pozostać opisane
jako parametry diagnostyczne.

## Dlaczego nie podłączać tego do zwykłego Start gry

Wyświetlenie oryginalnego terenu nie tworzy grywalnej misji. Nie odtwarza
inicjalizacji jednostek, obiektów świata, rozkazów, ekonomii, walki, zwycięstwa,
AI ani ich czasu symulacji. Przeniesione pojedyncze reguły arytmetyczne i bramki
AI również nie zastępują tych systemów. Podłączenie samego terenu do zwykłego
Start sugerowałoby gotową rozgrywkę; właściwy jest osobny, jawnie uruchamiany
widok diagnostyczny do dalszego porównywania z oryginałem.
