# Pierwsza referencja oprawy świata

Stan: 2026-11-02. Odtworzono sześć kafli terenu i trzy pojedyncze sprite’y
świata z odzyskanych bajtów. To materiał do wiernej modernizacji, bez zmiany
obowiązującego celu pełnego ekranu **1920×1080, 16:9**. Żaden obraz nie jest zrzutem uruchomionej
gry ani nową teksturą/modelami remake’u. Pliki źródłowe i projekt Unity
pozostały nietknięte przez ten krok.

## Paleta ma dowód w kodzie i danych

`installed/missions/maplib.dkx/.dkd` zawiera jedyny nazwany `PALETTE` typu 1
w katalogu 62 przebadanych kontenerów. Wpis wskazuje offset **1980988** w DKD,
długość 1068: DIB 1×1, 256 wpisów BGRA. SHA-256 payloadu:
`27ec5162a2aedfed681d53b5e95bb221d5f51eb32f3a2a4e2c4b6a35c03e054f`.
Sama zgodność nazwy nie byłaby dowodem użycia. Łańcuch statyczny programu:

| Adres programu | Odczytany fragment |
| --- | --- |
| `0x004eda40` | `AncientAppTy::InitAppDB` otwiera `MISSIONS/maplib`, zachowuje bazę pod `app+0xd50`, ładuje `b_ALIB` i `s_ALIB`. |
| `0x004edc50` | `InitGameDB` otwiera `objects`, zachowuje bazę pod `app+0xd54`. |
| `0x005101a7` w `0x0050f8a0` | `GameSystemTy::GetMessage` ładuje typ 1 o nazwie `PALETTE`, odczytuje 256 kolorów do `game+0x139e`, kopiuje do `app+0x11ad`. Nazwę funkcji potwierdza jej własny string diagnostyczny `0x005beedc`. |
| `0x0051bcb0` | `MapaTy::InitMapaBig` ustawia bok kafla `0x40` = 64, kopiuje `PALETTE` do własnej tablicy, zwalnia rekord przez bazę `app+0xd50`; z tej samej bazy ładuje `ANIM_PALETTE`. |
| `0x0056c4b0` | Kopiuje BGR bajty tabeli DIB od +40 do RGB wpisów. Nie dodaje korekcji gamma, odcienia ani zastępczych kolorów. |

Eksport Ghidra i referencje stringów:
`artifacts/binary-analysis/menu-interaction/export-app-palettes/`.
SHA-256 badanego EXE:
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Hash samej tablicy 256×RGB po zamianie kolejności kanałów:
`41a0675766dab4d042bd802796139ed06259699033e0a5f8fdcc394971cd5270`.

To dowód bazowej palety świata, bez twierdzenia, że każda klatka w grze
używa jej bez zmian. Obecność `ANIM_PALETTE` w kodzie i zasobach jednoznacznie
wymaga dalszego badania cykli kolorów.

## Konkretne próbki i kontrola kolorów

| Zasób | Rozmiar źródłowy | Wynik |
| --- | --- | --- |
| `b_isl_bkg00_001` | 64×64 | DIB terenu, własna paleta; użyte kolory równe bazowej `PALETTE`. |
| `b_isl_bkg00_015` | 64×64 | DIB brzegu, ten sam sprawdzony warunek. |
| `b_isl_bkg01_001` | 64×64 | DIB terenu drugiego zestawu, ten sam warunek. |
| `b_isl_bkg01_015` | 64×64 | DIB skalistego brzegu, ten sam warunek. |
| `b_sea00_001` | 64×64 | DIB wody, ten sam warunek dla stanu zapisanego w pliku. |
| `b_shelf_001` | 64×64 | DIB wody/płycizny; nazwę semantyczną traktować jako opis wizualny. |
| `CORP_1A0000` | 56×56 | Sylwetka statku, sprite z `OBJECTS`, indeksy odwzorowane przez bazową paletę. |
| `VOLCANO0_00` | 128×128 | Pojedynczy sprite wulkanu, ta sama bazowa paleta. |
| `FISH_3236` | 64×64 | Pojedynczy sprite ryb/wody, ta sama bazowa paleta. |

Sześć DIB-ów zostało wyeksportowanych z ich **własnych zapisanych palet**.
Niezależnie porównano każdy użyty indeks z bazową `PALETTE`. Różnice w
nieużywanych komórkach nie zmieniają wyniku obrazu i nie są błędnie zgłaszane
jako różnice widocznych kolorów.

Audyt obejmuje wszystkie **223 DIB-y maplib**: 202 mają identyczne RGB dla
wszystkich użytych indeksów; 21 ma różnicę pod indeksem 186. Są to
`s_sea00_001` i 20 wariantów `s_shelf_*`. Nie zostały automatycznie
przekolorowane ani opisane jako równoważne. Pełna lista jest w manifeście.

Sprite’y zachowują dokładne wymiary, indeksy i maski pokrycia RLE. Alfa jest
wyprowadzana z pokrycia; zapisany indeks zero pozostaje widoczny. Nie
odgaduje się przezroczystości z koloru RGB. Nie ustalono jeszcze cieni,
rebarwiania gracza, światła ani dynamicznych zmian palety. Ich wynik opisujemy
jako **rekonstrukcję w bazowej palecie**, nie pełny render oryginału.

## Odtwarzanie i testy

```sh
.venv/bin/python tools/inspect_world_reference.py \
  --output artifacts/world-reference/new-verified-reference
.venv/bin/python -m unittest tests.test_world_reference -v
```

Narzędzie weryfikuje SHA-256 pięciu oryginalnych plików przed eksportem,
wymaga nowego katalogu wynikowego i zapisuje hashe wszystkich PNG, buforów
RGBA oraz indeksów/masek sprite’ów. Nazwy zasobów nie sterują ścieżkami PNG.
Indywidualne pliki `00.png`–`08.png` zachowują rozmiar źródłowy. Arkusz
`world-reference-sheet.png` pokazuje kafle w jawnej skali 2× nearest, sprite’y
w rozmiarze źródłowym, z podpisami; nie jest kadrem gry.

Aktualny, rzeczywiście wygenerowany i obejrzany wynik:
`artifacts/world-reference/verified-base-20261102/manifest.json` oraz arkusz
w tym samym katalogu. Trzy wykonane testy sprawdzają indeksowane kolory,
powtarzające się RGB, nieprzezroczyste zero, maski i uszkodzone dane.

Do dalszego etapu pozostają: powiązania jednostek ze zbiorami klatek,
kotwice, kierunki, kolejność i tempo animacji, cykle palety oraz porównanie
z działającym oryginałem. Same końcówki nazw nie dowodzą żadnej z tych reguł.
Nie utworzono mapy ani misji i nie dodano tych próbek do Unity. Dają one
konkretną bazę sylwetek i palety do nowej oprawy silnie inspirowanej oryginałem.
