# Briefing — wybór trudności i kontrakt sterowania

Stan: 2026-11-02. Bieżący cel remake’u: 1920×1080, 16:9, pełny ekran.
Oryginał jest analizowany statycznie i przez ograniczone wykonanie instrukcji
w Unicorn; system operacyjny nie uruchamia tutaj EXE. SHA-256 oryginału:
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.

## Ważna korekta identyfikacji kontrolki

Trudność briefingu nie korzysta bezpośrednio z `RadioClassTy::GetMessage`
`0x54bae0` ani z typu3 `ButtonClassTy`. `MTaskSystemTy::CreateSystemObjects`
`0x53f2f0` wywołuje fabrykę z **ID5**. Tablica fabryki od `0x5c0d90` mapuje
ID5 na konstruktor `0x551a40`; ten tworzy obiekt z vtable `0x59bbbc`, którego
handlerem jest **`TabClassTy::GetMessage`, `0x550ba0`**. Odrębny `RadioClassTy`
ma w tej samej tabeli ID9. Przeniesienie zachowania tamtej klasy dawałoby
błędny moment wyboru i nieprawidłowe stany wizualne.

Wpisy tabeli, konstruktor i handler wyeksportowano lokalnie do
`artifacts/binary-analysis/briefing-controls/radio/`; dalsze funkcje i xrefy
znajdują się w podkatalogach `export/` i `factory/`.

## Ikony, etykiety i geometria

`StartSystemTy::LoadGraph`, `0x53d5a0`, zapisuje `T_PLAYER6` do `+0x194`,
a **`M_CHECK` do `+0x19c`**. MTask tworzy i rysuje kontrolki przez `+0x19c`.
`T_PLAYER6` jest sprite’em146×154 i nie jest ikoną trudności.

Odkodowane strumienie Type6 `0M_CHECK0` i `0M_CHECK1` mają **23×23**;
`0M_BUT2_00/01` oraz `0M_BUT3_00/01` mają **116×40**. Dowód wymiarów pochodzi
z odkodowanych nagłówków sprite’ów. Referencje kodu `+0x2c/+0x2e` dotyczą
struktury zasobu po wczytaniu, nie interpretacji tych samych offsetów jako
wymiarów w surowym 52-bajtowym rekordzie Type11. Manifest źródeł i hashy:
`briefing-controls/resource-evidence.json`.

Oryginalne prostokąty ikon: `(660,440,23,23)`, `(660,470,23,23)`,
`(660,500,23,23)`. Etykiety są osobnym rysowaniem od x690 i **nie należą do
obszaru kliknięcia**. Nazwy PE RT_STRING106/107/108 to Easy/Normal/Hard.
Wartości logiczne poziomu to 0/1/2; identyfikatory rekordów kontrolki to1/2/3.

MTask draw `0x53f4e0`, case `0x20f`, oraz PaintSTab `0x4eaa70` i mapowanie
`0x4e9940` dają:

| Stan rekordu TabClass | Znaczenie w tym ekranie | Sprite | Wariant fontu etykiety |
| ---: | --- | --- | ---: |
| 0 | niezaznaczony | M_CHECK0 | 1 |
| 1 | zaznaczony | M_CHECK1 | 2 |
| 2 | niedostępny | indeks2, fallback0 przy dwóch klatkach | 1 |

W drugim polu deskryptora tworzonego przez MTask jest0; do `Tab+0x70` trafia
więc wyłączona obsługa wyróżnienia hover. Poruszanie kursorem nie zmienia
stanu0/1 ani poziomu. Nie ma wizualnego stanu naciśnięcia w tej konfiguracji.

## Wybór następuje na lewy down

`TabClassTy::GetMessage`, case `0x61`:

1. Sprawdza **półotwarty** prostokąt: `x≤mouseX<x+width`, analogicznie y.
2. Pomija rekord, jeżeli jego ID jest już zapisane w `Tab+0x68` albo rekord
   ma stan2.
3. Dotychczasowy zaznaczony rekord dostaje stan0; nowy dostaje stan1.
4. `Tab+0x68` otrzymuje ID nowego rekordu i od razu jest wysyłana wiadomość
   rodzica `0x210` z **wskaźnikiem do całego nowego rekordu**.
5. MTask odczytuje pierwszy bajt ID i zapisuje `DIFFICULTY=ID−1`.

`0x62` (lewy up) niczego tutaj nie wybiera. Nie trzeba oczekiwać na zwolnienie,
a wyjście kursora poza ikonę po down nie cofa już dokonanego wyboru. Prawy down/up
`0x63/0x64` nie wybiera poziomu. Ponowny klik wybranego poziomu nie wysyła
wiadomości zmiany. Nie należy używać mechaniki anulowanego przeciągnięcia
przycisku głównego menu dla tej grupy ikon.

## Domyślny poziom i zachowanie wartości

`AncientAppTy` reset/config `0x5016a0`, gałąź `param_2&1`, zeruje
`0x9b` dwordów od `0x5ca528`. Zakres obejmuje bajt **`0x5ca78d`**, który nie
jest następnie ustawiany na1. Oznacza to **Easy0 przy czystej inicjalizacji**.
Dalsze domyślne mapowanie klawiszy `0x5014e0` nie nadpisuje tego bajtu.

Dodatkowe źródło danych: `installed/demo.dkx/.dkd` ma Type12 `DIFFICULTY`,
offset28392, długość4, bajty `00 00 00 00`, SHA-256
`df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119`.

`TuneGamePtr` `0x4ed700` wywołuje setter `0x4ed3e0`, który czyta nazwany rekord
DIFFICULTY; **jeżeli go nie ma, pozostawia globalną wartość**. W katalogu
miss000 takiego rekordu nie znaleziono. Wczytanie progresji pod `0x53069b`
może nadpisać wartość z zapisu. Dlatego nie twierdzimy, że każdy profil zawsze
ma Easy; właściciel stanu musi przechować bieżący wybór. Cancel zwalnia dane
briefingu i wysyła App `0x100`, bez wyzerowania globalnej trudności w tej ścieżce.

## Tekst, czas i skróty

MTask Paint `0x53f4e0`, wiadomość5, wywołuje `PaintSarr` `0x4eb2f0`.
Ten przekazuje do `WrSarr` `0x547cb0` **firstline0, count−1, x0, y0,
fontvariant2**: rysowane są wszystkie sformatowane wiersze od początku.
W przebadanym `MTaskSystemTy::Life`, `0x53fb30`, nie ma mutacji bufora tekstu
ani obszaru jego odsłaniania. Wartości3000ms i20000ms dotyczą stanów
uruchomienia/powtórzenia VOICE i flag audio. Nie są dowodem efektu typewriter.
Pełny timing i audio nadal wymagają oryginalnego runtime.

CreateSystemObjects ustawia akceleratory Start z surowymi kodami `0x1c`
i `0x39`; deskryptor Start zawiera też parę `0x38,0x1f`, a Cancel kod `0x01`.
Kody są zgodne z konwencjonalnymi scancode PC (Enter, Space, Alt+S, Escape),
ale pełna ścieżka tłumaczenia/modifierów i routing platformowy nie zostały
w tym etapie wykonane. To dowód zapisanych deskryptorów, nie test wszystkich
skrótów klawiaturowych. Cancel klikany ma potwierdzone message `0x16e` → App0x100.

## Implementacja i walidacja różnicowa

`BriefingDifficultySelection` jest czystą klasą C# w Runtime. Konstruktor
przyjmuje poziom0..2 oraz trzy prostokąty ikon i kopiuje ich geometrię.
`Process(message,x,y)` zwraca true tylko po rzeczywistej zmianie na left down.
Nie przechowuje stanu aplikacji, nie zapisuje konfiguracji i nie zmienia świata.

`tools/validate_briefing_difficulty.py` wykonuje rzeczywiste instrukcje
oryginalnego TabClass `0x550ba0` i helpera wyboru `0x550b70`, a następnie
kompiluje **rzeczywisty plik C# projektu** przez Mono z przypiętego Unity.
Porównuje selected0..2 oraz changed z emisją oryginalnej wiadomości.
Oryginalne rekordy/state i payload mają dodatkowe kontrole tylko po stronie x86.

Wynik: **558/558 kroków w222ciągach**, wszystkie trzy wartości początkowe,
oryginalne23×23 i natywne41×41, kliki i powtórki, granice, label/outside,
hover, down→leave→up oraz prawy przycisk. Dodatkowe10 kontroli C# sprawdza
niepoprawną konfigurację i własność skopiowanej geometrii; nie przypisujemy
oryginałowi tych wyjątków walidacyjnych.

Trzy hooki: setjmp zwraca normalnie; virtualpaint wyłącznie zapisuje wywołanie;
parentdispatch zapisuje wiadomość zamiast wykonywać MTask. Oryginalny pusty
base `0x542550` wykonuje się bez hooka. Nie testowano cyklu życia, OS-input,
shaderów, klawiatury, globalnej persystencji ani wpływu trudności na AI/gameplay.

```sh
.venv/bin/python tools/validate_briefing_difficulty.py \
  --output artifacts/binary-analysis/briefing-controls/difficulty-validation-next.json
.venv/bin/python -m unittest tests.test_briefing_difficulty -v
```

Pierwszy raport: `difficulty-validation-first.json`; focused unittest1/1
przeszedł bez pominięć. Wcześniejszy original-only trace `tab-pointer-trace.json`
ma17kroków i nie udaje porównania z C#. Narzędzie odmawia innego SHA oryginału
oraz nadpisania istniejącego raportu.

## Niezależny przegląd integracji runtime

Przejrzano read-only `RgbaResourceTexture.cs`, `BriefingPanel.cs` oraz ich
integrację w `NativeMenuFrame.cs`. Nie znaleziono nowej usterki P0/P1 w
następujących obszarach:

- Difficulty.Process jest wywoływany przed przyciskami panelu i zmienia
  wybór wyłącznie na down. Właścicielem bieżącej wartości pozostaje cachePanel;
  Cancel/reopen nie tworzy go na nowo i zachowuje wybrany poziom.
- Dla zwykłego ponownego otwarcia miss000 zachowanie ma źródłowy dowód:
  537ef0 ładuje właśnie miss000, a TuneGamePtr4ed700 wywołuje4ed3e0. Setter nie
  zapisuje globalnej trudności, jeżeli lookupDIFFICULTY zwracaNULL. Pełny indeks
  miss000 ma63wpisy i nie zawiera tej nazwy; wynik i hashe zapisano w
  `briefing-controls/miss000-no-difficulty.json`. SetMode53c8b0 i
  PlNameCreate53d1b0 również nie zmieniają poziomu. Rekord demoDIFFICULTY0
  nie należy do tej zwykłej ścieżki ponownego otwarcia miss000.
- Cancel wraca do menu, resetuje stany pointera i kończy bieżący dispatch;
  release nie propaguje się do przycisku ukrytego menu. Main dispatch ma break
  po otwarciu panelu. Nie stwierdzono click-through w odczytanym przepływie.
- Start ma jawnie stan0/disabled i nie emituje komendy. Jest to ograniczenie
  prototypu z niegotowym światem, nie twierdzenie, że oryginalny Start jest
  domyślnie niedostępny.
- Manifest sprawdza canvas1920×1080, kolejność Start/Cancel i trzech poziomów,
  rozmiary atlasów i prostokąty. RgbaResourceTexture ogranicza wymiary i wymaga
  dokładnie width×height×4 bajtów. TextAsset jest zwalniany po odczycie;
  częściowo załadowane tekstury panelu są zwalniane przy błędzie, a cache jest
  sprzątany przez właściciela przy zakończeniu.

Znaleziono i przekazano P2 dotyczące dotychczasowego diagnostycznego replay:
po nowej komendzie Startscenario101 dawny scenariusz zakładał dalszą obecność
menu. Rodzic potwierdził zmianę replay o Cancel→menu przed kolejnymi komendami.
Przegląd nie wykonuje playera; dowody kompilacji i faktycznych przejść/pikseli
pozostają w głównym raporcie walidacji roota. Hashy odczytanych źródeł dotyczy
`briefing-controls/runtime-review-source-sha256.json`.
