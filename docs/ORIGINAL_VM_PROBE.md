# Pełna VM do referencji oryginału

Aktualizacja2026-11-04:kontrolnyPE32 i wybrane oryginalne funkcje CRT przeszły
w nowej VM z przygotowanym profilem i zależnościami ekranu. To nie uruchomienie
pełnej gry. Czytać[QUEUED_CRT_CONTEXT.md](QUEUED_CRT_CONTEXT.md);poniższe
nieudane próby są historyczne i pozostają zachowane.

---

Stan: 2026-11-02. Próba pełnego gościa Linux w QEMU TCG rozwiązuje inny problem
niż dotychczasowy `qemu-user`: gość ma własny kernel z obsługą IA32. Nie zmieniono
EXE, adresu bazowego ani danych Ancient Conquest. Wymiar remake’u nie wpływa
na konfigurację oryginału w tym badaniu.

## Zweryfikowane narzędzia

Do lokalnego `/workspace/toolchains/original-vm-root` rozpakowano 31 oficjalnych
pakietów Debiana. APT używał wcześniej zweryfikowanych podpisanych indeksów i
sprawdził hashe pobrań. Pakiety zajęły 126 MB transferu; systemowego APT nie
modyfikowano. Manifest SHA-256 jest w
`/workspace/toolchains/original-vm-apt/package-manifest.json`.

- QEMU `10.0.13`, pakiet `1:10.0.13+ds-0+deb13u1`.
- Kernel `6.12.113+deb13-amd64`, pakiet `6.12.113-1`.
- Konfiguracja kernela: `CONFIG_IA32_EMULATION=y`; domyślne wyłączenie IA32 nie
  jest ustawione.
- SeaBIOS `1.16.3-2`; ścieżka BIOS-u jest przekazywana jawnie.
- BusyBox statyczny `1:1.37.0-6+b9` i niewielki initramfs z czterema modułami 9p.
- Wine 11.0 pochodzi z wcześniej zweryfikowanej instalacji WineHQ.

`tools/prepare_original_vm.py` tworzy initramfs i zbiera 109 bibliotek systemowych,
zapisując SHA-256 ich źródeł. Uwzględnia zarówno `ldd`, jak i SONAME-y ładowane
przez `dlopen` w oryginalnych modułach Wine: samo `ldd` pomijało wymagane biblioteki
grafiki/fontów. Cztery brakujące opcjonalne SONAME-y są jawnie zapisane w
`dlopen-libraries.json`; nie uznano ich za zainstalowane.

`guest-wine` jest osobną kopią przez hardlinki Wine, uzupełnioną publicznymi danymi
XKB, `xkbcomp`, fontami i konfiguracją Fontconfig z zarządzanego Debiana.
Nie kopiuje kont, konfiguracji uwierzytelniania ani katalogów użytkowników.

## Ograniczenie dostępu

VM działa przez TCG, bez `/dev/kvm`, sieci gościa i hostowego serwera ekranu.
Udostępniono tylko trzy katalogi danych/narzędzi do odczytu i jeden nowy katalog
raportów do zapisu. Nie eksportuje się hostowego `/`, kont, sekretów ani całego
`/workspace`. Profil Wine i framebuffer Xvfb są w pamięci gościa pod `/tmp`.

Pierwsza próba zakończyła się przed startem kernela: QEMU nie znalazł BIOS-u.
Ponowienie poza sandboxem zostało odrzucone przez automatyczny przegląd z powodu
limitu użycia usługi przeglądu; nie był to werdykt niebezpieczeństwa. Dalszy probe
wykonano bez eskalacji w zwykłym sandboxie, z wyżej ograniczonym dostępem.

Gość rzeczywiście wypisał `Linux ... 6.12.113+deb13-amd64 ... x86_64` oraz
`wine-11.0`. Statyczny ELF32 wykonuje bezpośrednie `int 0x80` i wypisuje
`IA32_PROBE_OK`, kończąc się kodem `IA32_EXIT=0`. Źródło asemblera i hash binarki
znajdują się w manifeście. To dowód odblokowania ścieżki IA32 w pełnej VM,
nie dowód ukończenia inicjalizacji Wine ani uruchomienia PE32 gry.
Pierwsze konfiguracje Xvfb wymagały dwóch poprawek przygotowania: framebuffer
musi być w lokalnym `/tmp` (mmap przez 9p odrzucony), a rootfs musi zawierać
XKB oraz `xkbcomp`. Surowe logi zachowano pod `artifacts/runtime-original/vm`.

## Uruchomienie kontrolne

```sh
python3 tools/prepare_original_vm.py
bash tools/run_original_vm_probe.sh \
  /workspace/gierka/artifacts/runtime-original/vm/fresh-run-name
```

Launcher odmawia nadpisania istniejącego katalogu i zapisuje hashe kernela,
BIOS-u oraz initramfs. Hostowy limit wynosi 360 s, guest `wineboot` ma limit
240 s, a kontrolny PE32 `cmd.exe` 45 s. Gość ma 4 GB RAM; zapisuje dane profilu
i cache w swoim `/tmp`. Start nie wymaga sieci ani uprawnień poza zwykłym
sandboxem. Lokalny loopback służy wyłącznie komunikacji procesów gościa.

Próby z krótszym limitem 90 s nie zakończyły Wineboot; po nich kontrolny PE32
również osiągał limit. Zrzut ósmego gościa pokazuje okno „The Wine configuration
... is being updated, please wait…”, nie grę. Profil zajmował około 1 GB;
było wolne miejsce, a pula entropii wynosiła 256. Log odnotowuje błędy
marshalingu COM i otwarcia usługi RpcSs, bez przypisywania ich Ancient Conquest.

Stan końcowy i dowód PE32 należy odczytać z `serial.log`, `control32.log` oraz
`status.json`; obecność Xvfb lub samego procesu nie jest wynikiem działania
oryginału. Narzędzie obecnie wykonuje kontrolę PE32, nie startuje automatycznie
Ancient Conquest po jej zakończeniu. Oryginał pozostaje oddzielną bramką.

## Końcowy wynik tego etapu

Próba `artifacts/runtime-original/vm/ninth-240s-wineboot/` wykonała cały
uzgodniony limit: **Wineboot 240 s → 143 (zakończenie przez timeout), kontrolny
PE32 45 s → 143**. Log zawiera błędy COM/RpcSs, uruchamiania usługi `winebth`
oraz oczekiwania sekcji krytycznej loadera NTDLL. Nie ustalono jednego
potwierdzonego źródła tej nowej blokady Wine i nie przypisano jej grze.

Kernel, ELF32 `int 0x80`, natywny Wine i Xvfb przeszły swoje kontrole. **PE32
i Ancient Conquest nie przeszły bramki uruchomienia**. Hostowe ograniczenie IA32
nie wyjaśnia już wyniku pełnej VM; dalsza analiza powinna dotyczyć inicjalizacji
Wine w gościu lub kompletnego, zgodnego stanowiska referencyjnego.

QEMU zakończył się kodem 0 po poprawnym wyłączeniu gościa; ten kod **nie oznacza
powodzenia Wine ani gry**. Nie pozostał żaden własny aktywny proces VM.
`artifacts/runtime-original/vm/status.json` zawiera rozdzielone wyniki,
sumy raportów i pomiary; `final-input-manifest.json` zapisuje hashe źródeł,
kernela, BIOS-u, initramfs i binarki ELF32. Końcowy zrzut gościa obejrzano:
jest czarnym ekranem Xvfb z kursorem. We wcześniejszej ósmej próbie widoczne
było okno aktualizowania profilu Wine. Żaden nie przedstawia menu Ancient Conquest.
