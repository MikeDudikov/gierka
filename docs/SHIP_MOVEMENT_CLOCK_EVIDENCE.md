# Zegar statków i doprowadzenie kroku do Ship::Life

Stan: 2026-11-02. Docelowy obraz pozostaje 1920×1080, 16:9 i pełny ekran.
Ten dowód dotyczy czasu w jednej ścieżce oryginalnego kodu x86; nie uruchamia
pełnej gry, ruchu, AI ani źródłowego zegara w Unity. Nie ustala arbitralnego
FixedUpdate ani 60 Hz.

Badano niezmieniony `ancient.exe`, SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Punktem wyjścia są [dowody gałęzi zegara](SIMULATION_CLOCK.md) i rzeczywisty
`SingleStepClock.cs`. Nowy oracle uzupełnia je o drogę do handlera statku,
nie poszerza wcześniejszych 1287 porównań C#/x86 na całą pętlę gry.

## Cztery różne wartości czasu

| Wartość źródłowa | Znaczenie w badanym kodzie | Jednostka / granica |
| --- | --- | --- |
| `app+0x18` | Zapamiętany odczyt czasu aplikacji; getter `0x5417d0` to `MOV EAX,[ECX+0x18]; RET` | 32-bitowy wzorzec czasu oparty na `timeGetTime`; nie licznik kroków statku |
| `PlaySystem+0xe6` | Faza poprzednio rozliczonego czasu w badanej gałęzi | Taka sama dziedzina jak czas aplikacji |
| `PlaySystem+0xe2` | Liczba kroków dostępna podczas callbacków | W tej konkretnej gałęzi 0 albo 1; w innych ścieżkach nie wolno zakładać tej granicy |
| `PlaySystem+0xde` | Narastający licznik przyjętych kroków | Dodanie `+0xe2` z zawijaniem 32-bitowym; nie milisekundy |

`AppClassTy::RunApp` pod `0x541600` odczytuje import WinMM `timeGetTime`,
uwzględnia okres pętli i zapisuje pole `app+0x18`, zanim wywoła iterację
`0x541520`. Getter `0x5417d0` nie wykonuje nowego odczytu zegara OS.
Nazwa `GetPosAppMessageTime` nie jest odzyskanym symbolem ani napisem z EXE;
identyfikację tego prostego gettera opieramy na adresie i instrukcjach.
Nie wolno wywoływać zegara OS osobno dla każdego statku i uznać tego za tę
samą sekwencję źródłową.

Domyślna konfiguracja pod `0x5016a0` zapisuje indeks prędkości 5; może go
później zastąpić konfiguracja lub zapis gry. Pierwszy dword rekordu
`0x5bed74 + index*24` ma dla indeksów 1…9 wartości
13, 17, 20, 33, 40, 50, 60, 70, 80. Drugi dword jest okresem pętli aplikacji,
a nie dodatkowym mnożnikiem wzoru ruchu. Dla indeksu 5 oba wynoszą 40.
To nie dowód stałej częstotliwości wszystkich trybów lub rzeczywistego FPS.

## Od iteracji aplikacji do statku

Potwierdzona droga wywołań wygląda następująco:

1. `0x541520` wywołuje `0x5413c0`, które uruchamia slot vtable `+0x1c`
   aktywnych systemów i przechodzi ich dzieci. Rozpatrywanym systemem jest
   `PlaySystemClassTy::Life`, `0x51fdb0`.
2. Play::Life odczytuje wspólny czas przez `0x5417d0`. Jeśli wybrano gałąź
   pod `0x520352`, dzieli signed różnicę od fazy przez aktualny kwant.
   Niezerowy iloraz ogranicza przez unsigned porównanie do jednego kroku.
3. Przed callbackami zapisuje `+0xe2=1` i dodaje krok do `+0xde`. Następnie
   woła kolejno `0x521500`, `0x522850`, `0x542320`.
4. `0x521500` obsługuje m.in. rekordy/wejście. `0x522850` ma diagnostyczną
   nazwę `PlaySystemTy::SendMail`: wysyła rekordy, m.in. komunikat `0x280f`.
   Nie jest samą funkcją przesuwania statku. Nowy oracle pomija pierwszy
   callback i wykonuje SendMail tylko dla pustego zbioru rekordów.
5. `SystemClassTy::Life`, `0x542320`, obsługuje kolejkę, zeruje 32-bajtowy
   komunikat i podaje go do `GetToAllObjects`, `0x542200`.
6. `0x542200` iteruje tablicę obiektów pod `system+0x10`, wywołując ich slot
   vtable `[0]` z tym samym komunikatem. Dla `ShipClassTy` jest to
   `GetMessage`, `0x4dc630`. Pole komunikatu `+0x10` wynosi 0; żaden argument
   komunikatu nie przenosi tu delta-ms.
7. Ship::GetMessage dla komunikatu 0 i istniejącego głównego sprite’a
   wywołuje `Ship::Life`, `0x4dec40`. Bieżący krok i licznik są wtedy nadal
   dostępne przez wskaźniki systemowe obiektu.
8. Po callbackach Play::Life zeruje `+0xe2`, ponownie odczytuje aktualny kwant
   i fazę, po czym aktualizuje fazę z signed resztą. Czyste API C# zachowuje
   to przez rozdzielenie `Begin` i `Complete`.

W obiekcie statku są dwie odrębne drogi dostępu:

- `*(ship+0x0c)+0xe2`: mnożnik kroku w `MoveShip`, `0x4a3f40`;
- `*(ship+0x70)+0xde`: znaczniki czasu w Ship::Life, ruchu i animacji.

Źródłowe powiązanie **obu wskaźników z tym samym PlaySystem** ma osobny
dowód dla tworzonego statku:

- `CreateObject 0x541ad0` otrzymuje this PlaySystem od wrappera i pod
  `0x541b2d` zapisuje factory object+0x0c=this.
- `Ship` ctor `0x4dc3f0` wywołuje GameObj ctor `0x50b8f0`, który pod
  `0x50b900` zeruje object+0x14. Fabryka nie zastępuje tej wartości.
- Wrapper wczytywania obiektu `0x51f0e0`, wywołany przez źródłowy loader,
  dla object+0x14==0 ustawia +0x68=this+0x18 (app), +0x6c=this+0x1c oraz
  pod `0x51f128` +0x70=this. Generic +0x0c i dodatkowy +0x70 wskazują zatem
  ten sam system przy tym tworzeniu.

`pointer-bind-validation.json` wykonał trzy właściwe bloki oryginału bez
hooków dla czterech ID, w tym 0b; kontrola object+0x14=1 potwierdziła
pominięcie dodatkowego bindowania. Wcześniejszy oracle doprowadzenia czasu
podawał oba wskaźniki jawnie; powyższy osobny dowód uzasadnia ich alias dla
nowego GameObj/Ship, bez deklaracji wykonania całego StartGame lub wszystkich
późniejszych zmian właściciela. Ślad źródłowy i hashe:
`artifacts/movement/time/bind-c/source-bind.json`.

## Co czas zmienia w ruchu i grafice

W badanym fragmencie `MoveShip`, `0x4a3f40`:

```text
nowa_prędkość = dotychczasowa_prędkość + pendingSteps * przyspieszenie
akumulator = reszta + pendingSteps * nowa_prędkość
przesunięcie_i_reszta = signed dzielenie akumulatora przez 3000
```

To tylko widoczne zależności czasowe. Oryginał ma ponadto ograniczenia
prędkości, wiatr, stany ruchu, kierunki, podział osi, maski i zmiany komórek.
Nie jest to kompletny przepis kinematyki. Szczegóły samego ruchu należą do
osobnej analizy i jej [oracle przygotowanej trasy](../artifacts/movement/kinematics/prepared-path-kinematics.json).
Przekazanie pendingSteps 2 nie musi dać tego samego wyniku co dwa wywołania
z 1: aktualizacja prędkości i pozostałe skutki zachodzą w innym porządku.

W tym głównym wzorze ruchu nie występuje delta-ms ani ułamek fazy `+0xe6`.
Kwant 40 wpływa na częstość przyjętych kroków badanej gałęzi, a nie przez
mnożenie prędkości przez `40/1000`. Nie wykazano tu kompletnego kontraktu
interpolacji lub wszystkich innych ścieżek renderera.

Animacja podstawowego sprite’a czyta licznik kroków, np. w turn `0x4a3320`
i końcu `0x4a3f40`:

```text
uint32(nowStepCounter - sprite.lastStepCounter) > sprite.threshold
```

Porównanie jest **strict `>`**, nie `>=`. `0x4e0160` ustawia próg `sprite+0x7d`
na 2. Przy niezmienionym progu i kolejnych pojedynczych krokach różnice 1 i 2
nie przekraczają progu, a 3 go przekracza. Jest to próg w krokach, nie 2 ms.
Dobór klatek, tryb idle i RNG mają osobny dowód agenta animacji; nie przenosimy
tego progu na wszystkie efekty statku.

Rysowanie świata w `AncientAppTy::CommonFunction`, `0x4ef530`, ma odrębny
warunek czasu ponad 39 oraz dodatkowy licznik z tabeli prędkości. Samo
odświeżanie obrazu nie oznacza kolejnego kroku ruchu. Nie należy dodawać
kroku symulacji przy każdym renderze ani kopiować tego progu jako całego
zegara animacji.

## Wykonane kontrole

`artifacts/movement/time/validate_ship_clock.py` tworzy świeży raport
`ship-clock-validation-final.json`. SHA oryginału jest wymagany przed
wykonaniem. System operacyjny nie uruchamia EXE; pracuje emulator x86.

- Osiem pełnych wywołań gettera `0x5417d0`, bez hooków, potwierdza powrót
  dokładnego wzorca 32-bitowego, w tym `0xffffffff`.
- 76 przypadków zaczyna się od **wejścia** `Play::Life 0x51fdb0`, przechodzi
  jego rzeczywiste warunki i kończy na połączeniu `0x5209e2`. Obejmuje wszystkie
  dziewięć kwantów, dwie fazy, granice kwant−1/kwant/kwant+1, przestój 5000,
  ujemne signed różnice oraz zawijanie czasu i licznika.
- 57 przyjętych kroków dotarło rzeczywistą drogą System::Life →
  GetToAllObjects → Ship::GetMessage do przechwyconej granicy Ship::Life.
  Każde wywołanie widziało pendingSteps 1 i licznik po inkrementacji, a jego
  komunikat miał dokładnie 32 zerowe bajty. Połączenie zegara kończyło się
  pendingSteps 0. Duży przestój nadal dawał jeden callback, bez nadrabiania
  wszystkich zaległych kroków.
- Trzy dodatkowe kontrole wykonały wczesny gate app+0x322d, inną gałąź
  app+0xd7c=0 z this+0x28=0 oraz inną gałąź GameSystem+0x17e6≠0 z pending=0.
  Żadna nie weszła do `0x520352`. To dowód tych konkretnych kombinacji,
  bez przypisywania im kompletnej semantyki pauzy, sieci lub replay.
- Rodzime pomocniki scope listy `0x5593a0/0x570320`, iteracja i wysyłanie
  zerowego komunikatu wykonują się bez hooków. Użyto syntetycznych pustych
  kolejek oraz tablicy z jednym obiektem. ID11 i komórka16,2 odpowiadają
  OBJ_0000000b, ale jego konstruktor i pełna inicjalizacja nie są wykonywane.
- Przecięte granice to normalny setjmp, callback wejścia `0x521500`, samo
  Ship::Life `0x4dec40` i efekt widoczności `0x50d400`. **Ship::Life nie jest
  wykonane w tym oracle**; rejestrujemy tylko parametry w chwili jego wywołania.
- Osobno wykonano cztery przypadki bindowania i kontrolę gałęzi innej klasy,
  bez hooków, w blokach 0x50b8f8…0x50b94f, 0x541b15…0x541b30 oraz
  0x51f104…0x51f12b. Nie wykonano fabryki, pełnych konstruktorów, wstawienia
  do listy ani skutków message2. Dowód zachowuje tę granicę.
- Wcześniejszy raport 1287 C#/x86 jest wykorzystany z weryfikacją SHA bieżącego
  pliku `SingleStepClock.cs`. Nie wykonano ponownie całej tej serii bez potrzeby.

[SIMULATION_CLOCK.md](SIMULATION_CLOCK.md) zachowuje dokładne warunki wymagane
przez badaną gałąź. Powyższe kontrole nie zamykają wyboru wszystkich trybów.
Nie wykonano OS timera, pełnego lifecycle, AI, poleceń ani ruchu w Unity.

## Kontrakt dla jawnego replayu diagnostycznego

Można niezależnie podać: zapisany czas aplikacji, fazę, indeks/kwant,
licznik kroków, pendingSteps oraz stan statku i sprite’a. Caller musi jawnie
wybrać zakres badanej gałęzi. Dla tej gałęzi:

1. Obliczyć `SingleStepClock.Begin` ze źródłowych wejść.
2. Tylko po przyjęciu kroku udostępnić pendingSteps 1 i zaktualizowany licznik
   wszystkim badanym callbackom. Nie zamieniać liczników na sekundy.
3. Zachować kolejność wejście → SendMail → Life, o ile te warstwy są w zakresie
   replayu; przy samym przygotowanym kernelu ruchu jawnie wyłączyć pozostałe.
4. Dopiero po callbackach wywołać `Complete` z ponownie odczytaną fazą i kwantem.

Taki replay jest powtarzalnym testem z jawnymi danymi czasu. Nie stanowi
nowego zegara pełnej gry, samodzielnej nawigacji ani dowodu identycznego
StartGame. Nie podłącza się automatycznie do Unity Time.deltaTime/FixedUpdate.
