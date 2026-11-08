# Statyczna analiza kodu oryginału

Stan: 2026-11-02. Badanie dotyczy wyłącznie `ancient.exe` z dostarczonego obrazu:
SHA-256 `cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`,
PE32 x86, ImageBase `0x400000`. Nie odzyskano oryginalnych plików C++.
Dekompilacja jest przybliżeniem kodu maszynowego, nie odtworzonym kodem źródłowym.

Analizowano kopię w `artifacts/binary-analysis/input/`; oryginał zachował hash.
W ramach tej analizy statycznej i opisanego niżej testu oryginał nie był
wykonywany przez system operacyjny. Nie wysyłano binariów do zewnętrznej usługi.
Nie patchowano EXE ani jego zabezpieczeń.

## Narzędzia i odtwarzalność

Zainstalowano lokalnie oficjalne Ghidra **12.2** i Temurin JDK **25.0.5+8**,
wymagany przez tę wersję Ghidra. Systemowa Java 21 pozostała bez zmian.

| Artefakt | Oficjalne źródło | SHA-256 |
| --- | --- | --- |
| `ghidra_12.2_PUBLIC_20261016.zip` | GitHub `NationalSecurityAgency/ghidra`, `Ghidra_12.2_build` | `2c2cd776db3c1f6a097ba418922378ac3649cadd5e844a6f5f088ae628a7be67` |
| `OpenJDK25U-jdk_x64_linux_hotspot_25.0.5_8.tar.gz` | GitHub `adoptium/temurin25-binaries`, `jdk-25.0.5+8` | `68982529869257d0ee6b824ec5aa270ff8b118bb438670da0b97ebdab178d7fb` |

Obie sumy porównano z metadanymi oficjalnych wydań przed użyciem. TLS i proxy
pozostały włączone. Narzędzia są w `/workspace/toolchains/`; ustawienia Ghidra
i cache również trafiają do tego katalogu. Limit sterty 8 GiB, maksymalnie
4 CPU. Pierwsza analiza zakończyła się poprawnie po 157 s i rozpoznała
**4360 funkcji**. Nie znaleziono PDB ani DWARF. Nie ładowano DLL Windows;
typy API pochodzą z archiwum typów dostarczonego z Ghidra.

Sprawdzony pomocnik odmawia analizy innego EXE i nadpisania raportu:

```sh
bash tools/analyze_original_binary.sh \
  /workspace/gierka/artifacts/binary-analysis/export-new
```

Wymaga już zainstalowanych, przypiętych Ghidra/JDK oraz `pefile` ze środowiska
repozytorium. Tworzy kopię wejścia i projekt analizy przy pierwszym uruchomieniu;
następnie używa istniejącego projektu tylko do odczytu, bez powtarzania analizy.
Eksport obejmuje xrefy do API czasu, diagnostycznych nazw AI/misji i wybrane
funkcje ich wywołania. Powtórzenie pomocnika zakończyło się kodem 0; końcowy
eksport zawiera **139 funkcji i 212 referencji**. Wyniki C i JSON są ignorowane
przez Git.

## Potwierdzone punkty wejścia

Adresy poniżej to **VA**, nie offsety pliku. Nazwy pochodzą z diagnostycznych
napisów w tym samym EXE i ich xrefów. Nie oznaczają znalezienia plików źródłowych.

| VA funkcji | Powiązanie | Zakres potwierdzenia |
| --- | --- | --- |
| `0x541600` | `AppClassTy::RunApp` | Pętla komunikatów Windows, `timeGetTime`, oczekiwanie i dyspozycja iteracji |
| `0x541520` | Iteracja aplikacji | Opróżnia kolejki komunikatów, wywołuje aktualizację systemów |
| `0x5413c0` | `AppClassTy::LifeToAllSystem` | Wywołanie slotu vtable `+0x1c` aktywnych systemów i rekursja po dzieciach |
| `0x5417d0` | Odczyt wspólnego zegara | Zwraca pole `this+0x18`, aktualizowane przez pętlę aplikacji |
| `0x50f6d0` | `GameSystemTy::Life` | Menedżer systemu gry; nie należy automatycznie utożsamiać go z krokiem symulacji |
| `0x51fdb0` | `PlaySystemClassTy::Life` | Rozgałęziony przebieg kroku świata, zegara i trybów pracy |
| `0x448d40` | `Boss_KibClassTy::GetMessage` | Dyspozycja komunikatów i bramka wywołania decyzji AI |
| `0x448610` | Wywołanie decyzji z powyższego handlera | Treść wyeksportowana; pełne znaczenie priorytetów i stanów jeszcze nieodtworzone |
| `0x421490` | `LAiGetTownsInZone` | Nazwa potwierdzona napisem błędu i xrefem `L_Ai.cpp` |
| `0x421740` | Pomocnik z `L_Ai.cpp` | Wyszukiwanie danych obiektu/strefy; semantyka wszystkich pól nieustalona |

Zmapowano również procedury diagnostycznie związane z `brain/miss000.cpp` do
`miss013.cpp`, `missCOM.cpp`, `missweb.cpp`, `Plr_kib.cpp` i pokrewnymi plikami.
Sama mapa funkcji nie dowodzi ukończenia scenariuszy ani znajomości wszystkich
reguł AI. Pełny aktualny eksport: `artifacts/binary-analysis/export-final/`.

## Zegar i prędkość gry

`0x4ed410` odczytuje rekord `SPEED_GAME`, zapisuje indeks w `0x5ca556` i ustawia
pole okresu pętli aplikacji `this+0x34` z tabeli o kroku 24 bajtów. Instrukcja
pod `0x4ed439` adresuje drugi dword jako `0x5bed78 + indeks*24`.
Inicjalizacja ustawień pod `0x5016a0` przypisuje indeks **5**. To wartość
domyślna kodu przed ewentualnym wczytaniem konfiguracji/zapisu.

Zaobserwowana tabela danych obejmuje dziewięć rekordów:

| Indeks | Pole 0, użyte jako kwant czasu świata | Pole 1, okres pętli aplikacji | Pozostałe cztery dwordy |
| --- | ---: | ---: | --- |
| 1 | 13 | 13 | 15, 3, 13, 5 |
| 2 | 17 | 17 | 12, 2, 17, 5 |
| 3 | 20 | 20 | 10, 2, 20, 5 |
| 4 | 33 | 33 | 7, 1, 33, 3 |
| 5 | 40 | 40 | 5, 1, 40, 2 |
| 6 | 50 | 40 | 4, 1, 40, 2 |
| 7 | 60 | 40 | 3, 1, 40, 1 |
| 8 | 70 | 40 | 2, 1, 40, 1 |
| 9 | 80 | 40 | 1, 1, 40, 0 |

Nie przypisano pozostałym polom nazw bez prześledzenia wszystkich odczytów.
Plik `speed-table-observed.json` zachowuje wartości i adres każdego rekordu.

W **jednej konkretnej gałęzi** `PlaySystemClassTy::Life`, od `0x520352`,
różnica bieżącego zegara aplikacji i pola `this+0xe6` jest dzielona przez pole 0
tabeli. Wynik trafia do `this+0xe2`. Zero pomija krok; każdy wynik większy od
1 w porównaniu unsigned jest ograniczany do **jednego**. Przyjęty krok dodaje
się do licznika `this+0xde`, po czym wywoływane są `0x521500`, `0x522850`
i bazowa aktualizacja. Reszta modulo zachowuje fazę czasu w `this+0xe6`.

To ważna różnica względem nieograniczonego nadrabiania kroków po zacięciu.
Portowanie całości jako arbitralnego `FixedUpdate` 60 Hz zmieniłoby zachowanie.
Domyślna para wartości to 40/40, ale nie jest to jeszcze pomiar rzeczywistej
liczby klatek ani dowód wszystkich trybów rozgrywki.

Ta funkcja ma osobne wcześniejsze ścieżki: `app+0x322d`, `GameSystem+0x17e6`,
`app+0xd7c`, `app+0x30d9` z `app+0x30de`, a także warunki przy polach
`app+0x1a11`, `this+0x4f`, `GameSystem+0x17ea`, `this+0xee`. Ich pełne znaczenie,
powiązanie z pauzą, siecią i odtwarzaniem wymaga dalszej analizy. Nie wolno
przenosić tylko opisanej gałęzi jako całego zegara gry.

Nie należy mylić tego z wrapperem `timeSetEvent` pod `0x583d24`: przelicza on
64-bitową różnicę czasu przez 10000 i ustawia **jednorazowy** callback dopiero
dla wartości co najmniej 50, z rozdzielczością 10. Jest to osobna ścieżka
multimedialna; nie wyznaczono na jej podstawie częstotliwości symulacji.

## Pierwsza izolowana reguła AI i porównanie z instrukcjami oryginału

`Boss_KibClassTy::GetMessage` kopiuje pole `*(this+0x0c)+0xde` do `this+0x18`,
następnie wywołuje bazowy handler `0x542550`. Potem odczytuje ID komunikatu
z `message+0x10`:

| ID | Bezpośrednia akcja bramki |
| --- | --- |
| 0 | Wywołaj `0x448610` tylko jeśli uint32 counter modulo 250 wynosi zero |
| `0x0d8fd7` | Wywołaj `0x448610` niezależnie od licznika |
| 2 | Wyzeruj bajt globalny `0x5c7468`, bez wywołania decyzji |
| inne | Bez wywołania decyzji i bez zmiany tego bajtu |

Normalne ścieżki zwracają zero i przywracają własny łańcuch obsługi wyjątków.
Nie zakładamy jednostki licznika w samym kontrakcie. Przed podłączeniem go do
zegara trzeba potwierdzić wiązanie rodzica i sposób dostarczania komunikatu 0.
Nie opisujemy tej reguły skrótem „AI co 250 ms”.

Unicorn **2.1.4** wykonał oryginalne instrukcje tej funkcji w odizolowanej
pamięci emulowanego x86. Przecięto dokładnie trzy wywołania: `__setjmp3`
zwraca 0, bazowy handler jest no-op, a `0x448610` zapisuje fakt wywołania.
Nie wykonuje to mózgu AI ani nie potwierdza skutków ubocznych bazowego handlera.

Porównano z czystym C# **35 przypadków**: liczniki 0, 1, 249, 250, 251, 500,
uint32 max oraz ID 0, wymuszenie, 2, 1, uint32 max. C# zwrócił zgodne żądania
wywołania decyzji i wyzerowania flagi. Niezależnie sprawdzono po stronie
emulowanego x86 kopię licznika, zerowy wynik i przywrócenie łańcucha wyjątków;
te trzy efekty nie należą do kontraktu czystej reguły C#. Skompilowano i
wykonano rzeczywisty plik z projektu Unity, używając dostarczonego z nim Mono.

Reguła jest w
`Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/BossAiMessageGate.cs`.
Nie ma jeszcze podłączenia do zegara, scen ani kompletnego mózgu AI.
Przenośny test `tools/validate_boss_ai_gate.py` kompiluje właśnie ten plik z
`tests/fixtures/GateCaseProbe.cs`. Raport bieżącego wykonania znajduje się w
`artifacts/binary-analysis/boss-gate-validation.json`; wcześniejszą próbę
zachowano osobno w `pending-domain/validation.json`.

`tests/test_boss_ai_gate.py` wykonuje te same 35 porównań i przechodzi w tym
środowisku bez pominięcia. W środowisku bez prywatnych danych oryginału lub
lokalnego kompilatora zgłasza jawne pominięcie. Niezgodny hash EXE lub wynik
porównania jest błędem, nie pominięciem. Nie podmieniono AI na odgadnięty
algorytm. Jednostki licznika i priorytety decyzji pozostają do odtworzenia.

```sh
# Lokalne narzędzie analizy; nie zmienia zależności gry.
.venv/bin/python -m pip install -r tools/requirements-analysis.txt
.venv/bin/python tools/validate_boss_ai_gate.py \
  --output artifacts/binary-analysis/boss-gate-validation-new.json
.venv/bin/python -m unittest tests.test_boss_ai_gate -v
```

Narzędzie wyznacza katalog repozytorium na podstawie własnej lokalizacji.
Domyślnie znajduje Mono w lokalnej instalacji wersji Unity z `ProjectVersion.txt`;
inną instalację można podać przez `UNITY_MONO_ROOT` lub `--mono-root`.
Nie nadpisuje istniejącego raportu. Zależność emulacji to przypięty Unicorn
2.1.4 w `tools/requirements-binary-analysis.txt`, dołączony przez główny plik
zależności analitycznych.

Analiza nie potwierdza kompletnej symulacji, zachowania oryginału pod Windows,
gotowości remake’u ani wydajności na docelowym laptopie.
