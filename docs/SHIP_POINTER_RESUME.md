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

# Punkt wznowienia — zadania grup w kroku świata,2026-11-04

Następny dowódUI również ukończony: [QUEUED_UI_WORLD_EVIDENCE.md](QUEUED_UI_WORLD_EVIDENCE.md).
12cases2400frames48requests7344states zgodne x86/C#/shippingDLL;2testPASS107.791s.
Razem10testów w dwóch zestawach,330discovery bezfullrun. WPMOVE type8 znaleziony
w controlm:21części/36×29,cyfryWPNUM iWPMOVE,offsety/SHA w discoveryJSON;
bez graf.konstruktora lub nowychobrazów. Dalej adapterjawnychsłów/Shift+markery/QA.

Aktualny etap: [pełna integracja100/2 w świecie C#](QUEUED_WORLD_INTEGRATION.md).
ShipWorldStep odbiera Arrival po każdym aktorze i wywołuje Work100/1 lub100/2
w istniejącej pozycji floty. Źródłowe310 również dla100/1. Begin/Complete40,
jedna poczta i jeden właściciel zachowane;bez nowegoManager/ECS/Update.
Nowe przeciążenie TryAdvance ma jawne registry-ordered short words dla bieżącego
kroku;mapuje przez GetGroupMemberRegistryIndex do group order. Bez default117/0.
Stare przeciążenie odrzuca100/2 bez kontekstu. Błędne wejścia zachowują stan
przedcounter/mail/aktorami i poprzedni ukończony odczyt.10APIcontrols PASS.
50cases5536frames16608actorstates plus strict1001:31cases1796frames5388states.
ŻADNYCH pakietów źródłowych po starcie w nowej walidacji;C#world generuje wszystko.
Mixed4cases grup(13,11)/(13,12,11),words[32767,117,-32768],fleetfirst/last PASS.
8testPASS0skip188.276s,3nowemutanty+5legacy,clock1287;328discovery bezfullrun.
Legacy fixture nie zmieniane:ich obserwatory projektują dawnyret4a1700;
nowe strict310 i queued K obejmują WSZYSTKIE zdarzenia. Nie filtrować produkcji.
Windows64Mono152977451B0/0,DLL161a875ab0612b2945560d7adcd5f8922e45f56c144e6379b1b96cae683a517e.
73CS/131meta,1zmieniony(World)72bez zmian,275frozen/78Resources/10stages/9oryginałów.
Następny etap już rozpoczęty:probe_queued_ui_world.py,12cases2400frames48requests,
SHA7431c964531c4a15472404c3612795cf974f9218c3e9ef922a36a248a2087b0c.
Prawdziwe UI518070 i świat w dwóch silnikach:busy Shift,append,duplicate,normal.
UI nadal guarded;przed odblokowaniem wymaga jawnego per-wave kontekstu w adapterze.
Nie hardcode117:tylko profilWineCRT. Bez PNG/ZIP/publikacji/aplikacji/nowychagentów.
User zezwolił kontynuować KOLEJNE etapy autonomicznie bez kolejnego "kontynuuj".
PełneLife/AI/Start/300/311/40/oprawa2026/Win11/laptop nadal poza zakresem.
1920×1080/16:9/fullscreen. Starsze wyniki poniżej są historyczne.

---

Aktualny etap: [świat100/2 x86 i port zgłoszeń aktora](FLEET_QUEUED_WORLD.md).
46 scenariuszy / 5416 klatek / 16386 stanów; 24 permutacje rejestru i 3
niezależne granice UI/świat. Źródłowy4a1700 wykonuje się zamiast ret-boundary;
globalny5c7504 wskazuje istniejącą flotę.310 po statku może trafić do Work
grupy w tym samym ticku, lecz20 dopiero do następnej poczty. Przykład12:
flota first: arrival58 -> emit59 -> receipt60; flota last:58 ->58 ->59.
258 wywołań:196 near z4a4a67 i62 exact z4a49af; nie deduplikować.
ShipMoveOrder ma Arrival/LastStepArrivalCount/GetLastStepArrival. Przechwytuje
licznik i cel5b2, bez zmiany fizyki, członkostwa, tasków lub gridu. Near używa
5573d0 i STARYCH komórek sprite'a, po hamowaniu.72pozostałe C# bez zmian.
Clock/World/Membership/Task niezmienione; World nie konsumuje jeszcze Arrival.
Source fixture5d36373f7cf9e95fd2f66e338af1cdc6c0c6ad6526cd58610bf3217cfe98d885.
6testPASS0skip208.196s(5nowe+clock1287),3mutC# i3mutx86;324discovery bezfullrun.
Po zgodnych klatkach pierwszy checker odrzucił tuple/list metadanych terenu;
normalizacja poprawiona bez zmiany fixture/C#/oryginału, log zachowany.
C#body porównany przez odtworzenie pakietów x86, NIE przez C#world100/2.
Windows64Mono152975915B0/0, DLLb7247a256195d67d51bb91c8db3c8aa02b0270e8147127ae1e7c906d8ea53d55.
Następnie: przekazywać efekty po KAŻDYM Tick aktora do istniejącego właściciela,
przełączyć Work100/2 w pozycji floty i dodać jawny kontekst każdej fali. Nie
zbierać310 dopiero po całej pętli, nie dodawać globalnej fazy lub drugiego flush.
UI Shift dopiero po integracji.300/311,40,taskless events,fullLife/AI/Start
pozostają poza zakresem;117 nie jest uniwersalnym kontraktem Windows.
Bez PNG/ZIP/publikacji/aplikacji/nowych agentów.1920×1080/16:9/fullscreen.
Starsze wyniki poniżej są historyczne.

---

Bieżący etap:port100/2 do istniejącego ShipFleetNormalTask/ShipFleetMembership.
Czytać[FLEET_QUEUED_PORT.md](FLEET_QUEUED_PORT.md). Jeden Group.Task,Subtype1/2,
bez nowego tick/ECS/Update lub zmiany członkostwa/gridu. PierwszyShift20dla
wszystkich,dalszyappendbez20,deduplikacjaglobalna,Agezachowany.310LIFO+periodic
extra20+staletarget iuintwrap zachowane. WorkQueuedTask wymaga explicit signed16
prefixwords w kolejności członków;bezdomyślnego0/117. NowywariantwSourceWaveField
odtwarza545960,nie5578a0;2dodatkoweeksportyCasmGhidrareadonly.
64cases1121states+36setup,19API,20waves11520words zgodne x86/C#/shippingDLL.
4testPASS0skip132.663s(3nowe+clock1287),5mutantówC#wykrytych,319discovery
bezfullrun. Początkowe błędyadapterainactiveAge/mutantCS0219 zachowane i poprawione.
Worldpreflight odrzuca100/2przedcounter/mail/aktorami,pełnysnapshotguardPASS.
Begin/Complete,pozycjafloty,pending1 i kolejnośćmail/Life bez zmian.
Shipping1001:778states;owner2486;world5388;busyworld5088;UIreplace7248;
restore7704;live10827+130planners PASS. Unity6000.3.27f2 Windows64Mono
152975403B0/0,DLL8ca1c3b4ccf48ac651a1f3662bc50da32004a0aae2406d1bfe5632e3e367d001.
73CS/131meta/275frozen,4CSzmienione69bez zmian,78Resources/10stages/9oryginałów.
Następnie dowód100/2wświecie,poczta,rejestr,kontekstfali i310odstatków,potemUI.
Shift/queuedworld/300/311/40/fullLife/AI/Start nadalbramki. Nie hardcode117.
Brak dowodu finalnejoprawy2026/natywnegoWin11/laptopa/wydajności.
1920×1080/16:9/fullscreen. Bez PNG/ZIP/podglądów/publikacji/aplikacji/nowychagentów.
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

---

# Najnowszy punkt wznowienia — normalny task100/1,2026-11-03

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

---

# Najnowszy punkt wznowienia — pierwszy rozkaz floty,2026-11-03

Czytać[SHIP_FIRST_FLEET_CONTROL.md](SHIP_FIRST_FLEET_CONTROL.md),[VALIDATION.md](VALIDATION.md)
i[milestone-20261103-first-fleet-control.json](evidence/milestone-20261103-first-fleet-control.json).
Nowy pointer+fleet-selection+fleet-movement:wybór3,pierwszy normalny rozkaz,
41 przed20,formacja,ruch i Ctrl przywołanie grupy.23 punkty/69 stanów/230części/
782queueReads/6pakietów;bez deklaracji pełnego UI RGB0.360Ctrl i606core stanów
potwierdzone source/C#/shippingDLL.10test+2QA PASS0skip.71C#/129meta/10stagingów,
DLL5c9be5fd…;228 pre/postbuild hash zgodnych. Core/planer/formacja bez zmian.
Kolejne/queued/busy polecenia oraz Shift committed group pozostają zablokowane.
Następnie normalne zadanie100/1 i32B kolejka grupy:add300/remove311;
4a1340/4a1770 tylko dopisują zdarzenia,nie wolno pomijać ich konsumpcji.
49e850 Shift edytuje członkostwo;nie używać dawnego pending toggle.
Start i pełna gra/oprawa2026 nadal nieukończone.1920×1080/16:9/fullscreen.
Bez publikacji,ZIP,podglądu do prezentacji i nowych agentów.
Starsze punkty poniżej są historyczne.

---

# Najnowszy punkt wznowienia — rendering trzech statków,2026-11-03

Czytać[SHIP_FLEET_RENDERING.md](SHIP_FLEET_RENDERING.md),[VALIDATION.md](VALIDATION.md)
i[milestone-20261103-fleet-rendering.json](evidence/milestone-20261103-fleet-rendering.json).
Kontrolny --ship-fleet-motion-reference wykonuje normalne rozkazy0b/0c/0d
na wspólnej siatce i rysuje każdą publikację.0c używaA,0dH/A3 z pancerzem.
34 obrazy RGB0/102 stany/340 części/1156 odczytów kolejki;262 publikacje.
70C#/128meta/10stagingów,DLLd1d5a3e4…;14 testów PASS0skip41.923s.
Rdzeń poprzedniego etapu niezmieniony i ponownie sprawdzony z shippingDLL.
Następnie połączyć membership/formację/rozkazy/fizykę/renderowanie z myszą,
z dowodem zadań grupy i Ctrl. Jawne cele/grupy/ticki nie są pełnym Life.
Start i ruch floty myszą w dotychczasowym trybie nadal zablokowane.
1920×1080/16:9/fullscreen;pełna gra i oprawa2026 w budowie. Bez publikacji,
ZIP,podglądu do prezentacji i delegowania nowych agentów.
Starsze punkty poniżej są historyczne.

---

# Bieżący punkt wznowienia — 2026-11-03

Czytać[SHIP_LIVE_FLEET_ORDERS.md](SHIP_LIVE_FLEET_ORDERS.md),[VALIDATION.md](VALIDATION.md)
i[evidence/milestone-20261103-live-fleet-orders.json](evidence/milestone-20261103-live-fleet-orders.json).
CreateLiveLocal:odbiór20,rekord26B,promocja,dynamiczny planner i ruch0b/0c/0d
potwierdzone przez10827 stanów i130 osobnych wejść planera. Grupa5e jest
odczytywana po41,oddzielnie od UI5c.69C#/124meta/9stagingów;DLL53e9d500…;
10testów PASS0skip95.599s. Wcześniejszy błąd testu cache dotyczył braku
scenariusza;uzupełniona macierz wykrywa mutanty grup/cache/RNG.

Następnie:pełne klatki ruchu0c/0d,integracja membership/formacji/rozkazów/fizyki
z renderowaniem,kursorem i wyborem;własność zadań grupy oraz Ctrl istniejącej
grupy wymagają osobnego dowodu. Normalny Start i wspólny ruch myszą nadal
zablokowane;pełna gra i oprawa2026 w budowie.1920×1080/16:9/fullscreen.
Nie wracać do starych twierdzeń o braku dynamicznego planera w nowej gałęzi.
Starszy konstruktor0b nadal ma jawny kontrakt siedmiu statycznych peerów.
Bez publikacji,ZIP,podglądu do prezentacji ani delegowania nowych agentów.

---

# Punkt wznowienia — picker statków zwalidowany

Aktualny etap2026-11-03:wspólna fizyka0b/0c/0d na przygotowanych trasach.
Rozwinięto jeden rdzeń ShipMoveOrder przez CreatePreparedLocal i żywy opis
właścicieli;dotychczasowy adapter0b zachowuje ograniczony planer.6795 stanów,
6750 wywołań MoveShip,1440 publikacji,300 mutacji i22 API zgodne z x86 i DLL.
Własny0d:logical72,anchor−4,center36,limit52000,initialacc884→reserve1040.
7 testów PASS0skip26.234s;legacy0b956 stanów/446 publikacji/62 mutacje/35API.
69C#/124meta,9stagingów;zmieniony tylko ShipMoveOrder,pozostałe68 C# bez zmian.
Windows64Mono148065211B0/0,DLL e261360e02d6e49fd0d56599e2547a529273afc36ab84acc008c3806bf12b142.
Czytać[SHIP_PREPARED_FLEET_MOTION.md](SHIP_PREPARED_FLEET_MOTION.md)
i[VALIDATION.md](VALIDATION.md). Jawne trasy nie są dowodem promocji i planera.
Nowej gałęzi nie podłączono jeszcze do renderowania/sterowania trzech kadłubów;
normalny Start i ruch floty myszą nadal zablokowane. Następnie promocja26B,
dynamiczne planowanie/grupy/zadania i UI. Pełna gra/oprawa2026 w budowie.
Starsze punkty poniżej są historyczne.


Aktualny punkt wznowienia2026-11-03:ramka dla sterowanego0b ukończona
w ograniczonej diagnostyce.62C#/114meta,8 stagingów,DLL8ed5e4c…;234 discovery
+osobno2 QA;końcowy replay30 etapów RGB0 i regresje myszy/menu PASS.
Przed dalszą pracą czytać[SHIP_BOX_SELECTION.md](SHIP_BOX_SELECTION.md)
i[VALIDATION.md](VALIDATION.md). Następny krok:pozostałe selektory i pełna
flota;normalny Start nadal wyłączony. Starsze sekcje poniżej są historyczne.


Stan:2026-11-03. Użytkownik wznowił pracę. Etap predykatu masek jest
zwalidowany. Następnie ukończono C# ShipWorldPicker i diagnostykę Unity:
49C#/98meta,DLL a706aa5e9d9a5966b78c84bc1eace6f669f655a0e94601f82aeb2002e5305409,
196discoveryPASS+osobno7QA,53kadry1353query424bindingi.
Czytać bieżące docs/WORLD_PICKER_RUNTIME_VALIDATION.md i docs/VALIDATION.md.
Integracja sterowania myszą pozostaje kolejnym krokiem.
Nie publikowano,nie tworzono ZIP ani podglądu do prezentacji.

## Sprawdzenie poprzedniego ukończonego kroku

Przed nowymi zmianami ponownie sprawdzono331 plików dowodowych etapu
obiegu rozkazów,46 jego źródeł C# i DLL6c646…:wszystkie hashe były zgodne.
Etap ten pozostaje ukończony:182 testy discovery +7 osobnych QA,
4 sesje/53 kadry/159 ROI RGB0 oraz cztery grupy regresji.
Dowód historyczny:docs/evidence/milestone-20261103-order-cycle.json.

## Nowa praca zachowana lokalnie

Dodano `Runtime/Simulation/ShipPointerMask.cs` i meta. Przenosi rzeczywisty
predykat4e06c0 oraz bitlookup5575d0;klonuje24 osobne maski type18.
Precyzyjny hit używa opublikowanej pozycji sprite'a i STORED frame:
32…55→frame−32,w innych klatkach heading×3. Coarse zwraca true przed
sprawdzeniem geometrii. To nie jest pełny picker świata ani wejście myszy.

`tools/stage_ship_picking.py` weryfikuje trzy oryginalne pliki i przygotowuje
siódmy zestaw Resources/ShipPickingGenerated:96 masek A1/H1/B4/G4,
56×56/72×72/64×64/72×72,łącznie52800B,SHA256
60f3696904880fa4c4a51da2094f96145b30859013463369d1b953aebf3ba240.
Editor/BuildReferenceWindows wymaga teraz tego siódmego zestawu.
Poprzedni dokładny kod Editor zachowano i sprawdzono w
artifacts/world-input/picking/baseline-source/BuildReferenceWindows.cs.

Nowe pliki probe/validator/tests:
- tools/probe_ship_pointer_mask.py
- tools/validate_ship_pointer_mask.py
- tests/fixtures/ShipPointerMaskProbe.cs
- tests/fixtures/ship_pointer_mask.json
- tests/test_ship_pointer_mask.py
- tests/test_stage_ship_picking.py

## Potwierdzone wyniki nowego kroku

Rzeczywisty oryginał x86 bez hooków i checked C# z warnaserror zgadzają się:
432428 zapytań,423960 pikseli pełnych120 płaszczyzn (96 oryginalnych,
24 syntetyczne dla paddingu),8468 punktów,13 kontroli API.
Raport:artifacts/world-input/picking/mask-csharp-validation-final.json.
Fixture SHA256:8119cc2cb7e645edc671f2ba8daea5d1878a61ddeb0acca254e59a0c92163245.
Pięć testów celowanych PASS,0skip,14.360s:mask-targeted-tests.log.

Nowy build Windows Unity6000.3.27f2:0errors/0warnings,146364475B,
1920×1080,DLL SHA256
e211062e1098162e28bc1dcdf66ef9851a8dbfb2666f18d486b6e7e4443e2e89.
47 C#/96 poprawnych unikalnych meta;source-integrity.json wiąże źródła.
Nie zmieniano C# po buildzie. Raporty pod artifacts/world-input/picking/.

**Poprzedni discovery przerwano SIGINT na prośbę użytkownika;po wznowieniu
świeży unittest-resumed.log zakończył194PASS/0skip/181.146s.**
Zachować unittest-final.log;nie deklarować194PASS. Proces3622 sprawdzono
po argv i wysłano sygnał wyłącznie do własnego procesu testów.
Regresja playera nowego DLL zakończona:normal+two-after-clear,35 kadrów/105 ROI
RGB0,54pola/path/cache/RNG,1190queueReads,cleanup8/8exit0.
To stary ruch,nie integracja pickingu.45prób/10odrzuconych:7exactearlier/3unknown.
Pierwszy nieudany native-mask-probe.log zachowany:4e06c0 używa argumentu
output jako scratchbyte;harness poprawnie zeruje go przed każdym call.
Nie był to błąd samego źródłowego predykatu.

## Następne kroki po wznowieniu

1. Sprawdzić bieżące środowisko/boot i source-integrity.json.
2. Discovery194 i regresja35 są zakończone;nie powtarzać bez nowej zmiany.
3. Czytać docs/SHIP_POINTER_MASK_EVIDENCE.md oraz bieżącą VALIDATION.
4. Ship-only/noFog picker jest ukończony z1206C#/x86queries,5665wizytami
   i21guardami. Pełny fog/pozostałe sloty pozostają oddzielne.
   --ship-picking-reference sprawdza25/27query naheldcheckpoint;nie jest myszą.
5. Podłączyć c458→Fleet/group→action20 zgodnie z nowym dowodem.
   Korekta:normalny jeden aktor4cf070 dostaje byte0;FF dotyczy fallback4cc650.
   Pendingselection49ca60 tworzygroup0 wslot5,49bd60 ustawiaactor+5c
   i kolejkujeaction41 przedaction20. Nie ignorować członkostwa grupy;
   frozenShipMoveOrder/replanner mają dotychczasowy kontrolowany group−1.
   Dowód:docs/WORLD_COMMAND_SOURCE_EVIDENCE.md (6positive+3negative x86);
   worldpicker:docs/WORLD_PICKER_ORDER_EVIDENCE.md (1206native/C#).
   Skutki grup:docs/WORLD_MEMBERSHIP_MOVEMENT_EVIDENCE.md;ui5c!=simulation5e,
   actual41zmienia5e. Dla2tras different-group projekcjarównoważnałączniezmapami;
   samegroup aktorzywymagająrzeczywistejpolityki,nieignorowaćtego.
6. Dopiero po dowodzie podłączyć uporządkowane InputSystem i oryginalną
   grafikę zaznaczenia/healthbar/cursor. Nie napisano jeszcze tych mostów.

Istotne reguły źródłowego UI ze statycznych eksportów:Mapa51cd60 Move60
→517a60 cachedhover;LeftUp62 typ5 wybiera własny obiekt,typ7/e6=0 wydaje
normalny ruch. RightUp64 resetuje/kasuje/przełącza kontekst,nie zwykły ruch.
ButMapXY518070 używa cachedcell c9/cd i target d9,nie nowych współrzędnych
release. Uwzględnić dragstate,map+489<0 i flagi4/8;nie zakładać presslatch.
Queryc44f trafia do Dump499560→49a580. Maska nie jest alfą renderowania.

Selektor statku:4e0b80 RAM_056X056,10 klatek;4e0d00 publikuje i dopiero
przesuwa frame według pendingSteps. Wciąż sprawdzić kolejność względem
MoveShip/Work i healthbar50c890. Cursor5 CUR_OWN_ hotspot0/0,interval10000;
cursor7 CUR_SEA_ hotspot−18/−17,interval150. TAKE_CMD515df0 ma osobną
animację,punktkliknięcia−11/−24,interval250 — nie implementować na domysłach.

Wszystkie procesy Unity/Wine/Xvfb muszą być sekwencyjne i własne;root
prowadzi build/player. Agenci pomocniczy zakończyli się błędem limitu usługi;
nie zakładać,że działają w tle. Normalny Start nadal wyłączony.
Cel pełnej gry1920×1080/16:9/fullscreen,oprawa2026 i Windows11/laptop
pozostają obowiązujące. Pełna gra i sterowanie gracza pozostają nieukończone.
