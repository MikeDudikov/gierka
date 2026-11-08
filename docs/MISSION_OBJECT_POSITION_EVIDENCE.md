# Wybrane obiekty miss000 — pozycje i referencja raf

Stan: 2026-11-02. Oryginał `ancient.exe` SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Nie uruchomiono pełnej gry. Poniższe wykonanie x86 dotyczy wybranych funkcji,
z opisanymi wejściami i przechwyconymi usługami. Nie dowodzi startowego obrazu
całej misji, działania AI ani symulacji.

## Wybór małego, udowodnionego zakresu

`CreateSystemObjects0x51e7a0` przekazuje tag601 do fabryki jako0x1a64.
Tablica pod0x5c0ef8 ma parę `0x1a64,0x430e60`. Fabryka wywołuje konstruktor
`0x430070`, który instaluje vtable0x596a80. Pierwszy slot tabeli wskazuje
`0x4306d0`; napisy diagnostyczne nazywają tę klasę `ReefObjClassTy`.
`0x51f0e0` nadaje identyfikator i zależności, następnie wysyła komunikat2
z payloadem typu12 `OBJ_*`. To niezależna ścieżka od rekordów `LIST_OBJ`.

Zbadano także konstruktory i funkcje komunikatów innych klas, bez przenoszenia
ich niepełnego zachowania do Unity. Przykładowo400 to źródłowe `AmberClassTy`;
jego pozycje są w payloadzie+24/+28, a akceptacja pozycji zależy od mapy.
Nie można użyć jednego uniwersalnego offsetu dla wszystkich `OBJ_*`.

Eksporty read-only znajdują się w `artifacts/objects/position/export-ctors/`,
`export-messages/` i `export-human-messages/`. Oryginał pozostaje niezmieniony.

## Kontrakt klasy601, tryb0

Wszystkie pięć raf miss000 ma po32bajty. `0x4306d0` w gałęzi komunikatu2
odczytuje:

| Offset payloadu | Operacja kodu |
| --- | --- |
| +0 | tag klasy zapisany w object+0x50 |
| +16 | tryb odczytu:0 to źródłowa nowa referencja;1/2 to odmienne ścieżki |
| +20 | signed32 X komórki, zapis do object+0x7a |
| +24 | signed32 Y komórki, zapis do object+0x7e |
| +28 | **jeden bajt** wariantu, zapis do object+0x75; pozostałe trzy bajty nie są wariantem |

Dla trybu0 kod wysyła `SetState(1,0)` pod0x430320. Przy pustej komórce kolizji
stan pozostaje1 i wywołuje `LoadImages0x4300a0`. Ta funkcja formatuje dokładną
nazwę `BREEF%1uSPR_%1u`, podając wariant oraz stan. Następnie ustawia klatkę0,
worldX=`X<<6`, worldY=`Y<<6`, z zawijaniem do32bitów. Nie jest to pivot obrazka.

**Ograniczenie stanu:** `SetState` sprawdza istniejącą jednostkę w komórce.
W określonym stanie kolizji może wybrać3 zamiast1. Kolejne kroki świata
zmieniają stan i klatki. Dlatego `ReferenceState=1` i `ReferenceFrameIndex=0`
oznaczają zamrożoną referencję z pustą komórką, nie autorytatywny wynik pełnego
startu misji. Identyfikatory instancji nie są nazwami jednostek ani numerami
kolejności w `LIST_OBJ`.

| Zasób | ID | X,Y komórki | Wariant | Referencyjny zasób animacji | WorldX,WorldY |
| --- | ---: | --- | ---: | --- | --- |
| OBJ_00000005 |5|22,19|2|BREEF2SPR_1|1408,1216|
| OBJ_00000006 |6|16,22|3|BREEF3SPR_1|1024,1408|
| OBJ_00000009 |9|3,5|2|BREEF2SPR_1|192,320|
| OBJ_0000000a |10|20,10|2|BREEF2SPR_1|1280,640|
| OBJ_00000021 |33|5,21|2|BREEF2SPR_1|320,1344|

Oba deskryptory typu7 są w `files/DATA/OBJECTS.DKX/DKD`, nie w maplib.
Ich payload ma49bajtów, signedshort+0x23 zawiera30klatek. Osobny dowód
odczytu bibliotek i ramek nie należy do parsera pozycji. Nie wpisano
szerokości/pivotu na podstawie tych współrzędnych.

## Wykonanie oryginalnego kodu

`artifacts/objects/position/validate_reef_initialization.py` sprawdza hashe EXE,
misji i OBJECTS, a następnie wykonuje rzeczywiste:

- konstruktor601 pod0x430070 oraz konstruktor bazowy GameObj;
- obsługę komunikatu2 pod0x4306d0;
- `SetState0x430320`, w tym zapis stanu;
- `LoadImages0x4300a0`, w tym zapis indeksu0 i kotwicy świata;
- wspólną obsługę GameObj pod0x50c970.

Wejście zawiera pustą siatkę kolizji24×24, pola fabryki i pięć autentycznych
payloadów miss000. Przechwycone usługi: setjmp zwracający normalnie, wsprintfA
formatujący nazwę, InitSprite, GetSprite, SetImages, rejestracja sprite’a oraz
odświeżenie cache zajętości świata. SetImages dostaje liczbę30 odczytaną
z hash-guarded deskryptora. To nie wykonanie loadera bitmap ani renderera.
Pozostała logika ctor/msg2/SetState/LoadImages jest oryginalnymi instrukcjami.
Wynik pięciu przypadków: `reef-initialization.json` w tym samym katalogu.

Zamrożony fixture w repo: `tests/fixtures/mission_reef_seed.json`, SHA256
`8acc201d1bc05885684a1982f5ecd8f7dab9ea3bc4046251cb5787f3d9cdfdff`.
Zawiera źródłowe32bajty każdego seeda, hashe, wynik oraz warunki/hooki dowodu.
Walidator odrzuca zmieniony fixture przed kompilowaniem C#.

## Mały port C# i sprawdzenie

`MissionReefSeed.cs` jest niemutowalnym receptem referencyjnym, nie nową
instancją oryginalnego `ReefObjClassTy`. `TryRead` zwraca false dla innej
klasy; dla601 odrzuca niewłaściwą długość i rzuca NotSupportedException dla
trybu innego niż0. Nie zgaduje danych saved-state. `WorldPixelX/Y` zachowują
unchecked32bitowe przesunięcie, bez arbitralnego clampowania mapy.
`ReferenceResourceName` używa formatowania invariant.

Uruchomienie:

```sh
.venv/bin/python tools/validate_mission_reef_seed.py --output artifacts/objects/<nowy-raport>.json
.venv/bin/python -m unittest tests.test_mission_reef_seed -v
```

Walidator kompiluje rzeczywiste `MissionObjectSeed.cs`, `MissionReefSeed.cs`
i probe C# z `/checked+`. Porównuje104przypadki: pięć źródłowych fixture oraz
99przypadków stresujących. Dla wszystkich104 dodatkowo wykonuje dwa zakresy
oryginalnych instrukcji bez hooków: `0x430773..0x43079a` kopiuje pola, a
`0x43016e..0x43018c` przelicza obie kotwice świata. Obejmuje wartości ujemne,
INT_MIN/MAX, zawijanie przesunięcia oraz odczyt wyłącznie dolnego bajtu
wariantu, również gdy pozostałe bajty są niezerowe.

Przeszło104/104 oraz11oddzielnych strażników kontraktu C#. Przeszły dwa testy
unittest, w tym odrzucenie zmienionej referencji. Są to dowody ekstrakcji i
arytmetyki; stresowe współrzędne/nieznane warianty nie są deklaracją istnienia
odpowiedniej grafiki ani poprawnego miejsca w grywalnej misji.

W tym etapie nie odtworzono pełnej kolizji, AI, ruchu, destrukcji, zegara,
animacji, draw order wszystkich klas, pełnego spawn/WorldLife ani gameplayu.
Render diagnostyczny musi opisywać te pięć raf jako zamrożone referencje.
