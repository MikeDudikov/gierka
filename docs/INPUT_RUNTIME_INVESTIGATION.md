# Granica wejścia myszy w playerze Windows pod Wine

Stan: 2026-11-02. Docelowe wymaganie użytkownika to obecnie **1920×1080,
16:9, pełny ekran**. Poniższa diagnostyka dotyczy zachowanej, wcześniejszej
kopii playera **1280×1024** i służy ustaleniu granicy dostarczania wejścia.
Nie zmienia bieżącego celu rozdzielczości ani nie stanowi testu Windows 11.

## Wynik

Nie potwierdzono przejścia wejścia systemowego do interaktywnego menu Unity
w tej konfiguracji Wine 11/Xvfb. Natywne WinAPI potwierdzają właściwe okno
pierwszoplanowe, pozycję oraz naciśnięcie myszy. Osobny natywny odbiornik
otrzymuje prawidłowe dane przez **obie** ścieżki RAWINPUT. W badanym playerze
Unity zdarzenia `STAT` nadal zawierają pozycję początkową i zwolniony przycisk.

Przyczyna wewnątrz granicy pomiędzy natywną obsługą wejścia Windows w Unity
a tą konfiguracją warstwy zgodności pozostaje nierozstrzygnięta. Nie
przypisujemy błędu samej implementacji `GetRawInputBuffer`, Wine jako całości
ani regule `MainMenuButton` bez dalszego dowodu.

## Stanowisko i identyfikacja próby

- Wine **11.0.0.0~trixie-1**, natywny loader x64, `WINEARCH=wow64`.
- Własna kopia prefixu: `artifacts/unity-reference/input-probe/prefix`.
  Własny Xvfb **:80**, 1280×1024×24; nie używano sesji głównej :79.
- Kopia playera: `artifacts/unity-reference/input-probe/player-snapshot`.
  EXE SHA-256:
  `d91dbfa5c7d67cdf2c521d83112df029079f358519a1282d531baad4e1cd80c9`.
  Rzeczywisty `Assembly-CSharp.dll` SHA-256:
  `9093fe15c321b95dd042cc8a1b48dac62d5b4cf864e15be013b942758f220c17`.
  Sam hash launchera EXE nie identyfikuje zmienianego kodu zarządzanego.
- Uruchomienie z `--menu-input-diagnostics`. Log ogranicza diagnostykę do
  pierwszych zdarzeń, nie wypisuje klawiatury użytkownika ani środowiska.
- Win64 helpery są prawdziwymi PE32+, wywołują `user32`/`kernel32` i nie
  patchują gry, Unity ani Wine. Źródła: `tools/win64_menu_input_probe.c`
  i `tools/win64_raw_input_probe.c`.

## Kontrole i obserwacje

| Próba | Potwierdzone | Ograniczenie / wynik |
| --- | --- | --- |
| XTest/xdotool w głównych próbach | X11 raportuje zmienianą pozycję | Unity nadal środek/leftFalse; samo XTest nie wystarcza jako dowód wejścia playera |
| Odroczenie wejścia o 5 s | Ten sam brak reakcji | Osłabia hipotezę zbyt wczesnego testu splash; nie rozstrzyga całego procesu inicjalizacji |
| `FindWindowA`/`SetForegroundWindow`/`GetForegroundWindow` | Właściwy PID, `AncientConquest`, rect 0,0,1280,1024; SetForegroundWindow=1 | Poprawny foreground nie dowodzi przetworzenia RAWINPUT przez Unity |
| `SetCursorPos` i `SendInput` bez WM | GetCursorPos zmienia się np. do 251,430; SendInput=1/error0 | Unity dalej raportuje 640,511/leftFalse |
| `GetAsyncKeyState(VK_LBUTTON)` | Po SendInput down stan1, po up stan0 | Nie jest to jeszcze event Input System |
| Ślad `+rawinput` playera | Unity rejestruje mouse/keyboard do własnego HWND i wywołuje GetRawInputData/GetRawInputBuffer | Ślad nie ujawnia kompletnego sposobu przetworzenia danych przez natywny backend Unity |
| Natywny odbiornik `GetRawInputData` | Prawidłowe RAWINPUT ruch/down/up oraz legacy WM_MOUSEMOVE/WM_LBUTTONDOWN/UP | Kontrolne okno WinAPI, nie Unity |
| Natywny odbiornik `GetRawInputBuffer` | Te same rekordy i poprawne wyrównanie | Nie dowodzi zgodności wszystkich przypadków API lub kodu Unity |
| Jeden test z `twm` | WM działał, foreground nadal poprawny | Nie przywrócił wejścia Unity; po operacjach pozycja WinAPI wracała do środka; mechanizmu tego powrotu nie ustalono |

W próbach z natywnym helperem kliknięcie Quit nie zakończyło playera.
`player_exit: null` w statusie oznacza brak zakończenia po kliknięciu w oknie
czasu próby, a nie brak posprzątania: później własny player zamknięto przez
`taskkill` wysyłający WM_CLOSE, zakończono własny wineserver i Xvfb. Nie
uznano takiego zakończenia za dowód poprawnej obsługi Quit.

## Porównanie obu API RAWINPUT

Natywny helper rejestruje mysz, kolejkuje przez SendInput ruch/down/up i
odbiera je w dwóch osobnych uruchomieniach. Wynik obu procesów: exit0.
`sizeof(RAWINPUTHEADER)=24`, długość rekordu 48, adres modulo8 wynosi 0.
Pierwsze trzy rekordy są identyczne:

| Zdarzenie | dwType | hDevice | usFlags | usButtonFlags | lLastX | lLastY |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ruch | 0 | 1 | 0 | 0 | 200 | 200 |
| down | 0 | 1 | 0 | 1 | 0 | 0 |
| up | 0 | 1 | 0 | 2 | 0 | 0 |

`GetRawInputData` zwraca 48 bajtów na rekord. `GetRawInputBuffer` zwraca 3
rekordy w jednym odczycie; następne bloki są wyrównane do 8 bajtów. W obu
próbach dochodzi także dodatkowy zerowy rekord ruchu/fokusu. Hipoteza,
że SendInput daje tutaj `hDevice=NULL`, została **obalona**.

To konkretna kontrola układu danych x64 i tych zdarzeń. Nie jest testem
WOW64 x86, wszystkich flag RAWINPUT ani zgodności z fizycznym urządzeniem.

## Artefakty i narzędzia

Wszystkie poniższe ścieżki są pod `artifacts/unity-reference/input-probe/`:

- `native-api-trial/calls.json`, `player.log`, `status.json`: foreground,
  GetCursorPos, GetAsyncKeyState, SendInput i wynik playera bez WM.
- `rawinput-trial/launch.log`: ograniczony ślad rejestracji i odczytów
  RAWINPUT w tym playerze; zachowano także oddzielny log Unity.
- `raw-receiver-trial/stdout.txt`: pierwszy odbiornik WM_INPUT.
- `raw-buffer-comparison/data.stdout.txt`, `buffer.stdout.txt`, `status.json`:
  bezpośrednie porównanie obu API; osobne ślady Wine w tym katalogu.
- `twm-trial/`: pojedyncza próba z WM, wywołania WinAPI i log playera.
  Ostrzeżenia twm o nieobecnych zestawach znaków fontów nie zostały ukryte.
- `binary-hashes.json`: identyfikacja użytych binariów.

`tools/setup_mingw_probe.py` sprawdza podpis oficjalnego Debian InRelease
systemowym kluczem archiwum, hash niekompresowanego indeksu oraz rozmiary/SHA-256
sześciu pakietów. Wyłącznie rozpakowuje je do `/workspace/toolchains/mingw-probe`.
Lista z wersjami jest w `verified-packages.json` tego katalogu. Kompilacja
przez `tools/build_win64_menu_input_probe.sh <świeży-katalog>` używa prawdziwego
cross-kompilatora, nie konwersji relokacji ELF→COFF. Niewykonany kandydat z
wczesnej próby takiej konwersji został odrzucony i oznaczony `.rejected`.

Mały twm 1.0.10 pochodzi z oficjalnego, podpisanego indeksu Debian, hash pakietu
`0fee84bfee0c434e9e76c49abb69d2d5d9b0caa079f409cefcdefe04c0343eee`.
Rozpakowano go lokalnie do `/workspace/toolchains/input-wm`; systemowego WM
ani konfiguracji użytkownika nie zmieniono.

## Znaczenie dla walidacji remake’u

Test `ValidateMenuInput` z prawdziwą kolejką Input System bada scalanie
MouseState i regułę domeny, ale zaczyna **po** natywnym wejściu OS. Jego
prostokąt 112,398,278,64 jest geometrią izolowanego przypadku testowego,
a nie docelowym układem 1920×1080. Osobny jawny replay MouseState w playerze,
jeśli wykonany, również nie zastępuje testu fizycznej myszy/OS.

Nie przełączono produktu na stare `UnityEngine.Input`, nie dodano ukrytego
wejścia zastępczego i nie uznano braku wyjątku za działające sterowanie.
Pozostają do wykonania testy rzeczywistej ścieżki myszy w docelowym buildzie
1920×1080 na natywnym Windows 11 oraz wyjaśnienie opisanej granicy zgodności
w bieżącym hoście, jeśli ma służyć dalszym testom interaktywnym.
