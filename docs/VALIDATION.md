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

# Walidacja — kohorta świata i player,2026-11-04

Następny dowódUI również ukończony: [QUEUED_UI_WORLD_EVIDENCE.md](QUEUED_UI_WORLD_EVIDENCE.md).
12cases2400frames48requests7344states zgodne x86/C#/shippingDLL;2testPASS107.791s.
Razem10testów w dwóch zestawach,330discovery bezfullrun. WPMOVE type8 znaleziony
w controlm:21części/36×29,cyfryWPNUM iWPMOVE,offsety/SHA w discoveryJSON;
bez graf.konstruktora lub nowychobrazów. Dalej adapterjawnychsłów/Shift+markery/QA.

Aktualny raport: [QUEUED_WORLD_INTEGRATION.md](QUEUED_WORLD_INTEGRATION.md).
C#world100/2 pełny:50cases5536frames16608actorstates/10API;nie replay pakietów.
Strict1001 z prawdziwym310:31cases1796frames5388states/20API. Mixedprefix/group
order4cases.8testPASS0skip188.276s,3nowe+5legacy mutations,clock1287.
328discovery bezfullrun. Stare fixture pozostają niezmienione;ich testowe widoki
pomijają310,które dawniej ret-boundary nie wykonywało. Nowe widoki są pełne.
Shipping integrated50+strict31 PASS iregresjeWorld/busyworld/busyactor/UI/restore/
live10827+130planners/task1001/task1002.275frozen73CS131meta;World1zmieniony.
Unity6000.3.27f2 Windows64Mono152977451B0/0,DLL161a875ab0612b2945560d7adcd5f8922e45f56c144e6379b1b96cae683a517e.
Kolejny dowódUIShift12cases2400frames48requests wygenerowany w osobnych źródłowych
UI/world. UI Unity jeszcze nie odblokowane. BezPNG/ZIP/publikacji/aplikacji.
Starsze wyniki poniżej są historyczne.

---

Aktualny raport: [świat100/2 x86 i zgłoszenia dotarcia](FLEET_QUEUED_WORLD.md).
46scen/5416klatek/16386stanów,258wywołań4a1700 (196near/62exact),
24permutacje rejestru,3graniceUI/świat,48jawnych odczytówwave[-1].
Nowy port Arrival w ShipMoveOrder porównany z pakietami źródłowymi,
bez wykonywania C#task/world100/2.2API,3mutantyC# i3instrukcji x86.
6testPASS0skip208.196s(5nowych+clock1287),324discovery;bez pełnego run.
Shipping:nowy16386;task1002;normal1001;world5388;busyworld5088;
busyactor9984;live10827+130planowań;restore7704;UIreplace7248.
Unity6000.3.27f2 Windows64Mono152975915B0warnings/0errors,
DLLb7247a256195d67d51bb91c8db3c8aa02b0270e8147127ae1e7c906d8ea53d55.
275plików zamrożonych,73CS/131meta;1CSzmieniony72bez zmian. Poczta iClock bez zmian.
Pierwszy walidator odrzucił tuple/list metadanych po zgodnych klatkach;
poprawiono wyłącznie normalizację, bez zmiany fixture lub oryginału.
Logi/raporty:artifacts/fleet-queued-world-evidence. Shift i world100/2 pozostają
zablokowane. PełnyLife/AI/Start,oprawa2026,natywnyWin11 i laptop niepotwierdzone.
1920×1080/16:9/fullscreen;bez PNG/ZIP/publikacji/aplikacji/nowych agentów.
Starsze wyniki poniżej są historyczne.

---

Aktualna walidacja:[FLEET_QUEUED_PORT.md](FLEET_QUEUED_PORT.md),port100/2.
Status:Ready with limitations dla ograniczonego czystego C#,nie pełnej gry/UI.
64cases1121states+36setup,19API;freshx86 korpusy55+5+4,20pełnychpól/11520słów.
4testPASS0skip132.663s,5mutantówC#wykrytych;clock1287 zgodny.
319discovery,bezpełnegorun. Worldqueuedguard pełnysnapshotPASS.
Shippingregresje:1001 778;owner2486;world5388;busyworld5088;UIreplace7248;
restore7704;live10827+130planowań. WszystkoPASS na nowym DLL.
Unity6000.3.27f2 Windows64Mono152975403B0warnings/0errors,
DLL8ca1c3b4ccf48ac651a1f3662bc50da32004a0aae2406d1bfe5632e3e367d001.
275plikówzamrożonychprzed/po;73CS/131meta;4zmienione69bez zmian.
Raporty/logi:artifacts/fleet-queued-port. Pierwsze błędyadaptera i mutanta
zachowane;nie zmienianofixture luboryginału. HeadlessALSA bez urządzenia
i znany ComputeBufferGC nie są nowymi błędami kompilacji.
UIShift,world1002bezprefixcontext,300/311,40,fullLife/AI/Start nieaktywne.
Bez dowodu oprawy2026,natywnegoWindows11,laptopa lub wydajności.
1920×1080/16:9/fullscreen. Bez PNG/ZIP/publikacji/aplikacji/nowychagentów.
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

[Zakres](COHORT_WORLD_RESTORE.md),[build](../artifacts/cohort-world-restore/build-report.json),
[shippingDLL](../artifacts/cohort-world-restore/shipping-validation.json),
[testy](../artifacts/cohort-world-restore/targeted-tests.log),
[player](../artifacts/cohort-world-restore/runtime/report.json),
[punkt wznowienia](evidence/milestone-20261104-cohort-world-restore.json).
Ready with limitations dla kontrolowanego odtworzenia,nie pełnego save/load.

---

# Walidacja — stan ruchu i blokujący arbitraż C#,2026-11-04

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

[Zakres i granice](SHIP_STATE_PORT.md),[build](../artifacts/ship-state-port/build-report.json),
[shippingDLL](../artifacts/ship-state-port/shipping-validation.json),
[testy](../artifacts/ship-state-port/targeted-tests.log),
[player regresji](../artifacts/ship-state-port/input-regression/report.json),
[punkt wznowienia](evidence/milestone-20261104-ship-state-port.json).
Stan:Ready with limitations dla opisanego rdzenia C#,nie pełnego save/load.

---

# Dowód blokującego arbitrażu — 2026-11-04

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

Starsze wyniki buildów i C# poniżej pozostają historycznymi dowodami swoich etapów.

---

# Walidacja — normalne ponowienia20,2026-11-04

Stan:**Ready with limitations** dla zdrowych lokalnych0b/0c/0d,metadanych
0/255 i nieblokującego arbitrażu58b==0. Nowy ReceiveNormalCellMove przyjmuje
rozkaz podczas ruchu i nadpisuje rekord26B. Świat odbiera go w źródłowej
fazie poczty. Nie wprowadzono globalnej fazy grup lub zmian rejestracji.
Blokujące bramki,inne zadania,Shift zatwierdzonej grupy i Start nadal poza zakresem.

| Kryterium | Wynik |
| --- | --- |
| Świeży x86 aktorów |PASS:18 przypadków,9984 stany,210 rozkazów,9720 kroków;3335 publikacji,346 zmian grid |
| Świeży x86 świata |PASS:8 przypadków,1696 klatek,5088 stanów,4 pozycje floty;72 odbiory,24 emisje,1088 publikacji |
| API |PASS:12 kontroli odbiorcy i20 świata;checked+/warnaserror+ |
| Testy celowane |PASS:4,0 pominięć,70.211s;świeży x86 i1287przypadków zegara |
| Mutacje |PASS:3 wykryte;pierwszy zapis wygrywa,sztuczne zatrzymanie,natychmiastowy odbiór emisji |
| ShippingDLL |PASS:nowe9984+5088;regresje świata5388,live10827,prepared6795 iownership2486;130 planowań |
| Legacy lifecycle |PASS:7 scenariuszy wcześniejszego obiegu request/promotion/work/motion |
| Build |PASS:Unity6000.3.27f2 Windows64Mono,152955435B,0 błędów/ostrzeżeń |
| Player ponowień |PASS:15 punktów/45 stanów/150 części/510 odczytów/136 publikacji;9 odbiorów/3 emisje;exit0 |
| Regresja InputSystem/Ctrl |PASS:23 punkty/69 stanów/230 części/782 odczyty/136 publikacji/6 pakietów;exit0 |
| Integralność |73C#/131meta;3 istniejące C# zmienione,70 bez zmian;275 zamrożonych plików |
| Zasoby/źródła |78Resources/10 stagingów/9 oryginalnych wejść bez zmian |
| Pełny discovery |Nie ponawiano;zestaw283 testy |
| Inne bramki arbitrażu i pełny Life |Nieprzeniesione;oracle nadal wykonuje kontrolowany Promote+Work zamiast pełnego Ship::Life |
| Cała misja/oprawa2026/Win11/laptop/wydajność |Nieukończone lub niebadane;bez nowego dowodu pikseli |

DLL:`5d15a7030ef4b8b544937ebb293cb8fd182a65cd435251668697be865b6b93ce`.
Wartość58b jest sprawdzana w rzeczywistych śladach x86,nie wymuszana.
Stare API i CanRequestMove pozostają ograniczeniem wejścia UI. Odbiór41
nadal synchronizuje5e przed obiektami. Nowy koordynator nie zapisuje grid.

Nowy player przechodzi jako --ship-fleet-world-busy,przy jawnym rejestrze
fleet/11/12/13 i gotowej poczcie2;to kontrolowane wejścia,nie pełny zimnyStart.
Źródło emituje3 rozkazy w10,a odbiorcy otrzymują je w11. Zasoby póz i zajęcia
komórek zwolnione. Znany wcześniejszy komunikat ComputeBufferGC przy
zamykaniu pozostaje w logach;0/0 dotyczy buildu. Nie zmieniono scen,prefabów,
pakietów lub ustawień. Bez nowych PNG,ZIP,podglądów,publikacji/aplikacji.

[Zakres i adresy](SHIP_BUSY_ORDERS.md),
[build](../artifacts/busy-ship-orders/build-report.json),
[shippingDLL](../artifacts/busy-ship-orders/shipping-validation.json),
[testy](../artifacts/busy-ship-orders/targeted-tests.log),
[player](../artifacts/busy-ship-orders/runtime-busy-final/report.json),
[regresje rdzenia](../artifacts/busy-ship-orders/core-regressions.json),
[punkt wznowienia](evidence/milestone-20261104-busy-ship-orders.json).
Starsze wyniki poniżej dotyczą swoich historycznych DLL.

---

# Historyczny etap — zadania grup w kroku świata,2026-11-04

Stan:**Ready with limitations** dla wybranej gałęzi40ms świata.
`ShipWorldStep` rejestruje flotę i statki w jawnej kolejności między
`SingleStepClock.Begin/Complete`. Poczta jest przygotowana raz przed Life;
nowe emisje grupy oczekują na późniejszy odbiór. Emisja201→odbiór/promocja202
została potwierdzona x86 oraz playerem. Zwykły Start nadal wyłączony.

| Kryterium | Wynik |
| --- | --- |
| Świeży x86 / C# |PASS:31 scenariuszy,1796 klatek,5388 pełnych stanów,24 kolejności rejestracji |
| Poczta i publikacje |PASS:174 odbiory,76 emisji,1462 publikacje;counter,payload i kolejność |
| API |PASS:20 kontroli,checked+/warnaserror+ |
| Testy celowane |PASS:4,0 pominięć,75.531s;3nowe+zegar1287przypadków/63callback/4quantum |
| Kontrole negatywne |PASS:5 wykrytych mutacji;fixture z innym SHA odrzucana |
| ShippingDLL |PASS:powyższy nowy obieg oraz wcześniejsze7086 porównań członkostwa/rozkazów/Ctrl/zadania |
| Build |PASS:Unity6000.3.27f2 Windows64Mono,152954411B,0 błędów/ostrzeżeń |
| Nowy player |PASS:14 punktów/42 stany/140 części/476 odczytów/98 publikacji;3 odbiory/1 emisja;exit0 |
| Regresja InputSystem |PASS:23 punkty/69 stanów/230 części/782 odczyty/136 publikacji/6 pakietów;exit0 |
| Integralność |PASS:73C#/131 unikalnych meta;2 istniejące C# zmienione+1 nowy;70 dawnych bez zmian;275 plików przed/po buildzie |
| Zasoby/źródła |PASS:78Resources/10 stagingów i9 oryginalnych wejść bez zmian |
| Pełny discovery |Nie ponawiano;nowy zestaw280 testów;wcześniejsze wyniki są historyczne |
| Pełny Life i rejestracja misji |Nie dowiedziono;oryginalny Promote+Work działa przez kontrolowaną trampolinę |
| Busy20/35/queued/Shift/AI/Start |Nadal ograniczone lub zablokowane;nie odblokowano UI |
| Piksele/oprawa2026/Win11/laptop/wydajność |Nie badano lub nieukończone;bez nowego RGB0 |

DLL:`392620c155dc41fde6d61f1c30162d7c8c05113cb9ccc4d37f7a6873c71183cf`.
Fixture:`d4fe29c10cbbf7a86232754748d9c52f654bc2792f5be6808071a7972b74f66f`.
Oracle wykonuje rzeczywistą pocztę i dispatch PlaySystem59b828,obieg obiektów
oraz zadanie;pozostałe Ship::Life jest kontrolowaną granicą.Puste kolejki
SystemLife przed/po rejestrze,inne kohorty i pełna inicjalizacja nie są testowane.
Player wymaga jawnej kontrolowanej kolejności i zaczyna z gotową pocztą2.
Nie ustalono rzeczywistej kolejności rejestracji pełnej pierwszej misji.

Jedyny zapis5e jest przez istniejący odbiór41;coordinator nie zapisuje grid.
Nie zmieniono SingleStepClock,ShipMoveOrder,Membership,NormalTask aniGrid.
Siatka8 i3 właściciele póz zwolnione;InputSystem regresji odsubskrybowany.
Znany wcześniejszy komunikat ComputeBuffer przy zamykaniu pozostał w logach;
0/0 dotyczy buildu.Nie powstały PNG,ZIP lub podglądy;bez publikacji/aplikacji.
Pierwsze testy ujawniły błędy normalizacji JSON i nieobserwowalnej mutacji
w harnessie;poprawiono i ponowiono pełny celowany przebieg ze świeżym x86.

[Analiza kolejności i granice](SHIP_WORLD_STEP.md),
[build](../artifacts/world-group-loop/build-report.json),
[shippingDLL](../artifacts/world-group-loop/shipping-validation.json),
[testy](../artifacts/world-group-loop/targeted-tests.log),
[nowy player](../artifacts/world-group-loop/runtime-world/report.json),
[regresja](../artifacts/world-group-loop/input-regression/report.json),
[punkt wznowienia](evidence/milestone-20261104-world-group-loop.json).
Starsze wyniki poniżej dotyczą swoich historycznych DLL.

---

# Historyczny etap — własność zadań grupy,2026-11-04

Stan:**Ready with limitations** dla sprzężonego rdzenia członkostwa i normalnego
zadania100/1. Własność jest w `ShipFleetMembership`;bez nowego zegara/ECS/Update.
**Nie podłączono jej jeszcze do pracy świata ani UI.** Shift zatwierdzonej
grupy,kolejne/queued/busy rozkazy i Start pozostają zablokowane.
Pełna gra i oprawa2026 są nieukończone.1920×1080/16:9/fullscreen.

| Kryterium | Wynik |
| --- | --- |
| Sprzężone źródło x86 |PASS:262 przypadki,2486 punkty,3960 stanów grup;w tym225 par wyborów |
| Pakiety |PASS:3098 dokładnych adresatów/kolejności/payloadów;1566×41,1523×20,9×35 |
| Własność |PASS:osobne zadania/liczniki/zdarzenia,stare indeksy311,zachowany ogon,oddzielne300 i jawne41 |
| API |PASS:26 kontroli,checked+/warnaserror+ |
| ShippingDLL |PASS:nowe2486+legacy2175 członkostwa/1287 odbioru rozkazów/360Ctrl/778Task;łącznie7086 |
| Testy celowane |PASS:13,0 pominięć,350.891s;3nowe+10regresji;świeże x86 |
| Kontrole negatywne |PASS:7 nowych mutacji wykrytych;wcześniejsze mutacje41/20/Ctrl także przechodzą |
| Zegar |PASS:1287 przypadków SingleStepClock,63 warianty callback,4 kontrole quantum |
| Build |PASS:Unity6000.3.27f2 Windows64Mono,152945003B,0 błędów/0 ostrzeżeń |
| Player1920×1080 |PASS:23 punkty/69 stanów/230 części/782 odczyty/136 publikacji/6 pakietów;exit0 |
| Integralność |PASS:72C#/130 unikalnych meta;1 C# zmieniony,71 bez zmian;265 zamrożonych plików |
| Zasoby/źródła |PASS:78 Resources/10 stagingów i9 oryginalnych wejść bez zmian |
| Pełny discovery |Nie powtarzano;274PASS jest historyczne;nowy zestaw ma277 testów |
| Nowy taskWork w playerze |Nie uruchomiono;player to regresja poprzedniego pierwszego rozkazu i Ctrl |
| Pełne FIFO/fazy świata/Shift/busy/queued |Do wykonania;Q w nowym oracle dostarcza tylko41,bez20/35 |
| Nowe piksele/oprawa2026/Win11/laptop/wydajność/OSmouse |Nie badano lub nieukończone;bez nowej deklaracji RGB0 |

DLL:`80f9228368a20ccff99c9970647654936b7987daed707d35bbf74803e62d99e5`.
Fixture:`48832345adada86d26d2c5ed308d1dcb7dbf81a4646590fdd9f8314499e18719`.
Nowy oracle uruchamia membership/task/events i41consumer w jednym silniku x86,
przy jawnych fazach/counter/pending/komórkach/stanie fizycznym. Nie jest to
pełny App/Fleet/Ship Life ani pełna globalna kolejka sterowania.
Nowa własność nie wymusza kończenia zadania przy celu ani resetowania80.

Znany komunikat ComputeBuffer przy zamykaniu pozostał także w tej regresji,
jak w poprzednich logach. Własne wejście,3 właściciele póz i8 komórek zostały
zwolnione.0/0 dotyczy buildu Unity. Brak nowych scen,prefabów,pakietów,
ustawień,assetów lub meta. Bez publikacji,ZIP,PNG i podglądu do prezentacji.
Komentarze C# wskazują adresy/offsety:to inżynieria wsteczna,nie port źródeł C/C++.

[Zakres i następny krok](SHIP_FLEET_GROUP_OWNERSHIP.md),
[build](../artifacts/fleet-group-ownership/build-report.json),
[shippingDLL](../artifacts/fleet-group-ownership/shipping-validation.json),
[testy](../artifacts/fleet-group-ownership/targeted-tests.log),
[player](../artifacts/fleet-group-ownership/input-regression/report.json),
[punkt wznowienia](evidence/milestone-20261104-fleet-group-ownership.json).
Starsze wyniki poniżej dotyczą swoich historycznych DLL.

---

# Historyczny etap — normalny task100/1,2026-11-03

Stan:**Ready with limitations** dla izolowanego rdzenia normalnego zadania
floty. `ShipFleetNormalTask` jest w shippingDLL, ale nie jest podłączony do
zegara świata ani sterowania. Pierwszy normalny rozkaz i Ctrl nadal działają;
Shift zatwierdzonej grupy,kolejne/queued/busy rozkazy oraz normalny Start
pozostają blokowane. Pełna gra i oprawa2026 są w budowie.

| Kryterium | Wynik |
| --- | --- |
| Task100/1 |PASS:124 źródłowe scenariusze/778 snapshotów zadania |
| Przydziały/zdarzenia/zegar |PASS:32B300/311,20B przydziały,LIFO,retained slots,>100 przed pending,uint32/int32 |
| Pakiety taskWork/request |PASS:316 pakietów20 i14 pakietów35;pełne bajty i adresy |
| ShippingDLL |PASS:te same778 snapshotów i20 kontroli API |
| Testy nowego modułu |PASS:3,0skip,55.239s;świeże x86;sześć mutacji kodu wykrytych |
| Pełny discovery |PASS:274 testy,0 pominięć,684.534s |
| Windows64Mono |PASS:Unity6000.3.27f2,152941931B,0 błędów/0 ostrzeżeń;1920×1080 |
| Regresja pierwszego rozkazu i Ctrl |PASS:23 punkty/69 stanów/230 części/782 odczyty kolejki/136 publikacji;6 pakietów;exit0 |
| Integralność |PASS:72C#/130 unikalnych meta;71 wcześniejszych C# bez zmian;265 plików przed/po buildzie zgodnych |
| Zasoby |PASS:78 wcześniejszych plików Resources/10 stagingów i9 oryginalnych wejść bez zmian |
| Integracja taskWork do playera |Nie wykonano;obecna regresja playera sprawdza dotychczasowy pierwszy rozkaz |
| Shift/busy/queued/fazy świata |Do przeniesienia;265 źródłowych41 w fixture jest wejściem kontekstu,nie portem Shift |
| Nowe obrazy/pełny UI RGB0 |Nie generowano ani nie deklarowano;bieżące QA bez PNG |
| Pełna gra/oprawa2026/natywny Windows11/laptop/OSmouse/wydajność |Nieukończone lub niezweryfikowane |

DLL:`6d92c6590832d2ff5908b06bcc061d964662b04080fa1d850077057f55a4516f`.
Fixture:`f85cc3a6aa1a26304faaa5f9f746c239ee6ddb3930936d083e37185a1a849873`.
Wiek i dane członkostwa/slotów/stanu fizycznego są jawnymi wejściami nowego
modułu. Źródłowe procedury fleet/formation/event/serializer wykonują x86;
nie wykonuje się przy tym fizyki lub pełnego Life aplikacji.
Normalne100/1 nie jest usuwane przy dotarciu i nie czyści move-active80.
Obsługa powtórzonego20 wymaga portu arbitrażu zajętego odbiorcy.

Build i regresja playera dotyczą powyższego DLL. Znany komunikat ComputeBuffer
przy zamykaniu pozostał;występuje też w starszych logach. Własne3 właściciele
póz,wejście,selektory i8 komórek zostały zwolnione. Ostrzeżenia wcześniejszych
helperów Pillow zachowano.0/0 dotyczy kompilacji Unity.
Sceny,prefaby,pakiety,ustawienia i wszystkie wcześniejsze C# bez zmian.
Bez publikacji,ZIP i podglądu do prezentacji.

[Zakres i następny krok](SHIP_FLEET_NORMAL_TASK.md),
[build](../artifacts/fleet-task/build-report.json),
[shippingDLL](../artifacts/fleet-task/shipping-validation.json),
[testy celowane](../artifacts/fleet-task/targeted-tests.log),
[pełne testy](../artifacts/fleet-task/full-tests.log),
[regresja sterowania](../artifacts/fleet-task/input-regression/report.json),
[powtarzalny eksport read-only](../artifacts/fleet-task/source/ExportGroupRuntime.java),
[punkt wznowienia](evidence/milestone-20261103-fleet-normal-task.json).
Starsze wyniki pikseli poniżej dotyczą ich historycznych DLL.

---

# Historyczny etap — pierwszy rozkaz floty z kursora i Ctrl,2026-11-03

Stan:**Ready with limitations** dla pierwszego normalnego rozkazu floty w nowym
trybie pointer+fleet-selection+fleet-movement. Wybór,41 przed20,formacja,
promocja,ruch i renderer są połączone.Ctrl przywołuje zatwierdzoną grupę.
Kolejne/queued/busy rozkazy i Shift zatwierdzonej grupy mają jawne blokady.
Praca zadań grupy,pełna gra i oprawa2026 pozostają do wykonania;Start wyłączony.

| Kryterium | Wynik |
| --- | --- |
| Ctrl/plain/right blank |PASS:135 przypadków/360 stanów C#/x86 |
| Pierwszy normalny obieg |PASS:6 źródłowych pakietów,606 stanów,600 ticków,136 publikacji,12 mutacji |
| ShippingDLL |PASS:te same360 i606 stanów;33 kontrole API rdzenia |
| InputSystem w playerze |PASS:23 punkty,69 stanów,230 części,782 rzeczywiste odczyty kolejki |
| Anulowanie i Ctrl w playerze |PASS:wyczyszczenie wyboru i przywołanie wszystkich3 członków bez nowych41 |
| Testy celowane |PASS:10,0skip,87.778s;5 nowych+5 regresji |
| Osobne QA |PASS:2,0skip,12.195s;5 błędnych logów i1 mutacja Ctrl wykryte |
| Windows64Mono |PASS:Unity6000.3.27f2,152935595B,0 błędów/ostrzeżeń;1920×1080 |
| Poprzedni ruch0b |PASS:35 obrazów RGB0,dwa rozkazy,exit0 |
| Poprzedni wybór floty |PASS:46 obrazów RGB0,47 zdarzeń,11 operacji,exit0 |
| Poprzedni renderer3kadłubów |PASS:17 obrazów RGB0,51 stanów,170 części,578 odczytów kolejki,exit0 |
| Integralność |71C#/129 poprawnych unikalnych meta,6istniejących C# zmienionych+1nowy,64bez zmian,10 stagingów |
| Źródła po buildzie |PASS:228 plików bez zmian;rdzeń ruchu/planer/formacja/zasoby niezmienione |
| Pełny UI RGB0 nowego ruchu |Nie badano;nowy test sprawdza stan i rzeczywiste właściwości rendererów |
| Pełny discovery |Nie powtarzano;wyniki starszych DLL są historyczne |
| Zadania grupy/kolejne rozkazy/Shift |Do wykonania |
| Pełna gra/oprawa2026/natywnyWindows11/laptop/OSmouse/fokus |Nieukończone lub niezweryfikowane |

DLL:`5c9be5fd1b4ee4078e188a3ad5c955328dd50f65afc0cd7a6b7c86fe862abf49`.
Wszystkie regresje i nowy przebieg dotyczą tego DLL.98 przyjętych par obrazów
regresji ponownie zdekodowano;RGB jest identyczne.211 PNG ma zweryfikowane hashe.
Nowy UI nie generuje podglądu ani nie deklaruje porównania pełnego kompozytu
pikseli ruchomych selektorów. Bez publikacji i ZIP.

Dowód pierwszego obiegu ma jawną granicę dwóch emulatorów źródła:UI emituje
niezmienione pakiety,drugi silnik odbiera je dla trzech rzeczywistych kadłubów.
Nie jest to pełny połączony Life oryginału. Dla celu18,5 formacja przydziela
0b18,5 /0c20,6 /0d19,4;większy kadłub pozostaje na swojej komórce zgodnie ze
źródłem. Nie dodano sztucznego zakończenia jego move-active.

Komunikat o ComputeBuffer przy zamknięciu występuje również w wcześniejszym
rendererze i sterowaniu;jego log zachowano. Własne3 właściciele póz,selektory,
wejście i8 komórek są zwolnione. Ostrzeżenia Pillow zachowano w logach testów.
Nie są one ostrzeżeniami kompilacji Unity. Sceny,prefaby,pakiety,ustawienia
oraz78 wcześniejszych plików Resources nie wymagały zmiany.

[Zakres i dalszy krok](SHIP_FIRST_FLEET_CONTROL.md),
[build](../artifacts/fleet-control/build-report.json),
[shippingDLL](../artifacts/fleet-control/shipping-validation.json),
[testy](../artifacts/fleet-control/targeted-tests.log),
[QA](../artifacts/fleet-control/qa-tests.log),
[nowy player](../artifacts/fleet-control/runtime-first/report.json),
[regresja0b](../artifacts/fleet-control/pointer-regression/report.json),
[regresja wyboru](../artifacts/fleet-control/selection-regression/report.json),
[regresja renderera](../artifacts/fleet-control/rendering-regression/report.json),
[milestone](evidence/milestone-20261103-first-fleet-control.json).

---

# Historyczny etap — renderer trzech statków,2026-11-03

Stan:**Ready with limitations** dla kontrolnego połączenia normalnych rozkazów,
fizyki i renderowania0b/0c/0d. Nowy --ship-fleet-motion-reference wyświetla
każdą publikację z istniejącego CreateLiveLocal. Cele,grupa i kolejność ticków
są jawne. Wspólne sterowanie myszą i zadania grupy pozostają do połączenia.
Zwykły Start jest wyłączony;pełna gra i oprawa2026 nadal w budowie.

| Kryterium | Wynik |
| --- | --- |
| Grafika0d |PASS:88 pozycji,352 części,224 bitmapy;oryginalny loader/sort i1342 bufory RLE |
| Dotychczasowa grafika0b/0c |PASS:osiem testów wcześniejszego stagingu;domyślne wyjście byte-identyczne |
| Trzy statki w playerze |PASS:dwie sesje250ticków,pending1/normal i7/reverse;34 pełne obrazy RGB0 |
| Stan/sprite/kolejka |PASS:102 wiersze modelu,340 części,1156 odczytów34 rendererów |
| Publikacje |PASS:262 wpisy w źródłowej kolejności,każdy użyty przez pose adapter i native depth queue |
| Kontrakty checkera |PASS:sześć mutacji danych rzeczywistego playera wykrytych |
| Testy celowane |PASS:14 testów,0 pominięć,41.923s;6 nowych i8 regresji |
| ShippingDLL:rdzeń |PASS:10827 stanów,130 wejść planera,149760 komórek pól i33 API |
| Windows64Mono |PASS:Unity6000.3.27f2,152921579B,0 błędów/0 ostrzeżeń,1920×1080 |
| Player:dotychczasowe sterowanie0b |PASS:35 etapów,dwa rozkazy,pełne obrazy RGB0,exit0 |
| Player:dotychczasowy wybór floty |PASS:46 etapów/47 zdarzeń/11 operacji,pełne obrazy RGB0,exit0 |
| Integralność |70 C#/128 poprawnych unikalnych meta;64 dotychczasowe C# bez zmian;10 stagingów |
| Źródła po buildzie |PASS:226 zamrożonych plików bez zmian;rdzeń ruchu i9 wcześniejszych stagingów niezmienione |
| Pełny discovery |Nie powtarzano;starsze wyniki innych DLL pozostają historyczne |
| Wspólny ruch myszą/zadania grupy/Ctrl |Do wykonania |
| Pełna gra/oprawa2026/natywny Windows11/laptop/OS mouse/fokus |Nieukończone lub niezweryfikowane |

DLL:`d1d5a3e476a90eaadfb3ed702003dac24c05608bc26ce46f3b75330e51a7da22`.
Cały zestaw playera korzysta z tego DLL.34 nowe obrazy dowodzą kontrolnego
renderowania trzech ruchomych kadłubów;81 obrazów regresji sprawdza wcześniejsze
tryby wejścia. Wszystkie115 par ponownie zdekodowano i porównano po zakończeniu.
83 PNG dotyczą nowego ruchu;pozostałe regresji. To wewnętrzne QA,bez podglądu
przeznaczonego do prezentacji. Nie publikowano i nie tworzono ZIP.

Nowy atlasH/A3 zachowuje72×72,pancerz,kolejność1/5/7 oraz osobny cień0.
Poprzedni atlasA pozostaje identyczny. Zmieniono5 istniejących C# i dodano
ShipFleetMotionReference;rdzenia ruchu nie zmieniano. Sceny,prefaby,pakiety,
ustawienia i poprzednie73 pliki Resources zachowały hashe. Nowy dziesiąty zestaw
ma jawny stager;instrukcja instalacji dodaje jego sprawdzony krok.
Dwa DeprecationWarning z wcześniejszych helperów Pillow zachowano w logu
testów;nie są ostrzeżeniami buildu Unity i nie były wyciszane.

[Zakres i następny krok](SHIP_FLEET_RENDERING.md),
[build](../artifacts/fleet-rendering/build-report.json),
[rdzeń z DLL](../artifacts/fleet-rendering/shipping-validation.json),
[testy](../artifacts/fleet-rendering/targeted-tests.log),
[pending1](../artifacts/fleet-rendering/runtime-1/report.json),
[pending7/reverse](../artifacts/fleet-rendering/runtime-7-reverse/report.json),
[regresja wejścia](../artifacts/fleet-rendering/pointer-regression/report.json),
[regresja wyboru](../artifacts/fleet-rendering/selection-regression/report.json),
[milestone](evidence/milestone-20261103-fleet-rendering.json).

---

# Historyczny etap — rdzeń rozkazów i ruchu, 2026-11-03

Stan: **Ready with limitations** dla normalnego rdzenia rozkazów i ruchu
lokalnych0b/0c/0d. CreateLiveLocal przyjmuje20,przechowuje26B,promuje rozkaz,
planuje trasę z aktualnych zajęć/grupy symulacji5e i wykonuje ruch. Nowej gałęzi
nie podłączono jeszcze do sterowania/renderowania floty. Zwykły Start pozostaje
wyłączony;pełna gra i oprawa2026 są w budowie.

| Kryterium | Wynik |
| --- | --- |
| Odbiór/promocja/praca/ruch x86/C# |PASS:14 scenariuszy,10827 stanów,10740 aktualizacji |
| Rozkazy/grupy |PASS:45 rozkazów20;36 jawnych wejść grupy po źródłowym41,porównanych przy kolejnym stanie aktora |
| Publikacje/komórki |PASS:1997 frame/world/depth oraz196 uporządkowanych mutacji wspólnej siatki |
| Planer dynamiczny |PASS:130 osobnych wejść;149760 komórek pełnych pól;grupy/stany/cache/RNG |
| API |PASS:33 kontrole adresowania,priorytetu,granic i własności kopii |
| Rzeczywisty DLL Unity |PASS:ten sam zestaw ruchu i planera na hostowym Mono |
| Dawne moduły |PASS:przygotowany ruch6795 stanów/22API także z DLL;legacy0b956 stanów/35API;statyczny planer228/13API |
| Testy celowane |PASS:10 testów,0 pominięć,95.599s;3 nowe i7 regresji |
| Kontrole negatywne |PASS:3 nowe mutanty grup/cache/RNG;3 wcześniejsze mutanty fizyki;zmienione fixture odrzucone |
| Windows64Mono |PASS:Unity6000.3.27f2,148068283B,0 błędów/0 ostrzeżeń,1920×1080 |
| Player:dotychczasowe sterowanie0b |PASS:35 etapów i dwa rozkazy;pełne obrazy RGB0;exit0 |
| Player:dotychczasowy wybór floty |PASS:46 etapów/47 zdarzeń/11 operacji;pełne obrazy RGB0;exit0 |
| Integralność |PASS:69 C#/124 unikalne poprawne meta;67 C# bez zmian;9 stagingów bez zmian |
| Pełny discovery |Nie powtarzano;bieżący zestaw i regresje opisano powyżej |
| Zadania grupy/integracja nowego rdzenia z UI |Do wykonania |
| Pełna gra/oprawa2026/natywny Windows11/laptop/OS mouse/fokus |Nieukończone lub niezweryfikowane |

DLL:`53e9d5004246eb790562ab09b9e55f8c4284400e04487482850fe68e709587eb`.
Wszystkie regresje playera dotyczą tego DLL i dotychczasowych trybów wejścia.
Nowy rdzeń trzech ruchomych ciał sprawdzono osobno z tego samego DLL. Nie
przypisuje się81 obrazom dowodu renderowania nowej gałęzi. Cel pozostaje
1920×1080/16:9/fullscreen;badanie pod Wine nie potwierdza laptopa ani Windows11.

Pierwszy zestaw10 testów wykrył lukę w pokryciu mutacji czyszczenia cache,
a nie rozbieżność poprawnego C# z oryginałem. Log początkowy zachowano.
Dopisano130 kontrolowanych wykonań planera i pełnych pól;finalny zestaw10
przechodzi i wykrywa celową zmianę. Nie osłabiano testu ani reguły źródłowej.
36 obserwacji bezpośrednio po41 i130 zapytań planera nie są wliczone do10827
stanów odbioru/ruchu. Kontrolowana kolejność ticków i cele rozkazów są wejściami;
pełne zadania grupy,formacja połączona z pracą aktorów i scheduler nie są dowiedzione.

Zmieniły się dwa istniejące C#:ShipMoveOrder i ShipReplanPlanner. Po buildzie
C# nie zmieniano. Sceny,prefaby,pakiety,ustawienia,meta i stagingi pozostały
bez zmian. Pierwotne9 plików źródła i73 pliki Resources mają zachowane hashe.
Obrazy służą wewnętrznemu QA;bez publikacji,ZIP ani podglądu do prezentacji.

[Zakres i następny krok](SHIP_LIVE_FLEET_ORDERS.md),
[porównanie C#](../artifacts/live-fleet-orders/csharp-validation.json),
[wykonanie shippingDLL](../artifacts/live-fleet-orders/shipping-validation.json),
[testy](../artifacts/live-fleet-orders/targeted-tests.log),
[regresja wejścia](../artifacts/live-fleet-orders/pointer-regression/report.json),
[regresja wyboru](../artifacts/live-fleet-orders/selection-regression/report.json),
[milestone](evidence/milestone-20261103-live-fleet-orders.json).

---

# Historyczny etap — przygotowane trasy trzech statków, 2026-11-03

Ukończono wspólny rdzeń ruchu rzeczywistych0b/0c/0d na jawnych trasach
wejściowych. `CreatePreparedLocal` korzysta z istniejącego`ShipMoveOrder`,
własnych parametrów kadłuba i żywego opisu zajętości. To nie jest jeszcze
połączenie pakietów26B,promocji,dynamicznego planera i sterowania playera.
Normalny Start i wspólny ruch myszą pozostają zablokowane.
Pełny remake i oprawa2026 są w budowie.

| Kryterium | Wynik |
| --- | --- |
| C#/rzeczywisty x86 |PASS:15 scenariuszy/6795 stanów/6750 wywołań MoveShip |
| Publikacje i zajętość |PASS:1440 publikacji frame/world/depth i300 mutacji;żywa wspólna siatka |
| Parametry0d |PASS:72×72,anchor−4,center36,max52000,acc884→1040 po rezerwacji |
| Kolejność i blokowanie |PASS:odwrócona kolejność aktorów,pending1/2/3/7,mieszane kroki,skręty,przecięcia i zajęty cel |
| Rzeczywisty DLL Unity |PASS:te same6795 stanów,1440 publikacji,300 mutacji i22 API na hostowym Mono |
| Dawny adapter0b |PASS:956 stanów/446 publikacji/62 mutacje/35 API;ponownie actualx86/C# |
| Testy celowane |PASS:7 testów,0 pominięć,26.234s;3 nowe i4 powiązane |
| Kontrole negatywne |PASS:błędna kotwica0d,przyspieszenie i brak resetu retry wykryte;zmieniony fixture odrzucony |
| Windows64Mono |PASS:Unity6000.3.27f2;148065211B;0 błędów/0 ostrzeżeń;1920×1080 |
| Player:sterowanie0b |PASS:35 ujęć;dwa rozkazy;ruch i wejście zgodne z dotychczasową referencją;exit0 |
| Player:wybór floty |PASS:46 etapów/47 zdarzeń/11 operacji;RGBmean/max0;exit0 |
| Integralność |69 C#/124 poprawne unikalne meta;68 dotychczasowych C# bez zmian;9 stagingów |
| Pełny discovery |Nie powtarzano;bieżące testy i regresje opisano powyżej;starsze wyniki są historyczne |
| Promocja/dynamiczny planner/zadania/UI |Do połączenia z nowym rdzeniem |
| Pełna gra/oprawa2026/Windows11/laptop/OS mouse/fokus |Nadal nieukończone lub niezweryfikowane |

DLL:`e261360e02d6e49fd0d56599e2547a529273afc36ab84acc008c3806bf12b142`.
Trasy i początkowy stan ich instalacji są jawnymi wejściami sondy. Nie
przedstawia się tego jako dowodu planowania lub promocji. Nowa gałąź odrzuca
`RequestCellMove`,aby nie użyć planera statycznego0b dla innych kadłubów.
Posiada osobny dowód z DLL;81 kadrów playera sprawdza dotychczasowe tryby,
nie prezentację trzech jednocześnie ruchomych statków. Obrazy służą QA.

Sceny,prefaby,pakiety,ustawienia,meta i zasoby stagingów nie wymagały zmian.
Zmieniono tylko istniejący`ShipMoveOrder` oraz dodano sondę,validator i testy.
Nie zmieniano C# po buildzie. Źródła oryginału pozostają tylko do odczytu.
[Zakres i dalszy krok](SHIP_PREPARED_FLEET_MOTION.md),
[porównanie C#](../artifacts/fleet-motion/csharp-validation.json),
[wykonanie shippingDLL](../artifacts/fleet-motion/shipping-validation.json),
[testy](../artifacts/fleet-motion/targeted-tests.log),
[regresja wejścia](../artifacts/fleet-motion/pointer-regression/report.json),
[regresja wyboru](../artifacts/fleet-motion/selection-regression/report.json),
[milestone](evidence/milestone-20261103-prepared-fleet-motion.json).
Bez publikacji,ZIP i podglądu przeznaczonego do prezentacji.

---

# Historyczne formacje i odbiór — poprzedni DLL

Gotowe są moduły celów normalnej floty wodnej,pakietów20 i odbioru26B.
Nie wykonują jeszcze fizycznego ruchu wielu aktorów ani obsługi kursora.
Tryb wyboru floty nadal blokuje ruch;normalny Start pozostaje wyłączony.
Pełny remake oraz oprawa2026 są w budowie.

| Kryterium | Wynik |
| --- | --- |
| Formacja |2988 dokładnych wyników z3028 prób;40 jawnych ograniczeń kierunku nie wliczono do zgodności |
| Dostępna woda pierwszej mapy |PASS:wszystkie1452 próby;bez ograniczeń kierunku |
| Pełne pola formacji |PASS:5954029 porównanych komórek |
| Pełne fale |PASS:5250 przypadków/373506 komórek;także zablokowany seed i cel−1,−1 |
| Członkostwo→ruch→odbiór |PASS:237 scenariuszy/1050 pakietów/1287 stanów;12 fallbacków255 |
| DLL rzeczywistego builda |PASS:te same formacje,fale,pakiety i odbiorniki na hostowym Mono |
| API |PASS:19 kontroli formacji/fali oraz13 pakietów/odbioru |
| Testy celowane |PASS:11 testów,0 pominięć,168.155s;6 nowych i5 powiązanych |
| Kontrole negatywne |PASS:5 nowych mutacji kodu;3 zmienione fixture odrzucone;regresje dawnego41 i fali również PASS |
| Windows64Mono |PASS:Unity6000.3.27f2;148061627B;0 błędów/0 ostrzeżeń;1920×1080 |
| Regresja playera |PASS:46 etapów/47 zdarzeń/11 operacji wyboru;RGBmean/max0;exit0 |
| Integralność |69 C#/124 poprawne unikalne meta;9 stagingów;66 wcześniejszych C# bez zmian |
| Stary rdzeń fali |Calculate,Fill i FillFromOrigin bez zmian;749 dawnych przypadków ponownie PASS |
| Pełny discovery |Nie powtarzano w tym kroku;dawne wyniki innych DLL są historyczne |
| Fizyczny ruch grupy i integracja UI |Do wykonania |
| Pełna gra/oprawa2026/Windows11/laptop/OS mouse/fokus |Nadal nieukończone lub niezweryfikowane |

DLL:`70768189bb55a5f6328044620711ce36c2b6fa0eea48f7546da54041fe3c67e9`.
Pole grupy symulacji zmienia się po41,a20 ustawia dokładny pending80/26B;
nie jest to dowód promocji ani wykonania ruchu.40 ograniczeń oznacza brak
wybranego źródłowego kierunku w55f800;szczegóły i geometrie opisano w
[SHIP_FLEET_FORMATION.md](SHIP_FLEET_FORMATION.md). Nie udawano ich zgodności.
W playerze nadal działa dotychczasowy tryb pending-selection;nowe moduły są
sprawdzone osobno,z rzeczywistego DLL,przed integracją ze sterowaniem.

Pierwszy build odrzucił33-znakowy GUID nowego SourceFleetFormation.meta.
Poprawiono go do32 znaków i sprawdzono wszystkie124 meta przed buildem02.
Zachowano log pierwszego nieudanego builda. Końcowy build ma0/0;
C# i ustawienia nie zmieniały się po jego wykonaniu. Nowe skrypty nie wymagają
zmian scen,prefabów,pakietów ani dziewięciu zestawów Resources.

[Dowód źródła i DLL](../artifacts/fleet-formation/csharp-shipping-validation.json),
[testy](../artifacts/fleet-formation/targeted-tests.log),
[końcowa regresja](../artifacts/fleet-formation/selection-regression/report.json),
[milestone](evidence/milestone-20261103-fleet-formation.json).
Bez publikacji,ZIP i podglądu przeznaczonego do prezentacji.

---

# Historyczny moduł członkostwa — poprzedni DLL

Ukończono moduł normalnego członkostwa Mode10 oraz komunikatów41.
Ma własny dowód źródłowy i kompiluje się w buildzie Unity;nie jest jeszcze
podłączony do kursora/formacji/ruchu wielu jednostek. Wspólny ruch pozostaje
blokowany,a normalny Start wyłączony. Pełna gra i oprawa2026 są w budowie.

| Kryterium | Wynik |
| --- | --- |
| Przypisanie i odbiór41 | PASS:258 scenariuszy/2175 stanów rzeczywistego x86 i checked C# |
| Rzeczywisty DLL builda | PASS:te same2175 stanów oraz23 kontrole API na hostowym Mono |
| Negatywne kontrole | PASS:zmieniony fixture,brak41−1 i przedwczesna grupa symulacji odrzucone |
| Nowy i powiązane testy | PASS:10 testów,0 pominięć,95.534s;3 nowe +7 regresji źródłowych |
| Windows64Mono | PASS:Unity6000.3.27f2;148052523B;0 błędów/0 ostrzeżeń;1920×1080 |
| Regresja playera | PASS:46 etapów,47 zdarzeń,11 operacji wyboru;RGBmean/max0;exit0 |
| Integralność | PASS:67 C#/122 unikalne meta;66 wcześniejszych C# bez zmian;9 stagingów |
| Pełny discovery w tym kroku | Nie uruchamiano ponownie;sprawdzono nowy i powiązane moduły oraz playera |
| Integracja członkostwa z kursorem i20 | Do wykonania po źródłowej formacji |
| Pełny ruch/pełna gra/oprawa2026 | Nieukończone |
| Natywny Windows11/laptop/OS mouse/fokus | Nadal niezweryfikowane |

DLL:`550622dc91d698fa9b46735ceba20081386f162ef742ede61cee55eac8259bb1`.
Końcowa regresja ma101 PNG,46 przyjętych obrazów i55 prób (9 odrzuconych).
Obrazy służą wewnętrznej kontroli;nie są podglądem przeznaczonym do prezentacji.
Dwa przebiegi sondy,z ponownym dekodowaniem metadanych i z ich buforowaniem,
dały identyczny fixture SHA256`b937abe8f60d74abf1a166df9356f61b816f28324458d3d77af653bf5e96cfb0`.
Każdy scenariusz wykonuje nowy emulator;wyniki x86 nie są buforowane.

[Zakres i następny krok](SHIP_FLEET_MEMBERSHIP.md),
[raport porównania](../artifacts/fleet-orders/membership-validation.json),
[regresja playera](../artifacts/fleet-orders/selection-regression/report.json),
[milestone](evidence/milestone-20261103-fleet-membership.json).
Scena,prefaby,pakiety,ustawienia i dotychczasowy kod Unity nie wymagały zmian.
Pierwsze uruchomienia dodatkowego hostowego harnessu DLL wymagały referencji
netstandard i usunięcia Windows System.* z MONO_PATH. To naprawa harnessu;
modułu ani builda gry nie zmieniano po buildzie. Log diagnostyczny zachowano.

---

# Historyczny etap wyboru floty — poprzedni DLL

Nowy tryb`--ship-pointer-reference --ship-pointer-fleet-selection` obsługuje
wybór0b/0c/0d,ramkę,Shift/Ctrl,obrysy i pełne paski zdrowia.
Jest to tymczasowa flota;wspólne rozkazy i planowanie formacji nie są ukończone.
Pełny remake pozostaje w budowie.1920×1080,16:9,pełny ekran potwierdzono
w playerze Windows pod Wine;natywny Windows11 i docelowy laptop nie były testowane.

| Kryterium | Wynik |
| --- | --- |
| Wybór i hover |PASS:1710 transakcji i9280 stanów actualx86/C# |
| Kolejność i cykl życia |PASS:2376 stanów normal/callback/recycled slots |
| Obrysy i paski |PASS:1221 stanów,180 RLE i6 buforów zdrowia;3 rozmiary źródłowe |
| BuildWindowsMono |PASS:148048747B;0 błędów/ostrzeżeń |
| Discovery |PASS:241 testów,0 pominięć,348.857s |
| Dodatkowe QA |PASS:2 testy,64.831s;6 mutacji protokołu odrzuconych |
| Końcowy replay |PASS:46 etapów/47 zdarzeń/11 operacji wyboru;RGBmean/max0 |
| Regresje tego samego DLL |PASS:ramka30 kadrów,ruch25 kadrów,menu27 etapów/5 obrazów;exit0 |
| Integralność |PASS:66 C#/121 meta;9 stagingów;9 źródeł SHA zgodnych;C# bez zmian po buildzie |
| Pełny ruch grupy/pełna gra/oprawa2026 |Nieukończone;rozkazy są jawnie blokowane w nowym trybie |
| Windows11/laptop/OS mouse/fokus |Niewykonane lub nadal niezweryfikowane |

DLL:`c2839d9d4a34446534811d984c7e680d815fb25989532d73059a9607575fcb58`.
[Opis,raporty i granice](SHIP_FLEET_SELECTION.md),
[milestone](evidence/milestone-20261103-fleet-selection.json).
Nie wliczano pierwszego niepełnego przebiegu do46 etapów.
Zmiany lokalne;bez publikacji,ZIP i podglądu do prezentacji.

---

## Historyczny etap ramki — dane poprzedniego DLL

### Zaznaczanie ramką, 2026-11-03

Bieżący etap jest zwalidowany w ograniczonej diagnostyce jednego statku0b.
Pełna gra,selekcja całej floty i finalna oprawa2026 pozostają w budowie.
Widok pełnoekranowy1920×1080 został sprawdzony w playerze Windows pod Wine;
natywny Windows11 i laptop i5/16GB/RTX3050Ti nie zostały przetestowane.

| Kryterium | Wynik |
| --- | --- |
| Zapytanie/polityka/kontur |PASS:1745/144/1920 C#/x86;7864320 pikseli i25 kontroli API |
| Kompilacja WindowsMono |PASS:146986667B;0 błędów/ostrzeżeń |
| Discovery |PASS:234 testy,0 pominięć,254.424s |
| Dodatkowe QA protokołu |PASS:2 testy,63.685s;7 celowo błędnych zapisów odrzuconych |
| Końcowy replay ramki |PASS:30 etapów,33 zdarzenia,5 ramek,RGBmean/max0 |
| Regresja myszy/menu |PASS na tym samym DLL:25 kadrów oraz27 etapów/5 obrazów;exit0 |
| Integralność |PASS:62 C#/114 meta;8 stagingów;9 źródeł SHA zgodnych;C# bez zmian po buildzie |
| Pełna flota i pełna gra |Nieukończone;większy/inny zbiór blokowany przed zmianą zaznaczenia |
| Windows11/laptop/OS mouse/fokus |Niewykonane lub nadal niezweryfikowane |

DLL:`8ed5e4c2bfd5cc7780ab55426a66797e0c9631792e01bccfb5dfdfea2fe76fe1`.
Źródła,odtwarzanie,granice i raporty:[SHIP_BOX_SELECTION.md](SHIP_BOX_SELECTION.md).
Milestone:[milestone-20261103-box-selection.json](evidence/milestone-20261103-box-selection.json).
Pilot28-etapowy jest osobny i nie zwiększa liczby30 końcowych etapów.
Zmiany lokalne;bez publikacji,ZIP i podglądu do prezentacji.

---

## Historyczny etap wejścia świata — dane poprzedniego DLL

### Sterowanie pojedynczym statkiem, 2026-11-03

W ograniczonej scenie można wskazać i zaznaczyć statek0b oraz wydać mu
rozkaz ruchu myszą. Działają źródłowe zaznaczenie, pełny pasek zdrowia,
kursory i potwierdzenie rozkazu. **Pełny remake pozostaje w budowie;
zwykły Start jest nadal wyłączony.** Cel produktu:1920×1080,16:9,
pełny ekran na Windows11 i laptopie i5/16GB/RTX3050Ti.

Zmiany są lokalne na bazie864d5bdcb6c727495676c7a0d439615077a206a6.
Zasoby referencyjne nie są ukończoną oprawą2026. PNG służą wewnętrznej QA;
nie publikowano środowiska ani repozytorium i nie utworzono ZIP.

## Wyniki bieżącego etapu

| Kryterium | Wynik i zakres |
| --- | --- |
| Windows64Mono | Unity6000.3.27f2; 146968843B;0 błędów i0 ostrzeżeń |
| Finalny discovery | 232PASS,0 pominięć,229.058s |
| Celowane QA |14PASS,0 pominięć,18.123s;39 odrzuconych mutacji logu i12 błędnych protokołów fg |
| Ponowienie po rozszerzeniu fixture kursora | Osobno4PASS,2.863s;nie dodatkowe unikalne testy |
| Hover C#/x86 |2327 stanów,2319 zapytań,288 wizyt maski,15 kontroli API |
| Polecenia C#/x86 |55 stanów,19 kontroli API;odrębne UI5c i simulation5e |
| Zaznaczenie C#/x86 |407 stanów,226 publikacji,7 usunięć selectora i paska,5 kontroli API |
| Kursor/confirm C#/x86 |94 stany,44 operacje publikacji kursora,17 publikacji confirm,7 kontroli API |
| Grafika źródłowa |28 klatek/168 buforów native RLE;2 sentinele paska34×4;29 obrazów w nowym atlasie |
| Membership/planowanie |Grupy0/1/2 i siedmiu statycznych peerów;576 celów×2 dodatnie grupy;1309 stanów coupledWork |
| Gate przeciągania |1880 zdarzeń źródłowej mapy;aktywny prostokąt blokuje zwykły rozkaz |
| Finalny player myszy |2 sesje:35+25 kadrów;60 pełnych obrazów1920×1080,RGBmean/max0 |
| Ruch w playerze |197+101 kroków;358 wierszy motion;13 pól/16 wartości skalarnych zgodnych z native |
| Wejście i kolejka |39 zdarzeń myszy,5 pakietów41/20,2040 odczytów kolejki bazowych rendererów |
| Anulowanie |Usunięcie urządzenia PASS,bez sztucznego Up;fokus pozostaje niezweryfikowany |
| Regresje na tym samym DLL |Picker normal:12 kadrów/306 zapytań/96 bindings;menu:27 etapów/5 obrazów/6 komend;exit0 |
| Integralność |57 C#/109 meta,unikalne GUID,8 stagingów;C# bez zmian od początku finalnego buildu |
| Natywny Windows11/laptop |Niewykonane;nie ma wyników wydajności na docelowym sprzęcie |

Wcześniejszy discovery217 jest zachowany jako historia. Finalny discovery
obejmuje232 testów,łącznie z14 testami nowego QA. Cztery testy kursora powtórzono
po rozszerzeniu źródłowej fixture. Ruch ma13 nazwanych pól,w tym3 pary,
czyli16 wartości skalarnych;nie jest to54-polowa kontrola nowego UI.
Regresja starego pickera zachowuje swój54-polowy zakres ruchu.

## Artefakty i odtwarzanie

[BuildReport](../artifacts/pointer-input/build-report.json),
[log finalnego buildu](../artifacts/pointer-input/windows-build-05.log),
[integralność](../artifacts/pointer-input/source-integrity.json),
[finalny discovery](../artifacts/pointer-input/unittest-final.log),
[14 testów QA](../artifacts/pointer-input/qa-unit-tests-final.log).

Assembly-CSharp SHA256: `9402081fe31ba5135512f95ea385ee867d75d2c26a03f0f6060dde352d17de8a`.

[Dwa rozkazy](../artifacts/pointer-input/runtime-final-two-03/report.json),
[pojedynczy rozkaz](../artifacts/pointer-input/runtime-final-normal-01/report.json),
[regresje](../artifacts/pointer-input/final-regressions.json).
Próby fokusu do własnego WineNotepad nie wykazały rzeczywistej utraty
aktywności gry. SetForegroundWindow zwracało0,a foreground pozostawało
w playerze. Przyczyny odmowy nie ustalono;nie jest to dowód błędu callbacka
gry. [Audyt pięciu prób](../artifacts/pointer-input/qa-focus-unverified-independent-audit.json).
Testy wejścia używają syntetycznego InputSystem,nie sprzętowej myszy ani
natywnego Windows11.

[Implementacja](WORLD_POINTER_INPUT_IMPLEMENTATION.md),
[hover](WORLD_POINTER_HOVER_EVIDENCE.md),
[polecenia](WORLD_POINTER_COMMANDS.md),
[grupy](WORLD_POSITIVE_GROUP_MOVEMENT.md),
[grafika i animacja](SHIP_POINTER_VISUAL_EVIDENCE.md),
[QA i niezależne audyty](SHIP_POINTER_QA_EVIDENCE.md).

## Granice dowodu

Sterowany jest0b;pozostałych7 statków pozostaje statycznych. NoFog i puste
pozostałe sloty świata są jawnymi założeniami. Audio jest wyłączone.
Zaznaczanie wielu statków,ramka,zmodyfikowane komendy,zastępowanie aktywnego
ruchu,pełne fog,AI,walka i save/load pozostają do wykonania.

Zaznaczenie rekonstruuje się z rzeczywistych instrukcji źródła i źródłowych
publikacji kadłuba. Fazy kursora w niezatrzymanej części są obserwowane
z kontrolą zakresów,hotspotów,offsetu click−(11,24),interwałów i stampów.
Nie odtwarzano każdej niezaloggowanej transakcji Life. Zgodność obrazu
obejmuje zweryfikowaną fazę referencji,nie pełny scheduler aplikacji.

[Cadence](POINTER_APP_CADENCE_EVIDENCE.md) potwierdza osobny BaseSystem/UI
i zwykłe40ms przy szybkości5. Bieżący adapter używa niezależnej bramki40ms;
pilna kolejka,Sleep i pełna kolejność systemów RunApp pozostają otwarte.

Zachowano starsze próby:build3 tolerancyjnie przeszedł35 kadrów z różnicą
RGB2 wyłącznie w kursorze morskim;nowy SpriteRenderer32767 usunął tę różnicę.
Nie doliczamy historycznych ani częściowych prób do60 finalnych kadrów.
Fokus pozostaje do walidacji na platformie pozwalającej rzeczywiście
przełączyć aktywność. Pierwsza finalna regresja pickera
napotkała niepełną końcową linię logu;zachowany pełny log parsuje się poprawnie.
Adapter finalnej regresji odracza tylko linię bez newline i nadal odrzuca
błędne pełne rekordy. [Dowód framingu](../artifacts/pointer-input/stream-log-framing.json).

Regresja playera InputSystem/Ctrl na tym samym DLL:23 punkty,69 stanów,
230 części,782 odczyty kolejki,136 publikacji,6 pakietów,exit0.
Wejście odsubskrybowane,3 właściciele póz i8 zajęć komórek zwolnione.
