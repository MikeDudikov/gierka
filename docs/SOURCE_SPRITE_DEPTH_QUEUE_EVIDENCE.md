# Źródłowa kolejka głębokości przy zmianie pozycji

`SourceSpriteDepthQueue` przenosi kolejność świeżych, zwykłych węzłów
SpriteEngine. **3849 operacji rzeczywistego C# zgadza się z całymi oryginalnymi
procedurami x86**: 250 rejestracji i3599 zmian głębokości, w14 ciągach.
Kompilacja z `/checked+`,14 kontroli API i3 testy przeszły. To kolejka
identyfikatorów węzłów; nie jest rendererem ani pełnym cyklem świata.

- [Czysty C#](../Unity/AncientConquest/Assets/AncientConquest/Runtime/SourceSpriteDepthQueue.cs).
- [Walidator i niezależny oracle](../tools/validate_source_sprite_depth_queue.py),
  [probe C#](../tests/fixtures/SourceSpriteDepthQueueProbe.cs),
  [testy](../tests/test_source_sprite_depth_queue.py).
- [Przypięty fixture native](../tests/fixtures/source_sprite_depth_queue.json),
  1163486 bajtów, SHA256
  `9be3038d93fc54330f509c5652293bd52e6f716800f667bd4dcd0bb186d8593b`.
- [Końcowy raport](../artifacts/long-routes/depth/csharp-validation-frozen.json),
  [wynik testów](../artifacts/long-routes/depth/unittest-final.log).
- [Natywna mapa21 ID i przykładowa historia remisów](../artifacts/long-routes/depth/source-cohort-registration.json).

## Kod oryginału i zakres

Oracle wykonuje całe `0x55d670` (rejestracja), `0x55d960` (zmiana depth)
i rzeczywiste `0x571eb0`, bez hooków. Pamięć na64 świeże rekordy i ich
indeksy jest jawnie przygotowana; największy ciąg wykorzystuje63 rekordy,
więc nie wymaga oryginalnego realloc. Zawartość `ancient.exe` jest sprawdzana
SHA256 przed i po wykonaniu. Stary dowód
[UNIT_WORLD_ORDER_EVIDENCE.md](UNIT_WORLD_ORDER_EVIDENCE.md) niezależnie
potwierdził rysowanie od końca tablicy posortowanej rosnąco.

Każdy węzeł ma zachowane ID rejestracji (`+0x40`), signed depth (`+0x44`)
i aktualną pozycję w kolejce (`+0x48`). `UpdateDepth` odtwarza bezpośrednio
dwie pętle przesunięcia z `0x55d960`, z ich ścisłymi porównaniami sąsiadów.
Nie sortuje od nowa według ID lub resource name. Równy nowy depth nie
przestawia węzła. Zmniejszanie do depth poprzednika lub zwiększanie do
depth następnika również zachowuje dotychczasową stronę remisu.

Obsługiwane są świeże normalne węzły, bez callback bitu `0x4000`.
Pole warstwy wyliczane przez `0x571eb0` nie jest przenoszone; ten helper
wykonuje się w oracle, ale nie zmienia badanej kolejności. Usuwanie,
ponowne wykorzystanie slotów, callbacki, pełne zasoby i piksele nie są
objęte tym adapterem. Rejestracja z ujemnym początkowym depth zachowuje
`int.MaxValue`, dokładnie jak `0x55d670`; późniejszy `UpdateDepth` przyjmuje
cały zakres signed int32. Odrzucenie błędnych ID w C# jest defensywnym
kontraktem adaptera, nie deklaracją identycznych wyjątków starego C++.

## Dlaczego dłuższy ruch wymaga historii

Dla źródłowego0b, wysokości56 i stanu grafiki1:

```text
depth = max(10000, 20000 - 56 - publishedWorldY)
```

Depth statku0d wynosi19676, a0c19620. Zatem poruszający się0b osiąga remisy
odpowiednio przyY268 iY324. Samo Y nie określa wtedy kolejności: istotna
jest kolejność wcześniejszych publikacji.

| Historia Y0b | Depth0b | Dodatnie grupy w kolejności rysowania |
| --- | --- | --- |
| 267→268 | 19676 | 0b,0d,0c |
| 267→268→269→268 | 19676 | 0d,0b,0c |
| 323→324 | 19620 | 0d,0b,0c |
| 323→324→325→324 | 19620 | 0d,0c,0b |

To wyniki oryginalnego SetDepth, bez hooków. Powtórzona publikacja przy tym
samym Y pozostawia kolejkę. Należy przekazać **każde** źródłowe SetDepth
w kolejności, również gdy jeden call ruchu publikuje dwie pozy albo dwa
razy tę samą pozycję. Pojedynczy stan końcowy calla może utracić tę historię.

## Rejestracja znanego zbioru

Mapa pochodzi z przypiętego
[mission_ship_world_order.json](../tests/fixtures/mission_ship_world_order.json),
SHA256 `0ee61b970675c19a0cdfc021ba223752d6694721074cbba0c900dd428f2be0c6`.
Zachowuje potwierdzoną enumerację OBJ i rodzica przed jego osobnym cieniem.
Natywna rejestracja potwierdza pierwotną kolejność tego samego21-węzłowego
zbioru. ID węzła nie jest numerem SpriteRenderer w spłaszczonej kolejce34.

| ID | OBJ | Rodzaj | Początkowy depth |
| --- | --- | --- | --- |
| 0 | 05 | rafa | 20200 |
| 1 | 06 | rafa | 20200 |
| 2 | 09 | rafa | 20200 |
| 3 | 0a | rafa | 20200 |
| 4 | 0b | dodatni rodzic | 19812 |
| 5 | 0b | osobny cień | 21000 |
| 6 | 0c | dodatni rodzic | 19620 |
| 7 | 0c | osobny cień | 21000 |
| 8 | 0d | dodatni rodzic | 19676 |
| 9 | 0d | osobny cień | 21000 |
| 10 | 10 | dodatni rodzic | 18784 |
| 11 | 10 | osobny cień | 21000 |
| 12 | 21 | rafa | 20200 |
| 13 | 27 | dodatni rodzic | 18588 |
| 14 | 27 | osobny cień | 21000 |
| 15 | 28 | dodatni rodzic | 18524 |
| 16 | 28 | osobny cień | 21000 |
| 17 | 29 | dodatni rodzic | 19100 |
| 18 | 29 | osobny cień | 21000 |
| 19 | 2a | dodatni rodzic | 19036 |
| 20 | 2a | osobny cień | 21000 |

Zmiana depth0b przestawia jego dodatnią grupę względem innych grup.
Nie zmienia rejestracji cienia ani nie sortuje dodatnich składników osobno
w świecie. Każda grupa zachowuje swój potwierdzony lokalny porządek TYPE8:
[UNIT_ANIMATION_ASSET_EVIDENCE.md](UNIT_ANIMATION_ASSET_EVIDENCE.md).
Pełny zbiór nadal zawiera8 cieni,5 raf i21 dodatnich składników statków,
razem34 renderery. Pozostałe klasy, mgła, UI i warstwy świata pozostają poza
zakresem dowodu.

## API i powtarzanie

Namespace `AncientConquest.World`, publiczny typ `SourceSpriteDepthQueue`:

```csharp
var queue = new SourceSpriteDepthQueue();
int id = queue.Register(initialDepth);
queue.UpdateDepth(id, newDepth);
for (int index = 0; index < queue.Count; ++index)
    RenderGroup(queue.GetDrawNode(index)); // od tyłu do przodu, bez alokacji
```

`GetDepth(id)` odczytuje depth. `CopyAscendingOrder()` i `CopyDrawOrder()`
zwracają niezależne kopie do kontroli; `GetDrawNode(index)` nie alokuje.
W probe każdy poprawny indeks getterów porównano z native w3849 stanach.
Czternaście kontroli obejmuje pustą kolejkę, granice ID/indeksów, izolację
kopii i zachowanie stanu po błędnym wywołaniu.

Niezależne QA może użyć:

```python
from tools.validate_source_sprite_depth_queue import original_cohort_trace
trace = original_cohort_trace(all_published_world_ys)
```

Wynik ma `registration` z ID/resource/kind/depth, `initial_draw_order`
oraz `states[{world_y, depth, draw_order}]`. Przekazane Y muszą pochodzić
z pełnej historii publikacji źródłowego ruchu; tabela przyjmuje0…1535.
Sama obecność funkcji i testów nie potwierdza nowej integracji Unity.
Końcowy obraz i odczyty właściwości rendererów wymagają osobnego buildu/QA.
