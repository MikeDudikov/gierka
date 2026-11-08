# Zadania grup w kroku świata — 2026-11-04

**Historia pierwszej integracji.** Nowy odbiorca normalnych ponowień20 podczas
ruchu:[SHIP_BUSY_ORDERS.md](SHIP_BUSY_ORDERS.md). Kolejność faz pozostaje
niezmieniona;poniższe wyniki odnoszą się do wcześniejszego DLL.


`ShipWorldStep` łączy istniejące `SingleStepClock`, `ShipFleetMembership`,
`ShipFleetNormalTask` i `ShipMoveOrder`. To czysty C#, bez UnityEngine,
nowego zegara, ECS, Update lub źródła czasu. Zintegrowany przebieg jest
dostępny w istniejącej diagnostyce trzech statków. Zwykły Start nadal
pozostaje wyłączony;nie jest to kompletna pętla całej gry.

## Analiza kolejności x86

1. **Nie ma osobnej fazy „wszystkie grupy przed statkami”.** `542200`
   iteruje wektor `System+10`,rekord8B,wskazanie obiektu+4. Obiekt floty
   (`49ab30`,wiadomość0) pracuje w swoim miejscu rejestracji;statki w swoich.
   `4c4f40→4ccd80` wykonuje zadanie grupy. Dokładnej kolejności rejestracji
   całej oryginalnej misji nadal nie dowiedziono. Coordinator wymaga jawnego
   wektora,bez sortowania po rodzaju lubID. Test obejmuje wszystkie24
   permutacje floty i trzech statków.
2. **Poczta poprzedza Life.** Wybrana gałąź `520352..5203ec` wywołuje
   `521500 PrepareMail→522850 SendMail→542320 SystemLife`. Zatem rozkaz
   wygenerowany przez zadanie podczas Life zostaje w wychodzącej kolejce;
   ponowne opróżnienie jej w tym samym kroku byłoby odstępstwem od x86.
   Pakiety już przygotowane są dostarczane przed promocją `4ab720` i Work
   `4ab930`,więc mogą być promowane w **tym samym kroku odbioru**.
   Przykład źródłowy:emisja20 w201,odbiór i promocja w202.
3. **Cały cykl jest między Begin i Complete.** Po `Begin` aktualizowany
   jest counter;wykonują się przygotowanie i odbiór poczty oraz odwiedziny
   zarejestrowanych obiektów z pending1. Dopiero potem `Complete` oblicza
   fazę z czasu przechwyconego przez wywołującego. Adapter Unity konsumuje
   uporządkowane publikacje po zakończeniu symulacji.

## Wybrany profil i synchronizacja

Profil to normalna niedemonstracyjna gałąź40ms,indeks prędkości5:
rekord `5bed74+5*24` ma wartości `(40,40,5,1,40,2)`.
`System+3e` poniżej2 rośnie o1 i pozostawia pocztę w kolejce.
Po osiągnięciu2 przygotowywana jest cała bieżąca kolejka FIFO;normalny
niedemonstracyjny powrót **nie resetuje3e**. Początkowe0,1 i2 są testowane.
Nie należy wywodzić z40ms bezwarunkowego odbioru na każdym zimnym kroku.

`ShipWorldStep.TryAdvance` przyjmuje czas,fazę,counter,teren i wychodzącą
kolejkę. Konstruktor otrzymuje istniejące członkostwo,siatkę,aktorów,
wektor rejestracji i początkowy licznik poczty. Kolejka i stan pozostają
własnością wywołującego. Publikacje,odwiedziny,emisje i odbiory są
obserwowalne tylko przez odczyt;payloady są kopiowane.

Jedynym punktem zmiany symulacyjnego słowa grupy5e jest istniejący
`ShipFleetMembership.ConsumeNext` przy odbiorze41 (`50c970`). Odczyt grupy
przez aktora i planner wskazuje `GetSimulationGroup`,nie UI5c lub drugą kopię.
Siatka nie jest zapisywana przez coordinator;istniejące `ShipMoveOrder.Tick`
zachowuje wyłączną odpowiedzialność za rezerwacje i ruch. Stan komórek
i fizyki dla zadania jest odczytywany w miejscu odwiedzin floty.
Żadna zmiana w członkostwie,zadaniu,siatce,ruchu ani zegarze nie była
potrzebna w tym etapie.

Przed dostarczeniem wykonywane są jawne kontrole zakresu projekcji:
nieznany adresat,zła kolejność41,rozbieżne countery,zajęty odbiorca20,
duplikat20 w jednym odbiorze i35 zostają odrzucone. To ograniczenia
nieprzeniesionych gałęzi,nie nowe reguły gry. Nie wolno usuwać tych
blokad ani resetować sztucznie active80 po dotarciu do celu.

## Dowody i ich granice

Źródło:oryginalny `ancient.exe`,SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Brak plików C/C++;komentarze C# odnoszą się do adresów i offsetów.
Fixture `ship_world_step.json`,SHA256
`d4fe29c10cbbf7a86232754748d9c52f654bc2792f5be6808071a7972b74f66f`.

Nowy oracle wykonuje rzeczywisty blok zegara,przygotowanie i wysyłkę poczty,
PlaySystem `51f1e0`,obieg obiektów,zadanie grupy,odbiór41/20 i rdzeń ruchu
w jednym silniku x86. **Ship::Life jest granicą:**zamiast pełnego `4dec40`
kontrolowana trampolina wykonuje oryginalne `4ab720` i `4ab930`.
Pozostałe Life,widoczność,inicjalizacja całej aplikacji,renderer i audio są
wyłączone lub mają dotychczasowe granice harnessu. Kolejki komunikatów
SystemLife przed i po rejestrze są puste. Test nie dowodzi tych gałęzi.

Pierwszy pilot używał ogólnej tablicy System zamiast PlaySystem i nie
dostarczał typu4. Jest zachowany jako historia,**nie jako dowód odbioru**.
Końcowy oracle używa źródłowej tablicy `59b828` i wymaga rzeczywistych
odbiorów w każdym przypadku. Wczesny błąd eksportu Ghidry dla funkcji
zewnętrznej jest również zachowany;wyniki końcowe wymagają udanego eksportu.

| Kontrola | Wynik |
| --- | --- |
| Świeży x86 i C# |31 scenariuszy,1796 klatek,1736 zaakceptowanych kroków,5388 pełnych stanów aktorów;24 kolejności rejestracji |
| Poczta i publikacje |174 odbiory,76 emisji,1462 publikacje;adresaci,kolejność,stamp i payload zgodne |
| API |20 kontroli;checked+/warnaserror+ |
| Testy celowane |4 PASS,0 pominięć,75.531s;3 nowe i regresja1287 przypadków zegara |
| Mutacje |5 wykrytych:błędna bramka poczty,ponowny odbiór,kolejność rejestru,zły stamp,pominięcie41 |
| ShippingDLL |Powyższe31/1796/5388 oraz wcześniejsze7086 porównań członkostwa,rozkazów,Ctrl i zadań PASS |
| Build |Unity6000.3.27f2 Windows64Mono,152954411B,0 błędów/ostrzeżeń |
| Nowy player |14 punktów,42 stany,140 części,476 rzeczywistych odczytów kolejki,98 publikacji;exit0 |
| Regresja sterowania |23 punkty,69 stanów,230 części,782 odczyty,136 publikacji,6 pakietów InputSystem/Ctrl;exit0 na tym samym DLL |
| Integralność |73C#/131 unikalnych meta;2 istniejące C# zmienione+1 nowy;70 dawnych bez zmian;275 plików przed/po buildzie;78Resources/10 stagingów/9 źródeł bez zmian |

DLL:`392620c155dc41fde6d61f1c30162d7c8c05113cb9ccc4d37f7a6873c71183cf`.
Pełnego discovery nie ponawiano;nowy zestaw ma280 testów.
Pierwsze uruchomienie testów poprawiono w harnessie:normalizacja tuple/list
po JSON oraz zastąpienie mutacji bez obserwowalnego skutku. Końcowy PASS
dotyczy ponownego świeżego wykonania x86,nie tylko zapisanej fixture.

Nowy player wymaga jawnie:

```text
--ship-fleet-motion-reference --ship-fleet-world-step
--ship-fleet-world-registration fleet,11,12,13
--terrain-origin-x 9 --terrain-origin-y 0 --terrain-reference-exit-after 1
```

To **kontrolowana** kolejność i gotowa poczta2,nie odkryta kolejność misji
lub pełny zimny Start. Wybrany jest tylko0b;0c/0d nadal wykonują normalny
idle.Work. Zdarzenie300 przed201 wywołuje ponowny rozkaz. Log potwierdza
pozostawienie go w kolejce201,odbiór202 i promocję aktora.
Adapter stosuje wszystkie publikacje przez istniejący właściciel póz
i kolejkę głębi. Test porównuje również źródłowe numery sprite’ów i pozycje;
nie wykonuje nowej walidacji pikseli. Nie powstały PNG,ZIP lub podgląd.
Trzej właściciele póz i8 zajęć komórek zostali zwolnieni;regresja odłącza
wejście. W logach pozostaje znany wcześniejszy komunikat zwalniania
ComputeBuffer przy zamykaniu;nie jest ostrzeżeniem buildu Unity.

Ten kod jest w pełni zgodny z istniejącym `SingleStepClock` i nie narusza
deterministycznego stanu w opisanym i przetestowanym zakresie. Zachowuje
`ShipFleetMembership` i `MissionOccupancyGrid` oraz ich punkty synchronizacji.
Nie jest to potwierdzenie deterministyczności całej nieukończonej gry.

Pozostają:busy20 `4e2ba0/4abe50/4ab250`,35,Shift zatwierdzonej grupy,
kolejkowane zadania,inne kohorty,rejestracja całej misji,AI,walka,fog,audio,
save/load,pełny Start i oprawa2026. Natywny Windows11,docelowy laptop
i wydajność nie zostały sprawdzone. Cel1920×1080/16:9/fullscreen bez zmian.

Raporty:`artifacts/world-group-loop/`. Poprzedni etap:
[własność grupy](SHIP_FLEET_GROUP_OWNERSHIP.md). Następny krok:udowodnić
arbitraż20 przed odblokowaniem kolejnych rozkazów i Shift w UI.
