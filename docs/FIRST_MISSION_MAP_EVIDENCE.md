# Dane świata pierwszej misji — rekonesans

Stan: 2026-11-02. Wyłącznie analiza danych i kodu dostarczonego oryginału.
Nie uruchomiono gry i nie dodano mapy ani fikcyjnej rozgrywki do Unity.
Obowiązujący cel remake’u pozostaje **1920×1080, 16:9, pełny ekran**;
wymiary świata poniżej nie definiują docelowego viewportu ani skali kamery.

Badany `ancient.exe` ma SHA-256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Wszystkie VA odnoszą się do obrazu bazowego `0x400000`. Inwentaryzacja
pełnych 63 rekordów miss000 z offsetami/hashami i krótkimi nagłówkami:
`artifacts/binary-analysis/first-map/resource-inventory.json`.

## Potwierdzona mapa b_MAPA

`installed/missions/miss000` zawiera **typ17 `b_MAPA`**. Indeks DKX ma
metadane `18001800400040001ea44300`; pierwsze cztery little-endian signed short
wynoszą **24, 24, 64, 64**. Rekord DKD od offsetu4084 zajmuje1521bajtów
kompresji; dekoder odzyskuje9216bajtów. To nie mapa96×96 pojedynczych bajtów.

| Źródło x86 | Odczytane działanie |
| --- | --- |
| `0x4ecef0` w TuneGamePtr | Ładuje `b_MAPA` przez `0x544dc0`, zapisuje mapę w `app+0x19e5`. |
| `0x544dc0` mfBMapLoad | Czyta metadata typu17 do czterech shortów; tworzy mapę i wczytuje payload pod `map+8`. |
| `0x544cb0` mfBMapCreate | Zachowuje cztery shorty w nagłówku; rezerwuje `width*height*16 +10` bajtów. |
| `0x544ec0` mfBMapSave | Zapisuje typ17, metadata czterech shortów i dokładnie `width*height*16` bajtów od `map+8`. |
| `0x5196e0` DrawCellBig | Dla jednej komórki wywołuje `0x545190` osiem razy, warstwy0…7, w tej kolejności. |
| `0x545190` GetCellBitmap | Sprawdza x/y/warstwę; lowbyte selektora0 pomija rysowanie. |
| `0x544fc0` | Highbyte tego samego słowa przekazuje jako identyfikator biblioteki do `0x544ba0`. |
| `0x544ba0` | Szuka ID przez porównanie pierwszego bajtu rekordów o kroku211bajtów w b_ALIB. |
| `0x544c10` | Dla niezerowego selektora używa indeksu `selector−1` w odbudowanej tablicy klatek; zwraca też bajt typu rysowania deskryptora. |

Format jest więc **24×24 komórki, osiem planarnych warstw, po dwubajtowym
selektorze na komórkę/warstwę**. W samym payloadzie bez runtime nagłówka:

```text
offset = 2 * ((layer * height + y) * width + x)
word = payload[offset] | payload[offset+1] << 8
selector = word & 255       # zero: brak rysowania tej warstwy
library_id = word >> 8      # porównanie jako bajt, nie numer rekordu
frame_index = selector - 1  # tylko gdy selector != 0
```

X zmienia się najszybciej, potem Y, następnie warstwa. Nie wolno odczytać
każdych kolejnych16bajtów jako ośmiu warstw tej samej komórki.

Parametry kafla64×64 potwierdza również `InitMapaBig0x51bcb0`, ustawiając
bok kafla na0x40. `DrawCellBig0x5196e0` przelicza x na
`(x − viewX)*64 + offsetX + frameX`, analogicznie Y. Daje to siatkę źródłową
1536×1536pikseli; nie jest to dowód kadrowania całego świata ani jego skali
na ekranie remake’u.

Dekodowany payload, jego SHA i statystyki zapisano w
`map-layout.json` oraz `miss000-map-payload.bin` w katalogu dowodów.
Liczby aktywnych komórek (lowbyte !=0) kolejnych warstw:
**576, 9, 132, 70, 85, 12, 41, 82**. Niezerowy highbyte przy zerowym
lowbyte nie stanowi sam w sobie widocznej klatki.

## Powiązanie z biblioteką grafiki

`AncientAppTy::InitAppDB0x4eda40` otwiera `MISSIONS/maplib`, zachowuje DB pod
`app+0xd50`, ładuje **typ16 `b_ALIB`** do `app+0x15c1` i `s_ALIB` do+0x15c5.
`DrawCellBig` przekazuje właśnie duże `b_ALIB` do lookupu.

`b_ALIB` ma103rekordy ×211bajtów =21733bajty. ID jest pierwszym bajtem,
nazwa zasobu/prefiks leży na+8, a bajt typu rysowania na+40. Tablicy wskaźników
zapisanych w pliku nie wolno używać jako aktualnych adresów — loader odbudowuje
je w pamięci. Sama nazwa prefiksu nie dowodzi jeszcze wszystkich reguł klatek,
animacji lub aliasów.

W miss000 występuje17 aktywnych ID; wszystkie znaleziono w b_ALIB:

| ID | Odczytany prefiks |
| ---: | --- |
|0|`b_sea00_`|
|1|`b_shelf_`|
|2|`b_ban01_`|
|7|`b_isl_bkg00_`|
|8|`b_isl_bkg01_`|
|10|`b_isl_trav00_`|
|11|`b_isl_trav01_`|
|19|`b_isl_les01_`|
|20|`b_isl_les02_`|
|22|`b_isl_like00_`|
|26|`b_isl_val00_`|
|30|`b_isl_les03_`|
|34|`b_isl_zem00_`|
|35|`b_isl_zem01_`|
|47|`b_AMBER`|
|48|`b_isl_gor00_`|
|52|`b_isl_ruin00_`|

To identyfikatory źródłowe, nie nowe nazwy jednostek. Bazowa paleta świata ma
osobne dowody w [WORLD_ASSET_REFERENCE.md](WORLD_ASSET_REFERENCE.md).

## Obiekty i gracze: dwa różne zbiory

- Typ20 `LIST_OBJ` ma1040bajtów: nagłówek28 i **44rekordy po23bajty**.
  `mfDarLoad0x54a840`/`0x55f2e0` potwierdzają pola elementSize+8,
  count+12,capacity+16,grow+20 i dane od+28. To oddzielna reprezentacja;
  nie łączyć jej pozycyjnie z nazwanymi OBJ_*. Znalezione w niej współrzędne
  wyrównane do64 nie wystarczają do przypisania wszystkich pól i nazw obiektów.
- Nazwanych **typ12 `OBJ_*` jest45**, ze zmienną długością payloadu.
  Pierwszy dword jest tagiem wyboru klasy w `CreateSystemObjects0x51e7a0`.
  Numer instancji jest parsowany z sufiksu szesnastkowego nazwy.
- Gdy pole+4 wynosi1, loader sprawdza
  `PLAYERS_DESC[(field+8)*4 + (field+12)] !=0` i pomija obiekt dla zerowego
  slotu. To źródłowa podstawa rozdzielenia rodzaju/slotu gracza; nie dowód
  nazw frakcji, znaczenia pozostałych rodzajów lub interpretacji wszystkich
  per-class współrzędnych/statystyk.

Nagłówki wszystkich45payloadów, rozkład tagów oraz eksporty loadera:
`artifacts/binary-analysis/first-map/objects/initial-object-headers.json`
i `objects/export-objects-load/`. Nie zgadywano nazw statków z pamięci ani
nie traktowano liczby44/45 jako gotowej liczby jednostek gracza.

## Następny najmniejszy etap i granice

Następnym uzasadnionym krokiem jest deterministyczny parser nagłówka i ośmiu
warstw oraz powiązanie każdego aktywnego ID/frame z poprawnie odbudowaną
biblioteką b_ALIB. Potem można złożyć **diagnostyczny obraz terenu** według
oryginalnej kolejności warstw, rysowania DIB/sprite i masek. Dopiero z dowodem
kotwic, aliasów, palet/animacji i kamery można podłączyć go do właściwego widoku.

Ten rekonesans nie implementuje świata, misji, ruchu, ekonomii, walki, AI,
losowości, zapisu ani warunków zwycięstwa. Do odtworzenia initial setup potrzebne
są per-class Init funkcje, aktywne PLAYERS_DESC oraz kolejność/stany tworzenia.
Najważniejsze brakujące reguły renderu: pełny mfAnimLibLoad i nazwy klatek,
maski/type1 vs type6, zakotwiczenie obiektów, dynamiczne palety i viewport.
Nie dodano nowych testów do suite ani zmian Unity; wynik nie oznacza grywalnej
pierwszej misji ani porównania z działającym oryginałem.
