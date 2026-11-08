# Kontekst oryginalnego CRT i wave[-1] — 2026-11-04

Ustalono ograniczony, rzeczywiście wykonany profil oryginalnego CRT pod
Wine11 w pełnej VM. W512zmierzonych alokacjach1152B słowo przed buforem
wynosi117, nie0. Dla nieosiągalnego celu ta różnica zmienia emisję rozkazów
100/2. Kod C# i blokada Shift w Unity pozostają bez zmian.

## Wykonanie oryginału

- Ghidra readOnly/noanalysis:13funkcji CRT, C i assembler, weryfikacja SHA
  oryginalnego EXE `cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
- Oryginalny startup588e9b zerujeESI i przekazuje0 do heap_init58ec07.
  Ta funkcja wykonuje HeapCreate z flags1 i inicjalizuje tablice SBH.
- Próbnik Win32 wykonuje niezmienione58ec07(0),malloc589bf5 i free589bc6.
  Instrukcje i dane CRT są kopiowane z dostarczonego PE; nie są rekompilowane.
  IAT Kernel32 jest rozwiązywane do rzeczywistych funkcji Wine.
- Własna sekcja próbnika rezerwuje580000..5ddfff podczas ładowania PE,
  dzięki czemu CRT zachowuje oryginalne adresy. Nie wykonywano relokacji kodu
  oryginału ani jego wejścia588e44. Nieużywany kod gry nie jest uruchamiany.
- Przed pomiarami próbnik tworzy historię96alokacji o rozmiarach1..4096,
  zwalnia część, mierzy256bloków1152B i przeplata32dodatkowe alokacje/zwolnienia.
  Dwa świeże uruchomienia VM dają512próbek;wszystkie mają prefix117 i HeapSize1152.
  Próg źródłowego SBH to1016,początkowy HeapCompatibilityInformation=0.

To profil jawnej inicjalizacji i historii alokacji, nie pełny startup gry
ani pełna historia jej sterty. Nie dowodzi wartości117 w Windows98/Windows11
lub dla innych polityk sterty. W porcie nie wolno wpisywać117 jako ogólnej
stałej gry; słowo otoczenia musi być jawnym, uzasadnionym wejściem zgodności.

## Błędy prób i bramka PE32

Na hoście minimalny kontrolny PE64 przechodzi,PE32 kończy sięSIGSEGV,
także bez kodu gry. To oddzielna bramka architektury,nie błąd Ancient Conquest.
Minimalny gość wykonał ELF32,int0x80 i IA32_EXIT0,lecz kontrolaPE32 osiągnęła45s
(EXIT137),więc CRT poprawnie pominięto. KodQEMU0 nie oznacza powodzenia CRT.

Po dodaniu lokalnego Xvfb,fontconfig i cache oraz użyciu przygotowanego
profilu Wine kontrolny PE32 przechodzi. Profil i narzędzia są w VM tylko do
odczytu;reg jest kopiowane do jej tmpfs. VM nie ma sieci,KVM ani montowania
hostowego /. Jedynym udostępnionym katalogiem do zapisu jest nowy raport.
800×600 dotyczy pomocniczego Xvfb,nie rozdzielczości remake’u.

Pierwsze wrappery nie mogły zająć oryginalnego zakresu(EXEC error487)
przed wywołaniem CRT. Próba bufora od góry nie rozwiązała już istniejącego
mapowania. Finalny wrapper rezerwuje zakres jako własną sekcję PE i nadpisuje
w niej wyłącznie oryginalne strony CRT/danych. Dwa finalne goście mają:
IA32_EXIT0,CONTROL32_EXIT0,CRT_EXIT0 i komplet256rekordów każdy.
Zachowano wszystkie wcześniejsze logi i binarki;nie używa się ich jako sukcesu.

Kompilator i686 MinGW14 pochodzi z6oficjalnych pakietów Debiana,sprawdzonych
podpisanym InRelease i SHA pakietów. Rozpakowano je lokalnie do
`/workspace/toolchains/mingw32-crt`;systemowego APT nie zmieniono.
Pierwsze pobranie w sandboxie nie miało dostępu do sieci;ponowienie przez
skonfigurowane proxy poza sandboxem przeszło. Nie zmieniono polityki sieci.
Build wrapperów używa -Wall -Wextra -Werror. Poprawiono wyłącznie formatowanie
własnego C po pierwszym błędzie misleading-indentation. Odtworzenie trzech
własnych binarek daje identyczne SHA,bez timestampów linkera.

## Złożenie pomiaru z zachowaniem100/2

Słowo117 z rzeczywistego próbnika zostało przekazane jako jawny kontekst
do osobnego emulatora oryginalnego4ceab0/4cf550. UI518070 i wejście floty49e230
w niezależnych silnikach dają identyczne wyniki. Nie podmieniono instrukcji
porównania lub algorytmu wyboru punktu.

| Mapa/kontekst | Kandydaci fali dla0b/0c/0d | Okresowe20 |
| --- | --- | --- |
| Mapa misji,słowo0 |29994/29985/29991 |0b,0c,0d |
| Mapa misji,zmierzone117 |29994/29985/29991 |0b,0c,0d |
| Syntetyczne rozłączne wyspy,słowo0 |0/0/0 |0b,0c,0d |
| Te same wyspy,zmierzone117 |0/0/0 |Brak |

Mapa wysp ma tylko komórki startów i punktów oznaczone wodą,resztę blokuje.
Jest to jawne wejście testu,nie zmiana mapy misji na dysku lub dowód jej
osiągalności podczas gry. Wynik wykazuje,dlaczego wcześniejszy wyzerowany
backend alokatora był niewystarczającym kontraktem dla wszystkich tras.
Porównanie w4cebc7 jest signed16;nie zastępowaćOR→AND lub automatycznym0.

Korpus połączony:4przypadki/12CMP,24porównania dla obu wejść.
7testów PASS0skip12.933s:4nowe i3regresje wcześniejszej granicy fali.
316testów discovery;pełnego zestawu nie uruchamiano. Testy rozróżniają
zatrzymanieQEMU, kontrolęPE32, błąd mapowania i rzeczywisty komplet CRT.
Niekompletny log lub zmieniony fixture są odrzucane.

Fixture `measured_crt_wave.json`,SHA256:
`fda96fcd9758c18c716b9f664737564145124ad131957029e7115dbf6d20ce8d`.
Wrapper Win32 SHA256:
`55e2c24d073831743423f534362f74a82cfa8cc59a6d74b0d71466d5c1f594b9`.
Logi finalne:[vm-owned-pages](../artifacts/queued-crt-context/vm-owned-pages)
i[vm-owned-repeat](../artifacts/queued-crt-context/vm-owned-repeat).
Audyt:[milestone](evidence/milestone-20261104-queued-crt-context.json).

## Powtarzanie i wznowienie

`tools/setup_mingw32_crt_probe.py` przygotowuje lokalny kompilator.
`bash tools/build_win32_crt_probe.sh` odtwarza wrapper i kontrole.
`tools/run_crt_vm.py --preparation artifacts/queued-crt-context/vm-preparation-owned-pages.json
--output artifacts/queued-crt-context/FRESH_RUN` uruchamia świeżego gościa;
launcher odmawia nadpisania wyników. Przygotowany initramfs i binarki są
w aktualnym środowisku. Nie uruchamiać PE32 bezpośrednio przez hostowe Wine
jako zamiennika tej bramki. `tools/validate_crt_context.py` kontroluje wyniki.

73C#/131meta/275plikówprojektu/78Resources/10stagingów/9oryginałów oraz DLL
fa19e56ad2ee9d6902f89e7b5e423cad9d2f215e35182269727e4ae12ee9b235 bez zmian.
Nie wykonywano nowego builda Unity,playerQA lub pełnej gry. Regresja głównego
korpusu100/2 i zegara pozostaje w poprzednim punkcie;ten etap nie jest portem C#.
1920×1080,16:9,ExclusiveFullScreen dla remake’u zachowane. Bez PNG/ZIP/podglądów.
Nie dowodzi to oprawy2026,natywnegoWindows11,docelowego laptopa lub wydajności.

Następnie:port reprezentacji punktów i członków100/2 do istniejącego właściciela
zadań,z jawnym kontekstem word[-1] i porównaniem korpusów55+5+4. Zachować
310LIFO,dodatkowy pass okresowy,czas/pocztę i pojedynczą własność stanu.
UI Shift odblokować dopiero po integracji;nie dokładać globalnej fazy grup.
Edycja składu,300/311,raport40,pełnyLife/AI/Start pozostają osobnymi bramkami.
Nie publikowano ani nie aplikowano konfiguracji;nie używano nowych agentów.
