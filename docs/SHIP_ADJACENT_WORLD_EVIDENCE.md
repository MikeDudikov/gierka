# Sąsiednie cele statku 0b: zegar, teren i porządek obrazu

Stan: 2026-11-02. Cel pozostaje 1920×1080, 16:9, pełny ekran.
To źródłowe wsparcie ograniczonej diagnostyki sąsiednich celów, bez pełnego
StartGame, zegara świata, AI, sterowania myszy i finalnej oprawy 2026.
Nie uruchamiano Unity, Wine, Xvfb ani oryginału przez system operacyjny.

Niezmieniony `ancient.exe` ma SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Własny oracle i raport:
`artifacts/adjacent/time-depth/validate_adjacent_support.py` oraz
`adjacent-support-validation-final.json`. Nie powielają planera ani helpera
obrotu innych analiz; badają ich zależności i granice integracji.

## Początkowy znacznik animacji

`GameObj::InitSprite`, `0x50cb80`, rezerwuje obiekt 0x91 bajtów i wywołuje
konstruktor sprite’a `0x545e00`. Konstruktor jawnie ustawia m.in.:

```text
AnimObj+0x45 = 0     wewnętrzny indeks klatki
AnimObj+0x7d = 0     próg aktualizacji
AnimObj+0x81 = 0     znacznik ostatniej aktualizacji
```

To pola **obiektu wskazanego przez ship+0x8be**. Nie wolno pomylić ich
z osobnym polem ship+0x81, wykorzystywanym przez inne stany statku.
Ładowanie TYPE8 pod `0x546160` zapisuje grafikę, rozmiar i liczbę klatek;
w badanej ścieżce nie synchronizuje +0x81 z czasem aplikacji ani krokiem.

Późniejszy setup `0x4e0160` oblicza kotwicę z komórki i logicznych wymiarów,
ustawia frame=4*heading oraz próg +0x7d=2. **Nie zapisuje +0x81.** Dla nowego
0b daje world(1028,132), frame20, interval2, lastTick0. Nie wynika z tego,
że ponowne wywołanie setupu wyzeruje istniejący znacznik: kontrola lastTick73
zachowuje73.

Siedem prób wykonało cały konstruktor oraz dokładny blok setupu
`0x4e0160..0x4e01d6` bez hooków. Obejmują różne jawne liczniki systemu
0,1,2,3,40,0xffffffff oraz kontrolę istniejącego znacznika. Wynik setupu
nie zależał od podanego licznika systemu. Zatrzymano się przed obsługą
zasobu pomocniczego, bez emulowania całego ładowania sprite’ów.

Źródło czasu pozostaje takie jak w [dowodzie zegara](SHIP_MOVEMENT_CLOCK_EVIDENCE.md):
AnimObj odwołuje się do licznika kroków przez ship+0x70→system+0xde,
a kinematyka używa pending przez ship+0x0c→system+0xe2. Dla nowego Ship
bindowanie do tego samego PlaySystem ma osobny dowód fabryki.

## Epoch przygotowanej próby a pełne Life

Nowe ślady planowania/ruchu przyjmują jawnie planer przy counter1 i kolejne
wywołania Step przy2,3,… To **kontrakt przygotowanej próby**, a nie dowód,
że pełne oryginalne Life zawsze rozdziela te wywołania na różne kroki.

`ProcShipsWork0x4ab930` może w jednym wywołaniu przejść przez active80 do
`0x4a5f30`, a następnie przez active400 do `MoveShip0x4a3f40`. Nie zwiększa
między nimi globalnego licznika. Sześć nowych wykonań całego dispatchera
potwierdza to dla counter1,2,40 i kontrolowanego włączenia/wyłączenia
capability0x4000. Ciała work/plan i MoveShip zastąpiono wyłącznie granicami
rejestrującymi kolejność i ten sam licznik; nie wykonano w tej kontroli
samych poleceń, planowania ani ruchu. Normalny setjmp również jest hookiem.

Dlatego nie należy opisywać epoch plan@1→step@2 jako odtworzonej pierwszej
pełnej iteracji świata lub używać go do deklaracji tempa całej gry.
Dla diagnostyki z jawnymi wejściami czasu jest powtarzalnym zakresem.

W obrocie `0x4a3320` przy pierwszym wyborze kierunku może zapisać
frame32+3*heading bez publikacji. Dla początkowego heading5 jest to47.
Źródłowy strict unsigned warunek to `counter-lastTick > interval`.
Przy lastTick0/interval2 pierwsze wywołanie przy counter2 nie publikuje
klatki47; dopiero przekroczenie progu może opublikować kolejną klatkę.
To niezależne od zapisu ship+0x58d, który MoveShip aktualizuje jako znacznik
stanu. Sam obrót i jego wynik/state3 należą do helpera animacji; nie są
powtórnie portowane przez niniejszy oracle.

## Dziewięć komórek oryginalnej siatki

576 flag pochodzi z wykonanego oryginalnego tworzenia siatki i jest
przypięte SHA256
`eb8c22b2dc3a3d6de5be5c5a28560701333cbc8610e8dd687052f4f93b260283`.
Wokół source0b(16,2) występują:

| Y / X | 15 | 16 | 17 |
| --- | --- | --- | --- |
|1|0x308|0x8|0x1|
|2|0x1|0x1 — początek0b|0x1|
|3|0x7|0x7|0x1|

27 wykonań źródłowych zapytań dla dziewięciu komórek i restriction0/1/255
porównało 54 wyniki terrain/empty-entry. Wykonano całe `0x4999e0` i
`0x499a40` bez hooków na pełnej siatce z ośmioma źródłowymi właścicielami.
Początek jest zajęty; sześć przechodnich celów pozostaje pustych.
N(16,1) i NW(15,1) mają low nibble8, więc flagowy predykat je odrzuca.
Nie zastępujemy nieprzechodnich komórek wodą, aby wymusić osiem ruchów.

Osobny właściciel planera wykonał rzeczywiste `ProcPostMove/GetWayNew`;
raport `artifacts/navigation/adjacent/native-eight.json` potwierdza:

| Heading / cel | Wynik źródłowy |
| --- | --- |
|0 / E(17,2)|Dwa punkty: początek i cel|
|1 / NE(17,1)|Dwa punkty, mimo nieprzechodniego boku N|
|2 / N(16,1)|Brak trasy, count0|
|3 / NW(15,1)|Brak trasy, count0|
|4 / W(15,2)|Dwa punkty|
|5 / SW(15,3)|Dwa punkty|
|6 / S(16,3)|Dwa punkty|
|7 / SE(17,3)|Dwa punkty|

Nie interpretujemy return low byte0 jako bool sukcesu: jest0 również dla
przyjętych tras. W tym zakresie sukces wynika z zapisanej ścieżki i count2.
NE dowodzi również, że nie można dopisać ogólnej reguły odrzucającej przekątną
na podstawie samej flagi boku. Połączone statki, zajęte boki, dalsze cele
lub inne klasy mogą uruchamiać inne warunki; nie są tu rozstrzygnięte.

## Warunkowy obrys i sloty rysowania

Dla source0b logiczny rozmiar grafik wynosi56×56 zarówno w fazie ruchu,
jak i obrotu. Przypięty fixture88 pozycji potwierdza trzy części0/1/7,
offsety0 i depth−21000/10/4. Nowy driver publikuje tylko klatki0…55.

Przy opublikowanej kotwicy w obrysie:

```text
964 <= X <= 1092
 68 <= Y <= 196
logicalHeight = 56
bodyDepth = max(10000, 20000 - logicalHeight - Y)
```

bodyDepth mieści się w19748…19876. **Cały ten zakres jest niżej niż
rafy20200 i wyżej niż kolejny statyczny korpus19676.** Obrót w miejscu
pozostawia Y132 i depth19812. Nie należy używać movementState2 jako stanu
uszkodzenia: DrawSprite0x4df6e0 wybiera badaną formułę dla ship+0x74=1.

Trzy próby rzeczywistego `0x4df6e0` potwierdziły formułę dla Y68/132/196.
Hooki odcinają wyłącznie normalny setjmp, publikację SetLevel i DrawSprite;
rachunek i wybór ścieżki są kodem oryginału. Ten obrys jest warunkiem guardu,
nie dowodem dziewięciu legalnych celów ani całego ruchu poza tym zakresem.

Dziewięć dodatkowych zmian kotwicy/klatki wykonało całe źródłowe
`SetDepth0x55d960`, `SetFrame0x55ec00` i aktualizację osobnego cienia przez
`0x55e750→0x55eb50/0x55ea00/0x55ea40` **bez hooków**. W świeżym zbiorze
21 węzłów zachowano tablicę ID, liczbę węzłów i względny porządek.
Cień ma stale globalny depth21000 i otrzymuje nową pozycję/klatkę przez
istniejący slot. Ta aktualizacja nie rejestruje go ponownie ani nie zmienia
remisów cieni w tym zbiorze.

Test używa syntetycznej metadanej TYPE8 zgodnej z zerowymi offsetami0b,
zachowanego slotu cienia i pustych powierzchni bitmap. Nie rysuje pikseli.
Kierunek końcowego odczytu tablicy, od końca, ma wcześniejszy
[dowód oryginalnego renderera](UNIT_WORLD_ORDER_EVIDENCE.md). Nowy oracle
kontroluje rzeczywistą posortowaną tablicę, bez powielania tamtej pętli draw.
Nie rozciąga wyniku na callbacki, recykling ID, inne obiekty lub pełny sorter
zmiennego świata.

Dla ograniczonego zbioru można więc zachować istniejące sloty rendererów,
**pod warunkiem sprawdzenia obrysu, logicznego rozmiaru i statycznych
priorytetów sąsiadów**. Poza tym guardem potrzebny jest osobny dowód sortera.

## Przegląd integracji — przed walidacją playera

Read-only przegląd `ShipAdjacentReference` nie wykazał blockera przy
kontrakcie przygotowanej próby. Counter rozpoczyna się od1, kwant ma40ms,
a wielokrotne zatrzymania etapów jednego wywołania nie przesuwają źródłowego
zegara. Apply korzysta z DrawnFrame/PublishedWorld i bramki publikacji;
turn-start nie musi zmienić widocznej klatki. Guard obrysu odrzuca
wyjście poza zbadany zakres. Nie potwierdzono tu kompilacji, pełnego core
ani runtime; te kontrole są zadaniem integracji.

Niezależny przegląd ekstrakcji `SourceShipPoseReference` zachował kontrakt
88 pozycji/152 bitmap/maska0x83, Point i znak Y. Helper wymienia trzy istniejące
renderery0b, zachowując sort/material oraz pozostałe26 z29 rendererów.
Rollback usuwa własne zasoby, a Dispose najpierw odwiązuje wizualizacje,
potem zwalnia sprite’y i atlasy, z idempotentnymi guardami. To przegląd
statyczny; nie zastępuje regresji starego ruchu ani testu wyjścia.

Pierwsza próba nowego oracle zatrzymała się na błędnym założeniu schematu
fixture: selected_frames jest liczbą88, nie listą. Poprawiono kontekst testu,
bez zmiany oryginału lub progów. Log próby zachowano. Main README/plan
nie zostały zmienione przez ten etap dowodowy.
