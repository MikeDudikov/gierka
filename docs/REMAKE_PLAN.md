# PRZEKAZANIE DO CLAUDE CODE — 2026-11-04

Użytkownik polecił zakończyć ostatnią diagnostykę i przygotować przeniesienie.
Bieżący rozwój w tej sesji jest zatrzymany. Nie wznawiać automatycznie
historycznych planów ani instalatora. Niczego nie publikować lub pushować.
Instrukcje docelowe: [CLAUDE.md](../CLAUDE.md),
[handoff/START_TUTAJ.md](../handoff/START_TUTAJ.md) i
[handoff/STAN_I_PLAN.md](../handoff/STAN_I_PLAN.md).
Ostatni sprawdzony kod pozostaje na checkpoint source-app-activation:
74CS/133meta/279 plików;DLL670bf3055166d56115afc3e85e9d1e6ff812f991ec7ce956222aea2baedf173c.
Ostatnia VM została zamknięta z blokadą Wine przed instalatorem;instalacja
oryginału nie jest ukończona. Dokładny wynik:handoff/CLOSED_DIAGNOSTIC.json.
Starsze wpisy poniżej są historią i nie nakazują bieżącej kontynuacji.

---

# Aktualny etap — jawny reset kontekstu trasy, 2026-11-04

Prace wykonywać autonomicznie, bez proszenia o kolejne wznowienie.
[WM_ACTIVATEAPP i port widoczności](SOURCE_APP_ACTIVATION.md) ukończone:
96 przypadków x86, 4 mutacje; 150 stanów czystego C# i DLL, 5 mutacji portu.
Rzeczywisty łańcuch producent–BaseSystem–flota usuwa wyłącznie grafikę.
2 nowe playery: po39 checkpointów/117 stanów aktorów/291 publikacji,
4 konteksty i13 kontroli negatywnych; zwykły profil35/105/291 również PASS.
12 testów PASS; 349 discovery bez pełnego run. 33624 stanów regresji DLL PASS.
Build153601435B,0/0,DLL670bf3055166d56115afc3e85e9d1e6ff812f991ec7ce956222aea2baedf173c.
74CS/133meta/279 plików projektu; zmienione2 wcześniejszeCS, dodany1CS+meta.
Clock/World/Task/Membership/Grid/SlotQueue i80Resources bez zmian.
ReceiveSourceRouteContext jest jawnym wejściem zatrzymanego replaya;
OnApplicationFocus nie zmieniono. Nie twierdzić, że fizyczny fokus OS jest sprawdzony.
Następnie usuwać blokadę rejestru instalacji oryginału w prywatnym gościu,
używając rzeczywistego instalatora; nie wymyślać wpisów rejestru.
Zachować1920×1080/16:9/fullscreen. Bez publikacji, aplikacji, push, reset,
ZIP, PNG i nowych agentów. Nie kończyć pracy po pojedynczym checkpoint.
Starsze wpisy poniżej są historyczne i nie nakazują bieżącej pauzy.

---

# PRACE WSTRZYMANE — ostatnie polecenie użytkownika,2026-11-04

Bieżące zadanie ukończono. Nie rozpoczynać kolejnych zadań ani nie wznawiać
automatycznie; wcześniejsze polecenie ciągłej autonomicznej pracy zostało
zastąpione prośbą o zakończenie i raport. Czekać na nowe polecenie użytkownika.
Raport zbiorczy: [RAPORT_POSTEPU_REMAKE_2026-11-04.md](RAPORT_POSTEPU_REMAKE_2026-11-04.md).
Ostatni milestone: evidence/milestone-20261104-right-shift-input.json.
Protokół C45E:12przypadków/3mutacjex86/testPASS;bez integracji niezbadanego odbiorcy.
Planowanego nowego startu oryginału w VM nie rozpoczęto.
Kod gry i build pozostają bez zmian po tym checkpoint. Niczego nie publikować.
Poniższe instrukcje autonomicznej kontynuacji są historyczne.

---

# Aktualny punkt pracy — prawy Shift,2026-11-04

[Odrębny replay prawego Shift](RIGHT_SHIFT_INPUT.md) ukończony.
2RightShift i1LeftShift procesy PASS,rzeczywiste KeyControl sprawdzane;podmiana wykrywana.
Build153599195B0/0,DLLc650a6eda46ba0dbfac6528ed03fcb878df80be6b0092d332d27540605f2565b.
2CSzmienione:ShipFleetMoveInputReplay i diagnostykaWorldPointerInput.
Receiver/Clock/World/Task/Membership/Grid/SlotQueue/80Resources bez zmian.
8wybranychtestów PASS0skip,342discoverybezfullrun.
Następnie źródłowy C45E:producent4ee900 i4efd60;12przypadków już wykonanych,
bez podłączenia dofocus/resize/tick. Najpierw rozwiązać protokół i odbiorcę,nie zgadywać.
Dwa równoczesne Shift w snapshot bez kolejności nadal poza profilem.
Kontynuować autonomicznie po checkpoint,bez kolejnego pytania kontynuuj.
Bez PNG/ZIP/publikacji/aplikacji/pusha/resetu/nowychagentów.
Starsze wpisy poniżej są historyczne.

---

# Aktualny punkt pracy — komunikaty klawiszy Shift,2026-11-04

[Integracja źródłowej widoczności trasy](SOURCE_ROUTE_KEY_VISIBILITY.md) ukończona.
Istniejący WorldPointerInput.onEvent ->ShipPointerReference: C45D(1/0) tylko dla grafiki.
Clock/World/Task/Membership/Grid/SourceSpriteSlotQueue i wszystkie zasoby pozostają bez zmian.
4procesy PASS: committed first/last po33check/99actors/299pub/14marker/4key;
pending first/last po35check/105actors/291pub/22marker/4key.
ShiftUp50 usuwa przed rightUp;Ctrl nie odtwarza;ShiftDown200 odtwarza przed duplikatem.
Duplikat nadal odświeża task+8. Brak globalnej fazy grup/drugiego flush/nowegoUpdate.
Build153598683B0/0,DLL910293df07d49b8938416128ca0343b6694ce17a2dd155185bc5c420b3852ee0.
7wybranych testów PASS0skip,340discovery bezfullrun;historyczne logi zachowane.
Następnie: oddzielny rzeczywisty replay prawego Shift, potem źródłowy rejestr/C45E.
Dwie równoczesne zmiany Shift w snapshot bez kolejności są jawnie poza profilem.
Prefix117 to kontrolowane wejście,nie domyślna właściwość Windows.
Kontynuować kolejne kroki autonomicznie;checkpoint nie kończy pracy.
Bez PNG/ZIP/publikacji/aplikacji/pusha/resetu/nowychagentów.
Starsze wpisy poniżej opisują wcześniejsze etapy.

---

# Aktualny punkt pracy — 2026-11-04

Ukończono dwa kolejne kroki: [kolejkę zatwierdzonej grupy i WPMOVE](QUEUED_INPUT_AND_MARKERS.md)
oraz [pierwszy Shift i cykl grafiki trasy](PENDING_QUEUED_INPUT.md).
Rdzeń Clock/World/Task/Membership/Grid oraz SourceSpriteSlotQueue pozostaje bez zmian.
Pierwszy Shift: 41 przed 20, append/duplikat już w kroku 0, przed odbiorem poczty.
C453 usuwa tylko grafikę; Ctrl i Work jej nie odtwarzają. Duplikat odświeża task+8.
Build 153597659B/0 ostrzeżeń/0 błędów, DLL1c34891e234a59665a78c364f7c3b93a72af85a7eb01abcdb51da9fa2d626b25.
Player flota first/last: po35 checkpoints/105 actors/350 parts/1190 queue/291 pubs/22 markers.
Jawny kontekst signed16; 117 pozostaje wejściem kontrolnym, nie domyślną wartością gry.
Następnie GLOBALNE klawisze Shift: źródłowe C45D(1/0) są odrębne od flag rozkazu;
dowód x86 gotowy w artifacts/queued-key-visibility, jeszcze bez integracji mostka.
Sam Ctrl nie pokazuje trasy, ale Shift może pokazać ją przez C45D.
Nie utożsamiać tych diagnostyk z pełną klawiaturą/aplikacją/AI/Start/oprawą2026/Win11/laptopem.
Kontynuować kolejne kroki autonomicznie; checkpoint nie kończy pracy.
Bez PNG/ZIP/publikacji/aplikacji konfiguracji/pusha/resetowania repo i nowych agentów.
Starsze wpisy poniżej są historyczne.

---

# Ancient Conquest — plan remake’u w Unity

Następny dowódUI również ukończony: [QUEUED_UI_WORLD_EVIDENCE.md](QUEUED_UI_WORLD_EVIDENCE.md).
12cases2400frames48requests7344states zgodne x86/C#/shippingDLL;2testPASS107.791s.
Razem10testów w dwóch zestawach,330discovery bezfullrun. WPMOVE type8 znaleziony
w controlm:21części/36×29,cyfryWPNUM iWPMOVE,offsety/SHA w discoveryJSON;
bez graf.konstruktora lub nowychobrazów. Dalej adapterjawnychsłów/Shift+markery/QA.

Ukończono [integrację100/2 w świecie](QUEUED_WORLD_INTEGRATION.md):50cases/5536frames/
16608stanów,strict1001+3105388stanów,8testPASS188.276s,Windows152977451B0/0.
Zachowano rejestr/clock/pocztę;perstep registry words jawne,bez default117.
Następny etap rozpoczęty:źródłowy UIShift podczas ruchu,append/duplicate/normal
powrót12cases2400frames48requests. Następnie porównanie pełnego C#world tych
żądań i adapterInputSystem z jawnym kontekstem;dopiero odblokować Shift.
User autoryzował podejmowanie kolejnych kroków bez prośby "kontynuuj".
Nie publikować/aplikować,nie tworzyćPNG/ZIP lubnowychagentów. Format1920×1080.
Starsze wyniki historyczne.

---

Aktualny etap: [świat100/2 x86 i port zgłoszeń dotarcia](FLEET_QUEUED_WORLD.md).
Wykonano46scenariuszy/5416klatek i porównano16386stanów aktorów oraz258wywołań.
ShipMoveOrder udostępnia Arrival z obu źródłowych miejsc;nie zmienia tasków.
6testPASS0skip208.196s,3mutC#/3mutx86,clock1287 zgodny;324discovery bezfullrun.
Kolejny mały krok: odebrać Arrival po każdym Tick aktora, według4a1700 i danych
Membership, oraz uruchamiać WorkQueuedTask w istniejącej pozycji floty. Kontekst
każdej fali jawny, bez stałej117. Zweryfikować pełny C#world z tym korpusem,
w tym zróżnicowane słowa i kolejność członków przed włączeniem UI Shift.
Bez globalnej fazy grup, drugiej poczty lub nowej architektury.
300/311,40,taskless events,pełnyLife/AI/Start i oprawa2026 pozostają dalej.
1920×1080/16:9/fullscreen;bez PNG/ZIP/publikacji/aplikacji/nowych agentów.
Starsze wyniki poniżej są historyczne.

---

Etap100/2:port punktów, rekordów członków iWork ukończony w ograniczonym
czystym C#;[dowód i granice](FLEET_QUEUED_PORT.md). Jeden właściciel zadania,
jawny signed16wave[-1],310LIFO+periodicExtra20+staletarget,bez globalnej fazy grup.
64cases1121states i20pełnychpól zgodne x86/C#/DLL;4testPASS132.663s,
Windows64Mono152975403B0/0. Shift pozostaje zablokowane.
Następny mały krok:niezależny korpus100/2 w świecie,z jawną kolejnością rejestru,
pocztą,kontekstem każdej fali i310ze statków. Następnie integracja w istniejącym
ExecuteAccepted,bez nowej globalnej fazy;dopiero wtedy UIShift. Edycja składu
300/311,raport40,pełnyLife/AI/Start i oprawa2026 pozostają dalszymi bramkami.
Zachować1920×1080/16:9/fullscreen;bez PNG/ZIP/publikacji/aplikacji/nowychagentów.
Starsze wyniki poniżej są historyczne.

---

Bieżący etap2026-11-04:oryginalnyCRT wykonany wPE32/VM,nie C#port100/2.
OdblokowanoPE32 w gościu zpreparedprefix+Xvfb/fontconfig;hostPE32 nadalSIGSEGV,
PE64controlPASS. Dwa freshVM:IA32/CONTROL32/CRT exit0,512pomiarów1152B,prefix117.
Wykonano oryginalne58ec07(0)/589bf5/589bc6,bez rekompilacji/relokacji oryginału
lub jego588e44. Własna sekcja580000..5ddfff rezerwujeCRT/data,importsKernel32Wine.
WcześniejszeMAP487 i minimalVMcontrol137 zachowane;QEMUexit0nieoznaczaCRTpass.
13funkcjiCRT C+asm readonly. OfficialDebian i686MinGW6pakietów podpisy+SHA,
/workspace/toolchains/mingw32-crt;setup/build/run_crt_vm.py powtarzalne.
Uwaga:117 to zmierzonyprofilWine32/privateheap/history,nie ogólnastałaWindows.
Freshx86 połączony4przypadki12CMP/24par:misja0i117 emitują3,rozłączna mapa0
emituje3,a117zero(kandydaci0). Nie zastępowaćwave[-1]zerem lub poprawiaćOR.
7testPASS0skip12.933s(4nowe+3regresje),316discovery bez fullrun.
Fixturefda96fcd9758c18c716b9f664737564145124ad131957029e7115dbf6d20ce8d.
73CS/131meta/275projektowych/78Resources/10stages/9oryginałów iDLLfa19e56ad2ee9d6902f89e7b5e423cad9d2f215e35182269727e4ae12ee9b235
bez zmian;bez nowegoUnitybuild/playerQA/GameEntry. Unity1920×1080/16:9/fullscreen.
Czytać[QUEUED_CRT_CONTEXT.md](QUEUED_CRT_CONTEXT.md) i55cases
[SHIP_FLEET_QUEUED_EVIDENCE.md](SHIP_FLEET_QUEUED_EVIDENCE.md).
Następnie pureC#port100/2 punktów/members doobecnegowłaściciela,z jawnym
word[-1] i korpusami55+5+4;nie hardcode117 jako gry.310LIFO+periodicExtra20
musząpozostać. Shift/queued/edycjaskładu/300/311/40/fullLife/AI/Start nadalbramki.
Word117 niepotwierdzonyWin98/Win11/fullGameHeap. Nie deklarować pixel/oprawy2026/
OSmouse/laptopa/performance. BezPNG/ZIP/podglądów/publikacji/aplikacji/nowychagentów.
Starsze wyniki historyczne.

---

Bieżący etap2026-11-04:dowód x86 Shift100/2 przed portem. Bez zmian C#/Unity/player.
55scenariuszy1112stanów2224obserwacje(dwa osobne źródłowe wejścia518070/49e230),
3394wywołania śledzone,209Shift/600queries/101Work/11arrival/519pakietów.
65funkcji Ghidra C+asm readOnly. PierwszyShift usuwa100/1→100/2 i wysyła20 bez
normalnej formacji;następny append nie wysyła20,duplikaty w całej liście pomijane.
Istniejące100/2 iAge zachowane;nowa grupaAge0. Route+4 points12B,route+8 members17B.
310 z prawdziwego4a1700,LIFO;310+wiek101 może wysłać dwa20 temu samemu statkowi
w jednymWork,z targetem członka zachowanym przy pierwszym celu. Nie poprawiać.
Nowa luka kontraktu:4ceab0 przy4cebc7 czyta signedword wave[-1],2B przed1152B.
Osobny korpus5przypadków15CMP/30par:0/5000/-32768 emitują3pakiety,32767 żadnego.
Wartości sztuczne,nie dowód osiągalności w grze. IzolowanyCRT ma naturalne0;
nie zakładać tego w porcie. Obrazpróg5c63b8=1016,1152→HeapAlloc przy tym progu;
rzeczywistyCRT/word[-1] jeszcze nieustalone. Następnie wyjaśnić kontraktCRT,
potem port100/2 do istniejącego właściciela grupy,bez globalnej fazy grup.
5testPASS0skip105.083s+3boundaryPASS0skip8.550s,3mutacje x86.312discovery,
bez pełnego run. KorpusySHA8d0cab94992ccedce32b39d263923107b72bf2d5ecf9b56b9f0966ce7958913a
oraz307f39f575db59672a3232d8d66261b4b18b6d52d986c0adb54897ae88e9418b.
Metadane doprecyzowane,caseSHAe41345cd95470b1c28a50fe7c4570140e24dd09517ca18e228b3943b75a42a64
bez zmian. Przerwane próby formatu metadanych zachowane;finalne osobne logiPASS.
73CS/131meta/275projektowych/78Resources/10stages/9oryginałów iDLLfa19e56ad2ee9d6902f89e7b5e423cad9d2f215e35182269727e4ae12ee9b235
bez zmian. Ostatni build152966699B0/0 jest historyczny;nie nowyport100/2/playerQA.
Czytać[SHIP_FLEET_QUEUED_EVIDENCE.md](SHIP_FLEET_QUEUED_EVIDENCE.md).
WPMOVE ctor/dtor grafiki granice;4ced10 pozycje oryginalne,bez dowodu RGB/assetbinding.
Brak ActorWork/mail/world1002/300/311/40/fullCRT/App/Life/AI. Shift/queued,
edycja składu/Start nadalguardowane. Normalne committedbusyUI poprzedniego
etapu zachowane.1920×1080/16:9/fullscreen;bezPNG/ZIP/podglądów/publikacji/aplikacji/
nowychagentów. Nie deklarować oprawy2026/Win11/OSmouse/laptopa/performance.
Starsze wyniki historyczne.

---

Bieżący etap2026-11-04:kolejny normalny rozkaz zatwierdzonej grupy podczas ruchu.
49e230→49de70→4ccc30 reużywa100/1,bez41/300/resetuAge/immediateReceipt.
UI kolejkuje20 w tej samej poczcie świata;dwa żądania25→6pakietów→odbiór26,
ostatni zapis dla każdego aktora. Begin/Complete i rejestracja bez zmian.
12przypadków2400klatek16żądań7248stanów2416worldRows28API zgodne
świeżyx86+C#+shippingDLL. UI/world osobne emulatory z identycznymi pakietami.
Naturalne stany0/2/5,58b0;nie pełneApp/ShipLife lub wszystkie osiągalneprofile.
Player2warianty floty:first/last po30/90/300/1020queue/229pub/12pkt,exit0.
Sprawdzono Shiftguard i Ctrlrecall. PierwszyUIcold0 i legacyinput po23punktyPASS.
4testPASS0skip88.320s+2checkerPASS0skip11.440s,3mutanty+8negatywnychkontroli.
305discovery bez pełnego run. ShippingfirstUI7200/cohort7704/world5388/
busyworld5088/live10827+130planowań PASS. Unity6000.3.27f2 Windows64Mono
152966699B0/0,DLLfa19e56ad2ee9d6902f89e7b5e423cad9d2f215e35182269727e4ae12ee9b235.
73CS/131meta;2adaptery zmienione71CSbez zmian. RdzeńClock/World/MoveOrder/
Membership/Grid/Task i adapterpóz bez zmian.275frozen/78Resources/10stages/
9oryginałów zachowane. Czytać[SHIP_FLEET_UI_REPLACE.md](SHIP_FLEET_UI_REPLACE.md).
Zachowane pierwsze błędytestowe:bytes dlaUnicorn,obserwatorgridwrites złego
aktora i mutantselector2miejsca. Poprawione tylko narzędzia/testy,rdzeń bez zmian.
Znane ComputeBufferGC/Pillow pozostają. Brak PNG/ZIP/podglądów.
Następnie dowód x86 Shift+rozkaz100/2 i niezależny korpus przed UIportem.
Edycja składu osobno. Shift/queued/innefamilies/Start nadalguardowane;
busyUI dozwolone tylko normalnej zatwierdzonej grupie wzweryfikowanymzakresie.
Nie deklarować pełnegoLife/AI/oprawy2026/Win11/laptopa/performance/RGB.
Bez publikacji/aplikacji i nowychagentów.1920×1080/16:9/fullscreen.
Starsze wyniki historyczne.

---

Bieżący etap2026-11-04:pierwszy rozkaz UI przez wspólną pocztę świata i task100/1.
Nowy jawny --ship-pointer-fleet-world,wymagany kontrolowany wektor rejestracji.
UI CommitPending/RequestNormalMove tylko kolejkują41→20;SIM5e zmienia się przy
odbiorze w ShipWorldStep. Mail0/1/2 daje pierwszy odbiór3/2/1. Grupa pozostaje
w źródłowej kolejności542200,bez globalnej fazy i drugiego flush.
12świeżychx86/2400klatek/7200stanów/4pozycjefloty/20API zgodne C#+shippingDLL.
OracleUI iworld osobne z identycznymi6pakietami,potem jeden silnikworld.
Playercold0/fleetfirst i warm2/fleetlast:każdy23/69/230/782/136pub/6pkt,exit0;
legacyinput także23punkty. Tick200groupAge99 zgodnie ze źródłowym progiem>100.
5testPASS0skip65.669s+3checkerPASS0skip10.299s,6kontrolinegatywnych.
300discovery,bez pełnego run. Shippingcohort7704/world5388/busyworld5088/
live10827+130planowań PASS. Unity6000.3.27f2 Windows64Mono152965163B0/0,
DLL795a40e19767188766c28a1c911a62818ec6462906742534bb69fa58e05ee9ae.
73CS/131meta;2adaptery zmienione71CSbez zmian. Clock/WorldStep/MoveOrder/
Membership/Grid/Task/sceny/ustawienia bez zmian.275frozen/78Resources/10stages/
9oryginałów zachowane. Czytać[SHIP_FLEET_UI_WORLD.md](SHIP_FLEET_UI_WORLD.md).
Pierwszyruntimeodrzucony przez provenance po zmianiecheckera podczas QA;
końcowe3runtime na frozenfiles PASS. Pierwszytest zakładałage200;poprawiony99,
bez zmiany rdzenia. Znane ComputeBufferGC/Pillow pozostają. Bez PNG/ZIP.
Następnie dowód iport kolejnego normalnego UI podczas ruchu:Replace100/1,
poczta,arbitraż80. GuardShift/queued/busyUI/Start pozostają do osobnego dowodu.
Nie deklarować pełnegoLife/AI/oprawy2026/natywnegoWin11/laptopa/wydajności/RGB.
Bez publikacji/aplikacji i nowychagentów.1920×1080/16:9/pełnyekran.
Starsze wyniki są historyczne.

---

Bieżący etap2026-11-04:kontrolowane odtworzenie kohorty w świecie i playerze.
World.RestoreCohortInPlace preflightuje3 rekordy przed zmianą pierwszego aktora.
Zachowane counter/phase/mail/taskAge/membership/grid/rejestracja;import pozaLife.
Actor.ValidateInPlace wymaga tych samych komórek/rezerwacji/next i opublikowanych
pozycji. Poses odświeżane istniejącym adapterem,bez równogłębokościowej reinsercji.
12przypadków/2544klatki/24odtworzenia/7704stany/2568worldRows/29API zgodne
świeżyx86+C#+shippingDLL;4pozycje floty,3syntetyczne zestawy gates.
4testyPASS0skip79.551s,3mutanty;1287clock nadal zgodne.295discovery,bez pełnego
uruchomienia. Shippinglegacy port15096/world5388/busyworld5088/busyactor9984/
live10827+130planowań PASS. Player17punktów51stanów170części578queue136pub,
exit0. Reload1 pokazuje storedframe(np.0b20→47),reload10 zachowuje3pakiety
w kolejce do11;ponowienie102→103. Są jawne capturedTime40*n we replayu,
nie dowód tempa/wydajności hosta. Normalne tryby bez nowej flagi bez zmian.
Unity6000.3.27f2 Windows64Mono152962091B0/0,
DLLfadf3a5c511cc6ad0813c3a43da1c16e95ae2665377cad82eca0a03ac3f80cab.
73C#/131meta;3C#zmienione70bez zmian;275frozenfiles,78Resources/10stagingów/
9źródeł bez zmian. Clock/Membership/Grid/Task/sceny/ustawienia bez zmian.
Czytać[COHORT_WORLD_RESTORE.md](COHORT_WORLD_RESTORE.md),[VALIDATION.md](VALIDATION.md).
Nowy --ship-fleet-world-restore-dir wskazuje zewnętrzne rekordy1/ID.bin i10/ID.bin,
przy dotychczasowych flagach world,busy i jawnej rejestracji. Nie jest to pełny
save/load lub cofanie kontekstu;inne pozycje/konflikty są guardowane. Parentoracle
RestoreOracle przyjmuje seed0 dla połączenia zWorldOracle;stary default bez zmian.
NativeLife nadal trampoline Promote+Work,CRT/grafika granice. Nie ma dowodu
pełnego graficznego tworzenia/usuwania jak oryginał,RGB lub osiągalności wszystkich
gates w misji. Znany ComputeBufferGC pozostał. Bez nowych PNG lub ZIP.
Następnie pierwszy rozkaz floty przez tę samą pocztę świata i taskWork grupy,
z zachowaniem blokad UI Shift/queued/inne taskfamilies/Start. Nie zmieniać
kolejności x86. Pełna gra/oprawa2026/Win11/laptop nadal w budowie lub niebadane.
Bez publikacji/aplikacji,podglądów i nowych agentów.1920×1080/16:9/fullscreen.
Starsze wyniki są historyczne.

---


Bieżący etap2026-11-04:port stanu ruchu i blokującego normalnego80 w C#.
ShipMoveOrder.RestoreSourceMovementState(bytes,counter) czyta oryginalny rekord,
bez natywnych wskaźników. Stan autorytatywny pozostaje w tej samej klasie.
58b odtwarzane z542;deferred265 pominięte przez format,więc zachowane.
Tick:pending8 przed arbitrażem80;zerowy stopMask usuwa pending/deferred;
ready80=0 nie pomija arbitrażu. Zachowano sourcequirk odrzucenia nowego80.
222warianty/15096stanów(2odtworzenia)/10API zgodne świeżyx86+C#+shippingDLL.
Bramki/maski/deferred to kontrolowane wejścia testowe,nie dowód osiągalności
wszystkich kombinacji w misji. Testowy deferred jest wstrzykiwany tylko w harnessie;
produkcja nie ma debugsettera58b/deferred.4testyPASS0skip88.364s,4mutanty;
1287clock nadal zgodne.292testy discovery,pełnego zestawu nie uruchamiano.
Regresje shipping:świat5388,busyworld5088,busyactor9984,live10827,prepared6795,
ownership2486 i130wejść planera PASS. InputSystem/Ctrl23/69/230/782/136,
6pakietów exit0;3właściciele póz i8komórek zwolnione. Znany ComputeBufferGC.
Windows64Mono152960043B0/0,Unity6000.3.27f2,
DLLf3dd1ee9c7064de4a7abeb42adad18a7e59f25120d09901c9d89d8c5591fad69.
73C#/131meta,1C#zmieniony72bez zmian;275frozenfiles,78Resources/10stagingów/
9wejść bez zmian. Nie zmienionoClock,Membership,Grid,Task,scen lub ustawień.
Import wymaga jawnego zegara/membership/grid kohorty. Guard odrzuca konflikt
właściciela lub nieobsługiwany profil przed mutacją. Claim przez istniejąceTryClaim.
Źródłowy import sprite’a odtwarza storedframe;nowy oracle odświeża cache
obserwatora grafiki,nie pozostawia starej publikacji. Bez nowej walidacji pikseli.
Czytać[SHIP_STATE_PORT.md](SHIP_STATE_PORT.md) i[VALIDATION.md](VALIDATION.md).
Nie podłączono save/load lub importu z58b!=0 do playera:nowy kod wykonano
w harnessie C# i shippingDLL na Mono hosta;player jest regresją istniejącegoUI.
Następnie kontrolowana kohorta świata+adapterpóz/kolejkagłębi z jawnym
odtworzeniem wspólnego kontekstu i porównaniemx86. Bez globalnej fazy grup
lub przyspieszania poczty. Shift,Start,pełnyLife/inne taskfamilies/saveLoad/
AI/oprawa2026/Win11/laptop nadal nieukończone lub niezweryfikowane.
Zgodnośćx86 ma bezwzględne pierwszeństwo.1920×1080/16:9/fullscreen.
Bez publikacji/aplikacji,ZIP,PNG,podglądów i nowych agentów. Starsze stany są historią.

---


Bieżący etap2026-11-04:wykonano oryginalny eksport4e12e0 i odtworzenie4e2180.
36 przypadków/1152 kolejnych stanów zgodnych z niezależnym natywnym wykonaniem;
12buforów niezmienionych,24zsyntetyczną zmianą bramki+542(1/255).
Wszystkie naturalne eksporty w tym korpusie miały58b=0. To dowód procedur,
nie pełnego save/load ani osiągalności niezerowej bramki w misji.
3testyPASS0skip19.680s;289testów discovery,pełnego zestawu nie uruchamiano.
Nie zmieniono C#,DLL,scen lub zasobów;nie budowano nowego playera.
Granice CRT realloc i usług graficznych jawne w[SHIP_STATE_RESTORE.md](SHIP_STATE_RESTORE.md).
Następnie przenieść zweryfikowaną reprezentację ruchu do C# z importem bramki
oraz źródłową obsługą pending8/80,deferred i anulowania. Bez debugsettera58b
lub globalnej fazy grup. Obowiązuje poprzedni build normalnego20,blokujący
arbitraż w C# nadal nieodblokowany. Bez publikacji/aplikacji,ZIP,PNG,podglądów
lub nowych agentów. Zgodność x86 ma bezwzględne pierwszeństwo.

---


Bieżący etap2026-11-04:zamknięto dowód źródłowy blokującego arbitrażu.
144kontrolowane przypadki pełnego4abe50→4abc60→4a6330 i późniejszego4ab720;
60anulowań,20odrzuceń nowego80,30zmian stanu fizycznego.3testyPASS0skip23.237s;
286testów discovery,pełnego zestawu nie uruchamiano. Dane bramki/pending/deferred
są wymuszonymi wejściami testowymi,nie dowiedzionymi stanami rozgrywki.
Konstruktor4dc53a rzeczywiście zeruje4B588..58b u3aktorów. Statyczne4e2180
kopiuje0x85B z bufora503 do obiektu54c:58b odpowiada buforowi542.
Nie jest to jeszcze wykonany test pełnego odtworzenia stanu/save/load.
Czytać[SHIP_BLOCKING_ARBITRATION.md](SHIP_BLOCKING_ARBITRATION.md).
Nie zmieniono C#,DLL,scen lub zasobów;nie budowano nowego playera.
Obowiązuje ostatni build z etapu normalnych ponowień20;blokujący arbitraż
nadal nieodblokowany. Następnie dowód źródłowego odtworzenia bloku stanu
oraz kolejnych Work po anulowaniu,przed rozszerzeniem runtime. Bez globalnej
fazy grup,publikacji/aplikacji,ZIP,PNG,podglądu lub nowych agentów.

---


## Bieżący etap — normalny odbiór20 podczas ruchu

Bieżący etap2026-11-04:normalne ponowienia20 w `ShipMoveOrder.ReceiveNormalCellMove`
i odbiór w `ShipWorldStep`. Oryginalne x86 ma bezwzględne pierwszeństwo;
bez globalnej fazy grup lub przyspieszania odbioru nowych emisji.
Profil zdrowych0b/0c/0d,metadane0/255,nieblokujący arbitraż58b==0.
Nie mylić58b ze stanem58c/bramką596. Ostatni20 nadpisuje26B rekord858;
promocja nie zeruje wprost ruchu,trasy lub rezerwacji. Priorytet dopiero
przy promocji,255 zachowuje stary. Stare API/CanRequestMove i blokady UI bez zmian.
18 przypadków/9984stanów/210 rozkazów/12API oraz8przebiegów świata/
1696klatek/5088stanów/4pozycje floty/72odbiór/24emisje zgodne świeżyx86+C#+DLL.
Emisja10→odbiór11 lub36→37;41 nadal przed statkami,indeksy i sloty bez zmian.
4testyPASS0skip70.211s,3mutanty wykryte;1287przypadków zegara nadal zgodne.
Full discovery nie ponawiano;283testy. Regresje starego świata5388stanów,
żywej floty10827/przygotowanej6795/własności2486 potwierdzone na nowymDLL.
Unity6000.3.27f2 Windows152955435B0/0,
DLL5d15a7030ef4b8b544937ebb293cb8fd182a65cd435251668697be865b6b93ce.
73C#/131meta;3istniejąceC#zmienione,70bez zmian,bez nowych klas/meta.
275frozenfiles;78Resources/10stagingów/9oryginalnych wejść bez zmian.
Czytać[SHIP_BUSY_ORDERS.md](SHIP_BUSY_ORDERS.md),[VALIDATION.md](VALIDATION.md).
Nowy przebieg dodaje --ship-fleet-world-busy do wcześniejszych flag świata.
Kolejność całej misji nieznana;kontrolny rejestr/gotowa poczta2,nie pełny Start.
Ship::Life nadal ograniczone do oryginalnych Promote+Work przez trampolinę;
inneLife,AI,35,queued i Shift zatwierdzonej grupy nadal nieprzeniesione.
Następnie blokujący arbitraż przy niezerowych bramkach i skutki anulowania
4abe50→4abc60→4a6330,przed odblokowaniem dalszego UI. Nie resetować sztucznie80.
1920×1080/16:9/fullscreen;pełna gra/oprawa2026/Win11/laptop nadal niewykonane
lub niezweryfikowane. Bez publikacji/aplikacji,ZIP,PNG,podglądów i nowych agentów.
Starsze wyniki i wzmianki o blokadzie wszystkich busy20 są historyczne.

---


## Bieżący etap — zadania grup w SingleStepClock

Bieżący etap2026-11-04:zadania grup w `ShipWorldStep`,wewnątrz
`SingleStepClock.Begin/Complete`. Czysty C# wykonuje PrepareMail→SendMail→
SystemLife;obiekty w jawnej kolejności rejestracji,bez osobnej fazy groups-first.
Nowe emisje zadania zostają w kolejce do późniejszej poczty;już gotowe20/41
są dostarczane przed promocją i Work statków. Emisja201→odbiór/promocja202
potwierdzona x86 i playerem. Zimna bramka3e:0→1→2→odbiór;gotowa2 nie resetuje.
31 scenariuszy/1796 klatek/5388 pełnych stanów/24 permutacje/174 odbiory/
76 emisji/1462 publikacje/20API zgodne źródło+C#+shippingDLL.
4 testy PASS0skip75.531s;5 mutantów wykrytych;1287 przypadków zegara nadal
zgodne. Full discovery nie ponawiano;280 testów w nowym zestawie.
Shipping regresje wcześniejszych7086 porównań PASS. Windows152954411B0/0,
DLL392620c155dc41fde6d61f1c30162d7c8c05113cb9ccc4d37f7a6873c71183cf.
Nowy player14punktów/42stany/140części/476queueReads/98publikacji exit0;
stary InputSystem23/69/230/782/136 i6pakietów exit0. Bez PNG/nowego RGB0.
73C#/131meta,2 istniejące C# zmienione+1 nowy,70 dawnych bez zmian.
275 zamrożonych plików,78Resources/10stagingów/9wejść źródłowych bez zmian.
Oracle wykonuje rzeczywistą pocztę/obieg rejestru,ale Ship::Life zastępuje
trampoliną oryginalnych Promote4ab720+Work4ab930. Nie jest to pełny Life.
Kolejność rejestracji całej misji nadal nieznana;diagnostyka wymaga jawnego
--ship-fleet-world-registration. Ciepła2 w playerze jest kontrolowanym wejściem.
Jedyny autorytatywny5e pozostaje w membership po41;grid zapisuje wyłącznie
istniejący ruch. Nie zmieniono SingleStepClock,Membership,NormalTask,Grid
ani ShipMoveOrder. Następnie busy20 4e2ba0/4abe50/4ab250,przed Shift/kolejnymi
rozkazami.35/queued/AI/pełny Start/oprawa2026 nadal niewykonane lub blokowane.
Zasady:funkcjonalna inżynieria wsteczna,adresy/offsety i x86,bez zgadywania
reguł lub nowego ECS/Update.1920×1080/16:9/fullscreen;Win11/laptop niebadane.
Czytać[SHIP_WORLD_STEP.md](SHIP_WORLD_STEP.md) i[VALIDATION.md](VALIDATION.md).
Bez publikacji,ZIP,podglądów i nowych agentów. Starsze wyniki są historyczne.



## Cel i stan wejściowy

Odtworzyć **Ancient Conquest: Quest for the Golden Fleece** w Unity z zachowaniem
treści, mechanik, AI, tempa, sterowania, układu interfejsu, czcionek i charakteru
obrazu. Modernizacja obejmuje wykonanie wizualne, przy zachowaniu czytelności
i informacji przekazywanych przez oryginał. Wydanie docelowe: Windows 11,
pełny ekran, 1920×1080, 16:9; laptop z i5 opisanym jako 3,6 GHz, 16 GB RAM i RTX 3050 Ti.

To plan wykonania i weryfikacji, nie deklaracja ukończenia gry. Aktualizacja
2026-11-02: pobrano wszystkie 13 części RAR, sprawdzono ich integralność i odczytano
obraz BIN/CUE. Na ścieżce danych są 289 plików; statycznie odzyskano 120 plików
instalatora. Siedem ścieżek audio zachowano bez zmiany bajtów. Osobnych źródeł
C/C++ nie znaleziono w tych plikach; ścieżki `.cpp` w programie są napisami
diagnostycznymi. Katalog i granice tej obserwacji: `ORIGINAL_CATALOGUE.md`.

Po publikacji środowiska zweryfikowano zachowanie źródeł przez SHA-256 oraz
w zakończonym etapie terenu wykonano 94 testy. Poprzedni etap raf ma
109 testów, wszystkie przeszły bez pominięć. Zakończony etap statycznych statków ma 129
testów bez pominięć (`artifacts/units/full-tests-units-final.txt`). Nowy
etap pojedynczego odcinka ma143 testy bez pominięć i zamknięte QA/paczkę.
Zakończony etap sąsiednich celów ma155 testów bez pominięć w58.160s
(`artifacts/adjacent/unittest-final.log`) i build146207467 bajtów
z0 błędów/ostrzeżeń. Pilotaż E ma8 kadrów/24 obszary RGB0, cleanup8
i exit0. Końcowe10 sesji/53 kadry i159 ROI mają RGB0; wszystkie regresje
przeszły na tym samym DLL. Zgodnie z bieżącą preferencją nie tworzono
nowego ZIP ani podglądu do prezentacji. Zakończony etap dłuższych tras ma
build146250459 bajtów z0 błędów/ostrzeżeń i172 testy bez pominięć w107.491s.
Pilotaż zakrętu16 kadrów RGB0 przeszedł. Końcowe7 sesji/88 kadrów
i264 ROI ma RGBmean/max0 oraz zgodne31 pól i34 rzeczywiste wpisy kolejki.
Wszystkie siedem grup regresji przeszło na tym samym DLL, także zwykły Quit UI.
Zakończony etap2026-11-03: obieg request→promotion→Work→MoveShip ma
7 źródłowych scenariuszy i956 porównań stanów. Build146287259 bajtów
przeszedł z0 błędów/ostrzeżeń;discovery182 testy bez pominięć w151.698s
i osobne7 testów helpera QA bez pominięć w6.221s.
Pilotaż playera12 kadrów/36 ROI RGB0 przeszedł. Końcowy zestaw po restarcie
ma4 sesje/53 kadry/159 ROI RGB0,54 pola i34 rzeczywiste wpisy kolejki na etap.
Cleanup8/8/8/9,exit0 wszystkich sesji. Na tym samym DLL przeszły4 grupy
regresji:wybrane2 dłuższe trasy,stary odcinek,briefing i menu.
Zakończony mały etap masek kursora dodaje wyłącznie źródłowy `ShipPointerMask`
i siódmy staging:96 masek/52800B.432428 porównań x86/C#,13 kontroli API
oraz5 testów celowanych/14.360s przeszło. Nowy build146364475B ma0 błędów/
ostrzeżeń. Świeży discovery po wznowieniu ma194PASS/0skip/181.146s.
Regresja dotychczasowych rozkazów na nowym DLL ma35 kadrów/105 ROI RGB0,
cleanup8/8 i exit0. Wcześniejszy przerwany przebieg nie jest dowodem194PASS.
Pełne wskazywanie,
zaznaczanie i sterowanie myszy nie są ukończone.
Bieżący etap ograniczonego pickera dodaje `ShipWorldPicker` oraz osobny
obserwator w `--ship-picking-reference`:1206 zapytań/5665 odwiedzin/21 API
guards actualx86/C#,2 celowane testy/1.701s. Build146377147B ma0 błędów/
ostrzeżeń;discovery196PASS/0skip/175.263s i osobne7 testów QA/6.968s.
Pilot12 kadrów/306 zapytań/96 powiązań przeszedł;pełny player ma4 sesje/
53 kadry/159 ROI RGB0 oraz1353 zapytania/424 powiązania,cleanup8/8/8/9 exit0.
Na tym samym DLL przeszły2 grupy regresji:normalny rozkaz bez obserwatora
12 kadrów/36 ROI RGB0 cleanup8exit0 oraz menu27 etapów/5 obrazów/6 komend
przez syntetyczny InputSystem z normalnym Quit0. To dokładnie te2 grupy. Nie jest to wejście myszą ani zaznaczanie jednostki.
Oficjalny katalog Unity jest
dostępny: wybrano LTS `6000.3.27f2`, rewizja `22188f149405`, wydanie 2026-10-30.
Editor, aktywna Personal i Windows Mono działają. Prawdziwy import i build
URP 2D przeszły bez błędów. Pierwszy build etapu obiektów ma 0 błędów
i 0 ostrzeżeń. Obrazy raf, regresja terenu oraz regresje UI przeszły na tym samym DLL
tego poprzedniego etapu. Build statycznych statków również przeszedł: 0 błędów,
0 ostrzeżeń, 144110843 bajty (`artifacts/units/build-report-final.json`).
Pięć grup końcowego QA przeszło na tym samym DLL: trzy kadry statków,
cztery kadry raf, trzy kadry terenu oraz regresje briefingu i menu. Pełne
obrazy świata i osiem obszarów statków mają błąd RGB 0 pod Wine/Xvfb.
Uruchomiono go pod Wine 11 i potwierdzono historyczny pełny ekran 1280×1024 bez pasów. Najnowsze wymaganie użytkownika
zmienia całą grę na 1920×1080/16:9; bieżący staging i płótno już je stosują.
To natywny prototyp menu z osobnym tłem HD i atlasem stanów przycisków,
nie kompletna rozgrywka. Regułę AI sprawdzono w 35 przypadkach z kodem maszynowym,
przyciski w 150 krokach / 44 ciągach, a wydzieloną gałąź zegara w 1287 przypadkach.
Po pierwszych dziewięciu próbkach świata odtworzono statyczny teren `miss000`:
24×24 komórki, osiem warstw, 264 klatki i 1007 operacji rysowania. Wszystkie
użyte klatki mają porównania z oryginalnymi blitterami x86 (1584 bufory).
Parser C# zgadza się z 4608 odwołaniami mapy; wydzielona arytmetyka viewportu
przeszła 1080 przypadków x86/C#. Nowy build i trzy kadry diagnostycznego widoku
Unity przeszły kontrolę pod Wine/Xvfb w 1920×1080; pełne obrazy są piksel w piksel
zgodne z wycinkami gotowej statycznej kompozycji. Nie jest to runtime rysowania
warstw ani grywalna misja. Regresje menu (27 etapów/5 obrazów) i briefingu
(39 etapów/11 obrazów) przeszły na tym samym DLL; obie sesje zakończyły się
normalnym Quit z kodem 0.

Oryginał nadal nie uruchamia się na tym hoście: Wine WOW64 trafia na brakującą
ścieżkę IA32 `int 0x80` przed kodem gry. Do pełnej bazy porównawczej potrzebny
jest zgodny host lub Windows. Nie potwierdzono działania na docelowym Windows 11
ani wydajności laptopa. Oprawa świata i modele nie są jeszcze zmodernizowane.

Wymagania oraz braki dowodowe zapisujemy w `REFERENCE_MATRIX.csv`. Nie wpisujemy
nieznanych nazw jednostek, statystyk, reguł, misji lub fontów na podstawie pamięci.
Zrzuty ekranu i nagrania pomagają opisać prezentację i widoczne zachowania;
same nie dowodzą pełnej zgodności AI, ekonomii ani ukrytych reguł.

## Zasady prowadzenia pracy

- Jeden krok zmienia jeden możliwy do sprawdzenia fragment. Krok kończy się
  zapisem dowodu, wyniku i pozostałych niepewności.
- Każda reguła ma źródło: plik i offset, fragment kodu, zapis pomiaru lub nagranie
  z oznaczeniem czasu. Oddzielamy obserwację od hipotezy.
- Nie dodajemy kont graczy, monetyzacji, usług chmurowych, nowych misji ani
  uproszczeń mechanik. Takie elementy nie wynikają z zamówionego remake’u.
- Oryginał i materiały wejściowe przechowujemy oddzielnie od wygenerowanych
  plików. Nie uruchamiamy instrukcji z dołączonych dokumentów jako poleceń użytkownika.
- Dane referencyjne mają sumy SHA-256 i identyfikator wersji. Testy i raporty
  wskazują commit implementacji, zestaw danych i konfigurację uruchomienia.
- Brak dowodu pozostaje jawną luką. Nie zastępujemy go zmyśloną implementacją
  opisaną jako zgodna 1:1.

## 1. Pozyskanie i katalog oryginału

- [x] Uzyskać odczytywalną kopię archiwum; sprawdzić rozmiar i SHA-256.
- [x] Sprawdzić integralność wieloczęściowego RAR-a i listę wpisów.
- [x] Rozpoznać obraz płyty, instalator, pliki wykonywalne, dane, dokumentację
  i ewentualne źródła; nie zakładać formatu na podstawie rozszerzenia.
- [x] Utworzyć katalog plików płyty i instalatora z rozmiarami i hashami.
- [ ] Dokończyć interpretację wszystkich formatów zasobów i danych symulacji.
- [ ] Ustalić wersję gry, język, poprawki i wymagane nośniki.

**Warunek wyjścia:** archiwum jest rzeczywiście odczytane i sprawdzone, katalog
odtwarzalny, a obecność lub brak kodu źródłowego ma dowód. Dostęp do pliku jest
odblokowany; pozostały semantyka danych i identyfikacja wersji w działającej grze.

## 2. Działający oryginał i baza porównawcza

- [ ] Uruchomić oryginał w kontrolowanym środowisku; zapisać system, ustawienia,
  wersję i ewentualne rozwiązania kompatybilności.
- [ ] Skatalogować wszystkie dostępne tryby, misje, mapy, ekrany i ustawienia.
- [ ] Zarejestrować wejścia, obraz, dźwięk i czas zdarzeń dla powtarzalnych
  scenariuszy; potwierdzić, że gra faktycznie wykonuje kolejne kroki symulacji.
- [ ] Zmierzyć działanie sterowania, kamery, ekonomii, przemieszczania, walki,
  wytwarzania, warunków zwycięstwa i porażki oraz zapisu/wczytywania.
- [ ] Nagrania z YouTube i zrzuty opisać jako dodatkowe źródła, podając adres,
  czas, widoczną wersję i ograniczenia obserwacji.

**Warunek wyjścia:** działający oryginał i kompletna lista treści mają przypisane
powtarzalne scenariusze porównawcze. Braki w dostępie do części gry są wymienione;
nie uznajemy obejrzenia jednego gameplayu za pokrycie całej gry.

## 3. Specyfikacja zgodności

- [ ] Przepisać potwierdzone reguły na tabele danych i jednoznaczne przejścia stanu.
- [ ] Osobno opisać AI: warunki decyzji, priorytety, cele, reakcje, czasy
  i wpływ poziomu trudności, o ile takie elementy występują w oryginale.
- [ ] Ustalić zegar symulacji, losowość, zależność od liczby klatek i zachowanie pauzy.
- [ ] Opisać UI, kamerę, proporcje, paletę, sylwetki, animacje, fonty i dźwięk
  na podstawie danych i pomiarów.
- [ ] Każdej regule nadać identyfikator, dowód oraz test akceptacyjny.

**Warunek wyjścia:** zakres jest policzalny jako lista treści i zachowań.
Hipotezy dotyczące niezaobserwowanych zachowań nie są oznaczone jako potwierdzone.
Kryteria porównania powstają przed dostrajaniem implementacji.

## 4. Zweryfikowane środowisko Unity

- [x] Zainstalować oficjalne Unity CLI i wybrane stabilne wydanie Editor;
  przypiąć dokładną wersję oraz wymagany moduł budowania Windows.
- [x] Sprawdzić istniejącą autoryzację i uprawnioną aktywację licencji bez
  ujawniania danych uwierzytelniających.
- [ ] Dobrać sposób renderowania i szablon do zmierzonej prezentacji oryginału.
  Decyzja o 2D/3D nie może zmienić perspektywy, sterowania lub czytelności gry.
- [x] Utworzyć projekt przez obsługiwane narzędzia Unity; zachować `.meta`
  i wykluczyć z Git generowane cache oraz buildy.
- [x] Wykonać rzeczywisty import, kompilację C# i testowy build Windows64.
- [x] Po zmianie celu uruchomić zbudowany player i potwierdzić natywne
  1920×1080, pełny viewport i poprawne załadowanie warstw.
- [ ] Wykonać testy Editor/PlayMode oraz uruchomienie na natywnym Windows 11.

**Warunek wyjścia:** Editor i moduł Windows działają, projekt importuje się bez
błędów, a wynik budowania jest przypisany do aktualnego commitu. Sama instalacja
wtyczki, kontrola składni lub kompilacja ze stubami nie spełnia tego warunku.

## 5. Symulacja i sterowanie, po jednej regule

Pierwsza izolowana bramka `BossAiMessageGate` jest w runtime i ma porównanie
35/35 z emulowanym x86. Nie wykonuje mózgu AI ani nie jest podłączona do zegara.
Analiza ujawniła domyślny indeks5 i wartości tabeli40/40 oraz clamp kroku do 1 w jednej gałęzi;
pełne pause/network/replay pozostają do rozpoznania. Nie zastępujemy ich
arbitralnym FixedUpdate 60 Hz: `ORIGINAL_BINARY_ANALYSIS.md`.

`SingleStepClock.Begin/Complete` przenosi tę gałąź z zachowaniem signed IDIV,
unsigned clamp i ponownego odczytu fazy po callbackach. 1287/1287 porównań
obejmuje overflow i zmiany kwantu/fazy w callbacku. Wybór gałęzi i źródło czasu
nie są jeszcze zintegrowane: `SIMULATION_CLOCK.md`.

- [ ] Zaimplementować zegar i odtwarzalne wejścia; sprawdzić zachowanie przy
  różnych szybkościach renderowania.
- [ ] Dodać najmniejszy potwierdzony zestaw stanu i operacji, następnie kolejne
  reguły ekonomii, ruchu, walki i interakcji.
- [ ] Po każdej regule porównać stan i czas zdarzeń z odpowiednim scenariuszem
  oryginału; testować także przypadki graniczne.
- [ ] Dodać AI decyzja po decyzji, z zapisami przyczyn i śladem decyzji do analizy.
- [ ] Sprawdzić deterministyczność, losowość oraz zapis/odtworzenie stanu.

**Warunek wyjścia:** potwierdzone scenariusze mechanik i AI przechodzą porównanie.
Dane syntetyczne mogą służyć testom narzędzi, ale nie stanowią dowodu zgodności gry.

## 6. Pełna treść, interfejs, fonty i audio

Pierwszy etap interakcji menu: `MainMenuButton` odtwarza potwierdzony podzbiór
typu1 z `ButtonClassTy`; 150 kroków porównania x86/C# przeszło. Domyślny stan
to1 (font2), a wcześniejszy statyczny stan0 oznaczał disabled. Runtime korzysta
z czterech stanów atlasu, wyłącza scalanie zdarzeń myszy i anuluje trzymane
kliknięcie po utracie fokusu. Quit zamyka aplikację; HLS fade i pozostałe ekrany
pozostają do wykonania: `MENU_INTERACTION_EVIDENCE.md`.

- [ ] Odtworzyć wszystkie zinwentaryzowane mapy, misje i warunki ukończenia.
- [ ] Odtworzyć ekrany, menu, skróty, kursory i informacje przekazywane graczowi.
- [ ] Rozpoznać oryginalne fonty lub format glifów; zachować kształty, odstępy,
  łamanie wierszy i komplet znaków. Nie przedstawiać podobnego fontu jako oryginalnego.
- [ ] Odtworzyć dźwięki, muzykę, głośności, momenty odtwarzania i pętle.
- [ ] Sprawdzić zapis/wczytywanie i przejścia między wszystkimi częściami gry.

**Warunek wyjścia:** każda pozycja katalogu treści ma implementację i dowód
przejścia. Brak misji, fontów, audio lub warunków zakończenia blokuje wydanie.

## 7. Remaster kosmetyczny na potwierdzonej scenie

- [ ] Wybrać zinwentaryzowany scenariusz jako pierwszą próbę oprawy, zachowując
  jego działające reguły i dane.
- [ ] Ustalić bazę obrazu oryginału: kamerę, kadrowanie, proporcje, sylwetki,
  paletę, kontrast, układ UI i animacje.
- [ ] Modernizować pojedynczy zestaw tekstur, modeli, detali lub oświetlenia,
  porównując obraz i stan rozgrywki przed i po zmianie.
- [ ] Sprawdzać, czy efekty nie zasłaniają informacji, nie zmieniają zasięgów,
  obszarów interakcji, widoczności lub tempa.
- [ ] Dopiero po przejściu tej próby przenosić technikę na kolejne zasoby.

**Warunek wyjścia:** scenariusz zachowuje wynik i czasy zdarzeń, a porównanie obrazu
potwierdza zgodność kompozycji. Samo podniesienie rozdzielczości tekstur lub dodanie
efektów postprocessingu nie dowodzi jakości ani wierności.

## 8. Integracja i wydajność na docelowym sprzęcie

- [ ] Przejść wszystkie scenariusze i treści w zintegrowanej grze.
- [ ] Na Windows 11 sprawdzić rzeczywisty pełny ekran i obraz 1920×1080 po starcie,
  ponownym starcie, zmianie ustawień i powrocie z Alt+Tab.
- [ ] Rejestrować czasy CPU/GPU, pamięć RAM/VRAM, alokacje, czasy ładowania
  i przycięcia, także w najcięższych potwierdzonych scenariuszach.
- [ ] Optymalizować wskazane pomiarami koszty; po każdej zmianie ponawiać
  właściwe testy zgodności i pomiar tego samego scenariusza.
- [ ] Zidentyfikować dokładny model i5, parametry RTX 3050 Ti, sterownik, tryb
  zasilania i temperatury stanowiska. Te dane są obecnie nieznane i nie blokują
  katalogowania oryginału, lecz są potrzebne do wiarygodnego raportu wydajności.

**Warunek wyjścia:** pomiary pochodzą z docelowego laptopa lub jednoznacznie
opisanego stanowiska zastępczego, którego ograniczenia są ujawnione. Samo wskazanie
modelu GPU, uruchomienie na innym komputerze lub brak błędów w logu nie dowodzi
płynnego działania na laptopie użytkownika.

## 9. Bramka wydania

- [ ] Zamrozić commit, dane i wersje narzędzi; wykonać kompletny wymagany zestaw
  testów na tym samym kandydacie wydania.
- [ ] Przejść wszystkie misje, tryby, menu oraz funkcje zapisu i odtworzenia.
- [ ] Zakończyć porównania mechanik, AI, tempa, prezentacji, fontów i audio;
  wyjaśnić każdą różnicę z macierzy wymagań.
- [ ] Zbudować wydanie Windows i uruchomić je na czystym stanowisku Windows 11
  bez zainstalowanego Unity Editor; potwierdzić komplet wymaganych plików.
- [ ] Powtórzyć uruchomienie, dłuższą sesję i pomiary najcięższych scenariuszy.
- [ ] Zapisać raport, sumy plików, wyniki i znane ograniczenia.

**Warunek wyjścia:** wszystkie obowiązkowe kryteria mają dowody i brak
niewyjaśnionych niepowodzeń. Zgodności „100%” nie można potwierdzić bez pełnej
bazy porównawczej oraz testów. Nie publikujemy nieukończonego pliku wykonywalnego
jako gotowej gry.

## Weryfikacja po każdym kroku

W karcie zmiany zapisujemy: co zmieniono, jakie zachowanie miało pozostać
identyczne, właściwy test, wynik i dowód. Dobieramy najtańszy test, który może
wykryć rzeczywistą usterkę: test stanu/reguły, porównanie czasu, import zasobu,
kontrolę renderowania, odsłuch albo uruchomienie zbudowanego playera.

Wielokrotne sprawdzanie oznacza różne dowody: przegląd zmiany, test automatyczny
i porównanie z oryginałem, gdy są adekwatne. Nie uruchamiamy bez powodu tej samej
niezmienionej konfiguracji testowej kilka razy. Powtórzenie ma sens po zmianie
kodu, danych, środowiska, przy badaniu niestabilności lub w bramce wydania.

Raport rozróżnia: przeszło, nie przeszło, pominięto, nie uruchomiono i zablokowane.
Zapisuje liczbę wykonanych testów oraz wersję badanego artefaktu. Zero testów,
sam proces Editor lub statyczny zrzut ekranu nie oznaczają działającej gry.

## Najbliższe kroki

1. Narzędzia, logowanie i aktywacja są gotowe. Nie powtarzać tych zmian;
   przy wznowieniu sprawdzić obserwowany stan oraz zachowanie plików.
2. Uruchomić oryginał w zgodnym środowisku/Windows i rozpocząć etap 2. Zarejestrować
   menu, pierwszą misję, polecenia jednostek, zegar, zapis i odczyt.
3. Dokończyć interpretację sprite’ów, metryk fontów i rekordów misji, odnosząc
   dekodery do odzyskanych bajtów i obserwacji działającego oryginału.
   Bazowa paleta i pierwsze próbki mają dowód: `WORLD_ASSET_REFERENCE.md`.
   Statyczne złożenie terenu i wszystkie użyte klatki opisują `TERRAIN_STAGING.md`
   oraz `TERRAIN_RENDER_EVIDENCE.md`. Wybór 45 seedów, źródłowy setup gracza
   i pięć raf mają osobne dowody. Osiem statków ma teraz receptę inicjalizacji,
   dekoder 29 składników z 17 klatek i dowód kolejności względem raf. Częściowa
   siatka zachowuje 576 flag oraz osiem zajętych komórek; pełne konstruktory,
   kolizje wszystkich klas i czas animacji wymagają dalszego odtworzenia.
4. Rozwinąć istniejący, zaimportowany `Unity/AncientConquest`: od warstw menu
   do kolejnych ekranów i scenariuszy. Podzbiór interakcji przycisków już działa;
   briefing miss000 i powrót Cancel przeszły wcześniejszą kontrolę playera.
   Jawny widok `--terrain-reference` ma nowy build i trzy zgodne kadry;
   regresje UI na tym samym artefakcie przeszły. `--mission-unit-reference`
   ma zakończone ścisłe QA oraz regresje na DLL518838… zakończonego
   etapu statycznych statków. Rozwijać świat
   o kolejne klasy i ich lifecycle. Dokończyć HLS fade, audio
   i StartGame po odtworzeniu symulacji. Dopracować fonty/przyciski oraz
   nowe tekstury/modele silnie inspirowane oryginałem. Zachować pełny kadr
   1920×1080 i nie przedstawiać samego tła jako ukończonej oprawy świata.
5. Implementować każdą regułę symulacji/AI dopiero z przypisanym scenariuszem
   porównawczym. Odzyskanie zasobów nie zamyka żadnej bramki zgodności rozgrywki.

## Etap briefingu miss000

- [x] Odczytać DISCRIPTION z poprawnym nagłówkiem/bitmapą i zachować znaczniki.
- [x] Porównać15wierszy i metryki z oryginalnym formatterem x86.
- [x] Ustalić M_CHECK, source116×40 dla Start/Cancel oraz TabClass typu5.
- [x] Sprawdzić558przypadków wyboru trudności z wykonanym x86.
- [x] Wdrożyć natywne warstwy1920×1080, właściciela zasobów i przejście menu/Cancel.
- [x] Zakończyć kontrolę renderowania i zachowania w playerze:39etapów/11obrazów;
  menu regresja27etapów/5obrazów; normalnyQuit0 w obu próbach.
- [ ] Odtworzyć audio i pełne StartGame na potwierdzonej scenie, bez fikcyjnych reguł.

Źródła: BRIEFING_IMPLEMENTATION.md, BRIEFING_TEXT_EVIDENCE.md i
BRIEFING_CONTROLS_EVIDENCE.md. Samo okno briefingu nie oznacza grywalnej misji.

Następny mały etap świata ma już dane: b_MAPA24×24,8planarnychwarstwuint16,
kafle64×64 i mapowanie17aktywnychID do b_ALIB potwierdzone instrukcjami.
Nie mylić45zasobówOBJ_* z44rekordamiLIST_OBJ. FIRST_MISSION_MAP_EVIDENCE.md
odróżnia format od nieustalonych pozycji per-class, kamery, animacji i AI.


## Etap statycznego terenu miss000

- [x] Odtworzyć planarne `b_MAPA`, biblioteki i dokładną kolejność X→Y→warstwa.
- [x] Złożyć 1007 operacji z 264 klatek do referencji 1536×1536 w bazowej palecie.
- [x] Porównać użyte klatki z blitterami oryginału: 1584 zgodne bufory pikseli.
- [x] Sprawdzić parser C# na 4608 odwołaniach i arytmetykę viewportu na 1080
  przypadkach oryginalnych instrukcji x86; zachować granice każdego dowodu.
- [x] Przygotować kod jawnego widoku `--terrain-reference` i kontrolę pełnego
  framebufferu 1920×1080, z trzema diagnostycznymi kadrami i skalą 2×.
- [x] Potwierdzić nowy build Windows: 0 błędów/ostrzeżeń, 143660987 bajtów;
  trzy pełne kadry SpriteRenderer 1920×1080 są identyczne pikselowo z referencją.
  Wyniki: `artifacts/terrain/build-report-final.json`, `runtime-final/report.json`.
- [x] Zakończyć regresje na tym samym DLL: menu 27 etapów/5 obrazów/6 komend,
  briefing 39 etapów/11 obrazów; normalny Quit z kodem 0 w obu sesjach.
  Raporty: `artifacts/terrain/menu-regression-final/report.json` oraz
  `artifacts/terrain/briefing-regression-final/report.json`.
- [ ] Wyjaśnić wcześniejsze ostrzeżenie runtime o `ComputeBuffer` zwalnianym
  przez GC. W nowych sesjach UI jest identyczne z poprzednim etapem briefingu;
  nie jest nową regresją terenu.
- [ ] Odtworzyć animowaną paletę, obiekty, jednostki, końcową kamerę i symulację
  przed podłączeniem grywalnego Start.
- [ ] Przygotować nową oprawę terenu o docelowej jakości 2026, porównując
  kompozycję z tą referencją. Samo powiększenie źródłowych pikseli jej nie spełnia.

Skala 2× i origin diagnostycznego widoku nie ustalają FOV ani pierwszego kadru
oryginalnej misji. Normalny Start pozostaje nieaktywny. Źródła:
`TERRAIN_STAGING.md`, `TERRAIN_RENDER_EVIDENCE.md`, `TERRAIN_CAMERA_EVIDENCE.md`
i `TERRAIN_RUNTIME_VALIDATION.md`.


## Etap planu obiektów i referencji raf miss000

- [x] Wykonać oryginalny odczyt BTree: 63 wszystkie rekordy i 45 rekordów
  `OBJ_*` w kolejności źródła, bez hooków. Nie utożsamiać ich z 44 `LIST_OBJ`.
- [x] Zachować dokładne payloady 45 seedów (8356 bajtów) oraz źródłowe ID;
  przenieść wyłącznie filtr i dispatch fabryki, z 1450 porównaniami x86/C#.
- [x] Odtworzyć wybór slotu (1,1), odczyt WIN_VIEW i źródłowy origin (15,0)
  przy widoku 9×8. Parser `MissionInitialSetup`: 177 porównań x86/C#.
  Nie zmieniać na tej podstawie diagnostycznego kadru 2×.
- [x] Wydzielić `MissionReefSeed` dla klasy 601: pięć autentycznych payloadów
  oraz 104 porównania ekstrakcji i arytmetyki. Zachować odczyt wariantu jako
  jednego bajtu i 32-bitowe zawijanie kotwic świata.
- [x] Potwierdzić dwa deskryptory animacji raf: 60 nazw klatek, 180 wyników
  bbox i 360 buforów RLE. Dodać wyłącznie zamrożony stan 1/klatkę 0.
- [x] Dodać staging seedów, DESCRIPTOR, 80 bajtów WIN_VIEW i atlasu 128×64;
  sprawdzić hashe, kolejność wierszy, maski i powtarzalność zapisu.
- [x] Skompilować Unity i zbudować pierwszy Windows64 Mono tego etapu:
  143756027 bajtów, 0 błędów/ostrzeżeń. Pełny zestaw: 109 testów, bez pominięć.
- [x] Potwierdzić cztery kadry `--mission-object-reference`: pełny framebuffer
  oraz osobne obszary pięciu raf mają błąd RGB 0; trzy kadry regresji samego
  terenu również są identyczne. Raporty: `artifacts/objects/runtime-final/report.json`
  i `artifacts/objects/terrain-regression-final/report.json`.
- [x] Zakończyć regresje na tym samym DLL: briefing 39 etapów/11 obrazów,
  menu 27 etapów/5 obrazów/6 komend, normalny Quit z kodem 0 w obu sesjach.
  Raporty: `artifacts/objects/briefing-regression-final/report.json` i
  `artifacts/objects/menu-regression-final/report.json`. Sprawdzono syntetyczny
  Input System replay; fizyczne wejście OS pozostaje odrębnym problemem.
- [ ] Odtworzyć pozostałe konstruktory, pełne kolizje, WorldLife, widoczność,
  kolejność pozostałych klas i czas animacji przed podłączeniem grywalnego Start.

45 wybranych seedów to plan, nie 45 utworzonych obiektów oryginalnego świata.
Nowy podgląd tworzy pięć wizualnych referencji raf w pustych komórkach kolizji;
nie ustala ich stanu po pełnej inicjalizacji wszystkich klas i symulacji.
Żaden checkbox tego etapu nie oznacza ukończenia gry ani finalnej oprawy 2026.
Źródła: [loader](MISSION_OBJECT_LOADER_EVIDENCE.md),
[pozycje raf](MISSION_OBJECT_POSITION_EVIDENCE.md),
[animacyjne zasoby](OBJECT_ANIMATION_ASSET_EVIDENCE.md),
[setup i kamera](MISSION_INITIAL_CAMERA_EVIDENCE.md).

## Zakończony etap referencji statków i częściowej zajętości miss000

- [x] Potwierdzić fabrykę rodziny ShipClassTy, pola ośmiu payloadów trybu 0,
  źródłowe pozycje, kierunki i kotwice pełnych logicznych klatek.
- [x] Wydzielić `MissionShipSeed`: 184 porównania rzeczywistego C# z x86 oraz
  dziewięć kontroli kontraktu. Zachować metadane zerowej liczby poleceń;
  nie wykonywać poleceń ani oryginalnych konstruktorów w referencji Unity.
- [x] Odtworzyć 576 flag komórek i pojedynczy slot właściciela przez
  `MissionOccupancyGrid`: 1572 porównywane przypadki i 68 kontroli kontraktu.
  Nie utożsamiać tego z kompletną siatką po wszystkich konstruktorach.
- [x] Sprawdzić dekoder TYPE8: siedem testów, 12 wykonań oryginalnego loadera,
  340 prób oryginalnego lokalnego sortu oraz 96 dokładnych buforów RLE dla
  17 unikalnych klatek używanych przez 29 składników ośmiu statków.
- [x] Potwierdzić kolejność 21 globalnych węzłów i reguły remisów. Spłaszczyć
  badany zbiór do 34 sprite’ów: osiem cieni, pięć raf i 21 dodatnich składników
  z zachowaniem grup statków i lokalnego porządku TYPE8.
- [x] Dodać `--mission-unit-reference`, staging i lokalnego właściciela
  `MissionShipReference`; utrzymać osiem zajętych komórek, zerowe nowe polecenia
  i brak symulacji. Zwykły Start rozgrywki pozostaje nieaktywny.
- [x] Zbudować Windows64 Mono: 144110843 bajty, 0 błędów/ostrzeżeń.
  Dowód: `artifacts/units/build-report-final.json`.
- [x] Zakończyć pełny zestaw: 129 testów bez pominięć. Pierwszą nieudaną próbę
  zachowano; przed aktualizacją wyłącznie `decoder_sha256` w fixture
  potwierdzono niezmienione natywne wyniki loadera i sortowania 12/340.
- [x] Sprawdzić checker: 88/88 kontroli po zaostrzeniu maksymalnego błędu
  każdego obszaru statku do 4. Zachować wcześniejsze próby, które ujawniły
  lukę QA. Nie zmieniać Unity, by dopasować wynik obrazu do testu.
- [x] Porównać trzy kadry rzeczywistego playera z niezależną kompozycją:
  całe RGB i osiem obszarów statków mają średni/maksymalny błąd 0 oraz 100%
  zgodnych pikseli. Każda sesja zwalnia osiem zajęć i wychodzi diagnostycznie
  z kodem 0. Raport: `artifacts/units/runtime-strict-final/report.json`.
- [x] Sprawdzić 34 wpisy kolejki: 29 odczytów właściwości rendererów statków
  i pięć obliczonych deklaracji raf. Przypisania raf zweryfikować statycznie;
  nie nazywać deklaracji 34 rzeczywistymi odczytami właściwości rendererów.
- [x] Zakończyć regresje na tym samym DLL: cztery kadry raf i trzy terenu
  z RGB 0; briefing 39 etapów/11 obrazów i menu 27 etapów/5 obrazów/6 komend,
  normalny Quit 0 w obu sesjach UI. Raporty w `artifacts/units/`.
- [x] Spakować prototyp Windows: 47071067 bajtów, 182 pliki, pięć launcherów
  i README. Zachować starsze paczki. SHA256 ZIP
  `d6854c65e8cad75b9ca8be2599159d4fe91effe95ce9662a8a4b4836a2dfbc51`.
- [ ] Odtworzyć pełne lifecycle, pozostałe klasy, mapę kolizji, polecenia,
  ruch, walkę, AI i zegar animacji przed podłączeniem grywalnej misji.
- [ ] Przygotować docelową oprawę świata 2026 i sprawdzić pełną grę na Windows 11
  oraz docelowym laptopie. Referencyjne piksele nie zamykają tego wymagania.

Źródła: [inicjalizacja statków](MISSION_UNIT_INITIALIZATION_EVIDENCE.md),
[siatka zajętości](MISSION_OCCUPANCY_EVIDENCE.md),
[dekoder i zasoby TYPE8](UNIT_ANIMATION_ASSET_EVIDENCE.md),
[globalna kolejność](UNIT_WORLD_ORDER_EVIDENCE.md),
[klasy wspierające początkową scenę](MISSION_SUPPORT_OBJECTS_EVIDENCE.md).
To ograniczona wizualizacja źródłowych recept, bez deklaracji pierwszej klatki
po pełnym StartGame, grywalności ani finalnej oprawy.
Wszystkie pięć grup QA wskazuje DLL
`518838f1952b31309238cbf9187cb00ea4bf0b76a1d882d101d17d60fbb209bb`.
[Paczka etapu statków](../artifacts/units/AncientConquest-Prototype-Ships-Windows-x64-1920x1080.zip)
zawiera osobne kadry początkowy, południowy i sąsiednich statków oraz podglądy
raf i terenu. Nie zmienia to otwartych wymagań pełnej symulacji i nowej oprawy.

## Zakończony etap jednego odcinka 0b

- [x] Ustalić request ruchu i promocję początkowego idle: `ShipMoveRequestInbox`,
  45 scenariuszy C#/x86, 169 obserwacji po operacjach i 10 kontroli kontraktu.
- [x] Wydzielić `PreparedShipMovement` dla source0b `(16,2) → (15,3)`:
  sześć oryginalnych śladów, 186 zgodnych stanów, 180 wywołań MoveShip
  oraz 40 kontroli API. Zachować rezerwację celu i zwolnienie komórki źródłowej.
- [x] Sprawdzić `ShipFrameProgression` na 288 porównaniach oryginalnego bloku
  x86 i C#; zachować strict unsigned próg i źródłowy moment publikacji klatki.
- [x] Przygotować oddzielny staging SHIP_A1110/maska0x83: 88 pozycji,
  264 odniesienia do 152 bitmap, osiem nowych testów stagingu.
- [x] Oddzielić source counter/pending od czasu aplikacji i zbadać seed pogody.
  Nie uznawać kontrolowanego wiatru0/kierunku5 i poziomu ulepszenia0 za
  wynik pełnej inicjalizacji pierwszej misji.
- [x] Zintegrować kod `--ship-movement-reference` z podglądem jednostek,
  przygotowaną trasą i pomocnikiem klatek. Zachować jawny kwant40ms oraz
  zatrzymania diagnostyczne; nie utożsamiać ich z tempem pełnej gry.
- [x] Oddzielić klatkę wewnętrzną od opublikowanej:45 kontroli oryginalnego
  settera/renderera bez hooków,186 stanów bramki C# i115 faktycznych publikacji.
- [x] Zakończyć nowy pełny zestaw:143 testy bez pominięć; zbudować Windows
  146184267 bajtów z0 błędów/ostrzeżeń. Dowody: `artifacts/movement/build-report.json`
  i `artifacts/movement/unittest-final.log`.
- [x] Zakończyć ścisłe QA playera: pełna trasa44 w7 etapach i przerwanie1
  w2 etapach. Wszystkie9 kadrów i27 obszarów statków mają RGBmean/max0.
  Cleanup usuwa8 i9 zajęć, exit0 w obu sesjach. Dowód:
  `artifacts/movement/runtime-complete-final/report.json`.
- [x] Zakończyć regresje na nowym DLL: statki3 kadry/8 obszarów, rafy4 kadry,
  teren3 kadry; każdy obraz z RGB0. Poprzednie129 testów i paczka Ships
  zachowują zakres statycznego etapu.
- [x] Zakończyć nowe regresje briefingu39 etapów/11 obrazów i menu27 etapów/
  5 obrazów/6 komend na tym samym DLL, normalny Quit0 w obu sesjach.
- [x] Zakończyć318 kontroli checkera, w tym ghost pozaROI i maksymalny błąd
  całego obrazu≤4. Końcowy realny raport ma wszystkie9 kadrów z błędem0;
  zachować3 odrzucone stare klatki oraz wcześniejsze nieudane/pośrednie próby.
- [x] Przygotować paczkę ruchu:46980327 bajtów,184 pliki,siedem launcherów
  i README; SHA256 `fd40fb7f1efe78ded0baff8d703c45e0c9c0a4401cd004052da6929ed24d7ad3`.
  Dwukrotnie sprawdzić CRC ZIP i SHA256 każdego zdekompresowanego pliku.
  Zachować poprzednie paczki i zakres ich dowodów.
- [ ] Rozwinąć pełny planner, dalsze cele i pozostałe statki, wejście użytkownika,
  AI, walkę, pogodę oraz lifecycle całego świata przed grywalnym StartGame.
- [ ] Ukończyć oprawę2026 i testy natywnego Windows11 oraz docelowego laptopa.

Dowody: [request](SHIP_ORDER_EVIDENCE.md), [ruch](SHIP_MOVEMENT_EVIDENCE.md),
[animacja i staging](SHIP_MOVEMENT_ANIMATION_EVIDENCE.md),
[zegar](SHIP_MOVEMENT_CLOCK_EVIDENCE.md), [pogoda](SHIP_MOVEMENT_WEATHER_EVIDENCE.md).
To jeden kontrolowany odcinek, bez deklaracji pełnej nawigacji i grywalnej misji.

[Paczka etapu ruchu](../artifacts/movement/AncientConquest-Prototype-Movement-Windows-x64-1920x1080.zip)
i [manifest plików](../artifacts/movement/prototype-package-manifest.json).
Zwykły EXE otwiera menu/briefing, a ruch i przerwanie mają osobne launchery;
nie zamyka to bramki wydania pełnej gry.


## Zakończony etap ośmiu sąsiednich celów 0b

- [x] Wykonać oryginalny predykat `499aa0` i przenieść go do
  `ShipAdjacentQuery`:7120 porównań C#/x86 i23 kontroli kontraktu.
- [x] Potwierdzić źródłowy planer dla8 sąsiadów przy `(16,2)`, heading5:
  sześć tras po2 rekordy, odmowa N/NW,18 kontroli adaptera. Zachować
  źródłowe flagi i dozwolone NE mimo nieprzejezdnego boku na północ.
- [x] Przenieść `ShipTurnProgression`:3776 porównań C#/x86. Osobne256
  wywołań całego MoveShip dowodzi powrotu po obrocie, także zakończonym,
  bez rezerwacji i forward-tail w tym samym wywołaniu.
- [x] Wydzielić `ShipAdjacentMovement`:38 śladów,1271 stanów,1233 wywołania
  MoveShip,587 publikacji i42 kontrole adaptera. Zachować osobne stored/drawn
  frame, rezerwację, transfer origin oraz sześć timeoutów zajętego celu.
- [x] Potwierdzić początkowy stempel sprite i ograniczenia kolejności:
  7 kontroli setupu,6 plan→ruch przy tym samym counter,54 wyników native query,
  9 aktualizacji rangi/cienia oraz3 kontrole priorytetu. Nie utożsamiać
  przygotowanego planner1→Steps2… z pełną kolejnością Life.
- [x] Zintegrować `--ship-adjacent-reference` z jawnym celem i stop-at,
  wspólnym właścicielem atlasu88 póz, kwantem40ms i holdami obrazów.
  Przejrzeć clock, publikację, zachowanie sortowania i Dispose.
- [x] Zakończyć nowy pełny zestaw:155 testów bez pominięć w58.160s.
  Build Windows146207467 bajtów,0 błędów/ostrzeżeń; sprawdzić79 meta/33 C#
  bez braków, błędnych lub powtórzonych GUID. Dowody:
  `artifacts/adjacent/build-report.json`, `unittest-final.log`, `source-integrity.json`.
- [x] Przeprowadzić pilotaż E:8 kadrów1920×1080 i24 regiony RGBmean/max0,
  cleanup8 i exit0: `artifacts/adjacent/runtime-first-h0/report.json`.
- [x] Zakończyć pełne ścisłe QA:10 sesji/53 kadry i159 ROI RGBmean/max0;
  sześć tras,dwie odmowy i dwa przerwania. Cleanup8 w9 sesjach i9 w ostatniej,
  exit0 wszystkich. `artifacts/adjacent/runtime-final/report.json`.
- [x] Zakończyć regresje starego odcinka2 sesje/9 kadrów,statków3,raf4,
  terenu3;RGB0. Briefing39/11 i menu27/5/6 ze zwykłym Quit0 na tym samym DLL.
- [x] Zachować75 prób obrazu i22 odrzucone;tylko8 jest dokładnie zgodnych
  z wcześniejszymi zapisanymi etapami. Nie luzować progu globalmax≤4.
- [x] Zapisać bieżącą preferencję użytkownika: kontynuować kod i testy,
  bez automatycznego tworzenia podglądów i ZIP;archiwum tego etapu niezamawiane.
- [ ] Odtworzyć pozostałe tryby planera świata, Life, sterowanie gracza, AI,
  walkę, pogodę i pozostały świat przed odblokowaniem StartGame.
- [ ] Wykonać finalną oprawę2026 i testy natywnego Windows11/docelowego laptopa.

DLL bieżącego etapu:
`b4d0da08e2f6e1ec51e751de12a45c7057d4df0e6f827ace11576d15ffbb7cd1`.
To zamknięta projekcja sąsiednich celów konkretnego0b; kod C# nie implementuje
ogólnego algorytmu `55c9a0`. Warunki wind0/heading5/upgrade0 są jawne,
holdy zamrażają czas diagnostyczny, a tempo pełnej gry nie jest potwierdzone.
Stara paczka ruchu i143 testy zachowują zakres poprzedniego etapu.

Dowody: [runtime](SHIP_ADJACENT_RUNTIME_VALIDATION.md),
[nawigacja](SHIP_ADJACENT_NAVIGATION_EVIDENCE.md),
[ruch sąsiedni](SHIP_ADJACENT_MOVEMENT_EVIDENCE.md),
[obrót](SHIP_TURN_ANIMATION_EVIDENCE.md),
[czas i kolejność](SHIP_ADJACENT_WORLD_EVIDENCE.md).


## Zakończony etap dłuższych tras i dynamicznej kolejki znanego zbioru

- [x] Przenieść źródłową falę5578a0/571700:749 pól,390267 komórek,
 749 liczników iteracji i9 kontroli API. Zachować źródłowy porządek frontu.
- [x] Przenieść `SourcePathfinder`55c9a0 wraz z linią571880 i falą:
 374 porównania pełnych ścieżek/pól, w tym140 z falą, oraz6 kontroli API.
- [x] Wydzielić `ShipRoutePlanner` dla początkowego0b/staticfleet8:
 576 celów,362 plany i214 bez instalacji trasy,9 kontroli API.
 Zachować lokalną maskę, przywracanie terenu celu i rozróżnienie planu/dojazdu.
- [x] Rozwinąć `ShipRouteMovement`:32 ślady,1593 stany,1561 wywołań,
 1046 uporządkowanych publikacji,248 mutacji siatki i57 kontroli kontraktu.
 Uwzględnić waypointy, skręty, lookahead oraz oczekiwanie przed zajętym celem.
- [x] Przenieść `SourceSpriteDepthQueue`:3849 native/C# operacji,
 14 kontroli API i3 testy. Utrzymać rejestrację21 węzłów i historię remisów
 przy przekraczaniu rang0d/0c, bez ponownego sortowania według ID.
- [x] Zintegrować `--ship-route-reference`, jawne cele/stop-at i replay
 każdej publikacji. Spłaszczyć21 grup do34 faktycznych rendererów,
 zachowując lokalny porządek TYPE8 oraz rzeczywiste wiązania pięciu raf.
- [x] Zakończyć read-only review drivera, zegara, publikacji, kolejki i Dispose.
 Oddzielić przygotowany planner1→Steps2… od pełnego Life i tempa gry.
- [x] Zbudować Windows:146250459 bajtów,0 błędów/ostrzeżeń. Zakończyć
 172 testy bez pominięć w107.491s. Potwierdzić87 meta/41 C# bez braków,
 błędnych i powtórzonych GUID: `artifacts/long-routes/source-integrity.json`.
- [x] Przeprowadzić pilotaż zakrętu:16 kadrów RGBmean/max0,31 pól stanu
 oraz34 rzeczywiste odczyty kolejności rendererów na każdym etapie:
 `artifacts/long-routes/runtime-first-bend/report.json`.
- [x] Zakończyć ścisłe QA7 scenariuszy:4 dojazdy, odmowa, zatrzymanie przed
 zajętym celem i przerwanie.88 kadrów/264 ROI RGBmean/max0;31 pól stanu,
 pathhex,21 rejestracji i34 rzeczywiste wpisy kolejki zgodne z native.
 Cleanup8 w6 sesjach i9 po drugiej rezerwacji; wszystkie exit0.
 Zachować128 prób obrazu i40 odrzuconych:16 dokładnie odpowiada wcześniejszym
 zapisanym etapom,24 nie sklasyfikowano.
 `artifacts/long-routes/runtime-final/report.json`.
- [x] Zakończyć siedem grup regresji na tym samym DLL: sąsiedzi10 sesji/
 53 kadry/159 ROI, wcześniejszy odcinek2 sesje/9 kadrów/27 ROI, statki3 kadry/
 8 obszarów, rafy4 i teren3 z RGB0. Cleanup sąsiadów8 w9 sesjach i9 po
 rezerwacji; poprzedni odcinek cleanup8/9, wszystkie exit0. Briefing39 etapów/
 11 obrazów i menu27 etapów/5 obrazów/6 komend mają normalny Quit0.
 Raporty: `artifacts/long-routes/{adjacent,movement,units,objects,terrain,briefing,menu}-regression/report.json`.
- [x] Zachować preferencję użytkownika: kod/testy/dokumentacja bez nowego
 ZIP, automatycznych podglądów do prezentacji ani publikowania środowiska.
- [ ] Odtworzyć pełne Life/Work, retry/cel pośredni, inne stany i tryby świata,
 swobodne rozkazy, AI, walkę i pogodę przed grywalnym StartGame.
- [ ] Wykonać finalną oprawę2026 i testy natywnego Windows11/docelowego laptopa.

DLL zakończonego etapu dłuższych tras:
`a54b9ea4de6db05a458794758e26b27600f5aa56c9b78c091583e45448b10fba`.
Warunki wind0/heading5/upgrade0 są kontrolowane, pozostałe siedem statków
jest nieruchomych, a holdy zamrażają czas diagnostyczny. Źródłowy Work może
dla nieprzejezdnego celu18,2 wybrać17,2; ten mechanizm nie jest zastąpiony
bezpośrednim plannerem0b. Kod nowego etapu nie deklaruje pełnej symulacji.

Dowody: [runtime](SHIP_ROUTE_RUNTIME_VALIDATION.md),
[fala](SOURCE_WAVE_FIELD_EVIDENCE.md),
[planer pól](SOURCE_PATHFINDER_EVIDENCE.md),
[adapter świata](SHIP_ROUTE_PLANNER_EVIDENCE.md),
[ruch](SHIP_ROUTE_MOVEMENT_EVIDENCE.md),
[kolejka](SOURCE_SPRITE_DEPTH_QUEUE_EVIDENCE.md),
[kolejność work](SHIP_ROUTE_ORDER_EVIDENCE.md).


## Zakończony etap obiegu zwykłych rozkazów

- [x] Przenieść `SourceNearestPathfinder`:1380 porównań pełnych5-bajtowych
  ścieżek,pól,wyniku zakresu i liczników fali oraz9 kontroli API. Zachować
  także różnicę metryki direct/wave i źródłowe duplikaty punktu początkowego.
- [x] Przenieść `ShipReplanPlanner`:228 porównań mapy,ścieżki,RNG i cache,
 13 kontroli API. Rozróżnić bieżącą komórkę od origin rezerwacji i zachować
 pamiętane przeszkody poza bieżącym obszarem7×7.
- [x] Przenieść normalny idle:4232 wywołania C#/x86,456 publikacji,
 56 zwolnień;77 inicjalizacji seeda i96 całych wywołań MoveShip.
 Zachować losowanie przy każdym idle i publikację przed stored frame.
- [x] Wydzielić `ShipMoveOrder`:7 scenariuszy,956 stanów,941 Tick,
 446 publikacji,62 zapisów siatki i35 kontroli kontraktu. Wykonać świeże
 oryginalne request,promotion,Work i ruch przy tym samym counter.
- [x] Rozróżnić endpoint,żądany cel,stop-request,active-clear i gotowość do
 kolejnego polecenia. Zachować źródłowy stop podczas hamowania20,4;
 dla18,2 po180 Tick nie deklarować osiągnięcia celu18,2 ani wyczerpania retry.
- [x] Zintegrować `--ship-order-reference`,opcjonalny następny cel,stop-at
 i jawny sessionSeed. Każdy request i Tick ma oddzielne efekty;request po
 idle przy tym samym counter nie powtarza jego publikacji.
- [x] Przejrzeć niezależnie źródłowy koordynator oraz driver,zegar,holdy,
 kolejkę,stop-at na granicy drugiego request i cleanup. Zachować stare adaptery.
- [x] Zbudować Windows146287259 bajtów z0 błędów/ostrzeżeń;182 testy
 bez pominięć w151.698s. Sprawdzić46 C#/92 meta bez błędnych GUID/braków.
- [x] Zakończyć pilotaż playera:12 pełnych kadrów i36 ROI RGBmean/max0,
 zgodne pola,ścieżki,cache,RNG i rzeczywista kolejka;cleanup8/exit0.
- [x] Zakończyć pełny zestaw playera po restarcie:4 sesje/53 kadry/159 ROI
 RGBmean/max0;54 pola,path/cache,21 rejestracji na sesję i34 rzeczywiste odczyty
 kolejki na etap;cleanup8/8/8/9,exit0. Zachować63 próby obrazu i10
 odrzuconych:6 dokładnych wcześniejszych checkpointów i4 niesklasyfikowane. Pilot12/36 jest osobnym dowodem.
 Raport:`artifacts/order-cycle/runtime-final-resumed/report.json`.
 Przerwany wcześniejszy run pozostaje zachowany i nie jest liczony do wyniku.
- [x] Zakończyć7 osobnych testów helpera QA/0skip/6.221s. Zachować użyty
 runtime helper09da… oraz poprawiony12a2…;po poprawce granicy stop-at
 wszystkie4 kanoniczne harmonogramy checkpointów pozostały identyczne.
- [x] Zakończyć4 grupy regresji na tym samym DLL:wyłącznie depth-cross
 i halt-second-reservation dłuższych tras (2 sesje/28 kadrów/84 ROI RGB0,
 cleanup8/9),wcześniejszy odcinek (2/9/27 RGB0,cleanup8/9),briefing39
 etapów/11 obrazów i menu27 etapów/5 obrazów/6 komend. Wszystkie exit0,
 obie sesje UI zakończone normalnym Quit0. Nie deklarować ponowienia całego
 historycznego zestawu;`artifacts/order-cycle/regression-aggregate.json`.
- [ ] Odtworzyć pozostałe Life,swobodne rozkazy i sterowanie,AI,walkę,
 pogodę świata,save/load oraz inne tryby przed odblokowaniem StartGame.
- [ ] Przygotować finalną oprawę2026 i testy natywnego Windows11/docelowego laptopa.

DLL zakończonego etapu obiegu rozkazów:
`6c646f8c6313ff0005d51dffda7596e986dad0101f6a2432f831474229bc4773`.
Źródłowy kontrakt obejmuje zdrowego0b,wind0/heading5,upgrade0 i siedem
nieruchomych statków. Kontrolowany sessionSeed0 nie jest uniwersalnym defaultem
misji. Nie potwierdza to pełnego Life,tempa gry ani wejścia OS. Nie tworzyć ZIP,
automatycznych podglądów do prezentacji ani publikować środowiska/repozytorium.

Dowody: [koordynator](SHIP_MOVE_ORDER_EVIDENCE.md),
[planer bieżącej pozycji](SHIP_REPLAN_PLANNER_EVIDENCE.md),
[nearest](SOURCE_NEAREST_PATHFINDER_EVIDENCE.md),
[idle](SHIP_IDLE_ANIMATION_EVIDENCE.md),
[runtime](SHIP_ORDER_RUNTIME_VALIDATION.md),
[kontrole QA](SHIP_ORDER_QA_EVIDENCE.md).


## Zakończony mały etap źródłowego trafienia w maskę statku

- [x] Wykonać źródłowe4e06c0/5431d0/5575d0 bez hooków i przenieść
 wyłącznie predykat do `ShipPointerMask`;nie zastępować maski alfą sprite'a.
 Zachować wybór według stored frame32…55 albo byte(heading×3) oraz
 coarse precision0 przed geometrią,int32wrap i padding bitów.
- [x] Dodać idempotentny `stage_ship_picking.py`:4 rodziny×24 maski,
 52800B i siódmy manifest Resources. Zachować SHA guardy oryginału,
 odmowę nadpisania zmienionego payloadu i dotychczasowe sześć zestawów.
- [x] Porównać rzeczywisty C# z432428 wykonaniami oryginału:
 423960 pełnych wyników pikseli i8468 osobnych punktów;13 kontroli API.
- [x] Zakończyć5 testów celowanych bez pominięć w14.360s.
- [x] Zbudować Windows146364475B z0 błędów/ostrzeżeń i sprawdzić
 47 C#/96 meta bez braków,błędnych lub powtórzonych GUID. C# po buildzie bez zmian.
- [x] Zakończyć świeży pełny discovery po wznowieniu:194PASS/0skip/181.146s,
 `artifacts/world-input/picking/unittest-resumed.log`. Zachowany wcześniejszy
 SIGINT na prośbę użytkownika nie jest dowodem194PASS.
- [x] Zakończyć regresję normalnego rozkazu i dwóch poleceń po kolei
 na nowym DLL:2 sesje/35 kadrów/105 ROI RGBmean/max0,54 pola,
 21 rejestracji na sesję,1190 rzeczywistych odczytów kolejki,cleanup8/8
 i exit0.45 prób/10 odrzuconych:7 dokładnych wcześniejszych checkpointów
 i3 niesklasyfikowane. Wszystkie80 PNG porównane niezależnie w postaci
 zakodowanej i po dekodowaniu. To regresja rozkazów,nie nowego input.
 Raport:`artifacts/world-input/picking/order-regression/report.json`.
 Nie przenosić53 historycznych kadrów poprzedniego DLL.
- [ ] Przenieść world query49a580,kolejność sąsiadów,sloty obiektów,fog
 i własność przed uruchomieniem wyboru statku. Read-only dowód1206 zapytań
 oryginału jest gotowy:[WORLD_PICKER_ORDER_EVIDENCE.md](WORLD_PICKER_ORDER_EVIDENCE.md);
 na koniec tamtego etapu nie był to jeszcze port world pickera w C#.
- [ ] Odtworzyć reguły zaznaczenia i komend grupowych,zależności actor action20
 oraz przeliczenie współrzędnych InputSystem do źródłowego świata.
- [ ] Dodać źródłową wizualizację wyboru i zweryfikować input w playerze;
 sam predykat maski nie dowodzi sterowania myszą.
- [ ] Dokończyć pozostałe Life,AI,walkę,pogodę świata,save/load,oprawę2026
 oraz testy natywnego Windows11/docelowego laptopa przed odblokowaniem Start.

DLL etapu masek:
`e211062e1098162e28bc1dcdf66ef9851a8dbfb2666f18d486b6e7e4443e2e89`.
Nie wygenerowano ZIP,podglądu do prezentacji ani publikacji.
Dowód:[SHIP_POINTER_MASK_EVIDENCE.md](SHIP_POINTER_MASK_EVIDENCE.md).
`SHIP_POINTER_RESUME.md` zachowuje historyczny stan pauzy i nie jest bieżącym wynikiem testów.


## Zakończony etap zapytań ograniczonego pickera statków

- [x] Przenieść statek-slot branch49a580 i źródłowe tablice brzegów:
 1206 actualx86/C#query,5665 uporządkowanych wywołań predykatu,
 21 kontroli API,2 testy celowane bez pominięć w1.701s.
- [x] Zachować pierwszy sukces,centrum przed sąsiadami i ponowne wizyty
 tej samej referencji current/reservation;nie sortować po depth lub ID.
- [x] Zintegrować `ShipPickingReference` jako opcjonalnego obserwatora
 checkpointów `ShipOrderReference`;powiązać8 actorów z rzeczywistymi maskami,
 opublikowaną pozycją,stored frame,headingiem oraz bieżącą zajętością.
- [x] Dodać jawny `--ship-picking-reference`,który nie włącza myszy,
 zaznaczeń ani normalnego Start;zachować dotychczasowe flagi rozkazu.
- [x] Zbudować Windows146377147B z0 błędów/ostrzeżeń;sprawdzić
 49 C#/98 meta bez braków,błędnych lub powtórzonych GUID.7 stagingów bez zmian.
- [x] Zakończyć discovery196PASS/0skip/175.263s i osobne7 testów helpera QA/6.968s.
- [x] Zakończyć osobny pilot:12 kadrów,306 zapytań,96 powiązań actor/maska/poza.
- [x] Zakończyć pełny zestaw czterech scenariuszy nowego playera:
 53 kadry/159 ROI RGBmean/max0,1353queries/1243predicatevisits/57queryrows
 z powtórzonym ownerem,424actorbindings.53 pełne kontrole zajętości576
 komórek i1802 rzeczywiste odczyty kolejki. Cleanup8/8/8/9 exit0.
 58 prób/5 odrzuconych:4 dokładne wcześniejsze checkpointy i1 niesklasyfikowany.
 Wszystkie111 PNG niezależnie sprawdzone przed i po dekodowaniu.
 Pilot12/306/96 jest osobny,nie doliczany. Raport:`artifacts/world-picker/runtime-final/report.json`.
- [x] Zakończyć dokładnie2 grupy regresji na tym samym DLL:stary
 `--ship-order-reference` normal bez obserwatora (1 sesja/12 kadrów/36 ROI
 RGBmean/max0,cleanup8 exit0,brak nowych querylogów) oraz menu
 (syntetyczny InputSystem27 etapów/5 obrazów/6 komend,zwykły ApplicationQuit0).
 Raporty:`artifacts/world-picker/{legacy-order,menu}-regression/report.json`.
 Nie deklarować ponowienia wszystkich starszych grup ani input w rozgrywce.
- [ ] Rozwinąć pozostałe sloty świata/fog oraz pełną politykę wyboru,
 pendingselection,drag i grupy przed uruchomieniem sterowania.
- [ ] Przenieść membership action41 oraz rozróżnienie pól5c/5e,komendy
 do actor i zależne planowanie. [Źródłowy dowód](WORLD_MEMBERSHIP_MOVEMENT_EVIDENCE.md)
 jest source-only i nie oznacza implementacji grup w C#.
- [ ] Połączyć InputSystem ze źródłowym układem świata i wizualizacją
 wyboru;sprawdzić wejście w playerze i na docelowym Windows11.
- [ ] Dokończyć pozostałe Life/AI/walkę/pogodę/save/load/oprawę2026
 oraz testy docelowego laptopa przed odblokowaniem Start.

DLL etapu pickera:
`a706aa5e9d9a5966b78c84bc1eace6f669f655a0e94601f82aeb2002e5305409`.
Nie generować ZIP,podglądu do prezentacji ani publikować.
Dowody:[adapter i kolejność](WORLD_PICKER_ORDER_EVIDENCE.md),
[runtime](WORLD_PICKER_RUNTIME_VALIDATION.md).


## Bieżący etap sterowania pojedynczym statkiem myszą

- [x] Potwierdzić hover2327 stanami native/C#,cache SCREEN/WORLD i LifeRefresh.
- [x] Potwierdzić normalne LeftUp,kolejność41/20 i oddzielne pola UI5c/Sim5e;
  reselekcja tworzy kolejne grupy,a nie stale group0.
- [x] Sprawdzić planowanie wszystkich576 celów i coupledWork dla grup0/1/2
  przy siedmiu nieruchomych peerach;zachować zakres projekcji.
- [x] Potwierdzić selector407 i kursor94 stanami,oryginalne RLE/pasek i kolejkę;
  dostarczyć ósmy staging29 obrazów.
- [x] Połączyć InputSystem.onEvent z maskami,wyborem i fizyką;zachować Move
  przed Up oraz brak syntetycznego Up po anulowaniu.
- [x] Rozróżnić globalny Move z dwoma draw od Life z jednym;HD subpixel
  nie uruchamia draw. Oddzielić bounded40ms CursorLife od renderowania.
- [x] Usunąć różnicę RGB2 kursora przez późny SpriteRenderer32767;
  finalne60 kadrów maRGBmean/max0.
- [x] Zakończyć buildWindows0/0,finalny discovery i14QA,2 finalne scenariusze
  myszy i2 regresje na tym samym DLL;57C#/109meta bez zmian po buildzie.
- [x] Zachować blokadę aktywnego gestu ramki przy opuszczeniu viewportu;
  nie zamieniać powrotu z przytrzymaniem w przypadkowy rozkaz SEA.
- [ ] Rozszerzyć zaznaczanie na pozostałe statki,ramkę,modifiers i pełne grupy;
  zaimplementować kolejkę i zastępowanie aktywnego ruchu.
- [ ] Przenieść pozostałe sloty świata/fog i pełną politykę wyboru.
- [ ] Przenieść pełne RunApp z pilną kolejką/pauzą i potwierdzić kolejność systemów;
  bounded40ms nie jest dowodem całego schedulera.
- [ ] Dokończyć Life/AI/walkę/pogodę/audio/save/load i oprawę2026.
- [ ] Zweryfikować rzeczywistą utratę fokusu,natywny Windows11 i docelowy laptop
  przed odblokowaniem Start;próby aktywacji Wine były nieudane.

Bieżący dowód:[VALIDATION.md](VALIDATION.md),[implementacja](WORLD_POINTER_INPUT_IMPLEMENTATION.md),
[QA](SHIP_POINTER_QA_EVIDENCE.md). Milestone:
`docs/evidence/milestone-20261103-world-pointer-input.json`.
Poprzednie milestony pozostają historyczne. Bez publikacji i ZIP.


## Bieżący mały etap — ramka dla sterowanego0b

- [x] Odtworzyć źródłowe zbieranie normalnych statków po komórkach,z rezerwacją i deduplikacją;1745 porównań x86/C#.
- [x] Odtworzyć politykę ramki dla0b;pusty wybór,1×1,Shift/Ctrl i istniejąca grupa:144 porównania.
- [x] Odtworzyć kontur,podpisane wymiary,32 fazy i50ms;1920 buforów/7864320 pikseli,25 kontroli API.
- [x] Połączyć gest z InputSystem i URP;nie tworzyć komend ruchu przy ramce/prawym Up/anulowaniu.
- [x] Zakończyć końcowy replay30 etapów RGB0,234 discovery +osobno2 QA oraz regresje myszy/menu na tym samym DLL.
- [ ] Rozwinąć źródłowe selektory i wybór innych statków oraz wielu statków. Obecnie zbiór0b/0d/0c jest rozpoznany,ale jawnie blokowany przed zmianą wyboru.
- [ ] Przenieść pełną obsługę grup,modifiers w playerze,zastępowanie ruchu i planowanie dla współdzielonej grupy.
- [ ] Dokończyć fog/pozostałe sloty/scheduler/Life/AI/walkę/audio/save-load/oprawę2026 i testy Windows11/laptopa przed odblokowaniem Start.

Dowód i punkt wznowienia:[SHIP_BOX_SELECTION.md](SHIP_BOX_SELECTION.md).
Starsze sekcje dokumentują wcześniejsze etapy;bieżący stan jest podany tutaj.


## Bieżący etap — wybór tymczasowej floty

- [x] Odtworzyć wybór0b/0c/0d,Shift toggle,Shift box iCtrl przy group−1;1710 transakcji źródłowych.
- [x] Rozwinąć hover na wszystkie8 podzbiorów;9280 stanów C#/x86.
- [x] Zachować normal/callback ties oraz usuwane i ponownie używane sloty;2376 stanów.
- [x] Przenieść RAM56/64/72 i paski34/42/50;1221 stanów,180 RLE i6 buforów callbacku;dziewiąty staging33 obrazów.
- [x] Sprawdzić46 etapów playera RGB0,241 discovery i2 osobne QA oraz3 regresje na tym samym DLL.
- [x] Przenieść normalne przypisanie tymczasowej floty do Mode10,ponowne przypisanie i wszystkie membership41 z osobnym odbiorem FIFO;258 scenariuszy/2175 stanów x86/C#,także DLL builda Unity.
- [x] Przenieść formację i serializację20:2988 zgodnych formacji/40 jawnych ograniczeń;237 scenariuszy41→20 i1287 stanów skrzynek26B;pełna fala5250 przypadków.
- [x] Rozwinąć wspólny rdzeń fizyki0b/0c/0d na przygotowanych trasach:15 scenariuszy/6795 stanów,1440 publikacji i300 zmian komórek.
- [x] Połączyć normalny odbiór20/promocję26B,dynamiczny planner i fizykę0b/0c/0d:14 scenariuszy10827 stanów oraz130 osobnych przypadków planera.
- [x] Uzupełnić normalne animacje0c/0d i kontrolny rendering trzech ruchomych statków:34 pełne obrazy RGB0,102 stany,340 części,1156 odczytów kolejki.
- [x] Połączyć pierwszy normalny rozkaz floty z kursorem/wyborem i Ctrl przywołaniem grupy;23 punkty/69 stanów/6 pakietów w playerze.
- [ ] Przenieść pracę zadań grupy i rozszerzyć połączone sterowanie o kolejne rozkazy oraz Shift zatwierdzonej grupy.
- [ ] Ustalić własność zadań grupy i kolejność pełnego schedulera;odblokować sterowanie dopiero po walidacji połączonego obiegu.
- [ ] Uzupełnić kontekstowe akcje prawego przycisku,przywoływanie istniejącej grupy po Ctrl i zastępowanie rozkazów.
- [ ] Dokończyć pozostałe sloty/fog/scheduler/Life/AI/walkę/audio/save-load/oprawę2026 i natywny Windows11/laptop.

Dowód i wznowienie:[SHIP_FLEET_SELECTION.md](SHIP_FLEET_SELECTION.md).
Normalny Start nadal wyłączony. Bez publikacji,ZIP i podglądu do prezentacji.

Najnowszy podkrok:[SHIP_FLEET_MEMBERSHIP.md](SHIP_FLEET_MEMBERSHIP.md).
Sam moduł członkostwa nie odblokowuje ruchu. Dotychczasowy`ShipMoveOrder`
pozostaje projekcją0b z siedmioma statycznymi peerami;pełna flota wymaga
formacji,własnych skrzynek26B,promocji i dynamicznego planowania wspólnej grupy.

Najnowszy etap:[SHIP_FLEET_FORMATION.md](SHIP_FLEET_FORMATION.md). Gotowe są cele,
pakiety i odbiór pending80;promocja,fizyka pozostałych kadłubów i UI nadal wymagają portu.

Najnowszy podkrok:[SHIP_PREPARED_FLEET_MOTION.md](SHIP_PREPARED_FLEET_MOTION.md).
Ruch wielu ciał potwierdzono na jawnych trasach wejściowych;generowanie tras
z przyjętych rozkazów,promocja i integracja playera pozostają kolejnym krokiem.

## Bieżący etap — rozkazy i dynamiczny ruch trzech kadłubów

[SHIP_LIVE_FLEET_ORDERS.md](SHIP_LIVE_FLEET_ORDERS.md) zastępuje wcześniejsze
stwierdzenia o braku promocji/planera0c/0d. Nowy CreateLiveLocal przyjmuje
normalny rozkaz w idle i planuje na żywej siatce z grupą symulacji5e.
14 przebiegów10827 stanów/10740 ticków/1997 publikacji/196 mutacji oraz130
osobnych wejść planera/149760 komórek są zgodne z x86 i DLL Unity.
10 testów PASS0skip95.599s;trzy nowe mutacje wykryte. Build148068283B0/0.
Wcześniejszy nieudany test mutacji cache zachowano;dodano brakujący dowód
bez zmiany reguł oryginału. Kontrolowane ticki nie dowodzą całego Life.
Nowy rdzeń nie jest jeszcze połączony z myszą i renderowaniem0c/0d. Własność
zadań grupy,Ctrl istniejącej grupy,zastępowanie rozkazów i pełna gra pozostają
nieukończone. Następnie uzupełnić zasoby ruchu i dopiąć sprawdzone moduły do
playera,utrzymując1920×1080/16:9/fullscreen i odrębny etap oprawy2026.

## Bieżący etap — trzy statki w rendererze

[SHIP_FLEET_RENDERING.md](SHIP_FLEET_RENDERING.md):nowy kontrolny tryb wykonuje
normalne rozkazy trzech rzeczywistych kadłubów i wyświetla wszystkie publikacje.
Dwa przebiegi250ticków,pending1/7 i kolejność normal/reverse:34 obrazy RGB0,
102 stany,340 części,1156 odczytów kolejki.0d zachowuje pancerz i rozmiar72.
14 testów PASS0skip41.923s;Windows152921579B0/0;70C#/128meta/10stagingów.
Następnie UI i zadania grupowe. Cele/grupy/ticki są tu jawnymi wejściami;
nie odblokowano jeszcze wspólnego sterowania myszą ani normalnego Start.
Pełny scheduler,gra i oprawa2026 pozostają do wykonania. Bez publikacji i ZIP.

## Bieżący etap — pierwszy rozkaz floty z kursora

[SHIP_FIRST_FLEET_CONTROL.md](SHIP_FIRST_FLEET_CONTROL.md):normalny pierwszy
rozkaz trzech członków,41 przed20,formacja,ruch i Ctrl przywołanie grupy.
135 źródłowych przypadków Ctrl/360 stanów;606 stanów obieguUI→pakiety→body,
z jawną granicą dwóch emulatorów. Player:23 punkty/69 stanów/230 części/782
queue reads/136 publikacji i dokładne6 pakietów;bez nowej deklaracji UI RGB0.
10 testów celowanych+2QA PASS,0skip;Windows152935595B0/0;71C#/129meta.
Kolejne/queued/busy rozkazy oraz Shift zatwierdzonej grupy pozostają zablokowane.
Źródło49e850 zmienia prawdziwe członkostwo;4a1340/4a1770 dopisują300/311 do
32B kolejki zdarzeń grupy. Następnie przenieść jej konsumpcję i normalne
zadanie100/1,zamiast traktować zatwierdzoną grupę jak temporary toggle.
Cała gra,oprawa2026 i natywna walidacja docelowego sprzętu nadal nieukończone.

## Bieżący etap — rdzeń normalnego zadania100/1

[SHIP_FLEET_NORMAL_TASK.md](SHIP_FLEET_NORMAL_TASK.md):nowy czysty moduł
przechowuje żądanie,przydziały i32B zdarzenia oraz wykonuje źródłową pracę
grupy.124 scenariusze/778 snapshotów/330 pakietów20+35 i20 API zgodne
z oryginalnym x86 i shippingDLL;3 testy PASS0skip55.239s,sześć mutantów
wykrytych.72C#/130meta,wszystkie71 wcześniejszych C# bez zmian.
Windows152941931B0/0. Zadanie nie kończy się automatycznie przy celu;
nie czyści move-active80. **Nie podłączono go jeszcze do świata/sterowania.**
Następnie własność grupy/events/retained slots,kolejność faz świata i busy
odbioru20. Blokady kolejnych/queued/Shift pozostają;nie mylić fixture
z portem członkostwa Shift.1920×1080/16:9/fullscreen;gra/oprawa2026 w budowie.

Pełny discovery tego etapu:274PASS0skip684.534s. Regresja playera23 punkty/
69 stanów/230 części/782 odczyty/136 publikacji,exit0,bez PNG.265 plików
przed/po buildzie,78 Resources i9 oryginalnych wejść zachowało hashe.

## Własność zadań grupy — 2026-11-04

[SHIP_FLEET_GROUP_OWNERSHIP.md](SHIP_FLEET_GROUP_OWNERSHIP.md):rozszerzono
istniejący ShipFleetMembership,własny task/wiek/retained slots na grupę,
311 przed resetem indeksów,osobne300,41 dostarczane jawnie.262 scenariusze/
2486 punktów/3960 stanów grup/3098 pakietów i26 API zgodne z x86 i DLL;
225 par wyborów z aktywnych zadań.1 C# zmieniony,71 bez zmian,72C#/130meta;
Windows152945003B0/0. Nie jest to integracja z zegarem świata lub UI.
Następnie arbitraż busy20 i dowód faz,przed Shift/kolejnymi rozkazami.
Praca metodą funkcjonalnej inżynierii wstecznej;nie udawać źródeł C/C++,
TickManager/pełnego ECS ani brakujących reguł.1920×1080/16:9/fullscreen.

Testy etapu:13PASS0skip350.891s(3nowe+10regresji),7 mutantów wykrytych;
zegar1287 przypadków zgodny.265 plików przed/po buildzie,78 Resources
i9 oryginalnych wejść bez zmian. Pełnego discovery nie powtarzano.
