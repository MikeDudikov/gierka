# Izolowana gałąź zegara — dowód i kontrakt

Stan: 2026-11-02. Nie jest to kompletny zegar rozgrywki. Dodano czystą regułę
`SingleStepClock.Begin/Complete` w katalogu runtime Unity; nie podłączono jej
do `Update`, `FixedUpdate`, scen ani bramki AI. Odtworzenie wyboru trybów,
pauzy, sieci i replay nadal pozostaje otwarte.

## Źródło i granice fragmentu

Badany `ancient.exe` ma SHA-256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
VA `0x520352` znajduje się w `PlaySystemClassTy::Life` (`0x51fdb0`).
Fragment kończy się skokiem do wspólnego połączenia `0x5209e2`.
Zakres bajtów `[0x520352, 0x5203f7)` ma offset pliku `0x120352`, długość
165 i SHA-256 `db03994267e6be4d4f0e1dff9871c8eb5e665e752c7786495d1370c301e20cfd`.
To odczyt oryginalnych instrukcji, nie odzyskany kod C++.

Przed wejściem oryginalna funkcja sprawdza m.in. następujące pola:

| Pole | Warunek ścieżki prowadzącej do badanego fragmentu |
| --- | --- |
| `app+0x322d` | zero, inaczej powrót z całej funkcji |
| `GameSystem+0x17e6` | zero, inaczej inna gałąź aktualizacji |
| `app+0xd7c` | niezero |
| `app+0x30d9`, `app+0x30de` | nie jednocześnie bajt 2 i niezerowy dword |
| `app+0x1a11` | zero |
| `this+0x4f`, `GameSystem+0x17ea`, `this+0xee` | wszystkie zero |

Nie nadano tym polom nazw „pauza” lub „multiplayer” bez dowodu ich pełnej
semantyki. Test zaczyna się dopiero po tych warunkach i nie weryfikuje wyboru
gałęzi. Bazowy odczyt czasu następuje wcześniej przez `0x5417d0`; reguła
przyjmuje przechwyconą wartość 32-bitową jako argument i nie wybiera nowego
źródła czasu ani częstotliwości.

## Zachowanie instrukcji

| VA | Potwierdzone działanie |
| --- | --- |
| `0x520352–0x520368` | Indeks `0x5ca556`, kwant `0x5bed74 + index*24`; odejmowanie 32-bitowe, `CDQ`, następnie **signed `IDIV`** |
| `0x52036f–0x520377` | Iloraz zapisany do `this+0xe2`; zero pomija krok |
| `0x52037d–0x520389` | `CMP` i **unsigned `JBE`** ograniczają każdy niezerowy iloraz do 1, także ujemny |
| `0x52038c–0x52039a` | Dodanie kroku do licznika `this+0xde` z zawijaniem 32-bitowym |
| `0x5203a2`, `0x5203a9`, `0x5203b0` | Wywołania `0x521500`, `0x522850`, `0x542320`, w tej kolejności |
| `0x5203b5–0x5203c9` | Inkrementacja `app+0x344e`; wyzerowanie `this+0xe2` |
| `0x5203cc–0x5203ec` | Ponowny odczyt **aktualnych** indeksu/kwantu i fazy `this+0xe6`; signed reszta, zachowanie fazy |

Szczegół signed/unsigned ma znaczenie: przy kwancie 40 różnica -39 nie
wywołuje kroku, ale -40 wywołuje jeden. Nie „naprawiono” tego do innej reguły.
Faza po kroku używa reszty dzielenia ze znakiem, jak C# `%` dla `int`,
a każde odejmowanie ma zawijanie 32-bitowe.

Przykłady wykonanych instrukcji dla początkowej fazy/licznika 0 i kwantu 40:

| Przechwycony czas | Żądany krok | Nowy licznik | Końcowa faza |
| ---: | ---: | ---: | ---: |
| 39 | nie | 0 | 0 |
| 40 | tak | 1 | 40 |
| 41 | tak | 1 | 40 |
| 5000 | tak | 1 | 5000 |
| -39 | nie | 0 | 0 |
| -40 | tak | 1 | -40 |
| -41 | tak | 1 | -40 |

Przestój nie powoduje w tej gałęzi wykonania wszystkich zaległych kroków.
Nie wynika z tego jeszcze zachowanie innych gałęzi lub całego oryginału.

## Podział implementacji

`Begin(capturedTime, previousTime, counter, quantum)` zwraca żądanie pojedynczego
kroku i licznik po jego przyjęciu. Jeżeli nie ma kroku, właściciel zachowuje
starą fazę i nie wywołuje `Complete`.

Po wykonaniu właściwych callbacków właściciel wywoła
`Complete(capturedTime, currentPreviousTime, currentQuantum)` z **ponownie
odczytanymi** wartościami. Rozdzielenie zachowuje kolejność oryginału, nawet
jeśli callback zmieni fazę lub prędkość. Reguła nie wykonuje callbacków ani
ich skutków ubocznych, nie przechowuje globalnego stanu i nie deklaruje
pełnej symulacji świata.

API wymaga dodatniego kwantu; nie próbuje odwzorowywać błędnej konfiguracji
z zerem/ujemnym dzielnikiem. Z oryginalnej tabeli sprawdzono dziewięć
kwantów: 13, 17, 20, 33, 40, 50, 60, 70, 80. Walidacja parametrów C# jest
granicą narzędzia, a nie twierdzeniem o oryginalnym obsługiwaniu błędów.

## Walidacja różnicowa

`tools/validate_single_step_clock.py` wykonuje bajty oryginalnego x86 w
Unicorn 2.1.4 od `0x520352` do `0x5209e2`. System operacyjny nie uruchamia
EXE. Trzy wymienione callbacki są przecięte: zapisują wywołanie, nie wykonują
oryginalnych ciał. W 63 przypadkach pierwszy callback celowo zmienia fazę
i/lub indeks prędkości, by sprawdzić powtórny odczyt przed obliczeniem fazy.
To wstrzyknięcia testowe, nie twierdzenie, że konkretna misja dokonuje takich
zmian.

Skompilowano **rzeczywisty plik C# z projektu**, nie kopię reguły w Pythonie.
Użyto Mono z przypiętej instalacji Unity i `/checked+`, więc poprawne
zawijanie wymaga jawnego `unchecked` we właściwym kodzie.

Wynik: **1287/1287** zgodnych porównań żądania kroku, licznika i końcowej
fazy. Zestaw obejmuje wszystkie dziewięć kwantów, progi przed/na/po kroku,
duży przestój, ujemne różnice, granice `int`, zawijanie przechwyconego czasu,
liczniki 0/uint32 max oraz zmiany stanu w callbacku. Cztery odrębne kontrole
C# potwierdzają odrzucanie niepoprawnego kwantu.

Dodatkowo wyłącznie po stronie x86 sprawdzono kolejność callbacków, wskaźnik
`this`, wartość kroku 1 w czasie ich wywołania, końcowe zero w `this+0xe2`
i inkrementację licznika aplikacji. Te efekty nie są przypisywane czystemu
API C#.

Raport z wejściami, wynikami i hashami źródeł:
`artifacts/binary-analysis/single-step-clock-validation.json`.

```sh
.venv/bin/python tools/validate_single_step_clock.py \
  --output artifacts/binary-analysis/single-step-clock-validation-new.json
.venv/bin/python -m unittest tests.test_single_step_clock -v
```

Narzędzie odmawia innego SHA-256 oryginału i nadpisania raportu. Testy
pomijają porównanie jawnie, jeśli brakuje prywatnego EXE lub narzędzi;
niezgodność kodu/wyniku jest błędem. W bieżącym środowisku niczego nie
pominięto. Pełna pętla, decyzje AI, replay, pauza, sieć i działanie na
Windows 11 pozostają poza zakresem tej walidacji.
