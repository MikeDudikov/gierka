# Źródłowe żądanie ruchu statku

Stan: 2026-11-02. Potwierdzono wąską drogę przyjęcia i promocji polecenia
ruchu do komórki. Nie jest to implementacja całej kolejki zadań, AI,
pathfindingu, ruchu ani wejścia myszy. Docelowy obraz pozostaje 1920×1080.

Badany `ancient.exe` ma SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Przed wykonaniem sprawdzono również niezmienione SHA misji `miss000.dkx/dkd`
podane w [dowodzie inicjalizacji statków](MISSION_UNIT_INITIALIZATION_EVIDENCE.md).
Boot ID `02fd04eb-5227-4429-806a-a173a569004f` i marker
`root-new-environment-cb830790-marker-20261102` odpowiadają bieżącej sesji.
Oryginały odczytywano bez zapisu, Ghidra pracowała na prywatnej kopii projektu.

## Komunikat zewnętrzny i kopia wewnętrzna

`ShipClassTy::GetMessage` (`0x4dc630`; nazwa klasy pochodzi z napisu błędu)
dla kodu komunikatu `0x280f` z pola `message+0x10` przekazuje
`*(message+0x14)` do `0x4e2ba0`. Wcześniej wykonuje bazowy
`GameObjClassTy::GetMessage`, `0x50c970`. Dla badanego action20 bazowy
handler nie zmienia statku. To nie jest surowy komunikat Windows ani dowód
konkretnego przypisania przycisków myszy.

Pakiet akcji ma bajt akcji pod `+0x0c` i niewyrównany 32-bitowy wskaźnik
danych pod `+0x0d`. Dla akcji `0x14` dane mają postać:

| Offset danych akcji | Wartość |
| --- | --- |
| 0 | 32-bitowy wzorzec docelowego X |
| 4 | 32-bitowy wzorzec docelowego Y |
| 8 | Bajt przekazywany później do pola statku `+0x5c7` |

`0x4e6700(this,0x14,0)` dopuszcza tę akcję wtedy i tylko wtedy, gdy
`capabilities` pod `ship+0x261` mają bit `0x400`. Ta bramka nie sprawdza
własności, statusu życia, granic mapy, zajętości ani osiągalności celu.
Brak tych kontroli w handlerze nie uprawnia UI do wydawania poleceń dowolnym
obiektom; wybór odbiorców znajduje się poza tym dowodem.

Po pozytywnej bramce `0x4e2ba0` tworzy lokalny rekord **26 bajtów**,
zeruje go, wpisuje X/Y i ostatni bajt, po czym woła slot vtable `+4`:
`0x4a9e30(this,0x80,record)`.

| Offset rekordu 26 B | Wartość dla akcji `0x14` |
| --- | --- |
| 0…3 | Zera; bajt 0 jest później trybem nawigacji |
| 4…7 | X, dokładnie 32 bity danych akcji |
| 8…11 | Y, dokładnie 32 bity danych akcji |
| 12…24 | Zera; bajt 12 jest później podtrybem |
| 25 | Bajt z danych akcji `+8` |

`0x4a9e30` kopiuje sześć dwordów i jeden word, dokładnie 26 bajtów,
do `ship+0x858`, potem wykonuje `pending+0x7d6 |= 0x80`.
Rekord jest kopią wartości, a nie przechowanym wskaźnikiem. Kolejne takie
żądanie nadpisuje poprzedni oczekujący rekord. To pojedynczy slot oczekujący,
nie lista waypointów ani FIFO. Zmiana danych wywołującego po powrocie nie
zmienia zapisanej kopii.

## Promocja początkowego żądania

`0x4ab720` rozdziela pending i maskę gotowości `ship+0x7da`.
Konstruktor `0x4dc3f0` ustawia tę maskę na `0xffffffff`.
Status życia `ship+0x251` jest oddzielnym polem od damage-state `ship+0x74`.
Źródłowe `0x4bee60` zapisuje status życia 0 na wejściu, a dla zdrowia poniżej
1 zmienia go na 4. Referencyjny damage-state 1 nie oznacza statusu życia 1.

W badanej początkowej, nieaktywnej gałęzi wymagane są:

- pending z bitem `0x80`;
- status życia 0 i niezerowe `capabilities & 0x1f0`;
- gotowość z bitem `0x80`;
- brak zajętych podzadań w arbitrażu `0x4abe50`.

Wartości statusu życia 1, 2 i 4 blokują badaną promocję, ale **nie** sam
wcześniejszy zapis action20. Oczekujący rekord pozostaje. Podobnie brak
bitu gotowości `0x80` pozostawia rekord do późniejszej promocji. Sam bit
capability `0x400` wystarcza do przyjęcia akcji, lecz bez rodziny `0x1f0`
nie wystarcza do promocji zwykłego action20. Specjalna ścieżka podtrybu 23
ma dodatkowe wyjątki i nie należy do rekordu generowanego przez action20.

W nieaktywnej gałęzi `0x4abe50` czyści aktywne bity `0xf0`; pending80
przechodzi następnie do `0x4ab250`. Wynik tej funkcji jest następujący:

| Pole statku | Zapis |
| --- | --- |
| `+0x54c` | Tryb: bajt pending record 0; tu 0 |
| `+0x54d` | Podtryb: bajt pending record 12; tu 0 |
| `+0x54e / +0x552` | Docelowe X/Y |
| `+0x556 / +0x55a / +0x55e` | Dwordy rekordu pod offsetami 13/17/21; tu 0 |
| `+0x562…+0x582` | Najpierw wyzerowany zakres 33 B; następnie zapisy poniżej |
| `+0x57b / +0x57f` | Odpowiednio 0 i `0x19`; część powyższego zakresu |
| `+0x593 / +0x591` | Odpowiednio 1 i 0 |
| `+0x5c7` | Ostatni bajt rekordu, chyba że wynosi `0xff` |
| `+0x5c8` | 5 |
| `+0x7d6` | Usunięty bit pending `0x80` |
| `+0x25d` | Dodany aktywny bit `0x80` |

Bajt `0xff` jest wartownikiem zachowania wcześniejszego `+0x5c7`, nie
wartością wpisywaną do pola. W ścieżkach nawigacji i kolizji pole jest
porównywane unsigned; nie nadajemy mu nazwy pełnej polityki priorytetów.
Usunięcie capability `0x400` między przyjęciem a samą funkcją promocji
powoduje skasowanie pending80 bez rozpoczęcia akcji dla podtrybu 0.

Promocja nie sprawdza granic współrzędnych. Oracle potwierdził przejście
ujemnych wartości i obu granic int32 do pól celu. To dowód kopii bitów;
nie oznacza prawidłowej ścieżki ani bezpieczeństwa użycia takiego celu
przez późniejszy kod mapy.

`0x4ab930` dla aktywnego bitu `0x80` wywołuje `0x4a5f30`.
Przy `+0x593=1`, trybie 0 ta funkcja odpytuje cel przez `0x4999e0`, wywołuje
`0x4a6330` i zapisuje stan retry przez `0x4a6100`. Dopiero to jest droga do
planner/kernel ruchu. Oracle opisany tutaj kończy się przed tą drogą.
Zegar ma osobny [dowód](SHIP_MOVEMENT_CLOCK_EVIDENCE.md).

## Zastępowanie, kandydat priorytetu i oddzielna kolejka

Ponowne action20 przed promocją zastępuje 26-bajtowy pending record.
Ponowne action20 po promocji, ale przy braku zajętego podzadania, zastępuje
cel w kolejnym przejściu `0x4ab720`. Nie ustalono tu zastępowania celu
statku będącego w środku przejścia między komórkami.

Zajętość sprawdza `0x4abe50` jako pary aktywny bit / niezerowy bajt:
`0x20/+0x739`, `0x40/+0x77b`, `0x10/+0x6a0`, `0x80/+0x58b`,
`0x100/+0x5e2`. W zajętej gałęzi wybiera kandydat `+0x265` w kolejności
**0x20, 0x40, 0x10, 0x100, 0x80**, a następnie woła `0x4abc60`.
Po powrocie kasuje kandydat, jeśli całe pending `+0x7d6` pozostaje niezerowe,
i czyści pending maską `~0x1f0`. Dlatego powyższa kolejność nie jest
dowodem trwałej kolejki priorytetowej. Nowy oracle sprawdza 31 kombinacji
wyłącznie do instrukcji `0x4abef9`, przed wywołaniem anulowania. Nie przenosi
tej gałęzi jako kompletnego systemu kolejkowania.

Funkcje `0x4b9740`, `0x4b97d0`, `0x4bd0c0` dotyczą innej kolekcji:
rekordów 24 B od `+0x485`, z count `+0x482` i index `+0x483`.
`0x4bd0c0` kopiuje do rekordu pięć dwordów danych; pozostały dword ma
osobną rolę. Danych startowych misji dla ośmiu statków jest zero
(`payload+512`), a opisany action20 nie woła tych funkcji i nie zmienia
count/index. Nie nadajemy odzyskanym numerom zadań nazw bez dowodu.

Również wewnętrzny opcode1 `0x4a9e30` **nie** jest listą waypointów:
`0x4ab930 → 0x4bf170` używa pierwszego dwordu jako wskaźnika obiektu
przychodzącego, a drugiego jako jego ID, sprawdza `incoming+0x4c` i obsługuje
obrażenia. Nie należy go wykorzystywać do implementacji ruchu.

## Wykonane kontrole i granice dowodu

Polecenie odtworzenia w bieżącym środowisku:

```sh
.venv/bin/python artifacts/movement/orders/order_oracle.py
```

Raport `artifacts/movement/orders/order-validation.json` potwierdza
**47 przypadków request/promotion: 8 źródłowych i 39 stress**, a osobno
**31 kombinacji prefiksu wyboru priorytetu**. Całe GetMessage oraz
action20/copy/idle consumer wykonują oryginalne instrukcje x86.
Jedyna przechwycona granica w tej fazie to normalny powrót `__setjmp3`.
Obserwatory wywołań nie zmieniają argumentów ani instrukcji.

- Każdy z ośmiu rzeczywistych payloadów 616 B misji dostaje cel sąsiedni
  `(sourceX−1,sourceY+1)`. Dla `OBJ_0000000b` to `(16,2) → (15,3)` przy
  początkowym heading 5. Żadna z tych kontroli sama nie wykonuje ruchu.
- Sprawdzono dokładne 26 bajtów, modyfikację bufora wywołującego po powrocie,
  cztery arbitralne wzorce kopii oraz dwa bajty ochronne poza zakresem.
- Sprawdzono nadpisanie pending, zastąpienie aktywnego niebusy celu,
  odroczoną gotowość/status i późniejsze wznowienie, pięć masek wejścia,
  cztery maski rodzin capability konsumenta, statusy 0/1/2/4, maski gotowości,
  siedem wartości bajtu/wartownika i pięć skrajnych par współrzędnych.
- Zarejestrowano brak wywołań `0x4b97d0/0x4bd0c0` dla źródłowych requestów
  i brak zmiany count/index tej oddzielnej kolejki.

Stan wejściowy pochodzi z oryginalnego konstruktora i LoadDateBase, jednak
w fazie przygotowania jawnie pominięto `0x4bee60` (pochodna inicjalizacja)
i `0x50e640` (komunikat systemowy). Stan życia 0 po tej granicy jest zgodny
z pierwszą instrukcją źródłowego `0x4bee60` oraz dodatnim zdrowiem source8.
App/system i payload są jawnymi wejściami oracle. Nie jest to dowód pełnego
StartGame ani przypisania wszystkich wskaźników w rzeczywistym lifecycle.
`0x4e7220` i jego inicjalizacja flag wykonują się normalnie. Nie wykonano
systemowego EXE, Unity, Wine, pathfindingu, pełnego Life, AI ani grywalnej misji.

SHA256 skryptu natywnego oracle:
`8977282a28ece07b51d1e96663346a369538b99a9eca3b36021f9e9e7bc6a0e2`.
SHA256 raportu:
`1b460f6bbb187de7633039b8aee3a8cd92e570de6af8923e07db3eb5909db801`.
Eksporty źródłowe i logi Ghidry znajdują się w
`artifacts/movement/orders/export*`.

## Izolowany adapter C# i porównanie różnicowe

`Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipMoveRequestInbox.cs`
udostępnia wyłącznie powyższy początkowy zakres. Nie tworzy statku ani
samodzielnego kontrolera ruchu. Kontrakt wywołującego jest jawny:
wszystkie badane flagi busy pozostają zerowe.

- Konstruktor przyjmuje `capabilities`, `readyMask=uint.MaxValue`, `status=0`
  i początkowy `routeByte=0`.
- `UpdateContext(capabilities,readyMask,status)` aktualizuje jawne wejścia
  bramek, nie wykonuje ruchu.
- `RequestCellMove(x,y,opaqueByte=255)` zwraca przyjęcie kopii, nie
  osiągalność celu.
- `CapturePendingRecord()` zwraca nową, niezależną kopię 26 B, również po
  promocji lub przy braku pending. Źródło zachowuje bajty po usunięciu flagi.
- `ConsumeInitialIdleMove(busyContext=false)` zwraca enum
  `None`, `Deferred`, `Discarded` albo `Promoted`.
- Publiczne wyniki to `PendingFlags`, `ActiveFlags`, `HasPendingMove`,
  `TargetX/Y`, `RouteByte`, `FirstMove`. Nie obejmują cudzych typów poleceń.

Status spoza 0/1/2/4 i jawnie wybrany busy context kończą się
`NotSupportedException`. To **ograniczenie adaptera**, a nie twierdzenie,
że oryginał tak odrzuca wszystkie inne stany. Odrzucenie jest atomowe.
Brak pending daje `None`. Bramka statusu lub rodziny capability daje
`Deferred` przed zmianą ActiveFlags. Przy dopuszczonej rodzinie arbitraż
idle kasuje poprzedni aktywny bit80 **przed** kontrolą ready; brak gotowości
pozostawia wtedy pending i poprzedni cel, ale kasuje poprzedni active80.
Utrata cap400 przy zachowanej rodzinie capability i ready daje `Discarded`.

Trwały walidator `tools/validate_ship_move_request.py` odtwarza wszystkie
wcześniejsze 47 native request/promotion oraz 31 prefiksów. Dodatkowo
porównuje actual C#, skompilowany z `/checked+`, z oryginalnym x86 w
**45 scenariuszach i 169 obserwacjach stanu po operacjach**, z czego osiem
scenariuszy wykorzystuje rzeczywiste source8. Scenariusze częściowo
pokrywają wcześniejsze 47; nie należy sumować ich jako odrębnych 92
zachowań. Sprawdzono także 10 kontraktów adaptera, w tym izolację kopii
i odrzucenie unsupported context bez częściowej zmiany. Scenariusze
różnicowe obejmują ochronę starego requestu przy odrzuconym nowym wejściu.
Test porównuje także pośrednie pending, active i rekordy, nie tylko końcowy cel.

Źródłowy fixture `tests/fixtures/ship_move_request.json` ma SHA256
`f8f3b012b0308479ca80322b1a7903b3b217b889a63e2b75c0132faac79ff6b0`.
Jest odtwarzany przez x86 przed porównaniem z C#, a jego SHA jest przypięty
w walidatorze. Nie generuje się oczekiwań przez wywołanie portu C#.
Raport końcowy: `artifacts/movement/orders/csharp-validation-final.json`.
SHA256 niezmienionego C#:
`62eb735aae590d46f42a12f789f4b2278ec71d0ca98bfbe0b6633ceacd183217`.

```sh
.venv/bin/python tools/validate_ship_move_request.py --output artifacts/movement/orders/fresh-check.json
.venv/bin/python -m unittest tests.test_ship_move_request -v
```

Skrypt wymaga świeżej ścieżki raportu i zachowuje wcześniejsze dowody.
Zwykły `python3` bez opcjonalnych pefile/unicorn lub danych źródłowych
oznacza kontrolę jako skipped, zamiast powodować błąd importu testów.
Niezależny read-only review adaptera nie wykazał rozbieżności w badanym
zakresie. Nie wykonywano kompilacji Unity ani runtime QA przez ten walidator.
