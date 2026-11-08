# Kontrola diagnostyki zapytań o statek

Stan:2026-11-03. `tools/smoke_ship_picking.py` porównuje rzeczywisty
player Unity z oryginalnym49a580 dla ośmiu źródłowych statków. To diagnostyka
zapytań w kontrolowanym świecie:bez zdarzeń myszy,zaznaczania,mgły i innych
slotów obiektów. Normalny Start pozostaje wyłączony.

## Niezależne oczekiwania

[Helper](../tools/smoke_ship_picking.py) używa oryginalnego
[NativeShipWorldPicker](../tools/probe_ship_world_picker.py),który wykonuje
49a580,49a1d0 oraz rzeczywiste4e06c0/5431d0/5575d0. Hook na wejściu
predykatu wyłącznie odczytuje kolejność i argumenty;nie zmienia kodu,
rejestrów,pamięci ani zwrotów. Przebieg nie jest odtworzeniem algorytmu C#
w Pythonie. Każde oczekiwane trafienie i lista odwiedzonych ownerów pochodzi
ze świeżego wykonania oryginalnego x86.

Pozycje,stored frame,heading i bieżące/rezerwowane claims ruchomego0b
pochodzą z przypiętej fixture normalnego obiegu rozkazów. Pozostałe siedem
jednostek zachowuje źródłowe recepty. Dokładny descriptor_resource wiąże
każdą jednostkę z oryginalną rodziną masek A1/H1/B4/G4;nie używa się alfy
renderowania lub odgadywania rodziny z nazwy modelu. Źródła i siedem zestawów
Resources obejmuje provenance sprawdzane przed uruchomieniem i po nim.

Każdy checkpoint ma osiem logów rzeczywistych actor bindings. Po każdym
aktorze występują dwa zapytania środka:coarse i precise. Dalej badane są
published origin0b,prawa/dolna granica,bieżąca komórka,opcjonalna rezerwacja
i cztery narożniki mapy. To25 lub27 zapytań. Współrzędne mogą wypadać poza
kamerą;nie dowodzą konwersji ekranu ani oryginalnego FOV.

W aktualnym zbiorze cztery scenariusze dają53 checkpointy,
1353 zapytania,1243 wywołania predykatu i424 bindingi aktorów.57 zapytań
odwiedza tego samego ownera ponownie. W rezerwacji przy counter19 coarse
środka17,3 zwraca0b po jednym wywołaniu,a precise zwraca brak trafienia
po dwóch wizytach0b. Nie wolno deduplikować referencji zajmującej dwa pola.

## Fence i kontrolki

Na etapie obrazu helper porównuje54 pola normalnego rozkazu,pełne path/cache,
trzy części0b,21 rejestracji oraz34 rzeczywiste wpisy kolejki statków/raf.
Do fence wchodzą także wszystkie actor bindings,zapytania,kolejność wizyt
oraz końcowy marker `checkpoint_complete` z grid_unchanged=True. Marker
powstaje po sprawdzeniu wszystkich576 referencji zajętości w Unity.

Capture wymaga identycznego stanu przed i po odczycie framebufferu.
Obowiązuje dotychczasowy globalny max≤4,ścisłe ROI,deadline1s wewnątrz
holdu1,25s i zachowanie każdej odrzuconej próby. Oczekiwany obraz pochodzi
z oryginalnych zasobów i natywnej historii kolejki,tak jak w zweryfikowanym
etapie obiegu rozkazów. Zapytania nie dodają grafiki do obrazu.

[Siedem osobnych testów](../tests/test_smoke_ship_picking.py) przeszło bez
pominięć w6,968s:[log](../artifacts/world-input/picking/picking-qa-targeted-tests.log).
Obejmują36 jawnych negatywnych zmian logu:m.in. błędny descriptor,stored frame,
pozycję i claims,zły wynik lub precision,utraconą powtórną wizytę,błędne
sample/index oraz brak,podwojenie lub fałszywą wartość markera nonmutation.
Dodatkowo fence odrzuca zmianę zapytania przy niezmienionych pikselach/ruchu
oraz brak końcowego markera. Kontrola dodatnia akceptuje kompletny stały fence.
Parser zachowuje ownerID0 i powtórne wizyty0,0,odróżniając je od none.

Testy te są osobne od pełnego discovery196PASS/0skip/175,263s.
Nie deklarować203 testów w jednym przebiegu. Helper został zamrożony
przed playerem:SHA256
`9821b72b0de19edb00fb69ec0f50cb17e4433546df4680f10c328a8487bd6994`.

## Pilot playera

[Pilot](../artifacts/world-picker/runtime-first-normal/report.json) przeszedł:
12 pełnych kadrów1920×1080/36 ROI RGBmean/max0,306 zapytań,96 bindingów,
283 wywołania predykatu,w tym12 zapytań z powtórnym ownerem.
408 rzeczywistych odczytów kolejki. Cleanup8 i exit0.

[Niezależny audyt](../artifacts/world-picker/qa-pilot-independent-audit.json)
potwierdził wszystkie25 plików PNG po ich SHA i decodedRGB,aktualne
provenance oraz zgodność query rows z natywnymi wynikami i pełnymi
argumentami wywołań. Zachowano13 prób obrazu,w tym jedną odrzuconą,
której nie sklasyfikowano jako dokładny wcześniejszy checkpoint.

## Końcowe cztery sesje

[Pełny raport](../artifacts/world-picker/runtime-final/report.json) przeszedł:
53 pełne kadry1920×1080/159 ROI RGBmean/max0. Rzeczywiste wyniki wszystkich
1353 zapytań i1243 kolejnych wywołań predykatu zgadzają się z oryginałem.
57 zapytań powtarza ownera;424 rzeczywiste bindingi i53 końcowe markery
nonmutation są zgodne. Każdy marker zamyka kontrolę576 referencji siatki.
1802 rzeczywiste odczyty kolejki i54 pola rozkazu/path/cache/RNG są poprawne.

| Scenariusz | Kadry | Zapytania | Wizyty | Bindingi |
| --- | --- | --- | --- | --- |
|normal|12|306|283|96|
|nearest;limit180|10|254|222|80|
|two-after-clear|23|587|551|184|
|halt-reservation;limit46|8|206|187|64|

Cleanup8/8/8/9 oraz exit0 wszystkich sesji. Nearest nie osiąga żądanego
celu18,2;endpoint17,2 i active1152 pozostają rozdzielone. Przerwanie przy
46 zachowuje dodatkową rezerwację aż do cleanup. Pilot12/36 jest osobny
od końcowych53/159,bez podwójnego liczenia.

[Niezależny audyt końcowy](../artifacts/world-picker/qa-runtime-final-independent-audit.json)
zweryfikował wszystkie111 plików PNG zarówno po kodowanych SHA,jak i po
zdekodowanych RGB. Każdy query row porównano z natywnym wynikiem,pełnymi
argumentami i listą obserwowanych wywołań. Wszystkie aktualne provenance
nadal pasują. Bazowe logi ruchu,rendererów,kolejki i oczekiwane piksele
są identyczne z odpowiadającymi scenariuszami poprzedniego przypiętego
zestawu53 kadrów. Zachowano58 prób,w tym5 odrzuconych:4 dokładnie pasują
do wcześniejszych checkpointów,1 nie sklasyfikowano.

Unity6000.3.27f2 Windows x64 Mono:146377147 bajtów,0 błędów i ostrzeżeń
BuildReport,DLL SHA256
`a706aa5e9d9a5966b78c84bc1eace6f669f655a0e94601f82aeb2002e5305409`.
49 źródeł C#/98 meta;bez zmian C# po buildzie.

Zapytania nie są walidacją zdarzeń InputSystem ani rzeczywistych kliknięć.
Oryginalny oracle dostaje jawne sprite geometry,tablice masek oraz zajętość
z recept i stanów kontrolowanego zbioru;nie wykonuje pełnych konstruktorów
statków,loadera type11 lub inicjalizacji świata.

## Granice wnioskowania

W siedmiu dotychczasowych natywnych śladach ruchu stored i drawn mogą się
różnić,lecz zawsze wybierają ten sam indeks maski. Także physicsWorld jest
równy publishedWorld. Same wyniki tych zapytań nie rozróżniają zamiany tych
pól. Rzeczywiste binding logs sprawdzają przekazaną wartość stored frame
(np81 przy drawn80),a niezależny przegląd mostu wiąże ją z tym samym Pose,
który jest używany przez predykat. Osobny dowód pełnych masek i surowych
wejść pozostaje dowodem samej reguły wyboru maski i opublikowanej geometrii.

Osiem częściowych ownerów zajętości nie zastępuje pełnego świata45 obiektów.
Nie potwierdzono pozostałych slotów,fog,pełnej inicjalizacji selektora grup,
UI,myszy,cursorów,healthbar,natywnego Windows11 ani wydajności laptopa.
Źródłowe grafiki pozostają wzorcem zgodności,bez deklaracji finalnej oprawy2026.
Nie utworzono podglądu do prezentacji,ZIP ani publikacji.
