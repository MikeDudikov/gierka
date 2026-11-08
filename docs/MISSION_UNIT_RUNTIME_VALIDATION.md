# Kontrola obrazu ośmiu referencyjnych statków miss000

`tools/smoke_mission_units.py` obserwuje prawdziwy player Windows Mono pod
lokalnym Wine/Xvfb. Sprawdza jawny tryb `--mission-unit-reference`, który
pokazuje teren, pięć zamrożonych raf oraz osiem zamrożonych statków.
Nie uruchamia grywalnej misji, konstruktorów oryginału, ruchu, AI ani animacji.

Obowiązujący obraz to **1920×1080, 16:9, pełny ekran i pełny viewport**.
Skala diagnostyczna2× oznacza kadr960×540 źródłowych pikseli. Nie ustala
finalnego FOV remake’u ani nie jest nagraną pierwszą klatką oryginału.

## Uruchomienie

Po zbudowaniu aktualnego playera:

```sh
.venv/bin/python tools/smoke_mission_units.py --output artifacts/units/<nowy-katalog>
```

Katalog musi być nowy. Istniejące dowody pozostają zachowane. Test uruchamia
trzy sesje kolejno, każdą z własnym Xvfb i playerem. Odmawia przejęcia
istniejącego wyświetlacza`:79`, kończy wyłącznie swoje procesy i nie używa
globalnego kill Wine. W tym hoście usługi wymagają lokalnego IPC poza sandboxem.
Nie wolno budować do katalogu playera, gdy jest uruchomiony.

Narzędzie nie wstrzykuje wejścia OS, nie wywołuje metod C#, nie przełącza
sceny przez testowy API i nie wysyła poleceń jednostkom. Czyta logi, geometrię
okna oraz rzeczywisty framebuffer X11. Syntetyczne porównania samych obrazów
sprawdzają checker, lecz nie zastępują sesji playera.

## Niezależna referencja

Pozycje, modele i kierunki wynikają z pełnych616bajtów ośmiu źródłowych
payloadów w `tests/fixtures/mission_ship_seed.json`, a nie z deklarowanych
pozycji nowego renderera. Fixture ma przypięty hash:
`1ae221249bf8812b5a033c769134b22d6266e85d232d18a53e8473fa0cfcdab9`.
Każdy payload jest porównywany z rzeczywistym blobem stagedObjectSeeds.

Grafiki są dekodowane ponownie z hash-guarded `OBJECTS.DKX/DKD` oraz bazowej
PALETTE świata. Wybór type8, maski, nazwy klatek, offsety i localdepth muszą
zgadzać się z wykonanym oryginalnym loaderem w
`tests/fixtures/composite_original_selection.json`, hash:
`25e59c7365666e669edb6705b9c85fd5947cae5ba9c016a3563411a6d0818e50`.
Ten wynik zachowuje12przypadków loadera i340przypadków sortowania.
Wcześniejsza wersja różniła się wyłącznie hashami kodu dekodera po dodatkowym
sprawdzeniu masek; wszystkie przypadki źródłowe pozostały identyczne.

Kolejność grup pochodzi z
`tests/fixtures/mission_ship_world_order.json`, hash:
`0ee61b970675c19a0cdfc021ba223752d6694721074cbba0c900dd428f2be0c6`.
Oryginalna kolejka tej ograniczonej kohorty daje:

1. Osiem osobnych cieni o globaldepth21000, w odwróconej kolejności rejestracji.
2. Pięć raf o depth20200, również z udowodnionym porządkiem remisu.
3. Osiem grup kadłubów według malejącego
   `max(10000,20000−logicalHeight−worldY)`.

W każdej grupie kadłuba dodatnie komponenty są porządkowane oryginalną
metodą wymian parami po localdepth. Ujemny depth części oznacza oddzielny
sprite cienia, a nie przezroczysty lub nieistniejący komponent.
21grup rozwija się do29części statków oraz5raf, łącznie34rysowań nad terenem.
Nie deklarujemy zgodności kolejki całego świata z pozostałymi klasami i mgłą.

Dane przekazywane do Unity są dodatkowo sprawdzane względem tej referencji:

| Plik | Bajty | SHA256 |
| --- | ---: | --- |
| CellFlags.bytes |2304|`eb8c22b2dc3a3d6de5be5c5a28560701333cbc8610e8dd687052f4f93b260283`|
| ShipComponentsRgba.bytes |317952|`b5fe5fd59554f82ca710a9fdce4999ca7044b7c5dddb52e724dafbfb79de284c`|

Manifest `MissionUnitsManifest.json` ma przypięty hash
`2ec3b9ef431b1a36f1d267740605d2a2334988d1da2747160af69a081294fe2e`.
Kontrakt: schema1, miss000, mapa24×24,8statków,29instancji części,
17unikalnych klatek w atlasie1104×72 RGBA32 bottom-up.
Płaszczyzny atlasu muszą odpowiadać ponownie zdekodowanym grafikom źródłowym.
Hashy i geometrii nie zastępuje samo poprawne parsowanie JSON.

## Trzy kadry i osiem pełnych obszarów

| Sesja | Origin w komórkach | Statki sprawdzane w całości |
| --- | --- | --- |
| home-fleet |9,0|0b,0c,0d|
| south-fleet |0,15|10,27,28|
| adjacent-ships |0,10|29,2a|

Cały świat źródłowy jest najpierw składany zgodnie z kolejką grup i maskami,
a dopiero potem kadrowany. Widoczne fragmenty innych statków przy krawędzi
pozostają w porównaniu całego ekranu; nie są po cichu pomijane.
Kompletne obszary kontroli obejmują pełne logiczne płaszczyzny56×56,
64×64 lub72×72, po skali2×. Kotwica środkuje tę płaszczyznę w kaflu64,
zamiast dodawać bbox ponownie.

Wymagane są równocześnie:

- Pełny framebuffer1920×1080 ze średnim błędemRGB **ściśle poniżej1**.
- Co najwyżej0,5%pikseli z błędem dowolnego kanału większym niż4.
- Dla każdego z ośmiu pełnych obszarów statku średni błądRGB **poniżej1**.
- Osobno dla pikseli pokrytych źródłową maską części tego statku średni
  błądRGB **poniżej1**.
- W każdym pełnym obszarze statku maksymalny błąd dowolnego kanałuRGB
  **co najwyżej4**, również gdy średnie są mniejsze niż1.

Ostatni warunek zapobiega ukrywaniu brakującej małej części w tle całego
ekranu lub w przezroczystej części płaszczyzny. Na przykład w kontroli
usunięcia samego cienia statku0d średni błąd całej płaszczyzny wyniósł0,978,
ale na pikselach pokrytych źródłem2,245; checker odrzucił wynik bez zmiany progu.
Całkowicie zasłoniętej części lub nieobserwowalnego remisu nie da się
potwierdzić samym obrazem. Takie reguły mają osobne dowody oryginalnego kodu.

Kontrole negatywne wykryły lukę pierwszej wersji checkera: usunięcie małej
części TARAN w czterech statkach zmieniało112pikseli, ale średnia pokrytych
źródłem pikseli0,824 nadal mieściła się w progu1. Przestawienie dwóch
sąsiednich kadłubów zmieniało8pikseli i także przechodziło same średnie.
Zachowano nieudane kontrole i PNG w `artifacts/units/qa-helper-controls/`.
Dodano więc warunek maksymalnego błęduROI≤4; pozostałe progi pozostały
bez zmian. Odrzuca on te błędy z maksimum229 i81. To poprawka checkera,
nie zmiana grafiki, danych ani renderera. Rzeczywiste wcześniejsze capture
miały maksimum0, ale końcowy player jest sprawdzany ponownie mocniejszą kontrolą.

Puste, jednokolorowe i shader-magenta obrazy, zła rozdzielczość, brak klatki,
odwrócenie obrazu, błędny wariant, maska i kotwica muszą zostać odrzucone.
Zmiana sortowania jest kontrolą negatywną tylko wtedy, gdy zmienia widoczne
pokrycie alfa. Nie przypisujemy dowodu kolejności dwóm identycznym obrazom.

## Logi i zakończenie

W każdej sesji wymagane są również:

- ExclusiveFullScreen1920×1080 oraz okno0,0,1920,1080.
- Dokładnie8deklaracji źródłowych statków, bez braków i duplikatów,
  z poprawnym ID, komórką, wariantem, signed kierunkiem, klatką, maską,
  kotwicą i globaldepth.
- Dokładnie34deklaracje kolejki rendererów o unikalnych sortingOrder10…43:
  8cieni,5raf i21dodatnich części statków. Rodzaj, ID, sourcepart oraz depth
  muszą odpowiadać niezależnej fixture oryginalnego iteratora. Brak wpisu,
  duplikat, zły remis i przestawiona kolejność kończą test błędem, również
  wtedy, gdy źródłowe alfa nie pozwala wykryć przestawienia samym obrazem.
- 29rendererów, zero wykonanych konstruktorów źródłowych i frozenstate1.
- Częściowa siatka576komórek,8udanych zajęć,0kolejkowanych poleceń,
  `simulation=False` i `full_world_order=False`.
- Zwykłe zakończenie procesu kodem0 po diagnostycznym timerze8s.
- Po zakończeniu log zwolnienia wszystkich8własnych zajęć i wyczyszczenia
  referencji wizualnych; wymuszone sprzątanie nie zalicza wyjścia.

Dokładny marker końcowy to
`Mission unit reference cleanup: claimed_released=8; visual_refs_cleared=True`.
Marker timera pochodzi z istniejącej diagnostyki terenu; nie jest dowodem
działania produktowego Quit. Menu i briefing mają oddzielne replaye.

Źródło logów kolejki trzeba rozróżnić:29wpisów części statków odczytuje
rzeczywisty `SpriteRenderer.sortingOrder` przy tworzeniu renderera.
Pięć wpisów raf ponownie oblicza deklarowane sloty ze wzoru, zamiast
odczytywać właściwość renderera. Przegląd statyczny potwierdził zgodność
tego wzoru z przypisaniem slotów rafom, a captureRGB0 potwierdza widoczny
wynik. Porównanie34wpisów pozostaje zaliczone w tym zakresie; nie opisujemy
go jako34odczytów właściwości silnika.

Log gotowości nie wystarcza do zaliczenia pikseli. Narzędzie zachowuje
wszystkie próby capture i czeka na faktycznie przedstawioną klatkę. Jeżeli
nie pojawi się zgodny obraz, test kończy się błędem i zachowuje differencePNG.

Każdy przypadek zapisuje launch/provenance, logi playera/Wine/Xvfb,
geometrię, expectedPNG, rzeczywiste capture i ich metryki. FinalnyreportJSON
powstaje dopiero po trzech zaliczonych sesjach. DLL, executable, manifesty,
payloady, źródła, fixture i sam plik checkera muszą zachować te same hashe
przez cały test. Raport przypadku zawiera pełną zweryfikowaną kolejkę34
rendererów i hash fixture porządku źródłowego.

## Granice walidacji

Przygotowanie checkera i jego kontrole obrazów są niezależne od rzeczywistego
uruchomienia playera. Wynik konkretnego buildu należy odczytać z jego świeżego
reportJSON oraz z `VALIDATION.md`; sama obecność narzędzia nie oznaczaPASS.
Pierwszy rzeczywisty przebieg `artifacts/units/runtime-final/report.json`
potwierdził3kadry,8pełnych obszarów statków i zwolnienie8zajęć; wszystkie
badane RGB miały błąd0. Zachowano go przed dodaniem silniejszego sprawdzenia
logowanej kolejki34rendererów. Te same3logi przeszły następnie odczyt bez
uruchamiania usług (`artifacts/units/qa-existing-renderer-logs.json`).
Silniejszy test rzeczywisty z kontrolą kolejki przeszedł oddzielnie w
`artifacts/units/runtime-order-final/report.json`. Po wykryciu luki średnich
ROI zachowano ten raport i wykonano nową serię z ograniczeniem maksimum4:
**`artifacts/units/runtime-strict-final/report.json`**.

Końcowy przebieg obejmuje3nowe sesje playera na tym samym DLL
`518838f1952b31309238cbf9187cb00ea4bf0b76a1d882d101d17d60fbb209bb`.
Cały RGB i wszystkie8pełnych obszarów statków mają średni oraz maksymalny
błąd0; w każdej sesji kolejka34rendererów jest zgodna z fixture,
zwolniono8zajęć i proces zakończył się diagnostycznym kodem0.
Report wskazuje faktycznie użyty checker o SHA256
`00dcc8206b21ee447f088d37a87eff7e9cd123f077535bb07bd1f9c7992577d4`.

Osobne kontrole checkera w
`artifacts/units/qa-helper-controls-strict/report.json` przeszły88/88:
7poprawnych akceptacji i81odrzuceń. Obejmują brak każdego statku i cienia,
małe brakujące tarany, warianty, kotwice, maski, kierunki, kolejność tam,
gdzie jest widoczna, błędne deklaracje kolejki i cleanup. Granica maksimum
ROI4jest akceptowana,5jest odrzucana. Nie uruchamiały usług i mają ten sam
hash checkera co końcowy test rzeczywistego playera.

Wine/Xvfb nie potwierdza natywnego Windows11, fizycznej myszy ani wydajności
i5/16GB/RTX3050Ti. Nie ma pomiaru FPS, animacji, obciążenia pełnej misji,
zgodności AI i czasu, ekonomii ani audio. Statyczna grafika jest referencją
oryginału, nie finalną modernizacją2026. Normalny Start pozostaje niedostępny
do odtworzenia grywalnego świata.
