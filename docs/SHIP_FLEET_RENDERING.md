# Renderowanie trzech poruszających się statków — 2026-11-03

Etap poprzedniego DLL. Późniejsze połączenie pierwszego normalnego rozkazu
z kursorem opisuje[SHIP_FIRST_FLEET_CONTROL.md](SHIP_FIRST_FLEET_CONTROL.md).
Poniższe historyczne ograniczenie braku sterowania nie dotyczy nowego trybu
pierwszego rozkazu;pełne zadania grupowe nadal pozostają do wykonania.

Nowy tryb `--ship-fleet-motion-reference` wykonuje normalne rozkazy trzech
lokalnych statków0b/0c/0d i wyświetla ich rzeczywiste publikacje ruchu, obrotu
oraz bezczynności. Korzysta z istniejącego `ShipMoveOrder.CreateLiveLocal`,
aktualnej wspólnej siatki i źródłowej kolejki głębokości21 grup. Nie instaluje
ręcznie tras. Grafika0c korzysta z profiluA, a0d zachowuje osobny większy
profilH i warstwę pancerza.

**To kontrolowany przebieg rozkazów, jeszcze bez sterowania flotą myszą.**
Cele i odebrane słowa grupy są jawnymi wejściami diagnostyki. Scheduler zadań
grupy, Ctrl istniejącej grupy i połączenie całego UI pozostają do wykonania.
Zwykły Start jest nadal wyłączony; pełna gra i oprawa2026 pozostają w budowie.
Obowiązuje1920×1080,16:9,pełny ekran całego widoku na Windows11.

## Zasoby i wykonanie

`stage_ship_movement.compose` zachowuje identyczny domyślny profilA dla0b/0c
i udostępnia drugi ograniczony profilH. Stager `stage_ship_heavy_movement`
zapisuje dziesiąty zestaw Resources/ShipHeavyMovementGenerated. Poprzednie
dziewięć stagingów nie wymaga ponownego wygenerowania ani zmiany bajtów.
`BuildReferenceWindows` wymaga obecności nowego manifestu i atlasu.

| Parametr0d | Wartość |
| --- | --- |
| Deskryptor / maska |SHIP_H1110 / a3 |
| Klatki |0…87:32 ruchu,24 obrotu,32 normalnej bezczynności |
| Logiczny rozmiar |72×72;własna kotwica−4 w komórce |
| Wybrane części |0 cień,1 kadłub,5 pancerz,7 żagiel |
| Lokalna kolejność |1,5,7;cień pozostaje osobną grupą21000 |
| Zestaw |88 pozycji,352 wpisy części,224 unikalne bitmapy |
| Atlas |2304×504,RGBA32,bottom-up,4644864B |
| SHA256 atlasu |f057829bdbd9c53090bc2b680ef419e299bd5e56c4a33c275f6a0177cb194138 |
| SHA256 manifestu |29552570a7d0caee1a9ab155e57019c388ed63b530e5ad68e0ef0b9ca66704f4 |

Pełny oryginalny loader554d50 i sort55e56b…55e659 potwierdziły wszystkie88
pozycji i352 części. Loader wykonuje608 odczytów wybranych części całego
źródłowego deskryptora152 klatek;porównany zakres obejmuje0…87. Oryginalny
blitter574290 bez hooków porównał1342 bufory dla224 bitmap:pełne bbox,
wycinki,przeskok wierszy,dwie wartości początkowe,stride i bajty ochronne.
Hooki loadera dotyczą wyłącznie źródłowego I/O,alokacji,setjmp i zwalniania.
Sort i kod pikseli nie zostały zastąpione. Paletę i pełne płaszczyzny atlasu
sprawdzono osobno,z zachowaniem rzeczywistego pokrycia RLE.

Fixture `tests/fixtures/ship_heavy_poses.json`,SHA256
`abc5d63688c335ad456dbeea4adfb1f9d9be254ddec53aa8d93af42308f7bbe2`.
Bootstrap loadera pozostaje niezmieniony i chroniony pełnym SHA.
To źródłowa referencja wyglądu;nie jest deklaracją ukończenia nowej oprawy2026.

`SourceShipPoseReference` otrzymał drugi profil. Dotychczasowy konstruktor
zachowuje zachowanieA. Każdy właściciel pozy posiada własne sprite’y i teksturę,
zwalniane przy zamknięciu lub nieudanej inicjalizacji. Nowy
`ShipFleetMotionReference` konsumuje **każdą** publikację w kolejności
aktorów i w kolejności wewnątrz kroku:Apply(frame,world) oraz UpdateParent(depth).
Nie interpoluje pozycji ani nie zastępuje drawnFrame zapisaną klatką po idle.
Kolejka zachowuje źródłowe identyfikatory i historię remisów głębokości.

## Walidacja playera

Dwa rzeczywiste przebiegi WindowsMono pod Wine:pending1 z kolejnością11,12,13
oraz pending7 z kolejnością13,12,11. Każdy wykonuje250 kontrolowanych ticków,
normalne cele18,5 /20,6 /18,4 i17 zatrzymanych punktów obserwacji.
Rozkaz nie przesuwa statku;trasa powstaje z rozkazu w rdzeniu.
Początkowa grupa−1 i odebrane słowa41→0 są jawnym wejściem,tak jak w źródłowym
scenariuszu. Nie jest to nowe potwierdzenie pełnej formacji lub zadań grupy.

| Sprawdzenie | Wynik |
| --- | --- |
| Pełne obrazy1920×1080 |34 przyjęte pary;RGB identyczne piksel w piksel |
| Stany trzech aktorów |102 pełne wiersze modelu względem x86,także trasa/cache/RNG/pending26B |
| Rzeczywiste części |340 odczytów sprite/pozycja/sortingOrder,w tym pancerz0d |
| Kolejka |1156 rzeczywistych odczytów34 rendererów;źródłowy native depth-update dla każdej publikacji |
| Publikacje |262 w kolejności,188+74;wszystkie wykorzystano w kolejce i pose adapterze |
| Obserwacje obrazu |83 PNG,49 prób,34 przyjęte;15 odrzuconych ujęć,z zachowaniem granic stanu |
| Zamknięcie |Obie sesje exit0;3 właścicieli póz zwolnionych;8 komórek zwolnionych |
| Testy celowane |14PASS,0 pominięć,41.923s;6 nowych i8 regresji staginguA |
| Negatywne kontrole QA |6 wykrytych zmian:brak pancerza,błędna kotwica,przedwczesna grupa,brak kolejki,kolejność publikacji,brak końcowego fence |
| ShippingDLL:rdzeń |10827 stanów/130 wejść planera/149760 komórek/33API ponownie PASS |

Oczekiwany obraz powstaje z oryginalnych RLE,palety i natywnych stanów ruchu.
Osobny oryginalny NativeQueue aktualizuje odpowiedni węzeł dla publikacji
każdego z trzech statków. Deklaracje renderera nie wybierają oczekiwanych
współrzędnych,sprite’ów ani kolejności. Log rzeczywistego playera ma własny
pinned fixture;kontrole negatywne wykazują,że checker odrzuca brakujące dane.
Kontrola obrazu wymaga błędu maksymalnego0 oraz niezmienionych granic stanu
przed i po przechwyceniu. Obrazy są wewnętrznym QA,bez podglądu do prezentacji.

Build Unity6000.3.27f2 Windows64Mono:152921579B,0 błędów/0 ostrzeżeń.
DLL `d1d5a3e476a90eaadfb3ed702003dac24c05608bc26ce46f3b75330e51a7da22`.
70 C#/128 poprawnych unikalnych meta;zmieniono5 wcześniejszych C# i dodano1.
Dotychczasowe64 C# i rdzeń ruchu zachowano.226 plików zamrożonych przed
buildem nie zmieniło się po nim. Scen,prefabów,pakietów i ustawień nie zmieniano.
Poprzedni atlasA i domyślne wyjście stagera są byte-identyczne.
Pełnego discovery nie powtarzano;wyniki poprzednich DLL pozostają historyczne.

Raporty pod `artifacts/fleet-rendering/`:runtime-1 i runtime-7-reverse,
shipping-validation.json,targeted-tests.log,build-report.json i windows-build.log.
Regresje dotychczasowego wejścia i wyboru podaje[VALIDATION.md](VALIDATION.md).
[Punkt wznowienia](evidence/milestone-20261103-fleet-rendering.json).

## Granice i dalszy krok

Kwant40ms i zatrzymania na obserwacje są kontrolą harnessu. Nie dowodzą pełnego
RunApp/Life,tempa gry ani docelowej wydajności. Znany zbiór21 grup nie obejmuje
pełnego świata,fog,walki ani wszystkich klas. Wspólny ruch myszą i własność
zadań grupowych wciąż wymagają połączenia ze sprawdzonymi modułami UI.
Następny krok:połączyć membership/formację/rozkazy/fizykę/renderowanie z
kursorem i wyborem,rozstrzygając Ctrl oraz ponawiane rozkazy z dowodem źródła.
Natywny Windows11,docelowy laptop,OS mouse/fokus i finalna oprawa2026
pozostają niezweryfikowane lub nieukończone. Bez publikacji i nowego ZIP.
