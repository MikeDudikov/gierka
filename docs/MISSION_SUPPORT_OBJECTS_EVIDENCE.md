# Wspierające obiekty miss000: tagi50,57,58

Stan: 2026-11-02. Analiza dostarczonego, niezmodyfikowanego oryginału;
EXE SHA256 `cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Cel prezentacji remake’u pozostaje1920×1080,16:9,pełny ekran. Nie uruchomiono
pełnej gry, AI, zegara ani kompletnej inicjalizacji świata.

## Fabryka i rzeczywiste klasy

| Tag | Zasób / ID | Kod fabryki / wpis tabeli | Factory / ctor / vtable / handler |
| ---: | --- | --- | --- |
|50|OBJ_00000012 /18|5265;0x5c0e48|0x445190 /0x43b000 /0x597018 /0x441ba0|
|57|OBJ_00000013 /19|5275;0x5c0ec0|0x430010 /0x42ff40 /0x596990 /0x42ffc0|
|58|OBJ_00000014 /20|5276;0x5c0ec8|0x4177b0 /0x416290 /0x5957c0 /0x416f90|

Diagnostyka handlera50 nazywa klasę **TownObjClassTy** i plik `artem/town`.
Handler58 zawiera nazwę **DockClassTy**, plik `artem/Dock.cpp`.
Dla57 w badanym wrapperze nie znaleziono osobnej nazwy diagnostycznej;
potwierdzony prefix grafiki to **PT**, a wspólna klasa bazowa to
**ShipServiceDirObjClassTy** (`0x4e8660`) i ShipServiceObjClassTy
(`0x4e7640`). Nie nadano57 niepotwierdzonej nazwy bohatera ani jednostki.

Te obiekty nie są trzema dodatkowymi statkami tag200. Town ma obsługę
inwentarzy/produkcji; Dock ma m.in. kolejkę i późniejsze komunikaty tworzenia.
Nie przeniesiono tych niepełnych zachowań do Unity.

## Pola właściwe dla źródłowych payloadów trybu0

Wszystkie trzy mają kind1,side1,player1 i mode0 (`payload+16`). Wybrane są
właściwą tabelą Start scenario; sama obecność w zasobach nie dowodzi ich
przejścia przez mapową akceptację.

| Zasób | Bajty / SHA256 | X,Y z+20/+24 | Pole+28 | +32/+36 | +40 |
| --- | --- | --- | ---: | --- | --- |
|OBJ_00000012|1244;`baf2032043cbe22c8554350d43ec6b77f6ab992c281806403d87abd2f0251146`|19,0|100|zawartość klasowa Town|zawartość klasowa Town|
|OBJ_00000013|88;`aee2be68996a9cbcd64dc126fbf6ccfceec569a5135ae6e50c826a686275228f`|18,2|100|19,0|6|
|OBJ_00000014|88;`d2fe3f99c4b082c8875aad4e8804500099bb44c789192731a8f0116ede20bdc4`|21,2|100|19,0|6|

Town message2 pyta Mapę komunikatem0x4e9, następnie po dodatniej odpowiedzi
kopiuje tag,side/player,X/Y i pole100 do object+0x50,+0x54/+0x55,
+0x74/+0x78,+0xa8. Gałąźmode0 wybiera stan1; odrzucenie pozycji ustawia0xff.
Nie wolno przedstawiać zamrożonego stanu1 jako dowodu pełnego startu misji.

Wspólna inicjalizacja WorkLandObjClassTy `0x427f50` dla57/58 pyta Mapę0x4eb.
Po akceptacji kopiuje te same pola i, gdy bit8 object+0x1d8 jest ustawiony,
odczytuje orientację z+40 do object+0x1dc. Konstruktory57/58 ustawiają
object+0x1d8=30, więc ta gałąź dotyczy obu źródłowych rekordów.

Przy flagach0x30 i side!=4 kod kopiuje+32/+36 do object+0x1cc/+0x1d0.
To **żądane współrzędne powiązania**, nie ID18/19/20: oba rekordy podają19,0,
zgodne z pozycją Town. W trybie0 ten fragment nie wykonuje natychmiast
`0x427de0`; tryb1 i późniejsze komunikaty mają osobną ścieżkę wiązania.
Nie oznaczono jeszcze uzyskanego wskaźnika/ID rodzica jako potwierdzonego.

## Zamrożone recepty obrazu przy zaakceptowanym stanie1

Town używa rzeczywistego SetImages `0x43bd60`, dwie klasy usług wspólnego
LoadImages `0x4e7f90`. Obie procedury wykonują kwantyzację pola100 za pomocą
oryginalnego mnożeniaFPU, zaokrąglenia i konwersji; wynikiem jest3.
To wynik wykonania x86, nie zgadnięty wariant grafiki.

| Zasób | Obraz typu8 | Maska typu18 | Pivot ctor | Kotwica świata |
| --- | --- | --- | --- | --- |
|OBJ_00000012|TSPR_15013|TMSK_15013|0,0|1216,0|
|OBJ_00000013|PTSPR_157163|PTMSK_157163|0,7|1152,121|
|OBJ_00000014|DKSPR_158163|DKMSK_158163|0,7|1344,121|

Format Town to `TSPR_%1u%2u%1u%1u`: side1,tag50,state1,quant3.
Format usług to `%sSPR_%1u%2u%1u%1u%1u`: prefixPT/DK,side1,tag57/58,
state1,orientation6,quant3. Maski używają analogicznychMSK. Kolejność ostatnich
pól **orientacja,kwant** jest istotna; nazwa157136 byłaby błędna.

Konstruktory ustalają pivots object+0xc4/+0xc8. Obie procedury obrazu liczą
`worldX=(cellX<<6)-pivotX`, `worldY=(cellY<<6)-pivotY`, z arytmetyką32bit.
Nie wolno pozycjonować wszystkich klas w środku kafla ani ponownie dodawać
left/top z RLE. RAM w Town ma nazwę128×128, w usługach064×078; nazwaRAM sama
nie ustala wymiarów faktycznej klatki.

Trzy deskryptory typu8 w OBJECTS mają po44bajty i wskazują odpowiednio
`GRCNB_11`, `GRPRDNL_00`, `GRSYDNL_00`. Faktyczne rekordy tych nazw są typu6;
metadane mają128×128,64×64,64×64. Pełny loader typu8, maski i piksele wymagają
oddzielnego dowodu; nie zastąpiono ich interpretacją samej nazwyRAM.

## Wykonane kontrole

Katalog `artifacts/units/supporting-classes/` zawiera źródłowe payloady,
`source-payloads.json`, eksportyGhidra i dwa wąskie skrypty/raporty:

- `validate_support_copy.py` / `copy-validation.json`:3przypadki.
  Faktyczne konstruktory oraz kopiowanie zaakceptowanych pól wykonane
  **bez hooków**. Town zakres0x441cff…0x441d3e; usługi
  0x4280a1…0x4280f7 i0x4283af…0x4283f4. Pominięte są wcześniejsza akceptacja
  mapy oraz późniejsze skutki uboczne.
- `validate_support_images.py` / `images-validation.json`:3przypadki.
  Faktyczne konstruktory i kompletne LoadImages wykonane z natywnąFPU,
  initializerem dispatchuCRT, ceil/ftol, wyborem formatu i kotwicami.
  Przechwycono setjmp,wsprintfA,SetImages,odczyt/rozmiar maski i rejestrację
  położenia sprite’a. Stan1 oraz zaakceptowane pola message2 są dostarczonym
  kontekstem, nie wynikiem pełnego StartGame. SetImages dostaje referencyjną
  liczbę1dla jednoelementowego deskryptora; samego loadera klatek tu nie ma.
  Pole klatki pozostaje0z dostarczonego nowego sprite’a; nie jest to dowód
  pierwszej klatki faktycznie pokazanej przez oryginał.

Oba narzędzia sprawdzają SHA EXE,miss000 iOBJECTS. Żadna funkcja gry nie była
uruchamiana jako proces systemowy; nie zmieniono Unity ani wspólnych tools.
Nie potwierdzono mapowej akceptacji całego footprintu, rejestracji kolizji,
parentbinding, zawartości Town, ekonomii, aktywności produkcji, draworder,
widoczności, AI ani działania pełnej misji. Trzy recepty mogą służyć wyłącznie
jawnej, zamrożonej diagnostyce, dopóki te zależności pozostają otwarte.
