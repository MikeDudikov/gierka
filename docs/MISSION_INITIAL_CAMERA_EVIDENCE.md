# Pierwsza kamera miss000 — inicjalizacja i granice dowodu

Stan: 2026-11-02. Zbadano dane i wybrane instrukcje dostarczonego oryginału,
bez uruchomienia gry jako procesu systemowego. Docelowy remake pozostaje
**1920×1080, 16:9, pełny ekran**. Poniższe wartości opisują źródłowy układ;
nie narzucają skali ani FOV współczesnego widoku diagnostycznego.

Źródłowy `ancient.exe` SHA-256:
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Adresy są VA przy bazie `0x400000`. Zachowano źródła bez modyfikacji.

## Wniosek dla zwykłego Start scenario → miss000

Przed rozpoczęciem świata kod wybiera parę grupy/slotu **(1,1)**.
Tablica `WIN_VIEW` ma **20** dwordów (80 bajtów); **12 jest typem zasobu,
nie liczbą presetów**. Indeks tej pary to `1*4+1=5`. W miss000 pozycja5
zawiera pakowany origin **(15,0)**. Przy źródłowym widoku9×8 i mapie24×24
oryginalny clamp pozostawia **(15,0)**.

Jest to potwierdzony stan wynikający z badanej inicjalizacji i wysłania
`0xcba`, a nie nagrany pierwszy framebuffer działającego oryginału.
Nie odtworzono tu całej kolejki wejścia, pętli renderowania ani symulacji.
Nie należy zastępować tym originem kadru960×540/skala2× bieżącej diagnostyki:
jej15×9komórek dałoby inną granicęX, a więc inny widok.

## Sekwencja źródłowa

1. Handler menu `0x531030`, polecenie Start scenario, wywołuje
   `0x537ef0(app,0,0)`: indeks kampanii0 i indeks misji0 wybierają miss000.
   Powiązanie zostało wcześniej opisane w SCENARIO_MENU_EVIDENCE.md.
2. `0x537ef0` otwiera miss000 i wywołuje `TuneGamePtr0x4ed700` z flagą0.
   Ten loader wczytuje m.in. DESCRIPTOR (`0x4ecf70`), mapę (`0x4ecef0`),
   opcjonalny PLAYERS_DESC (`0x4ed130`) oraz WIN_VIEW (`0x4ed530`).
3. `0x4ed530` najpierw zeruje wszystkie20dwordów od `app+0x2ef5`.
   Jeżeli typ12 WIN_VIEW istnieje, kopiuje z niego dokładnie80bajtów.
   Zerowanie, kopiowanie i przypadek braku zasobu wykonano przez x86.
4. Po powrocie z TuneGamePtr **`0x537ef0` ponownie zeruje PLAYERS_DESC**
   (`app+0x1a1d`,20bajtów), po czym przechodzi po rekordach DESCRIPTOR.
   Licznik tej ścieżki jest pod+16, pierwsza pozycja rekordu pod+20,
   krok wynosi104bajty. Para grupy/slotu leży pod+28/+32 dla pierwszego
   rekordu; status jest słowem pod+20. To rozpoznanie pól potrzebnych tej
   ścieżce, nie pełna specyfikacja DESCRIPTOR.
5. Dla indeksu kampanii0 para(1,1) otrzymuje status2 oraz PLAYERS_DESC=1;
   pozostałe rekordy otrzymują status3 i PLAYERS_DESC=3. Oryginał zapisuje
   wybraną parę w `app+0x3212/+0x3213`. W prawdziwym miss000 są dwa
   badane rekordy: pary(1,1) i(4,0). Końcowa tablica ma wyłącznie
   `PLAYERS_DESC[5]=1` i `PLAYERS_DESC[16]=3`.
6. W źródłowym miss000 nie ma osobnego rekordu PLAYERS_DESC. Jego brak
   sam w sobie nie oznacza wyzerowania: `0x4ed130` z flagą0 może przeglądać
   wcześniejszą zawartość aplikacji. W tej ścieżce wynik ustala późniejsze
   jawne wyzerowanie i przepisanie w `0x537ef0`, opisane wyżej.
7. Briefing zmienia trudność przez globalny `DAT_005ca78d`, ale jego obsługa
   nie przepisuje powyższej pary ani WIN_VIEW. `StartGame0x4ebf50` kopiuje
   trudność do `app+0x32a1` i **zeruje `app+0x328d`**. Nie jest to wybór
   innego slotu dla Easy/Normal/Hard.
8. Konstruktor `GameSystem0x50ee70` ustawia origin0,0 i widok9×8.
   `StartGame` aktywuje ten system, potem wysyła do niego wiadomość0x101.
   Handler `0x50f8a0` w gałęzi0x101 ponownie zeruje origin.
9. Tworzenie obiektów `FieldSystem0x503660` tworzy obiekt typu0x2f4
   z parametrem inicjalizacji1. Factory-table para pod0x5c0de8 wiąże
   typ0x2f4 z konstruktorem0x519560; ten tworzy Mapa z vtable0x59b824.
   Jej handler `0x51cd60`, wiadomość2, zapisuje parametr1 do `Mapa+0x58`.
   Wiadomość8 prowadzi przez `InitMapa0x51be90` do `InitMapaBig0x51bcb0`.
   Zatem zwykła ścieżka korzysta z dużej mapy w trybie1, nie z minimapy.
10. `InitMapaBig` kopiuje9×8 i bieżący origin z GameSystem, ustawia
    kafel64, offsetY8 oraz brak dodatkowego sub-offsetu. OffsetX pochodzi
    z `GetPos0x511100`; przy `app+0x328d=0` i argumencie8 wynosi8 albo216
    zależnie od globalnej flagi `DAT_005ca54a`. Nie zrównano tej flagi
    z nieweryfikowanym współczesnym układem HUD.
11. Jeszcze wewnątrz gałęzi GameSystem0x101, po utworzeniu systemów,
    kod sprawdza `app+0x3212 != 0xff`, wybiera
    `WIN_VIEW[4*group+slot]` i wysyła obiektowi0x2f4 wiadomość0xcba.
    Dla miss000 jest to indeks5 i argument15. Handler Mapa rozpakowuje
    dolne/górne unsigned16 jakoX/Y; w trybie1 wywołuje DrawMapaXY0x519ef0.
12. Oryginalny clamp dla mapy24×24 i widoku9×8 pozostawia15,0;
    wynik jest zapisywany zarówno w Mapa, jak i GameSystem. Późniejsza
    wiadomość0x4e8 w tej samej inicjalizacji zapisuje globalną flagę,
    nie przestawia origin. Źródłowy prostokąt tego widoku ma576×512pikseli.

## Poszerzenie widoku jest oddzielnym przełączeniem

Handler `GameSystem0x50f8a0`, wiadomość0x4e1, przełącza `app+0x328d`,
zmienia układ kontrolek i wysyła Mapa0xcc3. W trybie1 handler Mapa ustawia
szerokość `9+(app+0x328d!=0 ? 3 : 0)` i ogranicza dotychczasowy origin.
Przełączenie9→12komórek przy źródłowym X15 dajeX12; wysokość pozostaje8.
StartGame wcześniej zeruje tę flagę, więc12×8 nie jest domyślnym FOV
badanej ścieżki Start scenario. Nie dodano arbitralnego zoomu ani przewijania.

## Wykonany wąski oracle x86

Skrypt i raport są w `artifacts/objects/camera/`:

- `validate_camera_setup.py`, `camera-setup-validation.json`.
- Prawdziwy DESCRIPTOR SHA256
  `458dac3b5942c5dff55d0640cb354a3761be9c824074cb99c29a939856a03ded`.
- WIN_VIEW SHA256
  `b8a17a6b40efc364c44dc2a1470a1ace8188de20e6cf057edd6865eff04800f8`.
- Blok wyboru `0x5380d7..0x538194` wykonano dla indeksów kampanii0…3,
  na tym samym prawdziwym miss000 DESCRIPTOR, **bez hooków**. Wynik dla0
  to para1,1 oraz opisane wyżej dwa niezerowe sloty. Pozostałe indeksy są
  kontrolami tego bloku na danych miss000, nie dowodem innych kampanii.
- Całą funkcję WIN_VIEW `0x4ed530` wykonano dla obecnego i nieobecnego
  zasobu. Jedyny hook zastępuje getter `mfAObjLoad0x549740` zweryfikowanym
  payloadem lub NULL. Nie przechwycono zerowania ani kopiowania.
- Clamp `0x519f3d..0x519f91` wykonano dla origin15,0 oraz widoków9×8
  i12×8, **bez hooków**. Wyniki15,0 i12,0 zapisują się zgodnie w obu
  właścicielach. Zakres zaczyna się po prelude/setjmp i kończy przed redraw;
  szerszy zestaw1080porównań opisuje TERRAIN_CAMERA_EVIDENCE.md.
- Źródłowe EXE i oba pliki miss000 są chronione pełnymi hashami w skrypcie.

Eksporty Ghidra: istniejące `artifacts/binary-analysis/scenario-menu/export/`,
`first-map/export/` oraz nowe `artifacts/objects/camera/export/`.
Ghidra pracowała readOnly na osobnej kopii projektu po stwierdzeniu blokady
wspólnego projektu. Nie usuwano cudzych locków. Pierwszy nowy eksport mapy
z błędnym adresem środka funkcji zachowano jako nieudany; wniosek o trybie
pochodzi z poprawnego handlera0x51cd60 i istniejącego InitMapa0x51be90.

Nie wykonano kompletnego StartGame w emulatorze, pełnej rejestracji systemów,
renderera lub pętli gry. Nie istnieje jeszcze zrzut pierwszej klatki oryginału
na natywnym Windows. Powyższy dowód zamyka konkretne luki wyboru slotu,
ładowania WIN_VIEW i ograniczenia origin, nie cały problem kamery i rozgrywki.

## Wydzielony parser Unity C#

`Runtime/MissionInitialSetup.cs` (`AncientConquest.World`) odtwarza wybór
slotu i odczyt zapisanego origin jako niemutowalny wynik. Konstruktor przyjmuje
surowy DESCRIPTOR,80bajtów zapisanych widoków i indeks kampanii0…3. Udostępnia
SelectedSide/SelectedPlayer, SavedOriginX/Y, źródłowy rozmiar9×8 oraz kopię
20bajtów PLAYERS_DESC. Nie tworzy obiektów i nie zmienia kamery Unity.

Nie mutuje DESCRIPTOR, choć oryginalny blok zapisuje statusy2/3 w rekordach;
wynik publiczny zachowuje tablicę i wybór. Długości, licznik, zakresy grup0…4
oraz slotów0…3 są sprawdzane przed odwołaniem. Odrzucenie uszkodzonych danych
jest kontraktem parsera, nie twierdzeniem o zachowaniu oryginału przy korupcji.
Przypadek braku wybranej pary jest jawnie odrzucany: oryginał pozostawia wtedy
wcześniejszy bajt aplikacji, którego ten konstruktor nie otrzymuje. Dotyczy
to m.in. użycia DESCRIPTOR miss000 z indeksami kampanii1…3. Nie wprowadzono
zastępczego gracza ani zgadywanego origin.

Walidator `tools/validate_mission_initial_setup.py` wykonuje **177porównań**
rzeczywistego pliku C# skompilowanego z `/checked+` z oryginalnymi blokami:
wybór `0x5380d7..0x538194` oraz przygotowanie argumentu WIN_VIEW/0xcba
`0x5100d8..0x510122`. **Oba bez hooków**; drugi zakres kończy się przed
wysłaniem wiadomości. Jeden przypadek używa prawdziwego miss000, pozostałe176
sprawdzają regułę na syntetycznych rekordach:4kampanie,20slotów, oba porządki,
duplikaty, pełne tablice i współrzędne unsigned16. Nie są to dowody treści
pozostałych kampanii. Stała9×8 ma osobny dowód konstruktora, a nie pochodzi
z tych dwóch zakresów.

Dodatkowo probe wykonał **25kontroli kontraktu C#**: braki/truncation,
nieprawidłowe sloty/indeksy, overflowlicznika, brak wyboru, niemutowanie wejść,
niezależność wyniku od ich dalszego życia, izolację kopiowanej tablicy oraz
origin65535. Trzy unittesty przeszły bez pominięć; dwa dodatkowe testy chronią
hash oryginalnego EXE oraz obu plików misji przed odmiennymi wejściami.

Raport: `artifacts/objects/camera/mission-initial-setup-validation.json`;
wynik testów: `mission-initial-setup-tests.txt`. Nie oznacza to potwierdzonego
importu Unity, playera ani zintegrowanego StartGame; te kontrole należą do
osobnego etapu integracji.
