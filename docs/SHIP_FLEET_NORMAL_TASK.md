# Normalne zadanie grupy100/1 — historyczny etap2026-11-03

Nowsza własność grupy:[SHIP_FLEET_GROUP_OWNERSHIP.md](SHIP_FLEET_GROUP_OWNERSHIP.md).
Rdzeń zadania poniżej pozostaje bez zmian;aktualne testy/build w[VALIDATION.md](VALIDATION.md).

Dodano czysty moduł `ShipFleetNormalTask`: żądanie i ponowne użycie zadania,
przydziały celów, źródłowe zdarzenia32B oraz okresową pracę grupy.
**Moduł jest w buildzie, ale nie jest jeszcze podłączony do zegara świata ani
sterowania.** W playerze nadal obowiązuje pierwszy normalny rozkaz i Ctrl;
kolejne/queued/busy polecenia i Shift zatwierdzonej grupy pozostają blokowane.
Zwykły Start i pełna gra pozostają w budowie. Docelowo1920×1080,16:9,
pełny ekran na Windows11;oprawa2026 jest osobnym nieukończonym etapem.

## Odtworzone reguły

| Źródło | Zachowanie |
| --- | --- |
|4cc500/4ccc30 |100/1 ma101B. Kolejne żądanie aktualizuje cel i counter, zachowując przydziały i wiek grupy. |
|4cc7d0 |Przydział20B jest aktualizowany po ID lub dopisywany. Usunięcie członka nie usuwa starego przydziału. |
|4a1340 |Add300:counter,indeks członka,ID;pozostałe bajty zdarzenia zerowe. |
|4a1770/4dc600 |Remove311 zapisuje dawny indeks,ID i **komórkę**, a nie piksele renderera. |
|4cc6a0 |Zdarzenia od końca wektora.300 próbuje ponownie wyznaczyć formację całej aktualnej grupy;311 jest tylko usuwane z kolejki. |
|4cc590/55b490 |Szybki odczyt dawnego slotu poprzedza szukanie ID w aktualnych członkach. Usuwanie nie zeruje ogona wektora;dawny slot może nadal wskazać usuniętego aktora. |
|4ccd80 |Próg to unsigned **wiek>100 przed dodaniem pending**. Bezczynny statek dostaje20 dopiero dalej niż1 komórka na którejkolwiek osi od własnego przydziału. |
|4cc6a0 — brak formacji |Dla obsługiwanego add300 wysyła20/byte255 tylko do rozwiązanego aktora, potem22B action35. Dodatni wynik obsługi zdarzeń pomija okresowy przebieg. |
|4ccd80 — zwykłe ponowienie |Używa przydziału, a przy jego braku celu zadania, zawsze z byte0. Nie dopisuje przydziału. |
|4a1c60/4cc4c0 |Jawne czyszczenie zwalnia zdarzenia i przydziały;wiek należy do grupy i pozostaje u właściciela. |

Dotarcie do celu **nie usuwa automatycznie**100/1. Praca tego podtypu nie
czyści też bezpośrednio move-active0x80. Koryguje to wcześniejsze przypuszczenie,
że sama praca grupy zakończy rozkaz0d z celem równym jego komórce.
Nie należy dodawać sztucznego zakończenia ani zdejmować blokady busy.
Źródło sprawdza stan fizyczny0, więc może ponawiać20 mimo aktywnego zadania
ruchu. Taki pakiet wymaga jeszcze portu arbitrażu zajętego odbiorcy.

`Work` przyjmuje aktualnych członków i identyfikatory źródłowych slotów,
w tym zachowany ogon wymagany przez300. Są to jawne dane właściciela grupy;
moduł nie tworzy drugiego rejestru członkostwa. Zwraca nowy licznik grupy.
`Request`/`Work` udostępniają wyemitowane pakiety bez ich dostarczania.
Enqueue nie dostarcza ani nie czyści ostatnich emisji. Payloady i rekordy
zdarzeń są zwracane jako kopie. Nieobsługiwany kontekst formacji lub raportu
przerywa przed zmianą stanu modułu.
Anulowanie zaznaczenia i Ctrl nie są czyszczeniem zadania. `Clear` odpowiada
jawnemu4a1c60;nie wolno wiązać go z ogólnym `ShipPendingSelection.Clear`.

## Dowód i granice

Oryginalne x86 wykonuje tworzenie/pracę/czyszczenie zadania, rzeczywiste
wektory, formację i serializację. Shift49e850 tworzy rzeczywiste300/311.
Fixture zawiera124 scenariusze i778 porównywanych snapshotów zadania,
316 pakietów20 oraz14 pakietów35.265 pakietów41 pochodzi z oryginalnego
upstream członkostwa;**nie jest porównaniem nowego portu Shift w C#**.
Kolejność członków, komórki, stany fizyczne i zachowane sloty są jawnym
kontekstem dla badanego modułu. Nie wykonuje on fizyki ani odbioru pakietów.

Przypadki obejmują wszystkie15 uporządkowanych niepustych podzbiorów0b/0c/0d,
mapę źródłową/zablokowaną, progi99/100/101, pending0/1/2/3/7/FFFFFFFF,
przepełnienie uint32, różnice int32/INT_MIN, stany fizyczne0..6,
tolerancję±1, zmianę celu, usunięcie wszystkich członków, powrót do grupy,
nieaktualny indeks, zachowany ogon i jawne czyszczenie.

Fixture `ship_fleet_normal_task.json`,SHA256
`f85cc3a6aa1a26304faaa5f9f746c239ee6ddb3930936d083e37185a1a849873`.
20 kontroli API;checked+/warnaserror+. Świeże x86 uruchomiono w teście
dodatnim. Sześć mutacji kodu zostało wykrytych:próg,kolejność zdarzeń,
utracony ogon,wyczyszczenie przydziałów,tolerancja i payload35.
3 nowe testy PASS,0skip,55.239s. Pełny discovery:274PASS,0skip,684.534s.
Snapshoty i20 API zgodne również z
rzeczywistym shippingDLL `6d92c6590832d2ff5908b06bcc061d964662b04080fa1d850077057f55a4516f`.

Build Unity6000.3.27f2 Windows64Mono:152941931B,0 błędów/0 ostrzeżeń.
Regresja playera tego DLL:23 punkty,69 stanów,230 części,782 odczyty
kolejki,136 publikacji i6 pakietów;wybór,ruch,anulowanie i Ctrl,exit0.
To regresja wcześniejszego sterowania,nie runtime nowego taskWork.
Nie generowano PNG. Znany ComputeBuffer przy zamykaniu występuje też
w poprzednich logach;własne3 właściciele póz,wejście i8 komórek zwolnione.
Dodano1 C# i meta;wszystkie71 wcześniejszych C# pozostają bez zmian.
72C#/130meta,10 istniejących stagingów. Brak nowego atlasu,sceny,prefabu,
pakietu lub ustawienia. Raporty w `artifacts/fleet-task/`.

To ograniczony task100/1 dla lokalnych normalnych statków wodnych,patrol off
i zerowe pola watch. Interrupted-task report/action40 jest jawnie odrzucany;
queued100/2,AI,inne klasy i złożone zadania pozostają poza zakresem.
Oracle używa istniejących minimalnych aktorów UI z MoveOracle, nie nowych
pełnych kadłubów fizyki. Zachowuje wcześniejsze granice CRT/render/audio.
Nie jest to pełny oryginalny Fleet/App/Ship Life ani dowód tempa całej gry.

## Następny krok

Połączyć zadanie z właścicielem grupy:rzeczywiste zmiany członkostwa,
32B zdarzenia i zachowane sloty. Następnie ustalić kolejność faz oryginalnego
świata i przenieść arbitraż ponawianego20 do zajętego odbiorcy. Dopiero po
porównaniu tych granic odblokować Shift i kolejne rozkazy w diagnostyce.
Punkty wejścia odbiorcy są już wyeksportowane:4e2ba0 dla20 tworzy pending80,
4abe50 arbitruje stare i nowe zadanie,a4ab250 promuje zapis. Sam warunek
fizycznego state0 nie zastępuje tych procedur. Materiał w
`artifacts/movement/orders/export-arbitration` i `export-consumer`.
Pełna gra,AI,walka,fog,audio,save/load,oprawa2026 i natywny Windows11/laptop
pozostają nieukończone lub niezweryfikowane. Bez publikacji,ZIP i podglądu.
