# Shift i zadanie 100/2 — dowód x86, 2026-11-04

Ukończono zaplanowany etap dowodowy przed portem 100/2. Powstały dwa
niezależne od C# korpusy wykonywania oryginalnego kodu maszynowego.
Nie zmieniono kodu Unity, scen, danych ani ustawień; Shift nadal ma blokadę.
Znaleziono zależność od pamięci przed buforem fali, którą trzeba rozstrzygnąć
przed deklarowaniem pełnej zgodności portu.

## Przebieg źródłowy

| Adres | Potwierdzone działanie |
| --- | --- |
| 518070 → 49e230 → 49de70 | Shift ma bit4; rozkaz20 przechodzi do4cf2c0. |
| 4cf2c0 / 4cef80 | Pierwszy Shift usuwa inne zadanie, tworzy100/2 o rozmiarze101B i rejestruje trasę. |
| 4cf2c0, istniejące100/2 | Aktualizuje counter i nagłówek celu, zachowuje zadanie, trasę i group+8. |
| 4ce6c0 | Dopisuje punkt, pomija duplikat znaleziony gdziekolwiek w wektorze. |
| 4ce8a0 | Rejestruje aktora w osobnym wektorze; samo w sobie nie wysyła40. |
| 4ce7c0 | Wybiera poprzedni/następny punkt i flagę końca; signedchar±2 dopuszcza zawijanie. |
| 4a1700 | Buduje rzeczywiste32B zdarzenie310 z counter, ordinalem, ID i komórką. |
| 4cf0b0 / 4cf550 | Konsumuje zdarzenia od końca; po nich może wykonać również pass okresowy. |
| 4a1c60 / 4cef60 / 4ce5a0 | Usuwa zadanie, wektory i znaczniki; wiek grupy pozostaje. |

Pierwszy Shift w istniejącej grupie zastępuje100/1 przez100/2. Wysyła20
z pierwszym punktem każdemu statkowi, bez normalnej formacji100/1. Następny
Shift dopisuje punkt bez natychmiastowego20. Duplikat nie powiększa trasy,
lecz aktualizuje counter i nagłówek celu. Nagłówek nie jest więc niezależnym
poleceniem ruchu dla każdego członka.

Gdy wybór jest jeszcze tymczasowy, najpierw następuje źródłowe utworzenie
grupy i41, potem inicjalizacja100/2 i20. Nowa grupa zaczyna z wiekiem0;
istniejąca zachowuje wiek, także podczas zmiany typu zadania.

Przykład punktów A=(18,6), B=(16,4), C=(18,5):po A,B,A,C lista to A,B,C.
Dla mode1 przejście z C daje−1 i flagę końca1. Dla mode2 daje A i tę samą
flagę końca1. Dla mode−2 przejście z A zawija do C. Zwykłe kliknięcie usuwa
100/2 i wraca do100/1 ze źródłową formacją; nie dopisuje punktu do starej listy.

## Struktury i granice własności

| Offset/rozmiar | Reprezentacja w źródle |
| --- | --- |
| group+25 | Jeden wskaźnik zadania100/1 albo100/2. |
| task+0..18 | Siedem DWORD:100,2,counter,x,y,1,0 w tej ścieżce. |
| task+61 | Wskaźnik12B struktury trasy. |
| route+0 | Liczba zarejestrowanych członków. |
| route+4 | Wektor punktów12B: x,y,wskaźnik znacznika. |
| route+8 | Wektor członków17B: actorPtr,ID,signedbyteMode,targetX,targetY. |
| group+2d | Wektor32B zdarzeń;310 jest istotne dla przejścia do kolejnego punktu. |

Odwołania do statków są obserwowane przez rzeczywiste ID i ordinale rejestru.
Normalizowane są wyłącznie wskaźniki alokacji/znaczników. Nie powstał drugi
właściciel członkostwa, nowa siatka lub alternatywny zegar.

Praca grupy nadal należy do oryginalnego4c4f40 w jej miejscu rejestru świata.
Ten etap wykonuje sam moduł grupy z jawnymi wejściami komórek/stanu/counter/
pending; nie dowodzi nowej integracji100/2 z Begin/Complete, pocztą lub ShipLife.
`SingleStepClock`, `ShipWorldStep`, `ShipFleetMembership`, `MissionOccupancyGrid`
i wszystkie pozostałe klasy C# pozostają identyczne z poprzednim punktem.

## Efekty uboczne, których nie należy poprawiać

Zdarzenia310 są przetwarzane LIFO. W korpusie zdarzenia0b:A,0c:B,0d:C
powodują emisje najpierw0c→C, potem0b→B; ostatni punkt0d nie ma następcy.
Test pojedynczego obiektu4a0230 powoduje też różnicę:przy jednym członku
zdarzenie z komórką niezgodną z bieżącą jest pomijane. Przypadek trzech
członków nie przechodzi przez ten sam filtr i może wysłać następny punkt.

Pass okresowy sprawdza wiek>100 przed dodaniem pendingSteps. Obsłużenie310
nie musi go wyłączyć. Dla wieku101 i0b stojącego w A jeden Work wysyła0b→B,
a następnie okresowo0b→C oraz pozostałe rozkazy. Zapisany target członka0b
pozostaje B. Nie należy redukować tego do jednego rozkazu lub aktualizować
tego pola po każdej emisji. To konkretne pomiary źródła, nie proponowane reguły.

## Odczyt wave[-1] i CRT

4a1e90 alokuje dokładnie2*576=1152B pola fali. W4ceab0 warunek zakresu jest
alternatywą, nie koniunkcją; x86 przy4cebc7 wykonuje CMP z word[EAX+EDX*2]
także dla EDX=−1. Jest to odczyt dwóch bajtów przed przydzielonym buforem.

Oddzielny korpus wykonuje oryginalne instrukcje i kontroluje tylko te dwa
bajty jako syntetyczne wejście otoczenia. W5przypadkach po3porównania,
dla osobnych wejść UI i floty, otrzymano:

| Wejście sąsiedniej pamięci | Wynik trzech porównań | Okresowe pakiety20 |
| --- | --- | --- |
| Naturalne w izolowanym allocatorze:0 |0,0,0 |0b,0c,0d |
| Wymuszone0 lub5000 |0,0,0 |0b,0c,0d |
| Wymuszone32767 |1,1,1 |Brak |
| Wymuszone−32768 |0,0,0 |0b,0c,0d |

Rzeczywiste lewe argumenty CMP w tym teście to29994,29985,29991. Nie są to
zastępcze wyniki modelu Python. Odczyt iSETL wykonuje oryginalny x86.
Wymuszone wartości nie dowodzą ich osiągalności podczas gry.

557700 wywołuje oryginalny_malloc589bf5; obecny emulator izoluje backend CRT.
Statyczny obraz ma próg małych bloków1016 pod5c63b8. Przy tej wartości rozmiar
1152 kieruje589c33 do HeapAlloc przez import5941c0. Nie ustalono jeszcze
rzeczywistej wartości word[-1] dla oryginalnego procesu/sterowania CRT.
Nie wolno utożsamiać wyzerowanego sąsiedztwa w emulatorze z kontraktem Windows,
naprawiaćOR→AND albo ukryć tego odczytu w C# bez jawnego dowodu zgodności.

## Walidacja i ograniczenia

- Ghidra12.2, eksport65funkcji z C i assemblerem, readOnly/noanalysis,
  kontrolaSHA oryginalnego EXE i jawny marker zakończenia.
- Korpus główny:55scenariuszy/1112stanów; dwa osobne emulatory dla518070
  i49e230 dają2224porównywane obserwacje. W tej liczbie są również jawne
  ustawienia wejściowej pamięci, nie same wywołania funkcji.
-3394wywołania śledzonych funkcji w obu ścieżkach;209Shift,600zapytań trasy,
 101Work,11jawnych310 oraz519zserializowanych pakietów w kanonicznym śladzie.
- Wszystkie15uporządkowanych podzbiorów1..3statków, start100/1 lub bez
  zadania, duplikaty, usuwanie/ponowne tworzenie, granice wieku i unsignedwrap.
- Osobny korpus pamięci:5przypadków/15porównań,30obserwacji dla obu wejść.
-5testów PASS0skip105.083s oraz3testy granicy pamięci PASS0skip8.550s.
  Trzy izolowane mutacje instrukcji wykrywają błąd deduplikacji, zawijania
  i rozróżnienia pierwszego wysłania od dopisywania. Plik EXE nie jest zmieniany.
-312testów discovery;pełnego zestawu nie uruchamiano. Regresja zegara
  nadal potwierdza1287wejść. Nie wykonano nowej kompilacji Unity lub playerQA.
-73C#/131meta/275plikówAssets+Packages+ProjectSettings/78Resources/10stagingów/
 9wejść oryginału oraz DLLfa19e56ad2ee9d6902f89e7b5e423cad9d2f215e35182269727e4ae12ee9b235
  pozostają bez zmian. Ostatni build Windows152966699B0/0 jest historyczny,
  nie walidacją100/2 w playerze.1920×1080,16:9,ExclusiveFullScreen zachowane.

Tworzenie/usuwanie graficznych znaczników WPMOVE jest granicą usługową.
Oryginalny4ced10 nadal wyznacza pozycje x*64+14,y*64+18 na własnych obiektach
z niepodłączonym rendererem. Numeracja/bitmaski rzeczywistego konstruktora,
piksele i wiązanie zasobów Unity nie zostały zweryfikowane.
Nie wykonywano ActorWork, dostawy20/41, świata w40ms, zdarzeń300/311,
raportowania przerwania40, pełnegoCRT/App/ShipLife/AI lub OSinput.
Zdarzenia310 zostały skonstruowane przez prawdziwy4a1700, nie wpisane ręcznie.

Doprecyzowano wyłącznie metadane opisu liczby emulatorów/obserwacji;
SHA kanonicznych danych przypadków przed/po jest identyczny:
`e41345cd95470b1c28a50fe7c4570140e24dd09517ca18e228b3943b75a42a64`.
Zachowano przerwane próby korekty końcowej nowej linii w metadanych.
Ostateczne logi testów są osobne i kompletne. Nie poprawiano obserwacji,
aby dopasować je do implementacji. Nie generowanoPNG/podglądów/ZIP.

Fixture główne SHA256:
`8d0cab94992ccedce32b39d263923107b72bf2d5ecf9b56b9f0966ce7958913a`.
Fixture pamięci SHA256:
`307f39f575db59672a3232d8d66261b4b18b6d52d986c0adb54897ae88e9418b`.
Dowody:[artifacts/fleet-queued-evidence](../artifacts/fleet-queued-evidence).
Punkt kontrolny:[milestone](evidence/milestone-20261104-fleet-queued-evidence.json).

Następny krok:ustalić kontrakt sąsiedztwa pamięci dla oryginalnego CRT i
wywołań4ceab0, potem przenieść zweryfikowany100/2 do obecnego właściciela
zadań grupy. Zachować przypadki310+pass okresowy i granice czasu/poczty.
Blokada Shift, edycji składu i Start pozostaje do wykonania portu i porównań.
Pełny remake/oprawa2026/natywnyWindows11/laptop/performance nadal nieukończone
lub niebadane. Bez publikacji/aplikacji i nowych agentów.
