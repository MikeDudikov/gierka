# QA kolejki myszy w scenie statków

Stan: 2026-11-03. Ten etap sprawdza ograniczoną ścieżkę
`QueueStateEvent → InputSystem.onEvent → hover → źródłowe zwolnienie przycisku
→ membership41/action20 → ShipMoveOrder → renderer`.
Nie stanowi odbioru pełnej gry, oprawy 2026, sprzętowej myszy, natywnego
Windows 11 ani wydajności docelowego laptopa.

Dwa zakończone replaye build5 przeszły: 60 obrazów, pełne ciągi
liczników 0…101 i 0…197, dokładne pakiety 41/20 oraz 41/20/20 i zero różnic RGB. 14 testów
samego QA przeszło bez pominięć. Utrata fokusu pozostaje niezweryfikowana:
pięć prób jej wyzwolenia zakończyły się niepowodzeniem, a ostatni probe
Win32 nie zdołał aktywować Notepada. Nie wywoływano sztucznego callbacku
ani nie zmieniano gry w celu uzyskania pozytywnego testu.

## Kontrakt i niezależne wzorce

[Replay C#](../Unity/AncientConquest/Assets/AncientConquest/Runtime/ShipPointerInputReplay.cs)
dodaje własne urządzenie Mouse i wysyła wyłącznie stany przez
`InputSystem.QueueStateEvent`. Nie wywołuje domenowych metod wyboru ani ruchu.
Zatrzymanie zegarów, dodatkowe 750 ms czasu UI i odczyt checkpointów są jawnie
instrumentacją QA. Przesunięcie czasu UI nie przesuwa fazy fizyki.

[Helper](../tools/smoke_ship_pointer.py) porównuje producenta komend
z rzeczywistym `518070`, Fleet i serializacją uruchomionymi w
[native oracle](../tools/probe_ship_pointer_commands.py). Zaznaczenie i pasek
zdrowia rekonstruuje przez źródłowy `4e0d00`, wywołując go przy rzeczywistych
publikacjach kadłuba oraz w odpowiedniej gałęzi po Life. Ruch, cache, RNG,
rezerwacje i34 bazowe renderery pochodzą z dotychczasowego zamrożonego
wzorca natywnego dwóch tras. Osobne dowody wyjaśniają
[hover](WORLD_POINTER_HOVER_EVIDENCE.md),
[komendy](WORLD_POINTER_COMMANDS.md),
[projekcję różnych grup](WORLD_MEMBERSHIP_MOVEMENT_EVIDENCE.md),
[animację i źródłowe piksele](SHIP_POINTER_VISUAL_EVIDENCE.md)
oraz [zegar aplikacji](POINTER_APP_CADENCE_EVIDENCE.md).

Testowane punkty są stałe: środek maski0b `(1056,160)`, pusta komórka18,5
i późniejszy cel16,4. Native mask/picker/hover mają własne szersze testy;
ten replay nie jest dowodem wszystkich pozycji i kontekstów kursora.

[Niezależny kompozytor](../tools/ship_pointer_image_reference.py) sprawdza
siedem plików źródłowych, manifest, payload i wszystkie 29 płaszczyzn ósmego
stagingu. Dokłada selector, pasek, potwierdzenie i kursor do źródłowego
obrazu świata. Zachowuje pełne przezroczyste marginesy i skalowanie Point2×.
Selector i pasek mają kolejność 45/44 przy obu istniejących węzłach;
potwierdzenie 46, a końcowy SpriteRenderer kursora 32767.

## Przebieg i wymagane kontrole

Scena pracuje w 1920×1080, viewport zajmuje cały ekran. Kamera ma początek
świata576,0; jeden piksel logiczny źródła zajmuje2×2 piksele ekranu.
Normalny replay ma 25 checkpointów; dwa rozkazy 35.

- Down nad0b pozostawia wybór pusty; LeftUp zaznacza. Para Down/Up w tym
  samym update także musi dotrzeć w prawidłowej kolejności.
- RightUp na pustym SEA usuwa wybór i nie wydaje ruchu.
- Usunięcie urządzenia przy wciśniętym Left anuluje stan bez sztucznego Up.
  Odzyskanie wejścia wymaga neutralnego stanu i zmiany piksela logicznego.
- Pierwszy rozkaz przechodzi z przytrzymania w komórce 18,4 do zwolnienia
  w 18,5 w jednym pakiecie stanu. Move musi poprzedzać Up. Wynik to
  `41(group0)`, potem `20(18,5,byte0)`. Drugi rozkaz to tylko
  `20(16,4,byte0)` przy counter 101.
- Po pierwszym rozkazie czas UI wzrasta o 750 ms, lecz ruch o1 piksel HD
  pozostaje w tym samym pikselu logicznym. Nie może opublikować kursora
  ani potwierdzenia. Pierwszy confirm pozostaje niewidoczny, frame−1,
  stored0, stamp0.
- Każdy wiersz ruchu ma 13 kluczy i 16 wartości skalarnych. Kolejność
  liczników nie może się cofać. Końcowy odczyt
  wymaga wszystkich liczników 0…101 lub0…197, także liczników bez obrazu.
- Obraz jest pobierany dopiero po pełnym bloku checkpointu: metadane kolejki
  nakładek,4 wizualizacje i34 bazowe renderery. Cały odczyt logu przed i po
  przechwyceniu musi być identyczny, a przechwycenie mieścić się w1s
  z zatrzymania1,25s. Zachowywane są wszystkie próby i ich metryki.
- Opcja `--focus-cancel` uruchamia własny Notepad przez ten sam Wine
  przed playerem. Przy `cancel-down` uruchamia osobny, przypięty hashem
  program Win32: `FindWindow`, `ShowWindow`, `BringWindowToTop` i
  `SetForegroundWindow` przełączają player→Notepad→player. Probe obserwuje
  `GetForegroundWindow` i PID-y w trzech fazach, ze 160 ms pobytu w Notepadzie.
  Nie wysyła wejścia ani ręcznie skonstruowanych komunikatów okien.
  Helper wymaga rzeczywistych różnych HWND/PID-ów, przywrócenia playera,
  nowego callbacku Cancel przy counter 0 i zachowania dotychczasowych 12
  zdarzeń. Same zmienione XID-y lub powodzenie API nie wystarczają.
  Identyczne wielokrotne callbacki są dozwolone w tej samej fazie.
  Notepad i probe mają własne uchwyty Popen, logi i cleanup.
- Anulowanie ma dokładny schemat, licznik i stan wyboru. Wymagany jest
  co najmniej jeden Cancel w zatrzymanej fazie `cancel-down`; późniejsze
  callbacki cleanup są dozwolone po zakończeniu replay. Potwierdzenie
  zawsze ma źródłowy offset kliknięcia−(11,24), nawet gdy jest niewidoczne.
  Interwał kursora wynosi500ms na początku,150ms dla SEA i10000ms dla0/5/6.
- Końcowy raport wymaga kodu wyjścia0, odpięcia wejścia, zwolnienia8 zajęć
  siatki, usunięcia referencji wizualnych i niezmienionego provenance.

## Stan historyczny przed korektą koloru kursora

[Build3 dwa rozkazy](../artifacts/pointer-input/runtime-final-two-01/report.json)
z DLL `41a260011c5dec049d66e7017ba581deb61f4a802a2b2099c9b5572ebed67c93`
zakończył 35 obrazów, 21 zdarzeń, 232 wiersze ruchu i 198 różnych liczników 0…197.
Używał jeszcze kursora OnGUI oraz historycznego helpera SHA
`7ce0687bb0c9204961d548e955c6bf331b33e7b75956a17f61acc5186f7a172b`,
zachowanego w [archiwum](../artifacts/pointer-input/helper-initial-7ce0687.py).

[Niezależny audyt](../artifacts/pointer-input/qa-build3-independent-audit.json)
sprawdził wszystkie 70 plików PNG oraz ponownie złożył35 obrazów wzorcowych.
20 przechwyceń różniło się od źródłowych pikseli: maksymalnie RGB 2 i 236
pikseli w klatce. Wszystkie różnice leżały w prostokącie kursora. Pozostałe
piksele były dokładne. Był to PASS historycznego kryterium RGB ≤ 4, a nie
ostateczny odbiór wierności koloru.

Nowszy walidator sprawdził wszystkie liczniki również w tym historycznym
logu. Adaptacja obejmowała jawnie tylko `cursor_gui=True→False` i
`order=gui-last→32767`; nie zmieniała wejścia, czasu, ruchu ani pikseli.
Nie jest to uruchomienie build4. Wynik kolejnego rzeczywistego przebiegu
opisano poniżej.

## Build4: rzeczywisty przebieg dwóch rozkazów

[Końcowy player](../artifacts/pointer-input/runtime-final-two-02/report.json)
używa DLL `3a4f400a7e499ff2e78763240f7cbb30d55d57bf05c23bce0b0b0ddfe42ab054`
i helpera SHA `291b13389d25107ee707e8efeb7b2eb360ff8d9e936141e0664381f6173e1491`.
Oficjalny build Windows64Mono Unity6000.3.27f2 miał 0 błędów, 0 ostrzeżeń
oraz 146968843 B. Kursor jest końcowym SpriteRendererem URP Point, co usuwa
historyczną różnicę koloru OnGUI bez zmiany źródłowych płaszczyzn.

[Niezależny audyt końcowy](../artifacts/pointer-input/qa-final-two-independent-audit.json)
ponownie wykonał walidację natywnych komend, ruchu, selector i kolejki,
złożył wszystkie 35 obrazów oraz sprawdził70 hashy PNG i zdekodowane RGB.
Nie stosował adaptacji pól. Wynik:35 checkpointów,21 zdarzeń, 232 wiersze
ruchu, wszystkie198 liczników 0…197, trzy dokładne pakiety,0 ponownych prób,
**maksymalny błąd RGB 0 i 0 różnych pikseli**. Kod wyjścia0 i cleanup8.
Wszystkie zapisane wartości provenance zgadzały się z plikami
przed i po wykonaniu tego audytu. [Skrypt audytu](../artifacts/pointer-input/qa-audit.py)
wiąże swój hash z wynikiem; nie uruchamia usług ani playera.

Pierwsza osobna [próba fokusu](../artifacts/pointer-input/runtime-final-focus-01/failure.json)
zatrzymała się przy `cancel-down`: zmiana fokusu na X root nie wywołała
w wymaganym czasie faktycznego callbacku Cancel. Próba jest zachowana
jako FAIL kontroli środowiska/wyzwolenia; nie jest zaliczona do35 obrazów
ani do dowodu utraty fokusu. Usunięcie urządzenia w zakończonym przebiegu
pozostaje osobno sprawdzone. Nie ustalono tym błędu domenowych komend gry.
[Próba02 z Notepadem](../artifacts/pointer-input/runtime-final-focus-02/failure.json)
zakończyła się wcześniej: zapytanie `getwindowfocus` otrzymało X PointerRoot1
i zgłosiło BadWindow przed zmianą okna. Ta próba także nie potwierdza
anulowania przez utratę fokusu; sprawdzanie środowiska przerwało ją bez
zaliczenia wyniku domenowego.
[Próba03](../artifacts/pointer-input/runtime-final-focus-03/failure.json)
potwierdziła zmianę surowych XID-ów, lecz nadal nie otrzymała callbacku
Cancel. X focus nie dowodzi zmiany foreground aplikacji Win32. Dlatego
ostatni driver korzysta z prawdziwych API Win32 zamiast kolejnej zmiany
C# lub wywołania sztucznego callbacku. Jego
[źródło](../tools/win64_pointer_focus_probe.c) i
[reprodukowalny build](../tools/build_win64_pointer_focus_probe.sh)
są przypięte hashem; wynik, stdout i stderr pozostają w katalogu przebiegu.


## Build5: końcowy ponowny przebieg

Po poprawce zachowania istniejącego gestu przy wyjściu poza mapę
[build5](../artifacts/pointer-input/build-report-05.json) zachowuje 57 skryptów
C#, 109 meta,0 błędów i0 ostrzeżeń. DLL ma SHA
`9402081fe31ba5135512f95ea385ee867d75d2c26a03f0f6060dde352d17de8a`.
Nie dodaje tym selekcji ramką; zamyka możliwość przypadkowego zwykłego
rozkazu po ponownym wejściu przy trwającym prostokącie.

[Nowy rzeczywisty replay dwóch rozkazów](../artifacts/pointer-input/runtime-final-two-03/report.json)
używa zaostrzonego walidatora SHA
`79f286d93ace585615044925ce5c37cf7a1eb8445812ea704d6b2cd289bd9262`.
Względem poprzedniego walidatora wymaga on również obecności i kontekstu
Cancel, monotoniczności liczników, źródłowej pozycji confirm oraz interwału
kursora. Dokładna poprzednia wersja pozostaje w
[archiwum291b](../artifacts/pointer-input/helper-color-fix-291b1338.py).

[Niezależny audyt build5](../artifacts/pointer-input/qa-build5-two-independent-audit.json)
przeszedł bez adaptacji:35 obrazów źródłowych złożonych ponownie, wszystkie 70
hashy PNG i RGB,21 zdarzeń, 232 wiersze ruchu,198 liczników 0…197, dokładne
pakiety41/20/20,0 ponownych prób, maksymalny błąd RGB 0 i 0 różnych pikseli.
Wszystkie 57 aktualnych skryptów i pozostałe provenance były niezmienione
podczas sprawdzania. Po korekcie wyłącznie sterowania fokusem walidator
offline ma SHA `7d06d6e2ed281df9bd8b94f56b24ba33e52410f371fd667b64e72f3c034ae33e`.
Audyt rozróżnia ten hash od runtime79f i sprawdza dokładne
[archiwum79f](../artifacts/pointer-input/helper-hardened-79f286d9.py); nie
zmienia przy tym źródeł, natywnych reguł, obrazów ani semantyki checkerów. Kod wyjścia0, cleanup8. To aktualny dowód dwóch
rozkazów; poprzednie przebiegi pozostają historycznymi etapami diagnozy.

## Build5: osobny przebieg jednego rozkazu

[Normalny replay](../artifacts/pointer-input/runtime-final-normal-01/report.json)
wykonał osobną trasę 18,5 z końcem przy counter 101, używając obecnego
helpera `0276e3117efc0083af119c702d1cfc816f7a468c4ad5ba2678aa2f3de804483a`
i tej samej DLL build5. [Niezależny audyt](../artifacts/pointer-input/qa-build5-normal-independent-audit.json)
sprawdził wszystkie 25 obrazów, 50 PNG, 18 zdarzeń, 126 wierszy ruchu,
102 liczniki 0…101 i dwa źródłowe pakiety. Wynik: zero ponownych prób,
maksymalny błąd RGB 0 i zero różnych pikseli, exit 0 i cleanup 8.

| Zakończony przebieg build5 | Obrazy | PNG | Zdarzenia | Wiersze ruchu | Liczniki |
| --- | ---: | ---: | ---: | ---: | --- |
| Jeden rozkaz | 25 | 50 | 18 | 126 | 0…101 |
| Dwa rozkazy | 35 | 70 | 21 | 232 | 0…197 |
| Łącznie | 60 | 120 | 39 | 358 | Pełne w obu przebiegach |

Wszystkie 60 przechwyceń pasuje do źródłowych pikseli bez różnic RGB.
Niepełne próby fokusu i historyczne buildy nie zwiększają tych liczb.

## Testy samego walidatora

[14 testów QA](../tests/test_smoke_ship_pointer.py) przeszło bez pominięć
w 18,123 s; [log](../artifacts/pointer-input/qa-unit-tests-final.log). Obejmują39 odrzuconych mutacji logu oraz12 błędnych protokołów Win32 foreground, akceptację wyłącznie
niezakończonego ogona podczas odczytu na żywo, oraz dwa odrzucone przypadki
fence obrazu. Kontrole zmieniają m.in. krawędź/pozycję Up, dodają rozkaz do
RMB, usuwają membership lub licznik2, zmieniają byte0/RNG/stored frame,
kolejność health/selector, hotspot, rodzinę kursora i stan po 750 ms bez Move.
Sam poprawny obraz nie może ukryć zmiany UI pomiędzy odczytami.

[Fixture logu](../tests/fixtures/ship_pointer_input.log) jest zapisanym
wyjściem Unity przeznaczonym do kontroli parsera. Nie jest wzorcem binarnym
oryginału. [Manifest](../tests/fixtures/ship_pointer_input_manifest.json)
wiąże jego SHA z rzeczywistym końcowym logiem build4, DLL i helperem.
Fixture zachowuje wszystkie wybrane wartości pól bez adaptacji; usuwa
wyłącznie niepowiązane z diagnostyką linie playera.

## Ostatni opcjonalny driver fokusu

Helper ma SHA `0276e3117efc0083af119c702d1cfc816f7a468c4ad5ba2678aa2f3de804483a`.
Semantyka ruchu i checkerów źródłowych jest taka sama jak w zaostrzonej
wersji79f. Następne poprawki dotyczą wyłącznie wyzwalania i odczytu fokusu;
[wersja7d](../artifacts/pointer-input/helper-xfocus-7d06d6e2.py) jest zachowana.

Reprodukowalny probe EXE ma SHA
`d6bc85fd7b632c8cc1d44fd6fe367f6f3fe0be133350a52e9051ca0fe5359069`,
źródło C `027b22060d98b468149d9cf3514f3658edd61577cbf26486a9505f8becff1b29`,
a skrypt budowania `bc31b184a726392bcf0d8bc4e72be600523a9d68f414d7d8ab7beda5aae88b24`.
W ostatniej wersji probe tworzy własną kolejkę przez PeekMessage i próbuje
AttachThreadInput z wątkami obu własnych okien; przy wyjściu odłącza udane
połączenia. Nie generuje wejścia ani nie fałszuje komunikatów. Rezultaty
AttachThreadInput nie są zapisane w JSON, więc nie zakłada się, że samo
połączenie wątków się powiodło. Dokładna wcześniejsza
[wersja b77](../artifacts/pointer-input/helper-win32-b77b9b0a.py) oraz
[C i EXE sprzed tej zmiany](../artifacts/pointer-input/win32-focus-probe/before-attach/)
są zachowane.

JSON rozróżnia faktyczny foreground od wartości zwrotnej próby aktywacji.
Jeśli foreground Win32 się zmieni, a player nie wyśle Cancel, utrata fokusu
w Wine pozostanie niezweryfikowana. Nie zastępuje się tego dowodu przez
bezpośrednie wywołanie metody gry. Żaden z tych testów nie potwierdza
natywnego Windows 11 ani sprzętowej myszy.

[Końcowa próba05](../artifacts/pointer-input/runtime-final-focus-05/failure.json)
nie przeniosła foreground Win32 na Notepad: `SetForegroundWindow` zwrócił 0,
a `GetForegroundWindow` we wszystkich fazach wskazał player. Przyczyna
odmowy aktywacji nie została ustalona. Nie jest to dowód, że Unity pominęło
callback po rzeczywistej utracie foreground. Nie zaobserwowano nowego
Cancel ani dodatkowego Up; opcjonalne badanie zatrzymano bez zmian C#.

[Niezależny audyt pięciu prób](../artifacts/pointer-input/qa-focus-unverified-independent-audit.json)
wiąże ich failure JSON, provenance, źródło i binarny probe oraz surowe
obserwacje Win32. W ostatniej próbie 12 zdarzeń nie wydało żadnego pakietu.
Jedenaście wcześniejszych checkpointów ma dokładne źródłowe RGB, lecz
niepełnej próby nie zaliczono do ukończonych przebiegów gry. Zakończony
replay dwóch rozkazów osobno potwierdza anulowanie po usunięciu urządzenia.

## Granice wyniku

Obsługiwany jest0b, siedmiu nieruchomych sąsiadów, pełne zdrowie, brak mgły,
puste pozostałe sloty obiektów i wyłączony backend audio. Projekcja planera
dotyczy różnych grup; nie przenosi zachowania wspólnej grupy ani całej floty.
Nie zweryfikowano tu box selection, modyfikatorów, podmiany celu w ruchu,
innych aktorów, aktywnego audio ani całego obiegu komunikatów oryginału.

Native primitives potwierdzają reguły animacji kursora i confirm, ale log
nie zawiera każdego Draw wywołanego podczas nieprzerwanej części Life.
Tam fazę czasu UI ograniczają poprawne klatki, pozycje i stemple; obrazy
sprawdzają źródłowe piksele dla zweryfikowanego zalogowanego stanu.
Nie należy przedstawiać tego jako niezależnego odtworzenia całej historii
czasowej UI. Selector i fizyka mają osobno rekonstruowany przebieg natywny.
Adapter 40 ms nie portuje kompletnej polityki Sleep i pilnych kolejek RunApp.

Nie uruchomiono testu sprzętowej myszy ani natywnego Windows 11. Udany osobny
test foreground Win32 mógłby potwierdzić callback w używanym playerze Wine. Referencyjne
obrazy źródłowe służą zgodności; oprawa 2026 i pełna gra pozostają dalszą pracą.
Pliki obrazów są wewnętrznym dowodem QA, bez podglądu, ZIP i publikacji.
