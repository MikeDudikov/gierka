# Indeksy i maski sprite’ów oryginału

Stan: 2026-11-02. `tools/decode_sprite.py` odtwarza indeksy palety i maski zapisu
zasobów typu 6. Dowody: rzeczywiste payloady oraz procedury `ancient.exe`
`0x572d40` (wiersze) i `0x574d50` (kopiowanie pikseli). Nie jest to test gry.

## Format

Nagłówek little-endian ma 22 bajty: długość uint32 (+0), wymiary płótna int32
(+4,+8), flagi uint16 (+12), lewa/górna krawędź prostokąta (+14,+16), jego
szerokość/wysokość (+18,+20). Po ewentualnej dekompresji LZ długość musi być
dokładnie zgodna z nagłówkiem.

Bity 10..12 flag wskazują liczbę pozycji uint16 tabeli wierszy. Zaobserwowano
`min(7, wysokość_prostokąta // 16)`. Pozycje dla wierszy 16,32,… są liczone
względem offsetu 22; pozycja dokładnie za końcem prostokąta jest zerowa.
Komendy zaczynają się pod `22 + 2 * liczba_pozycji` i biegną od góry do dołu:

- `01..7F`: pomiń wskazaną liczbę pikseli bez zapisu.
- `81..BF`: zapisz kolejne `komenda & 63` dosłowne indeksy.
- `C1..FF`: powtórz kolejny indeks `komenda & 63` razy.

Wymagana jest dokładna szerokość każdego wiersza, zgodność tabeli pozycji i
zużycie całego payloadu. Zapis indeksu zero nie oznacza przezroczystości.

## Eksport

`*-indices.png` zawiera indeksy w jednokanałowym PNG, a `*-coverage.png`
wartość 255 dla zapisanego piksela i 0 dla pominiętego. Techniczne zero w
niezapisanej części indeksów rozróżnia maska. Nie ustala ona jeszcze pełnego
sposobu mieszania sprite’a z tłem w oryginalnym rendererze.

Manifest podaje hashe DKX/DKD, nazwy, offsety, wymiary, flagi i hashe buforów.
`stored_payload_sha256` dotyczy zapisanych bajtów; `decoded_payload_sha256`
payloadu po ewentualnym LZ. Zastępują niejednoznaczną nazwę `payload_sha256`.
Opcjonalny DIB wybrany przez `--preview-palette` jest jawnie niezweryfikowaną
paletą podglądu. Skala szarości pokazuje indeksy, nie oryginalne kolory.

## Weryfikacja i granice

| Kontener | Sprite’y | Błędy / nieobsługiwane warianty |
| --- | ---: | ---: |
| DATA/CONTROLG | 283 | 0 |
| DATA/OBJECTS | 51408 | 0 |
| missions/controlm | 686 | 0 |
| Łącznie | 52377 | 0 |

Raport: `artifacts/original/sprite-validation.json`. Sprawdzono granice płócien,
przebiegów, tablice wierszy i zakończenia strumieni. Sześć testów obejmuje
komendy, nieprzezroczyste zero, prostokąty, wiersze, pusty sprite i uszkodzenia.
Pięć próbek odtworzono na nowej maszynie w
`artifacts/original/sprite-indices-representative/`.

Flagi: wariant 8-bitowy `0x0080`, opcjonalne `0x0100`, tabela w bitach 10..12.
Znaczenie `0x0100` pozostaje nieustalone. Istniejąca w oryginalnym kodzie
komenda zerowego wiersza nie wystąpiła w badanych danych; jest odrzucana,
podobnie jak zerowe długości `80`, `C0` i inne flagi. Limity: 16 Mi pikseli
na płótno i 256 MiB payloadu. Palety, cienie, rebarwianie, kotwice, powiązania
z jednostkami i tempo animacji wymagają osobnych badań.

```sh
.venv/bin/python tools/decode_sprite.py \
  reference/raw/ancient-conquest/files/DATA/OBJECTS.DKX \
  reference/raw/ancient-conquest/files/DATA/OBJECTS.DKD \
  --name CORP_1A0000 --name TARAN_1D0012 --name DRG_ATK0_00 \
  --name FISH_3236 --name VOLCANO0_00 \
  --output artifacts/original/sprite-indices-new
```

Katalog wynikowy musi być nowy; nazwy zasobów nie sterują ścieżkami.
