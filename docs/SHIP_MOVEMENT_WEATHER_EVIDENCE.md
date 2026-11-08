# Pogoda jako jawne wejście ruchu statku

Stan: 2026-11-02. Cel obrazu pozostaje 1920×1080, 16:9 i pełny ekran.
Ten etap ustala dane inicjalizacji WeatherClassTy oraz zależność wiatru od
źródłowego seeda. Nie wykonuje pełnego StartGame, ruchu w Unity, AI,
renderowania ani oprawy 2026.

Badany `ancient.exe` ma SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Raport i walidator: `artifacts/movement/weather/weather-validation.json`
oraz `validate_weather.py`. Oryginały pozostają bez zmian.

## Rzeczywisty zasób pierwszej misji

W `miss000.dkx/.dkd` istnieje zasób **WEATHE typu 12, 56 bajtów**, o SHA256
`955c9931323017b3e749d5eb43f9d3bb38dd4ca0f68359767666c90f312a6fd4`.
Jego 14 słów little-endian to:

```text
704, 3, 0, 0, 0, 909450863, 0, 0, 0, 0, 0, 0, 0, 0
```

Tag 704 i diagnostyczny napis handlera wiążą go z `WeatherClassTy`.
Offset +16 wynosi 0, więc handler `0x407a80`, komunikat 2, wybiera nową
inicjalizację. Dane zapisanego stanu mają inną ścieżkę pod `0x407fa0`
i inny układ; nie można opisać nimi tego 56-bajtowego payloadu.

**Słowo payloadu +20 nie jest aktywnym seedem generatora pogody.**
Handler kopiuje 909450863 do weather+0x28. Osobno ładuje aktywny seed
weather+0x18 z app+0x2ee5, po czym wykonuje `0x407e60`. Roli surowego pola
weather+0x28 poza tym zapisem nie nadano nazwy bez dalszego dowodu.

## Skąd pochodzi seed

Loader ustawień `0x4ed080` czyta ADD_TIK, TIK_TIME, OLD_TIME, LAST_NAME
oraz RND_INIT. Dla istniejącego RND_INIT kopiuje jego dword do app+0x2ee5.
Gdy go brak, wywołuje `0x5417d0` z this App i zapisuje wynik w tym samym
polu. Cały katalog 63 rekordów `miss000` **nie zawiera RND_INIT**;
ADD_TIK, TIK_TIME i OLD_TIME są czterobajtowymi zerami, LAST_NAME również
jest nieobecne.

Getter `0x5417d0` zwraca cached app+0x18, aktualizowane w pętli aplikacji
z `timeGetTime`. Nie jest to generator liczb losowych i nie odczytuje nowego
czasu OS na potrzeby każdego statku. Dokładne rozdzielenie czasu aplikacji,
kwantu i kroków opisuje [dowód zegara ruchu](SHIP_MOVEMENT_CLOCK_EVIDENCE.md).

Dla zadanej wartości app+0x2ee5 początkowa pogoda jest deterministyczna.
Nie mamy jednak przechwyconego czasu rzeczywistego oryginału z chwili tego
wczytania. Sam WEATHE z płyty nie ustala zatem jednego początkowego kierunku
i siły wiatru dla wszystkich uruchomień. To granica danych, nie powód do
przyjęcia stałego wind=0 jako oryginalnego ustawienia.

## Nowa inicjalizacja i zmiana pogody

Konstruktor `0x407970`, wraz z bazowym `0x542530`, ustawia m.in. aktywny
seed+0x18=0, akumulator kroków+0x1c=0 i pierwszy okres+0x24=10000.
Tryb 0 w message2 następnie ustawia seed z aplikacji, generuje pogodę
oraz zeruje pole specjalnego trybu+0x2c.

Generator wykonuje oryginalne 32-bitowe działania:

```text
seed = seed * 0x41c64e6d + 0x3039  (z zawijaniem 32-bitowym)
```

`0x407e60` wykonuje pierwszy krok LCG i ustala strength=(seed>>16 &7)+2,
a po kolejnym kroku heading=seed>>16 &7. Potem wywołuje `0x407d20`, które
kopiuje je do bieżących pól +0x34/+0x38 i przygotowuje następne +0x3c/+0x40.
Stąd w tej nowej inicjalizacji **bieżąca siła zawsze wynosi 2…9**,
a kierunek 0…7. Nie wynika z tego zakres wyłącznie 2…9 w późniejszych stanach.

| Pole Weather | Zakres przypisanego znaczenia |
| --- | --- |
| +0x18 | Bieżący stan PRNG; różny od surowego parametru payloadu +20 |
| +0x1c | Akumulator kroków podstawowego trybu pogody |
| +0x24 | Okres liczony w krokach: początkowo 10000 |
| +0x28 | Skopiowane surowe słowo payloadu; dalszej roli nie ustalono |
| +0x2c | Wybór zwykłego lub specjalnego trybu, początkowo 0 |
| +0x34/+0x38 | Bieżąca siła i kierunek, czytane przez kod ruchu |
| +0x3c/+0x40 | Przygotowana następna siła i kierunek |

Message0 w zwykłym trybie dodaje pendingSteps z `*(weather+0x0c)+0xe2`
do akumulatora +0x1c. Gdy unsigned dzielenie przez okres daje wynik niezerowy,
zeruje akumulator, ustala następny okres `(LCG(seed)>>16)%10000+1500`
i wykonuje `0x407d20`. Nowy okres wynosi 1500…11499 kroków.
To nie milisekundy i nie kontrakt aktualizacji co określoną liczbę sekund.
Inne kwanty, pauzy i opuszczone kroki zmieniają relację do czasu rzeczywistego.

`0x407d20` może wybrać gałąź pełnego losowania albo zmianę siły i kierunku
przez delty −2…2 oraz normalizację. Bieżąca siła staje się poprzednio przygotowaną wartością;
zmiana nie polega na liniowym mieszaniu pól przez Unity deltaTime.
Pełnego portu generatora i jego wszystkich granic nie dodano do C#.
Specjalny komunikat `0x1103` oraz saved-state loader są poza nowym oracle.

Przykłady wykonanej oryginalnej inicjalizacji:

| Jawny seed app+0x2ee5 | Bieżąca siła/kierunek | Przygotowana następna para |
| ---: | --- | --- |
| 0 | 2 / 4 | 0 / 5 |
| 1 | 8 / 6 | 9 / 0 |
| 40 | 6 / 4 | 5 / 5 |
| 909450863 | 7 / 2 | 7 / 3 |
| 0xffffffff | 3 / 1 | 2 / 2 |

Dla seeda 0 pierwsza zmiana po progu 10000 kroków daje więc 0 / 5.
Para controlled wind=0, heading=5 jest osiągalnym stanem generatora,
ale nie początkową pogodą seeda 0 ani uniwersalnym defaultem miss000.
Nie nazywamy jej też „neutralnym mnożnikiem 100%”: źródłowa tabela wpływu
wiatru może skalować ruch także przy sile 0. Samą tabelę i wzór ruchu
weryfikuje osobna analiza kinematyki.

## Wykonany oracle i jego granice

`validate_weather.py` wymaga dokładnych hashy EXE oraz pary miss000.
Wykonuje cały konstruktor Weather, całe GetMessage dla message2/trybu0
oraz wybrane ścieżki message0. Generatory `0x407e60` i `0x407d20`
wykonują się **bez hooków**.

- 71 jawnych seedów: 0…63 i wartości graniczne, w tym payloadowe 909450863,
  0x12345678, signed granice i 0xffffffff. Bieżąca siła/kierunek odpowiada
  dwóm pierwszym źródłowym krokom LCG; zaobserwowano pełny zakres 2…9.
- Pięć kontroli przejścia okresu: pending0 nie dodaje kroku; jawnie podany
  akumulator9998 po pending1 daje9999 bez zmiany, kolejne pending1 daje
  zmianę przy10000, wyzerowanie akumulatora i okres1500…11499. Nie wykonano
  w tym teście 10000 pełnych kroków całego świata.
- Osiem wywołań całego loadera `0x4ed080` z rzeczywistą nieobecnością RND_INIT
  i źródłowymi zerowymi rekordami: app+0x2ee5 jest dokładnie cached time.
  Getter czasu nie jest hookowany.
- Trzy osobne kontrole z syntetycznie dodanym RND_INIT potwierdzają gałąź
  zapisanego seeda i pierwszeństwo przed cached time. To dane kontrolne,
  nie zawartość źródłowej pierwszej misji.

Przecięto normalny powrót setjmp oraz publikację `0x4079a0`, która dotyka UI
lub dźwięku po wyliczeniu pól. Przy loaderze ustawień hook `0x549740` podaje
bajty rzeczywistych nazwanych rekordów albo null; nie wykonuje całej biblioteki
zasobów. Wskaźniki object+0x0c i +0x10 podano jawnie jako PlaySystem i App;
ich ogólne bindowanie ma odrębny dowód fabryki.

Pamięć przed konstruktorem wypełniono 0xcd. Niezapisane pola zachowują taki
wzorzec w raporcie; nie są interpretowane jako ustawienia, czas czy polecenia.
Nie potwierdzono działania publikacji, pełnego StartGame ani docelowego laptopa.

## Zakres kontrolowanego replayu ruchu

Replay przygotowanej trasy może przyjmować jawne source counter/pendingSteps,
wind_strength, wind_heading i poziom ulepszenia gracza. Taka próba sprawdza
reakcję kodu ruchu na dokładnie opisane wejścia. Może działać niezależnie od
całej pogody i zegara aplikacji, jeśli nie jest przedstawiana jako wykonanie
pełnej pierwszej misji.

Wybrana para 0 / 5 jest wejściem kontrolnym, a poziom ulepszenia 0 osobnym
wejściem. Odtworzenie domyślnej ekonomii/ulepszeń, seeda aplikacji i pełnego
cyklu pogody pozostaje kolejnym zakresem. Nie zastępuje się źródłowych wejść
czasowych Unity deltaTime lub nową stałą częstotliwością.
