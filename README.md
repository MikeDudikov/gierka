**Pełna paczka do pobrania: [gierka/START_TUTAJ.md](gierka/START_TUTAJ.md).** Zawiera sześć części Git LFS oraz skrypty automatycznego pobierania i scalania oryginalnego archiwum6,2GB.

**Przekazanie do Claude Code przygotowane; rozwój w tej sesji zatrzymany.** Zacznij od [CLAUDE.md](CLAUDE.md) i [instrukcji przekazania](handoff/START_TUTAJ.md). Pełny stan, plan i blokada ostatniej diagnostyki: [handoff/STAN_I_PLAN.md](handoff/STAN_I_PLAN.md).

**Prace trwają autonomicznie.** [Jawny reset kontekstu trasy](docs/SOURCE_APP_ACTIVATION.md): x86 i port C# zweryfikowane, dwa nowe replaye oraz wcześniejszy profil PASS. Build Windows1920×1080:0 błędów/ostrzeżeń; pełna gra pozostaje nieukończona.

Historyczny punkt pauzy: [zbiorczy raport postępu](docs/RAPORT_POSTEPU_REMAKE_2026-11-04.md). Został zastąpiony bieżącym poleceniem kontynuacji.

Aktualny etap: [prawy Shift i odczyt rzeczywistej kontrolki](docs/RIGHT_SHIFT_INPUT.md). Dalej źródłowy protokół C45E; gra pozostaje nieukończona.

Aktualny etap: [źródłowe komunikaty Shift i grafika trasy](docs/SOURCE_ROUTE_KEY_VISIBILITY.md). Dalej odrębny replay prawego Shift; gra pozostaje nieukończona.

Aktualny etap: [pierwszy Shift i WPMOVE](docs/PENDING_QUEUED_INPUT.md). Kolejny krok: źródłowe komunikaty klawiatury C45D; gra nadal jest nieukończona.

# Ancient Conquest — remake w Unity

Cel: odtworzyć treść, mechaniki, AI i tempo oryginału oraz przygotować nową oprawę
w jego stylu. **Obowiązujący format: 1920×1080, 16:9, pełny ekran i pełny viewport,
bez czarnych pasów.** Platforma: Windows 11; laptop i5 3,6 GHz, 16 GB RAM,
RTX 3050 Ti. Nowe tekstury i modele są dozwolone, jeżeli wierne odnowienie starych
nie daje jakości oczekiwanej w 2026 roku: [ART_DIRECTION.md](docs/ART_DIRECTION.md).

Najnowszy etap: [integracja100/2 w świecie C#](docs/QUEUED_WORLD_INTEGRATION.md).
50 scenariuszy i 5536 klatek potwierdza zadania, zdarzenia310, pocztę i ruch
bez podawania pakietów z oryginału po starcie.8testów PASS;buildWindows0/0.
Rozpoczęto źródłowy dowód Shift podczas ruchu i powrotu do zwykłego rozkazu.
UI Shift czeka na adapter z jawnym kontekstem pamięci fali.
Pełna gra i oprawa2026 nadal w budowie.

## Stan — 2026-11-04

**Prototyp obejmuje menu,pierwszy briefing,teren,pięć raf,osiem statków,
ograniczony ruch0b,wybór floty i kontrolny ruch trzech lokalnych statków. Pełna gra
pozostaje w budowie;zwykły Start jest nadal wyłączony.**
`--ship-pointer-reference --ship-pointer-fleet-selection` dodaje kliknięcie,
ramkę,Shift/Ctrl,oryginalne obrysy i paski zdrowia0b/0c/0d.
Bez flagi fleet-movement pozostaje to tryb samego wyboru grupy.
Dotychczasowe sterowanie0b pozostaje dostępne bez dodatkowej flagi.

Nowy `--ship-pointer-reference --ship-pointer-fleet-selection
--ship-pointer-fleet-movement` obsługuje pierwszy zwykły rozkaz wybranej floty:
kliknięcie celu,41 przed20,formację,ruch i animacje.Ctrl przywołuje całą
zatwierdzoną grupę. Przebieg InputSystem sprawdził23 punkty kontrolne,69 stanów
modelu,230 części i782 odczyty kolejki. Kolejne rozkazy i Shift zatwierdzonej
grupy są jawnie blokowane do czasu portu pracy zadań grupowych.
Dotychczasowy kontrolny rendering trzech kadłubów pozostaje dostępny osobno.

Nowy etap [normalnych ponowień rozkazu20](docs/SHIP_BUSY_ORDERS.md) dodaje
odbiór podczas ruchu i przed promocją. Zachowuje źródłowe nadpisanie rekordu
oczekującego oraz fazy świata:zadanie grupy emituje w10,statki odbierają w11.
18 scenariuszy/9984 stany i8 przebiegów świata/5088 stanów zgadzają się
ze świeżym x86,C# i shippingDLL. Zakres:zdrowe lokalne statki,normalne0/255,
nieblokujący arbitraż58b==0. Inne gałęzie i kolejne rozkazy przez UI nadal
wymagają dalszej pracy;nie odblokowano Shift zatwierdzonej grupy lub Start.

[Poprzedni build Windows x64 Mono](artifacts/busy-ship-orders/build-report.json)
Unity6000.3.27f2 ma152955435B i0 błędów/ostrzeżeń.4testy celowane PASS0skip;
3mutanty wykryte. Pełnego discovery nie ponawiano.73C#/131meta,3 istniejące
C# zmienione,70 bez zmian;sceny,prefaby,pakiety i zasoby bez zmian.
[Walidacja](docs/VALIDATION.md) określa zakres i pozostałe ograniczenia.

[Opis wejścia](docs/WORLD_POINTER_INPUT_IMPLEMENTATION.md) wyjaśnia zakres
jednego statku,osobne membership UI/symulacji i źródłową kolejność kliknięć.
[Plan](docs/REMAKE_PLAN.md) zachowuje dalsze kroki:pełną selekcję/grupy,
pozostałe sloty i fog,scheduler,AI,walkę,save/load oraz oprawę2026.
Źródłowy atlas zaznaczeń i kursorów jest referencją wierności;
modernizacja wszystkich modeli/tekstur i natywne testy Windows11/laptopa
pozostają do wykonania. Zmiany pozostają lokalne;bez publikacji,ZIP i podglądu
przeznaczonego do prezentacji. Input System pozostaje przypięty do1.20.1.

Player ma pełny obraz **1920×1080 ExclusiveFullScreen**. „Start scenario”
otwiera briefing pierwszej misji **Lemnius's Parchment** z oryginalnym tekstem
i fontami. Trudność zmienia się po naciśnięciu ikony, zgodnie z oryginałem;
Cancel wraca do menu, a ponowne otwarcie zachowuje wybór. Przejścia, obrazy
11 stanów i normalny Quit przeszły test przez jawny Input System replay.
Regresje na poprzednim buildzie ruchu przeszły: briefing 39 etapów/11 obrazów,
menu 27 etapów/5 obrazów/6 komend, normalny Quit z kodem 0 w obu sesjach. Wejście OS pod Wine pozostaje osobnym nierozstrzygniętym
obszarem: [raport](docs/INPUT_RUNTIME_INVESTIGATION.md).

Start samej rozgrywki pozostaje nieaktywny. Audio briefingu, pełna symulacja,
pozostałe ekrany, docelowe fonty/tekstury/modele i natywny Windows11/laptop
nie są ukończone lub zweryfikowane. Tła są szkicami poniżej finalnej jakości
natywnego detalu, a bitmapowe glify zachowują oryginalne kształty.

- [Ostatni spakowany prototyp Windows z ograniczonym ruchem statku](artifacts/movement/AncientConquest-Prototype-Movement-Windows-x64-1920x1080.zip).
- [Poprzedni prototyp Windows ze statycznymi statkami](artifacts/units/AncientConquest-Prototype-Ships-Windows-x64-1920x1080.zip).
- [Poprzedni prototyp Windows z briefingiem](artifacts/briefing/AncientConquest-UIPrototype-Briefing-Windows-x64-1920x1080.zip).
- [Prototyp etapu raf z referencjami obiektów](artifacts/objects/AncientConquest-Prototype-Objects-Windows-x64-1920x1080.zip).
- [Poprzedni prototyp z diagnostycznym podglądem terenu](artifacts/terrain/AncientConquest-Prototype-Terrain-Windows-x64-1920x1080.zip).
- [Rzeczywisty kadr po przygotowanym ruchu0b](artifacts/movement/runtime-complete-final/full-route/arrived-attempt-01.png).
- [Rzeczywisty kadr terenu 1920×1080](artifacts/terrain/runtime-final/origin-0-0/frame-02.png).
- [Rzeczywisty obraz terenu](artifacts/terrain/runtime-final/interior-4-4/frame-01.png) i [trzy porównania playera](artifacts/terrain/runtime-final/report.json).
- [Rzeczywisty obraz briefingu](artifacts/briefing/player-native-ui-sampling/briefing-easy.png).
- [Rzeczywisty obraz podglądu raf z poprzedniego etapu](artifacts/objects/runtime-final/reef-00000009/frame-01.png).
- [Walidacja](docs/VALIDATION.md), [kontekst Unity](docs/UnityProjectContext.md),
  [kontrakt danych](docs/BRIEFING_IMPLEMENTATION.md).

**Historyczny pełny przebieg discovery:196 testów bez pominięć w175.263s** ([wynik](artifacts/world-picker/unittest-final.log));osobno7 nowych testów helpera QA/6.968s. Zamknięty etap masek miał194 discovery oraz5 testów celowanych/14.360s. Poprzedni obieg rozkazów miał182 testy discovery oraz osobne7 testów helpera QA/6.221s. Zakończone dłuższe trasy miały172 testy,sąsiedzi155,pojedynczy odcinek143,statyczne statki129,rafy109,a teren94. Porównania rzeczywistego kodu z oryginalnym
x86 obejmują bramkę AI35, przyciski150kroków/44ciągi, gałąź zegara1287 i wybór
trudności558kroków/222ciągi. Oryginalny formatter oraz metryki fontu potwierdziły
15wierszy briefingu. To wybrane reguły, nie kompletny mózg AI i zegar świata.

Zakończony etap terenu odtwarza statyczną mapę `miss000` z oryginalnych danych:
24×24 komórki, osiem warstw, 1007 operacji rysowania i 264 użyte klatki.
Oryginalne procedury x86 dały 1584 zgodne bufory pikseli; parser C# przeszedł
4608 odwołań mapy, a arytmetyka viewportu 1080 przypadków. To dowody dekodowania
i wybranej geometrii, nie gotowej misji.

Widok `--terrain-reference` pokazuje gotową, złożoną wcześniej teksturę przez
SpriteRenderer w pełnym 1920×1080 przy diagnostycznej skali 2×. Nie rysuje ośmiu
warstw osobno w runtime ani nie uruchamia misji. Trzy kadry Windows playera
pod Wine/Xvfb są **piksel w piksel zgodne** z odpowiednimi wycinkami referencji;
każda sesja zakończyła się diagnostycznym wyjściem po ośmiu sekundach z kodem 0.
Regresje [menu](artifacts/terrain/menu-regression-final/report.json) oraz
[briefingu](artifacts/terrain/briefing-regression-final/report.json) przeszły na tym samym DLL. Źródłowa grafika
pozostaje referencją bazowej palety, bez animacji, jednostek i finalnej oprawy
2026. Szczegóły: [staging terenu](docs/TERRAIN_STAGING.md),
[dowody renderera](docs/TERRAIN_RENDER_EVIDENCE.md),
[geometria i ograniczenia kamery](docs/TERRAIN_CAMERA_EVIDENCE.md),
[procedura kontroli playera](docs/TERRAIN_RUNTIME_VALIDATION.md).

Przy zamykaniu playera UI nadal występuje znane ostrzeżenie o zwalnianiu
`ComputeBuffer` przez GC. Jest identyczne z logami poprzedniego etapu briefingu;
nie zostało wprowadzone przez teren i pozostaje do wyjaśnienia.

## Zakończony etap planu obiektów i referencji raf miss000

Odtworzono dokładne payloady 45 zasobów `OBJ_*` i ich wybór do planu tworzenia.
Wykonany oryginalny BTree potwierdził kolejność 63 wszystkich rekordów oraz
45 rekordów obiektów bez hooków. `MissionObjectSelection` przeszedł 1450
porównań z x86. Jest to filtr i wybór kodów fabryki — **żaden oryginalny
konstruktor nie jest wykonywany przez ten plan**.

`MissionInitialSetup` przeszedł 177 porównań. Dla Start scenario wybiera slot
(1,1), źródłowy zapisany origin (15,0) i źródłowy widok 9×8 komórek. Wynik
nie zmienia kadru diagnostycznego 2×/1920×1080 i nie dowodzi nagranej pierwszej
klatki oryginału. `MissionReefSeed` ma 104 porównania, w tym pięć autentycznych
raf. Loader ich animacji potwierdził 60 nazw klatek, 180 wyników geometrii
bbox i 360 buforów RLE.

Flaga `--mission-object-reference` dodaje do terenu pięć osobnych sprite’ów
zamrożonych w stanie 1/klatce 0, przy założeniu pustych komórek kolizji.
To referencja pozycji i grafik, bez symulacji, animacji, mgły i pełnego porządku
rysowania świata. Cztery kadry pod Wine/Xvfb przeszły porównanie całego RGB:
wszystkie piksele są identyczne z referencją. Osobne porównanie obszarów pięciu
raf również ma błąd 0. Trzy kadry regresji samego terenu są identyczne na tym
samym DLL. [Raport obiektów](artifacts/objects/runtime-final/report.json) i
[regresja terenu](artifacts/objects/terrain-regression-final/report.json).

Regresje [briefingu](artifacts/objects/briefing-regression-final/report.json)
(39 etapów/11 obrazów) i [menu](artifacts/objects/menu-regression-final/report.json)
(27 etapów/5 obrazów/6 komend) przeszły na tym samym DLL co oba testy terenu.
Obie sesje UI zakończyły się normalnym Quit z kodem 0. To syntetyczny replay,
nie test fizycznego wejścia OS. Z paczki tego etapu `Podglad-obiektow.cmd`
otwiera osobny podgląd; normalny Start rozgrywki pozostaje wyłączony,
a grafika źródłowa nie jest finalną oprawą 2026.

Dowody: [loader i wybór obiektów](docs/MISSION_OBJECT_LOADER_EVIDENCE.md),
[pozycje i granice referencji raf](docs/MISSION_OBJECT_POSITION_EVIDENCE.md),
[zasoby animacji](docs/OBJECT_ANIMATION_ASSET_EVIDENCE.md),
[źródłowy wybór gracza i kamery](docs/MISSION_INITIAL_CAMERA_EVIDENCE.md).

## Zakończony etap statków i częściowej siatki zajętości

`MissionShipSeed` odczytuje osiem źródłowych statków `miss000`, ich właścicieli,
warianty, komórki, kierunki i kotwice grafiki. Rzeczywisty C# przeszedł 184
porównania z x86 i dziewięć kontroli kontraktu. `MissionOccupancyGrid`
zachowuje 576 flag komórek oraz reguły pojedynczego właściciela: 1572
porównywane przypadki i 68 kontroli kontraktu. To częściowa siatka, bez
wyszukiwania ścieżek i pełnego systemu kolizji.

Dekoder złożonych sprite’ów TYPE8 ma siedem testów oraz dowody z oryginału:
12 wywołań loadera, 340 prób lokalnego sortowania i 96 dokładnych buforów RLE
dla 17 użytych klatek składników. Osiem statków składa się z 29 instancji tych
składników. Osobny oracle potwierdził kolejność 21 globalnych węzłów i remisy;
po spłaszczeniu razem z pięcioma rafami otrzymujemy 34 sprite’y w kolejności
cienie → rafy → grupy kadłubów i pozostałych dodatnich składników.
To dowód ograniczonej kolejności źródłowej, bez pozostałych klas świata.

Nowa flaga `--mission-unit-reference` włącza teren, pięć raf i
`MissionShipReference`. Referencje pozostają w stanie 1 i źródłowej klatce
kierunku. Kod zajmuje osiem komórek własnymi właścicielami, nie wykonuje
oryginalnych konstruktorów i nie dodaje poleceń: `source_constructors_executed=0`,
`pending_orders=0`, `simulation=False`. Normalny Start rozgrywki pozostaje
wyłączony. To źródłowa grafika do porównań, przed finalną oprawą 2026.

Build Windows tego etapu przeszedł z 0 błędów/ostrzeżeń. [Końcowe porównanie
playera](artifacts/units/runtime-strict-final/report.json) obejmuje trzy kadry
1920×1080 i osiem pełnych obszarów statków: średni i maksymalny błąd RGB 0,
100% identycznych pikseli. Każda sesja potwierdziła 34 wpisy kolejki,
zwolnienie ośmiu zajęć i diagnostyczne wyjście z kodem 0. Kolejka opiera się
na 29 odczytach właściwości rendererów statków oraz pięciu obliczonych
deklaracjach raf, których przypisania sprawdzono statycznie.

Kontrole checkera przeszły 88/88 po zaostrzeniu kontroli każdego obszaru
statku. Osobne regresje [raf](artifacts/units/objects-regression-final/report.json)
(cztery kadry) i [terenu](artifacts/units/terrain-regression-final/report.json)
(trzy kadry) mają RGB 0. [Briefing](artifacts/units/briefing-regression-final/report.json)
przeszedł 39 etapów/11 obrazów, a [menu](artifacts/units/menu-regression-final/report.json)
27 etapów/5 obrazów/6 komend; obie sesje zakończyły się normalnym Quit 0.
Wszystkie pięć grup sprawdza DLL SHA256
`518838f1952b31309238cbf9187cb00ea4bf0b76a1d882d101d17d60fbb209bb`.

Pełny zestaw 129 testów przeszedł bez pominięć. Pierwszą nieudaną próbę
zachowano: fixture miała nieaktualny `decoder_sha256`. Przed aktualizacją
wyłącznie tego pinu potwierdzono niezmienione natywne wyniki loadera i sortu
12/340. Zachowano też próby, które ujawniły lukę checkera; poprawka QA nie
zmieniła kodu Unity. Szczegóły: [walidacja](docs/VALIDATION.md).

[Paczka etapu statków](artifacts/units/AncientConquest-Prototype-Ships-Windows-x64-1920x1080.zip)
ma 47071067 bajtów i 182 pliki, SHA256
`d6854c65e8cad75b9ca8be2599159d4fe91effe95ce9662a8a4b4836a2dfbc51`.
Po rozpakowaniu całego ZIP `Podglad-statkow.cmd`,
`Podglad-statkow-poludnie.cmd` i `Podglad-statkow-sasiednich.cmd` otwierają
trzy osobne kadry; zachowano launchery raf i terenu oraz instrukcję README.
Podglądy zamykają się diagnostycznie po 30 sekundach.

Dowody: [inicjalizacja statków](docs/MISSION_UNIT_INITIALIZATION_EVIDENCE.md),
[flagi i zajętość](docs/MISSION_OCCUPANCY_EVIDENCE.md),
[złożone zasoby TYPE8](docs/UNIT_ANIMATION_ASSET_EVIDENCE.md),
[kolejność świata](docs/UNIT_WORLD_ORDER_EVIDENCE.md) oraz
[pozostałe klasy początkowej sceny](docs/MISSION_SUPPORT_OBJECTS_EVIDENCE.md).
Pełna symulacja, ruch, walka, AI, czas animacji, nowe modele i tekstury oraz
testy na Windows 11 i docelowym laptopie pozostają otwarte.

## Zakończony etap jednego odcinka statku 0b

`--ship-movement-reference` uruchamia osobną diagnostykę `OBJ_0000000b`
na przygotowanej źródłowej trasie `(16,2) → (15,3)`. Pozostałe siedem
statków i pięć raf pozostają referencjami. Normalny Start gry jest wyłączony.

[Końcowy raport playera](artifacts/movement/runtime-complete-final/report.json)
sprawdza pełny odcinek 44 kroków w siedmiu etapach oraz przerwanie po kroku 1
w dwóch etapach. Wszystkie dziewięć kadrów 1920×1080 i po trzy obszary statków
0b/0c/0d na każdym mają średni i maksymalny błąd RGB 0 oraz 100% zgodnych
pikseli. Sesje zwolniły odpowiednio osiem i dziewięć zajęć oraz wyszły z kodem 0.
Trzy jeszcze poprzednio przedstawione klatki odrzucono; poprawne obrazy
uzyskano w ograniczonym oknie 1s, bez zmiany C#. Pierwszy nieudany raport
i pośrednie kontrole zachowano. Końcowy checker przeszedł 318 kontroli,
w tym odrzucenie dodatkowego statku poza bieżącymi ROI; maksymalny błąd
całego obrazu ma granicę 4, a wszystkie rzeczywiste kadry mają błąd 0.

Na tym samym DLL regresje statków (3 kadry/8 ROI), raf (4 kadry) i terenu
(3 kadry) mają RGB 0. Briefing przeszedł 39 etapów/11 obrazów, a menu
27 etapów/5 obrazów/6 komend; normalny Quit 0 w obu sesjach.

Czyste reguły C# mają osobne porównania z x86: przyjęcie i promocja requestu
(`ShipMoveRequestInbox`: 45 scenariuszy, 169 obserwacji, 10 kontroli kontraktu),
przygotowany odcinek (`PreparedShipMovement`: sześć śladów, 186 stanów,
180 wywołań, 40 kontroli API) i ogon animacji (`ShipFrameProgression`:
288 porównań). Osiem testów stagingu sprawdza 88 pozycji z 152 bitmap.
Oddzielono klatkę wewnętrzną od opublikowanej: oryginalny setter/renderer
ma 45 kontroli bez hooków, a bramkę publikacji C# porównano na 186 stanach,
w tym 115 faktycznych publikacjach.

Warunki są jawne: wiatr o sile 0 i kierunku 5, poziom ulepszenia 0,
pełne zdrowie, pojedyncze kroki źródłowego zegara i kwant 40 ms.
Nie oznaczają domyślnej pogody każdej nowej misji. Zatrzymania etapów służą
kontroli obrazu, bez pomiaru tempa pełnej gry. Trasa jest zamrożonym wynikiem
osobnego oryginalnego planera; adapter przyjęcia requestu nie wykonuje
pełnego pathfindingu.

[Paczka etapu ruchu](artifacts/movement/AncientConquest-Prototype-Movement-Windows-x64-1920x1080.zip):
46980327 bajtów, 184 pliki, SHA256
`fd40fb7f1efe78ded0baff8d703c45e0c9c0a4401cd004052da6929ed24d7ad3`.
Rozpakować cały ZIP. `Podglad-ruchu.cmd` pokazuje odcinek, a
`Podglad-przerwania-ruchu.cmd` sprawdza wyjście przy zarezerwowanym celu.
Zachowano pięć starszych launcherów; `README-ETAP-RUCHU.txt` opisuje zakres.
EXE otwiera menu i briefing. [Manifest paczki](artifacts/movement/prototype-package-manifest.json)
wiąże pliki z buildem i jawnymi dodatkami. Dwukrotnie sprawdzono CRC ZIP
oraz SHA256 każdego zdekompresowanego pliku.

Źródła: [komenda ruchu](docs/SHIP_ORDER_EVIDENCE.md),
[kinematyka](docs/SHIP_MOVEMENT_EVIDENCE.md),
[klatki i staging](docs/SHIP_MOVEMENT_ANIMATION_EVIDENCE.md),
[zegar](docs/SHIP_MOVEMENT_CLOCK_EVIDENCE.md),
[pogoda](docs/SHIP_MOVEMENT_WEATHER_EVIDENCE.md).
Pełne sterowanie, pathfinding, AI, walka, pogoda świata i finalna oprawa 2026
pozostają nieukończone. Natywny Windows 11 i docelowy laptop nie były testowane.

## Zakończony etap sąsiednich celów i obrotu 0b

`--ship-adjacent-reference` wybiera źródłowy statek `(16,2)`, kierunek5,
i jeden z ośmiu sąsiednich celów. E, NE, W, SW, S i SE mają potwierdzone
źródłowe trasy; N i NW są odrzucane przez nieprzejezdny teren. NE pozostaje
dozwolony mimo zablokowanego północnego pola bocznego. Nie zmieniano mapy
ani nie dodawano własnej reguły zakazującej takiej diagonali.

Czysty C# zgadza się z oryginałem: predykat sąsiada7120 przypadków,
planer ośmiu celów8 przypadków/18 kontroli API, obrót3776 przypadków oraz
kinematyka38 śladów/1271 stanów/1233 wywołań/587 publikacji i42 kontroli API.
Osobne256 wywołań całego MoveShip potwierdza, że zakończenie obrotu nie
uruchamia rezerwacji i ruchu w tym samym wywołaniu. Zapisana klatka jest
oddzielona od opublikowanej; pierwszy krok obrotu może zapisać47, gdy ekran
nadal pokazuje20. Wspólny `SourceShipPoseReference` wczytuje dotychczasowy
atlas88 póz i publikuje tylko trzy istniejące składniki statku0b.

Build etapu sąsiadów ma0 błędów/ostrzeżeń,146207467 bajtów, a DLL SHA256
`b4d0da08e2f6e1ec51e751de12a45c7057d4df0e6f827ace11576d15ffbb7cd1`.
155 testów przeszło bez pominięć w58.160s. Pilotaż E przeszedł:
[osiem kadrów i24 obszary](artifacts/adjacent/runtime-first-h0/report.json)
mają RGBmean/max0; zwolniono8 zajęć i proces wyszedł z kodem0.
[Pełny raport](artifacts/adjacent/runtime-final/report.json) potwierdza10 sesji,
53 kadry i159 ROI RGB0, cleanup8 w9 sesjach i9 po przerwaniu rezerwacji,
exit0 we wszystkich. Sześć grup regresji także przeszło na tym DLL.
Zapisano75 prób obrazu:53 zaakceptowano,22 odrzucono;8 z nich było dokładnie
identycznych z wcześniejszym zapisanym etapem. Progi całego kadru pozostają≤4.
Aktualna preferencja: kolejne podglądy i ZIP tylko na wyraźną prośbę.

To zamknięta projekcja źródłowych sąsiadów jednego statku, z jawnymi
wind0/heading5/upgrade0 i kwantem40ms. Planowanie przy counter1, a kroki
ruchu przy2,3,… są harmonogramem diagnostycznym: pełny oryginalny Life może
planować i poruszać w tym samym counter. Zatrzymania obrazów zamrażają
czas diagnostyki i nie potwierdzają tempa gry. Rangi źródłowych składników
zachowują kolejność wyłącznie w sprawdzonym obrysie tej sceny. Normalny
Start jest wyłączony; ogólny pathfinder, swobodne sterowanie, AI, walka,
pogoda świata, oprawa2026 oraz testy Windows11/laptopa pozostają otwarte.

Dowody: [runtime](docs/SHIP_ADJACENT_RUNTIME_VALIDATION.md),
[nawigacja](docs/SHIP_ADJACENT_NAVIGATION_EVIDENCE.md),
[sąsiednie trasy i ruch](docs/SHIP_ADJACENT_MOVEMENT_EVIDENCE.md),
[obrót](docs/SHIP_TURN_ANIMATION_EVIDENCE.md),
[stemple czasu i kolejność świata](docs/SHIP_ADJACENT_WORLD_EVIDENCE.md).

## Zakończony etap dłuższych tras i kolejności grafik

`--ship-route-reference` uruchamia źródłowe planowanie i ruch0b z `(16,2)`,
heading5, do dalszego celu. Pośrednie punkty, skręty z zachowaną prędkością,
rezerwacje oraz oczekiwanie przed zajętym celem mają osobne dowody.
Planer otrzymuje źródłową mapę i jawny statyczny zbiór ośmiu właścicieli;
nie oznacza to pełnej inicjalizacji ani symulacji pozostałych klas świata.

Porównania z oryginalnym x86 obejmują: falę749 pól/390267 komórek,
`SourcePathfinder`374 przypadki pełnych ścieżek i pól, `ShipRoutePlanner`
wszystkie576 celów (362 plany,214 bez instalacji trasy) oraz ruch32 ślady/
1593 stany/1561 wywołań/1046 uporządkowanych publikacji/248 zapisów siatki.
Osobny `SourceSpriteDepthQueue` ma3849 zgodnych operacji i14 kontroli API.
Zachowuje historię remisów, gdy0b przecina rangę statków0d i0c. Każda
publikacja zmienia kolejkę, także gdy jeden call publikuje dwie pozy.

Nowy build Windows ma0 błędów/ostrzeżeń i146250459 bajtów. DLL SHA256:
`a54b9ea4de6db05a458794758e26b27600f5aa56c9b78c091583e45448b10fba`.
172 testy przeszły bez pominięć; sprawdzono87 meta i41 plików C# bez braków
lub niepoprawnych GUID. [Pilotaż zakrętu](artifacts/long-routes/runtime-first-bend/report.json)
ma16 kadrów RGB0 i potwierdza31 pól stanu oraz34 rzeczywiste odczyty
kolejności rendererów. [Końcowy raport](artifacts/long-routes/runtime-final/report.json)
potwierdza7 sesji:4 dojazdy, odmowę terenu, zatrzymanie przed zajętym celem
i przerwanie po drugiej rezerwacji. Wszystkie88 kadrów i264 obszary mają
RGBmean/max0. Sprawdzono31 pól, pathhex,21 rejestracji i34 rzeczywiste
odczyty kolejki; cleanup zwolnił8 zajęć w6 sesjach i9 w ostatniej, wszystkie
exit0. Zachowano128 prób obrazu;40 odrzucono przed ścisłą zgodnością:
16 dokładnie odpowiada wcześniejszym zapisanym etapom,24 nie sklasyfikowano.
Siedem grup regresji przeszło na tym samym DLL: sąsiedzi10 sesji/53 kadry/
159 ROI, wcześniejszy odcinek2 sesje/9 kadrów/27 ROI, statki3 kadry/8 obszarów,
rafy4 i teren3 — RGB0. Briefing39 etapów/11 obrazów oraz menu27 etapów/
5 obrazów/6 komend zakończyły się normalnym Quit0. Starsze155 i143 testy
oraz paczki pozostają dowodami własnych wcześniejszych artefaktów.

Warunki pozostają jawne: wind0/heading5/upgrade0, pending1, kwant40ms,
planner przy counter1 i ruch odcounter2. Oryginalny Work może planować
i poruszać w jednym counter; pełny Life, retry i dobór celu pośredniego
nie są przeniesione. Zatrzymania etapów służą wewnętrznemu QA, bez
potwierdzenia tempa pełnej gry. Normalny Start jest wyłączony. Swobodne
sterowanie, dynamiczny świat, AI, walka, pogoda, finalna oprawa2026
oraz natywny Windows11 i laptop pozostają otwarte. Nie tworzymy nowego
ZIP ani podglądu do prezentacji; wewnętrzne framebuffer’y są dowodami QA.

Dowody: [runtime](docs/SHIP_ROUTE_RUNTIME_VALIDATION.md),
[fala](docs/SOURCE_WAVE_FIELD_EVIDENCE.md),
[planer pól](docs/SOURCE_PATHFINDER_EVIDENCE.md),
[adapter statku](docs/SHIP_ROUTE_PLANNER_EVIDENCE.md),
[ruch wielopunktowy](docs/SHIP_ROUTE_MOVEMENT_EVIDENCE.md),
[kolejność grafik](docs/SOURCE_SPRITE_DEPTH_QUEUE_EVIDENCE.md),
[kolejność work i granica dojazdu](docs/SHIP_ROUTE_ORDER_EVIDENCE.md).

## Zakończony etap obiegu rozkazów ruchu

`--ship-order-reference` uruchamia źródłowe request→promotion→Work→MoveShip
przy wspólnym counter,od początku0. Cel wskazują `--ship-order-target-x/y`
(domyślnie18,5),a para `--ship-order-next-x/y` zleca kolejne polecenie dopiero
po usunięciu active80,fizycznym state0 i publikacji idle. Nie obejmuje
zastępowania aktywnego rozkazu podczas ruchu. `--ship-order-stop-at` ogranicza
liczbę Tick;`--ship-order-session-seed` wybiera kontrolowany uint32 seed.
Domyślne0 jest wejściem diagnostyki,nie domyślnym seedem nowej misji.

`SourceNearestPathfinder` ma1380 porównań pełnych ścieżek/pól z oryginałem
oraz9 kontroli API. `ShipReplanPlanner` ma228 porównań i13 kontroli:
aktualną pozycję/rezerwację,cel zastępczy,pamiętane przeszkody i wspólny RNG.
`ShipIdleProgression` ma4232 porównania,77 inicjalizacji seeda i96 całych
wywołań MoveShip. Idle losuje próg przy każdym wywołaniu i publikuje obraz
przed zmianą stored frame. Nie zeruje RNG po przyjęciu kolejnego polecenia.

`ShipMoveOrder` potwierdza7 scenariuszy i956 stanów,941 kroków,
446 uporządkowanych publikacji,62 zapisów siatki oraz35 kontroli API.
Endpoint ścieżki,żądany cel i koniec active80 są osobnymi obserwacjami:
dla żądanego18,2 ścieżka kończy się17,2,a po180 Tick rozkaz pozostaje aktywny.
W przypadku20,4 źródło usuwa active80 podczas wyhamowywania,przed końcową
kotwicą obrazu. Następny request nie powtarza publikacji poprzedniego Tick.

Build ma146287259 bajtów,0 błędów/ostrzeżeń,DLL SHA256:
`6c646f8c6313ff0005d51dffda7596e986dad0101f6a2432f831474229bc4773`.
Pełny discovery182 testy/0skip/151.698s i osobne7 kontroli helpera/0skip/6.221s
przeszły.46 plików C# i92 meta nie mają
brakujących,błędnych ani powtórzonych GUID. Po buildzie nie zmieniano C#.
Pilotaż ma12 kadrów/36 ROI RGB0 i nie jest doliczany do końcowych53.
[Końcowy player](artifacts/order-cycle/runtime-final-resumed/report.json)
przeszedł4 scenariusze:normalny rozkaz,nearest18,2 obserwowany do180 Tick,
dwa polecenia po kolei i halt46.53 kadry/159 ROI mają RGBmean/max0;
54 pola,pathhex/cache i34 rzeczywiste odczyty kolejki na etap są zgodne.
Cleanup8/8/8/9 i exit0 wszystkich sesji.63 próby obrazu obejmują10
odrzuconych:6 dokładnych wcześniejszych checkpointów i4 niesklasyfikowane.
Na tym samym DLL przeszły cztery grupy regresji:wyłącznie depth-cross
oraz halt-second-reservation dłuższych tras (2 sesje/28 kadrów/84 ROI RGB0,
cleanup8/9),wcześniejszy odcinek (2 sesje/9 kadrów/27 ROI RGB0,cleanup8/9),
briefing39 etapów/11 obrazów oraz menu27 etapów/5 obrazów/6 komend.
Wszystkie procesy exit0;UI zakończyło się normalnym ApplicationQuit0.
Nie jest to ponowienie całych siedmiu historycznych grup ani wszystkich
wcześniejszych scenariuszy tras. [Agregat regresji](artifacts/order-cycle/regression-aggregate.json)
zachowuje ich dokładny zakres.

To nadal kontrolowany zdrowy0b,wind0/heading5,upgrade0 i siedem
nieruchomych jednostek. Holdy QA nie dowodzą tempa pełnej gry. Pełne Life,
sterowanie gracza,AI,walka,pogoda świata,save/load,finalna oprawa2026 oraz
natywny Windows11/docelowy laptop pozostają nieukończone lub niezweryfikowane.
Normalny Start pozostaje wyłączony. Bez nowego ZIP,podglądu do prezentacji i publikacji.

Dowody: [koordynator](docs/SHIP_MOVE_ORDER_EVIDENCE.md),
[ponowne planowanie](docs/SHIP_REPLAN_PLANNER_EVIDENCE.md),
[najbliższa ścieżka](docs/SOURCE_NEAREST_PATHFINDER_EVIDENCE.md),
[idle i RNG](docs/SHIP_IDLE_ANIMATION_EVIDENCE.md),
[runtime i granice](docs/SHIP_ORDER_RUNTIME_VALIDATION.md),
[kontrole helpera i audyt](docs/SHIP_ORDER_QA_EVIDENCE.md).

## Zakończony etap źródłowych masek trafienia

`ShipPointerMask` przenosi wyłącznie źródłowy predykat `4e06c0` wraz z
lookupem sekwencji `5431d0` i testem bitu `5575d0`. Precyzyjny test korzysta
z osobnych masek type18,a nie alfy grafiki. Dla stored frame32…55 wybiera
maskę frame−32;pozostałe normalne klatki wybierają byte(heading×3).
Coarse precision0 zwraca true przed testem geometrii. Arytmetyka int32
zawija się zgodnie z oryginałem;stride jest wyrównany do8 bitów.

Nowy staging [stage_ship_picking.py](tools/stage_ship_picking.py) sprawdza
hash EXE/OBJECTS i zapisuje siódmy zestaw Resources:24 maski dla każdej
rodziny A1/H1/B4/G4,łącznie96 płaszczyzn i52800B. Geometria pochodzi
z type8. Zmodyfikowany wcześniejszy payload nie jest nadpisywany nawet
przy replace-generated. Renderowania ani pozostałych sześciu zestawów nie zmieniano.

Rzeczywisty x86 i checked C# porównano w432428 wywołaniach:
423960 pikselach pełnych płaszczyzn (96 oryginalnych+24 syntetyczne dla
paddingu) i8468 osobnych punktach.13 kontroli API i5 testów celowanych
przeszło. [Build](artifacts/world-input/picking/build-report.json) ma146364475B,
0 błędów/ostrzeżeń,DLL SHA256:
`e211062e1098162e28bc1dcdf66ef9851a8dbfb2666f18d486b6e7e4443e2e89`.
Sprawdzono47 C#/96 meta bez braków,błędnych lub powtórzonych GUID;
po buildzie C# bez zmian. [Świeży discovery](artifacts/world-input/picking/unittest-resumed.log)
po wznowieniu ma194PASS/0skip/181.146s. Wcześniejszy przebieg przerwany
na prośbę użytkownika pozostaje historyczny i nie jest dowodem194PASS.

[Regresja normalnego rozkazu i dwóch poleceń](artifacts/world-input/picking/order-regression/report.json)
na nowym DLL ma2 sesje/35 kadrów/105 ROI RGBmean/max0,54 pola,
21 rejestracji na sesję i1190 faktycznych odczytów kolejki. Cleanup8/8,
exit0;45 prób obrazu,10 odrzuconych:tylko7 dokładnych wcześniejszych
checkpointów i3 niesklasyfikowane. Wszystkie80 PNG sprawdzono niezależnie
w postaci zakodowanej i po dekodowaniu. To regresja starszych rozkazów;
nie potwierdza nowego world pickera ani input.

Nie ma jeszcze pełnego world pickera49a580 ani porządku sąsiadów,fog,
pozostałych slotów obiektów,własności,reguł wyboru grupy i przekazania
kliknięcia do actor action20. Kolejne kroki to world query,zaznaczenia
oraz group commands,integracja InputSystem i wizualizacja wyboru.
[1206 źródłowych zapytań pickera](docs/WORLD_PICKER_ORDER_EVIDENCE.md)
na końcu tamtego etapu był dowodem do portu;nowy ograniczony adapter C# opisano niżej.
Normalny Start pozostaje wyłączony;pełne Life,AI,walka,pogoda świata,
finalna oprawa2026 i natywny Windows11/laptop nadal są otwarte.
[Dowód i zakres](docs/SHIP_POINTER_MASK_EVIDENCE.md).

## Bieżący etap ograniczonego pickera statków

`ShipWorldPicker` przenosi statek-slot branch49a580 na siatce24×24,
przy jawnym braku fog i pustych pozostałych slotach. Najpierw testuje
właściciela komórki,przy precise także sąsiadów we właściwej kolejności
krawędzi/narożnika. Zwraca pierwszą trafioną referencję;nie sortuje według
sortingOrder i nie usuwa duplikatów current/reservation. Korzysta ze
sprawdzonego `ShipPointerMask`.1206 zapytań i5665 uporządkowanych odwiedzin
z oryginału zgadza się z actual checked C#;21 API guards oraz2 testy celowane/1.701s PASS.

`--ship-picking-reference` uruchamia istniejący obieg rozkazów z opcjonalnym
obserwatorem `ShipPickingReference`. Korzysta z dotychczasowych argumentów
`--ship-order-target-x/y`,next,stop-at i session-seed. Na checkpointach
wiąże8 rzeczywistych właścicieli/masek oraz aktualne current/reservation,
opublikowane współrzędne,stored frame i heading. Zapytania nie mutują siatki.
Tryb wyklucza pozostałe diagnostyki ruchu i replay UI;zwykły Start nie jest odblokowany.

[Build](artifacts/world-picker/build-report.json):146377147B,0 błędów/ostrzeżeń,DLL
`a706aa5e9d9a5966b78c84bc1eace6f669f655a0e94601f82aeb2002e5305409`.
49 C#/98 meta bez braków,błędnych i powtórzonych GUID;7 zestawów Resources bez zmian.
196 testów discovery/0skip/175.263s i osobne7 testów QA/6.968s PASS.
[Osobny pilot](artifacts/world-picker/runtime-first-normal/report.json):
12 kadrów,306 zapytań i96 powiązań,nie doliczane do pełnego zestawu.
[Pełny player](artifacts/world-picker/runtime-final/report.json):4 sesje/
53 kadry/159 ROI RGBmean/max0,1353 actualqueries,1243 odwiedziny predykatu
oraz57 zapytań z duplikatami właściciela.424 powiązania actor/maska/poza,
53 pełne kontrole niezmienności zajętości576 komórek i1802 rzeczywiste odczyty
kolejki przeszły. Cleanup8/8/8/9,exit0 wszystkich sesji.
58 prób obrazu/5 odrzuconych:tylko4 dokładne wcześniejsze checkpointy i1
niesklasyfikowany.111 PNG sprawdzono niezależnie przed i po dekodowaniu.
[Regresja starszego normalnego rozkazu](artifacts/world-picker/legacy-order-regression/report.json)
bez obserwatora:1 sesja/12 kadrów/36 ROI RGBmean/max0,cleanup8/exit0,
bez prefiksu nowych zapytań. [Menu](artifacts/world-picker/menu-regression/report.json)
przeszło syntetyczny InputSystem replay:27 etapów/5 obrazów/6 komend,
normalny ApplicationQuit0. Oba raporty wiążą ten sam DLL a706….
Nie jest to powtórzenie wszystkich starszych regresji ani test input w rozgrywce.

To diagnostyczne zapytania świata,nie InputSystem,hover,drag,wybór gracza
ani przekazywanie komend. [Źródłowy dowód membership i ruchu](docs/WORLD_MEMBERSHIP_MOVEMENT_EVIDENCE.md)
pokazuje różne pola grupy5c/5e i efekt action41;nie jest portem grup do C#.
Pozostają pozostałe sloty/fog,reguły zaznaczania i grup,komendy do actor,
InputSystem i wizualizacja wyboru,pełne Life/AI/walka/oprawa2026 i testy Windows11/laptopa.
Dowody:[kolejność i adapter](docs/WORLD_PICKER_ORDER_EVIDENCE.md),
[runtime i granice](docs/WORLD_PICKER_RUNTIME_VALIDATION.md).

## Materiały oryginału

Sprawdzono wszystkie 13 części RAR i obraz BIN/CUE: 289 plików płyty, 120 plików
instalatora, siedem ścieżek audio. Po publikacji środowiska ponownie potwierdzono
SHA-256 materiałów. Odczytano 62 kontenery / 76 243 rekordy, 5275 obrazów,
164 klipy PCM, 31 zestawów fontów / 74 atlasy i indeksy/maski 52 377 sprite’ów.

- [Katalog oryginału](docs/ORIGINAL_CATALOGUE.md), [instalator](docs/SETUP_FORMAT.md),
  [zasoby i korekta fontów](docs/ASSET_FORMATS.md), [sprite’y](docs/SPRITE_FORMAT.md).
- [Statyczna rekonstrukcja oryginalnego menu](docs/UI_REFERENCE.md).
- [Pierwsze kafle i sprite’y świata z potwierdzoną paletą](docs/WORLD_ASSET_REFERENCE.md).
- [Plan małych etapów](docs/REMAKE_PLAN.md) i [macierz wymagań](docs/REFERENCE_MATRIX.csv).

Osobnych źródeł C++ nie znaleziono. Ghidra wyeksportowała 139 funkcji i 212 xrefów
z programu; napisy ścieżek `.cpp` nie są kodem źródłowym. Oryginał PE32 nie doszedł
do menu w tej maszynie. Wine 11 trafia na nieobsługiwaną ścieżkę 32-bitowego
wywołania jądra `int 0x80` podczas inicjalizacji WOW64, przed kodem gry. Do pełnej
bazy porównawczej potrzebny jest działający oryginał na Windows lub zgodnym hoście:
[ORIGINAL_RUNTIME.md](docs/ORIGINAL_RUNTIME.md). Wydajności docelowego laptopa
ani natywnego Windows 11 nie zmierzono. Dostęp do nagrań zewnętrznych również
nie dostarczył zweryfikowanego gameplayu: [EXTERNAL_REFERENCES.md](docs/EXTERNAL_REFERENCES.md).

## Przygotowanie i testy

```sh
cd /workspace/gierka
python3 -m venv .venv
.venv/bin/python -m pip install --no-cache-dir -r tools/requirements-analysis.txt
.venv/bin/python -m pip check
bash tools/setup_7zip.sh
bash tools/setup_unity.sh
.venv/bin/python -m unittest discover -s tests -v
```

[UNITY_ENVIRONMENT.md](docs/UNITY_ENVIRONMENT.md) opisuje przypięte narzędzia,
licencjonowanie i dostęp do keyringu poza sandboxem. Skrypty instalacji nie
aktywują samodzielnie licencji i niczego nie publikują. Zasoby oryginału są w
ignorowanym `reference/raw/ancient-conquest/`; raporty i prywatne eksporty w
`artifacts/`. Nie umieszczamy oryginalnych binariów w Git.

Przygotowanie natywnych warstw i build: [FIRST_FRAME.md](docs/FIRST_FRAME.md).
Powtórzenie pojedynczych analiz:

```sh
.venv/bin/python tools/inventory_disc.py \
  'reference/raw/ancient-conquest/disc/[PC] Ancient Conquest.cue' \
  --output artifacts/original/disc-new.json
.venv/bin/python tools/extract_setup.py \
  reference/raw/ancient-conquest/files/SETUP.DAT \
  --output artifacts/original/setup-new.json
.venv/bin/python tools/validate_boss_ai_gate.py \
  --output artifacts/binary-analysis/boss-gate-validation-new.json
```

Raporty i katalogi eksportu muszą być nowe; narzędzia chronią istniejące dane.
Testy analizy, pojedyncza reguła i widok menu nie potwierdzają kompletnego remake’u.
