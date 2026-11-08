# Początkowe obiekty miss000 — kolejność, filtr i wybór klasy

Stan: 2026-11-02. Badany oryginał ma SHA-256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Źródłowe `miss000.dkx` i `.dkd` także mają jawne, sprawdzane hashe w
`tools/validate_mission_object_selection.py`. Oryginału nie uruchamia system
operacyjny i żaden jego plik nie jest modyfikowany.

Ten dowód dotyczy **wyboru początkowych zasobów, identyfikatora instancji
i kodu fabryki**. Nie wykonuje konstruktorów, klasowego Init, AI ani symulacji.
Docelowy obraz całego remake’u pozostaje 1920×1080, 16:9 i pełny ekran.

## Dwie niezależne reprezentacje

`LIST_OBJ` typu20 zawiera nagłówek28bajtów oraz 44rekordy po23bajty.
Loader DArray `0x54a840`/`0x55f2e0` potwierdza rozmiar elementu, count,
capacity i dane. Nie jest to lista45nazwanych payloadów `OBJ_*` typu12.
Nie wolno łączyć tych zbiorów po numerze wiersza ani uznawać44za liczbę
tworzonych jednostek. `AncientAppTy::StartGame0x4ebf50` zeruje count tablicy
`app+0x15c9`; początkowe klasy powstają przez odrębną enumerację nazwaną.

`PlaySystemClassTy::GetMessage0x522ce0` w obsłudze komunikatu8 i lokalnej
gałęzi `app+0xd7c !=0` wywołuje `mfAObjEnum0x5497e0`. Prefiks tworzony
z `PTR_DAT_0x5c1f50` to `OBJ_`. Enumerator wybiera zasoby typu12, ładuje
payload i jego długość, a następnie przekazuje do callbacku:

```text
CreateSystemObjects(payload, byteLength, DB, exactResourceName, playSystem)
```

Callback to `0x51e7a0`. Gałęzie sieciowe i opcjonalne dodatkowe obiekty
z bufora odtwarzania nie należą do tej walidacji.

## Kolejność ma dowód z oryginalnego iteratora

Nie przyjęto kolejności fizycznych offsetów DKD. W Unicorn wykonano:

- `0x570ea0`: ToBeg;
- `0x57af80`, `0x57e8d0`, `0x57af40`, `0x57f790`: przejście BTree GetNext;
- `0x543440`: rzeczywistą funkcję długości klucza;
- `0x5444c0`, `0x544490`, `0x588f90`: filtr typu/prefiksu i wyszukiwanie napisu.

**Nie przechwycono żadnej funkcji iteratora ani filtru.** Oryginalny indeks
DKX jest mapowany do pamięci; struktury kontekstu tworzy narzędzie.
Nie wykonuje się systemowego otwierania pliku ani oryginalnego DB konstruktora.

Iterator zwrócił63klucze całego indeksu oraz, w osobnym przebiegu,
dokładnie45kluczy typu12 o prefiksie `OBJ_`. Ich nazwy to
`OBJ_00000001`…`OBJ_0000002c`, następnie `OBJ_0000002e`.
`OBJ_0000002d` nie istnieje. Offsety wszystkich45zasobów zgadzają się z
odczytanym indeksem; zmienianie ID na ciągłe1…45 byłoby błędem.

Ogólny comparator klucza `0x5433d0` porównuje najpierw unsigned byte typu,
potem signed16 długości nazwy, a na końcu surowe bajty nazwy przez porównanie
case-sensitive. To nie jest ogólne sortowanie `(type, name)`.
Wszystkie kanoniczne nazwy tej misji mają ten sam typ12 i długość12, dlatego
**dla tego zbioru** zwykłe ordinal ASCII nazwy odtwarza oryginalną kolejność.

Dowody: `artifacts/objects/loader/oracle/original-btree-order.json` i
`original-obj-order.json`; trwała fixture kolejności:
`tests/fixtures/mission_miss000_object_order.json`.
Walidator C#/x86 powtarza faktyczne przejście iteratora przy każdym pełnym teście.

## Nagłówek, gracze i ID

`CreateSystemObjects0x51e7a0` czyta cztery little-endian uint32:

| Offset | Ustalone znaczenie w badanej ścieżce |
| --- | --- |
| +0 | Tag wyboru klasy; nie kod fabryki ani nazwa jednostki |
| +4 | Kind; specjalny filtr gracza działa tylko dla wartości1 |
| +8 | Pierwszy indeks w tabeli graczy, mnożony przez4 |
| +12 | Drugi indeks gracza, dodawany do poprzedniego |

Dla `kind==1` oryginał sprawdza bajt
`PLAYERS_DESC[side*4+player]` pod `app+0x1a1d`. Zero pomija cały obiekt;
każda wartość niezerowa, również128/255, pozwala przejść dalej. Dla innych
kind nie wykonuje tego odczytu. Nie nadano kind0/2 arbitralnych nowych nazw.
Tabela ma20bajtów, pięć wierszy po cztery sloty.

Pierwsze Start scenario nie korzysta bezpośrednio z zapisanej tabeli jako
końcowej aktywności. `0x537ef0` czyści20bajtów i odbudowuje je z rekordów
DESCRIPTOR. Dla kampanii0 aktywny człowiek(1,1) ma wartość1, a obecny
gracz(4,0) ma3; pozostałe bajty są0. Osobny dowód inicjalizacji graczy i kamery
znajduje się w `MISSION_INITIAL_CAMERA_EVIDENCE.md`.

ID instancji pochodzi z **nazwy**, a nie z pozycji rekordu. `0x51e7a0`
pomija prefiks długości4 i wywołuje oryginalny parser `0x570190` z bazą16.
Parser wraz z pomocnikami CRT wykonano bez hooka. Kanoniczne granice:

| Sufiks | Wynik uint32 |
| --- | ---: |
| `00000000` | 0 |
| `0000000f`, `0000000F` | 15 |
| `7fffffff` | 2147483647 |
| `80000000` | 2147483648 |
| `ffffffff`, `FFFFFFFF` | 4294967295 |

Port C# przyjmuje wyłącznie kanoniczne `OBJ_` +8cyfr hex; nie deklaruje
zgodności błędów parsera, przepełnień dłuższych napisów ani niekanonicznych nazw.

## Kod fabryki i granica dowodu

Oryginał ma61rozpoznanych tagów w badanym dispatchu. Tagi200…211 wybierają
kod5256; pozostałe są jawnie porównywane. Pełną tabelę odtworzono z eksportu
`0x51e7a0` i sprawdzono wykonaniem wszystkich tagów0…1000 oraz dużych uint32.
Nieznany tag nie tworzy obiektu i kończy callback wynikiem0.

W samej miss000 występuje13tagów:

| Tag źródłowy | Kod fabryki | Liczba zasobów |
| ---: | ---: | ---: |
| 50 | 5265 | 1 |
| 57 | 5275 | 1 |
| 58 | 5276 | 1 |
| 63 | 6763 | 1 |
| 72 | 5775 | 2 |
| 200 | 5256 | 8 |
| 400 | 5758 | 10 |
| 401 | 5756 | 7 |
| 601 | 6756 | 5 |
| 606 | 6165 | 6 |
| 700 | 5859 | 1 |
| 702 | 5855 | 1 |
| 703 | 5776 | 1 |

`0x51f0e0` pobiera klasę z fabryki `0x541ad0`, przypisuje jej ID/owner,
a następnie wysyła komunikat2 z payloadem do vtable. Nasz oracle zatrzymuje
się **przed tą operacją**, rejestrując wyłącznie kod fabryki i ID.
Nie oznacza tego jako dowodu poprawnego stanu po inicjalizacji.

## Implementacja i walidacja

`AncientConquest.World.MissionObjectSeed` jest niezmienną kopią dokładnego
payloadu, z `InstanceId`, `ClassTag`, `Kind`, `SideIndex`, `PlayerIndex`,
`ByteLength`, ograniczonym `ReadUInt32/ReadInt32/ReadByte`.
`MissionObjectSelection.TrySelect(seed, players, out factoryType)` zwraca
wybór i kod fabryki, bez uruchamiania konstruktorów. C# jawnie odrzuca
nieprawidłowe indeksy kind1 oraz tablicę graczy innego rozmiaru;
oryginał dla takich danych odwołuje się do surowej pamięci.

Rzeczywiste źródła C# skompilowano z `/checked+` i porównano z oryginalnym
`0x51e7a0`: **1450/1450przypadków**.

| Grupa | Liczba | Zakres |
| --- | ---: | --- |
| Źródłowe payloady | 315 | 45rekordów ×7masek graczy, w tym właściwa maska Start scenario |
| Tagi | 1003 | 0…1000,0x7fffffff,0xffffffff; rozpoznane i nieznane |
| Sloty i wartości | 120 | 20slotów ×0/1/2/3/128/255 |
| Kind inne niż1 | 4 | Brak odczytu tabeli nawet przy dużych słowach indeksów |
| Kanoniczne ID | 8 | Zero, mixed case i pełny unsigned32 zakres |

Przechwycono tylko normalny powrót `setjmp0x587318` i wyżej opisaną granicę
`0x51f0e0`. Parser ID nie jest przechwycony. Przy każdym przebiegu sprawdzono
wynik0, powrót funkcji i przywrócenie łańcucha wyjątków. Tryb sieciowy wyłączono
w kontrolowanym kontekście. Wszystkie45rekordów właściwej maski są wybrane;
to liczba **żądań tworzenia**, nie wykonanych instancji ani jednostek gracza.

Dodatkowo36kontroli C# sprawdza kopię danych, LE/odczyt ze znakiem,
odczyt bez wyrównania, granice, nieprawidłowe nazwy i długości, tablicę graczy
oraz odrzucenie błędnego slotu. Są to kontrole kontraktu bez odpowiednika
w bezpiecznym wejściu oryginału; nie wliczono ich do1450porównań x86.

```sh
.venv/bin/python tools/validate_mission_object_selection.py --output <nowy-raport.json>
.venv/bin/python -m unittest tests.test_mission_object_selection -v
```

Fixture45rekordów: `tests/fixtures/mission_miss000_object_selection.json`,
SHA256 `8502df484e066fd80a75872583fe01fbc46ff3031f75942e375f020fffc9c812`.
Walidator chroni ten hash i porównuje fixture z ponownym wykonaniem oryginału.
Eksporty C/dekompilacji są w `artifacts/objects/loader/{export,enum-export,tree-export}`.

Wynik nie potwierdza pozycji wszystkich klas, aktywności ich konstruktorów,
kolizji, kolejności rysowania, wyglądu świata po inicjalizacji, AI, tempa,
rozgrywki ani zgodności całego remake’u1:1. To osobny, mały krok inicjalizacji.
