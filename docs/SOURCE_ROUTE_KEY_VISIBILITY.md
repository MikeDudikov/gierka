# Źródłowe komunikaty Shift i grafika trasy — 2026-11-04

Istniejący `WorldPointerInput.onEvent` przekazuje teraz uporządkowane zmiany
klawiszy Shift do `ShipPointerReference`. Naciśnięcie pokazuje punkty bieżącej
zatwierdzonej grupy, zwolnienie usuwa ich grafikę. Zadanie, lista punktów,
poczta, członkostwo, siatka i licznik świata pozostają poza tym odbiorcą.
Ścieżka działa w diagnostyce z jawnym kontekstem `--ship-fleet-wave-prefixes`.

## Ślad x86

Oryginalne 4eff00 i 4e9710 wykonały rejestrację trzech akceleratorów:

| Skan | Drugi skan | Komunikat naciśnięcia | Komunikat zwolnienia |
| --- | --- | --- | --- |
| 29 | 46 | 163, parametr 0 | brak |
| 42 | 0 | C45D, parametr 1 | C45D, parametr 0 |
| 54 | 0 | C45D, parametr 1 | C45D, parametr 0 |

Dwa ostatnie rekordy odpowiadają Shift. Pierwszy rekord jest osobnym
akceleratorem; nie zastępuje dotychczasowego Ctrl z kliknięciem myszy.

Rekord ma 74 bajty. W komunikacie rejestracji jego wskaźnik znajduje się pod
msg+14, nie msg+18. Początkową błędną obserwację zerowego bufora zachowano,
a walidator wymaga konkretnych skanów, kodów komunikatów i parametrów.
Usuwanie akceleratorów zachowuje odwrotną kolejność rejestracji.

4eff00 zapisuje parametr C45D w BaseSystem+20 i wywołuje metodę wirtualną +18
z kopertą `[0,0,100h,3,C45D,value,0,0]`. Dla C45E przy niezerowym przechowanym
stanie wywołuje odbiorcę +20 z kopertą C45D(0), nie zerując przechowanego pola.
Odbiorcy wirtualni i globalny rejestr 540540 są w tym dowodzie granicami;
nie wykonywano odpytywania urządzenia systemowego ani całej aplikacji.
C45E nie ma jeszcze podłączonego źródłowego producenta w adapterze.

Korpus `source_key_visibility.json` ma dziesięć operacji. SHA256:
`470fbee7542cf8f5552447f0cf1ee24ff9e4b871a5d17e9bea3b67e9c17f033e`.
Wykonano świeżą walidację oryginalnych instrukcji, nie tylko odczyt pseudokodu.
Znaczniki pokazuje/usuwa istniejąca ścieżka odtworzona z 4a2050/4ced10/4cef10.

## Integracja

Nie dodano nowego Update, managera, ECS lub systemu ticków. Zmieniono dwa
istniejące pliki C#: mostek zdarzeń i odbiorcę prezentacji. Przechowywany stan
klawisza należy do prezentacji. `SingleStepClock`, `ShipWorldStep`, zadanie,
członkostwo, zajętość i kolejka sprite'ów pozostają identyczne bajtowo.
Zasoby Unity, ich meta, manifesty i wszystkie dziewięć oryginalnych wejść
również pozostają bez zmian.

Snapshot zmieniający naraz oba klawisze Shift nie niesie kolejności pierwotnych
zdarzeń. Ograniczony adapter jawnie odrzuca taki przypadek przed przekazaniem
komunikatów. Nie wymyśla kolejności. Osobny replay prawego Shift oraz szerszy
cykl urządzeń i źródłowego rejestru są kolejnymi krokami.

## Wyniki

Cztery odrębne procesy Windows przez Wine przeszły pełne porównania:

| Profil | Pozycja floty | Punkty kontrolne | Stany aktorów | Publikacje | Odczyty markerów | Koperty klawiszy |
| --- | --- | --- | --- | --- | --- | --- |
| Grupa zatwierdzona | pierwsza | 33 | 99 | 299 | 14 | 4 |
| Grupa zatwierdzona | ostatnia | 33 | 99 | 299 | 14 | 4 |
| Pierwszy Shift | pierwsza | 35 | 105 | 291 | 22 | 4 |
| Pierwszy Shift | ostatnia | 35 | 105 | 291 | 22 | 4 |

Przy pierwszym Shift zwolnienie klawisza w kroku 50 usuwa grafikę przed
prawym przyciskiem myszy. Ctrl nie odtwarza znaczników. Ponowne naciśnięcie
Shift w kroku 200 odtwarza dwa znaczniki jeszcze przed obsługą duplikatu.
Duplikat sam nie tworzy grafiki, ale nadal odświeża task+8.

Przy zatwierdzonej grupie zwolnienie Shift usuwa grafikę przed zdarzeniem
normalnego rozkazu w kroku 85. Zgodne są numery, pozycje, oryginalne sloty,
kolejność rysowania, nagłówki zadania oraz wszystkie pakiety i stany świata.
Checker odrzuca brak komunikatu klawisza i brak odtworzenia trasy, oprócz
wcześniejszych usterek poczty, punktów i renderowania.

Przeszło siedem wybranych testów bez pominięć: świeży x86, dwa testy nowego
runtime i cztery historycznych profili bez globalnego C45D. Historyczne logi
nie zostały przepisane pod nowe oczekiwania. Discovery: 340, bez pełnego run.

Build Unity 6000.3.27f2, Windows64Mono: 153598683 bajty, 0 ostrzeżeń, 0 błędów.
DLL SHA256: `910293df07d49b8938416128ca0343b6694ce17a2dd155185bc5c420b3852ee0`.
Na tej DLL porównano też 1200 stanów pierwszego Shift, 7344 starszej kolejki,
1224 dostępnego normalnego celu, 16608 świata i 7248 normalnego ponownego ruchu.
Wszystkie pakiety po starcie generuje C#; nie wstrzykuje się ich z wyników x86.
Raporty i pełne logi: `artifacts/queued-key-visibility`.

Ten kod jest w pełni zgodny z istniejącym `SingleStepClock` i nie narusza
zweryfikowanego deterministycznego stanu. Stwierdzenie dotyczy opisanych
scenariuszy i nie oznacza ukończenia całej gry.

Nadal obowiązuje 1920×1080/16:9/ExclusiveFullScreen. Próby używają syntetycznych
zdarzeń InputSystem; nie potwierdzają routingu klawiatury/myszy systemowej,
Windows 11, laptopa, końcowej oprawy 2026 lub pełnego App/Life/AI/Start.
Nie generowano nowych obrazów lub ZIP, niczego nie publikowano.
