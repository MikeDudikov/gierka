# Briefing miss000 — format tekstu i składanie wierszy

Stan: 2026-11-02. Analiza statyczna i wykonanie wyizolowanego formatowania
w Unicorn; nie jest to uruchomienie oryginalnej gry ani pomiar ujawniania
tekstu/audio. Badany EXE SHA256:
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.

## Dane i deserializacja

`0x549480` ładuje typ23 DISCRIPTION, a `0x56e730` deserializuje zapisany SArr.
Nagłówek ma24bajty (sześć DWORD): flagi, pozycja, liczba elementów na+8,
pojemność+12, przyrost+16, historyczne pole wskaźnika+20. Po nagłówku jest
`ceil(count/8)`bajtów bitmapy obecności. Element0 odpowiada bitowi7 pierwszego
bajtu, element1 bitowi6 itd. Obecne elementy mają kolejne łańcuchy zakończone
NUL; nieobecny slot nie zużywa bajtów stringa. Pole wskaźnika z pliku nie
jest adresem do dereferencji.

Miss000 ma16elementów i bitmapęFFFF. Dane zaczynają się na+26, a wszystkie
16łańcuchów kończą się dokładnie z końcem payloadu594bajty. SHA256 payloadu:
`c785a8550585b6ead4b07110db48578d301f2a87cf208ef865336e274a0f408b`.

## Parametry pochodzące z programu

`MTaskSystemTy::LoadData`0x53ee80 ustawia odstępy fontuS_FNT_MH na1,1 przez
0x547080. Następnie wywołuje FormIndentSarr0x548240 z:

| Wartość | Źródło |
| --- | --- |
| Separatory słów ` ,.;:!?/\\()[]{}` | Łańcuch pod0x5be7e4 |
| Separator akapitu `@` | Łańcuch pod0x5c2398 |
| Szerokość630 | MTaskSystem+0xc0, konstruktor0x53ecd0 |
| Start0 / liczba-1 | Wszystkie elementy SArr |
| Prefiks dwóch spacji | Łańcuch pod0x5c2640 |

NUL jest granicą fizycznego stringa w SArr. **Nie oznacza automatycznie
nowego wiersza.** `@` kończy zgromadzoną grupę, a każda taka grupa jest
osobno formatowana. Funkcja dodaje substring przed `@`, nawet jeżeli jest
pusty; po końcu fizycznego stringa dopisuje pozostały niepusty substring.
Przed formatowaniem grupy wstawia prefiks `  ` jako osobny element SArr.

Miss000 zawiera wyłącznie ASCII bez sterowania kolorem `&`. Ogólne funkcje
fontu rozpoznają `&` i następną cyfrę szesnastkową, gdy flaga fontu+0x82 jest
włączona; tego nie należy zastępować nieudokumentowanym parserem Unicode.
Poniższe wykonanie szerokości ograniczono jawnie do tekstu bez `&`.

## Dokładny algorytm FormSarr

`0x547f40` wywołuje tokenizer `0x547e60`. Token obejmuje pierwszy napotkany
separator kończący; kolejne spacje mogą więc być osobnymi tokenami. Tokenizer
nie usuwa znaków. Szerokość mierzy `0x547240`, tj. sumę szerokości glifów
z odstępem1 tylko pomiędzy widocznymi znakami.

Pseudokod dla grupy bez sterowania kolorem (takiej jak miss000):

```text
line = ""
line_width = 0
first_emitted = true
for physical_string in group:
    for token in tokens_including_ending_delimiter(physical_string):
        if line_width + measure(token) + horizontal_spacing > width_limit:
            if line != "":
                emit(line if first_emitted else lstrip_space_tab(line))
                first_emitted = false
            line = ""
        line += token
        line_width = measure(line)

    saved = line
    if line != "":
        line += delimiters[0]   # jedna spacja po niepustym buforze
    line_width = measure(line)
    if line_width > width_limit:
        line = saved
        if line != "":
            emit(line if first_emitted else lstrip_space_tab(line))
            first_emitted = false
        line = ""
        line_width = 0

if line != "":
    emit(line if first_emitted else lstrip_space_tab(line))
```

W gałęzi overflow przed dopisaniem tokenu oryginał nie zeruje od razu starego
`line_width`; nie jest on jednak ponownie używany przed `line += token`
i ponownym pomiarem nowej linii. Ta kolejność nie oznacza dodatkowego wcięcia.

`0x571250` usuwa wyłącznie początkowe spacje/tabulatory przy emisji wszystkich
wierszy poza pierwszym w danej grupie. Nie usuwa spacji końcowych. Długi token
może przekraczać szerokość; funkcja nie dzieli go automatycznie na znaki.

Prefiks jako osobny string i dodatkowe spacje po stringach mają widoczny
skutek: typowe pierwsze linie akapitów otrzymują trzy spacje, a początkowy
znak `@` daje pierwszy wiersz złożony z czterech spacji. Nie należy usuwać
tych wierszy ani normalizować podwójnych spacji w treści.

## PaintSarr — brak centrowania pionowego

Handler0x53f4e0(message5) wywołuje PaintSarr0x4eb2f0 z prostokątem20,80,630,440,
fontemS_FNT_MH, odstępami1,1 i wariantemfontu2. Wrapper wywołuje WrSarr0x547cb0:

```text
WrSarr(array, start_index=0, count=-1, x=0, y=0, font_variant=2)
```

Parametry0,-1 to indeks i liczba elementów, **nie pozycja x/y**. X iY są tutaj
zerowe, więc ciało tekstu nie jest centrowane. Funkcja centruje pionowo dopiero
przy y<0. Ogólna wysokość tablicy (0x547580) to suma maksymalnych wysokości
glifów każdego wiersza plus `vertical_spacing*(count-1)`. Rysowanie kolejnych
wierszy (0x547cb0) dodaje wysokość danego wiersza i odstęp pionowy1.

Odzyskane15wierszy miss000 mają po18px wysokości, łącznie284px. LokalneY:
0,19,...,266. W oryginalnym prostokącie tytuł (drugi wiersz) jest naY99,
a ostatni wiersz naY346. Nie wypełnia się sztucznie całego obszaru440px.
Wariant2 pozostaje wyjściowym kolorem wszystkich tych zwykłych stringów.

## Odtwarzalne wykonanie oryginalnych instrukcji

`artifacts/briefing/text-evidence/emulate_text.py` wykonuje oryginalny x86
od0x548240 i pełne funkcje FormSarr/tokenizera. Przecięte są tylko:

- zarządzanie SArr (alokacja, append, insert, remove, concat i zwolnienie),
- zwykły powrót setjmp,
- pomiar szerokości: rzeczywiste glify0S_FNT_MH z odczytanego kontenera,
  odstęp1, jawne odrzucenie tekstu z `&`.

Hooki nie przepisują podziału na tokeny, akapity ani wiersze w Pythonie.
Nie emuluje się rendererów, audio, timerów ani pozostałych stanów fontu.
Wynik15wierszy, szerokości i wysokości oraz liczba wywołań hooków:
`artifacts/briefing/text-evidence/original-formatted-lines.json`.
Eksporty Ghidra są pod`text-evidence/export/`, skrypt eksportu i log obok.
To punkt odniesienia dla implementacji parsera, nie dowód całego briefingu.

## Mocniejsze wykonanie z natywnym pomiarem glifów

Dodatkowy `emulate_text_full_native.py` pod tym samym katalogiem wykonał także
oryginalne `0x547240/0x547210/0x547100` oraz `0x5472e0/0x5471e0`, z obiektem
fontu wskazującym rzeczywisty payload0S_FNT_MH. Nie hookuje pomiaru szerokości
ani wysokości. Wynik jest identyczny:15wierszy, szerokości i wysokości zgodne
z pierwszym ograniczonym probe. Raport:
`original-formatted-lines-full-native.json`. Pozostały jedynie jawne hooki
zarządzania tablicami i normalnego powrotu setjmp; nie badano błędów alokacji.
Pierwszy limit2mln instrukcji był niewystarczający dla natywnego wyszukiwania
glifów; końcowy bieg z limitem50mln doszedł prawidłowo do powrotu funkcji.

`0x5469c0` ma ważny warunek: nie dokleja separatora do pustego bufora. Dla
FormSarr([""]) poprawny wynik to pusta tablica, nie jeden wiersz ze spacją.
Prefiks powoduje, że ten warunek nie zmienia opisanych15wierszy miss000.
