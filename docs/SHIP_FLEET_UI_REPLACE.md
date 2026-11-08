# Kolejny normalny rozkaz grupy podczas ruchu — 2026-11-04

Ukończono ograniczony etap diagnostyczny w istniejącym trybie
`--ship-pointer-fleet-world`:zatwierdzona grupa może przyjąć kolejny zwykły
rozkaz także podczas ruchu. Pierwszy rozkaz i starszy tryb pozostają zgodne
z wcześniejszymi referencjami. Pełna gra nadal jest w budowie.

## Ustalenia x86 i integracja

- `49e230` dla istniejącej grupy pomija `49ca60` i przechodzi przez
  `49de70` do `4ccc30`. Flaga4 oznacza inną,nieodblokowaną ścieżkę Shift.
- `4ccc30` ponownie używa tego samego100/1 i zapisuje counter/cel,parametry1/0.
  Nie zeruje group+8,nie tworzy nowych41 lub zdarzeń300 i nie wykonuje Work.
  W oracle sprawdzono także tożsamość alokacji zadania przed/po żądaniu.
- Dotychczasowa sekwencja świata pozostaje:521500 PrepareMail,
  522850 SendMail,następnie542320/542200 Life. Pozycja grupy względem statków
  jest jawnym wejściem rejestru. Nie ma nowej globalnej fazy grup ani flush.
- Dwa zwykłe rozkazy przed następną fazą pozostają w FIFO:sześć20 ze
  znacznikiem25 trafia do odbioru26. Odbiornik26B zachowuje ostatni zapis
  każdego statku,przed istniejącym arbitrażem80,promocją i Work.
  Kliknięcie samo nie zmienia inbox/ruchu ani nie wykonuje ticku.

`ShipPointerReference.DispatchExistingFleetMove` używa tego samego
`ShipFleetMembership.RequestNormalMove` i tej samej kolejki
`ShipWorldStep.Command`. Przyjmuje tylko wybraną zatwierdzoną grupę
z normalnym zadaniem,gotowym członkostwem SIM i istniejącymi odbiornikami20.
Nie używa idle-only `CanRequestMove` do odrzucania normalnego zastąpienia.
Tymczasowy wybór podczas ruchu lub zmiana składu pozostają poza tym zakresem.
Nie ma bezpośrednich zapisów członkostwa lub zajętości.

Jedynym właścicielem Begin/Complete40ms pozostaje `ShipWorldStep`.
`SingleStepClock`,`ShipWorldStep`,`ShipMoveOrder`,`ShipFleetMembership`,
`ShipFleetNormalTask`,`MissionOccupancyGrid` i adapter póz pozostają bez zmian.
Zmiany obejmują tylko adapter wejścia i istniejący replay InputSystem.
Nowa metoda ma komentarz49e230→49de70→4ccc30. W zweryfikowanym zakresie kod
jest w pełni zgodny z istniejącym `SingleStepClock` i nie narusza
deterministycznego stanu symulacji. Deklaracja dotyczy poniższego korpusu.

## Dowody i zakres testów

12przypadków:4pozycje floty × pojedyncze zastąpienie po10,po100 oraz dwa
zastąpienia po25. Razem2400klatek,16żądań,7248stanów aktorów z granicami
żądań,2416wierszy świata i28kontroli API. Porównano pełne wiersze kadłubów,
clock/mail/registry/publikacje,przydziały/zdarzenia/wiek oraz pola żądania zadania.
Naturalne stany w granicach żądań:0,2,5;58b=0 w kontrolowanym profilu.
To nie dowód osiągalności wszystkich kombinacji blokującego arbitrażu w misji.

UI wykonuje rzeczywisty518070→49e230→49de70→4ccc30 w osobnym emulatorze.
Przed żądaniem otrzymuje jawne komórki,58c i5e od emulatora świata.
Oba źródłowe przebiegi muszą wyemitować identyczne20. Dalej świat wykonuje
w jednym silniku rzeczywistą pocztę,grupę i ograniczone ShipLife Promote+Work.
Nie zastąpiono odbioru,arbitrażu,promocji,planowania lub ruchu modelem Python.
Nie przedstawia się tego jako jednego pełnego RunApp ani dostępnego C/C++.

ShippingDLL potwierdza7248stanów oraz regresje:firstUI7200,cohort7704,
world5388,busyworld5088,live10827 i130przypadków planowania.
4testy celowane PASS0skip88.320s,w tym świeże x86 i3mutacje granicy:
zły counter żądania,utrata wcześniejszego FIFO i natychmiastowy odbiór.
2testy checkera PASS0skip11.440s,z8celowymi błędami kontekstu/stanu/strumienia.
305testów discovery;pełnego zestawu nie uruchamiano.

Dwa rzeczywiste przebiegi playera/InputSystem:flota pierwsza oraz ostatnia,
mail2. Każdy30punktów/90stanów/300części/1020odczytów rzeczywistej kolejki/
229publikacji/12pakietów/exit0. Syntetyczne kliknięcia po25 tworzą cele18,6
oraz16,4;Shift jest jawnie blokowany i nie zmienia zadania lub kolejki.
W26 odebrano wszystkie6nowych20 ze znacznikiem25,z zachowaniem kolejności.
Wiek w obu żądaniach25,przydziały ostatniego celu dla0b/0c/0d to17,4 /18,5 /
16,4,bez wymuszania wspólnego celu. Po ruchu przeszło anulowanie i Ctrl0c
przywołujące całą grupę. Cleanup:3pozy i8claims zwolnione,input odsubskrybowany.

Pierwszy rozkaz przez świat z mail0 oraz starsze sterowanie bez świata:
każdy23punkty/69stanów/230części/782queue/136publikacji/6pakietów/exit0.
Zachowano1920×1080,16:9,ExclusiveFullScreen. Unity6000.3.27f2,
Windows64Mono152966699B,0błędów/0ostrzeżeń. DLL SHA256:
`fa19e56ad2ee9d6902f89e7b5e423cad9d2f215e35182269727e4ae12ee9b235`.
73C#/131unikalnychmeta;2istniejące adaptery zmienione,71C# bez zmian.
275plikówAssets/Packages/ProjectSettings zamrożonych przed/po buildzie;
78Resources/10stagingów/9wejść oryginału zachowane.

Fixture `ship_fleet_ui_replace.json`,SHA256:
`944ac00954fbf02fc12b931bcd521e82e95a80827bf42e60e1d95f11fe82adae`.
Player `ship_fleet_ui_replace_player.log`,SHA256:
`da8e6ac96ff8d62ccd0bb017aabb66bd63263ed5d30a2b149b65834a28daa264`.
Dowody:[artifacts/fleet-ui-replace](../artifacts/fleet-ui-replace).
Punkt kontrolny:[milestone](evidence/milestone-20261104-fleet-ui-replace.json).

## Ograniczenia i wznowienie

Nowy `--ship-pointer-fleet-replace-replay` rozszerza istniejący
`--ship-pointer-fleet-movement-replay`;wymaga jego dotychczasowego trybu
world z jawnym rejestrem. Interakcje są MouseState/KeyboardState w InputSystem,
bez wywoływania metod rozkazu z replaya. Zatrzymania są diagnostyczne,
nie dowodzą naturalnego harmonogramu App,tempa lub wydajności hosta.

Zachowano pierwsze błędy narzędzi:testowego mem_write wymagającego bytes,
obserwatora ostatnich mutacji komórek przypisanego do złego aktora oraz
selektora mutacji trafiającego w dwa miejsca. Skorygowano narzędzia/test,
bez zmiany rdzenia C#. Powtórzone kontrole przechodzą. Znany ComputeBufferGC
przy zamykaniu i deprecacjePillow w QA pozostają,nie są ostrzeżeniami builda.
Nie tworzonoPNG/podglądów/ZIP;kompozycje QA wyłącznieRAM.

Shift/queued100/2,edycja składu zatwierdzonej grupy,inne rodziny zadań,
pełnyShipLife/AI,Start/saveLoad/oprawa2026 pozostają nieukończone lub
niezweryfikowane. Pełna rejestracja oryginalnej misji nadal nieustalona.
Wine nie jest dowodem natywnego Windows11,OSmouse lub docelowego laptopa.
Nie publikowano ani nie aplikowano konfiguracji środowiska.

Następnie:ustalić z x86 semantykę Shift+rozkaz i zadania100/2 oraz przygotować
niezależny korpus przed odblokowaniem tej ścieżki UI. Edycja składu pozostaje
osobnym tematem;nie dodawać automatycznych300/311 lub nowej fazy świata.
