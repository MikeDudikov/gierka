# Stan przekazania i kolejność kontynuacji

Użytkownik zlecił zakończyć ostatnią diagnostykę i przygotować przeniesienie
do Claude Code. W tej sesji nie rozpoczynamy dalszego rozwoju po przekazaniu.
Stare polecenia ciągłej pracy w dokumentach są historią.

## Ostatni sprawdzony stan Unity

- Projekt: `Unity/AncientConquest`; Editor6000.3.27f2(22188f149405).
- Checkpoint: `docs/evidence/milestone-20261104-source-app-activation.json`.
  SHA256: `97300b269a9662eeeffffbdb8ed9ff6c359f1a21d2e27612beac39efd5925669`.
- 74 pliki C#,133 meta,279 plików projektu. Manifest indywidualnych sum:
  `artifacts/source-app-activation/project-frozen.json`.
- Build Windows64Mono:153601435 bajtów,0 błędów/ostrzeżeń,1920×1080.
  DLL SHA256:`670bf3055166d56115afc3e85e9d1e6ff812f991ec7ce956222aea2baedf173c`.
- 12 wybranych testów PASS;349 wykrytych testów, bez pełnego uruchomienia.
  33624 porównane stany aktorów na finalnej DLL PASS.
- Dwa replaye kontekstu: każdy39 checkpointów,117 stanów aktorów,291 publikacji,
  4 operacje kontekstu i13 kontroli negatywnych. Wcześniejszy profil35/105/291 PASS.
- `SingleStepClock`, `ShipWorldStep`, zadania, członkostwo, siatka i80 plików
  Resources nie zmieniły się w ostatnim etapie.

Szczegóły: `docs/SOURCE_BASE_DISPATCH.md` i `docs/SOURCE_APP_ACTIVATION.md`.
Nie ma nowej implementacji fizycznego fokusu OS. Istnieje jawne wejście
resetu kontekstu do kontrolowanego replaya oraz port stanu C45D/C45E.

## Ostatnie działanie i jego wynik

Badano oficjalny instalator oryginalnej gry w prywatnej VM bez sieci, aby
usunąć komunikat „The registry record is corrupted. Try to reinstall the game.”
Oryginał nie został jeszcze poprawnie zainstalowany w tym profilu.

`artifacts/original-install-vm/observe-01`: kontrola Wine nie ruszyła przez
właściciela skopiowanego profilu; poprawiono właściciela tylko w gościu.
`observe-02` i `observe-03`: kontrola PE32 przeszła; odczytano okna wymagań
DirectX/DirectShow. Oficjalne regsvr32 dla DirectDraw32 zakończyło się kodem0.
Istniejące mapowanie DLL w initramfs było już prawidłowe; próba ponownego
utworzenia aliasu w03 była zbędna i jest usunięta z aktualnego skryptu.

`install-01`: zastosowano odczytaną opcję Resume. Instalator zatrzymał się na
DirectShow, a ograniczony czas obserwacji upłynął; nie wyeksportowano konfiguracji
gry. `install-02`: kontrolny proces Wine został zakończony kodem137 po błędzie
loadera/usługi, zanim ruszył instalator; eksport rejestru również nie powstał.
`exit_code=0` całej VM nie oznacza poprawnej instalacji. Nie ma pozostawionej
działającej VM ani zakończonej instalacji, którą należałoby traktować jako sukces.

Oryginalne pliki nie zostały zmienione. Ta diagnostyka nie zmieniła Unity.
Wyniki są zamknięte jako rozpoznana blokada środowiska, nie działający remake.

## Następne kroki dla Claude

1. Uruchomić `handoff_verify.py` i sprawdzić finalny projekt, źródłowe EXE,
   fixture i aktualne instrukcje; zachować bieżący dirty/untracked stan Git.
2. Odtworzyć Python i toolchainy według `SRODOWISKO.md`; wykonać małą walidację
   x86 i C#. Nie odtwarzać na ślepo historycznych poleceń z logów.
3. Ustabilizować kontrolę PE32 w prywatnej VM, zanim ponowi się instalator.
   Aktualny runner: `tools/run_original_installer_vm.py`; nie używać kolejnego
   katalogu wyników, który już istnieje. Najpierw jedna hipoteza i kontrola,
   potem instalator. Brak OpenGL oraz brakujące klasy32bit COM są w stderr.
4. Dokończyć oficjalną instalację, sprawdzić wynik konfiguracji, komplet plików
   i SHA EXE; nie wymyślać wpisów rejestru. `actions.txt` steruje wyłącznie
   znanymi kontrolkami własnego instalatora. Nie traktować nieaktualnej akcji
   zapisanej do pliku po wyłączeniu VM jako wykonanej.
5. Dopiero po poprawnym starcie oryginału wrócić do natywnego pomiaru4eff00
   oraz cyklu wejścia/aktywacji. Nie łączyć Unity OnApplicationFocus z całym
   WM_ACTIVATEAPP na podstawie samej nazwy callbacka.
6. Kontynuować plan `docs/REMAKE_PLAN.md` na podstawie dowodów. Pełne misje,
   Start, AI/bitwy/ekonomia/audio/zapis i końcowa oprawa2026 nadal wymagają pracy.

Host Wine32 wcześniej nie docierał do entry point z powodu ograniczenia IA32.
Nie powtarzać bez zmiany warunków tych samych nieudanych prób hosta.
Maszyna lub nowy komputer z prawidłowym wsparciem32bit może być prostszym
źródłem natywnych pomiarów niż obecny cloud; nie zmienia to algorytmów gry.

Po kontynuacji nie publikować ani nie pushować bez nowego polecenia użytkownika.
Nie generować cyklicznych podglądów i paczek. Zgłaszać postęp po polsku.
