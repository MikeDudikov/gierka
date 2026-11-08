# Pierwszy rozkaz UI przez świat — 2026-11-04

Status: ukończony ograniczony etap diagnostyczny. Pełna gra pozostaje w budowie.
Nowy tryb `--ship-pointer-fleet-world` łączy istniejący wybór i pierwszy zwykły
rozkaz floty z `ShipWorldStep`, wspólnym członkostwem i zadaniem100/1.
Starszy tryb bez tej flagi pozostaje referencją regresji.

## Kolejność i własność stanu

1. Oryginalna gałąź520352..5203ec wykonuje521500 PrepareMail,
   522850 SendMail, następnie542320/542200 SystemLife. Miejsce grupy względem
   statków wynika z jawnego wektora rejestracji; nie istnieje globalna faza
   „wszystkie grupy przed statkami”. Pełna rejestracja oryginalnej misji
   nadal nie jest ustalona i nie jest wyprowadzana z ID ani sortingOrder.
2. UI zatwierdza wybór przez istniejące `CommitPending` (49ca60),
   tworzy100/1 przez `RequestNormalMove` (4ccc30) i umieszcza41 przed20
   w tej samej kolejce `ShipWorldStep.Command`. Kliknięcie nie wywołuje
   `ConsumeNext`, `ReceiveMembership` ani odbioru20 w statku.
   PoleUI5c jest już ustawione, lecz SIM5e i inbox pozostają bez zmian.
3. `ShipWorldStep.TryAdvance` jako jedyny wykonuje Begin/Complete40ms.
   Odbiór41 synchronizuje5e przez istniejące `ConsumeNext` (50c970),
   odbiór20 poprzedza promocję i Work statków. Przy poczcie0 pierwsza
   dostawa jest w tick3, przy1 w tick2, przy2 w tick1. Pakiety wyemitowane
   dopiero przez grupę wewnątrzLife zostają do kolejnej fazy poczty;
   nie dodano drugiego opróżnienia kolejki ani wymuszenia tego samego ticku.

`ShipFleetMotionReference.BindInputWorld` wiąże istniejące trzy kadłuby
z tym samym `ShipFleetMembership`, które obsługuje wybór UI.
Czytnik planera używa jego5e; tablica legacyGroups nie staje się drugim
źródłem prawdy. `AdvanceInputWorld` przekazuje czas/licznik/fazę/teren/kolejkę
jawnie do czystego C#. Po kroku adapter odczytuje publikacje50d5f0 w kolejności
świata i aktualizuje istniejące pozy, głębokość oraz selektory.
Nie dodano nowego MonoBehaviour, TickManager, ECS, Unity physics lub Update
sterującego nową logiką. Istniejący Update pozostaje adapterem czasu i widoku.

`SingleStepClock`, `ShipWorldStep`, `ShipMoveOrder`, `ShipFleetMembership`,
`ShipFleetNormalTask` i `MissionOccupancyGrid` nie zostały zmienione.
UI nie zapisuje bezpośrednio pól członkostwa ani komórek zajętości.
Nowe metody adaptera mają odniesienia do adresów kodu maszynowego.
W zweryfikowanym zakresie kod jest w pełni zgodny z istniejącym
`SingleStepClock` i nie narusza deterministycznego stanu symulacji.
Ta deklaracja dotyczy poniższego korpusu i kontrolowanych granic.

## Walidacja

- Świeże x86 i checked C#:12przypadków,2400klatek,7200stanów,
  4pozycje floty × poczta0/1/2,72odbiory,1632publikacje,20kontroli API.
- UI wykonuje rzeczywiste procedury wyboru/release w osobnym dotychczasowym
  emulatorze. Jego6pakietów musi być identyczne z wynikiem49ca60/4ccc30
  w emulatorze świata. Dalej poczta, grupa i trzy kadłuby działają już
  w jednym silniku x86. To jawnie sprawdzona granica między emulatorami,
  nie jeden kompletny oryginalny RunApp i nie oryginalne C/C++.
- ShippingDLL potwierdza7200stanów oraz regresje:cohort7704,
  world5388,busyworld5088,live10827 i130przypadków planowania.
- Player/InputSystem:zimna poczta0 i flota pierwsza oraz poczta2 i flota
  ostatnia. Każdy przebieg23punkty/69stanów/230części/782odczyty rzeczywistej
  kolejki/136publikacji/6pakietów/exit0. Dostawy odpowiednio3 i1.
  Sprawdzono także anulowanie wyboru,Ctrl przywołujące całą grupę,
 23odczyty kontekstu świata,usunięcie subskrypcji i zwolnienie3póz/8claims.
- Starszy tryb wejścia bez nowej flagi:23/69/230/782/136/6pakietów,exit0.
- 5testów celowanych PASS0skip65.669s;3testy checkera PASS0skip10.299s.
  Checker odrzuca6celowych błędów:przedwczesne5e/odbiór,znacznik ticku,
  wiek grupy,wyłączony lifecycle i brak końcowego kontekstu.
  Dodatkowo akceptuje nieukończoną linię tylko jako oczekiwanie na zapis.
 300testów discovery;pełnego zestawu nie uruchamiano.
- Zachowano źródłowy próg okresowej pracy grupy:sprawdzenie wieku>100
  następuje przed dodaniem kroku. W tym korpusie tick200 ma wiek99,
  nie200. Nie zeruje to zadania100/1 ani nie wymusza zakończenia80 statku0d.
- Unity6000.3.27f2,Windows64Mono,152965163B,0błędów/0ostrzeżeń,
 1920×1080,16:9,ExclusiveFullScreen. DLL SHA256:
 `795a40e19767188766c28a1c911a62818ec6462906742534bb69fa58e05ee9ae`.
- 73C#/131unikalnychmeta;zmieniono2istniejące adaptery,71C# bez zmian.
 275plikówAssets/Packages/ProjectSettings niezmienionych przez build,
 78Resources/10stagingów/9wejść oryginału bez zmian.

Fixture `ship_fleet_ui_world.json`,SHA256:
`9ffb6a782dce24639a0b59cba50fc70c5b1f9e980185eee886242f224b8f1728`.
Zapis playera `ship_fleet_ui_world_player.log`,SHA256:
`eb577ab1b3202b4c8dcd1d4c102c30708a2f9b685f2a27f409f3e817a2891415`.
Dowody:[artifacts/fleet-ui-world](../artifacts/fleet-ui-world).
Punkt kontrolny:[milestone](evidence/milestone-20261104-fleet-ui-world.json).

Pierwszy runtime został odrzucony przez kontrolę niezmienności,ponieważ
podczas wykonywania poprawiono checker odczytu niepełnej linii logu.
Zachowano failure.json;końcowe przebiegi wykonano już na zamrożonych plikach.
Pierwsza kontrola negatywna zakładała błędnie wiek200;skorygowano wyłącznie
założenie testu do rzeczywistego99. Zachowano checker-tests-first.log.
Znany komunikat ComputeBufferGC przy zamykaniu i deprecacjePillow w QA
pozostają;nie są nowymi ostrzeżeniami kompilatora Unity.

## Uruchomienie i ograniczenia

Do dotychczasowych flag `--ship-pointer-reference --ship-pointer-fleet-selection
--ship-pointer-fleet-movement` dodać `--ship-pointer-fleet-world`,
`--ship-fleet-world-registration fleet,11,12,13` i opcjonalnie
`--ship-pointer-fleet-world-mail 0` (domyślnie2). Wektor musi zawierać
wszystkie trzy statki i flotę raz. Mail to jawny kontrolowany stan wejściowy,
nie pełna inicjalizacja PlaySystem. Replay używa istniejącego
`--ship-pointer-fleet-movement-replay` i syntetycznego InputSystem.

Blokady kolejnego rozkazu,Shift/queued,busyUI i edycji zatwierdzonej grupy
pozostają. Zwykły Start nadal wyłączony. Ship::Life w oracle pozostaje
udokumentowanym trampoline do rzeczywistego Promote+Work;inneLife,
AI,pełna misja i tworzenie grafiki oryginału nie są dowiedzione.
Nie wykonano nowego porównaniaRGB,podglądów,PNG lub ZIP;QA kompozycje tylkoRAM.
Wine/Xvfb nie dowodzi natywnego Windows11,OSmouse,wydajności laptopa ani
oprawy2026. Nie publikowano ani nie aplikowano konfiguracji środowiska.

Następny krok:zbadać x86 i przenieść kolejny normalny rozkaz UI podczas ruchu
tej samej grupy,łącznie z zastąpieniem100/1,pocztą i arbitrażem80.
Nie odblokowywać Shift lub kolejkowanych rozkazów przy okazji.
