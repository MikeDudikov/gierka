# Start scenario — następny ekran i zakres możliwego odtworzenia

Stan: 2026-11-02. Analiza read-only tego samego `ancient.exe`, SHA-256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
VA odnoszą się do obrazu PE o bazie `0x400000`. Nie uruchomiono oryginalnej
aplikacji; poniżej rozróżniono zasoby/kod i brakujące potwierdzenie runtime.

**Wniosek: Start scenario prowadzi do briefingu pierwszej misji, a nie do
potwierdzonej listy 14 scenariuszy.** Materiały pozwalają odtworzyć statyczny
pierwszy briefing i istotną część jego kontrolek. Kompletnego działania
„Start” i audio jeszcze nie potwierdzono. Późniejsza analiza potwierdziła
rysowanie całego tekstu: patrz BRIEFING_TEXT_EVIDENCE.md.
Nie należy tworzyć fikcyjnej listy wyboru misji ani podłączać przycisku do
wymyślonej rozgrywki.

## Potwierdzone przejście

1. Główne menu, handler `0x531030`, click `0x168`: wywołania `0x53d1b0`,
   `StartSystem::SetMode` (`0x53c8b0`) z argumentem 0 i `0x537ef0(app,0,0)`.
   Setter zapisuje `StartSystem+0x1a1=0`, `app+0xd7c=1`.
2. `0x537ef0` sprawdza tryb/nośnik, konstruuje nazwę `MISSIONS/miss%d%02d`;
   argumenty 0,0 wybierają **miss000**. Ładuje kontener i uruchamia
   `TuneGamePtr` (`0x4ed700`). `0x4ece90` wczytuje z niego `DISCRIPTION`
   do `app+0x19e1`. Ustawia również `app+0x3215=0` i flagi strony gracza.
3. Zwykła gałąź wysyła wiadomość App `0x10c`; przy `DAT_005ca53c & 2`
   i indeksie misji 0 istnieje odrębna ścieżka `0x128` o parametrach 5,0
   (prezentacja filmowa wymaga dalszego prześledzenia).
4. App `GetMessage` (`0x4ec1a0`) przygotowuje system startowy i przekazuje
   `0x10c`. `StartSystemTy::GetMessage` (`0x53e170`), case `0x10c`, tworzy
   **MTaskSystemTy** (`0x53ecd0`), wczytuje dane (`0x53ee80`), tworzy obiekty,
   aktywuje dziecko i ustawia `StartSystem+0x20=11`.

To konkretne powiązanie danych i ekranu, nie tylko podobieństwo nazw.

## Zasoby pierwszego briefingu

`MTaskSystemTy::LoadData`, `0x53ee80`, szuka kontenera `VIDEO/TASKS.DKD`.
Według flagi strony i numeru misji próbuje `VOICE%d%02d` (typ 2),
`FON%d%02d` (typ 2) oraz `BKG%d%02d` (typ 1), z fallbackami `FON000`
i `BKG000`. Na tej płycie TASKS zawiera **tylko typ 2 `FON000`**:
DKD offset36, zachowane bajty i SHA w
`artifacts/binary-analysis/scenario-menu/tasks-resource-inventory.json`.
Brak VOICE/BKG w tym kontenerze jest wynikiem jego pełnego indeksu,
a nie awarii dekodowania.

Gdy nie ma obrazu BKG, kod bierze `StartSystem+0x7c`, czyli **`0M_BKGND_05`**
z `installed/missions/controlm`. To obraz 800×600 z wbudowanym nagłówkiem
„YOUR MISSION”, rynsztunkiem wojownika i dolnym ornamentem. Został odczytany
i obejrzany; plik `briefing-fallback-background.png` oraz manifest pochodzenia
są w `artifacts/binary-analysis/scenario-menu/`. Prefiks 0 jest jawnie wybraną
badaną ścieżką zasobów; warunek wyboru 0/3 nadal wymaga pełnego potwierdzenia.

Tekst pochodzi z rekordu **typ 23 `DISCRIPTION`** konkretnej misji, nie z
PE RT_STRING. Wczytanie tego rekordu przez `0x4ece90` oraz przekazanie
`app+0x19e1` do formatowania w `0x53ee80` są potwierdzone. Rekord zawiera
nagłówek i kodowanie tekstu z NUL/@, nie jest po prostu plikiem UTF-8.
Nagłówek24bajty, bitmapaMSB, znacznikiNUL/@ oraz formatter i metryki zostały
później rozpoznane i porównane z wykonanym x86 dla miss000:
[BRIEFING_TEXT_EVIDENCE.md](BRIEFING_TEXT_EVIDENCE.md). Surowe bajty nie są UI.

Odzyskane, zdekompresowane rekordy 14 misji oraz SHA i źródłowe offsety
zapisano w `scenario-menu/mission-description-resources.json` i oddzielnych
`missNNN-description.bin`. Poniższe tytuły występują w ich oznaczonych
łańcuchach (zachowano pisownię oryginału):

| Plik misji | Odczytany tytuł |
| --- | --- |
| miss000 | Lemnius's Parchment |
| miss001 | The Magic Oar |
| miss002 | Argus's Hammer |
| miss003 | The Journey begins |
| miss004 | Perseus and Athena's Mirror Shield |
| miss005 | Odysseus |
| miss006 | Orpheus and Zetes |
| miss007 | Atalanta and Hercules |
| miss008 | Propontis |
| miss009 | Wizard of Fire |
| miss010 | Golden Fleece |
| miss011 | Expansion |
| miss012 | Euxine |
| miss013 | The Last Battle |

Obecność tych 14 rekordów nie dowodzi, że oryginał oferuje wybór wszystkich
na jednym ekranie. Końcowe spacje/przecinki/znaczniki zachowują pliki dowodowe;
tabela jest czytelnym zestawieniem nazw.

## Geometria i kontrolki — oryginalne 800×600

`MTaskSystemTy` constructor `0x53ecd0`, create `0x53f2f0`, handler
`0x53f4e0` oraz odczytane RT_STRING potwierdzają:

| Element | Pozycja / obszar | Treść lub zasób |
| --- | --- | --- |
| Tło | 0,0,800,600 | fallback `0M_BKGND_05` |
| Tekst zadania | x20,y80,w630,h440 | `DISCRIPTION`, font `S_FNT_MH` |
| Nagłówek trudności | x660,y405 | RT_STRING105 `Difficulty level:`, `S_FNT_BH` |
| Trzy kontrolki radio | x660,y440/470/500 | zasób `M_CHECK`; etykiety x690 |
| Poziomy | jak wyżej | RT_STRING106 `Easy`,107 `Normal`,108 `Hard` |
| Start pierwszej misji | x244,y543 | RT_STRING1010 `Start`, descriptor `M_BUT2_` |
| Cancel pierwszej misji | x440,y543 | RT_STRING1002 `Cancel`, descriptor `M_BUT3_` |

Dla misji o indeksie innym niż 0 Start przesuwa się do x335 i Cancel nie
jest tworzony w tej gałęzi. Stan początkowy pochodzi z `DAT_005ca78d`; inicjalizacja nowego profilu daje
Easy0, a zwykłe ponowne otwarcie miss000 zachowuje wybór. Pełny indeks miss000
nie ma rekordu DIFFICULTY, więc setter go nie nadpisuje. Dowody i558porównań:
[BRIEFING_CONTROLS_EVIDENCE.md](BRIEFING_CONTROLS_EVIDENCE.md).
Geometria 800×600 jest referencją układu; projektowy canvas/remaster wymaga
własnej adaptacji bez rozciągania kształtów zasobów.

Handler rysowania `0x53f4e0`, message5, rysuje tło, tekst poprzez `0x4eb2f0`
i nagłówek trudności. Radio wysyła `0x210` i ustawia globalny poziom na
`wybór−1`. Paint radio `0x20f` wybiera etykietę106..108 oraz wariant fontu
zależny od zaznaczenia. Rzeczywisty wrapper to TabClassTy factory5/0x550ba0, nie RadioClass. Wybór
następuje na lewy down wewnątrz półotwartego prostokąta ikony23×23; etykieta,
hover i release nie wybierają. M_CHECK0/font1 jest niezaznaczony,
M_CHECK1/font2 zaznaczony. Wcześniejsze przypisanie T_PLAYER6 było błędne.

## Start/Cancel i braki do pełnego UI

- **Cancel `0x16e`:** zwalnia dane briefingu przez `0x53edc0`, wysyła
  App `0x100`, który prowadzi do ekranu startowego. Paint `0x16f` wiąże
  napis RT_STRING1002.
- **Start `0x178`:** zwalnia dane; wykonuje warunkową ścieżkę zapisu/progresji
  `0x53a330` z polami `app+0x32fd/+0x3305`, potem wysyła App `0x101`.
  App `0x101` przechodzi do `AncientAppTy::StartGame` (`0x4ebf50`), tworząc
  `GameSystemTy`. Paint `0x179` wiąże napis1010.
- PaintSarr rysuje cały sformatowany tekst. W MTaskLife nie znaleziono
  mutowania tekstu;3000/20000ms dotyczą stanów audio/VOICE i nie są dowodem
  efektu typewriter. Audio nadal wymaga pełnego odtworzenia i odsłuchu.
- Nie ma jeszcze zgodnej symulacji świata, pełnego parsera DESCRIPTOR,
  obiektów misji lub warunków zwycięstwa. Przejście Start→fikcyjna scena
  nie byłoby zgodnym odtworzeniem tej ścieżki.

**Wykonalny kolejny mały etap:** parser rekordu DISCRIPTION i statyczna
rekonstrukcja briefingu miss000 z oryginalnym tłem, fontem oraz trudnością;
porównać układ i metryki z kodem/zasobami, a następnie dodać zweryfikowany
Cancel→menu. Pełnego briefingu z audio/czasem i Start→rozgrywka nie należy
jeszcze oznaczać jako gotowego. Analiza scenariusza nie zmieniła Unity ani danych źródłowych.

Eksporty funkcji i ich xrefy: `artifacts/binary-analysis/scenario-menu/export/`.
Wszystkie narzędzia działały na istniejącym projekcie Ghidra readOnly.

Aktualna implementacja pierwszego statycznego briefingu i staging:
[BRIEFING_IMPLEMENTATION.md](BRIEFING_IMPLEMENTATION.md). Start pozostaje
nieaktywny do czasu gotowej symulacji; Cancel i trudność mają osobną walidację
runtime. Nie jest to jeszcze pełny StartGame ani wszystkie misje.
