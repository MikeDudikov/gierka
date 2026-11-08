# Start projektu w Claude Code

1. Rozpakuj całą paczkę do katalogu, który pomieści projekt i zachowane dowody.
   Nie kopiuj tylko plików śledzonych przez Git: Unity, dane źródłowe i duża
   część testów są obecnie nieśledzone lub ignorowane.

   ```sh
   tar -xzf AncientConquest-ClaudeCode-2026-11-04.tar.gz --no-same-owner
   cd AncientConquest-ClaudeCode/gierka
   ```

   Katalogi gierka i toolchains powinny pozostać obok siebie. Archiwum obejmuje
   kilkadziesiąt GB danych przed kompresją; zachowane dowody są większe niż
   sam projekt Unity. Sprawdź sumę archiwum z sąsiedniego pliku .sha256.
2. Otwórz katalog `gierka` w Claude Code. Instrukcje zostaną odczytane z
   głównego `CLAUDE.md`. Gotowy tekst pierwszego polecenia jest w
   `handoff/POLECENIE_DLA_CLAUDE.txt`.
3. Przeczytaj `STAN_I_PLAN.md` oraz `SRODOWISKO.md`. Uruchom weryfikację plików:

   ```sh
   python3 tools/handoff_verify.py --root .
   ```

4. Najbardziej zgodny układ roboczy to `/workspace/gierka`, z narzędziami
   w `/workspace/toolchains`. Wiele dotychczasowych skryptów celowo używa
   tych ścieżek. Dostarczony Dev Container odwzorowuje ten układ. Można też
   pracować bez kontenera w Linux/WSL2, zachowując te ścieżki.
5. Zainstaluj zależności Python przez `bash tools/handoff_bootstrap.sh`.
   Tryb `--unity` odtwarza oficjalny toolchain Unity, a `--wine` uruchamia
   istniejący instalator Wine. Żaden tryb nie publikuje projektu ani nie
   akceptuje lub przenosi danych logowania.
6. Otwórz `Unity/AncientConquest` w Unity6000.3.27f2. Cache Library jest celowo
   pominięty; Editor odbuduje go. Nie aktualizuj wersji projektu lub pakietów.

## Co jest przenoszone

Cały kod, komplet Assets/Packages/ProjectSettings i meta, referencje z płyty,
testy i ich fixture, zachowane dowody i logi, ostatni build Windows oraz historia
repozytorium. Paczka obejmuje również bieżące niecommitowane pliki.

Pominięto odtwarzalne cache Unity/Python, prywatne profile Wine, pełny Unity
Editor i dane aktywacji. Przenośne narzędzia analityczne są w sąsiednim
katalogu toolchains. Dokładną listę wyłączeń i sumy
plików zapisuje `TRANSFER_MANIFEST.json`. To nie jest sam eksport UnityPackage.

Nie przenosimy sprzętowo powiązanej aktywacji Unity Personal. Na nowej maszynie
Editor może wymagać zalogowania właściciela licencji. Analiza kodu i testy x86
mogą ruszyć wcześniej. Nie zapisuj tokenów lub plików licencji w repozytorium.
