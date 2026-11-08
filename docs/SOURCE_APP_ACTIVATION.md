# Dezaktywacja aplikacji i jawny reset trasy — 2026-11-04

Ukończono następny etap po [rozwiązaniu odbiorcy BaseSystem](SOURCE_BASE_DISPATCH.md):
wykonanie źródłowej gałęzi WM_ACTIVATEAPP oraz port stanu widoczności trasy.
Nowe wejście kontekstowe działa w kontrolowanym replayu. Zwykły mostek
klawiatury nadal używa istniejących zdarzeń InputSystem.

## Dowód x86

Oryginalne `4ee970` obsługuje komunikat `1C` jako WM_ACTIVATEAPP.
Niezerowy parametr aktywności wybiera aktywację; zero wybiera dezaktywację.
Wykonano 96 przypadków obejmujących obie bramki, zapisany stan Shift,
obecność kontekstu grafiki, obecność sceny i parametr FFFFFFFF.

Przy aktywacji źródło czyści bit100 w kontekście grafiki, przywraca ustawienia,
opcjonalnie scenę, zapisuje App+329d=1 i wybiera kursor835. Przy dezaktywacji
ustawia bit100, sprawdza dźwięk, wywołuje4ee900, zapisuje App+329d=0, a następnie
wybiera kursor7F00. C45E nie jest wysyłane przez gałąź aktywacji.

Obsługa pustego rejestru dekodera540b00, flagi grafiki, wyłączona konfiguracja
audio i łańcuch C45E wykonują oryginalne instrukcje. Importy kursora i przywrócenie
sceny są jawnymi granicami. Nie wywoływano fizycznych zdarzeń systemu operacyjnego.
Cztery mutacje x86 wykryły odwrócenie aktywności, brak producenta resetu,
błędną flagę po dezaktywacji i błędny zasób kursora.

Osobny test wykonuje już cały łańcuch aż do floty:
`4ee900 →540540/540560 →4eff00 →541ee0/541f00 →49ab30 →4a2050 →4cef10`.
Zablokowana aplikacja oraz nieaktywna rejestracja zachowują oba znaczniki.
Skuteczny reset usuwa oba, kolejne wywołanie niczego nie wysyła. Nagłówek
zadania, zdarzenia, wiek grupy, członkostwo, trzy rejestracje członków oraz
logiczne punkty trasy pozostają identyczne. Granicą pozostaje konstrukcja
i destrukcja obiektu grafiki, nie logika usuwania znacznika z trasy.

## Port i integracja

`SourceRouteKeyVisibility` jest małą strukturą czystego C#. Przechowuje pełne
słowo uint ze źródłowego BaseSystem+20. Odtwarza C45D, rekurencyjne C45E oraz
projekcję bramek producenta: App+20 równy0 i rejestracja równa dokładnie1.
Nie scala stanu aplikacji z fizycznymi klawiszami. Porównano150 stanów C#
z obserwacjami x86 i wykryto pięć celowych błędów portu, także normalizację
FFFFFFFF do bool i traktowanie dowolnej niezerowej rejestracji jak aktywnej.
To samo porównanie przeszła DLL wyprodukowana przez Unity.

Istniejący `ShipPointerReference` używa tej struktury dla dotychczasowych
zdarzeń Shift. Jawny `ReceiveSourceRouteContext` przekazuje skuteczny reset
do tej samej ścieżki prezentacji. Metoda wymaga zatrzymanego, kontrolowanego
profilu. Dodatkowy przełącznik replaya to `--ship-pointer-source-context-replay`,
używany razem z wcześniejszym profilem pierwszego Shift i jawnymi prefixwords.
Nie zmieniono `WorldPointerInput.OnApplicationFocus` ani nie przypisano mu
automatycznie całej semantyki oryginalnego WM_ACTIVATEAPP.

Projekcja dotyczy wyłącznie widoczności. Nie udaje portu przywracania audio,
DirectDraw, prostokąta17 lub odbiorcy14A. Są to osobne części oryginalnej aplikacji.

## Walidacja playera

Build Unity6000.3.27f2, Windows64Mono:153601435 bajtów,0 błędów i0 ostrzeżeń.
DLL SHA256: `670bf3055166d56115afc3e85e9d1e6ff812f991ec7ce956222aea2baedf173c`.

| Profil | Flota w rejestrze | Checkpointy | Stany aktorów | Publikacje | Odczyty markerów | Konteksty |
| --- | --- | --- | --- | --- | --- | --- |
| Lewy Shift i reset | pierwsza | 39 | 117 | 291 | 26 | 4 |
| Prawy Shift i reset | ostatnia | 39 | 117 | 291 | 26 | 4 |

Każdy profil sprawdza390 odczytów części statków,1326 odczytów kolejki renderera,
pięć kopert widoczności i cztery rzeczywiste KeyControl. Trzynaście mutacji
logu jest odrzucanych przez checker, w tym utrata resetu, błędna bramka,
przesunięcie ticka i zachowanie starego słowa klawisza.

Wszystkie cztery operacje kontekstu odbywają się w zatrzymanym ticku50.
Porównywane są pełne rekordy świata, poczta, stany aktorów, nagłówki zadania,
punkty, wybór i kolejka. Reset zmienia wyłącznie grafikę znaczników i słowo
widoczności. Fizyczne zwolnienie Shift po resecie nadal wysyła C45D(0), tak jak
oryginał, choć stan już wynosi0. Nie odtwarza się ani nie usuwa logicznej trasy.

Na tej samej DLL przeszło także33624 stanów aktorów z pięciu wcześniejszych
zestawów:1200 pierwszego Shift,7344 kolejki UI,1224 dostępnego celu,
16608 pełnego kontrolowanego kroku świata i7248 normalnego ponownego ruchu.

Ten kod jest w pełni zgodny z istniejącym `SingleStepClock` i nie narusza
zweryfikowanego stanu deterministycznego. Sam Clock, ShipWorldStep,
ShipFleetMembership, MissionOccupancyGrid i kolejki sprite'ów pozostają bez zmian.
Zmieniono dwa wcześniejsze pliki C#, dodano jeden plik C# i jego meta.
Wszystkie80 plików Resources, sceny, pakiety i ustawienia zachowano.

## Ograniczenia i zachowane błędy diagnostyki

Pierwszy import nie powiódł się przez33-znakowy GUID nowego meta; poprawiono
go do32 znaków i ponowiono rzeczywisty build. Pierwszy test pomocniczy błędnie
oczekiwał0 rejestracji trasy zamiast zmierzonych3; poprawiono oczekiwanie i test
przeszedł. Walidator DLL początkowo nie podawał referencji netstandard;
naprawiono uruchomienie zgodnie z istniejącymi walidatorami. Nie zmieniano
danych x86 ani reguł gry, aby obejść te błędy. Nieudane logi są zachowane.

W playerze nadal występuje wcześniejszy komunikat Unity o zwalnianiu
ComputeBuffer przez GC, obecny także w obu poprzednich replayach Shift.
Nie jest nową regresją tej zmiany. Kontrole zwolnienia zasobów właścicieli
prezentacji i odpięcia wejścia pozostają częścią checkera.

Nie potwierdzono natywnego Windows11, wydajności wskazanego laptopa,
fizycznego wejścia OS, całej gry, pełnego AI/Start/Life ani końcowej oprawy2026.
Obowiązuje1920×1080/16:9/pełny ekran; w obu sesjach geometria playera to
X=0,Y=0,WIDTH=1920,HEIGHT=1080. Prefix117 pozostaje kontrolowanym wejściem
profilu Wine, nie domyślną własnością gry lub Windows.

Raporty i logi: `artifacts/source-app-activation`. Nie generowano obrazów
lub paczek ZIP, niczego nie publikowano. Kolejny krok: usunąć blokadę poprawnej
instalacji oryginału w prywatnym gościu, używając danych instalatora i bez
wymyślania wpisów rejestru. To umożliwi szersze pomiary rzeczywistej aplikacji.
