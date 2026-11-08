# Ponowienie normalnego rozkazu20 — 2026-11-04

Nowy etap rozszerza istniejący `ShipMoveOrder` o `ReceiveNormalCellMove`.
Przyjmuje on normalny rozkaz20 również podczas ruchu. `ShipWorldStep`
używa tego odbiorcy po przygotowaniu poczty,przed aktualizacją obiektów.
Nie wprowadzono globalnej fazy grup ani zmiany kolejności `SingleStepClock`.
Użytkownik potwierdził,że zgodność z zachowaniem x86 ma bezwzględne pierwszeństwo.

Zakres to zdrowe lokalne0b/0c/0d,normalne metadane0/255 i źródłowy warunek
nieblokującego arbitrażu `actor+58b == 0`. Ten bajt **nie jest** fizycznym
stanem ruchu `+58c` ani bramką środka `+596`. Oracle sprawdza58b po każdym
kroku;nie zastępuje go sztucznie zerem. Inne rodziny zadań i arbitraż przy
niezerowych bramkach pozostają nieprzeniesione.

## Reguły z kodu maszynowego

| Adres | Zachowanie |
| --- | --- |
|4e2ba0,action20 |Przygotowuje wyzerowany26B rekord,cel w+4/+8,metadane w+25. Nie sprawdza „idle” jako warunku odbioru. |
|4a9e30,command80 |Kopiuje rekord do actor+858 i ustawia pending80 w+7d6. Kolejny20 nadpisuje ten sam rekord;ostatni wygrywa przed promocją. |
|4ab720→4abe50 |W nieblokującym profilu usuwa deferred i bity aktywnego zadania przez maskęffffff0f. Nie zeruje wprost stanu fizycznego,trasy lub rezerwacji. |
|4ab250 |Promuje cel i zeruje migawkę ponowienia;lastPlan0,interwał25,firstNavigation1,retry0. Bajt255 zachowuje priorytet;inne metadane są stosowane dopiero tutaj. |
|4ab930→4a5f30 |Istniejący Work i planer obsługują nowy cel z bieżącego stanu fizycznego i siatki. |
|521500→522850→542320 |Poczta przed Life;nowe emisje zadania pozostają do późniejszej poczty. W nowym przebiegu grupa emituje w10,statki odbierają w11. |

Źródło nadal stanowi oryginalny EXE o SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`,
dekompilacja i wykonanie x86. Nie znaleziono oryginalnego C/C++.
Kopie wykorzystywanych eksportów są w `artifacts/busy-ship-orders/source/`.
Komentarze nowych metod wskazują adresy;walidacja współrzędnych i zakresu
profilu jest jawną granicą projekcji zarządzanej,nie regułą oryginalnej gry.

Starsze `ReceiveCellMove`, `RequestCellMove` i `CanRequestMove` zachowują
dotychczasowe ograniczenie wejścia idle. Dzięki temu sterowanie myszą
nie odblokowuje się przed przeniesieniem pozostałych gałęzi. Nowy odbiorca
wymaga profilu `CreateLiveLocal`. Przygotowane trasy nie uzyskują odbioru.
Nie zmieniono członkostwa,zadania grupy,siatki,planera,scen,prefabów,
zasobów,pakietów ani ustawień. Koordynator nadal nie zapisuje grid;
5e nadal zmienia istniejący odbiór41. Sloty i zachowane ogony bez zmian.

## Dowód behawioralny

-18 scenariuszy,9984 pełne stany,9720 kroków,210 rozkazów i54 wejścia41.
  Odbiory w fizycznych stanach0/2/3/4/5;3335 publikacji i346 zmian siatki.
  Ponowienia przed pierwszą promocją,podczas obrotu i ruchu,seryjne nadpisania,
  różne RNG oraz pending1/2/3/7.12 kontroli API.
-8 przebiegów świata,1696 klatek,5088 stanów,4 położenia floty w rejestrze.
  Zdarzenie300 w10 lub36;72 rzeczywiste odbiory,24 emisje,1088 publikacji.
  Odbiór20 dopiero w11 lub37.20 kontroli API.
-Świeże wykonanie x86 i porównanie C# PASS;shippingDLL także PASS.
  Trzy mutanty wykryte:pierwszy zapis wygrywa,sztuczne StopNavigation przed
  promocją,natychmiastowy odbiór nowych emisji grupy.
-4 testy celowane PASS,0skip,70.211s,w tym1287 przypadków zegara.
  Pełnego discovery nie ponawiano;zestaw ma283 testy.

Fixture aktorów:`30268bff1368c805d01419f8513cf343f99517c542ecf3dd7c6d00928fdbc6f3`.
Fixture świata:`2d1dc4597711ddde7bfbaf84c66e6bbd58b7d8e9e7a6eb678b2f44c2f25f46dd`.
Build Unity6000.3.27f2 Windows64Mono:152955435B,0 błędów/ostrzeżeń.
DLL:`5d15a7030ef4b8b544937ebb293cb8fd182a65cd435251668697be865b6b93ce`.

Player Windows pod Wine/Xvfb:15 punktów,45 stanów,150 części,510 odczytów
rzeczywistej kolejki i136 publikacji;9 odbiorów/3 emisje,exit0. Emisja10
odtwarzana po odbiorze11,bez resetu slotów lub grid. Końcowa sesja ma poprawiony
opis zakresu QA:normalne busy20 przy58b0 są objęte testem;blokujący arbitraż nie.
Własne3 właściciele póz i zajęcia komórek zwolnione;znany ComputeBufferGC
przy zamykaniu jest wcześniejszym komunikatem,nie ostrzeżeniem buildu.
Regresje na tym samym DLL:świat5388 stanów,live10827,prepared6795,
ownership2486 i130 wejść planera. Starszy lifecycle7 scenariuszy także PASS.
73C#/131meta,3 istniejące C# zmienione,70 bez zmian;275 plików przed/po
buildzie,78Resources/10 stagingów i9 oryginalnych wejść bez zmian.


Nowa diagnostyka dodaje `--ship-fleet-world-busy` do istniejących flag
`--ship-fleet-motion-reference --ship-fleet-world-step
--ship-fleet-world-registration fleet,11,12,13 --terrain-origin-x 9
--terrain-origin-y 0 --terrain-reference-exit-after 1`.
To kontrolowany rejestr i gotowa poczta2,nie odkryta kolejność całej misji.

Ten kod jest w pełni zgodny z istniejącym `SingleStepClock` i nie narusza
deterministycznego stanu w opisanym i przetestowanym zakresie. Pozostają:
blokujący arbitraż58b!=0,inne rodziny zadań,35,Shift zatwierdzonej grupy,
kolejkowane rozkazy i pełny Ship::Life. Zwykły Start pozostaje wyłączony.
Pełna gra,AI,walka,audio,fog,save/load i oprawa2026 nadal w budowie.
Cel1920×1080/16:9/fullscreen;Win11,laptop i wydajność niezweryfikowane.
Nie tworzono PNG,ZIP lub podglądu;bez publikacji/aplikacji środowiska.

Regresja playera InputSystem/Ctrl na tym samym DLL:23 punkty,69 stanów,
230 części,782 odczyty kolejki,136 publikacji,6 pakietów,exit0. Wejście
odsubskrybowane,3 właściciele póz i8 zajęć komórek zwolnione.
