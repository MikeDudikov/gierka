# Próba uruchomienia oryginału — 2026-11-02

Status referencyjnego oryginału: **Blocked**. Nie uzyskano menu ani pomiaru
rozgrywki. Wine 10/QEMU kończył się konfliktem obrazu PE (`c0000018`).
Po odblokowaniu sieci zainstalowano oficjalny Wine 11.0 i sprawdzono nowy
WOW64: część natywna 64-bitowa działa, lecz zarówno kontrolny program PE32,
jak i oryginał kończą się SIGSEGV (kod 139). Nie jest to wynik obserwacji
mechanik ani stwierdzony błąd logiki Ancient Conquest.

## Sprawdzone środowisko

Badanie wykonano w nowej maszynie po publikacji środowiska, po sprawdzeniu
pliku kontrolnego głównego agenta i identyfikatora uruchomienia
`02fd04eb-5227-4429-806a-a173a569004f`. Wyników wcześniejszych sesji
pomocniczych na innej maszynie nie uznano za dowód tej instalacji.

Do `/workspace/toolchains/wine-root` pobrano i rozpakowano lokalnie pakiety
Wine `10.0~repack-6` dla amd64/i386, Xvfb, xdotool oraz oficjalny `qemu-user`.
APT sprawdził podpisane indeksy Debiana trixie, trixie-security i
trixie-updates oraz integralność pobieranych pakietów. Nie instalowano ich do
systemu, nie zmieniano polityki sieci, nie wyłączano TLS ani podpisów.
Konfiguracja lokalnego APT i logi: `/workspace/toolchains/wine-apt/`.

Oryginalne pliki pozostają w `reference/raw/ancient-conquest/`. Kopia robocza
w `artifacts/runtime-original/game/` łączy pliki instalatora z `DATA`, `SOUND`,
`VIDEO` oraz `ID_CD.DSK` z płyty. Wszystkie pliki pochodzące z tych źródeł
ponownie porównano przez SHA-256 po próbach uruchomienia. Nie patchowano EXE,
danych gry ani mechanizmu sprawdzania nośnika. Profile Wine są odizolowane
w `artifacts/runtime-original/prefix*`.

## Wyniki kontroli

| Próba | Wynik |
| --- | --- |
| Lokalny Xvfb, ekran `:78`, 1280×1024×24 | Proces działał; nie dowodzi renderowania gry |
| Natywny Wine64 `wineboot` | Kod wyjścia 0 po naprawieniu lokalnych ścieżek DLL |
| Wine64 `system32/cmd.exe /c ver` | Kod 0, `Microsoft Windows 10.0.19043` |
| Natywny Wine32 `--version` | Kod 126, kernel odrzuca ELF i386 (`Exec format error`) |
| Lokalny interpreter ELF32 wywołany bezpośrednio poza sandboxem | Kod 126, `Exec format error`; problem nie wynika wyłącznie z braku `/lib/ld-linux.so.2` |
| Wine32 przez QEMU `--version` | Kod 0, rozpoznany Wine 10.0 |
| Wine32 przez QEMU, pierwsze uruchomienie profilu | Niepowodzenie uruchomienia potomnego loadera i386 |
| Wine32 przez QEMU po poprawce lokalnego loadera, `cmd.exe /c ver` | Kod 0, `Microsoft Windows 10.0.19043`; część usług tła generuje ostrzeżenia sygnału 11 QEMU |
| Eksperymentalny WOW64 Wine64, kontrolny `syswow64/cmd.exe` | Kod 1 przed uruchomieniem; załadowano NTDLL32, następnie błąd ShellExecuteEx/FormatMessage |
| Oryginalny `ancient.exe` | Brak uruchomienia głównego modułu: `c0000018`; menu nie osiągnięto |

Dla lokalnie relokowanego Wine rozpoznano i poprawiono ścieżki do plików NLS
oraz `zlib1.dll`. Kontrola `strace` potwierdziła również konieczność udostępnienia
32-bitowych PE DLL w katalogu przeszukiwanym przez natywny Wine64.
Lokalny wrapper QEMU w miejscu opcjonalnego `wine-preloader` umożliwił
procesom potomnym uruchomienie loadera i386 i kontrolnego `cmd.exe`.
To pozwoliło przejść wcześniejsze błędy brakujących plików i wykonać kontrolę
32-bitową, lecz obraz PE gry nadal koliduje z przestrzenią adresową loadera.
Próby nie zapewniają uruchomienia gry. Zapisano diagnostyczny helper
`tools/probe_original_runtime.sh`: tryby `--control32` i `--control64` wykonują
zweryfikowane `cmd.exe /c ver`, a `--game32` zachowuje rzeczywisty błąd loadera.
Nie zmieniano obrazu PE ani jego adresu bazowego.

Zweryfikowane parametry PE oryginału: `ImageBase=0x400000`,
`SizeOfImage=0x1de000`, charakterystyka `0x10f`, katalog relokacji `0/0`.
Obraz jest nierelokowalny. Dwie kontrolowane próby z obsługiwanymi opcjami
QEMU nie rozwiązały konfliktu: `QEMU_GUEST_BASE=0x100000000` z
`QEMU_RESERVED_VA=0` oraz z `QEMU_RESERVED_VA=0x100000000`; obie stosowały
`WINEPRELOADRESERVE=00400000-00600000`. Obie zakończyły się kodem 24 i
`c0000018`, bez osiągnięcia menu. Nie próbowano patchować ani relokować gry.

Helper wymaga przygotowanej lokalnej instalacji, profili opisanych powyżej
i działającego Xvfb na `:78`. Przykład diagnostyczny (nie gotowy start gry):

```sh
LD_LIBRARY_PATH=/workspace/toolchains/wine-root/usr/lib/x86_64-linux-gnu \
  /workspace/toolchains/wine-root/usr/bin/Xvfb :78 \
  -screen 0 1280x1024x24 -nolisten tcp -ac
# W osobnym terminalu:
bash tools/probe_original_runtime.sh --control32
bash tools/probe_original_runtime.sh --control64
bash tools/probe_original_runtime.sh --game32
```

Helper ma limit 30 s i zachowuje kod procesu potomnego. Kontrole zwracają 0;
tryb gry pozostaje nieudany. Po badaniu Wine 10 zakończono własne procesy referencyjne;
nie należy zakładać, że Xvfb albo Wine nadal działa w nowej sesji.

## Dowody i następny krok

Podsumowanie maszynowe: `artifacts/runtime-original/runtime-status-current.json`.
Logi kontroli i ścieżek loadera są w tym samym katalogu, m.in.
`control-win64-cmd.log`, `control-wow64-cmd.log`, `control-qemu32-cmd.log`,
`wine32-execve.log`, `wine32-loadpaths.log`, `ancient-wow64-module.log`
oraz `ancient-qemu32-recursive.log`.

Do zebrania referencyjnej rozgrywki potrzebna jest działająca obsługa natywnych
procesów i386, kompletna wspierana dystrybucja nowego WOW64 albo stanowisko
Windows. Nie należy przypisywać tego błędu regułom gry ani uważać statycznie
zrekonstruowanego ekranu menu za zrzut działającego oryginału. Testy sterowania,
AI, zegara, zapisu i odczytu pozostają niewykonane.

## Potwierdzony następny wariant: Wine 11.0, nowy WOW64

Oficjalne ogłoszenie stabilnego Wine **11.0**, odczytane z tagu `wine-11.0`
w [lustrze źródeł Wine](https://github.com/wine-mirror/wine/blob/wine-11.0/ANNOUNCE.md),
potwierdza ukończenie nowej architektury WOW64. Nowy tryb jest w pełni wspierany
i ma niemal pełną zgodność funkcji ze starym. W istniejącej instalacji można
wymusić go przez `WINEARCH=wow64`, pod warunkiem użycia profilu utworzonego jako
64-bitowy. Czyste profile `WINEARCH=win32` są przestarzałe i nie są obsługiwane
w nowym trybie. To konkretna różnica względem przebadanego pakietu Wine 10,
który odrzucał taką wartość `WINEARCH`.

Oficjalna konfiguracja repozytorium WineHQ dla Debiana 13 jest pod adresem
`https://dl.winehq.org/wine-builds/debian/dists/trixie/winehq-trixie.sources`.
Pierwszy odczyt zwrócił proxy HTTP **403**. Użytkownik następnie zmienił politykę
sieciową na nieograniczoną; jej stan `enforced/connected` sprawdzono przed
ponowieniem. Konfiguracji nie zmieniał agent. Obecnie odczyt działa i zweryfikowano
podpisane indeksy WineHQ. Dokładna wersja pakietów: **`11.0.0.0~trixie-1`**.

Dowody: `artifacts/runtime-original/wine11-prerequisite/`, w tym zachowane
ogłoszenie 11.0, odpowiedź HTTP oraz `status.json`. Potwierdzenie możliwości
upstream nie dowodzi jeszcze uruchomienia tej gry w nowym trybie.

## Rzeczywista instalacja i próby Wine 11.0

Odczytano również oficjalną [instrukcję WineHQ dla Debiana/Ubuntu](https://gitlab.winehq.org/wine/wine/-/wikis/Debian-Ubuntu).
Wskazuje ona użyty adres klucza `https://dl.winehq.org/wine-builds/winehq.key`.
Klucz publiczny ma przypięty fingerprint
`D43F640145369C51D786DDEA76F1A20FF987672F`; APT poprawnie zweryfikował nim
indeksy i integralność pakietów. Dokumentacja określa adres klucza; fingerprint
zapisano z faktycznie pobranego klucza i kontroluje go zapisany instalator.

Pakiety WineHQ stable dla trixie nadal są rozdzielone na amd64/i386. Część i386
zawiera PE DLL potrzebne do uruchamiania programów 32-bitowych. Nowy tryb 11.0
wymuszono przez `WINEARCH=wow64`; podczas tych prób **nie używano QEMU ani ELF32**.
Pakiety rozpakowano do `/workspace/toolchains/wine11-root`, a świeży profil
utworzono w `artifacts/runtime-original/prefix-wine11`.

Zapisano i wykonano ponownie [setup_wine_wow64.sh](../tools/setup_wine_wow64.sh):
instalacja zakończyła się kodem 0, z ponowną kontrolą podpisów, fingerprintu i
wynikiem `wine-11.0`. Jest to lokalna instalacja, bez systemowego APT i publikacji.
Opcjonalny instalator Wine Mono pominięto: oryginał jest programem C++, a nie .NET.

| Próba Wine 11.0 | Wynik |
| --- | --- |
| Świeży `wineboot`, profil 64-bitowy, `WINEARCH=wow64` | Kod 0 |
| Kontrola PE64 `system32/cmd.exe /c ver` | Kod 0, `Microsoft Windows 10.0.19045` |
| Kontrola PE32 `syswow64/cmd.exe /c ver` po udostępnieniu oficjalnych DLL | SIGSEGV, kod 139 |
| Oryginalny `ancient.exe` | SIGSEGV, kod 139, bez menu |
| Kontrola launchera `run_wine11_reference.sh` z programem PE64 | Kod 0 |

Ślad kontrolnego PE32 rejestruje `SIGSEGV` z `si_code=SI_KERNEL` i `si_addr=NULL`.
Dalszy kontrolowany odczyt rejestrów przez `ptrace` ustalił dokładną instrukcję:
`RIP=0x7f2780246d4a`, `CS=0x33`, `SS=0x2b`; jest to offset plikowy `0x3ed4a`
w `x86_64-unix/ntdll.so`. Statyczna deasemblacja pokazuje `mov eax,0xf3`, po
którym wykonuje się **`int 0x80`**. Oficjalny kod źródłowy Wine 11.0,
`dlls/ntdll/unix/signal_x86_64.c`, wiersze 104–127, identyfikuje tę sekwencję
jako `alloc_fs_sel`: wywołanie 32-bitowego `SYS_set_thread_area`.

Zatem niepowodzenie występuje w wymaganej ścieżce zgodności wywołań IA32 podczas
inicjalizacji Wine, przed wykonaniem gry. Bieżący wykonawca dostarcza sygnał
przy instrukcji przerwania; nie zaobserwowano zwrotu `EPERM` ani `ENOSYS`.
Dokładnej konfiguracji kompilacji kernela nie badano. W połączeniu z odrzuceniem
natywnego interpretera ELF32 jest to konkretna bramka środowiskowa: potrzebny
jest zgodny wykonawca IA32 albo stanowisko Windows do pomiarów oryginału.
Nie odczytywano pamięci procesu ani środowiska; zachowano tylko adresy rejestrów,
nazwę mapowanego modułu i porównanie z niezmienionym plikiem narzędzia.
Dowody: `fault-registers.json`, `fault-static-disassembly.txt`,
`upstream-signal_x86_64.c` i `fault-provenance.json` w katalogu raportów Wine 11.
Kompilacji Wine nie rozpoczynano i nie przypisuje się tego błędu logice gry.

[run_wine11_reference.sh](../tools/run_wine11_reference.sh) jest sprawdzonym
launcherem natywnym dla **64-bitowych** programów Windows, przydatnym do
testów zgodności playera Unity pod Wine. Taki test nie jest uruchomieniem na
Windows 11 ani na docelowym laptopie. Xvfb `:79`, 1280×1024×24, pozostawiono
na czas dalszego testu playera; procesu nie wolno zakładać po odtworzeniu sesji.

Końcowe dowody Wine 11: `artifacts/runtime-original/wine11/`, plik
`status.json`, logi kontroli, `control32-systemcalls.log`,
`setup-repeatability.log` i `launcher-control64.log`. Publiczne źródła,
indeksy, konfiguracja lokalnego APT i manifest hashy pakietów są w
`/workspace/toolchains/winehq-apt/`.

## Nowa próba pełnej VM — 2026-11-02

[ORIGINAL_VM_PROBE.md](ORIGINAL_VM_PROBE.md) opisuje oddzielny QEMU TCG z własnym
kernelem Debiana. Test ELF32/int0x80 przeszedł z kodem0, więc hostowa bramkaIA32
nie dotyczy już tej ścieżki. Wineboot240s i kontrolnyPE32 45s nie zakończyły się
w limicie (143); oryginału nie uruchomiono. Nie traktować uruchomienia kernela,
Xvfb ani QEMUexit0 jako dowodu gry. Wszystkie własne procesy VM zakończono.
