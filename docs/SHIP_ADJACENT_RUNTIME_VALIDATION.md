# Walidacja ruchu do sąsiednich celów

Stan: 2026-11-02. Zakres: zamknięta projekcja source0b z(16,2), heading5,
wiatr0/kierunek5,upgrade0 i pozostałe siedem statków nieruchomych.
Cel obrazu pozostaje1920×1080,16:9,pełny ekran i pełny viewport.
Nie jest to pełna misja, ogólny pathfinding, sterowanie OS ani finalna grafika2026.

## Końcowy player

[Raport](../artifacts/adjacent/runtime-final/report.json) powstał w rzeczywistym
Windows x64 Mono playerze pod Wine11/Xvfb na buildzie Unity6000.3.27f2.
Build ma146207467 bajtów,0 błędów/ostrzeżeń. Assembly-CSharp SHA256:
`b4d0da08e2f6e1ec51e751de12a45c7057d4df0e6f827ace11576d15ffbb7cd1`.

| Przypadek | Cel | Wynik | Sprawdzone etapy | Zwolnione zajęcia |
| --- | --- | --- | --- | --- |
| h0 E |17,2|obrót i dojazd|8|8|
| h1 NE |17,1|obrót i dojazd|8|8|
| h2 N |16,1|odmowa źródłowego planera|2|8|
| h3 NW |15,1|odmowa źródłowego planera|2|8|
| h4 W |15,2|obrót i dojazd|8|8|
| h5 SW |15,3|dojazd bez obrotu|5|8|
| h6 S |16,3|obrót i dojazd|8|8|
| h7 SE |17,3|obrót i dojazd|8|8|
| halt-turn |17,2|przerwanie po pierwszym kroku obrotu|2|8|
| halt-reserved |15,3|przerwanie po rezerwacji|2|9|

Wszystkie10 sesji zakończyły się exit0. Wszystkie53 zaakceptowane kadry
mają globalne RGBmean/max0 i100% dokładnych pikseli;159 regionów trzech
widocznych statków również ma RGBmean/max0. Nie zmieniano C# po buildzie.
Pilot h0 stanowi osobny wcześniejszy przebieg8 kadrów/24 ROI, również RGB0:
[raport pilota](../artifacts/adjacent/runtime-first-h0/report.json).
Nie sumujemy go do53 kadrów końcowego zestawu.

Etapy pochodzą ze zdarzeń: initial,turn-start,turn-published,turn-complete,
reserved,first-pixel,transferred,arrived albo rejected. Przerwania są osobnymi
sesjami. Jeśli kilka zdarzeń wystąpi w jednym wywołaniu, mają ten sam licznik
źródłowy i osobne zatrzymania bez wykonywania dodatkowego kroku.
`turn-start` wykrywa pierwszą wewnętrzną klatkę32…55; w E jest to call1,
counter2,stored47/drawn20. Pierwsza publikacja następuje później.

## Niezależne dane oczekiwane

`tools/smoke_ship_adjacent.py` przypina fixture
`tests/fixtures/ship_adjacent_movement.json`, SHA256
`2ffc6d70e131770dc065b252e88818e02aca203f681ea1ff373875883f8e9075`.
Wybiera dokładnie h0_pending1…h7_pending1 z wariantu source_static.
Dodatkowe przypadki zajętego celu służą testom rdzenia i nie są przedstawiane
jako działająca misja playera.

Stany pochodzą z całego oryginalnego MoveShip i rzeczywistego planera
uruchomionych w x86 z opisanymi granicami usług. Oczekiwane grafiki pochodzą
z oryginalnego TYPE8/RLE, palety i przypiętych88 póz. Manifest nowego renderera
nie definiuje samodzielnie oczekiwanych pozycji ani klatek. Dla każdej próbki
porównano28 pól stanu oraz faktyczne nazwy, pozycje i sortingOrder trzech
SpriteRendererów0b. Oczekiwany raster korzysta z opublikowanej klatki i pozycji,
nie z numeru wewnętrznego. Inne26 składników statków i pięć raf zachowują
zweryfikowaną kolejność badanego zbioru.

Kamera diagnostyczna9,0/skala2 pokazuje całe jednostki0b/0c/0d. Cały
obraz i bieżące regiony jednostek mają maksymalny błąd kanału≤4,
przy zachowaniu wcześniejszych progów średnich. Końcowe rzeczywiste błędy
wynoszą0. W całym kadrze sprawdzamy maksimum, żeby wykryć także pozostawioną
starą grafikę poza aktualnym ROI.

## Prezentacja i kontrole negatywne

Każdy etap jest zatrzymany na1,25s. QA może oczekiwać najwyżej1s na jego
prezentację; przed i po każdej próbie sprawdza niezmienność wszystkich pól,
etapu oraz odczytów rendererów. Zachowuje odrzucone obrazy i metryki.
Przekroczenie czasu, zmiana etapu i niezgodność kończą test błędem.

W końcowym przebiegu wykonano75 prób:53 zaakceptowano,22 odrzucono przed
poprawną prezentacją. Dokładnie8 odrzuconych obrazów było identycznych z
wcześniejszym zarejestrowanym etapem. Pozostałych14 nie określamy tak bez
osobnego dowodu; żadnego nie zaliczono jako poprawny bieżący kadr.
Nie luzowano progów i nie zmieniano danych ani DLL w celu uzyskania zgodności.

Pięć testów `tests/test_smoke_ship_adjacent.py` przeszło. Obejmuje macierz
49 etapów ośmiu celów/53 wraz z przerwaniami i31 jawnych negatywów:
24 mutacje logów,5 mutacji pikseli i2 błędne warunki fencing. Osobno sprawdza
stale→correct retry. Pełny zestaw projektu:155 testów,0 pominięć w58,160s.
Końcowy helper SHA256:
`57ffd9f99c3727ec13c9617f03a3bb062dcd02380082f88c44d693cf614571c6`.

## Odtwarzanie i granice

```sh
.venv/bin/python tools/smoke_ship_adjacent.py --case h0 --output artifacts/adjacent/<nowy-pilot>
.venv/bin/python tools/smoke_ship_adjacent.py --output artifacts/adjacent/<nowy-katalog>
```

Sesje uruchamiać kolejno, z własnym Xvfb/playerem i wolnym`:79`.
Nie budować do katalogu uruchomionego playera ani kończyć globalnie Wine.
W tym hoście Editor i Wine wymagają IPC poza sandboxem.

Planowanie przycounter1, a kolejne kroki przy2… to jawny harmonogram tej
próby. Pełny source Life może planować i wywołać MoveShip w tym samym counter.
Zatrzymania harnessu nie dowodzą tempa całej gry ani jej trybu pauzy.
Po przybyciu grafika jest zamrożona, bez idle RNG. Brak próby fizycznej myszy,
natywnego Windows11, wydajności laptopa, AI/walki i całego świata.

Zgodnie z aktualną preferencją użytkownika etap jest przekazywany jako kod
i dokumentacja: bez nowego ZIP i bez generowanego podglądu dla prezentacji.
Pliki framebufferów w QA są wewnętrznym dowodem walidacji.

Powiązania: [kinematyka](SHIP_ADJACENT_MOVEMENT_EVIDENCE.md),
[nawigacja](SHIP_ADJACENT_NAVIGATION_EVIDENCE.md), [obrót](SHIP_TURN_ANIMATION_EVIDENCE.md),
[czas i kolejność](SHIP_ADJACENT_WORLD_EVIDENCE.md), [bieżąca walidacja](VALIDATION.md).
