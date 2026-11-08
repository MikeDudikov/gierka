# Instalator PQ z odczytanego obrazu Ancient Conquest

Stan: 2026-11-02. Narzędzie `tools/extract_setup.py` odczytuje `SETUP.DAT`
statycznie, bez uruchamiania `SETUP.EXE` ani zainstalowanych programów.

## Potwierdzona struktura

Źródło: `reference/raw/ancient-conquest/files/SETUP.DAT`, SHA-256
`a9f37e68c45b86df306bea396d4d56924caec98ead9e97f879c14cdbb7ccc3c8`.
Hash należy porównać z aktualnym raportem; ścieżka i katalogi oryginału są
ignorowane przez Git.

- Nagłówek zaczyna się od `PQSetup data for AC` zakończonego zerem.
- Dane plików zaczynają się na pozycji `0x53`.
- Ostatnie osiem bajtów to dwa `uint32` little endian: pozycja tablicy i liczba
  rekordów. Na tej płycie: `8247024` oraz `121`.
- Rekord rozpoczyna `uint32` długości bez tego pola. Długość wynosi
  `555 + 4 × liczba_bloków`; całość zajmuje dodatkowe cztery bajty.
- Pozycje względem początku rekordu: bajt `+8` to flaga kompresji; nazwa pliku
  zaczyna się na `+10`, katalog na `+271`, liczba bloków `uint32` na `+551`,
  a rozmiary zapisanych bloków `uint32[]` na `+559`.
- Nazwy są zakończone zerem; katalogi używają separatora Windows `\`.
  Rekord bez bloków o nazwie `*EMPTY` oznacza pusty katalog.
- Bloki danych są kolejne, zgodnie z kolejnością tablicy. Suma ich rozmiarów
  dokładnie pokrywa odcinek od `83` do `8247024`. Zapamiętane wskaźniki w
  rekordach nie służą do adresowania danych na dysku.

## Kompresja

Algorytm zidentyfikowano w `SETUP.EXE`, procedura pod wirtualnym adresem
`0x408b20`. Strumień ma 16-bitowe słowa sterujące, czytane od najmłodszego bitu.
Po szesnastym bicie kolejne słowo jest pobierane **przed** danymi bieżącego
elementu. To istotne przy odtwarzaniu granic strumienia.

- `1`: jeden dosłowny bajt.
- `00`: dwa bity długości (`2..5`) oraz bajt przesunięcia (`-256..-1`).
- `01`: słowo little endian. Długość wynosi `((word >> 8) & 7) + 2`,
  przesunięcie `-8192 | ((word & 0xf800) >> 3) | (word & 255)`.
- W długim wariancie długość `2` wprowadza dodatkowy bajt: `0` kończy blok,
  `1` kontynuuje bez danych, a pozostałe wartości oznaczają długość `bajt + 1`.
- Kopiowanie wsteczne może zachodzić na właśnie dopisywane bajty. Historia
  odniesień nie przechodzi między blokami. Odzyskane bloki mają maksymalnie
  `131072` bajtów.

Dekoder odrzuca ucięte dane, odwołania przed początkiem bufora, nadmiarowe
bajty po znaczniku końca, przekroczenie limitów i niespójne tablice. Nie
zidentyfikowano wewnętrznych sum kontrolnych instalatora; poprawny odczyt
struktury nie zastępuje zewnętrznych hashy i testu RAR.

## Wynik rzeczywistego odczytu

Odzyskano **120 plików**, **20 225 360 bajtów** oraz rekord pustego `savegame/`.
Wszystkie bloki zakończyły się dokładnie na deklarowanej granicy.

- `ancient.exe`: 1 904 640 bajtów; skompilowany program Windows, nie źródła.
- `mapedit.exe`: 847 872 bajty; dodatkowo `config.exe`, `sndcfg.exe` oraz pliki
  pomocy `ancient.hlp` i `mapedit.hlp`.
- 25 par `custom/BATTLE01..25.DKD/DKX` i 15 par `custom/SINGLE01..15.DKD/DKX`.
- 14 par `missions/miss000..013.DKD/DKX`, `maplib` i `controlm`, a także `demo`.
  Same nazwy nie dowodzą liczby grywalnych misji ani sposobu uruchomienia.
- W tym instalatorze nie znaleziono plików o rozszerzeniach kodu źródłowego.
  To nie dowodzi jeszcze pełnego rozpoznania wszystkich kontenerów danych.

Kompletny raport z hashami znajduje się w ignorowanym
`artifacts/original/setup-inventory.json`, a odzyskane pliki w
`reference/raw/ancient-conquest/installed/`.

## Powtórzenie odczytu

```sh
.venv/bin/python tools/extract_setup.py \
  reference/raw/ancient-conquest/files/SETUP.DAT \
  --output artifacts/original/setup-inventory-new.json

# Katalog docelowy i plik raportu muszą być nowe.
.venv/bin/python tools/extract_setup.py \
  reference/raw/ancient-conquest/files/SETUP.DAT \
  --extract-to reference/raw/ancient-conquest/installed-new \
  --output artifacts/original/setup-extracted-new.json

.venv/bin/python -m unittest tests/test_extract_setup.py -v
```

Limit danych wynikowych domyślnie wynosi 2 GiB, pojedynczego bloku 128 KiB,
a wejściowego instalatora 64 MiB. Nieudany odczyt może pozostawić częściowe
pliki w nowym katalogu; nie są oznaczane jako udane ani nadpisywane przy
kolejnym uruchomieniu.
