# Obiektowe zasoby animacji — minimalna referencja raf miss000

Stan: 2026-11-02. Badanie lokalnego, niezmienionego oryginału. Dotyczy wyboru
zasobów i geometrii klatek raf typu601, bez uruchomienia pełnej gry. Nie ustala
ostatecznej oprawy2026, kompletnej sceny ani pierwszej widocznej klatki rozgrywki.

## Chronione źródła

| Plik pod `reference/raw/ancient-conquest` | SHA-256 |
| --- | --- |
| `installed/ancient.exe` | `cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021` |
| `files/DATA/OBJECTS.DKX` | `67aa31b7e7728a1c4f215c63932b55ea66f3ac1ecdb732bfd368bae2a8375f60` |
| `files/DATA/OBJECTS.DKD` | `01474065782a7170d54f564df2205572f8a0675411bef0f350dab55c3fd20e50` |

W `OBJECTS` jest852deskryptorów typu7. Ich inwentaryzację, metadane i nagłówki
zapisano w `artifacts/objects/animation/type7-inventory.json`. Poniższy dowód
wykonawczy obejmuje wyłącznie dwa konkretne deskryptory raf, nie wszystkie852.

## Loader typu7 i nazwy klatek

`GameObjClassTy::SetImagesReg` (`0x50d010`) wybiera rejestr sprite’a i wywołuje
metodę pod `0x546160` z jego tablicy wirtualnej. Dla typu7 metoda używa `mfRLoad`
(`0x5428d0`), którego gałąź7 wywołuje `mfSSprLoad` (`0x554b80`). Są to inne
zasoby i inna konwencja nazw niż terrainowe biblioteki `b_ALIB`.

Deskryptor ma49bajtów. Potwierdzone przez instrukcje loadera pola:

| Offset | Pole używane przez loader |
| --- | --- |
| `+0x00` | Prefiks nazw, ASCII zakończone NUL; nie nazwa samego deskryptora |
| `+0x20` | Bajt minimalnej liczby cyfr w nazwie |
| `+0x21` | Signed short początkowego numeru klatki |
| `+0x23` | Signed short liczby klatek |
| `+0x25` | W runtime nadpisywany wskaźnikiem bazy; wartości zapisanej nie wolno dereferencjonować |
| `+0x29/+0x2b` | Runtime width/height; loader zeruje pola, następnie bierze je z pierwszej rzeczywistej klatki |
| `+0x2d` | Początek odbudowanej tablicy wskaźników do klatek; nie używać wskaźników serializowanych w pliku |

Loader rezerwuje `count*4 + 49`bajtów i kopiuje49bajtów deskryptora. Dla
każdego `i` od0 do `count-1` woła `0x5443e0(prefix,digits,start+i)`, następnie
ładuje **typ6** przez `0x542e50`. Funkcja nazw faktycznie tworzy dla tych zasobów
format `%s%02u`. Nie należy dopisywać terrainowego `001` ani wyszukiwać klatek
innego typu. Surowe pola wymiarów mają w badanych plikach m.in. śmieciowe bajty;
nie stanowią wymiarów grafiki. Po wykonaniu loadera obie płaszczyzny mają64×64.

| Deskryptor typu7 | Prefiks | Cyfry/start/count | Początkowy zasób typu6 |
| --- | --- | --- | --- |
| `BREEF2SPR_1` | `BREEF2L_` | `2 / 0 / 30` | `BREEF2L_00` |
| `BREEF3SPR_1` | `BREEF3L_` | `2 / 0 / 30` | `BREEF3L_00` |

Przypisanie601, wariantów2/3 i stanu1 wynika oddzielnie z inicjalizacji raf
opisanej w `MISSION_OBJECT_POSITION_EVIDENCE.md`. `Reef::LoadImages0x4300a0`
zeruje pole indeksu klatki sprite’a. Indeks0 jest więc **stanem inicjalizacji**;
nie jest dowodem pierwszej klatki faktycznie pokazanej przez działającą grę.
`Reef::DrawSprite0x4301f0` może później zwiększać indeks według zegara gry.
Diagnostyczny widok zamrożonej klatki musi zachować to ograniczenie.

## Kotwica i maska

Rafy są rysowane w pełnej płaszczyźnie64×64 zakotwiczonej w źródłowym
`worldX/worldY`; nie pośrodku kafla ani według arbitralnego dolnego środka.
`SpriteEngine::0x5728e0` dla ścieżki RLE oblicza:

```text
logical width/height = sprite.width / sprite.height
content X = worldX + sprite.left
content Y = worldY + sprite.top
content width/height = sprite.box_width / sprite.box_height
```

`left/top` już określają położenie pokrycia RLE wewnątrz zdekodowanej pełnej
płaszczyzny. Przy nakładaniu takiej płaszczyzny na worldX/worldY nie wolno ich
ponownie dodawać, odejmować połowy64 ani traktować jako pivotu.

| Klatka | Wymiary | left/top/boxWidth/boxHeight | Flagi | SHA-256 zdekodowanego payloadu |
| --- | --- | --- | --- | --- |
| `BREEF2L_00` | `64×64` | `3,7,58,52` | `0x0c80` | `5628737a6ae599b57e9ddf411e3b628b9efd912fa756ddfab1d50be1913131f7` |
| `BREEF3L_00` | `64×64` | `4,2,57,59` | `0x0c80` | `4981177cab80615d4f5d1fbbe31abdfbefa8d51b7a96c183b914b2649a654a0a` |

Pokrycie wynika z zapisanych przebiegów RLE. Nie przypisujemy automatycznie
przezroczystości indeksowi0 ani6. Zamiana indeksów na bazową paletę świata
jest osobnym, już opisanym etapem (`WORLD_ASSET_REFERENCE.md`); efektów mgły,
widoczności, cieniowania i animowanych palet te dowody nie obejmują.

## Wykonane oryginalne instrukcje

`artifacts/objects/animation/validate_reef_animation.py` wykonuje w Unicorn
rzeczywisty `0x554b80` i `0x5443e0` z EXE o wskazanym SHA. Oba deskryptory
wybrały **60/60 poprawnych nazw**, załadowały wszystkie30+30klatek typu6,
odbudowały właściwe wskaźniki tablicy i uzyskały wymiary64×64. Hooki zastępują
wyłącznie odczyt zasobów, alokację, zwalnianie, setjmp oraz standardowe
`itoa/wsprintfA`; rzeczywiste formaty z kodu są zapisane w raporcie.
Nie jest to pełny test parsera bazy danych ani systemu operacyjnego.

Ten sam test wykonał kompletną procedurę bbox `0x5728e0` dla wszystkich60klatek
w trzech pozycjach `(0,0)`, `(1024,192)`, `(-64,128)`: **180/180 zgodnych
wyników**. Na tej ścieżce bbox nie było hooków. Raport:
`artifacts/objects/animation/reef-animation-validation.json`.

`validate_reef_pixels.py` wykonuje rzeczywisty dispatcher `0x574290` i jego
procedury RLE. Dla każdej z60klatek porównuje pełny bbox, wewnętrzny wycinek
i seek od wiersza17, każdy na dwóch wartościach bufora początkowego.
**360/360 buforów pikseli jest dokładnie zgodnych**, wraz z maską, stride i
bajtami ochronnymi. Żaden callee blittera nie jest hookowany. Raport:
`artifacts/objects/animation/reef-rle-validation.json`.
To porównanie indeksów i pokrycia, nie RGB/palety ani obrazu działającej gry.

Eksporty Ghidra są w `artifacts/objects/animation/export*`; oryginały nie były
modyfikowane. Nie edytowano Unity. Pełna kolejność renderowania sceny,
widoczność, rozkazy, zegar animacji, interakcje, AI i kompletna misja pozostają
poza zakresem tego małego dowodu.
