# Pierwszy briefing — dane i warstwy natywne

Stan: 2026-11-02. `tools/stage_briefing.py` przygotowuje statyczny briefing
`miss000` na płótnie **1920×1080, 16:9**. Nie uruchamia oryginalnego EXE.
Integracja przejść oraz sprawdzenie w playerze są osobnym zadaniem runtime.

## Źródła i dwie korekty wcześniejszej analizy

Narzędzie sprawdza dokładne SHA-256 EXE, `controlm.dkx/.dkd` i `miss000.dkx/.dkd`
przed odczytem danych. Zasoby i ich offsety/hashe zapisuje w manifeście.
Oryginalne pliki pozostają nietknięte.

- Deskryptory `M_BUT2_` i `M_BUT3_` używają sprite’ów **116×40**, podczas gdy
  przyciski głównego menu mają 174×40. Natywne Start/Cancel mają **209×72**.
- Kontrolki trudności używają **`M_CHECK`**, nie `T_PLAYER6`. `LoadGraph`
  (`0x53d5a0`) zapisuje `T_PLAYER6` pod `StartSystem+0x194`, a `M_CHECK` pod
  `+0x19c`, które odczytują `0x53f2f0` i `0x53f4e0`. `M_CHECK0/1` mają23×23;
  nie należy używać 146×154 obrazu `T_PLAYER6` jako radiobuttona.

Prawdziwy typ kontrolki to `TabClassTy`, factory5 → `0x551a40` → `0x550ba0`.
Rekord niezaznaczony ma stan0, zaznaczony1. `PaintSTab` (`0x4eaa70`) wraz
z mapowaniem `0x4e9940` wybiera odpowiednio `M_CHECK0`/`M_CHECK1`. Etykieta ma
font BH wariant1 dla niezaznaczonego i wariant2 dla zaznaczonego. Brak osobnego
stanu najechania w tej konfiguracji. Domyślny Easy0 ma dowód w inicjalizacji
`0x5016a0` oraz `demo.DIFFICULTY`; nie jest arbitralnym wyborem stagera.
Szczegółową politykę wejścia weryfikuje osobna analiza kontrolek.

## DISCRIPTION: deserializacja i tekst

Rekord typu23 ma nagłówek24bajty: liczba slotów pod+8, pojemność+12,
przyrost+16. Po nim występuje bitmapa obecności `ceil(count/8)` bajtów,
z najstarszym bitem dla pierwszego slotu. Obecne sloty są kolejnymi łańcuchami
zakończonymi NUL. Stager zachowuje brakujące sloty; odmawia uciętego nagłówka,
bitmapy/stringa, niepoprawnych długości i nadmiarowych końcowych bajtów.
Wybrana misja ma tekst ASCII; inne kodowanie nie jest zgadywane.

Formatter `0x548240` grupuje fizyczne sloty NUL w akapity przez znacznik `@`.
NUL nie jest znakiem nowego wiersza. Każda grupa dostaje osobny prefiks dwóch
spacji. `0x547f40` tokenizuje z zachowaniem kończącego separatora i po każdym
fizycznym stringu dopisuje spację, o ile bieżący bufor nie jest pusty. Nie wolno usuwać podwójnych ani
końcowych spacji. Po zawinięciu tylko kolejne emitowane wiersze grupy tracą
początkowe SP/TAB. Pełny opis i wykonanie oryginalnego x86:
[BRIEFING_TEXT_EVIDENCE.md](BRIEFING_TEXT_EVIDENCE.md).

Wynik miss000 to dokładnie **15 wierszy**, w tym początkowy czterospacowy
wiersz. Wiersze, szerokości i wysokości stagera porównano z wykonanym oryginalnym
formatterem x86. Test repo zawiera digest wyniku, nie kopię prywatnego tekstu
misji. Mocniejszy probe wykonał także oryginalny lookup i pomiar szerokości/wysokości
fontu, bez hookowania metryk: wszystkie15wierszy i ich metryki są zgodne.

Font `0S_FNT_MH`, wariant2, odstępy1/1 i oryginalny wrap630 zachowują metryki.
`PaintSarr` wywołuje `0x547cb0(array,0,-1,0,0,2)`: `0,-1` oznacza index/count,
natomiast x/y wynoszą0/0 — **nie ma centrowania pionowego**. Wysokość tekstu
wynosi284 piksele źródłowe; y wierszy to0,19,…,266. Skala warstwy1.8 zachowuje
kształt glifów; nie rozciąga całego starego ekranu.

## Kontrakt dla Unity

`Assets/Resources/BriefingGenerated/BriefingManifest.json`, schema1:

| Plik / pole | Wymiary lub znaczenie |
| --- | --- |
| `BackgroundRgba.bytes` |1672×941; niezmienione piksele wybranego szkicu |
| `StaticUiRgba.bytes` |1920×1080, przezroczysta warstwa tekstu i nagłówka |
| `ButtonsRgba.bytes` |418×288; 2kolumny × 4stany, komórka209×72 |
| `DifficultyRgba.bytes` |504×149; 3kolumny po168×149, jedna na każdy wybór |
| `controls` |Start1010:620,977,209,72; Cancel1002:1091,977,209,72 |
| `text_rect` |237,144,1134,792 |
| `difficulty_rect` |1591,792,168,149 |
| `difficulty_controls` |Ikony41×41 przy1591,792 /846 /900; value0/1/2 |
| `default_difficulty` |0 = Easy |

Radio labels mają globalne x1656, y792/846/900; hitboxy obejmują wyłącznie
ikony. Nagłówek Difficulty level ma x1584,y729. Wszystkie napisy pochodzą
z oryginalnych RT_STRING albo DISCRIPTION, bez dopisywania treści.

Wiersze buforów idą od dołu do góry (`Texture2D.LoadRawTextureData`), RGBA32.
Manifest zawiera `payloads[name].bytes/sha256`, source hashes, pochodzenie tła,
wymiary atlasów, prostokąty, oryginalne wiersze oraz ograniczenia. Istniejące
identyczne pliki są ponownie używane. Różne dane wymagają `--replace-generated`,
które najpierw sprawdza hashe poprzednich buforów. Symlinki są odrzucane.

Tło `briefing-background-widescreen-draft.png` ma SHA-256
`a2771579fafc083f6f7640975a5e91ab26bc2809b69e461580f1e36a30063492`.
Źródło jest mniejsze od docelowej rozdzielczości: wymagane jest jawne
`--allow-draft-upscale`, a `background_upscale_draft=true` pozostaje w manifeście.
Stager go nie skaluje ani nie przycina. To **roboczy szkic**, nie gotowy detal
natywny2026. Także bitmapowe fonty i przyciski wymagają finalnego opracowania.

```sh
.venv/bin/python tools/stage_briefing.py \
  --background artifacts/native-art/briefing-background-widescreen-draft.png \
  --background-sha256 a2771579fafc083f6f7640975a5e91ab26bc2809b69e461580f1e36a30063492 \
  --allow-draft-upscale \
  --preview artifacts/briefing/new-preview
.venv/bin/python -m unittest tests.test_stage_briefing -v
```

Osiem focused testów przeszło, bez skip; obejmują obecność/null bitmapy,
uszkodzone dane, tokeny/formatowanie, faktyczny wynik x86 miss000, proporcje,
orientację RGBA, idempotencję i odmowę nadpisania zmodyfikowanego bufora.
Rzeczywisty staging wykonano dwukrotnie z identycznym wynikiem. Trzy wyjściowe
warstwy PNG obejrzano w `artifacts/briefing/first-native-1920x1080/`.

## Jawne ograniczenia tego etapu

Tekst jest od razu w całości widoczny. Nie odtworzono jeszcze ujawniania
w czasie, skip/voice, pętli audio ani przejść filmowych. `Start` jest w runtime
celowo wyłączony, dopóki wierna rozgrywka nie jest gotowa; atlas nadal eksportuje
wszystkie cztery stany. To jawna różnica prototypu, nie twierdzenie o oryginale.
Wybrany prefiks zasobów0, paleta w uruchomionym oryginale oraz pozostałe misje
wymagają porównania runtime. Żaden z tych eksportów nie dowodzi pełnej gry.

## Zintegrowany i sprawdzony runtime

NativeMenuFrame otwiera BriefingPanel poStartscenario. Panel współdzieli
RgbaResourceTexture i zachowuje cacheDifficulty poCancel/reopen; Start jest
nieaktywny do czasu gotowej symulacji. WybórnaDown/ikonaOnly, Cancel i powrót
sprawdzono w rzeczywistymplayerze1920×1080 przez39etapów i11zrzutów.
Osobna regresja menu przeszła27etapów/5zrzutów; oba wyjścia przezQuit mająkod0.
Dowody: `artifacts/briefing/player-native-ui-sampling/report.json` i
`artifacts/briefing/menu-regression-final/report.json`; to synthetic InputSystem
onEvent, nie dowód wejścia OS lub laptopa. Pełny suite:80testów bezskip.

Pierwszy test obrazu wykrył dodatkową interpolację natywnego UI: średni błąd
nieprzezroczystych pikseli tekstu5.696 i wyboruEasy4.707. Gotowe warstwy mają
już antyaliasing w natywnym rozmiarze, więc UI/atlasy zmieniono zBilinear naPoint;
tła pozostałyBilinear. Przy tych samych progach4 błąd tekstu spadłdo0.0233,
Easydo0.0202. Nie zmieniono pikseli, fontów ani tolerancji testu.
Nieudana próba zachowana w `player-integration-first/`.
