# Źródłowy hover, cache wskaźnika i wybór rodzaju kursora

Stan: 2026-11-03. `ShipPointerHover` zgadza się z rzeczywistym oryginałem x86
w **2327 stanach, 2319 zapytaniach c44f i 288 uporządkowanych wizytach masek**.
Sprawdzono 15 kontroli API. Trzy testy celowane przeszły bez pominięć w 16,789 s.
To ograniczona logika normalnego wskaźnika źródłowego 0b, bez pełnej gry,
mgły, wyboru grup, walki i natywnego wejścia Windows.

## Punkty wejścia i kolejność

`Cursor::GetMessage` (0x518d90) przy 0x60 porównuje najpierw współrzędne
**ekranu**. Przy ich zmianie w trybie 2 zeruje `hasMapPosition` (+0xb9)
i fazę `blocked` (+0xe6), po czym przekazuje zdarzenie mapie.
Normalny `Mapa::GetMessage` (0x51cd60) ogranicza obszar i wywołuje
`Cursor::SetMapXY` (0x517a60) z pozycją świata i komórki.

`SetMapXY` porównuje pozycję **świata**. Dopiero jej zmiana zapisuje świat,
komórkę, screen i `hasMapPosition=1` oraz uruchamia `GCGameState` (0x517540).
Zatem zmiana screen przy identycznym world może pozostawić `hasMap=false`.
Ponowne wejście w ten sam world po anulowaniu także nie wymusza poprawy flagi.
Nie należy dodawać ponownego uaktywnienia na podstawie samego release.

Brak ruchu nie oznacza braku hover: `GetMessage` przy wiadomości 0
(Life kursora) wywołuje `517540(1,-1,-1)`. Każdy taki krok ponownie wykonuje
c44f z ostatnim **cached world/cell**, jeżeli hasMap jest prawdziwe.
Poruszony statek lub nowy STORED frame maski może zmienić target pod
nieruchomym wskaźnikiem. Refresh przy `hasMap=false` nie wykonuje query,
ustawia standardowy kursor 0 i maskę akcji 0; stara pozycja i target pozostają
w cache. Nie wykorzystuje świeżych współrzędnych samego button-up.

Dwukrotny zoom 1920×1080 jest odpowiedzialnością osobnego mostu prezentacji.
Przed tym helperem screen ma logiczne piksele źródłowego widoku; połówkowy
ruch w pikselach HD nie może sztucznie zerować source hasMap. Move otrzymuje
już poprawne współrzędne wewnątrz mapy 24×24, wyliczone normalnym mapowaniem.
Clipping pełnego viewportu HD i anulowanie urządzenia to osobne warstwy.

## Ograniczone wyniki normalnego kontekstu 0

| Kontekst | Oryginalny wynik |
| --- | --- |
| Brak wyboru, picked lokalny normalny statek | Type 5, `CUR_OWN_` |
| Brak wyboru, puste miejsce | Type 0, `CUR_STD_` |
| Brak wyboru, picked obcy statek | Brak SetGCType; poprzedni rodzaj może pozostać |
| Wybrany 0b, picked ten sam 0b | Type 6, `CUR_SELECT_` |
| Wybrany 0b, puste miejsce, cap400 i teren przejezdny oraz niezajęty | Type 7, `CUR_SEA_` |
| Wybrany 0b, puste miejsce bez cap400 lub nieprzejezdne/zajęte | Type 0 |
| Wybrany 0b, inny lokalny statek z cap4 | C452 daje type100/mask101; GCGameState wybiera pierwszy bit → type5, E2=101, E4=1 |
| Wybrany 0b, inny lokalny statek bez cap4 | Type 5, mask 0 |

Brak maskowego trafienia nie oznacza pustej komórki. Przezroczysty fragment
w komórce zajętej przez statek nadal blokuje `499a40`; nie daje automatycznie
SEA. W normalnym noFog źródłowy C451 wykonuje rzeczywiste
`4e6700(action20)`, `50e800` (zwrot −1), a następnie `499a40/4999e0`.
Nie zastąpiono tego kolorem wody lub nazwą kafelka.

Po c451/c452 `517540` rozstrzyga reply przez maskę akcji. Nie zeruje E4,
gdy E2 staje się 0. Jeżeli maska 101 się nie zmieniła, zachowuje aktualny
bit cyklu i rodzaj kursora; porównanie obejmuje także jawnie zaimportowane
state12/bit100 jako zewnętrzny stan po release. Helper nie implementuje
samego cyklu przycisku ani renderowania tego dodatkowego rodzaju.
Wybrany 0b nad obcym celem/atak pozostaje jawnie poza kontraktem.

## C# API

[ShipPointerHover.cs](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipPointerHover.cs)
ma SHA256 `ca46d0900ee785c40a5e6909c11c31ca7b853c48f57fe7b0a6c42d42663540b6`.

- `ShipHoverActor(side,player,capabilities,classTag)` opisuje normalny kind1,
  klasy 200…211. Dane wszystkich ośmiu statków pochodzą z wcześniejszej
  przypiętej fixture konstrukcji/LoadDateBase. Capabilities 0b/0c/10 to
  `fffff7ff`, a 0d/27/28/29/2a to `fffffeff`; nie uogólnia się pola 0b na flotę.
- Konstruktor `ShipPointerHover(grid,controlledOwner,poses,actors,localSide=1,localPlayer=1,selector=0)`
  przyjmuje dwie lokalne funkcje opisujące pozy i metadane. Nie posiada
  rendererów lub obiektów Unity.
- `Move(screenX,screenY,worldX,worldY,cellX,cellY,selected0b)` stosuje oba
  źródłowe porównania. Jego false oznacza brak aktualizacji world/query,
  ale może już zmienić screen i hasMap; wywołujący zawsze czyta Current.
- `Refresh(selected0b)` odpowiada okresowej normalnej Life kursora.
- `InvalidateMap()` przenosi wyzerowanie b9/e6 bez usuwania ostatniego
  targetu/pozycji. Porównano rzeczywiste dwa zapisy 518f2d…518f39.
- `ApplyReleaseCursor(type,mask,bit,blocked)` przyjmuje jawne wyniki osobnego
  helpera release. Nie wykonuje pickera, wyboru ani rozkazu.
- Current udostępnia cached screen/world/cell, HasMapPosition, HoveredOwner,
  CursorType, ActionMask, ActionBit, Blocked, Selector i LastQueryPerformed.

Source0bSelected zakłada faktycznie jednego lokalnego 0b w źródłowej grupie.
Wykonano oryginalne callbacki zarówno bieżącej grupy, jak listy pending.
Nie jest to dowód wyboru/utworzenia tej grupy ani jej późniejszej symulacji;
te procedury mają osobny adapter. Helper nie zmienia siatki, pozy ani RNG.

## Wykonany dowód

[Oracle](../tools/probe_ship_pointer_hover.py),
[walidator](../tools/validate_ship_pointer_hover.py),
[probe C#](../tests/fixtures/ShipPointerHoverProbe.cs),
[testy](../tests/test_ship_pointer_hover.py),
[raport](../artifacts/world-input/hover-csharp-validation.json),
[log testów](../artifacts/world-input/hover-targeted-tests.log).

Trwała [fixture](../tests/fixtures/ship_pointer_hover.json) ma SHA256
`8b6378752fed97d06f5890e6ed4de07646f96b0c14860971ad2ffa7d010ba547`.
Fresh original musi być w całości równy przypiętemu JSON przed porównaniem
rzeczywistego C#, kompilowanego `checked+` i `warnaserror+`.

2339 operacji obejmuje 2327 obserwowanych stanów i 12 jawnych zmian danych
sceny/capabilities. Matrix przechodzi wszystkie 576 komórek bez wyboru oraz
571 komórek z wyborem; 5 trafionych obcych statków wykluczono z wybranego
kontekstu walki. Każdy punkt ma Move i Life. Dodatkowo wykonano zmiany
cap400/cap4, rezerwację bez trafienia maski, ruch obiektu pod nieruchomym
wskaźnikiem, zmianę STORED maski obrotu, cache screen/world, invalidation,
przeniesienie stanu release i zachowanie cyklu 101.

Wykonywane są całe oryginalne 518d90, 51cd60, 517a60, 517540,
Dump 499560/49a580, Fleet 49ab30/49e620/49e490 oraz Ship 4dc630 z predykatami
4e6700, 50e800, 499a40/4999e0. Picker i prawdziwe type18 maski wykonują
4e06c0, 5431d0, 5575d0. SetGCType 516e30 oraz DrawSprite 516640 nadal wykonują
oryginalne przypisania; 55ea00 i cached clock 5417d0 wykonują się bez hooków.

Jawne granice są cztery: normalny powrót setjmp 587318; lookup systemu 540540
przekierowuje system 69 do rzeczywistego Mapa 51cd60, pozostałe panele UI są
nieobecne; 516d90 zastępuje wyłącznie ładowanie zasobu kursora; 55eb50 zastępuje
publikację grafiki. Nie przechwytuje się decyzji hover ani odpowiedzi aktora.
Nie ma hooka jądra lub zegara. Viewport 24×24 i normalne tryby są
kontrolowanym wejściem, nie domyślną kamerą nowej misji.

Zachowano wcześniejsze nieudane logi. `hover-first.log` ujawnił zły cleanup
stosu w harnessie clock 5417d0; usunięto zbędny hook i uruchomiono prawdziwy
odczyt cached time. `hover-native-first-full.log` zachowuje potrzebę jawnego
stopu izolowanego zakresu invalidation po jego drugiej instrukcji w już
skompilowanym bloku Unicorn. `hover-validation-launch.log` zachowuje różnicę
Python tuple/list przy porównaniu JSON; po normalizacji zapisu JSON wszystkie
wartości pozostały zgodne. Nie zmieniano oryginału ani nie luzowano wyników.

Nowa logika jest zamrożona po porównaniu C#. Osobne testy playera, InputSystem,
wyboru, kursora i pełnego runtime muszą wskazywać własny DLL i raporty.
Nie uruchamiano tutaj Unity, Wine, Xvfb, nie tworzono podglądu lub ZIP,
nie publikowano i nie modyfikowano dawnych helperów.
