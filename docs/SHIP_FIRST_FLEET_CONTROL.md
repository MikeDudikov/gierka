# Pierwszy normalny rozkaz floty z kursora — historyczny etap2026-11-03

Nowszy rdzeń task100/1:[SHIP_FLEET_NORMAL_TASK.md](SHIP_FLEET_NORMAL_TASK.md).
Nie jest jeszcze podłączony do świata;poniższe ograniczenia UI pozostają.
Ustalenie źródłowe:normalny task nie kończy automatycznie move-active0d.
Bieżący build i testy:[VALIDATION.md](VALIDATION.md).

Nowy tryb `--ship-pointer-reference --ship-pointer-fleet-selection
--ship-pointer-fleet-movement` łączy wybór trzech lokalnych statków,źródłową
formację,pakiety41/20,promocję,ruch i renderer. Pierwsze zwykłe kliknięcie
morza lewym przyciskiem zatwierdza tymczasowy wybór. Po anulowaniu wyboru
Ctrl na statku przywołuje całą zatwierdzoną grupę.

**Zakres jest celowo ograniczony do pierwszego normalnego rozkazu.** Kolejne,
zastępujące i kolejkowane rozkazy oraz edycja zatwierdzonej grupy przez Shift
mają jawne blokady. Nie odtworzono jeszcze schedulera zadań grupy. Zwykły Start
pozostaje wyłączony;pełna gra i oprawa2026 nadal są w budowie.1920×1080,
16:9,pełny ekran całego widoku pozostają obowiązujące.

## Połączenie modułów

`ShipPendingSelection` czyta rzeczywiste członkostwoUI i kolejność członków
grupy. Ctrl wykonuje źródłowe49ecb0→49d320:deselekcja poprzedniego wyboru,
przywołanie grupy i selekcja jej członków. Zwykłe kliknięcie ponownie tworzy
tymczasowy wybór jednego aktora. Prawy przycisk na pustym polu czyści wybór.
Nie są wtedy wysyłane nowe41. Domyślny konstruktor bez czytników grup zachowuje
dotychczasową projekcję actor group−1.

`MarkCommitted` odpowiada49e230→49c250:po zatwierdzeniu znika tymczasowy
wektor,lecz selektory pozostają. Rozdzielono liczbę widocznie wybranych aktorów
od TemporaryCount. Zatwierdzenie sprawdza identyczność i kolejność członków.
Przywołanie grupy nie zastępuje jej nową grupą i nie zmienia pól symulacji.

`ShipPointerReference` korzysta z istniejącego `ShipFleetMotionReference`
jako właściciela trzech rzeczywistych kadłubów i ich animacji. Wskazywanie
używa bieżących opublikowanych pozycji oraz storedFrame każdego statku,
a ramka pomija rezerwacje wszystkich poruszających się lokalnych statków.
Publikacje przesuwają także odpowiedni selektor. Nie powielono rdzenia ruchu.

Przed pierwszym rozkazem sprawdzani są odbiorcy w idle oraz obsługiwany
kontekst źródłowej formacji. Następnie moduł członkostwa zatwierdza grupę,
a wszystkie41 trafiają FIFO przed20. Pole5e zmienia się przy odbiorze41.
Promocja i fizyka ruszają dopiero w następnym ticku. Cel pochodzi z pamięci
kursora po Move;nie jest wyznaczany ponownie z pozycji samego release.

W potwierdzonym przykładzie kliknięcie18,5 daje:

| Statek | Źródłowy cel | Payload20 |
| --- | --- | --- |
|0b |18,5 |120000000500000000 |
|0c |20,6 |140000000600000000 |
|0d |19,4 |130000000400000000 |

Większy statek0d pozostaje w swojej komórce zgodnie z formacją oryginału.
Dwa pozostałe przemieszczają się do przydzielonych celów. Nie zmieniano celu0d,
aby wymusić ruch wszystkich trzech. W bounded Work jego move-active może
pozostawać ustawione przy celu równym bieżącej komórce;dalsza obsługa wymaga
oryginalnej pracy grupy. Nie dodano sztucznego zakończenia rozkazu.

## Dowód źródłowy i runtime

| Sprawdzenie | Wynik |
| --- | --- |
| Ctrl/plain/right blank |135 scenariuszy,360 stanów rzeczywistego x86 i checked C# |
| Pierwszy obieg UI |Rzeczywiste procedury wyboru0b/0c/0d i release morza z jawnym hover emitują41×3,20×3 |
| Odbiór i ruch |606 porównanych stanów,600 wywołań ticków,136 publikacji,12 mutacji komórek,33API |
| Rzeczywisty DLL |Te same360 i606 stanów ponownie zgodne na hostowym Mono |
| Player przez InputSystem |23 punkty kontrolne,69 pełnych wierszy modelu,230 części i782 odczyty kolejki |
| Pakiety z playera |Dokładne6 adresów/akcji/payloadów,kolejność41 przed20 |
| Odtworzone interakcje |Wybór0b,Shift+0c/0d,rozkaz18,5,ruch do tick200,anulowanie,Ctrl+0c→cała grupa |
| Testy celowane |10PASS,0skip,87.778s;5 nowych i5 wcześniejszych regresji wyboru |
| Osobny checker QA |2PASS,0skip,12.195s;5 celowych błędów wykrytych |

Dowód obiegu używa **dwóch oddzielnych emulatorów źródła**:pierwszy wykonuje
cursor/fleet/formation/serializację,drugi rzeczywiste konstruktory trzech
statków,odbiór,promocję i Work/Move. Między nimi przenosi się niezmienione
pakiety i jawny stanUI. Nie przedstawia się tego jako jednego pełnego Life
oryginału. Odbiór41 i20 wykonuje rzeczywisty kod x86,tak samo jak ticki fizyki.
Test playera porównuje te granice i ich dane w działającym kodzie C#.

Fixture Ctrl:`ship_committed_selection.json`,SHA256
`28a8a56c05ed88823dc075f41b6da73f9609272e68392ee2006a0d806537ef90`.
Fixture obiegu:`ship_fleet_input_cycle.json`,SHA256
`944dfe8904be35dc60af6083ed78dccaf5b7b1e421a5f435ecf111fbbd30cd26`.
Rzeczywisty log playera:`ship_fleet_control_player.log`,SHA256
`96e0aabb53515c8f3a79dc946a431200972218a3f1177ee6720a90ebc3b9c587`.
Kontrole negatywne wykrywają zły odbiorca/payload41,brak członka wyboru,
błędną żywą pozycję oraz brak końcowego fence;osobna mutacja kodu wykrywa
pominięcie Ctrl. Zmienione fixture są odrzucane przed wykonaniem.

Nowy test UI nie porównuje pełnego kompozytu pikseli z ruchomymi selektorami.
Potwierdza stany modelu i rzeczywiste sprite’y,pozycje oraz sortingOrder.
Wcześniejsze testy pikseli renderera i selektorów pozostają oddzielne.
Nie należy na tej podstawie deklarować nowego pełnego UI RGB0,OS mouse,
natywnego Windows11,docelowego laptopa ani wydajności.

Build Unity6000.3.27f2 Windows64Mono:152935595B,0 błędów/0 ostrzeżeń.
DLL `5c9be5fd1b4ee4078e188a3ad5c955328dd50f65afc0cd7a6b7c86fe862abf49`.
71 C#/129 meta,10 stagingów. Rdzeń ruchu,planer,formacja i zasoby nie były
zmieniane. Zmieniło się6 istniejących C#,dodano1 replay.228 plików przed/po
buildzie zachowało hashe. Pełnego discovery nie powtarzano.
Znany komunikat o ComputeBuffer przy zamykaniu występuje także w poprzednich
logach renderera i sterowania;zachowano go. Własne3 atlasy póz,wejście i8 zajęć
komórek zostały zwolnione. Ostrzeżenia Pillow z wcześniejszych helperów także
pozostały w logach. Nie są ostrzeżeniami kompilacji Unity.

Raporty pod `artifacts/fleet-control/`:committed-comparison.log,
input-cycle-validation.json,shipping-validation.json,runtime-first/report.json,
targeted-tests.log,qa-tests.log,build-report.json i windows-build.log.
Aktualne regresje:[VALIDATION.md](VALIDATION.md).
[Punkt wznowienia](evidence/milestone-20261103-first-fleet-control.json).
Bez publikacji,ZIP ani podglądu do prezentacji.

## Następny krok

Przenieść własność i pracę normalnego zadania100/subtype1 przed odblokowaniem
kolejnych rozkazów i Shift zatwierdzonej grupy. Nowe eksporty źródła pokazują:
4cc500 tworzy101B zadania,4ccc30 aktualizuje jego żądanie,4a1150 tworzy kolejkę
32B zdarzeń grupy;4a1340 dopisuje300 dla dodania członka,a4a1770 dopisuje311
z indeksem członka,ID i pozycją przy usunięciu. Samo przepięcie41 nie zastępuje
obsługi tej kolejki.49e850 dla Shift zatwierdzonej grupy zmienia rzeczywiste
członkostwo;nie wolno uruchamiać wcześniejszego toggle tymczasowego wyboru.
Eksporty w `artifacts/fleet-control/source/export` pochodzą z read-only Ghidra.

Dalej pozostają pełny scheduler/fog/AI/walka/audio/save-load,pozostałe klasy,
oprawa2026 i natywne testy Windows11/laptopa. Pierwszy sterowany rozkaz i Ctrl
są domkniętym podkrokiem,nie ukończeniem rozgrywki.
