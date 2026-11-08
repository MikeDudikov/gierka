# Walidacja diagnostycznego ruchu statku

Narzędzie `tools/smoke_ship_movement.py` sprawdza jeden jawnie przygotowany
ruch `OBJ_0000000b` z `(16,2)` do `(15,3)`. Warunki to heading 5,
wind force 0, wind heading 5, upgrade 0, pełne zdrowie, siedem nieruchomych
pozostałych statków floty oraz jedna źródłowa trasa dwóch punktów. Nie jest to
test wejścia myszy, ogólnego pathfindingu, AI ani grywalnej misji.

**Końcowy wynik: PASS** —
`artifacts/movement/runtime-complete-final/report.json`, SHA256
`adc1e6d873d06e17d385dc2bb15f1b0ac57d8535b442090467889d2b270ce8ed`.
Dwie sesje dostarczyły dziewięć dokładnych kadrów 1920×1080: globalny
RGB mean/max 0 oraz 27 kompletnych ROI statków z błędem 0. Cleanup zwolnił
odpowiednio osiem i dziewięć claimów; oba playery zakończyły się kodem 0.
Użyto helpera `ac37af28a8adbe67ee4b1e1d06a54ba15f9bd70edb3f99a2429ae2f9efaa6694`
i tej samej DLL `4d31ab124c18d6d0d0e935e0325d79782bfac160cf2d56aad1945e9a9903504c`.
Nie przebudowano runtime w celu poprawienia obserwatora obrazu.

Player Windows Mono jest obserwowany pod Wine/Xvfb w 1920×1080, fullscreen.
Kamera diagnostyczna ma origin `(9,0)`, scale 2. Dzięki temu pełne płaszczyzny
statków `0b/0c/0d` pozostają w kadrze. Origin `(0,0)` umieszczałby cały
badany ruch poza widocznym zakresem X, więc nie służy do tej kontroli.

## Niezależne oczekiwania

Obraz powstaje przez odczyt chronionych SHA oryginalnych danych i ich
dekodowanie w Pythonie, bez wywoływania metod renderera C#. Obejmuje cały
kadr: teren, pięć raf, osiem referencyjnych statków i znaną kolejność grup.
Poza kadrem pozostaje pięć statków, ale ich wpisy są zachowane w modelu świata.
Ruchomy statek zachowuje kolejkę części 17/23/24; jego body depth
19812…19748 nie przecina następnej nieruchomej grupy o depth 19676.
Nie jest to dynamiczny sorter całego świata.

Przypięte fixture źródłowe:

| Dane | SHA256 |
| --- | --- |
| `prepared_ship_movement.json` | `28931c2849e05f46c7fd005c0f7b923f1d19bf26c045148a1a2388191cf2d374` |
| `ship_forward_publication.json` | `9567c1a18cd894892af9a97841ff5c73399a0b0030847a7a562a064b2f42b666` |
| `ship_a_pose_selection.json` | `b1bc3be7a6db713b4055eddf949c07340436cb644fcccb1aa97c834a93b362a0` |

Pierwszy fixture dostarcza pełny native trace, drugi osobno przechowaną
i faktycznie opublikowaną klatkę, trzeci wybór części i kolejność loadera
type8 oraz dowód source RLE. Sprawdzono staged atlas 88 pozycji, 264
odniesień i 152 unikalnych bitmap względem źródłowego dekodera i fixture.
Manifest ma SHA `6aa1c312fa979993dc950df862bea69ee8e1522a3c7d1197dfe9583fc64ab5fc`,
a 1906688 B atlasu — `9b204db564030e808e6ef067aa64caef8f3f462ae555d186b55b04916193fb82`.

| Stage / call | World | Cell | Stored / drawn frame | Occupied / reserved |
| --- | --- | --- | --- | --- |
| initial / 0 | 1028,132 | 16,2 | 20 / 20 | 8 / −1 |
| reserved / 1 | 1028,132 | 16,2 | 20 / 20 | 9 / 87 |
| animation-only / 3 | 1028,132 | 16,2 | 21 / 20 | 9 / 87 |
| first-pixel / 5 | 1027,133 | 16,2 | 21 / 21 | 9 / 87 |
| before-transfer / 29 | 994,166 | 16,2 | 21 / 21 | 9 / 87 |
| transferred / 30 | 991,169 | 15,3 | 22 / 22 | 8 / −1 |
| arrived / 44 | 964,196 | 15,3 | 22 / 22 | 8 / −1 |

Log zawiera dodatkowo counter, state, speed, remainder, deceleration,
next, center_gate i last_tick. Wszystkie wartości są porównywane z native
trace. Trzy wpisy części każdego stage odczytują nazwę sprite’a,
sortingOrder i pozycję renderera. Stage 3 rozróżnia zmianę stored frame
od publikacji: obraz pozostaje source20 pomimo stored21. Kontrola samego
przybycia tego błędu by nie wykryła.

## Kryteria i dwie sesje

Pełny przebieg wykonuje siedem checkpointów i zwalnia osiem claimów.
Oddzielny player zatrzymuje się przy call 1, po rezerwacji celu: musi
zwolnić **dziewięć** claimów. Ten przypadek nie może ogłosić arrived ani
pełnego completion. Oba playery muszą zakończyć się kodem 0 przez
diagnostyczny timer. Nie jest to kontrola przycisku Quit produktu.

Każdy kadr musi przejść dotychczasowe progi globalne: mean RGB < 1,
odsetek pikseli z błędem kanału > 4 najwyżej 0,005, brak jednobarwnego
lub magenta framebufferu. Ten nowy tryb wymaga dodatkowo **global max
channel error ≤ 4**. Nie zawiera tekstu ani antyaliasingu, więc ograniczenie
obejmuje każdy piksel kadru. Każda z trzech kompletnych płaszczyzn statków
ma osobno mean RGB < 1, mean źródłowego pokrycia < 1 i max channel error ≤ 4.
Nie stosuje się masek wyłączających UI ani wybranych próbek obrazu.

Każdy checkpoint zatrzymuje zegar harnessu na 1,25 s. Observer ma najwyżej
1 s na uzyskanie właściwego framebufferu w **tym samym** stage. Przed
i po każdej próbie sprawdza niezmienność całego zaobserwowanego stanu
i wpisów części. Zmiana stage lub pola kończy kontrolę błędem. Poprzedni
framebuffer nie jest akceptowany jako nowy obraz, nawet jeśli globalny
mean przechodzi. Każda nieudana próba zachowuje PNG i metryki; następna
może być przyjęta wyłącznie po przejściu tych samych ścisłych progów.
Trwale błędny obraz kończy się porażką, bez rozszerzania deadline.

## Zachowany pierwszy błąd obserwacji

`artifacts/movement/runtime-final` zachowuje pierwszy nieudany przebieg
na DLL `4d31ab124c18d6d0d0e935e0325d79782bfac160cf2d56aad1945e9a9903504c`.
Pierwsze trzy kadry były dokładne RGB, a pierwszy odczyt stage5 był
**identyczny z poprzednim obrazem**, mimo poprawnych pól i wpisów renderera.
Niezależne `first-failure-analysis.json` potwierdza mean/max 0 względem
initial oraz mean 0,08793595679 / max 209 względem właściwego stage5.
To potwierdzenie starego odczytu framebufferu, a nie zgodności z nowym stage.

Pierwszy helper robił pojedynczy odczyt natychmiast po logu po
WaitForEndOfFrame. Dodano bounded presentation retry w obrębie stage;
nie zmieniono C#, DLL, danych stanu ani progów obrazu. Wersje helpera
0bcbea…, 879be4… i ac37af… zachowano z pełnym SHA w
`artifacts/movement/helper-history`.

Pierwsze pure controls zachowano w `artifacts/movement/qa-helper-controls`:
304/306 spełniło oczekiwania. Dwie celowe sprzeczne dodatkowe linie
COMPLETE/HALTED ujawniły brak kontroli wszystkich linii tego prefiksu.
Guard poprawiono tak, aby końcowa lista była dokładnie jednym właściwym
markerem. PNG, logi i poprzedni raport pozostały zachowane.

Drugi przebieg, `artifacts/movement/runtime-strict-final`, przeszedł obie
sesje na tej samej DLL4d31: siedem pełnych checkpointów i dwa wczesnego
zatrzymania. Wszystkie dziewięć przyjętych kadrów miało global i ROI
RGB mean/max 0. Dwie pierwsze próby (`first-pixel`, `before-transfer`)
pokazały stary framebuffer; zachowano je, a druga próba w tym samym stage
uzyskała dokładny obraz. Pozostałe kadry zgadzały się przy pierwszej próbie.
Osiem i dziewięć claimów zwolniono zgodnie z oczekiwaniami; oba exit code 0.

Wersja879be4 przeszła 306/306 pure controls i dziewięć kontroli samego
presentation retry. Osobny dodatkowy probe ujawnił lukę wcześniejszego
kryterium obrazu: poprawny arrived wraz z pozostawionym całym starym
statkiem poza bieżącymi trzema ROI przechodził globalny mean i odsetek
błędów. `qa-helper-controls-final/ghost-control-report.json` i PNG zachowują
ten dowód. Dlatego wrapper nowego trybu dodaje global max ≤ 4, bez zmiany
niezmiennego helpera frozen-unit QA i bez jakiegokolwiek luzowania progów.
Dziewięć zapisanych poprawnych kadrów przeszło tę dodatkową kontrolę
z max0: `artifacts/movement/saved-captures-complete-guard.json`.

Na helperze ac37af… końcowe pure controls przeszły **318/318**:
306 kontroli obrazu/logów, dziewięć mocków capture, jeden ghost i dwie
granice globalnego błędu 4/5 poza bieżącymi ROI. Ten sam ghost PNG,
wcześniej przepuszczony, teraz jest odrzucany przez global max255.
Raport zbiorczy: `artifacts/movement/qa-helper-controls-complete/summary.json`.
Składają się na niego `report.json`, `capture-report.json`,
`ghost-control-report.json` i `global-boundary-report.json` w tym samym katalogu.
Kontrole capture potwierdzają zachowanie obu PNG przy stale→correct,
odrzucenie trwałego błędu do deadline 1 s, błędnej zmiany stage/pól,
spóźnionego poprawnego obrazu oraz wyjścia playera przed capture.
Nie uruchamiają usług ani nie zmieniają kodu runtime.

Ostateczny świeży przebieg `runtime-complete-final` z zaostrzonym globalnym
max odrzucił trzy stare odczyty: first-pixel, before-transfer i transferred.
W każdym właściwy obraz uzyskano przy drugiej próbie w tym samym stage;
pozostałe sześć kadrów pasowało przy pierwszej próbie. Wszystkie 12 prób
obrazu mają zachowane osobne PNG i metryki; do dziewięciu przyjętych
zaliczono wyłącznie ścisłe dopasowania. Wcześniejszy przebieg
`runtime-strict-final` miał dwa odrzucone odczyty i pozostaje dowodem
pośrednim. Końcowym dowodem jest `runtime-complete-final` z dodatkowym
global max ≤ 4.

Polecenie fresh QA:

```sh
.venv/bin/python tools/smoke_ship_movement.py --output artifacts/movement/runtime-complete-final
```

Narzędzie tworzy osobny Xvfb i proces playera dla każdej sesji, odmawia
użycia zajętego display79, zatrzymuje wyłącznie własne procesy i zapisuje
SHA DLL, EXE, pomocników, fixture, manifestów, payloadów oraz screenshotów.
Na tej podstawie nie wyciąga się wniosków o natywnym Windows 11, FPS,
docelowym laptopie ani finalnej oprawie 2026.
