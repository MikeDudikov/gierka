# Ograniczony picker statków — kod i player Unity

Stan:2026-11-03. Docelowa prezentacja gry pozostaje1920×1080,16:9,pełny ekran.
Etap przenosi źródłową kolejność wyboru statku pod wskazanym punktem świata
oraz sprawdza zapytania w działającym playerze. **Nie podłączono jeszcze myszy,
kliknięcia zaznaczenia ani interfejsu rozkazów.** Zwykły Start pozostaje wyłączony.

## Czysty kod

[ShipWorldPicker.cs](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipWorldPicker.cs)
używa MissionOccupancyGrid,niemutowalnej ShipPointerPose i wcześniejszych
ShipPointerMask. Najpierw sprawdza zajętość bieżącej komórki;precise sprawdza
następnie sąsiadów w oryginalnym porządku zależnym od brzegu. Pierwsze
prawdziwe trafienie wygrywa. Nie sortuje po depth i nie usuwa powtórzeń
tej samej referencji obecnej w komórce oraz rezerwacji.

Zakres wymaga24×24,noFog,pustych innych slotów obiektów i normalnych klas
statków200…211. Nie jest to port całej polityki fog i wszystkich klas świata.
Nieobsługiwane wejścia są jawnym błędem kontraktu adaptera.

[Świeży oryginał i C#](../artifacts/world-input/picking/world-picker-csharp-validation.json)
zgadzają się:1206 zapytań,5665 uporządkowanych wizyt predykatu,21 kontroli API.
Wykonano oryginalne49a580,klasyfikację brzegu,konstruktor/tablice i rzeczywiste
4e06c0/5431d0/5575d0;hook obserwacyjny tylko odczytuje wejścia predykatu.
Nie przechwytywano jego wyniku ani wywołań. C# ma `/checked+ /warnaserror+`.
Dwa testy celowane przeszły bez pominięć w1.701s.
[Pełny dowód](WORLD_PICKER_ORDER_EVIDENCE.md).

## Most do Unity i dane

Nowa flaga `--ship-picking-reference` implikuje znany teren,pięć raf i osiem
statków. Wyklucza pozostałe cztery tryby diagnostyki ruchu i menu/briefing replay.
Wykorzystuje dotychczasowe `--ship-order-target-x/y`,opcjonalne oba
`--ship-order-next-x/y`,session-seed i stop-at. Kamera diagnostyki ma Point2×,
origin9,0 w QA;to nie źródłowy zapisany viewport ani ostateczne FOV gry.

[ShipPickingReference.cs](../Unity/AncientConquest/Assets/AncientConquest/Runtime/ShipPickingReference.cs)
ładuje siódmy zestaw Resources,sprawdza SHA52800B oraz wszystkich96 płaszczyzn
przed utworzeniem4 masek rodzin. Łączy dokładne descriptor_resource z geometrią
każdego aktora. Ruchomy0b dostaje PublishedWorldX/Y,StoredFrame iHeading z
bieżącego snapshotu;pozostałe siedem statków ma zamrożone źródłowe pozy.

ShipOrderReference ma opcjonalnego obserwatora na końcu LogStage.
Stare wywołania przekazują null i zachowują poprzedni przepływ. Obserwator
wykonuje na każdym checkpoint25 albo27 zapytań:środki ośmiu statków coarse/
precise,początek i krawędzie0b,środek komórki/rezerwacji oraz rogi mapy.
Loguje wynik i rzeczywistą kolejność wizyt. Wszystkie576 referencji siatki
muszą pozostać niezmienione,po czym zapisuje checkpoint_complete.

Maski i query nie modyfikują czasu,RNG,rozkazu ani rendererów. Holdy1.25s
obejmują logowanie i zapytania,wyłączone z czasu diagnostycznego. Nie jest to
dowód tempa całej gry ani OS input. Scope readiness jawnie mówi mouse=False,
selection=False,fog=False,other_object_slots=empty.

## Build i testy

[BuildReport](../artifacts/world-picker/build-report.json):Unity6000.3.27f2,
Windows64Mono,146377147B,0 błędów/ostrzeżeń. DLL SHA256
`a706aa5e9d9a5966b78c84bc1eace6f669f655a0e94601f82aeb2002e5305409`.
[Integralność](../artifacts/world-picker/source-integrity.json):49 C#/98 meta,
bez braków,błędnych lub powtórzonych GUID;bez zmian C# po buildzie.
Nie zmieniano zasobów,scen,prefabów,pakietów ani shaderów.

[Pełny discovery](../artifacts/world-picker/unittest-final.log):196PASS,0skip,
175.263s. Osobno7 nowych testów helpera QA przeszło w6.968s;nie deklarować
203 testów w jednym discovery.

[Pilot playera](../artifacts/world-picker/runtime-first-normal/report.json):
12 checkpointów,306 zapytań,96 wiązań aktorów,PASS;osobno od końcowego zestawu.

[Pełny player](../artifacts/world-picker/runtime-final/report.json):4 sesje,
53 checkpointy,1353 zapytania,1243 wizyty predykatu,57 queryrows z duplikatem
właściciela,424 wiązania aktorów. Wszystkie53 snapshoty576 referencji gridu
pozostały niezmienione.54 pola ruchu,path/cache/RNG oraz1802 rzeczywiste
odczyty renderer queue są zgodne.53 pełne kadry i159 ROI mają RGBmean/max0.
Cleanup8/8/8/9 i exit0 wszystkich sesji.58 prób obrazu,5 odrzuconych:
4 dokładnie odpowiada wcześniejszemu checkpointowi,1 niesklasyfikowana.

[Niezależny audyt](../artifacts/world-picker/qa-runtime-final-independent-audit.json)
sprawdził111 PNG encodedSHA+decodedRGB,aktualny provenance/DLL i zgodność
z zapisanym śladem rozkazów. [QA](SHIP_PICKING_QA_EVIDENCE.md) obejmuje
36 jawnych negatywów logów oraz query-only mutation/missing-marker fences.
Przy przechwyceniu obrazu pełne actor/query/completion muszą być zgodne
przed i po capture. Nie wolno przyjmować samej obecności pierwszej linii stage.

Dwie wybrane regresje tego samego DLL przeszły:
[stary order normal](../artifacts/world-picker/legacy-order-regression/report.json)
ma12 kadrów/36 ROI RGB0,cleanup8/exit0 oraz brak nowego query prefix przy
null observer. [Menu](../artifacts/world-picker/menu-regression/report.json)
ma27 etapów/5 kadrów/6 komend i normalny ApplicationQuit0. Menu używa jawnego
synthetic InputSystem,nie OS mouse. Nie powtarzano wszystkich dawnych grup.

## Następne zależności i granice

[Kliknięcie→grupa→rozkaz](WORLD_COMMAND_SOURCE_EVIDENCE.md) oraz
[członkostwo→ruch](WORLD_MEMBERSHIP_MOVEMENT_EVIDENCE.md) są osobnymi
dowodami oryginalnego x86. UI5c i simulation5e są różnymi polami grupy.
Action41 synchronizuje5e,a normalny pojedynczy aktor dostaje action20 z
bajtem0. Nie należy pomijać członkostwa ani zastępować go dowolnymi stałymi.

Dla dwóch źródłowych tras projekcja requester0/peers−1 odpowiada wcześniejszej
kontrolowanej requester−1/peers0 łącznie z mapami planera. Nie dowodzi to całej
polityki wielu aktorów tej samej grupy. Pierwszy hover/kliknięcie zaznaczenia,
drag,modifiedflags,busy replacement i konsumpcja całego świata nie są portowane.

Aktualne rzeczywiste ślady trasy nie rozróżniają maskindexów Stored/Drawn ani
pozycji Published/Physics. Wiązanie pól ma osobny przegląd kodu i surowy dowód
predykatu;nie twierdzimy,że same obrazy tych tras wykrywają każdy taki błąd.

Pełny Life,AI,walka,pogoda,save/load i finalna oprawa2026 pozostają nieukończone.
Wine/Xvfb nie zastępuje natywnego Windows11 ani testów docelowego laptopa.
Nie tworzono ZIP,podglądu do prezentacji ani publikacji;PNG są wewnętrznym QA.
