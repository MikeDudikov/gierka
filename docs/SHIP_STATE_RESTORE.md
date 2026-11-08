# Odtwarzanie stanu statku — dowód x86,2026-11-04

Wykonano oryginalne procedury eksportu `4e12e0` i odtworzenia `4e2180`,
następnie32 kroki `4ab720`+`4ab930`.36 przypadków:trzy rzeczywiste kadłuby,
cztery chwile ruchu i trzy wartości bramki58b. Nie zmieniono C#,DLL lub UI.

## Wykonany dowód

-12 niezmienionych buforów źródłowych i24 buforów z kontrolnie zmienionym
  bajtem+542 na1 lub255. Oryginalny eksport miał tam0 we wszystkich przypadkach.
-Pełne procedury wykonują kopiowanie bloku85B z actor+54c do bufora+503
  i z powrotem,łącznie z58b. Bufory mają2268,2272,2276 lub2282B w tym zestawie;
  nie są stałą strukturą133B i nie wolno ignorować danych zmiennej długości.
-Oryginał kopiuje także trasę,odtwarza wektor cache oraz ponownie zgłasza
  zajęcia siatki. Wszystkie mierzone pola ruchu,rozkazów,trasy,cache,RNG,
  publikacji i zajęć siatki są zgodne przed i po odtworzeniu.
-1152 późniejsze stany są zgodne z niezależnym oryginalnym silnikiem,który
  nie wykonał importu. Kontrola otrzymuje ten sam bajt bramki bezpośrednio.
  Oba silniki dostają normalny20 do16,4. W20 przypadkach bramka blokująca
  prowadzi do wcześniej wykazanego odrzucenia nowego celu.

To dowód zachowania **procedur w kontrolowanym harnessie**,nie dowód pełnego
save/load gry lub osiągalności niezerowej bramki w misji. Zmiany+542 są
syntetycznymi wejściami. W mierzonej normalnej rozgrywce eksport nadal daje0.
Porównanie dotyczy wymienionych obserwowalnych pól,nie tożsamości wszystkich
bajtów obiektu,adresów sterty lub zasobów graficznych.

## Granice harnessu

Nie zastąpiono eksportu,odtworzenia,trasy,cache,grid,arbitrażu,promocji
lub Work. Wykonują się rzeczywiste instrukcje oryginalnego EXE o SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Zachowano dotychczasowe granice inicjalizacji,sterowania systemem i renderera.
Procedura jest uruchamiana w tym samym emulatorze co jej obiekt;nie jest
to jeszcze przenoszenie zapisu pomiędzy procesami.

Nowe granice usług:

| Adres | Zastępstwo |
| --- | --- |
|589c69 |CRT realloc:zachowanie prefiksu poprzedniej alokacji;NULL obsługiwany jak malloc. Wrapper558fd0 pozostaje oryginalny. |
|50cb80 |Tworzenie zasobu sprite’a pominięte. |
|50d4f0 |Zwrot istniejącego sprite’a kontrolowanego kadłuba. |
|4e1bb0 |Żądanie bitmap uszkodzeń pominięte. |
|4e0120,542eb0 |Wyszukiwanie zasobów graficznych poza badanym modelem. |
|50e640 |Rejestracja komunikatu systemowego poza pełnym App/Life. |

To nie jest odtworzenie zasobów lub renderera. Pierwszy pilot ujawnił brak
obsługi realloc(NULL);błąd harnessu poprawiono i zachowano pierwotny log.
Końcowy test ponownie wykonuje cały korpus x86 oraz kontrolę niezależną.

Fixture:`dd8827df6031a4f080f48cca0e042cd1135fd1aa9b3b513172d980508d6609e0`.
Raporty:`artifacts/ship-state-restore/`. Zestaw testów po dodaniu3 przypadków
ma289 testów;pełnego discovery nie wykonywano. Nie budowano nowego playera,
bo kod produkcyjny pozostaje bez zmian. Obowiązuje ostatni zweryfikowany
build normalnych ponowień20,bez obsługi blokującego arbitrażu w C#.

Następny krok:przenieść zweryfikowaną reprezentację stanu ruchu do C#,
z jawnym odtworzeniem bramki i zachowaniem kolejności obsługi pending8/80,
deferred i anulowania. Nie dodawać osobnego debugowego settera58b ani
globalnej fazy grup. Pełne save/load,inne rodziny zadań,pełny Ship::Life,
AI,oprawa2026,Win11 i docelowy laptop nadal poza zweryfikowanym zakresem.
Bez publikacji/aplikacji,ZIP,PNG i podglądów.1920×1080/16:9/fullscreen bez zmian.
