# Własność zadania i zdarzeń grupy — 2026-11-04

**Historyczny etap rdzenia.** Aktualne połączenie z wybraną gałęzią zegara
świata:[SHIP_WORLD_STEP.md](SHIP_WORLD_STEP.md). Wyniki poniżej dotyczą
poprzedniego DLL;UI Shift i busy20 nadal wymagają dalszej pracy.


Rozszerzono istniejący `ShipFleetMembership`. Każda grupa posiada teraz własny
`ShipFleetNormalTask`, licznik pracy i wektor członków zachowujący dawny ogon.
Nie utworzono nowego menedżera, ECS, zegara ani pętli Unity. Jedynym zmienionym
C# jest `ShipFleetMembership.cs`;pozostałe71 C# pozostają bez zmian.

To kolejny etap **funkcjonalnej inżynierii wstecznej**. Źródłami są oryginalny
kod maszynowy, dekompilacja i testy x86, nie nieistniejące pliki C/C++.
Komentarze nowych metod wskazują procedury i offsety. Zgodność dotyczy
obserwowalnych stanów i pakietów w określonych warunkach.

**Nowa własność jest połączona w rdzeniu C#, ale nie jest jeszcze wywoływana
przez zegar świata i sterowanie.** W playerze pozostają pierwszy normalny
rozkaz floty i Ctrl. Shift zatwierdzonej grupy, kolejne/queued/busy rozkazy
i zwykły Start nadal mają blokady. Pełna gra i oprawa2026 są w budowie.
Cel nadal1920×1080,16:9,pełny ekran na Windows11.

## Mapowanie zachowania

| Procedura/offset | Odtworzona reguła |
| --- | --- |
|49b990;grupa61B |Własny licznik+8,zadanie+25,kolejka32B+2d,wektor członków+31. |
|49ca60 |Zatwierdzenie uporządkowanego wyboru tworzy nową grupę i przenosi członków. Usunięcia z dawnych aktywnych zadań generują311. Nowa grupa nie ma jeszcze zadania. |
|49bd60 |Ten sam cel grupy zwraca obecny indeks bez41. Przeniesienie:usunięcie ze starej grupy,potem noweUI5c,41 i indeks nowego członka. **Nie dodaje300.** |
|4a1340 |Osobne powiadomienie300 z counter,indeksem iID,jeśli zadanie posiada kolejkę. Nie tworzy członkostwa ani41. |
|49bef0→4a1770 |Zapis311 ze starym indeksem i bieżącą komórką **przed** resetem indeksu/UI,41−1 i przesunięciem wektora. |
|55b490→4cc590 |Logiczna liczba maleje,ale ogon nie jest zerowany. Szybkie rozwiązanie300 może nadal odczytać usuniętego aktora przez dawny slot. |
|49bef0 — lokalny tryb |Pusta grupa pozostaje. Funkcja zwraca **0 także po skutecznym usunięciu**;1 oznacza usunięcie grupy w wyłączonej gałęzi. |
|4ccc30 |Żądanie trafia do zadania konkretnej grupy;członkowie są odczytywani przez jej ordinale rejestru. |
|4c4f40→4ccd80 |Jawny krok pracy aktualizuje wyłącznie licznik i zadanie wskazanej grupy. Bez zadania zwraca przed dostępem do aktorów. |
|4a1c60/4cc4c0 |Czyszczenie zadania nie resetuje wieku ani wektora członków grupy. Anulowanie selekcji pozostaje inną operacją. |
|50c970 —41 |Symulacyjne5e zmienia się dopiero przy jawnym odbiorze kolejnego pakietu41;UI może być wcześniej. |

`Slots.Count` jest liczbą znanych zapisanych slotów, a nie źródłową
pojemnością alokacji. `Count` odpowiada liczbie logicznych członków.
Ta reprezentacja przechowuje wszystkie zapisane pozycje wymagane przez300,
z zachowaniem ich wartości po przesunięciach. Nie odczytuje niezainicjalizowanej
pamięci. Logical lookup i retained-slot lookup są osobnymi operacjami.

Komórki i stan fizyczny pochodzą z jawnego, kompletnego rejestru w źródłowej
kolejności. Nie powstała druga kopia autorytatywnego ruchu. Starszy
`CommitPending(ids)` pozostaje zgodny dla grup bez zadania. Przenoszenie
z aktywnego zadania wymaga wariantu z bieżącym counter i rejestrem;bez nich
wywołanie zostaje odrzucone **przed zmianami**, zamiast wymyślać pozycję311.
`AddToGroup` i `NotifyMemberAdded` pozostają oddzielne jak49bd60 i4a1340.

## Dowód behawioralny

Nowy oracle wykonuje członkostwo, zdarzenia, zadania i odbiór41 w **jednym
emulatorze oryginalnego x86**.262 przypadki obejmują2486 punktów kontrolnych
i3960 stanów grup. Wszystkie3098 pakietów są zgodne co do adresata,
kolejności i bajtów:1566×41,1523×20,9×35.26 kontroli API.
Wśród przypadków jest225 par uporządkowanych niepustych wyborów0b/0c/0d,
kilka aktywnych grup, przejścia do nowych grup, powrót do starej, nieaktualne
indeksy, usunięcie wszystkich członków, zachowany ogon, zmieniona komórka,
osobne300, jawny odbiór41, czyszczenie i przepełnienie licznika.

Fixture `ship_fleet_group_tasks.json`,SHA256
`48832345adada86d26d2c5ed308d1dcb7dbf81a4646590fdd9f8314499e18719`.
Porównania używają checked+/warnaserror+. Test dodatni ponownie wykonuje
świeży oryginalny x86.13 testów celowanych PASS,0skip,350.891s,
w tym3 nowe i10 regresji. Siedem mutacji wykryto:utrata ogona,błędny
indeks311,automatyczne300,zły właściciel zdarzenia,reset wieku,
wspólny licznik grup i błędny wynik usunięcia. Pełnego discovery nie
powtarzano;historyczne274PASS dotyczą poprzedniego etapu. Nowy zestaw
ma277 testów.

Rzeczywisty shippingDLL również przechodzi2486 nowych punktów i26 API.
Na tym samym DLL zachowano2175 stanów członkostwa/23 API,1287 stanów
odbioru rozkazów/13 API,360 stanów Ctrl oraz778 stanów normalnego zadania/20 API.
Łącznie7086 porównań w tych pięciu zestawach.
DLL `80f9228368a20ccff99c9970647654936b7987daed707d35bbf74803e62d99e5`.
Build Unity6000.3.27f2 Windows64Mono:152945003B,0 błędów/0 ostrzeżeń.

Regresja playera przez InputSystem:23 punkty,69 stanów,230 części,
782 rzeczywiste odczyty kolejki,136 publikacji,6 pakietów i exit0.
To wcześniejszy pierwszy rozkaz i Ctrl, **nie nowy runtime pracy grupy**.
Własne wejście,3 właściciele póz i8 zajęć komórek zwolnione. Znany komunikat
ComputeBuffer przy zamykaniu występuje też w poprzednich logach.
Nie generowano PNG, ZIP ani podglądu;nie ma nowej deklaracji UI RGB0.

## Granice i zgodność architektury

Fazy, counter, pending, teren, komórki i stan fizyczny są jawnymi wejściami.
OperacjaQ dostarcza kolejne **41**, bez dostarczania20/35. Nie jest dowodem
pełnego globalnego FIFO kontrolnego ani kolejności całego świata.
Nie wykonuje się aktorowego Work, renderera oryginału ani całego Life.
Warunki:lokalne normalne statki wodne,patrol off,zerowe watch,bez kolejki100/2
i bez raportów przerwanych zadań40. Dotychczasowe ograniczenia formacji zostają.

Warstwa korzysta z istniejącego modelu jawnych kroków `SingleStepClock`,
rejestru `ShipMoveOrder` i siatki `MissionOccupancyGrid`. Nie zmienia tych klas,
źródła czasu, arytmetyki całkowitoliczbowej, RNG ani kolejności fizyki.
Nie dodaje ścieżek do zasobów, liczb zmiennoprzecinkowych lub mechanik.
Zgodność z istniejącymi klasami i zachowanie deterministycznego stanu
potwierdzono w powyższym zakresie;nie jest to potwierdzenie całej gry.
Sceny,prefaby,pakiety,ustawienia,72C#/130meta i10 stagingów pozostają w tej
samej architekturze;zmieniono1 C#,bez nowych plików C# lub meta.

Następnie przenieść odbiór i arbitraż ponawianego20 u zajętego aktora
(4e2ba0,4abe50,4ab250),ustalić fazy świata i dopiero wtedy połączyć UI Shift.
Nie resetować sztucznie move-active80:zadanie100/1 nie kończy go przy celu.
Pełna gra,AI,walka,fog,audio,save/load,oprawa2026,natywny Windows11,
docelowy laptop i wydajność pozostają do wykonania lub sprawdzenia.

Raporty:`artifacts/fleet-group-ownership/`. Poprzedni etap:
[SHIP_FLEET_NORMAL_TASK.md](SHIP_FLEET_NORMAL_TASK.md).
