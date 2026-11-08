# Natywny ekran 1920×1080 — wersja robocza

Ostatnia wiążąca instrukcja użytkownika ustala **1920×1080, proporcje 16:9,
pełny ekran dla całej gry**. Dotyczy to rozgrywki, kamery, interfejsu i nowej
oprawy. Poprzednie wymaganie 1280×1024 zostało zastąpione; jego artefakty
pozostają historycznymi dowodami wcześniejszego etapu.

Projekt: `Unity/AncientConquest`, Unity `6000.3.27f2`.

## Kontrakt nowego obrazu

`NativeMenuCanvas` i ustawienia playera mają wskazywać 1920×1080.
`NativeMenuFrame` ma wypełniać cały viewport, z kamerą `rect(0,0,1,1)`,
bez pasów i bez projekcji całej starej klatki 800×600. Tło, poszczególne
przyciski i fonty pozostają oddzielnymi warstwami. Proporcje kształtów
muszą być zachowane, a położenia UI dostosowane do nowego płótna 16:9.

Nowe tło musi dostarczać co najmniej 1920×1080 detali i być przygotowane
w proporcjach 16:9. Samo rozciągnięcie poprzedniego tła lub statycznej planszy
nie spełnia wymagań oprawy. Każda nowa generacja/staging wymaga zapisu
pochodzenia, wymiarów i hashy. Ostateczny tryb obrazu, Alt+Tab oraz wydajność
nadal wymagają pomiarów na natywnym Windows 11 i docelowym laptopie.

Kod i staging wskazują już nowy cel. Odczytano następujące dane z bieżącego
manifestu i rzeczywistego pliku tła; wyniki nowego buildu i uruchomienia są
osobnym krokiem i należy je odczytać z [VALIDATION.md](VALIDATION.md).

| Parametr bieżącej generacji | Wartość |
| --- | --- |
| Płótno UI i żądany obraz playera | 1920×1080, 16:9 |
| Schema manifestu | 3 |
| Prostokąty sześciu przycisków: lewy górny róg | `(220,418)`, `(316,511)`, `(412,605)`, `(508,698)`, `(604,792)`, `(700,886)` |
| Rozmiar pojedynczego przycisku | 313×72 |
| Atlas: sześć kolumn i cztery stany | 1878×288, 2 163 456 bajtów RGBA |
| Statyczna warstwa diagnostyczna UI | 1920×1080, 8 294 400 bajtów RGBA |
| Tło robocze | `artifacts/native-art/menu-background-widescreen-draft.png`, 1672×941 |

Tło ma SHA-256
`d999d1294806d76cb838f39a57e591d9ecda51b176d61bc95fa419078278c4ee`.
Generator zwrócił 1672×941 mimo żądania wyższej rozdzielczości. To
**tymczasowo powiększany szkic, poniżej docelowej jakości detalu**, nie
natywna tekstura 1920×1080 ani ostateczna oprawa 2026. Stager zachowuje
surowe piksele (6 293 408 bajtów RGBA), a powiększenie wykonuje GPU podczas
pełnoekranowego renderowania. Zmiana kanałów i kolejności wierszy nie tworzy
nowych szczegółów. Manifest jawnie zapisuje `background_upscale_draft: true`.

## Zachowana implementacja interakcji

`MainMenuButton` zawiera czystą regułę stanów z oryginalnego handlera typu 1.
Cztery stany to 0 — wyłączony, 1 — normalny, 2 — naciśnięty, 3 — najechanie.
Normalny stan korzysta z wariantu fontu 2. Warianty sprite’ów i rysowanie
fontów ustalono z kodu: [MENU_INTERACTION_EVIDENCE.md](MENU_INTERACTION_EVIDENCE.md).
Przyciski i fonty są nadal rekonstrukcją oddzielnych warstw bitmapowych;
antyaliasing nie zastępuje docelowej pracy nad jakością oprawy w 2026 roku.

`NativeMenuFrame` przekazuje zdarzenia Input System 1.20.1 w kolejności przez
`InputSystem.onEvent`, również down/up dostarczone w jednej klatce.
W `OnEnable` zachowuje poprzednie `disableRedundantEventsMerging` i ustawia
je na `true`, ponieważ scalenie ruchu poza przycisk i z powrotem zgubiłoby
anulowanie przeciągnięcia. `OnDisable` usuwa subskrypcje i przywraca ustawienie.

Utrata fokusu, odłączenie/wyłączenie bieżącej myszy i wyłączenie komponentu
anulują naciśnięcie. `requireLeftRelease` wymaga zaobserwowanego zwolnienia
przed nowym kliknięciem. To polityka adaptera Unity, oddzielna od porównanej
reguły oryginału. Nie dodano obsługi klawiatury ani nowych skrótów.

`Quit game` wywołuje `Application.Quit`; oryginalne wygaszenie palety HLS
pozostaje nieodtworzone. Pozostałe przyciski emitują rozpoznaną komendę do
logu, ale ich ekrany i scenariusze nie są podłączone. To prototyp menu,
bez działających misji i kompletnej gry.

## Dane i przygotowanie

Runtime ładuje osobne tło i atlas przycisków. Statyczny `MenuUiRgba` jest
zachowany do diagnostyki, a runtime go nie ładuje. Wiersze RGBA są zapisane
od dołu do góry dla `Texture2D.LoadRawTextureData`; tekstury nie mają mipmap
ani kompresji importera i są zwalniane przy zniszczeniu komponentu.
Rysowanie odbywa się podczas Repaint.

Narzędzie `tools/stage_native_menu.py` weryfikuje hashe źródeł, odmawia
niezgodnych danych i wymaga jawnego `--replace-generated` przy zmianie
istniejącej generacji. Domyślnie wymaga co najmniej 1920×1080 detali tła;
poniższy wariant roboczy wymaga osobnej, jawnej flagi:

```sh
.venv/bin/python tools/stage_native_menu.py \
  --background artifacts/native-art/menu-background-widescreen-draft.png \
  --background-sha256 d999d1294806d76cb838f39a57e591d9ecda51b176d61bc95fa419078278c4ee \
  --allow-draft-upscale --replace-generated
```

Nie używać starego tła 5:4 do nowej generacji. `--allow-draft-upscale` nie
oznacza spełnienia wymagań końcowej jakości tekstur.

Budowanie pozostaje przez `AncientConquest.Editor.BuildReferenceWindows.Build`.
`tools/smoke_native_menu.py` zapisuje osobny świeży katalog dowodów,
`launch.json`, zrzuty, `report.json` albo `failure.json`. Obsługuje
`--diagnostics`, a cleanup sygnalizuje wyłącznie własne procesy playera
oraz Xvfb. Wymiary ekranu, granice i środki przycisków pobiera z manifestu.
Odrzuca manifest innego celu niż 1920×1080.

`--presentation-only` sprawdza log wyłącznego pełnego ekranu, geometrię okna
i rozmiar zrzutu bez wstrzykiwania zdarzeń myszy. Raport jawnie rozróżnia
ten zakres od sprawdzenia kliknięć i Quit; własny player jest kończony
cleanupem, bez deklaracji normalnego wyjścia gry. Tryb służy niezależnej
kontroli obrazu podczas diagnozy Unity RAWINPUT pod Wine. Nie omija ani nie
uznaje za zaliczone testów interakcji.

## Historyczne dowody wariantu 1280×1024

Poprzedni staging miał schema 3, tło 1402×1122 oraz atlas przycisków
1668×256 (sześć kolumn 278×64, cztery stany). Statyczna warstwa diagnostyczna
miała 1280×1024. To dane poprzedniej generacji, nie parametry nowego obrazu.

Przed migracją wykonano **70 testów unittest bez pominięć**; log:
`artifacts/unity-reference/full-tests-interactive.txt`. Zestaw obejmował
staging, hashe, odmowę nadpisania, orientację RGBA i osiem wykonywanych
przypadków C# viewportu. Po zmianie płótna testy geometrii trzeba ponowić
na rzeczywiście zaktualizowanym kodzie i danych.

Niezależne od rozdzielczości czyste reguły porównano z instrukcjami x86:
przycisk — **150 kroków w 44 ciągach**, bramka AI — 35 przypadków,
`SingleStepClock.Begin/Complete` — **1287 przypadków**. Nie jest to dowód
poprawności adaptera Input System, renderowania ani kompletnego zegara gry.
Aktualne dowody kandydata należy czytać w [VALIDATION.md](VALIDATION.md).

Dalsze źródła: [SIMULATION_CLOCK.md](SIMULATION_CLOCK.md) oraz
[WORLD_ASSET_REFERENCE.md](WORLD_ASSET_REFERENCE.md) — dziewięć próbek świata
w rozmiarach źródłowych, z jawnym zakresem pewności kolorów. Same próbki nie
są ukończoną modernizacją tekstur lub modeli.

## Potwierdzony kandydat1920×1080

`windows-build-replay-frame-1920x1080.log`:0błędów/0ostrzeżeń.
`replay-1920x1080-presented/report.json`: rzeczywisty pełny player,
ExclusiveFullScreen, pięć przechwyconych stanów, sześć komend i normalny Quit/kod0.
Porównanie nieprzezroczystych pikseli wskazało właściwy stan atlasu w każdym
zrzucie, a anulowanie dało obraz identyczny z idle. To jawne syntetyczne
zdarzenia Input System przez normalny adapter; wejście OS i Windows11/laptop
pozostają niezweryfikowane. Bieżący pełny suite:71testów bezskip.
PaczkaUI: `AncientConquest-UIPrototype-Windows-x64-1920x1080.zip`,
176plików, CRC i SHA256 każdego pliku po dekompresji sprawdzone.
