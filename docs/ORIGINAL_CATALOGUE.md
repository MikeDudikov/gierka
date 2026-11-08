# Katalog dowodów oryginału

Stan analizy: 2026-11-02. Badanie jest statyczne: nie uruchomiono oryginalnej gry,
instalatora ani edytora map. Katalog opisuje odczytane dane, nie zgodność remake’u.
Względne ścieżki poniżej odnoszą się do `reference/raw/ancient-conquest/`.

## Materiał wejściowy i odtwarzalność

- 13 części RAR: 401 117 841 bajtów łącznie. Pełny test 7-Zip zakończył się
  `Everything is Ok`; raport: `artifacts/original/rar-integrity.txt`.
- BIN: 636 110 160 bajtów, SHA-256
  `a23d1141adb4342a625d4c75322b254c2e45af282d56b4b975eb48f5ebdcaeb1`.
- CUE: 377 bajtów, SHA-256
  `32996b89d0264da1ee84426569caf4f637ccd27de137944b246cf29e8ad85de4`.
- Jeden tor MODE1/2352 i siedem torów AUDIO. ISO9660 zawiera 289 plików
  o łącznej długości 256 319 856 bajtów. Pełny katalog, hashe plików i zakresy
  ścieżek: `artifacts/original/disc-inventory-with-audio.json`.
- Strumień danych toru 1 ma 257 040 384 bajty; SHA-256
  `0e9a9e6ae5255cc61485e314f96f3efb0532584ddadb968dd506654ab38bf792`.
  Sprawdzono znaczniki synchronizacji i trybu sektorów; nie wykonano kontroli CD
  EDC/ECC. Test RAR nie jest testem poprawności działania gry.
- `files/SETUP.DAT` odzyskano statycznie: 120 plików i rekord pustego katalogu
  `savegame/`. Szczegóły kompresji i granice dekodera opisuje [SETUP_FORMAT.md](SETUP_FORMAT.md).
- `artifacts/original/catalogue-evidence.json` zawiera rozmiary i SHA-256 wszystkich
  289 plików ISO oraz 120 plików instalatora, a także offsety wskazanych niżej
  ciągów w `ancient.exe`. Materiały i raporty są lokalne i ignorowane przez Git.

## Kod i identyfikacja wydania

`installed/ancient.exe` jest skompilowanym programem Windows x86 PE, 1 904 640
bajtów, SHA-256 `cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Znacznik czasu nagłówka PE to `1999-04-08T01:34:59Z`; sam znacznik nie potwierdza
wersji produktu, języka ani poziomu poprawek. Nie znaleziono tabeli wersji produktu
w odczytanych metadanych. Raport: `artifacts/original/executable-metadata.json`.

W 409 odzyskanych plikach nie znaleziono osobnych źródeł o rozszerzeniach
`.c`, `.cpp`, `.h`, `.hpp`, `.cxx`, `.inl`, `.cs`, `.pas`, `.s`, `.asm`, `.dsp`,
`.dsw` ani `.pdb`. To ustalenie dotyczy tego katalogu; nie dowodzi braku źródeł
w nieodczytanym podformacie lub poza dostarczoną płytą.

W pliku wykonywalnym występuje 145 tekstowych odwołań do ścieżek źródłowych,
np. `E:\MyProjects\ancient\artem\L_Ai.cpp` (dokładny offset dla każdej nazwy
podaje raport JSON),
`brain\miss000.cpp`–`brain\miss013.cpp` i `Ai\Boss_kib.cpp`.
Są to ciągi diagnostyczne w programie, a nie zawartość kodu źródłowego.
Nadają punkty zaczepienia do dalszej analizy binarnej, lecz nie definiują reguł AI.

Potwierdzone importy `DDRAW.dll`, `DSOUND.dll`, `DINPUT.dll`, `DPLAYX.dll`,
`WSOCK32.dll` i `WINMM.dll` wskazują zależności binarne. `WINMM.dll` zawiera
`mciSendCommandA` i `mciGetErrorStringA`. Nie ustalono jeszcze, które ścieżki audio
gra odtwarza ani jak obsługuje rozgrywkę sieciową.

## Odzyskana zawartość

| Grupa | Rzeczywiste pliki | Co pozostaje do sprawdzenia |
| --- | --- | --- |
| Gra i narzędzia | `ancient.exe`, `mapedit.exe`, `config.exe`, `sndcfg.exe` | Uruchomienie, konfiguracja, zależności i zapis zmian |
| Pomoc | `ancient.hlp`, `mapedit.hlp` | Pełna dekompresja tekstu, język i zgodność z wydaniem |
| Misje | Pary `missions/miss000.dkd/.dkx` do `miss013.dkd/.dkx` | Nazwy widoczne w grze, dostępność, kolejność i warunki ukończenia |
| Mapy własne | 25 par `custom/BATTLE01`–`BATTLE25`, 15 par `SINGLE01`–`SINGLE15` | Znaczenie rodzin, liczba graczy, tryby i przechodniość |
| Dane współdzielone misji | Pary `missions/maplib`, `missions/controlm` | Zależności i semantyka wpisów |
| Demonstracja | `demo.dkd`, `demo.dkx` | Format poleceń, odtwarzanie i zegar |
| Muzyka MIDI | `SOUND/ANCIENT1.MID`–`ANCIENT4.MID` | Instrumentacja, synteza, momenty i pętle odtwarzania |
| Filmy | `VIDEO/LOGO1.AVI`, `LOGO2.AVI`, `TITLE.AVI`, `MIS000.AVI`, `OUTRO0.AVI` | Wyzwalacze, pomijanie, proporcje i miks dźwięku |
| Audio płyty | TORY 02–08 zachowane jako surowe `.cdda` | Kolejność w grze i kolejność bajtów próbek przed konwersją WAV |

Liczba 14 par `miss...` nie jest jeszcze potwierdzoną liczbą grywalnych misji;
plik może należeć do wprowadzenia, demonstracji albo scenariusza specjalnego.
Analogicznie 40 par map nie stanowi dowodu działania 40 trybów.

Próbka `VIDEO/MIS000.AVI` ma Cinepak 400×184 przy 20 kl./s, stereo PCM16LE
22 050 Hz i długość 137,55 s (odczyt `ffprobe`). Klatka z 30 s jest materiałem
filmowym, nie zrzutem rozgrywki: `artifacts/original/mission-video-frame.png`.

## Grafika, fonty i dźwięki

Rozpoznano indeksy DKX/DKD; [ASSET_FORMATS.md](ASSET_FORMATS.md) dokumentuje
potwierdzone pola i ograniczenia dekoderów. W pięciu kontenerach płyty są:

| Kontener | Liczba indeksowanych wpisów |
| --- | ---: |
| `DATA/CONTROLG` | 4 470 |
| `DATA/DATAMAP` | 1 715 |
| `DATA/OBJECTS` | 57 744 |
| `SOUND/SOUNDS` | 391 |
| `VIDEO/TASKS` | 1 |

Liczby obejmują różne typy rekordów, w tym metadane; nie są liczbą obiektów gry
lub gotowych klatek animacji. Część obrazów i PCM została odczytana do PNG/WAV;
raporty `artifacts/original/asset-*.json` zachowują nazwy, offsety i hashe.
Odczyt pikseli nie ustala jeszcze przezroczystości, kotwic, warstw ani czasu klatek.
Pełny katalog 62 kontenerów (także instalatora) obejmuje 76 243 wpisy.
Raporty końcowe `asset-final-*.json` dokumentują eksport 5275 obrazów DIB,
164 klipów PCM i 31 zestawów fontów z 74 atlasami. Hashe plików wynikowych
sprawdzono ponownie: `artifacts/original/export-integrity-final.json`.

W `CONTROLG` występują m.in. rekordy fontów `0SYSTEM_FONT`, `3SYSTEM_FONT`,
`LITTLE_FONT`, `NUMBER_FONT`, `BUT_FONT`, `BSLT_FONT`, `INT_FONT`, `HELP_FONT`,
`FISH_FONT` i `MONEY_FONT` (część nazw ma prefiksy wariantów). To rzeczywiste
rekordy własnego formatu, nie potwierdzone pliki TTF/OTF. Odczytano prostokąty
glifów i liczbowe kody; kodowanie, advance, baseline, kerning i łamanie tekstu
wymagają odrębnej interpretacji i porównania.

## Punkty odniesienia do pomiarów zachowania

Poniższe scenariusze są listą przyszłych pomiarów, **nie wynikami testów**.
Offsety oznaczają pozycje ciągów ASCII w `installed/ancient.exe`, nie adresy funkcji.

| Scenariusz | Punkt zaczepienia w danych | Wymagany zapis referencyjny |
| --- | --- | --- |
| Start i wybór scenariusza | `NUM_MISSION`, `0x1bc918`; pary `miss...`, `BATTLE...`, `SINGLE...` | Pełne menu, nazwy i kolejność, ustawienia, faktycznie załadowany plik |
| Ruch i zatrzymanie | `CBUT_MOVE`, `0x1bcf70`; `CBUT_STOP`, `0x1bd2c8` | Wejścia, cel, pozycje i czasy przy kilku prędkościach renderowania |
| Walka i abordaż | `CBUT_FIRE`, `0x1bd2bc`; `CBUT_RAM`, `0x1bd26c`; `CBUT_BOARD`, `0x1bd278` | Zasięgi, stan początkowy, obrażenia, opóźnienia, wynik i losowość |
| Operacje zasobów | `CBUT_BUYFISH`, `0x1bcd14`; `CBUT_SELLFISH`, `0x1bcd24` | Koszty, stan przed/po, warunki dostępności i błędy graniczne |
| Zachowania AI | Teksty `CBUT_BEHPATROL`, `0x1bce28`; `CBUT_BEHCONVEY`, `0x1bce38`; odwołania do `L_Ai` i `Boss_kib` | Ślad decyzji dla kontrolowanych sytuacji; nazwy przycisków nie definiują algorytmu |
| Zapis/wczytanie | Obrazy `0CFILE_BMRKSAVE00` i `0CFILE_BMRKLOAD00`; katalog `savegame/` | Zrzut stanu przed i po, ten sam scenariusz, zegar i RNG |
| Fonty i układ UI | Fonty i warianty `0...`/`3...` w `CONTROLG`; `GAME_FIELD`, `0x1be5ec` | Obrazy wszystkich znaków i ekranów, metryki tekstu, reakcja na 1920×1080 |

Nie ustalono jeszcze wartości statystyk, zasad nawigacji, priorytetów AI,
częstotliwości symulacji, ziarna RNG ani warunków zwycięstwa. Odtworzenie tych
zachowań wymaga analizy kodu maszynowego i pomiarów działającego oryginału.
Nagrania zewnętrzne mogą uzupełnić obraz i interakcje, ale nie dowodzą pełnej
zgodności ukrytych reguł ani wszystkich scenariuszy.
