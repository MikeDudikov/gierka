# Źródłowa kolejność kandydatów pickera świata

Stan:2026-11-03. Ograniczony `ShipWorldPicker` zgadza się z oryginalnym x86
w1206 zapytaniach,5665 uporządkowanych wywołaniach predykatu i21 kontrolach
API. Dwa testy celowane przeszły bez pominięć w1,701s. Nie potwierdza to
wejścia Unity ani pełnej inicjalizacji świata. Oryginalny `ancient.exe`
SHA256 `cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`
pozostaje niezmieniony.

## Łańcuch zapytania

`Cursor::GCGameState0x517540` przekazuje wiadomość0xc44f do odbiorcy
`cursor+0xad`. Odbiorcą jest `DumpClassTy::GetMessage0x499560`,który wywołuje
`0x49a580(worldX,worldY,cellX,cellY,precise)` i zapisuje zwrócony wskaźnik
obiektu do wiadomości+0x18. Cursor kopiuje go do pola+0xd9.

Pełny49a580 ma gałęzie fog i kilka slotów różnych rodzajów obiektów.
Ten dowód kontroluje flagę5ca546=0 i zeruje wszystkie sloty poza zwykłą
zajętością jednostki. Nie oznacza to domyślnego stanu mgły nowej misji ani
pełnej polityki wyboru wszystkich45 obiektów miss000.

W tym ograniczonym zbiorze zwykłych statków procedura:

1. Sprawdza właściciela zajętości klikniętej komórki.
2. Przy `precise!=0` sprawdza sąsiednie zajętości w poniższej kolejności.
3. Zwraca pierwszego kandydata,którego rzeczywisty predykat virtual+8 zwróci
   true. Nie sortuje kandydatów według renderer depth i nie usuwa duplikatów
   referencji (ten sam statek może zajmować bieżące pole i rezerwację).

Właściciel zajętości jest pod `grid+8+24*index+4`. Nie jest to którykolwiek
z innych slotów oryginalnej24-bajtowej komórki. Koordynator musi dostarczać
aktualną zajętość i rzeczywistą pozycję/frame statku.

## Oryginalne tablice i granice

Konstruktor `0x499530` wykonuje rzeczywisty bazowy0x542530 i kopiuje9 liczników
z0x597900:3,3,3,3,5,5,5,5,8. `0x499ff0(width)` tworzy tablice offsetów.
`0x49a1d0(cellIndex)` klasyfikuje położenie przy brzegach mapy:

| Kind | Położenie | Kolejność sąsiadów |
| --- | --- | --- |
|1|lewy górny róg|E,SE,S|
|2|prawy górny róg|S,SW,W|
|3|prawy dolny róg|W,NW,N|
|4|lewy dolny róg|N,NE,E|
|5|górna krawędź|E,SE,S,SW,W|
|6|prawa krawędź|S,SW,W,NW,N|
|7|dolna krawędź|W,NW,N,NE,E|
|8|lewa krawędź|N,NE,E,SE,S|
|9|wnętrze|NW,N,NE,E,SE,S,SW,W|

Samo centrum jest sprawdzane wcześniej niż ta tabela. Dla wnętrza sąsiedzi
zaczynają się od NW,a nie od E/N ani od kierunku statku. Query sam nie
stanowi bezpiecznego kontraktu dla dowolnych pozamapowych cellX/Y;oryginalny
wywołujący wcześniej ogranicza obszar wejścia. Dowód używa24×24 i poprawnych
komórek. Przyszły adapter powinien jawnie odrzucać nieobsługiwane wejścia.

## Wykonany dowód

[Oracle](../artifacts/world-input/picking/probe_world_picker_order.py),
[raport](../artifacts/world-input/picking/native-world-picker-order.json),
[log](../artifacts/world-input/picking/native-world-picker-order.log).

**1206 zapytań przeszło**:

- Wszystkie576 komórek mapy,każda coarse oraz precise:1152 zapytania.
-49 możliwych pozycji pierwszego trafienia dla reprezentantów wszystkich9
  rodzajów brzegu;wywołania kończą się dokładnie przy pierwszym sukcesie.
-1 przypadek tej samej referencji w centrum i rezerwacji:predykat wywołuje
  się dwukrotnie,bez deduplikacji.
-4 przypadki dwóch jednocześnie trafionych masek:wygrywa pierwszy kandydat
  źródłowej kolejki zapytania,nie ustawiona ranga sprite'a.

Wykonano całe0x49a580 oraz rzeczywiste0x49a1d0,0x50e590 i wirtualne
`Ship::point0x4e06c0`,wraz z0x5431d0 i0x5575d0. Nie przechwytywano żadnego
powrotu ani callees. Hook na wejściu4e06c0 jedynie odczytuje rejestry/argumenty
w celu zapisania faktycznej kolejności;nie zmienia rejestrów,pamięci ani flow.

Zastosowano syntetyczne normalne obiektyclass200 z prawdziwą vtable59b48c,
geometry56×56 i24 maskami wypełnionymi jedynkami. Pozostałe kandydaty mają
pozycję poza testowanym punktem. To izoluje kolejność zapytania od kształtu
oryginalnych masek. Osobne istniejące432428 porównań masek C#/x86 potwierdza
rzeczywiste type18 maski;niniejszy raport ich nie zastępuje i nie liczy ponownie.

W coarse0 rzeczywisty4e06c0 zwraca true przed testem geometrii. W precise1
używa logicznego prostokąta i dedykowanej maski bitowej,nie alfy renderowanej
grafiki.32…55 wybiera maskę `storedFrame−32`,inne klatki `byte(heading*3)`.
Nie należy używać drawn frame w miejscu stored frame źródłowego predykatu.

Eksporty dodatkowe:
[Dump constructor](../artifacts/world-input/picking/neighbours-export/00499530.c),
[klasyfikacja brzegu](../artifacts/world-input/picking/neighbours-export/0049a1d0.c),
[cały query](../artifacts/units/collision/export/0049a580.c).
## Ograniczony adapter C#

[ShipWorldPicker.cs](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipWorldPicker.cs)
ma SHA256 `877539746bbc49afad876cef0435422b1b5eba53ade49d77c15e544734045930`.
Zawiera niemutowalną `ShipPointerPose(mask,publishedWorldX,publishedWorldY,
storedFrame,heading,runtimeClassTag=200)` i statyczne:

```text
Pick(grid,worldX,worldY,cellX,cellY,precise,describe) -> owner reference / null
```

`describe` jest wywoływane dla każdej faktycznie testowanej zajętej komórki,
także dla powtórzonej referencji. Handler nie filtruje właściciela jednostki
według strony gracza. Zachowuje tylko source ship-slot projection;polityka
wyboru/rozkazów i pozostałe sloty należą do innych warstw.

Adapter jawnie wymaga siatki24×24,komórek w mapie i normalnych klas200…211.
Wywołujący odpowiada za kontrolowany brak fog oraz pusty stan innych slotów.
Poza maskami i prywatnymi tablicami statycznymi nie alokuje na zapytanie.
Nie zmienia zajętości ani flag siatki. Sam `describe` jest zależnością wywołującego.
Używa już osobno sprawdzonego `ShipPointerMask`,a nie kopii predykatu bitowego.

[Nowy oracle](../tools/probe_ship_world_picker.py) wystawia także
`NativeShipWorldPicker.set_actor/set_claims/query`,aby osobne QA mogło
wykonać oryginał dla rzeczywistych masek i aktualnych póz floty.
Nie jest to wywołanie C# udające oracle. Wykonuje te same oryginalne49a580,
4e06c0,5431d0 i5575d0 z wyłącznie obserwacyjnym hookiem.

[Trwała fixture](../tests/fixtures/ship_world_picker.json),SHA256
`cee2e9f5c46c2de4db20068a78b63f3090428534f3d67948f2056abbb92a720b`,
wiąże1206 zapytań,wyniki i każdą odwiedzoną referencję. Przed porównaniem
rzeczywistego C# wykonuje się fresh original i wymaga pełnej równości fixture.
[Probe](../tests/fixtures/ShipWorldPickerProbe.cs) kompiluje się z checked+
i warnaserror+. [Walidator](../tools/validate_ship_world_picker.py),
[raport](../artifacts/world-input/picking/world-picker-csharp-validation.json),
[testy](../tests/test_ship_world_picker.py),
[wynik testów](../artifacts/world-input/picking/world-picker-targeted-tests.log).

21 kontroli obejmuje błędne siatki/współrzędne/delegate/pose/class,brak callbacków
przy błędnym wejściu i pustej siatce,coarse przed geometrią,referencję ownerID0,
klasę211 oraz niezmienność siatki. Osobny test zmienia duplikaty w oryginalnym
śladzie i wymaga odrzucenia przez hash fixture przed optional dependencies.

Dodano jedną klasę i meta,probe,oracle,walidator,dwa testy oraz fixture.
Nie zmieniono dawnych helperów ruchu,masek,scen,pakietów ani dawnych testów.
Nie uruchamiano Unity,Wine,Xvfb,nie tworzono podglądu lub ZIP i niczego
nie publikowano. Rzeczywisty player i most UI wymagają oddzielnej walidacji.
