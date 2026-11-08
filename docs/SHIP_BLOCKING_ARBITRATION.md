# Blokujący arbitraż — dowód źródłowy,2026-11-04

Ten etap dodaje **dowody i testy x86**,bez zmiany C#,DLL lub obsługi wejścia.
Normalne ponowienia20 przy58b==0 pozostają w playerze. Obsługi blokujących
stanów nie odblokowano na podstawie samego wymuszenia bajtu w emulatorze.
Zgodność z x86 ma bezwzględne pierwszeństwo przed zmianą kolejności świata.

## Co potwierdzono

144 kontrolowane przypadki wykonują całe `4abe50→4abc60→4a6330`,a potem
rzeczywiste `4ab720`. Bez przechwytywania arbitrażu,anulowania,PostMove
lub promocji. Ciała0b/0c/0d,trasy i stan fizyczny pochodzą z oryginalnej
inicjalizacji i Work. Pozostają dotychczasowe granice inicjalizacji,heap
i renderera harnessu. Nie jest to pełny Ship::Life.

**Bramka58b,flagi pending/deferred i relacja counter do lastPlan są jawnymi,
wymuszonymi wejściami testowymi. Nie dowiedziono,że wszystkie takie kombinacje
powstają podczas zwykłej rozgrywki.** Macierz:3 aktorów,4 chwile ruchu,
bramka0/1,pending0/80/88,deferred80,counter równy lastPlan lub lastPlan+1.

| Warunek przy aktywnym80 | Wynik samego4abe50 |
| --- | --- |
|58b=0,pending80 |pending80 pozostaje,deferred0;bez anulowania |
|58b=0,pending0,deferred80 |deferred jest przenoszone do pending |
|58b=1,pending80 |po anulowaniu pending0 i deferred0;nowy rozkaz znika |
|58b=1,pending88 |pozostaje pending8,deferred0 |
|58b=1,pending0,deferred80 |deferred80 może pozostać do kolejnej promocji |

Źródło wybiera kandydata odroczenia przed anulowaniem,ale po anulowaniu
zeruje deferred,jeśli cały pending pozostaje niezerowy;następnie maskuje
pending przezfffffe0f. Nie wolno zastąpić tego kolejką zachowującą każdy rozkaz.
W144 przypadkach jest60 wejść anulowania i20 odrzuceń nowego80.
30 przypadków potwierdza zmianę stanu fizycznego:2/3→0 lub4/5→1.
Przy równym counter i lastPlan `4a6330` wraca przed tymi zmianami.
Rezerwacje i zajęcia komórek nie zmieniają się w samym badanym anulowaniu;
dalsze skutki pełnego Life nie są objęte tym twierdzeniem.

Fixture SHA256:`4a96f382f5cd7ebc893850abc689b1492247de7e600243cbb6040f06a8deed82`.
Źródłowy EXE:`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Test dodatni ponownie wykonuje x86;negatywny wykrywa sztuczne zachowanie80
w deferred po źródłowym odrzuceniu. Osobno sprawdzana integralność fixture.

## Pochodzenie bramki

Ślad zapisu z oryginalnego konstruktora dla wszystkich3 aktorów pokazuje
`4dc53a`:zerowanie4B obejmujące actor+588..58b. Końcowe58b=0.
Jest to rzeczywisty zapis instrukcji x86,nie hostowe wymuszenie pamięci.

Przegląd zdefiniowanych instrukcji Ghidry znalazł bezpośredni odczyt58b
w`4abe87`. To nie jest dowód braku innych zapisów:szersze kopiowanie lub
arytmetyka wskaźnika mogą obejmować ten bajt. Szerszy eksport pokazuje m.in.
`4e2180`:kopiowanie0x85B z bufora+503 do obiektu+54c.58b odpowiada tu
buforowi+542. Jest to analiza statyczna funkcji odtwarzania stanu,**nie**
wykonany test pełnego importu,save/load lub dowód niezerowej wartości w misji.
Równe przesunięcia588 w innych klasach lub buforach nie oznaczają tego samego pola.

Następny krok:wykonać źródłowy zapis/odtworzenie bloku stanu i prześledzić
wartość58b,pozostałe bramki zadań oraz skutki anulowania przez następne Work.
Dopiero ten dowód uzasadni rozszerzenie modelu runtime. Nie dodawać pola,
settera lub nowej globalnej fazy wyłącznie dla wymuszonych stanów testowych.

Raporty:`artifacts/blocking-arbitration/`. Nowe narzędzia:
`probe_ship_blocking_arbitration.py`,`validate_ship_blocking_arbitration.py`.
Dotychczasowy build i ograniczenia:[SHIP_BUSY_ORDERS.md](SHIP_BUSY_ORDERS.md).
Cel1920×1080/16:9/fullscreen bez zmian. Pełna gra,oprawa2026,Win11 i laptop
nadal nieukończone lub niezweryfikowane. Bez publikacji,ZIP,PNG i podglądów.
