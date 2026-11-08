# Referencja statyczna głównego menu

Stan: 2026-11-02. `tools/render_reference_menu.py` składa obraz referencyjny
800×600 z oryginalnych zasobów i położeń odczytanych z programu. **Nie jest to
zrzut działającego oryginału ani implementacja w Unity.** Nie odtwarza jeszcze
interakcji, dźwięków, przejść, animacji ani adaptacji do 1920×1080.

## Materiał i odtwarzalność

Narzędzie przyjmuje wyłącznie zbadany `installed/ancient.exe`, SHA-256
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.
Zasoby menu są w `installed/missions/controlm.dkx` i `.dkd`, nie w
`files/DATA/CONTROLG`. Narzędzie odczytuje pliki, niczego z płyty nie uruchamia.

```sh
.venv/bin/python tools/render_reference_menu.py \
  reference/raw/ancient-conquest \
  --output artifacts/original/main-menu-reference-new
.venv/bin/python -m unittest tests.test_reference_menu -v
```

Katalog docelowy musi być nowy. Wyniki: `main-menu-state0.png` i `manifest.json`.
Manifest zawiera hashe trzech plików źródłowych, użytych zasobów, wycinków kodu
maszynowego, pikseli oraz PNG. Odtworzony tutaj obraz:
`artifacts/original/main-menu-reference/main-menu-state0.png`.

## Potwierdzona geometria i napisy

Konstruktor pod VA `0x530c40` ustawia bazę `(30,180)` i kroki `(40,52)`.
Dla przycisku o numerze `n` od 1 do 6 położenie wynosi
`(30 + 40n, 180 + 52n)`. Wszystkie płótna przycisków mają 174×40.
Deskryptory typu 11 naprzemiennie wskazują `0M_BUT0_` i `0M_BUT1_`.
Wybrany w referencji stan rysowania 0 korzysta ze sprite’ów `...00`.
Dekoder RLE zachowuje indeksy i maski pokrycia.

| Położenie | Zasób napisu PE RT_STRING | Tekst oryginalny | Szerokość tekstu | Lokalna pozycja tekstu |
| --- | ---: | --- | ---: | --- |
| 70,232 | 1042 | Best Conquerors | 130 | 22,8 |
| 110,284 | 101 | Start scenario | 112 | 31,8 |
| 150,336 | 1027 | Load game | 89 | 42,8 |
| 190,388 | 1026 | Custom missions | 132 | 21,8 |
| 230,440 | 1000 | MultiPlayer game | 136 | 19,8 |
| 270,492 | 103 | Quit game | 82 | 46,8 |

Powiązanie komend przycisków z zasobami napisów odczytano z obsługi menu
`0x531030..0x53149f`. Teksty narzędzie pobiera bezpośrednio z PE; występują
w tabeli oznaczonej LANGID 1049, chociaż ich odczytana treść jest angielska.
Sam LANGID nie jest podstawą do przypisania języka całego wydania.

Tło `0M_BKGND_00` ma 800×600; inicjalizacja pod `0x53d633` wiąże nazwę
`M_BKGND_00`, a ścieżka rysowania wyświetla je od `(0,0)`. Wybór prefiksu
zasobów `0` względem `3` zależy od nierozpoznanej jeszcze konfiguracji trybu.

## Font, przezroczystość i kolory

Menu wiąże font `S_FNT_BS` pod `0x53d76c`; tutaj jawnie wybieramy rekord
`0S_FNT_BS`. Z kodu wyszukiwania `0x547100`, szerokości `0x547210` i wysokości
`0x5471e0` wynika, że 10-bajtowe rekordy glifów zaczynają się na +102.
Pierwszy rekord jest glifem zastępczym. Liczba rekordów jest na +100,
a na końcu payloadu pozostaje 10 bajtów zarezerwowanych.

Rysowanie przycisku `0x4ea538..0x4ea53e` ustawia odstęp poziomy 1 i pionowy 0.
Pomiar `0x547240` sumuje szerokości glifów i dodaje odstępy wyłącznie pomiędzy
znakami. Wysokość wszystkich odczytanych etykiet wynosi 23. Tekst jest
centrowany całkowitoliczbowo w prostokącie 174×40. Wybrany stan 0 używa
wariantu atlasu 1; nie przypisujemy temu stanowi znaczenia „normalny” bez
porównania z wykonaniem gry.

Indeks przezroczystości fontu jest pod +66 i wynosi 6. Odczyt pod `0x547734`
przekazuje go do kopiowania; procedura `0x579260` pomija piksel o równym
**indeksie**, a nie o równym RGB. Eksport nie traktuje indeksu 0 jako
automatycznie przezroczystego. Użyte przez atlas kolory poza indeksem 6
odpowiadają tym samym indeksom palety tła; narzędzie sprawdza tę równość.
Sprite’y przycisków są na potrzeby tego obrazu mapowane przez paletę DIB tła.
Sposób instalacji palety w działającym menu wymaga jeszcze potwierdzenia.

## Kontrole i ograniczenia

Cztery testy sprawdzają: orientację i wyrównanie indeksowanego DIB, zachowanie
indeksów palety, glif zastępczy i odstępy, przezroczystość według indeksu nawet
przy powtarzającym się RGB oraz nieprzezroczysty indeks 0 w glifie.

Rzeczywisty obraz wygenerowano i obejrzano. Sześć zmierzonych szerokości
odpowiada powyższej tabeli. To dowód odtworzenia wybranej statycznej ścieżki
rysowania, **nie test zgodności z działającą grą**. Nadal wymagane są:

- porównanie z klatką menu uruchomionego oryginału;
- stany najechania, naciśnięcia i dostępności przycisków;
- wybór prefiksu rozdzielczości oraz palety w runtime;
- odtworzenie działania przycisków i przejść w Unity;
- osobna kontrola pełnego ekranu 1920×1080 w playerze Windows 11.
