# Statki miss000 — źródłowa inicjalizacja i granice recepty

Stan: 2026-11-02. Docelowy obraz remake’u pozostaje **1920×1080, 16:9,
pełny ekran**. Ten etap ustala pola ośmiu początkowych statków, a nie ich
działającą symulację, komplet statystyk, AI ani wygląd jakości2026.

Badany `ancient.exe` ma SHA256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Walidator sprawdza także dokładne hashe pary `miss000.dkx/.dkd`.
Oryginału nie uruchamia system operacyjny, a pliki źródłowe pozostają bez zmian.

## Klasa200 jest rodziną statków

Źródłowy `CreateSystemObjects0x51e7a0` wybiera kod fabryki5256/0x1488
dla tagów200…211. Para rejestru pod0x5c0e38 łączy ten kod z0x4dfa30.
Fabryka rezerwuje0x8eabajtów i wywołuje konstruktor0x4dc3f0, który instaluje
vtable0x59b48c. Handler pierwszego slotu to0x4dc630. Napisy diagnostyczne
wskazują **`ShipClassTy`** oraz `nik/ship.cpp`.

Zatem osiem zasobów typu12 z tagiem200 to statki, a nie budynki ani
osiem jednakowych modeli. Nie nadano im nazw gatunków z pamięci gry.
W badanej misji warianty pochodzą z osobnego pola payloadu.
`LIST_OBJ` pozostaje odrębną strukturą; patrz
[dowody loadera](MISSION_OBJECT_LOADER_EVIDENCE.md).

W gałęzi komunikatu2 handler `0x4dc630` sprawdza słowo trybu na+16.
Dla trybu0 wywołuje `LoadDateBase0x4dfa90`, tworzy sprite, dobiera stan
zależny od zdrowia i sprawdza przyjęcie pozycji przez mapę. Tryby1/2 mają
inne ścieżki i nie są obsługiwane przez nową receptę C#.

## Potwierdzone pola trybu0

Wszystkie osiem źródłowych payloadów ma dokładnie616bajtów i tryb0.
Nagłówek+8/+12 służy filtrowi tworzenia gracza. Własność klasy statku jest
**ponownie odczytywana z+20/+24**; nie wolno zamienić tych dwóch par.

| Offset payloadu | Odczyt i zapis oryginału |
| --- | --- |
| +16 | uint32 trybu; badana ścieżka wymaga0 |
| +20 | Jeden bajt właściciela: object+0x54, a także originSide+0x250 |
| +24 | Jeden bajt drugiego slotu właściciela: object+0x55 |
| +28 | **Cały dword+200**, z zawijaniem32bit, daje runtime classTag podobject+0x50 |
| +28 | Niezależnie **jeden dolny bajt** daje wariant modelu podobject+0x25a |
| +32 | Słowo flag maskowane przez0x4e6930; nie jest przeniesione jako pełna mechanika |
| +36/+40 | signed32 X/Y komórki podobject+0x5a3/+0x5a7 |
| +44 | Jeden bajt kierunku podobject+0x5af; renderer rozszerza go **ze znakiem** |
| +48 | signed32 procentu źródłowego zdrowia, przekazywany do0x4ac110 |
| +56 | Dolny bajt minus3, z zawinięciem i interpretacją signed8, podobject+0x27b |
| +60 | Dolny bajt podobject+0x27a; neutralna nazwa recepty `SourceEquipmentA` |
| +512 | Dword licznika źródłowych poleceń; recepta zachowuje metadane, nie wykonuje poleceń |

Właściciel+20 jest również przepisywany do+0x250, używanego przy doborze
grafiki. Oryginał liczy byte slotu jako `side*4+player`, z zachowaniem
dolnych8bitów. Pełne słowo modelu i jego bajt to różne wartości: na przykład
0x12340006 daje wariant6 oraz runtime classTag0x123400ce. Port nie redukuje
obu pól do `200+variant`.

## Osiem rzeczywistych statków

| Zasób | ID | Właściciel | Wariant | Runtime tag | KomórkaX,Y | Kierunek | Źródłowy indeks klatki |
| --- | ---: | --- | ---: | ---: | --- | ---: | ---: |
| OBJ_0000000b |11|1,1|0|200|16,2|5|20|
| OBJ_0000000c |12|1,1|0|200|21,5|4|16|
| OBJ_0000000d |13|1,1|7|207|19,4|4|16|
| OBJ_00000010 |16|4,0|1|201|11,18|0|0|
| OBJ_00000027 |39|4,0|6|206|9,21|1|4|
| OBJ_00000028 |40|4,0|6|206|10,22|1|4|
| OBJ_00000029 |41|4,0|6|206|6,13|1|4|
| OBJ_0000002a |42|4,0|6|206|6,14|1|4|

Każdy ma żądany procent zdrowia100 i licznik poleceń0. Są to dane
początkowych zasobów, nie twierdzenie o wykonaniu wszystkich skutków
pełnego StartGame lub o zakończonym tworzeniu instancji w Unity.

## Zdrowie i stan grafiki

Konstruktor rzeczywiście wykonuje `0x4ac210`, ustawiający tablice skalowania.
`0x4ac110` oblicza z oryginalnej tabeli pod0x5bb4b0:

```text
rawHealth = int32(table[modelByte] * 650 * requestedPercent) / 100
```

Mnożenia zawijają do32bitów, dzielenie jest signed i obcina do zera.
Dla autentycznych100% wynik i maksimum wynoszą18200 dla wariantu0,
58500 dla wariantu1 oraz23400 dla wariantów6/7. Nie zamieniono tych liczb
arbitralnie na inne jednostki UI ani nie przypisano im całej reguły walki.

`0x4be030` oblicza procent maksimum. Przy zdrowiu dodatnim granice stanu
to71% i36%: stan1 dla co najmniej71%, stan2 dla36…70%, stan3 poniżej36%.
W badanych ośmiu zdrowych referencjach wybiera stan1 i żąda przeładowania
grafiki przez `0x4e1bb0`. To **warunkowy wynik izolowanego inicjalizatora**:
oracle pomija rozsyłanie początkowych poleceń oraz złożony setup walki/ruchu.
Nie stwierdzamy, że odtworzono pełny stan statku w pierwszej klatce gry.

`MissionShipSeed` zachowuje żądany procent, ale nie wykonuje tego systemu
zdrowia ani nie udaje autorytatywnego stanu bojowego.

## Kotwica dotyczy całej logicznej klatki

`0x4e0160` zapisuje:

```text
spriteX = (cellX << 6) + (64 - logicalFrameWidth) / 2
spriteY = (cellY << 6) + (64 - logicalFrameHeight) / 2
frameIndex = sign_extend_int8(headingByte) << 2
spriteFrameMode = 2
```

Działania mają oryginalne zawijanie32bit i signed dzielenie do zera.
Nie wolno zastąpić środka klatki kotwicą lewy-górny róg kafla ani użyć
szerokości pojedynczego komponentu zamiast logicznej klatki kompozytu.
Nie należy ponownie dodawać bbox już zawartego w zdekodowanej płaszczyźnie.

Oracle wykonuje zakres **0x4e0160…przed0x4e01d6 bez żadnych hooków**.
Kończy się po zapisaniu położenia, klatki i trybu, przed opcjonalnym ładowaniem
dźwięku. Testowe rozmiary w tym oracle są wejściami arytmetycznymi;
nie stanowią dowodu rzeczywistych rozmiarów grafiki. Rozpoznanie zasobów,
składania komponentów i palet jest osobnym dowodem graficznym.

## Wąskie wykonanie x86 i C#

`tools/validate_mission_ship_seed.py` wykonuje oryginalne:

- konstruktor `0x4dc3f0`, jego bazowy GameObj i inicjalizację tabel;
- bezpośrednio `LoadDateBase0x4dfa90`, w tym kopie pól, maskę flag,
  skalowanie zdrowia i zapisy lokalnych tablic;
- dobór stanu pod0x4be030;
- oddzielny zakres wyliczenia kotwicy i klatki opisany wyżej.

To nie jest uruchomienie całego handlera komunikatu2. Kontekst fabryki
(ID, wskaźniki aplikacji/systemu) tworzy narzędzie. Przechwycone granice:

| Adres | Jawnie pominięta usługa |
| --- | --- |
| 0x587318 | Zwykły powrót setjmp0 |
| 0x4e7220 | Rozsyłanie początkowych poleceń |
| 0x4bee60 | Złożony setup walki/ruchu |
| 0x50e640 | Rozsyłanie wiadomości do systemu obiektów |
| 0x4e1bb0 | Rejestrowanie żądania grafiki stanu; bez ładowania zasobów |
| 0x4b97d0 | Kolejka początkowych poleceń, tylko syntetyczne przypadki z dodatnim licznikiem |

Argument procentu zdrowia odczytywany jest przy wejściu do rzeczywistego
`0x4ac110`, bez zastępowania tej funkcji. `SourceOrderCount` zachowuje
surowe słowo źródłowe; nie potwierdza wykonania kolejki poleceń.
Każdy pełny przebieg musi wrócić i przywrócić łańcuch wyjątków.

Rzeczywiste `MissionObjectSeed.cs` i `MissionShipSeed.cs` skompilowano
z `/checked+`. Wynik: **184/184przypadków** zgodnych z projekcją x86
oraz zakresem kotwicy. Rozdział wejść:

| Grupa | Liczba |
| --- | ---: |
| Autentyczne payloady miss000 |8|
| 12wariantów ×8kierunków |96|
| Bajtowe pola właściciela i wyposażenia |10|
| Pełne słowo modelu i jego dolny bajt |10|
| Argument procentu zdrowia, w tym wartości signed graniczne |12|
| Metadane licznika poleceń |6|
| Pozycje, wymiary, signed heading i przepełnienia kotwicy |42|

Zatem176wejść jest syntetycznych. Ujemne kierunki, nieprawidłowe wymiary
i współrzędne poza mapą są testami arytmetyki, a nie grywalnymi stanami.
Nie występują w ośmiu źródłowych rekordach.

Dodatkowo9kontroli C# sprawdza odrzucenie null, niewłaściwych długości,
nieobsługiwanych trybów oraz reset wyniku dla innych klas. Nie wliczono
ich do184porównań x86. Nieznana klasa zwraca false; recepta obejmuje wyłącznie
zaobserwowany tag200 i tryb0. Nie ma domyślnej, wymyślonej obsługi saved-state.

```sh
.venv/bin/python tools/validate_mission_ship_seed.py --output <nowy-raport.json>
.venv/bin/python -m unittest tests.test_mission_ship_seed -v
```

Trwała fixture: `tests/fixtures/mission_ship_seed.json`, SHA256
`1ae221249bf8812b5a033c769134b22d6266e85d232d18a53e8473fa0cfcdab9`.
Zawiera pełne616bajtów każdego payloadu, hashe, wynik i granice wykonania.
Walidator chroni hash fixture oraz porównuje ją z ponownym wykonaniem oryginału.
Raporty są w `artifacts/units/initialization/`; eksporty read-only w `export/`.

Pełna semantyka zapasów, uzbrojenia, załogi, obrażeń, poleceń, ruchu,
kolizji i AI pozostaje osobną pracą. Izolowany ctor i LoadDateBase nie są
dowodem działającej misji ani pełnej zgodności remake’u1:1.
