# Prawy Shift w działającym InputSystem — 2026-11-04

Odrębny replay potwierdził gałąź `Keyboard.rightShiftKey`. Sam parametr
uruchomienia nie jest dowodem: mostek zapisuje nazwę faktycznie odczytanego
`KeyControl`, a checker porównuje ją z oczekiwanym klawiszem.

Istniejący `ShipFleetMoveInputReplay` przyjmuje diagnostyczny parametr
`--ship-pointer-right-shift-replay`. Domyślny wariant nadal emituje LeftShift.
Nie dodano nowego sposobu aktualizowania gry. Kod mostka jedynie raportuje
odczyt przed przekazaniem tego samego źródłowego komunikatu C45D(1/0).
Wiązania skanów 42 i 54 pochodzą z wykonanej rejestracji x86 4e9710.

## Wyniki na jednym buildzie

| Próba | Pozycja floty | Punkty kontrolne | Stany aktorów | Publikacje | Markery | Koperty C45D | Kontrolki klawiszy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RightShift, grupa zatwierdzona | pierwsza | 33 | 99 | 299 | 14 | 4 | 4 RightShift |
| RightShift, pierwszy Shift | ostatnia | 35 | 105 | 291 | 22 | 4 | 4 RightShift |
| LeftShift, pierwszy Shift | pierwsza | 35 | 105 | 291 | 22 | 4 | 4 LeftShift |

Wszystkie procesy zakończyły się kodem 0. Zachowanie zadań, nagłówków, poczty,
aktorów i slotów grafiki pozostało zgodne z x86. Checker odrzuca podmianę
RightShift na LeftShift nawet przy identycznych wartościach bool i kopertach
C45D. Pozostałe kontrole obejmują pocztę, kolejność, punkty i odtworzenie grafiki:
osiem dla grupy zatwierdzonej i dziewięć dla pierwszego Shift.

Przeszło osiem wybranych testów bez pominięć: sześć wcześniejszych profili
oraz dwa testy nowego runtime. Discovery: 342; bez pełnego run.
Raporty: `artifacts/right-shift-input`.

Unity 6000.3.27f2, Windows64Mono, 153599195 bajtów, 0 ostrzeżeń, 0 błędów.
DLL SHA256: `c650a6eda46ba0dbfac6528ed03fcb878df80be6b0092d332d27540605f2565b`.
Na tej DLL porównano 1200 stanów pierwszego Shift, 7344 starszej kolejki,
1224 dostępnego celu, 16608 świata i 7248 normalnego ponownego ruchu.

Zmieniły się dwa istniejące pliki C#: replay i odczyt diagnostyczny mostka.
Odbiorca prezentacji, cały rdzeń symulacji, zasoby i meta pozostały bez zmian.
Ten kod jest w pełni zgodny z istniejącym `SingleStepClock` i nie narusza
zweryfikowanego deterministycznego stanu w opisanych scenariuszach.

## Następny dowód źródłowy

Zlokalizowano producenta C45E: funkcja 4ee900. Przy zerowym DWORD pod +20
wywołuje 4efd60, następnie wysyła C45E, potem 14A z wartością 15 w polu +0C koperty. To pole routingu komunikatu,
nie indeks grupy floty. 4efd60 pobiera
wymiary z +D91/+D95 i przekazuje prostokąt przez 540560(3,1,...).
Świeży korpus `source_key_context.json` zawiera dwanaście przypadków:
trzy wartości bramki i cztery pary wymiarów. Odbiorcy komunikatów są granicami.
Nie podłączono tej funkcji do focus/resize lub ticków na podstawie przypuszczeń.
Kolejny krok to walidacja tego protokołu i rzeczywistego odbiorcy wirtualnego.

To nadal syntetyczne zdarzenia InputSystem. Nie wykonano systemowej obsługi
klawiatury Windows 11, pełnej aplikacji ani pomiaru laptopa. Dwa jednoczesne
przejścia Shift w snapshot pozbawionym kolejności pozostają poza profilem.
Pełny Life/AI/Start, końcowa oprawa 2026 i pozostałe wcześniej zapisane braki
pozostają do wykonania. Target: 1920×1080/16:9/ExclusiveFullScreen.
Nie wygenerowano obrazów lub ZIP i niczego nie publikowano.
