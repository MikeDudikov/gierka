# Źródłowe maski trafienia kursorem w statek

Stan:2026-11-03. Dodano i porównano z oryginałem czysty predykat trafienia
statku. **Nie jest to jeszcze zaznaczanie statku ani obsługa myszy w grze.**
Pełny światowy picker,kolejka zaznaczeń i przekazywanie kliknięć pozostają
osobnymi etapami. Docelowy obraz całej gry nadal1920×1080/16:9/fullscreen.

## Reguła źródłowa

Wirtualny predykat statku `0x4e06c0` przy niezerowym precision korzysta
z osobnych1-bitowych masek type18. To inne dane niż alfa widocznych części
sprite'a. Pozycja pochodzi z main sprite `+0x59/+0x5d`,a rozmiar z
`+0x61/+0x65`. Odejmowanie współrzędnych zawija int32 tak jak oryginał.

1. Coarse (precision0) zwraca true przed geometrią i odczytem maski.
   Nie wolno używać tego wyniku jako prostokątnego testu UI.
2. Precise odrzuca punkty poza `[0,width)×[0,height)` względem sprite'a.
3. Dla **stored frame32…55** wybiera maskę `storedFrame−32`.
   Dla pozostałych klatek wybiera `byte(heading×3)`;port ogranicza normalne
   heading0…7. Wynik nie pochodzi z DrawnFrame.
4. Wykonuje oryginalny lookup sekwencji `0x5431d0` i bit test `0x5575d0`.
   Wiersze mają stride wyrównany do8 bitów;bit po lewej jest najstarszy.

Port:[ShipPointerMask.cs](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipPointerMask.cs).
Konstruktor klonuje24 płaszczyzny. Nie przechowuje mutowalnych tablic
wywołującego. Walidacja wymiarów/długości/headingu jest kontraktem adaptera,
nie deklaracją identycznej obsługi niepoprawnej pamięci w oryginale.

Eksporty źródłowe:
[4e06c0](../artifacts/units/animation/export-images/004e06c0.c),
[5431d0](../artifacts/units/animation/export-images/005431d0.c),
[5575d0](../artifacts/units/animation/export-images/005575d0.c).

## Dane i staging

[stage_ship_picking.py](../tools/stage_ship_picking.py) sprawdza SHA256
oryginalnego EXE oraz OBJECTS.DKX/DKD. Z type11 odczytuje sekwencję24 masek,
a rozmiary porównuje z logiczną geometrią type8. Nie odczytuje kolorów,
nie filtruje ani nie przeskalowuje masek.

| Rodzina | Sekwencja | Geometria | Liczba |
| --- | --- | --- | --- |
|A1|MASK_1A00…23|56×56|24|
|H1|MASK_1H00…23|72×72|24|
|B4|MASK_4B00…23|64×64|24|
|G4|MASK_4G00…23|72×72|24|

Siódmy zestaw `Assets/Resources/ShipPickingGenerated` ma manifest schema1
oraz `ShipHitMasks.bytes`:52800B,SHA256
`60f3696904880fa4c4a51da2094f96145b30859013463369d1b953aebf3ba240`.
Staging jest idempotentny i odmawia nadpisania zmodyfikowanego poprzedniego
payloadu,nawet przy `--replace-generated`. Editor preflight wymaga nowego
zestawu. Pozostałych sześciu zestawów ani grafiki renderowania nie zmieniano.
Nie wygenerowano podglądu ani ZIP.

```sh
.venv/bin/python tools/stage_ship_picking.py
.venv/bin/python tools/validate_ship_pointer_mask.py --output <świeży-raport.json>
```

## Rzeczywisty oryginał i C#

[Probe x86](../tools/probe_ship_pointer_mask.py) wykonuje całe4e06c0,
5431d0 i5575d0 **bez hooków**. Jawne struktury sprite'a/sekwencji i null
output pointer są wejściami testu;nie wykonuje się konstruktora statku,
renderera,UI ani całego pickera. Oryginał modyfikuje bajt stosowego argumentu
output na indeks maski;harness ponownie podaje null przy każdym call.
Pierwszy nieudany harness i jego log zachowano,bez modyfikacji oryginału.

[Validator](../tools/validate_ship_pointer_mask.py) najpierw sprawdza hash
fixture i oryginalnych plików,następnie wymaga świeżego native==fixture,
po czym kompiluje prawdziwy C# z `/checked+ /warnaserror+` i porównuje:

- 96 pełnych oryginalnych płaszczyzn oraz24 syntetyczne13×5 dla paddingu;
- 423960 wyników pikseli pełnych płaszczyzn (SHA256 i liczba trafień);
- 8468 osobnych punktów:frame0…87,granice32/55,heading0…7,krawędzie,
  coarse,int32wrap oraz kolejność bramek;
- łącznie432428 rzeczywistych wywołań oryginału i13 kontroli API C#.

[Końcowy raport](../artifacts/world-input/picking/mask-csharp-validation-final.json):PASS.
[Fixture](../tests/fixtures/ship_pointer_mask.json) SHA256
`8119cc2cb7e645edc671f2ba8daea5d1878a61ddeb0acca254e59a0c92163245`.
[C# probe](../tests/fixtures/ShipPointerMaskProbe.cs),
[testy](../tests/test_ship_pointer_mask.py),
[testy stagingu](../tests/test_stage_ship_picking.py).
Pięć testów celowanych przeszło bez pominięć w14.360s.

## Build i pozostała walidacja

[BuildReport](../artifacts/world-input/picking/build-report.json):
Unity6000.3.27f2,Windows64Mono,0 błędów/ostrzeżeń,146364475B.
DLL SHA256 `e211062e1098162e28bc1dcdf66ef9851a8dbfb2666f18d486b6e7e4443e2e89`.
[Integralność](../artifacts/world-input/picking/source-integrity.json):47 C#/96 meta,
bez braków,błędnych lub powtórzonych GUID;bez zmian C# po buildzie.

Poprzedni pełny discovery zatrzymano SIGINT na prośbę użytkownika.
Zachowany unittest-final.log nie jest dowodem194PASS. Świeży
[unittest-resumed.log](../artifacts/world-input/picking/unittest-resumed.log)
zakończył **194 testy PASS,0 pominięć,w181.146s**. Pięć testów celowanych
jest wliczonych w194;nie dodawać ich ponownie.

[Regresja istniejących rozkazów](../artifacts/world-input/picking/order-regression/report.json)
na tym samym nowym DLL:2 sesje,normal12+two-after-clear23=35 kadrów,
105 ROI RGBmean/max0,54 pola,path/cache/RNG,21 rejestracji na sesję,
1190 rzeczywistych odczytów queue. Cleanup8/8 i exit0. Sprawdzono wszystkie
80 PNG i ich decodedRGB. Zachowano45 prób obrazu,10 odrzuconych:
7 dokładnie pasuje do wcześniejszego checkpointu,3 nie sklasyfikowano.
To regresja istniejącego ruchu/renderowania;nie test trafienia myszą w playerze.

Dodatkowo [dowód kolejności world pickera](WORLD_PICKER_ORDER_EVIDENCE.md)
wykonał1206 zapytań oryginału. Nie jest jeszcze portem tego pickera do C#.

Nie potwierdzono pełnego world pickera49a580,kolejności jego sąsiadów,
fog,pozostałych slotów obiektów,własności,maski wyboru grupy ani kliknięcia
przekazywanego do actor action20. Wciąż brak pełnego sterowania,Life,AI,
walki i finalnej oprawy2026;normalny Start pozostaje wyłączony.
