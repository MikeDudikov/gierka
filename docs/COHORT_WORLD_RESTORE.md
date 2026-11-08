# Odtwarzanie kohorty w świecie i playerze — 2026-11-04

`ShipWorldStep.RestoreCohortInPlace(records,counter)` łączy istniejący import
aktora z kontrolowanym światem. Odtworzenie wykonuje się między krokami,
bez zmiany fazy zegara,poczty,wieku zadania,członkostwa lub rejestracji.
Nie ma nowego menedżera,ECS,pętli Update lub globalnej fazy grup.

To **odtworzenie na miejscu w zachowanym kontekście**,nie pełne save/load,
cofanie całej misji lub import nieznanej kohorty. Istniejące `SingleStepClock`,
`ShipFleetMembership`, `MissionOccupancyGrid` i `ShipMoveOrder` pozostają
autorytatywnymi systemami.

## Sekwencja i granice

1. Zakończenie zaakceptowanego kroku przez dotychczasowe Begin/Complete.
2. Wczytanie wszystkich3 rekordów źródłowych do pamięci. Kolejność odpowiada
   ordinalom aktorów,z którymi utworzono świat;nie kolejności sprite’ów.
3. Kopia buforów i walidacja **całej paczki przed pierwszą zmianą aktora**.
   `ValidateInPlaceSourceMovementState` używa tych samych granic4e2180 co
   import oraz sprawdza counter,komórki,rezerwację,next,właściciela grid
   i zgodność zapisanego położenia z bieżącą publikacją.
4. Istniejący import4e2180 w source-ordinal order. Membership5e jest
   sprawdzane przez dotychczasowy odczyt;UI i sloty nie są zapisywane.
   Siatka ma już pasujący kontekst claimów. Nie zeruje się poczty lub taskWorkAge.
5. Adapter istniejących póz stosuje odtworzoną klatkę i położenie.
   Rejestracja i głębokość rodzica pozostają bez zmian,ponieważ pozycja
   i rozmiar w tym profilu są takie same. Nie dopisuje się aktualizacji
   równej głębokości,która mogłaby zmienić kolejność remisów.
6. Kolejny zwykły krok:PrepareMail→SendMail→źródłowy rejestr obiektów.

Walidacja paczki jest granicą projekcji zarządzanej,nie nową regułą gry.
Błędny trzeci rekord,brakujący bufor,niezgodny counter lub zmiana położenia
są odrzucane przed zmianą pierwszego statku. Test sprawdza ten przypadek.
Nie jest to obietnica rollbacku dowolnego błędu systemowego lub pełnego
ładowania świata. Odtworzenie innego kontekstu wymaga osobnego portu.

Komentarze metod wskazują4e12e0/4e2180 i jawne granice adaptera.
Źródło to oryginalny EXE SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`,
dekompilacja i faktyczne wykonanie x86,nie nieistniejące źródła C/C++.

## Dowód x86 i C#

12 scenariuszy:4 położenia obiektu floty w rejestrze i3 zestawy bramek
`0/0/0`,`1/0/255`,`255/1/1`. Dwa odtworzenia w każdym przebiegu,w krokach1
i10.2544 zwykłe klatki,24 odtworzenia,7704 stany aktorów i2568 obserwacji
świata zgodnych z C# i rzeczywistym shippingDLL.29 kontroli API,
checked+/warnaserror+. Nie dowiedziono oryginalnej kolejności rejestracji
całej misji ani osiągalności syntetycznych niezerowych bramek w rozgrywce.

Oryginalny blok zegara,poczta,Fleet taskWork,eksport4e12e0,import4e2180
i normalne Promote+Work wykonują się w tym samym emulatorze. Pełny Ship::Life
nadal zastępuje udokumentowana trampolina. Pozostają wcześniejsze granice
CRT i tworzenia/wyszukiwania grafiki. Nie odtworzono pełnego App lub
graficznego usuwania/tworzenia wszystkich obiektów oryginału.

W kroku1 import zmienia obserwowaną klatkę z ostatniej publikacji na
klatkę zapisaną w sprite+45,np.0b z20 na47. W kroku10 kolejka zawiera3
nowe rozkazy20. Po odtworzeniu nadal czekają;odbiór następuje w11.
W wybranym przebiegu późniejsze ponowienie w102 dociera w103.
Nie przyspieszono poczty ani nie poprawiono źródłowego odrzucania rozkazu.

4 testy celowane PASS,0skip,79.551s,w tym świeży x86 i1287 przypadków
zegara.3 mutanty wykryte:częściowy import przed końcem walidacji,zły counter
i reset bramki poczty. Pełnego discovery nie ponawiano;zestaw ma295 testów.
Fixture:`bb8bf6f462d8fe88a3af24e785c870c93826d944fd0e4a16eac05ec7a743b225`.
Regresje na shippingDLL:port15096,świat5388,busy-world5088,busy-actor9984,
live10827/130 wejść planera zgodne.

## Player i prezentacja

Nowa flaga dodawana do dotychczasowego kontrolnego świata:

```text
--ship-fleet-motion-reference --ship-fleet-world-step
--ship-fleet-world-busy --ship-fleet-world-registration fleet,11,12,13
--ship-fleet-world-restore-dir <jawny-katalog-rekordów>
--terrain-origin-x 9 --terrain-origin-y 0 --terrain-reference-exit-after 1
```

Pliki to oryginalne rekordy binarne,z identyfikatorami aktorów w nazwach
`1/0000000b.bin` itd.oraz`10/0000000b.bin` itd. Są jawnymi wejściami
diagnostycznymi spoza Assets,nie nowymi ścieżkami zasobów lub formatem zapisu gry.
Ramka renderowania nadal korzysta z istniejących manifestów i właścicieli póz.

Tylko ten replay podaje zegarowi dokładne wejścia capturedTime40*n,takie
same jak oracle. Dzięki temu jitter renderowania hosta nie zmienia fazy
porównywanego zegara. Nie jest to dowód rzeczywistego tempa gry lub wydajności.
Dotychczasowe tryby bez flagi odtwarzania zachowują swoje źródło czasu.

Player Windows pod Wine/Xvfb przeszedł17 punktów,51 stanów,170 części,
578 rzeczywistych odczytów kolejki i136 publikacji,exit0. Sprawdzono oba
punkty odtworzenia,klatki sprite’ów,pozycje,sortowanie,zachowanie fazy
i poczty. To nie nowa walidacja pikseli. Nowy moduł nie jest wyłącznie
uruchamiany na Mono hosta:ścieżkę wczytania rekordów wykonano w playerze.

Build Unity6000.3.27f2 Windows64Mono:152962091B,0 błędów/ostrzeżeń.
DLL:`fadf3a5c511cc6ad0813c3a43da1c16e95ae2665377cad82eca0a03ac3f80cab`.
73C#/131meta,3 istniejące C# zmienione,70 bez zmian;bez nowych klas Unity
lub meta.275 plików przed/po buildzie,78Resources/10 stagingów i9 oryginalnych
wejść bez zmian. Znany wcześniejszy ComputeBufferGC przy zamykaniu pozostaje.

Ten kod jest w pełni zgodny z istniejącym `SingleStepClock` i nie narusza
deterministycznego stanu w opisanym i przetestowanym zakresie. Pełny Life,
cała misja,inne rodziny zadań,save/load,UI Shift/Start,AI,oprawa2026,Win11
i laptop nadal nieukończone lub niezweryfikowane. Cel1920×1080/16:9/fullscreen.

Następnie:połączyć dotychczasowy pierwszy rozkaz floty z tą samą kolejką
świata i pracą zadania grupy,utrzymując blokady nieprzeniesionych ścieżek UI.
Raporty:`artifacts/cohort-world-restore/`. Bez publikacji,ZIP,PNG i podglądów.

Regresja playera InputSystem/Ctrl na tym samym DLL:23 punkty,69 stanów,
230 części,782 odczyty kolejki,136 publikacji,6 pakietów,exit0.
Wejście odsubskrybowane,3 właściciele póz i8 zajęć komórek zwolnione.
