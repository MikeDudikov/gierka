# Środowisko po przeniesieniu

## Zalecany układ

Linux x86_64 lub WSL2. Najprościej użyć dostarczonego Dev Containera:
Debian trixie, projekt `/workspace/gierka`, narzędzia `/workspace/toolchains`.
Paczka zawiera katalogi `gierka` i `toolchains` obok siebie. Konfiguracja
kontenera montuje je pod tymi samymi ścieżkami co w dotychczasowym środowisku.
Nie przenoś samych skryptów bez danych i katalogu narzędzi.

Bez kontenera można użyć istniejącego Linux/WSL2 i utworzyć ten sam układ.
Zmienna AC_TOOLCHAIN_ROOT pomaga w nowych skryptach przekazania, ale stare
narzędzia nadal mają ścieżki absolutne. Nie wykonuj masowej zamiany ciągów
`/workspace` w całym repozytorium; zmieniłaby także historyczne dowody.

## Dołączone narzędzia Linux

Przenoszone są istniejące narzędzia do analizy: Mono z użytego edytora jako
osobny toolchain, Ghidra12.2/JDK25.0.5+8, lokalne kompilatory MinGW, Wine11,
QEMU z jądrem gościa i przygotowane obrazy initramfs. Nie przenosimy kont,
plików aktywacji Unity lub prywatnych profili Wine. Skrypty przekazania
weryfikują sumy dołączonych plików. Szczegóły mapowania zapisuje manifest.

Nie są to natywne narzędzia Windows. W Windows otwórz paczkę w WSL2 lub
Dev Containerze. Sam projekt Unity można otworzyć w natywnym edytorze Windows
w tej samej wersji, lecz dotychczasowe narzędzia analityczne działają w Linux.

## Python i szybki start

```sh
cd /workspace/gierka
bash tools/handoff_bootstrap.sh
source tools/handoff_env.sh
python3 tools/handoff_verify.py --root .
.venv/bin/python -m unittest tests.test_source_route_key_state tests.test_source_context_markers
```

Zależności są przypięte w tools/requirements-analysis.txt:
pycdlib1.22.0,pefile2024.8.26,Pillow13.0.0,Unicorn2.1.4.
Dołączone Mono pozwala porównywać czyste C# bez aktywnego Unity Editora.
Niektóre testy używają bibliotek z zachowanej DLL Windows/netstandard.

## Unity

Editor6000.3.27f2(22188f149405), URP17.0.3,InputSystem1.20.1.
Cache Library nie jest częścią paczki. Pełny Editor można odtworzyć:

```sh
bash tools/handoff_bootstrap.sh --unity
source /workspace/toolchains/unity-env.sh
Unity -batchmode -nographics -quit -job-worker-count 4 \
  -projectPath /workspace/gierka/Unity/AncientConquest \
  -executeMethod AncientConquest.Editor.BuildReferenceWindows.Build \
  -logFile /workspace/gierka/artifacts/handoff-new-build.log
```

Budowanie zapisuje wynik w artifacts/unity-reference/Windows. Przed nowym
buildem zachowaj jego aktualną DLL i build-report, gdy potrzebujesz porównania.
Na nowej maszynie może być potrzebna własna aktywacja Unity Personal; nie
kopiuj plików licencji z innego komputera. Instalator narzędzi sam jej nie aktywuje.

## Testy x86 i ostatnia funkcja

```sh
.venv/bin/python -m tools.validate_source_base_dispatch --output artifacts/handoff-base-check.json
.venv/bin/python -m tools.validate_source_app_activation --output artifacts/handoff-activation-check.json
.venv/bin/python -m tools.validate_source_route_key_state --output artifacts/handoff-csharp-check.json
```

Pełna kolekcja ma349 testów. Ostatni etap uruchomił12 wybranych, nie całość.
Nie traktuj samego discovery jako wyniku testów. Rozszerzaj zakres adekwatnie
do zmiany i zachowuj nieudane logi.

## Wine i VM

Prywatny profil należy odtworzyć; stare profile z kontami użytkownika nie są
częścią paczki. `bash tools/handoff_bootstrap.sh --wine-prefix` inicjuje pusty
profil w istniejącym miejscu oczekiwanym przez launchery. To nie instaluje
oryginalnej gry i nie usuwa znanej blokady32bit. W razie braku narzędzi Wine
można odtworzyć pakiety przez `--wine` (istniejący skrypt weryfikuje podpisy APT).

Ostatni runner: tools/run_original_installer_vm.py. Jego gość nie ma sieci,
wszystkie wejścia hosta są RO, rejestr i dysk C są prywatne. Używaj nowego
katalogu wynikowego. Do sterowania potrzebny jest świadomie zapisany actions.txt;
przy przekazaniu jest pusty. Nie uruchamiaj nieznanych akcji z dawnych logów.

```sh
.venv/bin/python -m tools.run_original_installer_vm \
  --output artifacts/original-install-vm/new-observation
```

Najpierw musi przejść kontrola PE32. Wynik ostatniej próby i dokładne blokady
opisuje STAN_I_PLAN.md. Nie ma potwierdzenia działania oryginału w całości.

Ghidra używa projektu artifacts/binary-analysis/projects/AncientConquest;
eksporty wykonuj read-only. Zachowane narzędzia Linux mogą wymagać zwykłych
bibliotek systemowych; Dockerfile instaluje ich podstawowy zestaw. Nie
testowano zimnego startu tego kontenera na komputerze użytkownika.
