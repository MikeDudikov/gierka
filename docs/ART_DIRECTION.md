# Oprawa i obszar renderowania

Obowiązujący cel po ostatnim doprecyzowaniu użytkownika: **1920×1080, 16:9,
pełny ekran i pełny viewport rozgrywki**. Nie stosujemy letterboxa ani projekcji
całego dawnego ekranu 800×600. Interfejs ma własny układ na natywnym płótnie;
geometria jednostek, sylwetki i litery zachowują proporcje.

Użytkownik dopuścił nowe tekstury i modele silnie inspirowane oryginałem, jeżeli
odnowienie starych zasobów nie zapewni odpowiedniej jakości. Nie zmienia to
wymagania zgodności mechanik, treści, AI i tempa.

## Zasady produkcji zasobów

- Pierwowzór pozostaje kontrolną bazą sylwetek, palety, funkcji i czytelności.
  Nowy model lub tekstura wymaga porównania obok oryginału, w tej samej pozie
  i rozmiarze na ekranie. Nie dodajemy jednostek, uzbrojenia i motywów bez źródła.
- Ważne tła i elementy UI powstają co najmniej w rozdzielczości ich docelowego
  wyświetlania. Powiększona stara bitmapa nie jest gotowym remasterem.
- Świat gry wymaga osobnych modeli/tekstur, materiałów wody, terenu, budowli,
  jednostek oraz spójnych animacji. Nie uznajemy retuszu menu za modernizację gry.
- Nowa oprawa nie może zmieniać hitboxów, zasięgów, reguł widoczności, czasu
  animowanych zdarzeń ani informacji przekazywanych przez efekty.
- Fonty zachowują rozpoznane kształty, glify i metryki. Skalowalne, wygładzone
  odwzorowanie wymaga osobnego opracowania; nie zastępujemy ich przypadkowym TTF.
- Jakość i budżety tekstur/meshy będą mierzone w rzeczywistym playerze na laptopie
  i5 / 16 GB / RTX 3050 Ti. Sama rozdzielczość pliku nie dowodzi jakości lub płynności.

## Bieżący pierwszy krok

`artifacts/native-art/menu-background-widescreen-draft.png` jest nowym,
wspomaganym AI szkicem tła 16:9, silnie inspirowanym oryginałem.
Rzeczywisty plik ma **1672×941**, SHA-256
`d999d1294806d76cb838f39a57e591d9ecda51b176d61bc95fa419078278c4ee`.
Generator zwrócił te wymiary mimo żądania wyższej rozdzielczości.

**To tymczasowo powiększany szkic, poniżej docelowej jakości detalu**,
nie natywna tekstura 1920×1080 ani zatwierdzona oprawa dla wydania w 2026 roku.
Stager zachowuje źródłowe piksele; dopiero GPU powiększa tło do pełnego
ekranu z zachowaniem proporcji. Nie przybywa od tego nowych szczegółów.
Domyślny staging nadal wymaga co najmniej 1920×1080; wyłącznie jawne
`--allow-draft-upscale` umożliwia ten wariant roboczy, oznaczony w manifeście
`background_upscale_draft=true`. Wymagania końcowej jakości pozostają otwarte.

Nowe płótno UI ma 1920×1080, atlas przycisków 1878×288 i pojedyncze elementy
313×72. Przyciski i glify są osobną rekonstrukcją kontrolną bitmap oryginału,
wymagającą dalszego wykończenia. Tło służy ocenie motywów, kompozycji i
liternictwa, a nie potwierdzeniu ukończenia grafiki gry.

Pierwsza konkretna referencja świata obejmuje sześć kafli DIB i trzy
sprite’y, z potwierdzoną paletą bazową i jawnymi ograniczeniami kolorów:
[WORLD_ASSET_REFERENCE.md](WORLD_ASSET_REFERENCE.md). Nie powstały jeszcze
nowe modele rozgrywki ani pełny zestaw jej tekstur. Sama referencja świata
nie jest jego modernizacją.

Poprzedni szkic `menu-background-draft.png` 1402×1122 i dowody 1280×1024/5:4
pozostają historyczne. Nie służą jako domyślna oprawa nowego celu 16:9.
Aktualny kod i staging opisuje [FIRST_FRAME.md](FIRST_FRAME.md); wynik nowego
buildu i playera należy sprawdzić w [VALIDATION.md](VALIDATION.md).
