# Źródłowe pole fali planera

Stan: 2026-11-02. `SourceWaveField.Fill` przenosi gałąź oryginalnego
`0x5578a0`, którą wywołuje `0x55c9a0` po nieudanym sprawdzeniu bezpośredniej
trasy. Nie zastępuje jej standardowym BFS, Dijkstrą ani A*. Dotyczy wyłącznie
pełnej mapy16-bitowej, wartości0/wolne i−1/zablokowane, z parametrami
`maxSteps=2*(width+height)`, `preferredHeading=-1`, `alternate=0`, `remaining=0`.
Nie jest to pełna implementacja wszystkich kombinacji argumentów5578a0.

## API i kierunek

```csharp
int SourceWaveField.Fill(short[] field, int width, int height,
                         int seedX, int seedY, int targetX, int targetY)
```

Metoda **modyfikuje** przekazane pole. `55c9a0` przekazuje jako seed cel
podróży, a jako target komórkę początkową statku; fala biegnie więc odwrotnie
niż późniejsza trasa. Wartość zwracana jest źródłowym licznikiem iteracji,
nie bool ani liczbą waypointów. Rozstrzygnięcie dostępności ścieżki wymaga
również odczytu etykiety komórki początkowej przez caller55c9a0.

Mapy C# są ograniczone defensywnie do szerokości/wysokości1…256, zgodnej
liczby komórek i poprawnych, wolnych endpointów. Nieobsługiwane ważone
etykiety są odrzucane przed mutacją wejścia. To ochronny kontrakt adaptera,
a nie odtworzenie natywnej reakcji na nieprawidłowe wskaźniki.

## Zachowane reguły

Źródło przechowuje segmenty frontu w16-bajtowych rekordach: kierunek,
metadane, długość, minimalny koszt segmentu i punkt początkowy. `571700`
wstawia nowe rekordy stabilnie według minimalnego kosztu; przy remisie
zachowuje dotychczasową kolejność. Przetwarzanie obejmuje dwa źródłowe
przebiegi segmentów z etykietami osiowymi+2 i przekątnymi+3. Kolejność
odkrywania i moment zatrzymania są częścią zachowania oryginału.

Kod C# zachowuje etykiety adresów i przepływ źródłowych bloków. Dodatkowe
etykiety flow obniżają skoki C do wspólnego zakresu, ponieważ C# nie pozwala
skakać do zagnieżdżonych zakresów. Wskaźniki zamieniono na indeksy słów
w zarządzanych tablicach. Nie jest wymagany tryb unsafe ani zmiana ustawień
projektu. W tym kontrakcie komórka0 po etykietowaniu nie wraca do0;
pozytywne koszty nie przepełniają16 bitów. Pojemność`cells+4` pokrywa zatem
wszystkie niepuste segmenty oraz cztery rekordy startowe. Eliminuje techniczną
potrzebę relokacji wskaźników, zachowując kolejność rekordów.

Nie modelowano błędu alokacji natywnej jako kodu−2; zarządzany brak pamięci
pozostaje wyjątkiem. Semantyka alokatora nie jest elementem dowodu pola.

## Dowód oryginalnego x86 i C#

Oryginalny `ancient.exe` jest chroniony SHA256:
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Oracle `tools/validate_source_wave_field.py` wykonuje całe5578a0 i571700.
Nie podmienia żadnego fragmentu algorytmu. Intercepty obejmują wyłącznie
wrappery malloc/realloc/free571200,5711e0,5576e0. W badanym zestawie
realloc nie został wywołany; nie twierdzimy, że przetestowano natywny wzrost
bufora. Obsługa standardowej relokacji jest dostępna w harnessie.

Wynik: **749/749 pól,390267/390267 komórek i749 liczników iteracji zgodnych**
z rzeczywistym C# skompilowanym z`/checked+ /warnaserror+`. Wewnętrzna
arytmetyka portu ma jawne unchecked zgodnie z x86. Osobno9 kontroli API.
Zestaw zawiera wszystkie128 układów wewnętrznych3×3 dla czterech skierowanych
par przeciwnych narożników, małe i jednowymiarowe mapy, deterministyczne
losowania do256×256 oraz30 przypadków na rzeczywistym wejściu GetWayNew.
Porównuje całe wynikowe pola bajt po bajcie, nie tylko osiągalność lub jedną
wybraną ścieżkę. Pierwszy niezależny etap280 losowych map także przeszedł;
raport zachowano jako historię, nie wliczono go do749.

Trwały fixture `tests/fixtures/source_wave_field.json` ma SHA256
`f08d21859e99b7637b6c9913ccc058276bd05731a59711dc1057a15551b842fe`.
`source_wave_native_map.bin` pochodzi z rzeczywistego wejścia
GetWayNew4a5740→55c9a0 dla0b(16,2)→(18,4), SHA256
`9fd5e1c1e5495186ec2872f85bcbd22a41ae476a8fa83aec8c36c0dbba5ae06b`.
Źródłowy zapis: `artifacts/long-routes/navigation/native-first.json`.
Samo użycie tej mapy nie oznacza pełnej rekonstrukcji inicjalizacji świata.

[Końcowe porównanie](../artifacts/navigation/long-route-wave/csharp-validation-optional-guard.json)
wiąże fixture, kod C#, probe i walidator przez SHA256.
[Dwa testy](../artifacts/navigation/long-route-wave/targeted-tests-optional-guard.txt)
obejmują natywne pola oraz odrzucenie zmienionego EXE przed wykonaniem.

## Odtwarzanie

```sh
.venv/bin/python tools/validate_source_wave_field.py --output artifacts/navigation/long-route-wave/<nowy-raport>.json
.venv/bin/python -m unittest tests.test_source_wave_field -v
```

Test wymaga oryginalnego EXE, Unicorn/pefile oraz istniejącego Mono/Roslyn.
Przy braku opcjonalnych prerequisites unittest zgłasza pominięcie; bieżący
wynik został uzyskany bez pominięć. Dodatkowy systemowyPython bez opcjonalnego pefile pomija
wykonanie, ale odrzuca zmieniony EXE przed kontrolą tych zależności.
Pierwsze niepowodzenie tej kolejności guardów zachowano w
`artifacts/long-routes/navigation/system-python-optional-tests.log`; poprawiono
wyłącznie kolejność walidacji Pythona, bez zmian C# i fixture. Ten dowód nie uruchamia Unity, Wine,
renderera, AI, ruchu statku ani całego oryginału. Nie generuje podglądów i ZIP.

## Rozszerzenie dla55b9e0

Nowy `FillFromOrigin` przenosi forward-wave z preferencją pierwszego sąsiada;
nie zmienia istniejącego Fill ani Calculate. Cel i seed mogą początkowo być
zablokowane,jak w źródłowej gałęzi55b9e0. Dokładne warunki,1380 nowych
porównań całego częściowego planera i749-przypadkowa regresja starej fali:
[dowód planera częściowego](SOURCE_NEAREST_PATHFINDER_EVIDENCE.md).
