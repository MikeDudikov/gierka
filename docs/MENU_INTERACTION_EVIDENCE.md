# Główne menu — zachowanie przycisków potwierdzone kodem

Stan: 2026-11-02. Oryginał: `installed/ancient.exe`, SHA-256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Adresy są VA obrazu PE32 o bazie `0x400000`. To analiza lokalna oraz emulacja
wybranej procedury x86; nie zrzut ani pełna sesja oryginalnej gry.

## Konstrukcja i znaczenie stanów

`MMenuSystemTy::CreateSystemObject` (`0x530c40`) tworzy sześć przycisków przez
`MSystemClassTy::CreateMBut` (`0x4ea2d0`). Początkowy stan przekazany do każdego
przycisku wynosi **1**. Deskryptory z `StartSystemTy::LoadGraph` (`0x53d5a0`)
mają pole typu przycisku `+0x10 = 1`. Tworzony descriptor ma 0x176 bajtów,
przed wypełnieniem jest zerowany. `CreateMBut` nie ustawia jego pól `+0x124`
i `+0x128`; po skopiowaniu przez `ButtonClassTy::GetMessage` odpowiadają one
polom obiektu `+0x12a/+0x12e`. Menu zatem nie używa dodatkowej maski trafienia
wywoływanej przez `0x5575d0`; obowiązuje prostokąt.

Handler przycisku to **`ButtonClassTy::GetMessage`, `0x54aab0`**. Dla typu 1:

| Stan `this+0x1c` | Znaczenie z warunków handlera | Sprite w `PaintMBut` | Wariant fontu |
| --- | --- | ---: | ---: |
| 0 | wyłączony; brak obsługi down/up | 0 | 1 |
| 1 | zwykły, kursor poza przyciskiem | 0 | 2 |
| 2 | naciśnięty | 1 | 3 |
| 3 | najechany | 1 | 0, następnie 3 |

Wcześniejsza rekonstrukcja `main-menu-state0.png` jest nadal poprawnym dowodem
rysowania stanu 0, ale **nie przedstawia domyślnego aktywnego menu**. Nie
przypisujemy jej już znaczenia normalnego stanu przycisków.

`PaintMBut` (`0x4ea470`) wywołuje `0x4ea280`, które zwraca sprite 1 tylko dla
stanów 2 i 3; pozostałe stany używają sprite 0. Po ustawieniu odstępów 1/0
stan 3 rysuje napis wariantem fontu 0 w pełnym prostokącie, potem wariantem 3
w prostokącie szerokość−4 i wysokość−4. `0x5470c0` ustawia ten prostokąt,
`0x547980` centruje tekst dzieleniem całkowitoliczbowym. Dla menu druga
warstwa przesuwa się o **−2,−2** względem pierwszej. Pozostałe stany mają
jedną warstwę wyśrodkowaną w pełnym prostokącie 174×40.

## Ruch, naciśnięcie i zwolnienie

Oryginał rozpakowuje pozycję z dwóch unsigned16 w `message+0x18`. Flagi
porównane w emulatorze: `this+0x196` naciśnięcie, `+0x19a` najechanie,
`+0x1c6` trafienie wewnątrz. Nie są to kopie właściwości silnika Unity.

- **Move `0x60`:** prostokąt zawiera lewą/górną krawędź i wyklucza prawą/dolną.
  Handler najpierw aktualizuje flagę `Inside`, również dla stanu wyłączonego.
  Wejście kursora ustawia stan 3 i flagę najechania, jeśli nie była ustawiona.
  Wyjście ustawia stan 1 oraz kasuje najechanie, naciśnięcie i `Inside`.
- **LeftDown `0x61`:** ten sam półotwarty test prostokąta. Trafienie ustawia
  `Inside`; przy nieustawionej fladze naciśnięcia ustawia stan 2 i tę flagę.
  Typ 1 nie emituje jeszcze komendy aplikacji.
- **LeftUp `0x62`:** test obejmuje także prawą/dolną krawędź. Komenda jest
  emitowana wyłącznie, gdy flaga naciśnięcia nadal jest ustawiona. Stan staje
  się 3 przy `Inside != 0`, inaczej 1; flaga naciśnięcia zostaje skasowana.
- Ruch poza przycisk podczas przytrzymania kasuje naciśnięcie. Powrót kursora
  i zwolnienie nie aktywują wtedy przycisku. Samo zwolnienie bez down też nie.
- Zwolnienie poza przyciskiem **bez wcześniejszego Move poza** pozostawia flagę
  naciśnięcia w oryginale. Adapter Unity nie powinien „poprawiać” tej reguły
  bez jawnego opisania zmiany. Test zawiera ten szczególny ciąg.

Własna polityka hosta Unity przy utracie fokusu (`CancelPointer`) jest osobno
opisana w implementacji. Nie uznajemy jej za potwierdzoną regułę oryginału.
Nie przypisujemy zbadanym trzem komunikatom kompletnej obsługi klawiatury,
prawego przycisku myszy, dźwięków lub pozostałych typów kontrolek.

## Komendy głównego menu

Konstruktor `0x530c40` ustawia parę click/paint; handler menu `0x531030`
wiąże paint z etykietą PE RT_STRING. Ustawiony tam callback kliknięcia nie
jest numerem etykiety ani callbackiem rysowania.

| Etykieta | Click | Paint | RT_STRING | Bezpośrednia ścieżka click |
| --- | --- | --- | ---: | --- |
| Best Conquerors | `0x1db` | `0x1dc` | 1042 | post App `0x10a` |
| Start scenario | `0x168` | `0x169` | 101 | `0x53d1b0`, `0x53c8b0(0)`, `0x537ef0(app,0,0)` |
| Load game | `0x1cf` | `0x1d0` | 1027 | post App `0x108` |
| Custom missions | `0x1cd` | `0x1ce` | 1026 | post App `0x107` |
| MultiPlayer game | `0x16a` | `0x16b` | 1000 | warunek `0x53cd10`, potem post App `0x104` lub błąd |
| Quit game | `0x164` | `0x165` | 103 | przekazanie App `0x131` |

`Start scenario` nie może zostać zastąpione arbitralnie wymyśloną listą misji.
Procedura `0x537ef0` sprawdza nośnik/tryb i ładuje ścieżkę
`MISSIONS/miss%d%02d` z argumentów; odczytuje dane scenariusza oraz wysyła
kolejne komunikaty startowe (`0x10c` albo warunkowo `0x128`). Samo odtworzenie
menu nie odtwarza tych danych ani świata.

## Quit: bez dialogu, z wygaszeniem palety

Click `0x164` pod `0x531219` przekazuje wiadomość `0x131` do aplikacji.
`AncientAppTy::GetMessage` (`0x4ec1a0`), case `0x131`, wywołuje
`AncientAppTy::DarkScreen` (`0x4ef2e0`) z parametrami **50,5**, następnie
ustawia `app+0x1c = 1` (flaga zakończenia pętli). **Brak pytania o zgodę lub
MessageBox w tej ścieżce menu.** Istnieje osobna warunkowa gałąź komunikatu
sieciowego przed wygaszeniem; nie jest częścią lokalnego prototypu menu.

`DarkScreen` odczytuje paletę i wywołuje `0x54a3f0`. Ten rozpoczyna licznik
od 0 i odczytuje `timeGetTime`; następnie wywołuje `0x54a2c0`, aż licznik
osiągnie 50. Krok dopuszczany jest przy `now >= last+5`; `last` staje się
`now`, więc nie ma nadrabiania opuszczonych kroków. Pierwszy krok następuje
najwcześniej po 5 ms, ostatni po co najmniej 250 ms. To nie jest gwarancja
rzeczywistego czasu trwania 250 ms na dowolnym hoście.

Krok `i = 0..49` wywołuje zmianę palety `0x549eb0` z malejącą składową
`100 - trunc((100.0 / 50) * i)`. Konwersja `0x549b30` przechowuje składowe
w kolejności **H,L,S**, gdzie `L=(minRGB+maxRGB)/2`. Mnożnik światła wynosi
zatem 1.00,0.98,…,0.02; hue i saturation pozostają przy mnożniku 1.
Po pętli paleta jest zerowana. Zwykłe nakładanie czarnego prostokąta na RGB
nie jest matematycznie tą samą operacją. Dokładność przeliczenia float→byte
wymaga osobnej walidacji przy implementacji efektu na nowym materiale HD.

W bieżącym etapie prototyp Unity po komendzie Quit wywołuje `Application.Quit`.
Wygaszenie HLS jest **osobnym kolejnym etapem i jawną różnicą prezentacji**;
nie deklarujemy pełnego odtworzenia ścieżki kończenia oryginalnej aplikacji.

## Test różnicowy i granice dowodu

`tools/validate_menu_button.py` wykonuje oryginalne instrukcje `0x54aab0`
w Unicorn 2.1.4 oraz kompiluje **rzeczywisty** plik
`Runtime/MainMenuButton.cs` z projektu Unity. Fixture
`tests/fixtures/MenuButtonProbe.cs` otrzymuje te same ciągi komunikatów.

Potwierdzono **150 kroków w 44 ciągach**, porównując stan, trzy flagi oraz
fakt emisji komendy. Przypadki obejmują normalne kliknięcie, down bez hover,
zwolnienie bez down, drag poza/powrót, powtarzane down/up, ruch podczas down,
stan wyłączony, każdą krawędź, narożnik oraz współrzędne 0 i 65535.
Dodatkowo po stronie oryginału sprawdzono zerowy wynik, odtworzenie łańcucha
wyjątków i liczby wywołań przeciętych procedur.

Przecięte wywołania: `__setjmp3` (`0x587318`) zwraca 0, bazowy handler
(`0x555b80`) i syntetyczny renderer vtable są no-op, transport komendy
(`0x5425a0`) zapisuje żądanie. Nie uruchamia to aplikacji ani efektów jej
komend. Test nie porównuje pikseli i nie dowodzi zgodności całej gry.
Polityka utraty fokusu Unity nie jest objęta porównaniem z x86.

```sh
.venv/bin/python tools/validate_menu_button.py \
  --output artifacts/binary-analysis/menu-interaction/button-validation-new.json
.venv/bin/python -m unittest tests.test_menu_button -v
```

Raporty bieżącego etapu: `button-validation-first.json` i powtórzenie przez
bezpośrednie wywołanie skryptu `button-validation-direct.json` pod
`artifacts/binary-analysis/menu-interaction/`. Narzędzie odmawia nadpisania
raportu oraz analizy innego SHA oryginału. Brak opcjonalnego oryginału lub
kompilatora jest jawnym pominięciem w unittest; inny hash lub niezgodność nie.

Eksporty Ghidra readOnly są w tym samym katalogu: `export/` (menu i rysowanie),
`export-buttons/` (handler przycisku), `export-app-palettes/` (App GetMessage)
i `export-color/` (konwersja HLS). Oryginał nie był zmieniany.
