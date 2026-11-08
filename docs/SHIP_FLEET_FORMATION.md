# Formacje i odbiór rozkazów floty — 2026-11-03

Przeniesiono wyznaczanie indywidualnych celów normalnych statków wodnych,
tworzenie pakietów20 i ich kopiowanie do skrzynek26B. Moduły współpracują
z poprzednim [członkostwem floty](SHIP_FLEET_MEMBERSHIP.md). Nie są jeszcze
podłączone do kursora ani fizycznego ruchu wielu jednostek. Diagnostyka wyboru
floty nadal blokuje ruch;normalny Start pozostaje wyłączony. Pełna gra i
oprawa2026 są w budowie. Obowiązuje1920×1080,16:9,pełny ekran całego widoku.

## Zachowanie źródłowe

`SourceFleetFormation.Assign` przenosi560090,560f10,5612f0 i55f800 dla2…8
normalnych statków kategorii0 na wspólnym polu wodnym. Zachowuje medianę,
czyszczenie ośmiospójnej zablokowanej składowej celu5732e0,pełne pola falowe,
przeglądanie pierścieni,kolejność kandydatów,projekcje i stabilne remisy.
Pole terenu jest kopiowane;wynik posiada własne cele,pasma i obrazy pól QA.

Dodano`SourceWaveField.FillAll` z parametrami celu−1,−1 i heading−1.
Dotychczasowe`Fill`,`FillFromOrigin` i cały rdzeń`Calculate` pozostają
niezmienione. Nie zastąpiono ważonej fali przez BFS ani inny planner.
Stos użyty wyłącznie do czyszczenia składowej daje ten sam zbiór komórek
co5732e0;potwierdzono całe płaszczyzny przed dalszą falą.

Zachowano także nieoczywiste reguły potwierdzone instrukcjami x86:

- W relokacji zablokowanej mediany oryginał sprawdza stały indeks terenu
  pierwszej komórki krawędzi,mimo przesuwania odczytu fali. Potwierdza to
  instrukcja560661. Nie poprawiano tej cechy do intuicyjnego testu każdej komórki.
- Projekcja celów używa przeciwnego kierunku,`direction−4 &7`. Wyrażenie
  wskaźnikowe w dekompilacji mogło sugerować−1;instrukcja55fa93 potwierdza−4.
- Przy równej projekcji kandydaci są sortowani malejąco według kosztu fali
  od początku;aktorzy rosnąco według kosztu od celu. Remisy pozostają stabilne.
- Mediana parzystej liczby celów zaokrągla się w stronę kliknięcia.

Dla początkowych pozycji0b16,2;0c21,5;0d19,4 i kliknięcia18,5 oryginał
i C# wyznaczają0b→18,5;0c→20,6;0d→19,4. Kolejność wysłania rozkazów
odpowiada kolejności członków,nie numerycznej kolejności ID.

`ShipFleetMoveCommands.Build` zachowuje jednoczłonowy skrót4cc970:bez fali,
bez odczytu terenu,bezpośredni kliknięty cel. Dla wielu statków używa formacji.
Sukces daje osobne9-bajtowe payloady20:podpisane int32X/int32Y little endian
i końcowe0. Po ujemnym wyniku formacji źródłowy4ccc30/4cc650 wysyła każdemu
kliknięty cel z bajtem255. Nie traktuje się braku trasy jako udanej formacji.

Pakiety41 powstają wcześniej,w`ShipFleetMembership`. Potem każdy20 jest
adresowany ID właściwej instancji. `CopyTo` kopiuje żądanie do istniejącego
`ShipMoveRequestInbox`;ustawia pending80 i dokładny26-bajtowy rekord.
Nie promuje go do aktywnego ruchu. Caller odpowiada za routing po InstanceId,
normalny typ/medium członków oraz kwalifikację celu przez mapę i kursor.

## Dowody i granice

| Sprawdzenie | Zakres |
| --- | --- |
| Formacja |3028 prób na29 mapach;2988 dokładnych wyników oraz40 jawnych ograniczeń opisanych poniżej |
| Pierwsza misja |2304 prób:wszystkie576 celów dla3 par i całej trójki;wszystkie1452 cele na dostępnej wodzie zgodne,bez ograniczeń kierunku |
| Pełne płaszczyzny formacji |5954029 porównanych komórek;czyszczenie składowej,fala celu,fala początku i rezerwacja kandydatów |
| Pełna fala |5250 przypadków/373506 komórek;wszystkie maski i początki1×1,2×2,3×3 oraz576 początków na źródłowym terenie misji |
| Pełny obieg41/20 |237 scenariuszy,1050 pakietów i1287 stanów odbiorników;wszystkie15 uporządkowanych niepustych podzbiorów lokalnych statków |
| Ujemna formacja |12 scenariuszy źródłowego fallbacku255;dokładne payloady i26B przed promocją |
| Kontrakty API |19 kontroli formacji/fali i13 kontroli pakietów/odbiornika |

Sondy wykonują rzeczywiste oryginalne funkcje formacji,serializacji i odbioru.
Nie zastąpiono funkcji algorytmu hookami;granice obejmują alokację/zwalnianie,izolowany FS:0
i wcześniejsze granice konstruktora/renderowania/wyłączonego audio.
Metadane wejściowe są buforowane w obrębie przebiegu,wyniki x86 nie są.
Pierwszy teren bierze się z rzeczywistego prefiksu49a950 i globalnego pola
wodnego,bez zajętości statków:SHA256
`3cc7c7ac49d9fd0512557cd909adad4c346db59705e0ff3ae047ff54b906843e`.
Wczesny`pilot-native.json` używał pola nawigacji0b zawierającego zajętość;
nie jest wzorcem formacji. Końcowe fixture używa właściwego pola.

W40 próbach oryginał nie wybiera kierunku podejścia w co najmniej jednej
pętli55f800. Potwierdzają to obserwacje55f9f0 i55fa6d. Dalsze obliczenia
mogą korzystać z pozostałej zawartości stosu/wskaźnika;to nie jest stabilna
reguła geometryczna. Są to12 zablokowanych celów pierwszej mapy oraz28
przypadków syntetycznych,w tym rozłączne obszary wody. C# jawnie odrzuca
taki kontekst. **Nie wliczono tych40 prób do2988 zgodnych formacji.**
Przed obsługą takich przypadków w pełnej grze potrzebny jest dalszy dowód
kontekstu callerów;nie przypisano arbitralnego kierunku ani uproszczonej trasy.

Zakres nie obejmuje mieszanych mediów,kategorii innych niż0,grup AI,
aktywnego zastępowania zadania grupy ani błędów alokacji. Normalne zadanie
100/subtype1 wykonuje się w sondzie,ale moduły C# nie utrzymują jeszcze
całej listy zadań grupowych ani schedulera. Statki nie poruszają się wskutek
samego przygotowania pakietów lub ustawienia pending80.

Nowy i powiązane moduły przeszły11 testów,0 pominięć,168.155s.
Pięć nowych mutacji kodu zostało wykrytych. Ten sam kod i pakiety sprawdzono
w rzeczywistym DLL Unity na hostowym Mono. To nie jest test natywnego Windows11.
BuildWindows64Mono148061627B ma0 błędów i ostrzeżeń. Pierwszy build odrzucił
nowy identyfikator meta o błędnej długości;został poprawiony przed drugim buildem,
a wszystkie124 meta sprawdzone. Log nieudanego builda zachowano.
Pełnego discovery nie powtarzano;wyniki wcześniejszych DLL są historyczne.

Wyniki końcowych testów,builda i regresji playera:
[VALIDATION.md](VALIDATION.md). Punkt kontrolny:
[milestone](evidence/milestone-20261103-fleet-formation.json).

## Następny krok

Przenieść promocję żądań i fizykę0c/0d wraz z ich rzeczywistymi parametrami,
dynamiczną zajętością i planowaniem we współdzielonej grupie. Dotychczasowy
`ShipMoveOrder` nadal opisuje0b przy siedmiu statycznych peerach.
Następnie zintegrować pełny obieg z kursorem,wyborem i zadaniami grupowymi,
odtworzyć Ctrl istniejącej grupy oraz zastępowanie rozkazów. Dopiero
zwalidowany wspólny ruch może zostać odblokowany w playerze.
