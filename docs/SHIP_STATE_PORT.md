# Stan ruchu i blokujący arbitraż w C# — 2026-11-04

Rozszerzono istniejący `ShipMoveOrder`,bez nowych klas Unity,menedżera,ECS
lub pętli Update. `RestoreSourceMovementState(bytes,sourceCounter)` odtwarza
obsługiwany stan ruchu z oryginalnego rekordu. `Tick` wykonuje teraz również
blokującą gałąź normalnego zadania80. `SingleStepClock` i kolejność świata
pozostają bez zmian.

## Odpowiedzialność i synchronizacja

Autorytatywny stan nadal znajduje się w `ShipMoveOrder`. Prywatny tymczasowy
`SourceRecord` kopiuje wejście,sprawdza granice i odczytuje offsety. Nie
przechowuje drugiej aktywnej symulacji. Żaden natywny adres nie jest
dereferencjonowany w C#:rekordy trasy i cache mają własne tablice.

Wywołujący przekazuje licznik źródłowego świata;nie jest on odczytywany
z czasu Unity. Przy odtwarzaniu całej kohorty trzeba najpierw odtworzyć
kontekst zegara,członkostwa i zajęć siatki,a potem aktorów,przed kolejnym
krokiem świata. Test ponownego odtworzenia robi to jawnie przez istniejące
API grid. Nie powstał nowy globalny scheduler lub loader całej gry.

Import sprawdza symulacyjną grupę5e przez istniejący odczyt membership;
nie zapisuje UI5c,ordinałów lub slotów. Niezgodna grupa wymaga właściwego
odtworzenia kontekstu członkostwa przez jego dotychczasową granicę41.
Claim bieżącej i zarezerwowanej komórki przechodzi przez `TryClaim`,jak
źródłowe4e2180→499800/499830. Nie czyści obcych lub niepowiązanych slotów.
Guard odrzuca konflikt właściciela lub dawny własny claim poza obsługiwanym
kontekstem **przed zmianą aktora**. To granica projekcji,nie nowa reguła gry.

## Zakotwiczenie w x86

| Procedura | Przeniesione zachowanie |
| --- | --- |
|4e12e0/4e2180 |Oryginalne regiony rekordu:flag214/218,blok aktora269..7d5 pod offsetem−49,pending7d6..8bd pod−4d.133B bloku54c nie wystarcza do odtworzenia całego ruchu. |
|4e2180 |Trasa5B×count,cache-wektor przez format55f280/55f2e0,21B danych sprite’a. Adresy tylko określają obecność danych;nie są przenoszone do modelu. |
|4dc53a,4abe87 |Bramka58b inicjalnie0;odtworzenie z bufora+542. Brak debugowego settera bramki. |
|4e12e0/4e2180 |Deferred265 jest pominięte w formacie. Import zachowuje istniejącą wartość zamiast czytać domniemany offset lub zerować. |
|4aa540 |Pending8 obsługiwane przed arbitrażem80. Zerowy stopMask anuluje i usuwa pending/deferred zadania;mask80 zachowuje odrębną ścieżkę. |
|4abe50→4abc60→4a6330 |Niezerowa bramka aktywnego80 prowadzi przez anulowanie. Niezero pending po anulowaniu usuwa kandydata deferred. Maskafffffe0f odrzuca pending zadania. |
|4a6330 |Równy lastPlan/counter wraca przed zmianą stanu. W przeciwnym razie2/3→0,inne ruchome stany→1,cache jest czyszczony. |
|4ab720/4ab250 |Arbitraż działa także przy ready80=0. Dopiero gotowość decyduje o promocji.255 zachowuje priorytet;nowe rozkazy grup nadal czekają na późniejszą pocztę. |

Źródło to EXE `cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`,
dekompilacja i wykonanie x86,nie nieistniejące pliki C/C++.
Komentarze nowych metod wskazują procedury lub jawne granice zarządzane.

## Dowód zgodności

222 warianty:0b/0c/0d,cztery chwile ruchu,bramki0/1/255,stopMask0/80,
istniejące deferred0/80,ready=0 lubffffffff. Flagi,bramki i maski są
kontrolowanymi wejściami testowymi,nie dowodem osiągalności wszystkich
kombinacji w oryginalnej misji. Oryginalne eksport/import oraz następne
32 Promote+Work wykonuje x86,z dotychczasowymi granicami CRT i grafiki.

C# importuje każdy rekord dwukrotnie. Drugie odtworzenie cofa ruch po
jawnym odtworzeniu kontekstu siatki.15096 pełnych porównań stanów PASS,
10 kontroli API,checked+/warnaserror+. To test ponownego importu i braku
aliasowania bufora,nie wyłącznie ustawienia58b. Osiem wcześniejszych kontroli
rozszerzono o właściciela i odrzucenie profilu prepared-only.

Nowy oracle aktualizuje obserwację grafiki z rzeczywistych pól odtworzonego
sprite’a. Starszy harness zachowywał cache ostatniej publikacji50d5f0;
przy odtwarzaniu zasobu jego klatka może różnić się od klatki zapisanej
w sprite+45. Nowy import odtwarza zapisaną klatkę i współrzędne. To nie
jest nowa walidacja pikseli lub renderera Unity.

Fixture:`4de52138da52a6a330c2f16f2cd173f5d43c63ee6b9020506e155cb5ac025bac`.
4 testy celowane PASS,0skip,88.364s,w tym świeży x86 i1287 przypadków zegara.
Cztery mutanty wykryto:zła bramka,zachowanie odrzuconego deferred,zły warunek
counter i przesunięty offset. Pełnego discovery nie powtarzano;292 testy.

ShippingDLL przechodzi te same15096 porównań i10 API oraz regresje:
świat5388,busy-world5088,busy-actor9984,live10827,prepared6795,ownership2486
i130 wejść planera. Unity6000.3.27f2 Windows64Mono:152960043B,0/0.
DLL:`f3dd1ee9c7064de4a7abeb42adad18a7e59f25120d09901c9d89d8c5591fad69`.
Pierwszy build zachowano osobno;końcowy obejmuje doprecyzowane granice profilu.

Ten kod jest w pełni zgodny z istniejącym `SingleStepClock` i nie narusza
deterministycznego stanu w opisanym i przetestowanym zakresie.73C#/131meta;
zmieniono1 C#,72 dawne bez zmian.275 plików przed/po buildzie,
78Resources/10 stagingów/9 oryginalnych wejść bez zmian.

## Granice tego etapu

To import **ruchu normalnych zdrowych lokalnych statków**,nie pełny obiekt
lub save/load. Inne task-families,tablice celów walki,inne sprite’y,konflikty
kohorty i obce profile są odrzucane. Import UI,assetów i całego świata
nie jest zaimplementowany. Odtworzenie blokującego stanu zostało wykonane
w testach czystego C# i rzeczywistym shippingDLL na Mono hosta;nie uruchamiano
nowej ścieżki ładowania zapisu w playerze. Nie odblokowano Shift lub Start.

Następnie:wpiąć odtwarzanie do kontrolowanej kohorty świata i istniejących
adapterów póz/kolejki głębi,z jawnym odtworzeniem wspólnego kontekstu i
porównaniem x86. Nie zmieniać kolejności poczty/rejestru ani opóźnienia emisji.
Pełny Life,AI,walka,fog,audio,save/load,oprawa2026,Win11 i laptop pozostają
nieukończone lub niezweryfikowane.1920×1080/16:9/fullscreen bez zmian.
Raporty:`artifacts/ship-state-port/`. Bez publikacji,ZIP,PNG i podglądów.

Regresja playera InputSystem/Ctrl na tym samym DLL:23 punkty,69 stanów,
230 części,782 odczyty kolejki,136 publikacji,6 pakietów,exit0.
Wejście odsubskrybowane,3 właściciele póz i8 komórek zwolnione. Znany
wcześniejszy komunikat ComputeBufferGC pozostaje;0/0 dotyczy buildu.
Tylko harness testowy ustawia preexisting deferred przez refleksję;produkcja
nie otrzymała debugowego settera bramki lub deferred.
