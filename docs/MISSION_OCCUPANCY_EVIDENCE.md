# Siatka zajętości miss000 — wąski kontrakt źródłowy

Stan:2026-11-02. Bieżący boot i marker środowiska potwierdzono przed pracą.
Oryginalny EXE ma SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
To analiza i wykonanie wybranych instrukcji x86, bez pełnego startu gry,
Unity Editor, Wine lub nowych grafik. Nie jest to implementacja pathfindingu.

## Oryginalna siatka

`DumpClassTy::GetMessage0x499560`, komunikat2, wywołuje
`mfBMapDumpCreate0x545780` z dużą mapą i b_ALIB. Zapisuje wynik pod
`DAT_005c74fc`, szerokość pod0x5c74ec, wysokość pod0x5c74f0 i liczbę komórek
pod0x5c74e8. W miss000 jest24×24komórki z geometrią źródłową64×64.

| Obszar | Format |
| --- | --- |
| Nagłówek+0,+2,+4,+6 | cztery signedshort skopiowane z b_MAPA:24,24,64,64 |
| Pierwsza komórka | baza+8 |
| Kolejna komórka | krok24bajty, indeks=`y*width+x` |
| Komórka+0 | uint32 flagi, po jednym nibble na każdą z8warstw |
| Komórka+4 | pojedyncza referencja occupanta używana przez helpery statków i ReefSetState |
| Komórka+8 | odrębny slot, np.AmberClassTy; nie ten sam co+4 |
| Komórka+20 | referencja rafy zapisywana przez jej msg2 |

Pozostałym slotom nie przypisano pełnych znaczeń. Nie wolno zmieniać24bajtów
na pojedynczy indeks statku lub utożsamiać wszystkich pól pointerowych.
Fabryka rezerwuje `width*height*24+32`bajty. `0x558f80` zeruje całą alokację,
kopiowany nagłówek ma8bajtów; końcowe24bajty pozostają wyzerowanym zapasem.
Zatem referencje startują jako0 przed inicjalizacją obiektów.

## Jak powstają flagi

`mfBMapGetCellType0x545650` dla maski0xff odwiedza osiem planarnych warstw.
Zerowy lowbyte selektora pomija warstwę. Highbyte identyfikuje **pierwszy**
rekord b_ALIB z takim ID, przez oryginalne `0x544ba0`. Kategoria jest dwordem
na **+4 tego rekordu**, nie bajtem typu bitmapy na+40.

```text
flags = 0
for layer in 0..7:
    word = uint16LE(mapPayload,2*((layer*height+y)*width+x))
    if (word & 255) != 0:
        category = uint32LE(firstLibraryRecordWithID(word >> 8),4)
        shift = layer*4
        flags = ((flags & ~(15 << shift)) | (category << shift)) modulo2^32
```

Oryginał nie przycina `category` do0xf przed OR; port zachowuje bity i
zawijanie x86. Nibble służy późniejszemu zapytaniu, lecz to nie uzasadnia
zmiany loadera. `0x545780` wpisuje te flagi do każdej komórki.

Wykonano rzeczywiste `0x545780`, `0x545650`, `0x544ba0` i zerowanie0x558f80.
Hooki obejmują wyłącznie577normalnych powrotów setjmp i jeden malloc
zwracający wcześniej wypełniony0xccbufor. Oryginalne zerowanie, lookupID,
przetwarzanie warstw i zapisy pól działają bez zastępstwa. Odtworzono wyłącznie
wejściowy runtime nagłówek b_ALIB oraz dane mapy; nie uruchamiano loadera plików.
Całe13856bajtów wyniku zgadza się z niezależnym złożeniem formatu.

- Pełna alokacja SHA256:
  `b0dc1c3abbcaf5848bdb31149ce4074d4d8744519d1b4350f7808e09b57e823c`.
-576samych flag uint32LE,2304bajty, SHA256:
  `eb8c22b2dc3a3d6de5be5c5a28560701333cbc8610e8dd687052f4f93b260283`.
- Fixture repo:`tests/fixtures/mission_cell_flags.bin` i odpowiadający JSON
  z warunkami dowodu. Oryginały i pełny bufor pozostają w prywatnych materiałach.

## Pojedyncza referencja: zapis, zwolnienie i zapytanie

`0x499800(ignoredSide,reference,x,y)` oblicza komórkę, następnie zapisuje
referencję na+4 **tylko jeżeli obecna wartość jest0**. Nie nadpisuje nawet
inną referencją tego samego rodzaju. Pierwszy argument nie wpływa na wynik
tej funkcji. `0x499830` jest wariantem z gotowym indeksem.

`0x499860(x,y,reference)` zeruje+4 **tylko jeżeli bieżąca referencja jest
równa przekazanej**. Wariant0x4998a0 przyjmuje indeks. Nie jest to bezwarunkowe
kasowanie komórki podczas wycofania nieudanej operacji.

Zapytanie `0x4999e0(x,y,restrictionByte)` sprawdza tylko flagi:

```text
low = flags & 15
high = (flags >> 4) & 15
allowed = low < 8
          and high not in {4,5,6}
          and (restrictionByte == 0 or high != 3)
```

`0x499a40` dodaje wymóg pustego slotu+4. Wyższe24bity flag pozostają
obecne, lecz nie uczestniczą w tym predykacie. Tych dwóch funkcji nie należy
opisywać jako kompletnego wyznaczania trasy, zasięgu jednostki lub reguł
umieszczania budynków. Same oryginalne helpery nie sprawdzają granic.

Dowód `artifacts/units/collision/source-occupancy-validation.json`:

-25sekwencji claim/release na pięciu komórkach, z pustym, zgodnym i obcym
  właścicielem, w tym niezerowymi opaque-pointer wartościami;
-1536wariantów flag/restrykcji/zajętości i3072wyniki obu zapytań;
- wszystkie te małe helpery wykonano bez przechwytywania funkcji.

## Dlaczego rafa może przejść do stanu3

ReefSetState0x430320 odczytuje slot+4 swojej komórki. Akceptuje tylko obiekty,
dla których `runtimeClass-200` mieści się w0..31 i należy do maski0xfff,
czyli runtime klasy200..211. Sam fakt zajęcia komórki nie wystarcza.
Następnie wywołuje `0x4ba790(unit,0)`.

Ta funkcja **szuka konkretnego typu polecenia0**, nie ogólnego bitu kolizji
ani domyślnego stanu idle. Liczba poleceń jest bajtem unit+0x483; ich typy
są dwordami od unit+0x4b5, krok24bajty. Zwraca1 po znalezieniu typu
przekazanego w argumencie. Z zerową liczbą wpisów zwraca0 bez odczytu tablicy.
Wykonano40przypadków tej funkcji bez hooków, w tym pustą listę, trafienia
na różnych pozycjach, brak trafienia oraz wartości z wysokim bitem.

Dopiero occupant właściwej klasy z poleceniem0 może wymusić stan3 w tej
badanej gałęzi. Inna klasa w tym samym pointerowym slocie nie spełnia filtra.
Nie należy twierdzić, że dowolna jednostka w komórce chowa rafę.

Wszystkie osiem źródłowych seedów klasy200 miss000 ma count+0x200=0.
Bytes po+0x204 bywają0xcdcd; przy count0 nie są listą poleceń i nie należy
ich interpretować. `ShipClassTy::LoadDateBase0x4dfa90` zeruje liczniki
+0x482/+0x483 przed ścieżką wczytywania poleceń. Nie dowodzi to, że późniejsze
callbacki i AI nigdy ich nie dodadzą.

| ID seeda200 | X,Y komórki | Wariant / runtime klasa po LoadDateBase |
| --- | --- | --- |
|0b|16,2|0/200|
|0c|21,5|0/200|
|0d|19,4|7/207|
|10|11,18|1/201|
|27|9,21|6/206|
|28|10,22|6/206|
|29|6,13|6/206|
|2a|6,14|6/206|

Żadna z tych kotwic nie jest równa pięciu kotwicom raf:22,19;16,22;3,5;20,10;
5,21. W źródłowej kolejności OBJ_ rafy05/06/09/0a występują przed pierwszym
seedem200(0b), a rafa21 po części statków. Nie znaleziono zatem w tych ośmiu
źródłowych pozycjach powodu do wymuszenia stanu3 przy tworzeniu tych raf.
To nie dowód całej siatki po wszystkich konstruktorach: odrębne klasy mogą
mieć dodatkowe callbacki, generować obiekty lub aktualizować sloty. Pełna
kolejność i lifecycle są osobnym zakresem.

## Mały port C#

`MissionOccupancyGrid.cs` przechowuje niemutowalną kopię576flag i odrębne
referencje właścicieli pojedynczego slotu. `TryClaim` i `Release` zachowują
reguły źródłowe. Właściciel jest **referencją obiektu**, a null oznacza pustkę.
Nie rezerwuje identyfikatora instancji0 jako sentinela. Równe wartości ID lub
nadpisane Equals nie pozwalają jednemu właścicielowi zwolnić drugiego.

`IsTerrainPassable` odtwarza flagowy predykat0x4999e0, `CanEnter` dodaje
pustego właściciela jak0x499a40. Sprawdzenia wymiarów/długości/granic i null
są polityką defensywnego API C#, nie zachowaniem oryginalnych helperów.
Zwracane bool claim/release opisują wynik API; źródłowe void porównuje się
według zmiany stanu. Nie nadano tym predykatom roli pełnego ruchu świata.

```sh
.venv/bin/python tools/validate_mission_occupancy.py --output artifacts/units/<nowy-raport>.json
.venv/bin/python -m unittest tests.test_mission_occupancy -v
```

Rzeczywisty C# i probe kompiluje się z `/checked+`. Potwierdzono576flag z
wykonanej oryginalnej fabryki,1536wariantów zapytań(3072wyniki) oraz36sekwencji
własności: razem1572porównywane przypadki.68oddzielnych kontroli API obejmuje
klon wejścia, wymiary, granice, null, identyczność referencji dla dwóch
właścicieli z ID0 i niezależność różnych komórek. Dwa testy unittest przeszły,
w tym odrzucenie zmienionego fixture i jego opisu. Wyniki:
`artifacts/units/collision/occupancy-csharp-validation-final.json`.

Ten port nie uruchamia wczytywania całej misji, wieloslotowych zapisów
innych klas, deformacji terenu, wyszukiwania ścieżek, ruchu, walki, AI,
pełnej obsługi poleceń ani poprawnego zachowania wszystkich kolizji.
