# Pierwszy Shift i życie znaczników — 2026-11-04

Pierwszy Shift dla tymczasowego zaznaczenia tworzy teraz zadanie 100/2.
W istniejącej poczcie umieszcza najpierw trzy pakiety członkostwa 41, następnie
trzy rozkazy 20. Kolejny punkt i duplikat w tym samym zatrzymanym kroku 0
nie dodają pakietów. Nie czekają na odbiór 41. Zwykły pierwszy rozkaz nadal
korzysta z istniejącej formacji 100/1.

Nie zmieniono rdzenia symulacji. Cała zmiana mieści się w istniejących adapterach
wejścia, prezentacji i sprawdzaniu zasobów podczas budowania. Parametry pamięci
fali pozostają jawne: `--ship-fleet-wave-prefixes 117,117,117` jest kontrolowanym
wejściem diagnostycznym, a nie domyślnym kontraktem Windows. Bez niego Shift
pozostaje objęty wcześniejszą blokadą.

## Zachowanie oryginału

Źródłowe 518070/49ca60/4cf2c0 i niezależny świat x86 potwierdziły dwa warianty
rejestru: flota przed i po statkach. Korpus ma 400 klatek i 1200 stanów aktorów,
z pełną pocztą, zdarzeniami 310 i punktami trasy. C# generuje pakiety po starcie
samodzielnie; nie odtwarza ich z pliku x86. Dziesięć kontroli API nadal przechodzi.

Osobny korpus wykonuje dziesięć etapów źródłowej prezentacji trasy:

- Utworzenie dwóch punktów daje dwa znaczniki.
- Wyczyszczenie zaznaczenia usuwa grafikę, zachowując zadanie i punkty.
- Ctrl i kolejny Work nie odtwarzają grafiki.
- Duplikat nie odtwarza usuniętego znacznika.
- Nowy punkt tworzy wyłącznie swój znacznik, z numerem wynikającym z całej trasy.
- Jawny 4a2050(1) odtwarza wszystkie znaczniki, a 4a2050(0) usuwa je ponownie.

Wykonano oryginalne funkcje zarządzające punktami, selekcją i usuwaniem wskazań
grafiki. Niższy konstruktor i destruktor renderera są tu granicami obserwacji.
Osobny dowód konstrukcji WPMOVE i zasobów opisuje
[QUEUED_INPUT_AND_MARKERS.md](QUEUED_INPUT_AND_MARKERS.md).

Duplikat odświeża task+8 bieżącym licznikiem, choć nie zmienia listy punktów ani
nie wysyła pakietów. Zapis w 4cf2c0 następuje przed wykrywaniem duplikatu.
C# zachowuje tę właściwość; nie poprawiano jej jako zbędnego efektu ubocznego.

## Próby InputSystem

Oba końcowe przebiegi przeszły po 35 punktów kontrolnych: 105 stanów aktorów,
350 części obrazu, 1190 odczytów kolejki świata, 291 publikacji pozycji oraz
22 odczyty znaczników. Obejmują pierwszy Shift, append, duplikat, ruch,
wyczyszczenie zaznaczenia w kroku 50, Ctrl i duplikat w kroku 200.
Pole pierwszego punktu jest w kroku 50 zarezerwowane, dlatego duplikat klikany
myszą sprawdzono dopiero po jego zwolnieniu. Nie obchodzono testów zajętości.

Checker odrzuca sześć usterek: nieuprawnione odtworzenie grafiki, usunięcie
logicznej trasy, zastąpienie zadania podczas wyczyszczenia zaznaczenia,
brak pierwszego 41, przedwczesny odbiór oraz uszkodzone przywołanie grupy.
Zachowano także pierwsze nieudane przebiegi i skorygowane oczekiwania testowe.

Raporty: `artifacts/pending-queued-input`. Końcowy build Windows64Mono:
153597659 bajtów, 0 ostrzeżeń, 0 błędów, Unity 6000.3.27f2.
DLL SHA256: `1c34891e234a59665a78c364f7c3b93a72af85a7eb01abcdb51da9fa2d626b25`.
Na tej samej DLL porównano także 7344 stany starszego korpusu Shift,
1224 scenariusza dostępnego pola, 16608 świata oraz 7248 zwykłego ponownego ruchu.

## Dokładna granica i następny etap

Te próby odtwarzają flagi rozkazów i zdarzenia selekcji. Nie podłączono jeszcze
oryginalnych globalnych akceleratorów klawiatury do prezentacji trasy.
To osobna ścieżka od flagi 4 w poleceniu ruchu. Nie należy opisywać wyników
jako zakończonej obsługi całej klawiatury lub pełnej pętli aplikacji.

W następnym kroku źródło już potwierdziło: 4eff00/4e9710 rejestrują skany Shift
42 i 54; naciśnięcie wysyła C45D z wartością 1, zwolnienie z wartością 0.
Korpus `source_key_visibility.json` ma dziesięć operacji oraz rzeczywiste
74-bajtowe rekordy rejestracji. Globalny odbiorca rejestru i odbiorcy metod
wirtualnych pozostają granicami. Nie wykonano odpytywania klawiatury systemowej.

Dalej należy połączyć te komunikaty z istniejącym mostkiem InputSystem,
bez nowego Update lub managera i bez zmiany stanu symulacji. Oczekiwania
markerów przy key-down/key-up muszą wynikać z tej ścieżki. Sam Ctrl nie
odtwarza grafiki; ponowne naciśnięcie Shift może to zrobić przez C45D.

Ten kod jest w pełni zgodny z istniejącym `SingleStepClock` i nie narusza
zweryfikowanego deterministycznego stanu: potwierdzają to porównania x86 oraz
niezmienione pliki rdzenia. Nie jest to deklaracja ukończenia całego remake'u.
Pełny Life/AI/Start, edycje 300/311, raport 40, historia sterty, finalna oprawa
2026, Windows 11 i docelowy laptop pozostają do wykonania. Nadal obowiązuje
1920×1080/16:9/ExclusiveFullScreen. Bez publikacji, nowych ZIP i podglądów.
