# Rozpoznane kontenery i zasoby oryginału

Stan badania: 2026-11-02. Dowody pochodzą z pobranego obrazu BIN/CUE, plików
ISO oraz plików odkodowanych z `SETUP.DAT`. Nie uruchamiano instrukcji z płyty.
`tools/inspect_dkx.py` sprawdza strukturę i hashe bez uruchamiania gry.

## Wynik odczytu

Wszystkie 62 pary DKX/DKD z płyty i instalatora dały łącznie **76 243 wpisy**.
Każdy wpis ma sprawdzony zakres i nagłówek przydziału oraz SHA-256 zapisanych
bajtów. `artifacts/original/asset-all-summary.json` wskazuje 62 pełne raporty
z hashami źródeł w `asset-container-inventories/`. Raporty i oryginały są lokalne,
ignorowane przez Git; brak ich w nowym checkoutcie wymaga przywrócenia danych.

| Kontener | Wpisy | Rozpoznane eksporty |
| --- | ---: | --- |
| DATA/CONTROLG | 4470 | 3993 obrazy, 15 fontów / 25 atlasów |
| DATA/DATAMAP | 1715 | 1266 obrazów, 2 fonty / 5 atlasów |
| DATA/OBJECTS | 57744 | Katalog i dekoder indeksów/masek sprite’ów |
| SOUND/SOUNDS | 391 | 163 klipy PCM |
| VIDEO/TASKS | 1 | 1 klip PCM stereo |
| missions/controlm | 856 | 16 obrazów, 14 fontów / 44 atlasy |

Pozostałe kontenery obejmują między innymi mapy i definicje misji; odczyt
rekordów nie oznacza jeszcze znajomości semantyki ich pól.

Odzyskano **5275 obrazów DIB**, **164 klipy PCM** oraz **31 zestawów fontów
z 74 atlasami wariantów**. 193 obrazy wymagały kodeka LZ z
`tools/extract_setup.py`; każdy strumień został zużyty w całości, a długość
wyniku odpowiadała metadanym. Pozostałe typy nie są zastępowane obrazami
zmyślonymi ani uproszczonymi.

PNG zachowuje kolory pikseli odczytane z palety DIB. Eksport do RGB nie zachowuje
indeksów palety ani znaczenia klucza przezroczystości. Oryginalne DKD i hashe
pozostają źródłem do ich późniejszego rozpoznania. Klipy WAV zachowują bajty
PCM, liczbę kanałów i częstotliwość próbkowania; reguły odtwarzania w grze
pozostają do ustalenia.

`artifacts/original/asset-reference-sheet.png` pokazuje przykładowe pojedyncze
zasoby UI, fontów i tytułu edytora scenariuszy. To arkusz podglądowy, nie zrzut
działającej gry ani obraz remake’u. Manifest obok niego wskazuje źródła.

## DKX: indeks DKBT

- Nagłówek 64 bajty, sygnatura `DKBT`, wersja `01 01`, rozmiar strony 2048
  zapisany jako `00 08`. Długość pliku pod offsetem 8, korzeń pod offsetem 36.
- Strony zaczynają się pod `64 + n * 2048`. Pierwsze 16 bajtów stanowi nagłówek
  strony; wskaźnik prawego poddrzewa jest pod +4, liczba użytych bajtów
  rekordów jako **uint16** pod +8. Kolejne bajty zawierają również stare dane
  pamięci; traktowanie +8 jako uint32 daje fałszywe błędy.
- Rekord: wskaźnik lewego poddrzewa (4), offset danych DKD (4), typ (1),
  długość zapisana (4), znacznik kompresji (1), długość po dekompresji (4),
  metadane typu (12), długość nazwy (2), nazwa. Liczby są little-endian.
- `FFFFFFFF` oznacza brak poddrzewa. Odczyt obejmuje wyłącznie osiągalne strony;
  dekoder odrzuca cykle, powtórne odwołania, niewyrównane strony, obcięte nazwy,
  powtórzone klucze `(typ, nazwa)` i nakładające się przydziały.

## DKD: alokacje DKFM

Nagłówek ma 32 bajty, sygnaturę `DKFM`, wersję `01 01` i długość pliku pod +8.
Każda alokacja ma 4-bajtowy znacznik przed danymi: starsze bity to długość
całego przydziału wyrównana do 4 bajtów, młodsze dwa bity to flagi. Zbadane
żywe przydziały mają flagę 1. Wpis indeksu wskazuje dane za znacznikiem.
W plikach edytowanych przydział bywa większy niż bieżący payload, np.
`custom/SINGLE06.DKX`, rekord `DISCRIPTION`, ma 10 bajtów wolnego miejsca.
Nie wymagamy więc równości przydziału i minimalnej długości payloadu.
Osiem ostatnich bajtów pliku nie jest kolejną alokacją.

## Obsługiwane payloady

- **Typ 1:** Windows DIB: `BITMAPINFOHEADER` 40 bajtów, 8 bitów na piksel,
  nieskompresowany bitmapowo, paleta BGRA, wiersze wyrównane do 4 bajtów.
  Kontener może osobno stosować kompresję LZ (znacznik 1).
- **Typ 2:** `WAVEFORMATEX` PCM, 18 bajtów, następnie uint32 długości próbek,
  4 bajty zarezerwowane i próbki. Sprawdzane są kodowanie, kanały, tempo
  bajtów, wyrównanie, bity i dokładna długość.
- **Typ 3:** font bitmapowy. Pierwszy uint16 podaje liczbę wariantów atlasu
  (zaobserwowano 1–4). Liczba wpisów glifów leży pod +100; 102-bajtowy nagłówek
  poprzedza wpisy po 10 bajtów: `x, y, width, height, code` jako uint16.
  Liczba wpisów i wszystkie prostokąty odpowiadają rozmiarom z indeksu.
  Pierwszy wpis jest glifem zastępczym; za tablicą pozostaje 10 bajtów
  zarezerwowanych. Atlasy są poprzedzającymi alokacjami DIB
  o zgodnych wymiarach. Każdy atlas ma osobny hash i offset w DKD.
  Znaczenie wariantów, kodowanie znaków, baseline, advance, mieszanie i klucz
  przezroczystości wymagają potwierdzenia kodem lub pomiarem wykonania.
- **Typ 6:** sprite’y RLE; osobny `tools/decode_sprite.py` odczytuje indeksy
  pikseli i maski pokrycia. Sprawdzono wszystkie 52 377 wpisów tego typu w trzech
  kontenerach. Powiązanie palety i znaczenie dodatkowych flag renderowania
  pozostają do zbadania: [SPRITE_FORMAT.md](SPRITE_FORMAT.md).
- Inne typy: zachowane nazwy, bajty metadanych i hashe; bez zgadywania reguł gry.

## Powtarzalne polecenia i kontrola

Po wznowieniu wykryto i poprawiono przesunięcie tablicy glifów: odczyt od +112
pomijał glif zastępczy i wciągał zerowe bajty końcowe. Procedura oryginału
`0x547100` czyta kod znaku pod +110+10*i, co potwierdza początek rekordu +102.
Wszystkie 31 fontów ponownie wyeksportowano z poprawnym zakresem. Bieżące raporty
to `artifacts/original/font-corrected-v3-*.json` i `font-correction-summary.json`.
Starsze `asset-final-*.json` zachowują prawidłowe obrazy i próbki PCM, ale ich
metadane fontów są historyczne. Atlasy nie wymagały zmiany pikseli.

```sh
.venv/bin/python tools/inspect_dkx.py \
  reference/raw/ancient-conquest/files/DATA/CONTROLG.DKX \
  reference/raw/ancient-conquest/files/DATA/CONTROLG.DKD \
  --output artifacts/original/controlg-new.json \
  --export-known artifacts/original/controlg-new
.venv/bin/python -m unittest tests.test_inspect_dkx -v
```

Plik raportu i katalog eksportu muszą być nowe. Nazwy eksportów są numeryczne;
nazwy zasobów nie sterują ścieżkami. Zależności: przypięte `Pillow` i Python
ze środowiska repozytorium; kodek LZ jest implementacją lokalną.

Sześć testów obejmuje błędy drzewa i zakresów, nagłówki alokacji, orientację
i paletę DIB, zgodność bajtów PCM w WAV, granice glifów i hashe atlasów.
To testy narzędzi analizy; nie dowodzą wierności symulacji, AI, fontów w runtime
ani ukończenia remake’u w Unity.
