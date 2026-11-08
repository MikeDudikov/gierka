Dalszy etap został ukończony: [pierwszy Shift i życie znaczników](PENDING_QUEUED_INPUT.md).
Poniższe wyniki opisują wcześniejszy etap zatwierdzonej grupy.

# Kolejka Shift i znaczniki WPMOVE — 2026-11-04

Istniejący adapter InputSystem obsługuje teraz Shift dla zatwierdzonej grupy:
przejście ze zwykłego zadania 100/1 do trasy 100/2, dopisywanie punktów,
pominięcie duplikatu oraz powrót do zwykłego zadania. Nadal jest to jawnie
uruchamiana referencja diagnostyczna, a nie ukończona misja.

## Granica symulacji

Adapter wymaga `--ship-fleet-wave-prefixes` z jednym signed16 słowem na aktora
rejestru. Przekazuje te wartości bezpośrednio do istniejącego przeciążenia
`ShipWorldStep.TryAdvance`. Wartość 117 w testach jest wejściem kontrolowanego
profilu pamięci Wine CRT; nie stała domyślna gry lub ogólna właściwość Windows.
Bez tego argumentu dotychczasowa blokada Shift pozostaje aktywna.

Żądania trafiają do istniejącego `ShipFleetMembership.Group.Task` i poczty
`outgoing`. Nie dostarczamy ich bezpośrednio statkom i nie resetujemy wieku
grupy. `ShipFleetNormalTask` wykonuje się na pozycji floty w rejestrze świata.
Nie dodano nowego Update, managera, ECS, fazy wszystkich grup ani drugiego flush.

Ten kod jest w pełni zgodny z istniejącym `SingleStepClock` i nie narusza
zweryfikowanego deterministycznego stanu. Zakres tego stwierdzenia stanowią
porównania klatek z x86 oraz niezmienione pliki rdzenia symulacji; nie jest
to deklaracja zgodności całej, nadal nieukończonej gry.

## Źródło grafiki

`controlm:8:WPMOVE` ma 21 części, rozmiar logiczny 36×29 oraz cyfry
`_WPNUM0`…`_WPNUM9`. Oryginalny konstruktor 4ced80/545e00 wykonano dla
wszystkich 256 wartości bajtu numeru. Granicami są niższe wywołania konfiguracji
545e80 i ładowania 546160, a nie sam konstruktor. Nie wykonywano całego
oryginalnego renderera. Dla numerów 1…99 maska wybiera cyfry; pozostałe wartości
pozostawiają sam znacznik, włącznie z przepełnieniem bajtu.

Oryginalny 4ced10 zapisuje cell×64+(14,18). Potwierdzono sześć przypadków,
w tym ujemne liczby i przepełnienie int32. 545e80 wybiera dla typu 8 zwykły
sprite na głębokości 7. Atlas powstaje przez istniejący dekoder części,
z ich źródłowymi indeksami, offsetami, kolejnością i paletą maplib.

`ShipFleetVisualReference` czyta tabelę z istniejącego manifestu zasobów.
Przechowuje wyłącznie obiekty renderowania, odczytując punkty z właściciela
zadania. Używa istniejącej `SourceSpriteSlotQueue`. Nie zmienia zadania,
członkostwa, siatki ani licznika. Znaczniki usuwa po powrocie do 100/1.
Dotychczasowy atlas selektorów pozostaje identyczny bajtowo.

## Dowody i wykryty problem scenariusza

Pierwsza próba runtime odrzuciła zwykły rozkaz do (18,5) w kroku 85:
komórka była zajęta lub zarezerwowana. Starszy korpus otrzymywał typ kursora 7
jako jawny kontekst UI, więc nie dowodził dostępności tego pola dla myszy.
Nie ominięto blokady. Nowy korpus `queued_input_world.json` stosuje wolne,
przejezdne pole (20,5); dwa silniki źródłowe potwierdzają pakiety i dalszy ruch.
Stary korpus pozostał bez zmian.

Dwa testy rzeczywistych zdarzeń InputSystem, z flotą przed i po statkach,
przeszły po 33 punkty kontrolne: 99 stanów aktorów, 330 części obrazu,
1122 odczyty kolejki świata, 299 publikacji i 16 odczytów znaczników.
Sprawdzono trasę, deduplikację, maski, pozycje, sloty, kolejność rysowania,
pocztę, powrót do zwykłego zadania oraz Ctrl ponownie wybierający grupę.
Wszystkie pakiety po starcie generuje C#; źródło nie steruje odtwarzaniem.

Checker odrzucił sześć uszkodzonych przebiegów: brak pakietu UI, złą pozycję,
maskę lub kolejność znacznika, zgubiony punkt oraz opóźnienie odbioru poczty.
To syntetyczne zdarzenia InputSystem, nie potwierdzenie routingu myszy systemowej.
Nie wykonywano zrzutów ekranu ani testu porównania całych klatek RGB.

Raporty: `artifacts/queued-input`. Build Windows64Mono 6000.3.27f2:
153596123 bajty, 0 ostrzeżeń, 0 błędów; 1920×1080, ExclusiveFullScreen.
DLL SHA256: `8cccbf2a52f777e5615f1a07e99e69b464727c000a43ab83cdf7d3b029b96523`.
Na tej DLL sprawdzono 1224 stany nowego scenariusza, 7344 starego korpusu Shift,
16608 świata i 7248 zwykłych ponownych rozkazów.

Zachowano pierwszą nieudaną próbę runtime oraz błąd licznika w raporcie testowym:
checker porównywał nowe dwa scenariusze, lecz raportował stałe liczby starego
korpusu 12 scenariuszy. Raport liczy teraz dane wejściowe. Nie zmieniono w tym
celu kodu symulacji ani wyników źródłowych.

## Następny krok

Obsługa pierwszego Shift tworzącego grupę z tymczasowego zaznaczenia,
sprawdzenie trwałości znaczników po wyczyszczeniu zaznaczenia i kolejne
porównanie InputSystem ze źródłem. Korpus źródłowy tego etapu jest już
przygotowywany w `artifacts/pending-queued-input`; nie jest jeszcze gotową
integracją adaptera.

Pełny Life, AI, Start misji, edycje 300/311, raport 40, pełna historia sterty,
finalna oprawa 2026, natywny Windows 11 i wydajność laptopa pozostają do wykonania.
Bez publikacji, aplikowania konfiguracji, nowych ZIP lub podglądów.
