# Zaznaczanie ramką — ograniczony etap 2026-11-03

W diagnostyce `--ship-pointer-reference` można teraz zaznaczyć ramką
sterowany statek0b. Kontur zachowuje źródłowe przerywane linie,32 fazy,
kolor palety201 i próg odświeżenia50ms. Widok nadal zajmuje cały ekran
1920×1080,16:9. **Pełna selekcja floty i pełna gra nie są ukończone.**

## Przeniesione zasady

- Przeciągnięcie staje się ramką dopiero po przekroczeniu progu na obu
  osiach:`abs(delta+1)>9`. Aktywacja tworzy zerowe wymiary; dopiero kolejny
  Move zapisuje podpisany rozmiar. Life publikuje kontur po upływie ponad49ms.
- Komórki początku i końca wyznaczają włącznie prostokąt wyboru. Zapytanie
  normalnych statków200…211 przechodzi komórki wierszami,porównuje
  `side*4+player`,pomija rezerwację ruchu i usuwa duplikaty przez tożsamość
  obiektu. Widoczny piksel kadłuba nie decyduje o wyborze ramką.
- Pusty prostokąt zachowuje poprzedni wybór. Prostokąt1×1 komórkę z kursorem
  rodzaju5/6 nie uruchamia ponownego zaznaczenia. Polityka źródłowa uwzględnia
  flagę Shift4; porównania obejmują też Ctrl8 i4|8.
- Wyboru ramką nie tłumaczy się na action41/20. Nie powstaje potwierdzenie
  rozkazu ani nowa grupa symulacji. Prawy przycisk podczas aktywnej ramki
  nie kończy jej i nie wydaje rozkazu SEA. Lewy Up kończy wybór.
- Wyjście z viewportu i anulowanie urządzenia zachowują ochronę przed
  przypadkowym rozkazem. Anulowanie nie wytwarza sztucznego Up.

## Zakres implementacji

`ShipBoxSelection` zbiera kandydatów ze wszystkich ośmiu referencyjnych
statków. Kod źródłowy zapytania/polityki/rasteryzacji wykonuje
[probe](../tools/probe_ship_box_selection.py),a niezależnie kompilowany C#
porównuje [validator](../tools/validate_ship_box_selection.py).
`ShipBoxGesture` przechowuje gest i zegar konturu;`ShipBoxOutline` odtwarza
wzory oraz kierunek i clipping oryginalnych linii.

Most `ShipPointerReference` stosuje wynik tylko dla pustego zbioru lub
samego0b. Wybór innych statków lub wielu statków jest jawnie blokowany
przed zmianą zaznaczenia (`unsupported-fleet-set`). Zapytanie przykładowej
większej ramki zwraca w kolejności źródłowej0b,0d,0c; nie jest to dowód
ukończenia sterowania taką flotą. Pozostałych siedem statków pozostaje
statycznych;NoFog,inne sloty puste,audio wyłączone.

Kontur jest dynamiczną siatką pasm pikseli,punktowo próbkowaną przez
materiał URP. Nie dodaje nowego atlasu ani dziewiątego stagingu. Ma
sortingOrder46; istniejący confirm dostaje47 tylko podczas ramki,kursor
pozostaje32767. Bufory siatki są ponownie używane;utworzone obiekty,
Mesh,Material i Texture2D są usuwane przy Dispose.

Źródło gestu to analiza normalnego map-view1 w`51cd60`. Nie emulowano
całego Map/RunApp,schedulera,scrollowania,fog ani wszystkich klas.
Kod zapytań `49c3f0/49c520/49c2f0`,polityka `517b90` i raster
`5195c0/56ff10/56ea10` mają osobne wykonywalne wzorce x86.

## Wyniki

| Sprawdzenie | Dowód |
| --- | --- |
| Zapytanie normalnych statków |1745 przypadków C#/x86; rzeczywisty wektor źródłowy i deduplikacja |
| Polityka pojedynczego0b |144 przypadki C#/x86:brak/pending/grupa,kursory0/5/6/7,flagi0/4/8/12,puste i niepuste ramki |
| Piksele konturu |1920 buforów8-bit C#/x86;7864320 porównań;32 fazy,dwie grubości,ujemne/zerowe wymiary i clipping |
| Węzeł konturu x86 |Konstruktor i zapis wymiarów nie publikują położenia; pierwsza publikacja ma fazę1;33 aktualizacje potwierdzają zawijanie32 |
| Kontrakt C# |25 kontroli zakresów,progu obu osi,zerowej aktywacji,50ms,zawijania uint i Cancel;checked+/warnaserror |
| Pełny discovery |234PASS,0 pominięć,254.424s; obejmuje2 nowe testy źródłowe |
| Osobne QA protokołu |2PASS,63.685s;7 odrzuconych mutacji stanu,członków,ramki,RNG,kolejki i komend |
| Końcowy player |30 etapów/33 zdarzenia/5 zakończonych ramek;pełne obrazy1920×1080 RGBmean/max0 |
| Próby obrazu |31 prób,30 przyjętych;1 odrzucona;61 PNG łącznie z30 obrazami wzorcowymi |
| Regresja myszy na tym samym DLL |25 kadrów/18 zdarzeń/126 wierszy motion;licznik0…101;RGB0;exit0 |
| Regresja menu na tym samym DLL |27 etapów/5 obrazów/6 komend;zwykły Quit0 |
| Build Windows x64 Mono |Unity6000.3.27f2;146986667B;0 błędów/0 ostrzeżeń |
| Integralność |62 C#/114 unikalnych meta;9 źródeł oryginału SHA-256 zgodnych;8 stagingów |

Finalny DLL:
`8ed5e4c2bfd5cc7780ab55426a66797e0c9631792e01bccfb5dfdfea2fe76fe1`.
C# nie zmieniono po końcowym buildzie. Rdzeń`ShipMoveOrder` pozostaje
zamrożony przy SHA-256`caa73d42265622175b3b9d44c4125972beae0d682c768d8ca263dbc1b9561cd9`.

Replay wysyła wyłącznie syntetyczne`InputSystem.QueueStateEvent`.
Zatrzymanie zegara i dwa impulsy diagnostyczne nie dowodzą pełnego tempa
rozgrywki. Dwa kroki bez rozkazu zachowują źródłowy idle/RNG i kolejkę
34 rendererów. Zaznaczenie jest porównane z wykonywanym`4e0d00`.
Wzorzec obrazu wykorzystuje oryginalny rasteryzator konturu i oryginalne
płaszczyzny grafik;nie ocenia jakości docelowej oprawy2026.

Nie zweryfikowano natywnego Windows11,myszy systemowej ani wydajności
na docelowym laptopie. Fokus pozostaje niezweryfikowany zgodnie z poprzednim
raportem;nie ponawiano tych samych pięciu prób. Zarejestrowane komunikaty
Wine dotyczą nieobsługiwanego ID3D11Fence/EnableMouseInPointer i audio
hosta;nie wprowadzono nowego wyjątku Unity. Normalny Start pozostaje wyłączony.

## Artefakty i wznowienie

- [Build](../artifacts/box-selection/build-report.json),[log](../artifacts/box-selection/windows-build-final.log),[testy](../artifacts/box-selection/full-tests-01.log).
- [Publikacja węzła](../artifacts/box-selection/native-node-publication.json).
- [Porównanie źródłowe](../artifacts/box-selection/csharp-guards.json),[QA](../artifacts/box-selection/qa-targeted-tests.log).
- [Player](../artifacts/box-selection/runtime-final/report.json),[regresje](../artifacts/box-selection/regressions.json),[audyt](../artifacts/box-selection/final-audit.json).
- [Milestone](evidence/milestone-20261103-box-selection.json).

```bash
.venv/bin/python -m tools.validate_ship_box_selection --output artifacts/<fresh>.json
.venv/bin/python -m unittest tests.test_ship_box_selection tests.test_smoke_ship_box -v
.venv/bin/python -m tools.smoke_ship_box --output artifacts/<fresh-directory>
```

Unity/Wine/Xvfb uruchamiać kolejno poza sandboxem IPC;display79 należy do
jednego własnego procesu QA. Nie budować podczas działania playera.
Pierwszy przebieg28-etapowy jest zachowany jako pilot i nie jest dodany do
końcowych30 etapów. Następnie rozwinąć wybór i oryginalne selektory
pozostałych statków,pełne grupy oraz zależne planowanie/zastępowanie ruchu.
Nie publikowano ani nie utworzono ZIP czy podglądu do prezentacji.
