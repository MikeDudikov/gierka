# Źródłowy planer pól 55c9a0

Stan: 2026-11-02. `SourcePathfinder` przenosi algorytm z oryginalnego
`ancient.exe` SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Nie używa NavMesh ani zastępczego A*. Wejściem jest krótka mapa0/wolne,
−1/zablokowane, z osobnym adapterem świata statków.

## Warstwy oryginału

1. `55c9a0` sprawdza granice i oba końce. Zajęte pole w tej warstwie oznacza
   niezerową wartość mapy, nie bezpośrednio referencję obiektu.
2. `571880` próbuje dwóch odcinków w dwóch dopuszczalnych kolejnościach.
   Kierunki dobiera ze stosunku bezwzględnych różnic X/Y oraz preferencji
   obrotu. Nie stosuje klasycznej linii Bresenhama. Remis preferencji nie
   zamienia pierwszego kierunku. Sprawdza tylko pola odcinka, bez osobnego
   zakazu przecinania narożników.
3. Jeśli obie próby zawiodą, `5578a0` wypełnia mapę odwrotną falą od celu.
   Przeniesiony scanline/frontier i stabilne wstawianie `571700` opisano w
   [dowodzie fali](SOURCE_WAVE_FIELD_EVIDENCE.md).
4. Rekonstrukcja `55c9a0` sprawdza najpierw sąsiadów nieparzystych1/3/5/7,
   potem parzystych0/2/4/6. Ma źródłowe reguły remisów oraz natychmiastowego
   przejścia do sąsiedniego celu. Preferencja dotyczy poprzedniego kierunku.
   Wybrane ścieżki są porównywane bajt w bajt, nie tylko długością.

Rekord ma5 bajtów:int16X,int16Y,heading. Od rekordu1 heading opisuje odcinek
**dochodzący** z poprzedniego punktu. Rekord0 w ścieżce fali ma literalnie0;
nie wolno użyć go jako początkowej orientacji statku. Dla ścieżki bez fali
rekord0 duplikuje pierwszy kierunek. Przypadek origin=goal zwraca dwa takie
same punkty z przekazanym heading; wyższy adapter statku nie instaluje go
jako ruchu.

## C# i własność

`SourcePathfinder.Find` kopiuje wejściowe pole. `Result` udostępnia liczbę
punktów,UsedWave,WaveIterations oraz kopie punktów i pola roboczego. Nie
zmienia trwałej siatki świata. Limity API:1…128 komórek na oś, zgodny rozmiar
pola, wartości0/−1 i preferredHeading−1…7. Poza tym zakresem zgłasza błąd.
Poza mapą lub przy zablokowanym końcu zwraca brak ścieżki. Te kontrolowane
błędy API nie odtwarzają niezdefiniowanych odczytów pamięci źródła.

`SourceWaveField` zachowuje źródłowy porządek segmentów; nie zastępuje go
prostym BFS/Dijkstra. Nie modelujemy niedostępności pamięci oryginalnego
alokatora. Zmienny koszt dodatni,warstwy shore i inne wartości wejściowej
mapy pozostają poza tym API.

## Wykonana walidacja

`tools/validate_source_pathfinder.py` uruchamia oryginalne `55c9a0`,
`571880`, `5578a0` i `571700`. Żaden algorytm nie jest hookowany. Hooki
obejmują wyłącznie alokację,realokację i zwolnienie:557700/571200/5711e0/5576e0.
Oryginalny EXE i źródłowe dane misji są hash-guarded. Flagi rzeczywistej mapy
mają przypięty SHA `eb8c22b2dc3a3d6de5be5c5a28560701333cbc8610e8dd687052f4f93b260283`.

**374/374 przypadki C#/x86 PASS**, w tym234 bez fali/wczesne powroty i140
z falą. Porównano pełne rekordy wszystkich ścieżek oraz każdą16-bitową
komórkę pola roboczego. Są otwarte mapy1×1…12×12, różne preferencje,
250 deterministycznych map losowych do24×24, rzeczywista mapa misji z lokalną
przeszkodą oraz zablokowane końce. C# kompilowano z `/checked+`.
Sześć kontroli API i własność kopii również przeszły.

Trwały fixture `tests/fixtures/source_pathfinder.json`, SHA256
`1cca921bcb53f2398d708c3f117ea0370369d32d6a8dc2ad57f4b9ea5998a4d2`.
Dwa testy `tests/test_source_pathfinder.py` obejmują rzeczywiste porównanie
oraz odrzucenie zmienionego fixture przed wykonaniem źródła.
Raport: [końcowe porównanie](../artifacts/long-routes/navigation/pathfinder-csharp-validation-final.json).
Wyniki pierwszego porównania również zachowano.

Ten dowód nie potwierdza playera Unity,mechaniki omijania ruchomych statków,
pełnego Life,tempa gry,Windows11 ani wydajności laptopa. To element
przyszłej nawigacji; użycie w świecie opisuje [adapter statku](SHIP_ROUTE_PLANNER_EVIDENCE.md).
