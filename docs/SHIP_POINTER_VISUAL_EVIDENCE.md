# Źródłowe zaznaczenie statku, kursor i potwierdzenie polecenia

Stan: 2026-11-03. Ten dowód dotyczy zdrowego `OBJ_0000000b`, normalnego trybu
mapy 1, pełnego zdrowia i kursorów 0/5/6/7. Nie potwierdza pełnej gry,
natywnego Windows11, wejścia systemowego ani finalnej oprawy2026.
Źródłowy EXE ma SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Wszystkie oryginały są odczytywane bez zapisu.

## Zaznaczenie jest osobnym animowanym sprite’em

`ShipClassTy::GetMessage` pod `0x4dc630`, komunikat `c453` z niezerowym
odbiorcą, tworzy sprite przez `0x4e0b80` i zapisuje `ship+252=1`.
Komunikat z zerem ustawia2, jeśli zaznaczenie istnieje. Wartość2 odtwarza
animację wstecz; nie usuwa jej natychmiast.

`0x4e0c80` wybiera nazwę `RAM_0%1dX0%1d` na podstawie rozmiaru głównego
sprite’a. Dla56×56 jest to typ7 `RAM_056X056`, mający10 klatek.
**Pełne bitmapy mają60×60**, mimo nazwy zasobu. Są centrowane na56×56,
więc kotwica wynosi `(mainX−2,mainY−2)`. Pierwsza klatka ma bbox
`12,12,36,36`, ostatnia `0,0,60,60`; przezroczystych marginesów nie usuwa się.

To slot4 kolekcji sprite’ów GameObj, niezależny od części składowych TYPE8
kadłuba i żagla. `50cb80→545e80→55db10` tworzy oddzielny globalny węzeł
z depth1020. Nie jest to wymyślony pierścień ani lokalna część4 kompozytu.

Nowy sprite ma frame0, interval0, lastCounter0 i nie jest opublikowany.
InitSprite nie ustawia flagi narysowania20. `SetImagesReg55e0e0` nie publikuje
obrazu niewidocznego węzła; pierwszy SetSprite następuje po kroku licznika.

`4e0d00` wykonuje transakcję przy unsigned `now−lastCounter > interval`:

1. Zapisuje stempel `now`, a stored frame≥10 sprowadza do9.
2. Wywołuje rzeczywisty GameObj setter `50d5f0` dla bieżącej klatki i pozycji.
3. Przy selected1 dopiero potem zwiększa stored frame o pendingSteps.
4. Przy stored frame≥10 pokazuje istniejący pasek zdrowia.
5. Przy deselect2 usuwa węzeł paska, zmniejsza stored frame o1 i po wartości
   ujemnej usuwa sprite oraz zeruje selected state.

Zatem published frame i stored frame różnią się. Reselect podczas animacji
wstecz zachowuje obecną klatkę, lecz nie odtwarza już usuniętego paska.
Dopiero całkowicie nowe zaznaczenie tworzy nowy węzeł paska.

`DrawSprite4df6e0` wywołuje `4e0d00` **przed** publikacją głównego sprite’a.
Po zakończeniu Life handler `GetMessage0` wywołuje je ponownie, jeśli stored
frame<10 lub trwa reverse. Ścisły stempel eliminuje podwójny krok przy tym
samym counter. W pełnym zdrowiu i po zakończeniu rozszerzania ramki dalsze
publikacje głównego sprite’a podtrzymują jej pozycję i pasek.

[Helper C#](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipSelectionProgression.cs),
[fixture](../tests/fixtures/ship_selection_visuals.json),
[native probe](../tools/probe_ship_selection_visuals.py),
[porównanie](../artifacts/world-input/visuals/selection-csharp-frozen.json).
**7 przypadków,407 stanów,226 publikacji,7 usunięć ramki i7 paska,5 kontroli API**
zgadza się z rzeczywistym C# skompilowanym z checked i warnings-as-errors.
Native wykonuje4e0b80/4e0d00/4e0cb0 oraz rzeczywisty50d5f0; granice dotyczą
alokacji/zasobów, renderer55ec00, IL i normalnego setjmp. Nie jest to
uruchomienie całego oryginalnego renderera lub całego Life.

## Pasek pełnego zdrowia

`50c890` tworzy callback IL o szerokości `selectorWidth−26=34` i wysokości4,
depth1020, początkowo ukryty. `50c7b0` rysuje go pod `(selectorX+14,selectorY)`,
czyli `(mainX+12,mainY−2)`. Dla packed health6464 callback `50c650`:

- wypełnia prostokąt32×4 kolorem0;
- rysuje wiersz1 od x1 do x30 indeksem palety200;
- rysuje wiersz2 od x1 do x30 indeksem199;
- nie zapisuje ostatnich dwóch kolumn przydzielonego34×4.

Dwa sentinelowe bufory potwierdziły dokładne piksele. Wykonano rzeczywiste
50c650,56ea10 i56f100; granicami są prostokątne wypełnienie DirectDraw,
lock/unlock powierzchni i setjmp. RGBA34×4 ma SHA256
`799e3913c5d94c75e4365476c9193255e7be7c901e3e8e84c78d22803233848c`.
Przezroczystość ostatnich dwóch kolumn oznacza brak zapisu do powierzchni.
Nie odtworzono tym zasobem innych wartości zdrowia ani innego formatu koloru.

Rzeczywista rejestracja21 dotychczasowych węzłów, następnie selector21 oraz
health22, daje przy wspólnym depth1020 kolejność końcową
`…health22,selector21`. Dla dotychczasowych rendererów10…43 oznacza to
**health44 i selector45**. Utworzenie, ukrycie i usunięcie wykonano przez
55db10/55dc20/55e080/55ed60 bez hooków. Nie rozszerza to dawnego kontraktu
normalnej kolejki na dowolne callbacki i recykling świata.

## Kursor i potwierdzenie

`SetGCType516e30` wybiera `CUR_STD_`, `CUR_OWN_`, `CUR_SELECT_`, `CUR_SEA_`
dla typów0/5/6/7. Sufiks jest N, gdy cursor+e6=0, i G w przeciwnym razie.
Hotspoty0/5/6 wynoszą0,0, a SEA7 ma−18,−17. Standardowy kursor i own/select
mają po jednej klatce21×22; SEA ma4 klatki40×41.

Źródłowe Init515c50 ładuje MENU_CUR i interval500. Dowód rozpoczyna się
w gotowym kontekście UI z aktywowanym kursorem; nie udaje kompletnego startu UI.
Następne interwały wynoszą10000ms dla0/5/6 i150ms dla7.
`516640` używa cached app milliseconds (`5417d0` odczytuje app+18) oraz
unsigned `(interval+lastTick) <= now`, bez nadrabiania wielu klatek.
SetGCType ładuje obrazy, rysuje przy **poprzednim** interwale i dopiero potem
zapisuje nowy interwał. Zmiana N↔G zachowuje poprawną klatkę SEA.

Life517540 wykonuje jeden draw: SetGCType rysuje sam, jeśli zmienił typ;
dodatkowy draw jest wykonywany tylko wtedy, gdy typ się nie zmienił.
Globalny Move518d90 ma inną kolejność: map-forward może zmienić typ i
narysować kursor na poprzednich screen71/75, po czym globalny handler zawsze
rysuje go na nowych screen+b1/b5. Ten przypadek może więc dać dwa wywołania.
Przy niezmienionych logicznych screen coordinates globalny Move niczego nie
rysuje. Dwa piksele diagnostycznego1920 odpowiadają jednemu źródłowemu pikselowi.

`CreateConfirmSprite515df0` tworzy typ7 `TAKE_CMD`,4 klatki21×27, depth1,
interval250, stored frame0 i stamp0. Normalny tryb mapy1 przekazuje world
pixels bez mnożenia przez8: pozycja wynosi `(worldX−11,worldY−24)`.
Pierwsza publikacja następuje po zwiększeniu klatki, więc zaczyna się od1.
Po opublikowaniu3 sprite jest usuwany przy **następnym** draw, nawet bez
kolejnych250ms. Zastąpienie potwierdzenia usuwa poprzednie od razu.

[Helper C#](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/PointerCursorProgression.cs),
[fixture](../tests/fixtures/pointer_cursor_visuals.json),
[native probe](../tools/probe_pointer_cursor_visuals.py),
[porównanie](../artifacts/world-input/visuals/cursor-csharp-move-final.json).
**8 przypadków,94 stany,44 operacje publikacji kursora,17 publikacji confirm,
5 usunięć i7 kontroli API** zgadza się z C# checked/warnings-as-errors.
Wykonuje się rzeczywiste funkcje kursora, InitSprite, SetImagesReg,
55e0e0/55eb50 i usuwanie; granice to zasoby, arena new/delete i setjmp.
Wektor dwukrotnego draw odtwarza sekwencję516e30→516640 i potwierdza
publikację confirm3 oraz natychmiastowe usunięcie przez drugi draw przy750ms.
Nie jest to wykonanie całej magistrali GetMessage518d90 i MapaTy.

## Zasoby i powtarzalność

[Stager](../tools/stage_ship_pointer_visuals.py) zapisuje oddzielny ósmy zestaw
`ShipPointerVisualsGenerated`, manifest schema1 i atlas1024×128 bottom-upRGBA.
29 obrazów obejmuje10 RAM, po2 STD/OWN/SELECT,8 SEA,4 TAKE_CMD i pasek34×4.
Każda klatka zachowuje pełną płaszczyznę, bbox, coverage i paletę maplib:PALETTE.
Siedem wejściowych plików ma osobne SHA guards. Stare zestawy nie są zmieniane.
Nie generuje się podglądu ani ZIP.

[Native pixels/cohort](../artifacts/world-input/visuals/pixels-native-first.json)
potwierdza28 bitmap i168 buforów oryginalnego RLE574290 bez hooków, dwa
bufory IL oraz powyższą kolejkę. [Testy](../artifacts/world-input/visuals/unit-tests-final.log)
obejmują native/C#, reselect, granice confirm, zmienione fixture,
siedem źródeł stagera, idempotencję i odmowę nadpisania uszkodzonego payloadu.
Aktualne testy kursora mają także osobny [log](../artifacts/world-input/visuals/cursor-tests-final.log).
Źródłowe piksele są wzorcem zgodności, a nie oceną jakości finalnej oprawy2026.
