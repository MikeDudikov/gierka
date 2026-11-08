# Ruch statku: potwierdzony odcinek referencyjny

`PreparedShipMovement` odtwarza jeden sprawdzony odcinek źródłowego statku
`OBJ_0000000b`: z `(16,2)` do `(15,3)`, przy kierunku5. Całe sześć śladów
oryginalnych instrukcji x86 zgadza się z rzeczywistym C# kompilowanym
z `/checked+`: **186/186 stanów, 180 wywołań MoveShip, 40 kontroli API**.
Jeden ślad obejmuje również oryginalne wyznaczenie sąsiedniej trasy.
Jest to jawny tryb referencyjny z wiatrem `(siła0,kierunek5)`, poziomem
ulepszenia0, pełnym zdrowiem i siedmioma nieruchomymi pozostałymi statkami.
Nie przypisujemy tych parametrów każdej nowej rozgrywce miss000.

Dowód i kod:

- [Raport x86/C#](../artifacts/movement/kinematics/prepared-movement-csharp-validation.json)
- [Wszystkie źródłowe stany i granice usług](../artifacts/movement/kinematics/prepared-path-kinematics.json)
- [Zamrożony fixture](../tests/fixtures/prepared_ship_movement.json), SHA-256
  `28931c2849e05f46c7fd005c0f7b923f1d19bf26c045148a1a2388191cf2d374`
- [Oryginalny oracle](../tools/probe_ship_kinematics.py),
  [walidator różnicowy](../tools/validate_prepared_ship_movement.py),
  [probe C#](../tests/fixtures/PreparedShipMovementProbe.cs),
  [testy](../tests/test_prepared_ship_movement.py)
- [PreparedShipMovement.cs](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/PreparedShipMovement.cs)

Oryginał pozostaje tylko do odczytu. Każdy oracle sprawdza SHA-256 EXE
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`
oraz obu plików miss000; dodatkowo pinujemy576 źródłowych flag komórek.
Do tego etapu nie uruchamiano Unity Editor, playera, Wine ani usług pulpitu.

## Rzeczywisty przepływ

`ShipClassTy::GetMessage`, wiadomość0, wywołuje `Life004dec40`.
Ta prowadzi do `004ab720` i `004ab930`; drugi dispatchuje
`ShipClassTy::MoveShip004a3f40`, gdy `ship+25d & 400` i `ship+25c==0`.
Adresy `004df0e0` i `004e0d00` dotyczą efektów statku, a nie przesunięcia kadłuba.
`004e7220` inicjuje wewnętrzne komendy; również nie jest krokiem kinematyki.

| Funkcja | Potwierdzona rola |
| --- | --- |
| `004a6330` | `ProcPostMove`: plan i instalacja trasy; osobna gałąź zatrzymania |
| `004a5740` | `GetWayNew`: przygotowanie mapy i wybór oryginalnej procedury trasy |
| `0055c9a0` | Rzeczywista procedura użyta dla sprawdzonego celu sąsiedniego |
| `004a3560` | `ShipsStateMove`: kontrola kierunku i rezerwacja następnego punktu |
| `004a3a70` | Zapytanie wejścia, rezerwacja cell+4, aktualizacja indeksów |
| `004a3f40` | Prędkość, reszta całkowita, piksele świata, granica komórki i zatrzymanie |
| `004a2f60` | `SetAccDelayObj`: wyliczenie hamowania z prędkości i odległości |
| `004a3970` | Zwolnienie rezerwacji przez `004998a0`; dodatkowa obsługa statków połączonych poza zakresem |
| `004df6e0` | Publikacja klatki i głębokości renderowania po ruchu |

Eksporty tylko do odczytu znajdują się w
[export-life](../artifacts/movement/kinematics/export-life/004a3f40.c),
[export-core](../artifacts/movement/kinematics/export-core/004a3560.c),
[export-nav](../artifacts/movement/kinematics/export-nav/004a6330.c)
i [export-step](../artifacts/movement/kinematics/export-step/004a3f40.c).
Dekompilowane typy wskaźnika siatki bywają mylące: rzeczywisty rozmiar
rekordu wynosi24 bajty, co potwierdza oryginalny kod zapisu i poprzedni
[dowód zajętości](MISSION_OCCUPANCY_EVIDENCE.md).

## Trasa i współrzędne

Punkt trasy ma5 bajtów: `int16LE x`, `int16LE y`, `byte heading`.
Oryginalny `004a6330` dla `(15,3)` zwraca dokładnie:

```text
1000020005 0f00030005
(16,2,5)   (15,3,5)
```

Ustawia `path+5c2`, `count+5ba=2`, `index+5be=1`,
`lastCell+5b2=87`, `state+58c=3`, `centerGate+596=1`.
Oryginalny prefiks `0049a950..0049a9ce` tworzy mapy przejścia dla576
komórek bez hooków. Następnie wykonano cały osiągnięty planner
`004a6330→004a5740→0055c9a0`. Przechwycono jedynie normalny powrót
setjmp i alokację/zwalnianie pamięci. Trasy nie dostarczyła funkcja zastępcza.
Pięć dalszych śladów zaczyna się od tej samej jawnie przygotowanej trasy;
nie uruchamiają ponownie plannerów.

`ship+5a3/+5a7` przechowuje komórkę logiczną; sprite `+59/+5d` przechowuje
kotwicę w pikselach świata. Logiczny wymiar kadłuba0b to56×56:
początek `(1028,132)`, cel `(964,196)`. Komórka ma64×64 piksele.
Tabela `005c4f44`, stride5, zawiera wektory:
`(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1),(0,1),(1,1)`.
Ruch h5 używa więc `(-1,+1)`.

## Arytmetyka jednego wywołania

Konstruktor `004ac210` wykonuje oryginalne tablice i dla modelu0 daje
limit60000 i przyspieszenie1200. `004bece0` uwzględnia zdrowie oraz poziom
właściciela; w oracle wykonano go dla pełnego zdrowia i jawnego poziomu0.
`MoveShip` pobiera liczbę pending ze wskaźnika `ship+0c→+e2`.
Znacznik animacji bierze osobno z `ship+70→+de`; powiązanie tych wskaźników
opisuje [dowód zegara statku](SHIP_MOVEMENT_CLOCK_EVIDENCE.md).

W sprawdzonym stanie bez order3 mnożnik tabeli wiatru `00597b2c`
wynosi60%, co daje limit36000 i przyspieszenie720. Siła0 nie oznacza100%.
Oryginał zwiększa prędkość o `pending*acceleration`, ogranicza limit,
następnie oblicza:

```text
total = pending*speed + remainder
q = total / 3000
remainder = total % 3000
worldX -= q / 3
worldY += q / 3
remainder += (q % 3)*3000
```

Dzielenie jest całkowite, ze znakiem, w kierunku zera; arytmetyka x86
ma32-bitowe zawijanie. Reszta może być większa niż2999, ponieważ zachowuje
część niewystarczającą na cały piksel diagonalny. Docelowe X/Y są
ograniczane do dokładnej kotwicy. Nie ma płynnej interpolacji Unity.
Wywołanie z pending2 nie jest równoważne dwóm wywołaniom z pending1:
przyspieszenie i moment hamowania są obliczane raz na wywołanie.

## Rezerwacja i przekroczenie komórki

`00499aa0` sprawdza flagi i zajętość celu, dopuszczając tego samego ownera.
Nieparzysty kierunek dodatkowo sprawdza dwie komórki boczne i szczególne
przypadki połączonych statków. W tej trasie komórki `(16,3)` i `(15,2)`
są puste. C# jawnie odrzuca ich inne obsadzenie zamiast zgadywać stan
sprzężenia statków. Pozostałe przypadki linked/state6 są poza zakresem.

Pierwszy krok przez `004a3560→004a3a70→00499830` rezerwuje cel87, zanim
zmienią się piksele. State przechodzi3→5, `reserved+5ab=87`, `next+5b6=87`.
Stara komórka64 nadal należy do tego samego ownera.
Do sprawdzenia przekroczenia granicy służy **środek sprite sprzed
aktualizacji pikseli**, `(oldWorld+28)/64`. Kiedy ten środek osiąga komórkę87,
oryginał zwalnia64, zmienia logiczne X/Y i `reserved=-1`, przechodzi do
hamowania4. Dopiero dojście do dokładnej kotwicy ustawia state0 i speed0.

| Pending na wywołanie | Rezerwacja87 | Zwolnienie64 | Dokładny cel i stop |
| --- | --- | --- | --- |
| 1 | 1 | 30 | 44 |
| 2 | 1 | 15 | 22 |
| 3 | 1 | 11 | 14 |
| 7 | 1 | 5 | 6 |

Dla pending1 pierwsza zmiana piksela następuje w wywołaniu5. Wywołanie29
kończy z `(994,166)`, state5 i dwiema zajętymi komórkami. Wywołanie30 daje
`(991,169)`, komórkę `(15,3)`, state4, speed21600, hamowanie−854 oraz
resztę1800. Następny krok dodatkowo skaluje hamowanie przez60%, zgodnie
z oryginalnymi instrukcjami. Wywołanie44 kończy na `(964,196)`, speed0,
reszcie7440 i state0.

Siatka zawiera8 właścicieli przed ruchem,9 zajętych pól podczas rezerwacji
i ponownie8 po oddaniu początku. To8 różnych referencji; ID0 nie jest
znacznikiem pustego pola. Siedmiu pozostałych właścicieli pozostaje na
źródłowych pozycjach. Są to minimalne statyczne obiekty potrzebne do
zajętości, nie siedem uruchomionych konstruktorów/AI pełnej symulacji.

Kontrola z obcym ownerem na celu po przygotowaniu trasy nie zapisuje
siatki i nie zmienia świata. W wywołaniu50, przy ścisłym unsigned
`counter-58d >49`, oryginał przechodzi3→0. Oracle kończy się na tej granicy;
dalsza losowa animacja idle nie jest częścią projekcji.

## API oraz granice walidacji

Konstruktor przyjmuje `MissionOccupancyGrid`, zachowaną referencję ownera
i źródłowy `MissionShipSeed`. Sprawdza cały wąski kontrakt0b, lokalne
flagi trasy i8 różnych ownerów na znanych pozycjach. Są to obronne zasady
adaptera; nie przypisujemy oryginałowi identycznych wyjątków C#.
`TryBeginAdjacentReferenceMove()` instaluje wyłącznie powyższą trasę.
`Step(pending,sourceCounter)` zwraca informację, czy osiągnięto oryginalny
ogon animacji. Wywołujący uruchamia wtedy `ShipFrameProgression`, także
w ostatnim kroku44. Dopiero `LastStepPublishesPose` pozwala opublikować
obliczoną klatkę i pozycję w rendererze. `Current` udostępnia stan fizyczny; po `IsStopped`
diagnoza zamraża go i nie wykonuje idle. Wyjątki po utracie ownera chronią
przed uwolnieniem cudzej komórki; nie stanowią portu reakcji całego świata
na dynamiczną kolizję.

Porównano wszystkie pola wszystkich186 stanów, w tym klatkę obliczoną
osobnym helperem, dokładne zajęte pola i ich liczbę. Hooki podczas ruchu
ograniczają się do normalnego setjmp, publikacji sprite, aktualizacji
widoczności i powiadomienia systemowego; pełny wykaz z argumentami jest
w fixture. Prędkość, hamowanie, zapytanie grid, rezerwacje i zwolnienia
wykonuje rzeczywisty x86. Osobny [dowód komendy ruchu](SHIP_ORDER_EVIDENCE.md)
dochodzi do aktywnego celu `(15,3)`, lecz nie połączono tych oracle w jedno
pełne wywołanie Life z wejściem użytkownika.

Osobno wykryto i zamknięto istotną różnicę między fazą animacji a obrazem.
`004a4d49` zwiększa `sprite+45`, lecz `004a4da9` publikuje sprite przez
`004df6e0→0050d5f0` dopiero po zmianie piksela. Oryginalny silnik ma osobny
rekord klatki do rysowania, `engineNode+c4`; jego zapis i użycie potwierdza
[oracle publikacji klatek](../tests/fixtures/ship_forward_publication.json).
Nie należy przerysowywać Unity po samym zwiększeniu fazy. W kanonicznym
śladzie po wywołaniach3 i4 przechowywana faza wynosi21, a opublikowana
klatka nadal20. Po wywołaniu6 wartości wynoszą22 i21.
`LastStepPublishesPose` sprawdzono przeciw **115 rzeczywistym publikacjom**
z sześciu świeżo wykonanych śladów x86, porównując flagę, ostatnią
opublikowaną klatkę i pozycję we wszystkich186 stanach C#.
Oryginalnego fixture nie zmieniano, aby dopasować implementację;
wykorzystano zapisane i ponownie zaobserwowane wywołania `0050d5f0`.
[Raport publikacji](../artifacts/movement/kinematics/pose-publication-validation.json)
zachowuje pełny ślad. Domyślne punkty0,1,5,29,30,44 mają zgodną fazę
i obraz, dlatego runtime dodaje punkt3 `animation-only` do obserwacji
tej różnicy.

Pełny pathfinding, inne cele i statki, obrót, zmiana trasy, połączenia,
AI, walka, pogoda w czasie i normalna gra pozostają osobnymi zadaniami.
Siła/kierunek pogody nowej misji zależą od seeda z cached timeGetTime,
jeśli nie ma `RND_INIT`; nie wyprowadzamy z tego jednego domyślnego wiatru.
Wykonanie C# nie dowodzi jeszcze integracji renderowania ani działania
playera w tym etapie. Kwant40 i render1920×1080 dobiera zewnętrzny tryb
referencyjny; nie zmieniają one wyników powyższej arytmetyki pending.
