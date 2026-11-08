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

# Kontekst projektu Unity

Następny dowódUI również ukończony: [QUEUED_UI_WORLD_EVIDENCE.md](QUEUED_UI_WORLD_EVIDENCE.md).
12cases2400frames48requests7344states zgodne x86/C#/shippingDLL;2testPASS107.791s.
Razem10testów w dwóch zestawach,330discovery bezfullrun. WPMOVE type8 znaleziony
w controlm:21części/36×29,cyfryWPNUM iWPMOVE,offsety/SHA w discoveryJSON;
bez graf.konstruktora lub nowychobrazów. Dalej adapterjawnychsłów/Shift+markery/QA.

Aktualny etap: [integracja task100/2 i310 w świecie](QUEUED_WORLD_INTEGRATION.md).
Zmiana runtime tylko ShipWorldStep. Arrival przekazywane po każdym aktorze,
Work100/1/2 w pozycji floty,jedna poczta. Prefix words jawnie perstep/rejestr,
mapowane do członków;null context dla100/2 jest odrzucany. Brak default117.
50scen5536klatek16608stanów plus pełny1001:5388stanów/310 PASS.
8testPASS188.276s,328discovery;clock1287;3mutnowe+5legacy.10APIcontrols.
Historyczne ret-notification fixture nie zmienione;tylko ich testowy widok
pomija nieobserwowane dawniej310. Nowe testy sprawdzają wszystko bez filtrowania.
DLL161a875ab0612b2945560d7adcd5f8922e45f56c144e6379b1b96cae683a517e,
Windows64Mono152977451B0/0.275frozen73CS131meta,1zmieniony72bez zmian.
Następnie UIShift z jawnym kontekstem. Źródłowy nowy korpusUI12/2400/48 gotowy,
jeszcze nie dowód C#UI. User prosi o dalszą autonomiczną pracę przez kolejne etapy.
1920×1080/16:9/fullscreen;bezPNG/ZIP/publikacji/aplikacji/nowychagentów.
Starsze wyniki historyczne.

---

Aktualny etap: [świat100/2 x86 i zgłoszenia aktora](FLEET_QUEUED_WORLD.md).
Zmiana runtime wyłącznie ShipMoveOrder: niezmienne Arrival(Counter,CellIndex),
LastStepArrivalCount i GetLastStepArrival; dwa źródłowe miejsca4a49af/4a4a67.
Nie jest to drugi bufor tasków; UI/member index nadal należą do Membership.
Świat C# jeszcze nie konsumuje nowego wyniku, guard100/2 pozostaje aktywny.
Korpus oryginału:46scen/5416klatek/16386stanów,258dotarć,48odczytówprefixu,
24rejestry i3niezależne graniceUI. Sametick310 nie oznacza sametickodbioru20.
6testPASS0skip208.196s,3mutC#/3mutx86,324discovery bezfullrun;clock1287 zgodny.
Pierwszy błąd tuple/list metadanych checkera poprawiony, bez zmiany danych x86.
275frozen,73CS/131meta;1CSzmieniony72bez zmian. Clock/World/Task/Grid bez zmian.
Windows64Mono152975915B0/0,1920×1080/16:9/fullscreen;
DLLb7247a256195d67d51bb91c8db3c8aa02b0270e8147127ae1e7c906d8ea53d55.
Następnie synchronizacja Arrival po każdym aktorze w istniejącym rejestrze,
przełączenie grupowego Work100/2 z jawnym kontekstem każdej fali, potemUI.
Bez PNG/ZIP/publikacji/aplikacji/nowych agentów. Starsze wyniki historyczne.

---

Bieżący etap:czysty C# port100/2 w istniejącym pojedynczym Group.Task.
Szczegóły:[FLEET_QUEUED_PORT.md](FLEET_QUEUED_PORT.md).
ShipFleetNormalTask obsługuje Subtype1/2;ShipFleetMembership nadal jedynym
właścicielem składu iAge. SourceWaveField ma osobne źródłowe jądro545960.
WorkQueuedTask wymaga jawnego signed16prefixu każdej fali;bez domyślnego117/0.
World/Clock nie wykonuje jeszcze100/2:preflight blokuje nieobsługiwany kontekst
przedcounter/mail,bez zmian kolejności rejestru iBegin/Complete.
64cases1121states,19API i20pól/11520słów zgodne x86/C#/shippingDLL.
4testPASS132.663s,319discovery bezfullrun. Windows64Mono152975403B0/0,
DLL8ca1c3b4ccf48ac651a1f3662bc50da32004a0aae2406d1bfe5632e3e367d001.
73CS/131meta;4CSzmienione69bez zmian;275frozen i78Resources zachowane.
Shift/300/311/40/fullLife/AI/Start pozostają bramkami. Następnie dowód100/2
w świecie i poczcie z310ze statków.1920×1080/16:9/fullscreen pozostaje.
Bez PNG/ZIP/publikacji/aplikacji/nowychagentów. Starsze wyniki historyczne.

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

---

## Historia poprzednich etapów

Aktualny etap2026-11-04:własność normalnego zadania w ShipFleetMembership.
Każda grupa ma własny ShipFleetNormalTask,wiek i zachowane sloty;bez nowego
menedżera/ECS/Update.262 przypadki/2486 punktów/3960 stanów grup i3098
pakietów(1566x41,1523x20,9x35) zgodne z x86 i shippingDLL;26 API.
13 testów PASS0skip350.891s(3nowe+10regresji),7 mutantów wykrytych;
1287 przypadków zegara nadal zgodne.Full discovery nie powtarzano;277oczekiwane.
W tym225 uporządkowanych par wyborów;w jednym source engine membership,
events,taskWork i41receipt. Q filtruje41;nie jest pełnym globalnym FIFO/Life.
49bd60 nie tworzy300;osobne4a1340.311 poprzedza reset UI/index i41−1;
55b490 zachowuje ogon;49bef0 zwraca0 także po usunięciu w trybie lokalnym.
Zmieniono tylko ShipFleetMembership.cs,pozostałe71 C# bez zmian;72C#/130meta,
10 stagingów.265 plików po buildzie zgodnych. DLL80f9228368a20ccff99c9970647654936b7987daed707d35bbf74803e62d99e5,
Windows152945003B0/0. Shipping legacy2175+1287+360+778 i nowe2486 zgodne.
Player23/69/230/782/136publikacji i6pakietów exit0,bez PNG/nowego UI RGB0.
To regresja starego sterowania:NOWEJ WŁASNOŚCI NIE PODŁĄCZONO DO ZEGARA/UI.
Shift/kolejne/queued/busy i Start nadal zablokowane. Następnie4e2ba0/4abe50/
4ab250 busy20 oraz fazy świata,przed UI Shift. Nie resetować sztucznie80.
Zasady:funkcjonalna inżynieria wsteczna;adresy/offsety i porównaniax86,
nie oryginalny C/C++ ani pełny ECS. UżywaćSingleStepClock,ShipMoveOrder,
MissionOccupancyGrid,obecnej arytmetyki i manifestów. Nie zgadywać reguł.
Czytać[SHIP_FLEET_GROUP_OWNERSHIP.md](SHIP_FLEET_GROUP_OWNERSHIP.md),[VALIDATION.md](VALIDATION.md).
1920×1080/16:9/fullscreen;pełna gra/oprawa2026/Win11/laptop nadal w budowie.
Bez publikacji,ZIP,podglądu i nowych agentów. Starsze punkty są historyczne.

Aktualny etap2026-11-03:czysty ShipFleetNormalTask100/1 w buildzie, jeszcze
bez podłączenia do zegara/sterowania.124 przypadki/778 snapshotów zadania,
316 pakietów20 i14 pakietów35 zgodnych z x86/checkedC#/shippingDLL;20 API.
32B zdarzenia od końca;300 reformuje grupę,311 jest odrzucane;zachowany
ogon slotów i stare przydziały. Wiek>100 przed dodaniem pending;ponowienie
idle poza tolerancją1. Samo dotarcie nie usuwa zadania ani move-active80.
Shift C# i arbitraż busy20 nie są jeszcze przeniesione;blokady w UI zachowane.
3 nowe testy PASS0skip55.239s;sześć mutacji kodu wykrytych.
Pełny discovery274PASS0skip684.534s;player23/69/230/782 i136publikacji
regresji pierwszego rozkazu/Ctrl PASS exit0,bez PNG/nowego UI RGB0.
72C#/130meta/10stagingów;71 wcześniejszych C# bez zmian.
Windows64Mono152941931B0/0,DLL6d92c6590832d2ff5908b06bcc061d964662b04080fa1d850077057f55a4516f.
Czytać[SHIP_FLEET_NORMAL_TASK.md](SHIP_FLEET_NORMAL_TASK.md),[VALIDATION.md](VALIDATION.md).
Następnie własność task/events/slotów w grupie oraz dowód faz świata/busy
odbioru20,przed Shift i kolejnymi rozkazami. Pierwszy rozkaz i Ctrl pozostają
w diagnostyce;Start/pełna gra/oprawa2026 nadal w budowie.1920×1080/16:9/fullscreen.
Starsze punkty poniżej są historyczne.

Aktualny etap2026-11-03:pierwszy normalny rozkaz floty przez kursor oraz
Ctrl istniejącej grupy. Nowy --ship-pointer-fleet-movement wymaga pointer
reference i fleet-selection. Kliknięcie zatwierdza pending vector,odbiera41
przed20,stosuje źródłową formację i wykonuje ruch w istniejącym rendererze.
Scope FIRST NORMAL ORDER ONLY;Shift committed-group editing/kolejne/queued
rozkazy zablokowane do portu zadań grupy. Start nadal wyłączony.
Ctrl135 przypadków360stanów;UI/body source-engine handoff606stanów/600ticków,
136publikacji/12mutacji/33API. Nie jest to jeden pełny natywny Life.
Player InputSystem23punkty/69stanów/230części/782queue reads;6pakietów.
10testów PASS0skip87.778s +2QA PASS0skip12.195s;5mutantów logu i1Ctrl wykryte.
71C#/129meta/10stagingów;6istniejących C# zmienionych+1replay,64bez zmian;
228plików zamrożonych przed/po buildzie zgodnych;core/planer/formacja bez zmian.
Windows64Mono152935595B0/0,DLL5c9be5fd1b4ee4078e188a3ad5c955328dd50f65afc0cd7a6b7c86fe862abf49.
Czytać[SHIP_FIRST_FLEET_CONTROL.md](SHIP_FIRST_FLEET_CONTROL.md),[VALIDATION.md](VALIDATION.md).
Nowy UI test porównuje stan/pakiety/sprite/pozycję/sortingOrder;NIE pełne RGB
kompozytu ruchomych selektorów. Osobne regresje pikseli opisuje VALIDATION.
Normalne zadanie100/1 ma101B;grupa posiada32B event queue,add300/remove311.
Następnie przenieść konsumpcję tej kolejki/pracę grupy przed rozszerzeniem
sterowania. Pełna gra/oprawa2026/natywnyWindows11/laptop/OSmouse w budowie.
Starsze punkty poniżej są historyczne.





Aktualny punkt wznowienia2026-11-03:ramka dla sterowanego0b ukończona
w ograniczonej diagnostyce.62C#/114meta,8 stagingów,DLL8ed5e4c…;234 discovery
+osobno2 QA;końcowy replay30 etapów RGB0 i regresje myszy/menu PASS.
Przed dalszą pracą czytać[SHIP_BOX_SELECTION.md](SHIP_BOX_SELECTION.md)
i[VALIDATION.md](VALIDATION.md). Następny krok:pozostałe selektory i pełna
flota;normalny Start nadal wyłączony. Starsze sekcje poniżej są historyczne.


<!-- unity-onboarding:generated:start -->

Stan: 2026-11-03. Projekt: `/workspace/gierka/Unity/AncientConquest`.
Bazowy commit repozytorium `864d5bdcb6c727495676c7a0d439615077a206a6`;
zmiany pozostają w katalogu roboczym.

## Obowiązujący cel i stan migracji

Ostatnia instrukcja użytkownika ustala **1920×1080, 16:9, pełny ekran całej
gry na Windows 11**. Obejmuje rozgrywkę, kamerę, UI, tekstury i modele.
Zastępuje poprzednie 1280×1024. Nowa oprawa silnie inspirowana oryginałem
jest dozwolona, przy zachowaniu mechanik, AI, treści i tempa.

Kod i staging mają płótno 1920×1080. Schema manifestu pozostaje 3; atlas
ma 1878×288 (2 163 456 bajtów RGBA), sześć kolumn 313×72 i cztery stany.
Prostokąty zaczynają się w `(220,418)`, `(316,511)`, `(412,605)`, `(508,698)`,
`(604,792)`, `(700,886)`. Statyczne UI ma 1920×1080 (8 294 400 bajtów).

Wybrane tło `artifacts/native-art/menu-background-widescreen-draft.png`
ma 1672×941, SHA-256
`d999d1294806d76cb838f39a57e591d9ecda51b176d61bc95fa419078278c4ee`.
To szkic wymagający powiększenia, **poniżej docelowej jakości detalu**.
Stager nie zmienia jego pikseli; GPU powiększa je podczas renderowania.
Domyślnie staging wymaga co najmniej 1920×1080. Osobny
`--allow-draft-upscale` umożliwia jawnie roboczy wariant i manifest zapisuje
`background_upscale_draft=true`. Nie traktować go jako gotowej oprawy 2026.
Szczegóły: [FIRST_FRAME.md](FIRST_FRAME.md), [ART_DIRECTION.md](ART_DIRECTION.md).
Nowy build i testy wymagają własnych dowodów. Historyczne wyniki 1280×1024
nie potwierdzają kandydata 16:9.

## Potwierdzone środowisko

- Unity **6000.3.27f2 / 22188f149405**, aktywna Personal, Windows Mono.
- Oficjalny szablon URP 2D 6.1.6; URP 17.0.3 / Renderer2D. QualitySettings
  wskazuje UniversalRP na wszystkich poziomach. Wcześniejszy import i player działały.
- Input System **1.20.1**, `activeInputHandler: 1`. Usunięto zbędny collab-proxy2.6.0;
  razem ze starszym Input 1.12 powodował potwierdzone błędy kompilacji w Unity 6.3.
- Test Framework 1.4.5, uGUI 2.0.0, wbudowany IMGUI 1.0.0;
  `Packages/packages-lock.json` został wygenerowany przez Editor.
- Brak Unity MCP w pakietach, konfiguracji i aktywnych narzędziach;
  nie dodawano mostu. Używane są oficjalne CLI, batch Editor i lokalne testy.
- Keyring/auth/licensing CLI wymagają wykonania poza sandboxem. Nie odczytywać
  ani nie wypisywać tokenów. Używać `/workspace/toolchains/unity-env.sh`.

## Struktura i architektura

| Ścieżka | Odpowiedzialność |
| --- | --- |
| `Assets/AncientConquest/Runtime/NativeMenuFrame.cs` | Pełnoekranowe tło i atlas, uporządkowane wejście myszy, własność zasobów i subskrypcji |
| `Assets/AncientConquest/Runtime/NativeMenuCanvas.cs` | Kontrakt natywnego płótna; nowy cel 1920×1080 |
| `Assets/AncientConquest/Runtime/TerrainReferenceFrame.cs` | Diagnostyczny teren i właściciel coroutine referencji obiektów/statków/ruchu; zwykły Start bez zmian |
| `Assets/AncientConquest/Runtime/TerrainMapData.cs` | Planarny parser ośmiu warstw i odwołania do klatek; bez rozwiązywania bibliotek/bitmap |
| `Assets/AncientConquest/Runtime/TerrainViewport.cs` | Izolowane ClampAxis i CellToScreen z arytmetyką oryginalnego x86 |
| `Assets/AncientConquest/Runtime/MissionShipSeed.cs` | Niemutowalna recepta pól statku trybu 0 i źródłowej geometrii; bez oryginalnego konstruktora |
| `Assets/AncientConquest/Runtime/MissionOccupancyGrid.cs` | Kopia flag i pojedynczy slot właściciela komórki; predykaty flag, claim/release po identyczności referencji |
| `Assets/AncientConquest/Runtime/MissionShipReference.cs` | Lokalny właściciel 29 zamrożonych składników ośmiu statków i częściowej siatki zajętości |
| `Assets/AncientConquest/Runtime/ShipMovementReference.cs` | Osobna diagnostyka przygotowanego odcinka0b; zamknięte historyczne QA ruchu/przerwania |
| `Assets/AncientConquest/Runtime/ShipAdjacentReference.cs` | Historycznie zweryfikowana diagnostyka8 sąsiadów0b:6 tras/2 odmowy, jawny zegar/holdy |
| `Assets/AncientConquest/Runtime/ShipRouteReference.cs` | Dłuższe trasy0b, każda publikacja/depth w kolejności,31 pól stanu i34 rzeczywiste odczyty kolejki |
| `Assets/AncientConquest/Runtime/ShipOrderReference.cs` | Jawna diagnostyka normalnych rozkazów0b; rozdziela sample/request/Tick i kolejne cele po idle |
| `Assets/AncientConquest/Runtime/Simulation/ShipWorldPicker.cs` | Ograniczony ship-slot49a580;centrum/brzegi/firsthit bez dedup i sortowania;bez fog/innych slotów |
| `Assets/AncientConquest/Runtime/ShipPickingReference.cs` | Opcjonalny obserwator checkpointów;rzeczywiste8 bindings/query,bez myszy lub zaznaczeń |
| `Assets/AncientConquest/Runtime/Simulation/ShipPointerMask.cs` | Czysty predykat źródłowych masek type18;stored frame/heading,bez zaznaczeń i input |
| `Assets/AncientConquest/Runtime/Simulation/ShipMoveOrder.cs` | Request/promotion/Work/replan/stop/ruch;legacy0b oraz CreateLiveLocal0b0c0d i osobna gałąź przygotowana |
| `Assets/AncientConquest/Runtime/Simulation/ShipReplanPlanner.cs` | Plan statycznego0b i PlanLive;bieżące stany/grupa5e,nearest,RNG i rewalidacja cache |
| `Assets/AncientConquest/Runtime/Simulation/SourceNearestPathfinder.cs` | Źródłowe55b9e0 partial path/range,bez ogólnej polityki świata |
| `Assets/AncientConquest/Runtime/Simulation/ShipIdleProgression.cs` | Normalne idle56…87,LCG,release i publikacja przed stored frame |
| `Assets/AncientConquest/Runtime/SourceCohortOrderReference.cs` | Wiąże21 grup z34 faktycznymi rendererami statków/raf; spłaszcza queue z lokalnym TYPE8order |
| `Assets/AncientConquest/Runtime/SourceSpriteDepthQueue.cs` | Czyste55d960 dla świeżych normalnych węzłów; zachowane ID i historia remisów; bez callback/recycle |
| `Assets/AncientConquest/Runtime/SourceShipPoseReference.cs` | Wspólny lokalny właściciel atlasu88 póz i publikacji3 istniejących rendererów0b; bez zmiany ich sortingOrder |
| `Assets/AncientConquest/Runtime/MainMenuButton.cs` | Czyste stany i podzbiór komunikatów myszy oryginalnego przycisku typu 1 |
| `Assets/AncientConquest/Runtime/Simulation/BossAiMessageGate.cs` | Izolowana reguła dyspozycji AI, niezależna od czasu |
| `Assets/AncientConquest/Runtime/Simulation/SingleStepClock.cs` | Izolowana gałąź kwantu czasu, Begin/Complete bez źródła czasu Unity |
| `Assets/AncientConquest/Runtime/Simulation/ShipMoveRequestInbox.cs` | Ograniczone przyjęcie i promocja komendy ruchu przy jawnym idle context; bez planera |
| `Assets/AncientConquest/Runtime/Simulation/PreparedShipMovement.cs` | Czysty krok przygotowanej trasy source0b16,2→15,3; jawne pending/counter i osiem właścicieli |
| `Assets/AncientConquest/Runtime/Simulation/ShipFrameProgression.cs` | Ogon fazy ruchu z oryginalnym unsigned progiem; bez idle i obrotu |
| `Assets/AncientConquest/Runtime/Simulation/ShipAdjacentQuery.cs` | Czysty predykat celu/narożników499aa0 i projekcja referencji właścicieli |
| `Assets/AncientConquest/Runtime/Simulation/ShipAdjacentPlanner.cs` | Zamknięta projekcja8 sąsiadów źródłowego0b; nie jest ogólnym pathfinderem |
| `Assets/AncientConquest/Runtime/Simulation/ShipAdjacentMovement.cs` | Obrót i ruch źródłowego0b do sąsiada, osobne stored/drawn pose, rezerwacja i transfer |
| `Assets/AncientConquest/Runtime/Simulation/ShipTurnProgression.cs` | Źródłowy pierścień obrotu32…55, ścisły unsigned próg i flaga publikacji |
| `Assets/AncientConquest/Runtime/Simulation/SourceWaveField.cs` | Źródłowe pole fali5578a0/571700 na mapie0/−1, ograniczona kombinacja argumentów |
| `Assets/AncientConquest/Runtime/Simulation/SourcePathfinder.cs` | Źródłowe55c9a0 z linią i falą; kopie input/output, brak modyfikacji trwałej siatki |
| `Assets/AncientConquest/Runtime/Simulation/ShipRoutePlan.cs` | Niemutowalny plan5-bajtowych rekordów i parametrów początkowego stanu |
| `Assets/AncientConquest/Runtime/Simulation/ShipRoutePlanner.cs` | Adapter początkowego0b/staticfleet8 do576 celów; bez pełnego Work/retry |
| `Assets/AncientConquest/Runtime/Simulation/ShipRouteMovement.cs` | Wielopunktowy ruch, lookahead, zakręty i zachowana kolejność wszystkich publikacji/mutacji |
| `Assets/AncientConquest/Editor/BuildReferenceWindows.cs` | Build Windows64 Mono i raport JSON |
| `Assets/Resources/ReferenceGenerated` | Ignorowane dane RGBA, atlas sześciu przycisków/czterech stanów i manifest |
| `Assets/Resources/TerrainGenerated` | Ignorowana referencja RGBA 1536×1536, planarne źródłowe dane i manifest miss000 |
| `Assets/Resources/MissionObjectsGenerated` | Ignorowane 45 seedów, setup gracza/kamery, atlas pięciu raf i manifest |
| `Assets/Resources/MissionUnitsGenerated` | Ignorowane flagi komórek, atlas 17 klatek i manifest 29 składników ośmiu statków |
| `Assets/Resources/ShipPickingGenerated` | Siódmy zestaw:96 source type18 masks/52800B i schema1 manifest;bez zmiany renderowania |
| `Assets/Resources/ShipMovementGenerated` | Oddzielny manifest 88 pozycji source0b i atlas 152 bitmap; nie nadpisuje referencji statycznej |
| `Assets/Settings` | URP, Renderer2D i Input System z szablonu |
| `tools/`, `tests/`, `docs/` repo | Odczyt oryginału, staging, testy i dowody |

Bez własnych asmdef: runtime w `Assembly-CSharp`, Editor w `Assembly-CSharp-Editor`.
Jedyna włączona scena BuildSettings: `Assets/Scenes/SampleScene.unity`, GUID
z szablonu zachowany. Bootstrap BeforeSceneLoad tworzy NativeMenuFrame;
przy jawnym `--terrain-reference`, `--mission-object-reference` lub
`--mission-unit-reference` zamiast niego powstaje TerrainReferenceFrame.
Nowe `--ship-movement-reference` implikuje podgląd jednostek i dodaje
coroutine jednego przygotowanego odcinka; poprzedni build i ścisłe QA ruchu przeszły.
`--ship-adjacent-reference` również implikuje jednostki, wyklucza poprzednią
flagę ruchu i wybiera cel przez `--ship-adjacent-target-x/y`. Opcjonalne
`--ship-adjacent-stop-at` przerywa po wskazanej liczbie calli. Poprzedni build,
155 testów,10 sesji/53 kadry i sześć grup regresji przeszły.
`--ship-route-reference` dodaje dłuższe trasy i wyklucza obie wcześniejsze
flagi ruchu. Cele: `--ship-route-target-x/y`, przerwanie: `--ship-route-stop-at`.
Poprzedni build dłuższych tras i172 testy przeszły; pilotaż zakrętu ma16 kadrów RGB0.
Końcowe QA7 sesji/88 kadrów/264 ROI RGB0 przeszło;31 pól i34 rzeczywiste
wpisy kolejki zgodne z native. Siedem grup regresji starszych trybów przeszło
na tym samym DLL; obie sesje UI zakończyły się zwykłym Quit0.
`--ship-order-reference` dodaje normalny obieg rozkazu i wyklucza pozostałe
trzy tryby ruchu. Cele: `--ship-order-target-x/y`,opcjonalnie oba
`--ship-order-next-x/y`;limit `--ship-order-stop-at`,jawny uint32
`--ship-order-session-seed` (kontrolowane0). Tick1 promuje,planuje i porusza
przy tym samym counter;request2 ma nowy sample,ale może zachować counter.
Poprzedni build obiegu rozkazów146287259/0 błędów/ostrzeżeń i discovery182PASS;osobno7 testów
helpera QA PASS.Pilotaż12 kadrów
RGB0. Końcowy player po restarcie ma4 sesje/53 kadry/159 ROI RGB0,
54 pola i34 rzeczywiste wpisy kolejki na etap. Cleanup8/8/8/9 i exit0.
Cztery grupy regresji na tym samym DLL przeszły:route depth-cross+halt
(2 sesje/28 kadrów),stary odcinek (2/9),briefing39/11 i menu27/5/6;exit0.
Zakończony mały etap dodał czysty `ShipPointerMask` i siódmy staging.
Build146364475B/0 błędów/ostrzeżeń,47 C#/96 meta;432428 native/C# i13 API
guards,5 testów celowanych/14.360s PASS. Świeży discovery po wznowieniu:
194PASS/0skip/181.146s. Regresja dotychczasowych rozkazów nowego DLL:
2 sesje/35 kadrów/105 ROI RGB0,cleanup8/8 exit0. Nie jest to jeszcze obsługa myszy.
Nowy `--ship-picking-reference` uruchamia obieg rozkazów z opcjonalnym
obserwatorem zapytań do `ShipWorldPicker`;wyklucza pozostałe tryby ruchu
oraz replay UI. Nie dodaje myszy/zaznaczeń. Bieżący build146377147B0/0,
49 C#/98 meta,discovery196PASS/175.263s i osobne7QA/6.968s.
Pilot12 kadrów/306queries/96bindings PASS;pełny zestaw4 sesji ma53 kadry/
159 ROI RGB0,1353queries/424bindings i cleanup8/8/8/9 exit0.
Dokładnie2 regresje tegoDLL PASS:normalny rozkaz bez obserwatora12/36 RGB0
cleanup8exit0 oraz menuInputSystem27/5/6 normalQuit0.
Nowych ZIP i podglądów do prezentacji nie tworzyć bez wyraźnej prośby użytkownika.
Druga flaga dodatkowo tworzy lokalnego właściciela pięciu zamrożonych raf.
Trzecia włącza także te rafy i właściciela ośmiu statków z częściową siatką
zajętości, bez zmiany zwykłego Start.
To osobna diagnostyka, bez przejścia z normalnego Start gry;
kamera ma pełne `rect(0,0,1,1)`. Własność tekstur jest lokalna,
cleanup w OnDestroy. Statyczny `MenuUiRgba` pozostaje diagnostyką i nie jest
ładowany przez runtime. Tło i poszczególne przyciski są oddzielnymi warstwami.

Konwencje: `AncientConquest.Presentation`, `.Simulation`, `.Editor`, `.World`;
czysta geometria TerrainViewport pozostaje w głównym `AncientConquest`; prywatne
pola camelCase, lokalne zależności, bez globalnego frameworka. GUID-y meta
zachowano i sprawdzono po imporcie.

## Interakcje i granice implementacji

Stany przycisku: wyłączony 0, normalny 1, naciśnięty 2, najechanie 3.
Normalny stan rysuje wariant fontu 2, zgodnie z oryginalnym kodem.
Natywna geometria 16:9 pochodzi z bieżącego manifestu, bez rozciągania
całej starej klatki 800×600.

`NativeMenuFrame.OnEnable` zachowuje poprzednie ustawienie Input System
`disableRedundantEventsMerging`, ustawia je na `true` i subskrybuje
`onEvent`/`onDeviceChange`; `OnDisable` przywraca ustawienie i usuwa subskrypcje.
Zdarzenia myszy są przetwarzane w kolejności, również down/up w jednej klatce.
Wyłączenie scalania zachowuje ruch poza przycisk i z powrotem, który kasuje
naciśnięcie w oryginale. Utrata fokusu, odłączenie myszy lub wyłączenie
komponentu anuluje stan. `requireLeftRelease` blokuje nowe naciśnięcie do
zaobserwowania zwolnienia; to polityka hosta, nie potwierdzona reguła oryginału.

Podzbiór myszy zmienia wygląd i emituje komendę. `Quit game` wywołuje
`Application.Quit`, bez jeszcze nieodtworzonego wygaszenia HLS. Docelowe
briefing miss000 jest teraz podłączony do Start scenario, a Cancel wraca
do menu. Start rozgrywki jest nieaktywny; inne ekrany i misje niepodłączone.
Nie ma kompletnej symulacji, zapisu, AI ani nowych modeli świata.
BriefingPanel jest lokalnym, leniwie tworzonym obiektem właściciela NativeMenuFrame;
cache zachowuje wybraną trudność po Cancel/reopen, a Dispose zwalnia tekstury.
BriefingDifficultySelection odtwarza TabClass550ba0: wybórnaDown wewnątrz ikony,
brak wyboru przez etykietę/hover/release, domyślnie Easy0.558porównańx86/C#
przeszło. RgbaResourceTexture współdzieli boundedloader; gotowe UI i atlasy
używają Point, tłaBilinear. NativePoint zachowuje przygotowany antyaliasing
zamiast rozmywać glify drugi raz.

`SingleStepClock.Begin` sprawdza kwant i inkrementuje licznik najwyżej raz.
`Complete` po callbackach ponownie otrzymuje bieżącą fazę/kwant i zachowuje
zawijanie 32-bit oraz resztę dzielenia ze znakiem. Callbacków i całej pętli
nie implementuje. Bramka AI pozostaje wyizolowana od świata. Kod nowej
diagnostyki ruchu wykorzystuje tę gałąź z jawnym źródłem realtime i kwantem40;
nie jest to kompletny zegar gry. Nie zastępować go arbitralnym FixedUpdate
60 Hz. Pełne pause/network/replay pozostają nieodtworzone.

## Dowody i walidacja

- Zakończony etap terenu 1920×1080: **94 testy unittest bez pominięć**,
  `artifacts/terrain/full-tests-terrain.txt`. Poprzednie80 zachowano w
  `artifacts/briefing/full-tests-briefing.txt`. Obejmują osiem
  przypadków viewportu C#, 35 porównań bramki AI, 150 kroków/44 ciągi przycisku
  oraz1287 porównań gałęzi zegara. EditorInputSystem ma także rzeczywistą
  kontrolę scalania zdarzeń w `input-system-validation.json`.
- Wcześniejszy Windowsbuild etapu briefingu:0błędów/0ostrzeżeń. Rzeczywisty player1920×1080
  ExclusiveFullScreen przeszedł jawny `--input-replay`: obrazy stanów zgodne
  z atlasem, anulowanie przywraca identyczną klatkę, sześć komend i Quit/kod0.
  Dowód `artifacts/unity-reference/replay-1920x1080-presented/report.json`.
  To syntetyczne InputSystem.onEvent, nie test OS/RAWINPUT/hardware.
- Referencja świata rozszerzona z dziewięciu próbek do całego statycznego terenu
  miss000: 24×24 komórki, osiem warstw, 264 klatki, 1007 operacji. Wszystkie
  użyte klatki mają 1584 zgodne bufory z wykonanych blitterów x86.
  TerrainMapData ma 4608 zgodnych odwołań i 44 osobne sprawdzenia kontraktu C#;
  TerrainViewport ma 1080 przypadków / 2160 porównań osi z instrukcjami x86.
  Nie jest to dowód całego renderera ani zachowania pierwszej misji.
- Poprzedni statyczny prototyp przeszedł import, Windows build bez błędów
  i ostrzeżeń oraz uruchomienie pod Wine 11 w 1280×1024 ExclusiveFullScreen.
  To historyczna baza środowiska, nie dowód 1920×1080 ani obecnych interakcji.
- Wyniki aktualnego buildu, adaptera Input System w Editor i smoke testu
  playera należy odczytać z [VALIDATION.md](VALIDATION.md). Nie przewidywać
  wyników trwających kontroli.
- Natywny Windows 11/laptop RTX 3050 Ti, pełna rozgrywka, kompletny TestRunner
  PlayMode/EditMode oraz zgodność całej gry pozostają niezweryfikowane.

`tools/smoke_native_menu.py` ma jawne `main/run_smoke`, świeży `--output`,
opcjonalne `--diagnostics` i zachowuje launch/report/failure artefakty.
Zamyka wyłącznie własne uchwyty procesów playera/Xvfb, bez zamykania
współdzielonego wineservera. Rozmiar ekranu i współrzędne wejścia pobiera
z manifestu i wymaga aktualnego celu 1920×1080. `--presentation-only`
oddzielnie sprawdza log pełnego ekranu, geometrię okna i rozmiar zrzutu,
bez zdarzeń myszy i testu Quit. Raport jawnie oznacza zakończenie własnego
procesu przez cleanup zamiast normalnego wyjścia gry. Tryb nie stanowi
zaliczenia interakcji; routing Unity RAWINPUT pod Wine jest nadal badany.
Narzędzie jest niezależne od oryginalnej VM. `--input-replay` uruchamia jedynie
jawny komponent Diagnostics/MenuInputReplay, który kolejkuje MouseState przez
normalny adapter. Probe loguje etap po WaitForEndOfFrame; capture oczekuje
obrazu zgodnego z atlasem wewnątrz tego samego etapu. Nie ma bezpośredniego
wywołania domeny ani Application.Quit w probe.

Oryginalny PE32 nie startuje w dotychczasowym Wine na tym hoście: WOW64
trafia na IA32 `int 0x80` podczas inicjalizacji. Pełna VM QEMU TCG wykonała ELF32/int0x80 z kodem0, ale Wineboot240s
i kontrolnyPE32 45s osiągnęły timeout143. Oryginał nieuruchomiony:
[ORIGINAL_VM_PROBE.md](ORIGINAL_VM_PROBE.md). Analiza binarna/Unicorn umożliwia
izolowane porównania, ale nie zastępuje uruchomionej referencji.

Źródła: ProjectVersion, manifest/lock, Graphics/Quality/Player/BuildSettings,
własne skrypty runtime/Editor, [FIRST_FRAME.md](FIRST_FRAME.md),
[VALIDATION.md](VALIDATION.md), [ORIGINAL_BINARY_ANALYSIS.md](ORIGINAL_BINARY_ANALYSIS.md),
[MENU_INTERACTION_EVIDENCE.md](MENU_INTERACTION_EVIDENCE.md),
[SIMULATION_CLOCK.md](SIMULATION_CLOCK.md),
[WORLD_ASSET_REFERENCE.md](WORLD_ASSET_REFERENCE.md).

<!-- unity-onboarding:generated:end -->

## Poprzedni etap briefingu

`artifacts/briefing/windows-build-briefing-final.log`: Windows64Mono,0błędów/ostrzeżeń,
133455363bajty. DLL65b034e1e47ed2b4d3f9b411644f971d7da3376fb67480e80c9389f62d939da7.
`player-native-ui-sampling/report.json`:39etapów/11zrzutów, normalnyQuit0.
`menu-regression-final/report.json`:27etapów/5zrzutów, powrót przezCancel poStartscenario,
normalnyQuit0. Oba testy badają ten sam rzeczywistyDLL i zwykły onEvent; sąsyntetyczne.
BuildReferenceWindows sprawdza wymagane manifesty/schema/canvas
i payloady menu/briefingu/terenu/obiektów/statków/ruchu przed budowaniem oraz tworzy lub weryfikuje
materiał URP2D Sprite-Unlit przez AssetDatabase. Odtwarzalne przygotowanie briefingu opisuje BRIEFING_IMPLEMENTATION.md.
Kolejny dowód mapy, bez deklaracji grywalnej sceny: FIRST_MISSION_MAP_EVIDENCE.md.


## Zakończony etap terenu

`tools/stage_terrain.py` tworzy TerrainManifest schema1 i dwa payloady:
TerrainRgba1536×1536 RGBA32 bottom-up oraz MapPlanar9216bajtów. Dane pochodzą
z b_MAPA/b_ALIB/maplib, są chronione hashami i ignorowane przez Git.
`TerrainReferenceFrame` wczytuje je dopiero po `--terrain-reference`, ustawia
pełny viewport1920×1080 i kamerę ortograficzną bez postprocessingu. SpriteRenderer
wyświetla gotową teksturę złożoną przez staging; nie rysuje ośmiu warstw runtime.
Parser MapPlanar ma osobny dowód i dostarcza tu geometrię. Źródłowe piksele mają Point i skalę2× (kadr960×540); parametry origin są diagnostyczne,
nie są potwierdzonym pierwszym kadrem ani FOV gry. Opcjonalne czasowe wyjście
jest diagnostyczne i nie zastępuje testu przycisku Quit.

`artifacts/terrain/build-report-final.json`: Windows64Mono, 0 błędów/ostrzeżeń,
143660987 bajtów. DLL SHA-256
`a3d98c1d40911cf0205e5ae553542edaeb2207383d1d3f88720e7a266db6d19f`.
`artifacts/terrain/runtime-final/report.json`: trzy osobne sesje playera pod
Wine/Xvfb, pełne 1920×1080 ExclusiveFullScreen. Każdy dopasowany kadr ma średni
błąd RGB0, maksymalny błąd0 i 100% identycznych pikseli; każde diagnostyczne
wyjście po8s dało kod0. Pierwszy nieprzedstawiony jeszcze capture w origin0,0
został odrzucony, drugi jest identyczny; wszystkie próby zachowano.
19 wcześniejszych kontroli dodatnich/ujemnych sprawdziło checker, a powyższy
raport sprawdza rzeczywisty player. Regresje na tym samym DLL również przeszły:
`artifacts/terrain/menu-regression-final/report.json` ma 27 etapów/5 obrazów,
sześć komend i normalny Quit0; `briefing-regression-final/report.json` ma
39 etapów/11 obrazów i normalny Quit0. Oba używają syntetycznych zdarzeń
normalnego adaptera Input System; nie potwierdzają wejścia OS.

Przy zamykaniu obu sesji UI występuje znane ostrzeżenie:
`GarbageCollector disposing of ComputeBuffer. Please use ComputeBuffer.Release() or .Dispose() to manually release the buffer.`
To ten sam komunikat co w poprzednich `artifacts/briefing/player-native-ui-sampling/player.log`
i `menu-regression-final/player.log`; nie jest nową regresją tego kroku.
Przyczyna pozostaje do wyjaśnienia. Build ma 0 ostrzeżeń kompilacji, co nie
usuwa tego ostrzeżenia runtime.

W tym etapie Start rozgrywki pozostawał wyłączony. Nie odtworzono animacji palety,
runtime obiektów i jednostek, AI świata, pełnej kamery ani dźwięku; źródłowa grafika jest referencją,
nie finalną oprawą2026. Szczegóły i ograniczenia:
[TERRAIN_STAGING.md](TERRAIN_STAGING.md),
[TERRAIN_RENDER_EVIDENCE.md](TERRAIN_RENDER_EVIDENCE.md),
[TERRAIN_CAMERA_EVIDENCE.md](TERRAIN_CAMERA_EVIDENCE.md),
[TERRAIN_RUNTIME_VALIDATION.md](TERRAIN_RUNTIME_VALIDATION.md).


## Zakończony etap seedów obiektów i referencji raf

`tools/stage_mission_objects.py` wymaga siedmiu hash-guarded źródeł.
Tworzy `Resources/MissionObjectsGenerated` z manifestem schema1 i czterema
payloadami: ObjectSeeds (8356 bajtów, 45 dokładnych payloadów),
ReefFramesRgba (128×64 RGBA32, bottom-up, 32768 bajtów), MissionDescriptor
(1788 bajtów) i SavedViews (80 bajtów). `LIST_OBJ` nie jest źródłem seedów.
Pierwszy build Windows tego etapu przeszedł z 0 błędów/ostrzeżeń,
143756027 bajtów (`artifacts/objects/build-report-first.json`). Pełny zestaw
109 testów przeszedł bez pominięć: `artifacts/objects/full-tests-objects-final.txt`.

| Runtime C# | Kontrakt i dowód |
| --- | --- |
| `MissionObjectSeed` | Niemutowalna kopia payloadu typu12 `OBJ_*`, canonical ID i jawny little-endian; brak konstruktora klasy świata |
| `MissionObjectSelection.TrySelect` | Filtr PLAYERS_DESC i kod fabryki, 1450 porównań z rzeczywistym x86; samo wybranie nie tworzy obiektu |
| `MissionInitialSetup` | Wybór pary gracza i odczyt źródłowego WIN_VIEW, 177 porównań x86/C#; zwraca kopię tablicy PLAYERS_DESC |
| `MissionReefSeed.TryRead` | Tylko klasa601/tryb0: pozycje, dolny bajt wariantu i kotwice z zawijaniem32bit; 104 porównania, w tym pięć prawdziwych seedów |
| `MissionObjectReference` | Lokalny IDisposable właściciel atlasu, sprite’ów i pięciu wizualnych referencji; żadne oryginalne konstruktory nie są wykonywane |

Oryginalny BTree bez hooków potwierdził kolejność 63 wszystkich rekordów
oraz 45 obiektowych. Fixture `tests/fixtures/mission_miss000_object_order.json`
chroni kolejność stagingu. Osobne instrukcje loadera potwierdziły dwa
oryginalne deskryptory raf, 60 nazw klatek, 180 wyników bbox i 360 buforów RLE.
Współrzędne pełnej płaszczyzny są w world cell ×64; bbox left/top jest już
zakodowany w przezroczystości i nie jest dodawany ponownie.

`--mission-object-reference` sam wybiera istniejący tryb TerrainReferenceFrame.
Po wczytaniu źródłowego setupu wybrane są wszystkie 45 seedów do planu,
ale wizualizowanych jest tylko pięć raf. SpriteRenderer używa Point,
pełnej płaszczyzny64×64 i materiału terenu. Referencje są nieruchome, stan1,
klatka0, przy założeniu pustych komórek kolizji. Overlay ma jawny porządek
referencyjny; nie emuluje pełnego draw order/fog oryginalnego świata.
Dispose usuwa wizualizacje, sprite’y i atlas przed zwolnieniem materiału terenu.

W źródłowej ścieżce Start scenario wybrano slot(1,1), tablicę20bajtów oraz
WIN_VIEW[5]=(15,0). Źródłowy rozmiar widoku to9×8; 12 jest typem zasobu
WIN_VIEW, nie liczbą presetów. To wynik badanej inicjalizacji, nie framebuffer
pierwszej klatki gry. Nie zmieniamy nim diagnostycznej kamery2×/1920×1080.
Nie podłączono `MissionInitialSetup` ani planu seedów do normalnego StartGame.

`artifacts/objects/runtime-final/report.json` potwierdza cztery rzeczywiste
kadry pod Wine/Xvfb, obejmujące wszystkie pięć raf. Każdy pełny obraz RGB ma
średni i maksymalny błąd 0 oraz 100% identycznych pikseli. Pięć osobnych obszarów
raf, w tym pokrytych pikseli sprite’ów, też ma błąd 0. Trzy kadry regresji terenu
w `artifacts/objects/terrain-regression-final/report.json` są identyczne.
Wszystkie sesje zakończyły się diagnostycznym wyjściem z kodem 0.

Oba raporty mają DLL SHA-256
`086b6336947ea73315854addb4c21713b5999d94697b19be729cb8234e8f8817`.
Regresje UI na tym samym DLL również przeszły:
`artifacts/objects/briefing-regression-final/report.json` ma 39 etapów i 11 obrazów,
`artifacts/objects/menu-regression-final/report.json` ma 27 etapów, 5 obrazów
oraz 6 komend. Obie sesje skończyły się normalnym callbackiem Quit z kodem 0.
Wszystkie cztery grupy raportów (obiekty, teren, briefing, menu) wskazują ten
sam runtime DLL. Przed spakowaniem tego etapu po QA nie zmieniano C#.

UI było sprawdzane syntetycznym Input System replay przez zwykły adapter,
bez bezpośrednich wywołań domeny ani zamknięcia. Nie potwierdza fizycznego
wejścia OS. Historyczne raporty zachowano dla ich własnych artefaktów.
Render referencyjny nie dowodzi symulacji ani natywnego Windows 11.

Dokumenty źródłowe: [loader i wybór](MISSION_OBJECT_LOADER_EVIDENCE.md),
[pozycje raf](MISSION_OBJECT_POSITION_EVIDENCE.md),
[zasoby animacji](OBJECT_ANIMATION_ASSET_EVIDENCE.md),
[wybór gracza i kamery](MISSION_INITIAL_CAMERA_EVIDENCE.md).
Dalsze braki tego etapu obejmowały pozostałe klasy i ich konstruktory,
kompletne kolizje, WorldLife, AI, ruch/walkę, czas animacji, audio, oprawę2026
i testy Windows11/laptopa. Bieżące częściowe rozszerzenie opisano poniżej.

## Zakończony etap statków i częściowej siatki zajętości

`tools/stage_mission_units.py` tworzy `Resources/MissionUnitsGenerated`:
manifest schema1, `CellFlags` (576 uint32 little-endian, 2304 bajty) i atlas
`ShipComponentsRgba`. Manifest opisuje osiem statków, 29 instancji składników
z 17 unikalnych klatek i kolejność ich rysowania; wymaga `miss000`, mapy24×24
i płótna1920×1080. Dane źródłowe i wygenerowane payloady są chronione hashami.

`MissionShipSeed` zachowuje właściciela, wariant, pełny runtime tag, pozycję,
kierunek, procent zdrowia i metadane początkowych poleceń. Odtwarza kotwicę
pełnej logicznej klatki z arytmetyką x86; nie implementuje systemu zdrowia,
ruchu, walki ani samego tworzenia instancji źródłowej klasy. Dowód obejmuje
184 porównania C#/x86 i dziewięć kontroli kontraktu.

`MissionOccupancyGrid` klonuje 576 flag i zachowuje osobną tablicę właścicieli
po identyczności referencji. Null oznacza pustkę, a ID0 może być poprawnym
właścicielem. Odtworzone predykaty flag i reguły claim/release mają 1572
porównywane przypadki oraz 68 kontroli kontraktu. To pojedynczy slot komórki,
bez pełnego lifecycle, wieloslotowych zapisów innych klas i pathfindingu.

Dekoder TYPE8 przeszedł siedem testów. Osobne wykonanie oryginału potwierdziło
12 prób loadera, 340 prób lokalnego sortowania składników i 96 dokładnych
buforów RLE dla użytych 17 klatek. Globalny porządek jest osobnym dowodem:
21 węzłów oraz kontrole remisów. Po spłaszczeniu badanego zbioru mamy 34
renderery: osiem osobnych cieni, pięć raf i 21 dodatnich składników statków.
Dodatnie składniki jednego statku zachowują grupę i źródłowy lokalny porządek;
nie przeplatamy kadłubów wszystkich statków z ich żaglami.

`--mission-unit-reference` uruchamia teren, rafy i `MissionShipReference`.
Każdy statek pozostaje w stanie1 i źródłowej klatce kierunku. Referencja
sprawdza pola manifestu wobec seedów, zajmuje osiem różnych komórek, tworzy
29 SpriteRendererów i ustawia kolejność z rafami pomiędzy cieniami a dodatnimi
składnikami. Atlas używa Point; pozycja to kotwica rodzica plus signed offset
składnika, bez ponownego dodawania bbox. Dispose usuwa renderery, sprite’y,
atlas i zwalnia osiem własnych zajęć przed zwolnieniem materiału terenu.

Log wyraźnie oznacza `source_constructors_executed=0`, osiem zajętych komórek,
`pending_orders=0` i `simulation=False`. Są to wizualne referencje, bez
wykonania 45 konstruktorów świata, AI, poleceń, ruchu, walki i zegara animacji.
Normalny Start pozostaje wyłączony. Źródłowe piksele służą porównaniom;
finalne modele i tekstury jakości2026 pozostają do wykonania.

`artifacts/units/build-report-final.json`: Windows64 Mono, 0 błędów,
0 ostrzeżeń, 144110843 bajty, rozdzielczość1920×1080. DLL SHA256
`518838f1952b31309238cbf9187cb00ea4bf0b76a1d882d101d17d60fbb209bb`.
Pełny zestaw przeszedł: 129 testów bez pominięć,
`artifacts/units/full-tests-units-final.txt`. Pierwszą nieudaną próbę zachowano:
fixture miała nieaktualny `decoder_sha256`. Przed zmianą wyłącznie tego pinu
potwierdzono identyczne natywne dowody loadera i sortowania 12/340.

Na tym samym DLL zakończono pięć grup QA pod Wine/Xvfb:

- `artifacts/units/runtime-strict-final/report.json`: trzy kadry 1920×1080,
  cały framebuffer i osiem pełnych obszarów statków ze średnim i maksymalnym
  błędem RGB 0 oraz 100% zgodnych pikseli. Każda sesja zwalnia osiem zajęć
  i kończy się diagnostycznym Application.Quit(0).
- `artifacts/units/objects-regression-final/report.json`: cztery kadry raf,
  RGB 0; `terrain-regression-final/report.json`: trzy kadry terenu, RGB 0.
- `artifacts/units/briefing-regression-final/report.json`: 39 etapów/11 obrazów,
  normalny callback Quit i kod 0.
- `artifacts/units/menu-regression-final/report.json`: 27 etapów/5 obrazów,
  sześć komend, normalny callback Quit i kod 0.

Każda sesja statków porównuje 34 wpisy kolejki z dowodem źródłowym.
29 wpisów statków odczytuje faktyczne `SpriteRenderer.sortingOrder`;
pięć wpisów raf to obliczone deklaracje, a ich przypisania sprawdzono
statycznie i porównaniem obrazu. Nie jest to 34 odczytów właściwości.
Obraz dowodzi kolejności tam, gdzie maski składników się pokrywają.

Kontrole checkera w `artifacts/units/qa-helper-controls-strict/report.json`
przeszły 88/88. Wcześniejsza seria ujawniła brak odrzucenia kilku małych
różnic obrazu; zachowano nieudane próby. Zaostrzono granicę maksymalnego
błędu każdego obszaru statku do 4, bez zmiany Unity. Ponowiony rzeczywisty
player ma błąd 0. Replay UI pozostaje syntetyczny i nie rozstrzyga wejścia OS.

[Paczka statków](../artifacts/units/AncientConquest-Prototype-Ships-Windows-x64-1920x1080.zip)
ma 47071067 bajtów i 182 pliki; SHA256
`d6854c65e8cad75b9ca8be2599159d4fe91effe95ce9662a8a4b4836a2dfbc51`.
Po rozpakowaniu całego ZIP dostępne są `Podglad-statkow.cmd`,
`Podglad-statkow-poludnie.cmd`, `Podglad-statkow-sasiednich.cmd`, launchery
raf i terenu oraz README. Podglądy wychodzą diagnostycznie po 30 sekundach;
QA sprawdzało wariant ośmiosekundowy. Starsze paczki zachowano dla ich DLL.

Źródła: [inicjalizacja statków](MISSION_UNIT_INITIALIZATION_EVIDENCE.md),
[zajętość](MISSION_OCCUPANCY_EVIDENCE.md),
[zasoby TYPE8](UNIT_ANIMATION_ASSET_EVIDENCE.md),
[kolejność świata](UNIT_WORLD_ORDER_EVIDENCE.md),
[pozostałe klasy sceny](MISSION_SUPPORT_OBJECTS_EVIDENCE.md).
Pełne StartGame, symulacja, finalna oprawa i testy natywnego Windows11/laptopa
pozostają nieukończone lub niezweryfikowane.

## Zakończony etap jednego odcinka ruchu

Nowe czyste helpery mają niezależne dowody C#/x86: `ShipMoveRequestInbox`
45 scenariuszy/169 obserwacji/10 kontroli, `PreparedShipMovement` sześć
śladów/186 stanów/180 wywołań/40 kontroli oraz `ShipFrameProgression`
288 porównań. Inbox oddziela pending request od active celu i nie deklaruje
osiągalności. Kinematyka instaluje wyłącznie potwierdzoną trasę source0b
z16,2 do15,3 i zachowuje referencję właściciela siatki. Helper fazy jest
wywoływany w momencie źródłowego ogona ruchu, także w ostatnim kroku.
Publikacja sprite’a wymaga osobnej bramki `LastStepPublishesPose`:
186 porównań stanów obejmuje115 faktycznych publikacji. Oryginalny setter
oraz wybór renderera wykonano bez hooków w45 kontrolach. Przykładowo po
kroku3 wewnętrzna faza wynosi21, a widoczna klatka nadal20; sam wzrost
licznika nie publikuje nowej pozy.

`tools/stage_ship_movement.py` przygotowuje SHIP_A1110/maska0x83,
pozycje0…87, 264 odniesienia i 152 bitmapy. Manifest i RGBA są oddzielone
od poprzednich statycznych ośmiu statków. Osiem nowych testów stagingu
sprawdza dobór, każdy region atlasu, paletę/pokrycie i kontrakt zapisu.
Same dane nie potwierdzają integracji renderowania playera.

`--ship-movement-reference` włącza podgląd jednostek i porusza wyłącznie0b. Warunki są kontrolowane: wind0/heading5,
upgrade0, pełne zdrowie, źródłowe pending/counter i kwant40ms. Diagnostyczne
zatrzymania etapów pozwalają porównać obrazy; nie są pomiarem pełnego tempa
oryginału. Normalny Start pozostaje wyłączony. Nowy pełny zestaw143 testów
przeszedł bez pominięć w45.431s (`artifacts/movement/unittest-final.log`).
Build Windows ma0 błędów/ostrzeżeń,146184267 bajtów
(`artifacts/movement/build-report.json`), DLL SHA256
`4d31ab124c18d6d0d0e935e0325d79782bfac160cf2d56aad1945e9a9903504c`.
Sprawdzono73 metadane i27 C# bez brakujących meta lub powtórzonych GUID:
`artifacts/movement/source-integrity.json`.

`artifacts/movement/runtime-complete-final/report.json` potwierdza dwie sesje:
pełną trasę44 kroków z etapami0/1/3/5/29/30/44 oraz przerwanie po kroku1,
z etapami0/1. Dziewięć kadrów ma cały RGBmean/max0, exact1 i po3 pełne
regiony statków0b/0c/0d z błędem0. Cleanup zwolnił8 i9 zajęć; oba procesy
wyszły diagnostycznie z kodem0. W finalnej kontroli trzy pierwsze zrzuty
first-pixel/before-transfer/transferred były jeszcze poprzednio przedstawionymi
klatkami: checker je odrzucił, a właściwe obrazy uzyskał w ograniczonym oknie1s.
Pozostałe sześć zrzutów przyjęto przy pierwszej próbie. Pierwszy nieudany
`runtime-final` i pośredni `runtime-strict-final` zachowano jako historię.

Dodatkowa kontrola wykryła, że duplikat statku poza aktualnymi ROI mógł przejść
poprzednią bramkę średniego błędu. Końcowy checker wymaga także globalnego
max≤4; w nowym realnym przebiegu wszystkie błędy wynoszą0. Główna seria318
kontroli obejmuje306 kontroli pikseli/logów,9 mocków capture, ghost i2 granice
globalnego błędu. Raport: `artifacts/movement/qa-helper-controls-complete/report.json`.
To poprawki QA bez zmiany C# lub DLL, a nie dopasowanie gry do oczekiwanego obrazu.

Regresje `artifacts/movement/units-regression/report.json` (3 kadry/8 obszarów),
`objects-regression/report.json` (4 kadry) i `terrain-regression/report.json`
(3 kadry) przeszły z RGB0 na tym samym DLL. Regresje UI też przeszły:
`artifacts/movement/briefing-regression/report.json` ma39 etapów/11 obrazów,
a `menu-regression/report.json`27 etapów/5 obrazów/6 komend; obie sesje kończą
się normalnym callbackiem Quit i kodem0. Wszystkie sześć grup wskazuje DLL4d31…;
po buildzie nie zmieniano C#. Paczka nowego etapu jest gotowa.
129 testów, DLL518838… i paczka Ships powyżej są historycznymi dowodami
statycznego etapu.

Źródła: [request](SHIP_ORDER_EVIDENCE.md), [kinematyka](SHIP_MOVEMENT_EVIDENCE.md),
[klatki i staging](SHIP_MOVEMENT_ANIMATION_EVIDENCE.md),
[zegar](SHIP_MOVEMENT_CLOCK_EVIDENCE.md), [pogoda](SHIP_MOVEMENT_WEATHER_EVIDENCE.md).
Nie zaimplementowano ogólnego pathfindingu, sterowania, AI, walki, zmian pogody
ani całego świata; oprawa2026 i natywny sprzęt docelowy pozostają otwarte.

[Paczka ruchu](../artifacts/movement/AncientConquest-Prototype-Movement-Windows-x64-1920x1080.zip)
ma 46980327 bajtów i 184 pliki, SHA256
`fd40fb7f1efe78ded0baff8d703c45e0c9c0a4401cd004052da6929ed24d7ad3`.
Siedem launcherów obejmuje nowe `Podglad-ruchu.cmd` i
`Podglad-przerwania-ruchu.cmd` oraz pięć poprzednich podglądów.
`README-ETAP-RUCHU.txt` opisuje kontrolowane warunki. Normalny EXE pozostaje
menu/briefingiem z wyłączonym Start gry. Manifest:
`artifacts/movement/prototype-package-manifest.json`. Dwie niezależne kontrole
CRC ZIP i SHA256 każdego zdekompresowanego pliku przeszły.


## Zakończony etap sąsiednich celów i obrotu

Nowy `ShipAdjacentMovement` korzysta z `ShipAdjacentPlanner`,
`ShipAdjacentQuery`, `ShipTurnProgression` i wcześniejszego helpera forward.
Przy początkowym0b `(16,2)`, heading5, dopuszcza E/NE/W/SW/S/SE; N/NW
mają źródłowe flagi8/0x308 i pustą trasę. NE nie jest odrzucane za sam
nieprzejezdny teren boczny. Plan C# to zamknięta projekcja tej inicjalizacji,
bez ogólnego algorytmu55c9a0, dalszych rozkazów lub swobodnej mapy.

Porównania rzeczywistego C# z x86: query7120 i23 kontrakty, planner8 i18
kontraktów, turn3776, kinematyka38 śladów/1271 stanów/1233 wywołań/587
publikacji i42 kontrakty. Dodatkowe256 wywołań całego MoveShip potwierdza,
że kończący obrót call nie rezerwuje i nie rusza piksela. Source sprite+81
zaczyna0; przy counter2 stored frame może wynosić47 przy drawn20.
`LastStepPublishesPose` steruje aktualizacją istniejących rendererów.
`SourceShipPoseReference` przejął dotychczasowy loader atlasu88 póz,
Point/pivot/offsety i lokalny cleanup. Dispose jest idempotentny; po detachu
rendererów usuwa swoje sprite’y i atlas. Poprzednia diagnostyka odcinka
korzysta z tego samego loadera, z zachowaniem starego kontraktu logów.

Nowy driver planuje przy counter1 i wywołuje kroki odcounter2 z pending1,
kwantem40ms, kontrolowanym wind0/heading5/upgrade0. Zatrzymania etapów
zamrażają capturedTime. To jawny przygotowany harmonogram: oryginalne
ProcShipsWork może wykonać planner i MoveShip w tym samym counter.
Nie jest to port pełnego Life ani potwierdzenie czasu gry. Opublikowane
worldX964…1092, worldY68…196 i frame0…55 zachowują sprawdzoną rangę
0b względem pozostałych statków i raf; poza tym guardem wymagany jest
nowy dowód globalnego sortowania.

`artifacts/adjacent/build-report.json`: Windows64Mono,146207467 bajtów,
0 błędów/ostrzeżeń. DLL SHA256
`b4d0da08e2f6e1ec51e751de12a45c7057d4df0e6f827ace11576d15ffbb7cd1`.
`artifacts/adjacent/unittest-final.log`:155 testów bez pominięć w58.160s.
`source-integrity.json`:79 meta/33 C#, bez brakujących meta, błędnych GUID
i duplikatów. Po buildzie nie zmieniano C#.

Pilotaż `artifacts/adjacent/runtime-first-h0/report.json` przeszedł:
8 kadrów1920×1080 i24 obszary statków mają RGBmean/max0, cleanup8 i exit0.
Pełne `artifacts/adjacent/runtime-final/report.json` jest PASS:10 sesji,
53 kadry/159 ROI RGBmean/max0. Sześć dojazdów,dwie odmowy i dwa przerwania;
cleanup8 w9 sesjach i9 w halt-reserved,każdaexit0. Odrzucono22 próby przed
zgodną prezentacją;tylko8 dokładnie odpowiada wcześniejszym zapisanym etapom.
Regresje starego manewru2/9,statków3,raf4,terenu3,briefingu39/11 i menu27/5/6
przeszły na tym samym DLL;UI zakończone zwykłym Quit0.
Nowy ZIP ani podgląd do prezentacji nie są zamawiane. Na wyraźne polecenie
użytkownika kontynuować kod/testy/dokumentację bez automatycznego pakowania
i generowania podglądów. Wewnętrzne framebuffer’y są dowodami QA.
Poprzednie143 testy/DLL4d31…/paczkaMovement pozostają historyczne.

Dowody: [runtime](SHIP_ADJACENT_RUNTIME_VALIDATION.md),
[nawigacja](SHIP_ADJACENT_NAVIGATION_EVIDENCE.md),
[ruch sąsiedni](SHIP_ADJACENT_MOVEMENT_EVIDENCE.md),
[obrót](SHIP_TURN_ANIMATION_EVIDENCE.md),
[czas i ranga składników](SHIP_ADJACENT_WORLD_EVIDENCE.md).
Normalny Start pozostaje wyłączony. Pełne pathfinding/Life/sterowanie/AI,
walka i pogoda świata, nowa oprawa2026, natywny Windows11 oraz wydajność
laptopa użytkownika pozostają nieukończone lub niezweryfikowane.


## Zakończony etap dłuższych tras

`ShipRoutePlanner` korzysta z `SourcePathfinder` i `SourceWaveField`,
odtwarzając źródłową linię/falę na mapie0/−1. Adapter świata jest ograniczony
do początkowego0b `(16,2)`, heading5, mode0/restriction0/priority0 oraz siedmiu
minimalnych nieruchomych rekordów floty. Lokalna maska nie jest globalną
maską wszystkich statków; teren celu jest przywracany po lokalnym blockerze.
Dlatego cel zajęty0d w19,4 może dostać plan, a ruch musi osobno zaczekać.

Dowody C#/x86: fala749 pól/390267 komórek i9 kontroli, planer374 przypadki
(140 z falą) i6 kontroli, adapter576 celów (362 plany/214 bez trasy) i9 kontroli.
`ShipRouteMovement` ma32 ślady/1593 stany/1561 wywołań/1046 publikacji/
248 mutacji siatki i57 kontroli API. W zakresie pending1/2/3/7 jest24 dojazdów,
4 odmowy i4 timeouty celu zajętego. `IsComplete` wymaga końcowej komórki,
kotwicy i zatrzymania; samo state0 lub koniec pośredniej tablicy nie oznacza
osiągnięcia active celu. Stan `stalled` jest logowany osobno.

`SourceSpriteDepthQueue` zachowuje źródłowe ID21 węzłów oraz historię
SetDepth z55d960.3849 porównań/14 kontroli/3 testy obejmują zmiany, powroty,
remisy, brak zmiany i signed extrema. `SourceCohortOrderReference` wiąże
8 rodziców,8 osobnych cieni i5 rzeczywistych rendererów raf. Rodzice
zachowują lokalną kolejność dodatnich składników; spłaszczenie ma34
renderery. Rejestracja jest po sourceID, rodzic przed cieniem. Zmiana
Y0b na268/324 przecina depth0d/0c i może wymagać zmiany order innych statków.
Nie wolno odtwarzać remisów wyłącznie z końcowego Y lub sortowania po ID.

`ShipRouteReference` replayuje każdą pozycję z `GetLastStepPublication`,
w kolejności `UpdateParent→poses.Apply`; nawet dwie publikacje w jednym call
wpływają na historię kolejki. Potem sprawdza finalny drawnframe/world względem
snapshotu. Log etapu ma31 pól,3 rzeczywiste części0b oraz34 rzeczywiste
odczyty kolejności rendererów, łącznie z pięcioma rafami. Poprzednie29 odczytów
plus5 obliczonych deklaracji pozostają właściwością historycznego etapu.
Własność atlasu88 póz jest wspólna; kolejka nie przejmuje zasobów raf/materialu.

`artifacts/long-routes/build-report.json`: Windows64Mono,146250459 bajtów,
0 błędów/ostrzeżeń, DLL SHA256
`a54b9ea4de6db05a458794758e26b27600f5aa56c9b78c091583e45448b10fba`.
`unittest-final.log`:172 testy bez pominięć w107.491s.
`source-integrity.json`:87 meta/41 C#, bez braków, błędnych lub powtórzonych GUID.
Pilotaż `artifacts/long-routes/runtime-first-bend/report.json` przeszedł:
16 kadrów RGBmean/max0,31 pól stanu i34 rzeczywiste wpisy kolejki.
`artifacts/long-routes/runtime-final/report.json` potwierdza7 sesji:
4 dojazdy, odmowę terenu, zatrzymanie przed zajętym celem i przerwanie
po drugiej rezerwacji.88 kadrów/264 ROI ma RGBmean/max0. Każdy etap
sprawdza31 pól stanu, pełną ścieżkę,21 rejestracji i34 rzeczywiste odczyty
kolejki względem oryginału. Cleanup8 w6 sesjach i9 w ostatniej; exit0 wszystkich.
128 prób obrazu,40 odrzuconych przed ścisłą zgodnością:16 dokładnie
odpowiada wcześniejszym zapisanym etapom,24 nie sklasyfikowano.
Wszystkie siedem grup regresji w `artifacts/long-routes/` przeszło na tym DLL:
`adjacent-regression`10 sesji/53 kadry/159 ROI, `movement-regression`2/9/27,
`units-regression`3 kadry/8 obszarów, `objects-regression`4 kadry i
`terrain-regression`3 kadry z RGB0. Sąsiedzi zwolnili8 zajęć w9 sesjach i9
po rezerwacji, wcześniejszy odcinek8/9; wszystkie procesy exit0.
`briefing-regression`39 etapów/11 obrazów i `menu-regression`27 etapów/
5 obrazów/6 komend zakończyły się normalnym callbackiem Quit0.
Wszystkie raporty mają DLL a54b9e…; po buildzie nie zmieniano C#.

Clock pozostaje jawnym harmonogramem planner1→Steps2… przy pending1,
wind0/heading5/upgrade0 i kwancie40ms. Każdy hold1.25s jest wyłączony z czasu.
Natywny Work może planować i poruszać w tym samym counter. Pełne Life,
retry/pośredni cel, inne tryby i dynamiczny świat nie są przeniesione.
StartGame pozostaje wyłączony; brak pełnego sterowania/AI/walki/pogody,
finalnej oprawy2026 i testów natywnego Windows11/docelowego laptopa.
Nie generować nowego ZIP ani podglądów do prezentacji; wewnętrzne kadry
służą wyłącznie QA. Publikowanie środowiska pozostaje poza autoryzacją.

Dowody: [runtime](SHIP_ROUTE_RUNTIME_VALIDATION.md),
[fala](SOURCE_WAVE_FIELD_EVIDENCE.md),
[planer pól](SOURCE_PATHFINDER_EVIDENCE.md),
[adapter świata](SHIP_ROUTE_PLANNER_EVIDENCE.md),
[ruch](SHIP_ROUTE_MOVEMENT_EVIDENCE.md),
[kolejka](SOURCE_SPRITE_DEPTH_QUEUE_EVIDENCE.md),
[work/retry](SHIP_ROUTE_ORDER_EVIDENCE.md).


## Zakończony etap normalnych rozkazów0b — 2026-11-03

`ShipMoveOrder` jest osobnym czystym właścicielem zmiennego stanu rozkazu
oraz normalnego ruchu. Historyczne `PreparedShipMovement`,
`ShipAdjacentMovement` i `ShipRouteMovement` pozostają zamrożone.
`SourceWaveField` dostał wejście FillFromOrigin dla nearest;stara gałąź
Fill ma ponowną regresję749 pól/390267 komórek. Nie dodawano zależności,
scen,prefabów,shaderów ani nowych zestawów stagingu.

Aktualne dowody pure native/C#:nearest1380/9 kontroli,planer bieżącego
origin228/13,idle4232/456 publikacji/56 zwolnień plus77 seed i96 wholeMove.
Koordynator ma7 śladów:956 samples (7initial/8request/941Tick),65 kolumn
porównania,446 publikacji i62 zapisów grid;35 API guards.
Raport `artifacts/order-cycle/lifecycle/csharp-validation-final.json`
wykonuje świeży oryginał równy fixture,a następnie faktyczny checked C#.
`native-consistency-verification.json` osobno sprawdza5777 source-entry
zdarzeń i wejścia/efekty każdej operacji.

Promocja i Work są przed ruchem w tym samym counter. Źródłowy Work
utrzymuje active400 po usunięciu active80;normalny idle nadal wykonuje RNG.
Początkowy RNG jest unchecked(sessionSeed×instanceId),nie stałym seedem
każdej misji. Próby>50 używają tego samego RNG co idle. Cache przeszkód
persistuje między planami,a odpowiedni ruchomy stop może go wyczyścić.
Nie zakładać,że cache zawsze przeżywa stop albo zawsze jest usuwany.

`Motion.IsComplete` sprawdza aktualny endpoint i kotwicę w state0;
`RequestedTargetReached` osobno porównuje aktywny target. Dla18,2 źródłowa
ścieżka17,2 nie oznacza dojścia do żądanego celu:po180 Tick active80 zostaje.
20,4 pokazuje stop-request102/active-clear103 podczas state4/przed fizycznym
anchor;nie utożsamiać active-clear z zakończeniem ruchu. Pierwszy18,5 ma
state0@87,stop98,clear99,idle-published101. Drugi request18,5→16,4 następuje
jako nowy sample przy tym samym counter101,bez powtórzenia poprzedniej publikacji.

Driver po każdym request/Tick odtwarza wszystkie publikacje do istniejącej
kolejki i rendererów. Dopuszcza normalne idle56…87 oraz nadal rozróżnia
stored/drawn. Holdy1,25s wyłączone z kwantu40ms są narzędziem QA,nie dowodem
tempa pełnej gry. Drugi request wymaga CanRequestMove+publikacji idle;
busy replacement nie jest portowane. Limit stop-at działa przed kolejnym
requestem i normalnym zakończeniem,bez dodatkowego Tick.

Build etapu rozkazów `artifacts/order-cycle/build-report.json` ma146287259 bajtów,
0 błędów/ostrzeżeń,DLL
`6c646f8c6313ff0005d51dffda7596e986dad0101f6a2432f831474229bc4773`.
`unittest-final.log`:discovery182PASS/0skip/151.698s;osobno
`qa-controls-final.log`:7PASS/0skip/6.221s.`source-integrity.json`:
46C#/92meta bez braków,błędnych lub powtórzonych GUID. Po buildzie C# bez zmian.
`runtime-first-normal/report.json`:12 kadrów/36 ROI RGB0,cleanup8/exit0.
Pierwszy końcowy run został przerwany restartem środowiska i zachowany.
`runtime-final-resumed/report.json` po wznowieniu potwierdza4 sesje/53 kadry/
159 ROI RGBmean/max0. To normalny rozkaz,nearest18,2 do180 Tick,dwa kolejne
rozkazy i halt46;54 pola,path/cache,21 rejestracji na sesję oraz34 faktyczne
odczyty kolejki rendererów na etap (1802 łącznie). Cleanup8/8/8/9,exit0 wszystkich sesji.
63 próby obrazu obejmują10 odrzuconych:6 ma dokładne odpowiedniki
wcześniejszych zapisanych checkpointów,4 są niesklasyfikowane. Pilot12 kadrów nie jest doliczany do53.
Agregat:`artifacts/order-cycle/runtime-aggregate.json`.
Na tym samym DLL przeszły4 grupy regresji pod `artifacts/order-cycle/`:
`route-regression`:wyłącznie depth-cross+halt-second-reservation,2 sesje/
28 kadrów/84 ROI RGB0,cleanup8/9;`movement-regression`:2 sesje/9 kadrów/
27 ROI RGB0,cleanup8/9;`briefing-regression`:39 etapów/11 obrazów;
`menu-regression`:27 etapów/5 obrazów/6 komend. Wszystkie exit0,a obie
sesje UI mają zwykły ApplicationQuit0. `regression-aggregate.json` wiąże
te cztery raporty. Nie przenosić na nowy DLL całych dawnych7 grup ani
wszystkich wcześniejszych tras;ich historyczne raporty zachowują własny zakres.

Helper użyty do playera ma SHA
`09da3d8365a0df18f7cab10afc64eecb0266351bdb443a2d277ba0314b5e3cf2`
i jest zachowany jako `artifacts/order-cycle/qa-helper-used-for-runtime.py`.
Po runtime poprawiono wyłącznie selektor granicy stop-at przy idle/drugim
request;bieżący helper
`12a2afab7237eb94fab0685c411a4ab07812ea0296d22ef95cff1440a7ba3d4c`
ma7 testów. Fingerprinty wszystkich4 kanonicznych zestawów checkpointów
pozostały identyczne (12/10/23/8),C# pozostał bez zmian. Nie opisywać7
osobnych testów jako jednego pełnego przebiegu189 testów.

Normalny Start pozostaje wyłączony. Pełne Life,inne tryby i aktorzy,dynamiczny
świat,sterowanie gracza,AI,walka,pogoda,save/load,finalna oprawa2026 oraz
natywny Windows11/laptop pozostają otwarte. Nie generować ZIP,automatycznych
podglądów do prezentacji ani publikować. Wewnętrzne framebuffery są dowodami QA.

Dowody: [koordynator](SHIP_MOVE_ORDER_EVIDENCE.md),
[planer bieżący](SHIP_REPLAN_PLANNER_EVIDENCE.md),
[nearest](SOURCE_NEAREST_PATHFINDER_EVIDENCE.md),
[idle](SHIP_IDLE_ANIMATION_EVIDENCE.md),
[runtime](SHIP_ORDER_RUNTIME_VALIDATION.md),
[kontrole QA i audyt](SHIP_ORDER_QA_EVIDENCE.md).


## Zakończony etap predykatu masek kursora — 2026-11-03

`ShipPointerMask` jest czystym przeniesieniem virtual4e06c0,lookup5431d0
oraz bit test5575d0. Nie uruchamia world pickera49a580,konstruktora statku,
UI ani InputSystem. Dane type18 są oddzielone od renderowanej alfy.
Coarse precision0 zwraca true przed geometrią;precise wybiera storedFrame−32
dla32…55 albo byte(heading×3) dla pozostałych normalnych klatek. Heading
w zakresie0…7,stride wyrównany do8 bitów,MSB po lewej,int32wrap odejmowania.
Konstruktor klonuje24 maski i nie przechowuje tablic wywołującego.

`tools/stage_ship_picking.py` sprawdza hash EXE/OBJECTS.DKX/DKD i weryfikuje
geometrię względem type8. Siódmy zestaw `ShipPickingGenerated` ma96 masek
(24×A1/H1/B4/G4),schema1 manifest i52800B `ShipHitMasks.bytes` o SHA
`60f3696904880fa4c4a51da2094f96145b30859013463369d1b953aebf3ba240`.
Staging jest idempotentny,odmawia nadpisania zmienionego wcześniejszego
payloadu także przy replace-generated;Editor build preflight wymaga zestawu.
Pozostałych sześciu zestawów,grafiki,scen,shaderów ani input nie zmieniano.

Nowy predykat ma432428 actualnative/C#calls:423960 pełnych wyników pikseli
z96 źródłowych i24 syntetycznych płaszczyzn oraz8468 osobnych punktów.
13 API guards,checked/warnaserror C#,świeży native równy fixture i5 testów
celowanych/0skip/14.360s PASS. Report:
`artifacts/world-input/picking/mask-csharp-validation-final.json`.
Nowy build `artifacts/world-input/picking/build-report.json`:
146364475B,0 błędów/ostrzeżeń,DLL
`e211062e1098162e28bc1dcdf66ef9851a8dbfb2666f18d486b6e7e4443e2e89`.
47 C#/96 meta bez braków,błędnych i powtórzonych GUID,C# po buildzie bez zmian.

`unittest-final.log` tego etapu przerwano SIGINT na prośbę użytkownika.
Nie opisywać go jako194PASS. Świeży `unittest-resumed.log` ma194PASS/
0skip/181.146s. `order-regression/report.json` na nowym DLL potwierdza
normalny rozkaz12 oraz dwa polecenia23,czyli2 sesje/35 kadrów/105 ROI
RGBmean/max0. Zgodne54 pola,path/cache/RNG,21 rejestracji na sesję,
1190 faktycznych odczytów kolejki;cleanup8/8 exit0.45 prób obrazu obejmuje
10 odrzuconych:tylko7 dokładnych wcześniejszych checkpointów i3
niesklasyfikowane. Wszystkie80 PNG zbadano niezależnie po SHA zakodowanego
pliku oraz po dekodowaniu. To regresja starego ruchu,nie walidacja nowego
wejścia/pickera. Poprzednie182+7 testów i53 kadry należą do zakończonego
DLL6c646… i zachowują własny historyczny zakres.

Pozostają world query,sąsiedzi,fog,sloty i własność,reguły zaznaczania
oraz group command,przekazanie actor action20,integracja InputSystem
ze źródłowym światem oraz wizualizacja wyboru. Read-only dowód1206
zapytań oryginału jest w [WORLD_PICKER_ORDER_EVIDENCE.md](WORLD_PICKER_ORDER_EVIDENCE.md);
na końcu tamtego etapu world picker C# nie był jeszcze wdrożony. Nie włączać zwykłego Start
na podstawie maski. Pełne Life/AI/walka/pogoda/save/oprawa2026 oraz natywny
Windows11 i docelowy laptop pozostają otwarte. Bez ZIP,podglądu i publikacji.
[Dowód masek](SHIP_POINTER_MASK_EVIDENCE.md).
[Stan historycznej pauzy](SHIP_POINTER_RESUME.md) nie zastępuje bieżących raportów.


## Bieżący etap ograniczonego world pickera — 2026-11-03

`ShipWorldPicker` przenosi zwykły ship-slot branch49a580 na24×24 przy
kontrolowanym braku fog i pustych pozostałych slotach. `describe` dostarcza
niemutowalny `ShipPointerPose(mask,publishedWorldX,publishedWorldY,
storedFrame,heading,runtimeClassTag)`. Dopuszczone normalne klasy200…211.
Kandydaci:centrum,następnie źródłowa tablica właściwego brzegu/narożnika.
Pierwszy trafiony zwracany po referencji ownera;nie deduplikować current/
reservation ani sortować według renderera. Picker nie filtruje strony gracza,
nie zmienia siatki i poza callbackiem nie alokuje na query.

Actualfreshnative==fixture,a potem checked/warnaserror C#:
1206 queries,5665 uporządkowanych wizyt,21 API guards,2 targetedPASS/1.701s.
Dowód:`docs/WORLD_PICKER_ORDER_EVIDENCE.md`,raport
`artifacts/world-input/picking/world-picker-csharp-validation.json`.
Nie jest to pełna inicjalizacja ani wybór wszystkich45 obiektów.

`ShipPickingReference` wiąże8 istniejących actorów i dotychczasowy siódmy zestaw masek.
Dla ruchomego0b używa aktualnego `Snapshot.Motion`:opublikowanej pozycji,
stored frame i headingu,nie surowego world ani drawn frame. Obserwuje
też current/reservation właścicieli. Odczyt przed/po query sprawdza brak
mutacji siatki. `ShipOrderReference` ma opcjonalny callback checkpointu;
bez niego dotychczasowa diagnostyka rozkazów zachowuje swój zakres.
Nowy tryb `--ship-picking-reference` korzysta z tych samych argumentów
order-target/next/stop/sessionSeed,wyklucza inne diagnostyki ruchu i replay UI.
Nie ma nowego input flow ani wyboru lub wizualizacji zaznaczenia.

Build `artifacts/world-picker/build-report.json`:Windows64Mono,
146377147B,0 błędów/ostrzeżeń,DLL
`a706aa5e9d9a5966b78c84bc1eace6f669f655a0e94601f82aeb2002e5305409`.
49 C#/98 meta bez braków,błędnych i powtórzonych GUID;7 zestawów Resources
bez zmian,C# po buildzie bez zmian. `unittest-final.log`:196PASS/0skip/
175.263s;osobno7 nowych testów helpera QA PASS/6.968s,nie203 w discovery.
`runtime-first-normal/report.json`:12 kadrów/306queries/96bindings PASS.
`artifacts/world-picker/runtime-final/report.json`:4 scenariusze/53 kadry/
159 ROI RGBmean/max0,1353queries i1243 rzeczywiste wywołania predykatu;
57 queryrows zachowuje duplikaty właścicieli.424actorbindings,53 pełne
kontrole niezmienności zajętości576 komórek i1802 rzeczywiste odczyty kolejki.
Cleanup8/8/8/9 exit0 wszystkich sesji.58 prób obrazu/5 odrzuconych:
4 dokładne wcześniejsze checkpointy i1 niesklasyfikowany.111 PNG audytowane
niezależnie jako zakodowane pliki oraz po dekodowaniu.
`qa-runtime-final-independent-audit.json` potwierdza te liczby;pilot12/306/96
jest osobnym wynikiem i nie jest dodawany do53.
Osobne7QA: `artifacts/world-input/picking/picking-qa-targeted-tests.log`.
Na tym samym DLL przeszły dokładnie2 grupy regresji:
`artifacts/world-picker/legacy-order-regression/report.json`:stary
`--ship-order-reference` normal z null obserwatorem,1 sesja/12 kadrów/
36 ROI RGBmean/max0,cleanup8exit0;nowy prefix query jest nieobecny.
`menu-regression/report.json`:normalny bootstrap,syntetyczny InputSystem
27 etapów/5 obrazów/6 komend,normalny ApplicationQuit0. Nie rozciągać tych
wyników na wszystkie starsze regresje ani input rozgrywki lub natywny OS.

Pozostają pozostałe sloty/fog,reguły wyboru/pendingselection/drag,
membership i komendy grupowe,InputSystem oraz selectionvisual.
[Źródłowy dowód membership/ruchu](WORLD_MEMBERSHIP_MOVEMENT_EVIDENCE.md)
wykonuje8 oryginalnych śladów/1212 snapshotów/1192Tick i rozróżnia5c/5e,
action41 i skutki cache/map. To source-only;żadne grupy C# nie są tym ukończone.
Normalny Start nadal wyłączony;pełne Life/AI/walka/pogoda/save/oprawa2026,
natywny Windows11 i laptop pozostają otwarte. Bez ZIP,podglądu i publikacji.
Dowody:[adapter](WORLD_PICKER_ORDER_EVIDENCE.md),[runtime](WORLD_PICKER_RUNTIME_VALIDATION.md).


## Aktualizacja — wejście świata, 2026-11-03

Finalny DLL:9402081fe31ba5135512f95ea385ee867d75d2c26a03f0f6060dde352d17de8a. BuildWindowsMono146968843B0/0;57C#/109meta;8 stagingów.
`--ship-pointer-reference` to szósty wykluczający się diagnostyczny tryb ruchu.
`--ship-pointer-input-replay` wymaga tej flagi;`--ship-pointer-replay-two-orders`
dodaje drugi cel. Normalny Start pozostaje wyłączony.

WorldPointerInput obsługuje onEvent i cykl urządzenia/fokusu. ShipPointerReference
łączy maski/hover,ShipPointerCommands,ShipSelectionProgression,
PointerCursorProgression i niezmieniony ShipMoveOrder. ShipPickingReference
udostępnia sprawdzony katalog masek i odczyty pozycji bez logowania readiness.
Nie dodano asmdef,pakietów,scen,prefabów ani shaderów.

ShipPointerVisualReference renderuje selector/health jako osobne depth1020
po34 rendererach świata. Confirm ma46,kursor32767;wszystko korzysta z URP/Point.
Kamera referencji ma960×540 pikseli źródła w1920×1080,origin9,0.
To kamera diagnostyczna,nie dowód pełnego oryginalnego FOV.

Osobne bramki fizyki i CursorLife mają40ms. Pełny RunApp,urgent queue,Sleep,
network i względna kolejność wszystkich systemów pozostają nieprzeniesione.
Audiooff,NoFog,pozostałe sloty puste;sterowany0b i7 statycznych peerów.
[Kontrakt](WORLD_POINTER_INPUT_IMPLEMENTATION.md) i[walidacja](VALIDATION.md).
