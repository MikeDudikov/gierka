# Źródłowy planer celu częściowego i zasięgu 55b9e0

`SourceNearestPathfinder.Find` przenosi oryginalną funkcję55b9e0 na mapie
0/wolne,−1/zablokowane. Zachowuje surowe5-bajtowe rekordy, osobny znacznik
`ReachedWithinRange` i pełne pole robocze. Nie jest konwencjonalnym wyborem
najbliższego wolnego pola i nie definiuje samodzielnie polityki rozkazu statku.
Oryginalne zachowanie pochodzi z `ancient.exe` SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.

## API i znaczenie wyniku

```csharp
SourceNearestPathfinder.Result Find(short[] initialField, int width, int height,
    int originX, int originY, int requestedX, int requestedY,
    int range = 0, int preferredHeading = 0)
```

API kopiuje wejście. Wynik udostępnia PointCount,Succeeded,
ReachedWithinRange,UsedWave,WaveIterations oraz kopie rekordów i pola.
`Succeeded` oznacza niepusty surowy bufor źródła. **Nie** gwarantuje ruchu,
osiągnięcia żądanego punktu ani prawa do instalacji trasy w klasie statku.
Dwa rekordy mogą opisywać tę samą komórkę początkową i źródłowe różne
headingi. Wyższy caller musi zachować własne reguły obsługi tego przypadku.

Ograniczenia:mapa1…128 na oś,zgodna długość,initial0/−1,range0…256,
preferredHeading−1…7. Współrzędne poza mapą dają pusty wynik. Ochronne
błędy API nie odtwarzają niezdefiniowanych odczytów pamięci źródła.
Nie modelowano niedostępności pamięci alokatora.

## Kolejność źródła

1.55b9e0 próbuje571880 z możliwością zatrzymania w zasięgu.
571880 dobiera dwa kierunki i ich kolejność tak jak źródłowy planer pełny;
sprawdza zasięg przed następnym krokiem. Nie sprawdza osobno flagi startu.
2.Gdy próba zawiedzie,5578a0 wykonuje falę **od punktu początkowego** do
żądanej komórki. To kierunek przeciwny do fali55c9a0. Wykorzystuje preferred
heading i źródłową poprawkę pierwszego sąsiada. Cel może być zablokowany;
sam5578a0 nadpisuje komórkę seed wartością1 również dla zablokowanego startu.
3.Jeśli cel nie ma dodatniej etykiety **lub range>0**, źródło skanuje pierścienie.
Kolejność to PRAWA KOLUMNA→GÓRNY WIERSZ→LEWA KOLUMNA→DOLNY WIERSZ,
z powtórzonymi narożnikami i źródłowym warunkiem zakończenia przy promieniu3.
Dla pierwszych dwóch pierścieni w zasięgu wybiera mniejszą etykietę fali;
dalsze wybory uwzględniają metrykę odległości i koszt, z zachowaniem remisów.
4.Rekonstrukcja biegnie od wybranego endpointu do początku:nieparzyste
headingi1/3/5/7 przed parzystymi0/2/4/6,źródłowe remisy i odwrócenie kierunku
przez `(heading−4)&7`. Dopiero na końcu odwraca kolejność całych rekordów.
Heading rekordu0 w tej gałęzi jest0; pozostałe opisują odcinek dochodzący.
5.Znacznik osiągnięcia zasięgu jest osobnym wynikiem. Przy udanej próbie
bez fali wynosi1; po fali wynika z odległości wybranego endpointu od celu.

### Dwie różne metryki

5573d0 ma formułę `max(|dx|,|dy|)+floor(min(|dx|,|dy|)/2)`.
557410 jest identyczne **poza |dx|=|dy|=2**, kiedy zwraca2 zamiast3.
Próba571880 oraz końcowy znacznik po fali używają5573d0; zapisywanie
krótszej ścieżki bez fali używa557410. Nie wolno ich ujednolicić.

| Przypadek | Rekordy źródła | Reached | Fala |
| --- | --- | --- | --- |
| misja(16,2)→(18,2),range0 |(16,2,h0),(17,2,h0)|0|2 iteracje|
| ta sama para,range1 |te same dwa rekordy|1|brak|
| misja(16,2)→(16,5),range0 |(16,2,h0),(16,3,h6),(16,4,h6)|0|3 iteracje|
| ta sama para,range1 |(16,2,h6),(16,3,h6),(16,4,h6)|1|brak|
| otwarta(0,0)→(2,2),range2 |(0,0,h7),(0,0,h7)|1|brak|
| ta sama para z przeszkodą(1,1),range2 |(0,0,h0),(0,0,h4)|0|3 iteracje|

Ostatnie dwa przypadki pokazują, dlaczego wyników nie należy normalizować
do pustej ścieżki ani wyliczać znacznika z samej końcowej współrzędnej.

## Wspólna fala

Dodano wyłącznie nowy publiczny adapter `SourceWaveField.FillFromOrigin`.
Istniejące Fill i prywatny Calculate zachowały semantykę. Nowy adapter
przekazuje origin jako seed,nie wymaga wolnego celu,przenosi preferencję,
a wynikowe pole może zawierać−2 po źródłowym zmniejszeniu zablokowanego
preferowanego sąsiada−1. Ta korekta nie otwiera pola do przejścia.
Nie użyto istniejącego Fill z ustawieniami odwrotnej fali przez pomyłkę.
Stary SourcePathfinder również pozostał niezmieniony.

Po rozszerzeniu **749/749 dawnych pól,390267 komórek i9 kontroli API**
przeszło ponownie:[regresja starej fali](../artifacts/order-lifecycle/nearest/old-wave-749-regression-final.json).

## Walidacja nowego algorytmu

`tools/validate_source_nearest_pathfinder.py` wykonuje pełne55b9e0,571880,
5578a0,571700,5573d0 i557410 w oryginalnym x86. Nie podmienia algorytmów;
obserwacja55bc13 odczytuje wyłącznie EAX po powrocie z fali. Hooki usług
ograniczają się do malloc/realloc/free. EXE i dane misji są hash-guarded.

**1380/1380 porównań C#/x86 PASS**, w tym850 bez fali i530 z falą.
Porównano komplet5-bajtowych rekordów,PointCount,ReachedWithinRange,
UsedWave,każdą komórkę pola roboczego i rzeczywistą liczbę iteracji fali.
C# kompilowano z `/checked+ /warnaserror+`;9 kontroli API także przeszło.
Zestaw zawiera otwarte mapy z różnymi preferencjami i zasięgami,wszystkie512
układów przeszkód3×3 (również zablokowany start/cel),400 deterministycznych
map losowych,30 przypadków na oryginalnej mapie i6 przypadków metryk.

Trwały fixture `tests/fixtures/source_nearest_pathfinder.json`,SHA256
`d79d1c319a22176c209839ff7320fc5b83cb70d21b373459eaa1ed9fe2eb8f9a`.
[Końcowy raport](../artifacts/order-lifecycle/nearest/nearest-csharp-validation-owned-map.json)
wiąże kod,probe i fixture przez hashe. Pierwszy1380-przypadkowy raport oraz
odpowiadający mu fixture przed dodaniem obserwacji liczby iteracji zachowano.
[Dwa nowe testy i regresja dwóch starych](../artifacts/order-lifecycle/nearest/targeted-tests-owned-map.txt)
przeszły4/4 bez pominięć. SystemowyPython bez pefile poprawnie
pomija dwa wykonania natywne,ale przechodzi oba testy zmienionych danych.
To nie wynik głównego pełnego zestawu projektu,który wykonuje root.

```sh
.venv/bin/python tools/validate_source_nearest_pathfinder.py --output artifacts/order-lifecycle/nearest/<nowy-raport>.json
.venv/bin/python -m unittest tests.test_source_nearest_pathfinder tests.test_source_wave_field -v
```

Dowód dotyczy czystego planera pól. Nie uruchamia Unity,Wine,całego Life,
AI ani pełnego świata i nie dowodzi czasu gry lub wydajności laptopa.
Nie generowano podglądów,ZIP ani publikacji.
