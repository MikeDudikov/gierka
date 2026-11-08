# Członkostwo floty — zakres kroku

`ShipFleetMembership` przenosi normalne przypisanie wybranych statków do
grupy Mode10 oraz oddzielny odbiór komunikatów41. To kolejny element
wspólnych rozkazów, po ukończonym [wyborze floty](SHIP_FLEET_SELECTION.md).
Moduł nie jest jeszcze podłączony do kursora ani ruchu wielu jednostek.
W trybie wyboru floty rozkazy nadal są jawnie blokowane; normalny Start
pozostaje wyłączony. Pełny remake i oprawa2026 są w budowie.

## Przeniesione zachowanie

- Niepusta, uporządkowana tymczasowa lista tworzy kolejną grupę Mode10.
  Kolejność członków odpowiada kolejności wyboru, także po ramce i Shift.
- Wektor grupy zawiera indeksy rejestru aktorów, a komunikaty są adresowane
  identyfikatorami instancji. Te dwie wartości są rozdzielone.
- Przenoszony statek otrzymuje najpierw komunikat41 z grupą−1, a następnie
  komunikat41 z nową grupą. Pozostali członkowie starej grupy zachowują
  kolejność i dostają poprawione indeksy pozycji.
- Puste starsze grupy są zachowane. Dotyczy to potwierdzonego ustawienia
  lokalnego właściciela, z wyłączonym usuwaniem pustych grup.
- Payload41 ma dokładnie6 bajtów: subtype1, podpisana32-bitowa grupa
  little endian oraz końcowe0. Usunięcie to `01ffffffff00`.
- Pole grupy UI zmienia się podczas przypisania. Pole grupy symulacji
  zmienia się dopiero przy dostarczeniu kolejnego41 do danego aktora.
  UI może wyprzedzać odbiorcę o kilka przypisań; nie scala się komunikatów
  usunięcia i ponownego dodania.
- Pusta lista zwraca0 bez tworzenia grupy i bez zmiany bieżącego indeksu,
  zgodnie z49ca60. Zwrot0 nie oznacza automatycznie nowej grupy0.

To projekcja normalnych, zainicjalizowanych lokalnych statków, bez aktywnego
zadania grupy. Nie obsługuje grup AI/Mode11, usuwania aktywnego zadania,
usuwania pustych grup, statusu4, zawijania16-bitowych indeksów ani uszkodzonego
rejestru. API odrzuca nieznanych lub powtórzonych członków przed zmianą stanu.
Historia wygenerowanych41 i jawny odbiornik FIFO stanowią adapter do kolejnego
etapu; nie zastępują pełnego schedulera ani transportu komunikatów gry.

## Źródło i sprawdzenia

Oryginalne49ca60,49b990,49bd60,49bef0,520c50 i5593a0 wykonują tworzenie grup,
przenoszenie członków i serializację. Oryginalne4dc630 oraz50c970 odbierają
komunikaty oddzielnie dla0b/0c/0d. Nie zastąpiono tych funkcji hookami ani
ręcznymi zapisami oczekiwanego członkostwa. Zachowano granice CRT, konstruktora,
renderowania i wyłączonego audio z poprzednich sond.

Sonda poprawnie inicjalizuje indeksy rejestru0/1/2 oraz rzeczywiste komórki
statków. Dawne klony używane wyłącznie do wyboru nie potrzebowały tych pól.
Każdy scenariusz ma nowy emulator. Optymalizacja sondy buforuje wyłącznie
ponownie dekodowane metadane wejściowe statków w obrębie jednego przebiegu;
nie buforuje wykonania x86 ani wyników. Zachowano osobny pierwszy przebieg
bez tej optymalizacji do porównania wyników.

Testy obejmują wszystkie16 uporządkowanych podzbiorów trzech statków przed
i po ponownym przypisaniu, częściowy odbiór pomiędzy przypisaniami, ciąg32
przypisań oraz serię zmian UI przed dostarczeniem pierwszego41. C# jest
kompilowany z`checked+` i`warnaserror+`; osobna kontrola wykonuje kod z DLL
rzeczywistego builda Unity na hostowym Mono. To nie jest test urządzenia
Windows11. Kontrole negatywne usuwają komunikat−1 oraz przedwcześnie zmieniają
grupę symulacji, sprawdzając, czy porównanie wykrywa regresje.

Końcowy wynik:258 scenariuszy/2175 stanów zgodnych dla źródła i DLL,
23 kontrole API oraz10 testów celowanych PASS/0skip/95.534s.
BuildWindows64Mono ma0 błędów i ostrzeżeń. Regresja wyboru ma46 etapów
RGB0 na tym samym DLL. Pełnego discovery w tym małym kroku nie powtarzano;
poprzedni discovery i wcześniejsze regresje innych DLL pozostają historyczne.

Wyniki końcowe są zapisane w [VALIDATION.md](VALIDATION.md) i raporcie
`artifacts/fleet-orders/membership-validation.json`. Nowy moduł nie wymaga
nowego stagingu; zachowano dziewięć dotychczasowych zestawów Resources.
[Milestone](evidence/milestone-20261103-fleet-membership.json) wiąże kod,
fixture,build i końcowe dowody. Zmiany pozostają lokalne.

## Następny krok: formacja i ruch

Przed połączeniem z kursorem należy przenieść4cc970→561470→560090: medianę
grupy, źródłowe pola falowe, kolejność kandydatów, remisy i przypisanie celów.
W oryginale cel kliknięty18,5 dla rzeczywistych początkowych pozycji trzech
statków daje0b→18,5;0c→20,6;0d→19,4. Kolejność wysyłania20 odpowiada
kolejności członków, ale nie zmienia tych przypisań w sprawdzonych przykładach.
To obserwacja źródłowa, a nie jeszcze port algorytmu.

Źródłowy konstruktor/loader potwierdza medium0 dla wszystkich trzech statków,
także modelu7/statku0d. Analiza i dekompilacje są pod
`artifacts/fleet-orders/source/`; `native-local-medium.json` przechowuje
wartości po rzeczywistym loaderze. `native-cells.json` ma poprawne pozycje.
`native-first.json` jest wcześniejszą sondą z błędnymi odziedziczonymi komórkami
0c/0d; nie wolno używać jej jako wzorca formacji.

Następnie potrzebne są dokładne20,26-bajtowe skrzynki odbiorcze wszystkich
członków, promocja, współdzielona grupa w zajętości oraz dynamiczne planowanie
tras. Dotychczasowy `ShipMoveOrder` jest projekcją pojedynczego0b z siedmioma
statycznymi peerami. Nie można użyć trzech jego kopii jako dowodu ruchu floty.
Przywoływanie istniejącej grupy po Ctrl, modyfikowane i zastępujące rozkazy
oraz kontekstowe akcje prawego przycisku także wymagają dalszego portu.
