# Odbiorca BaseSystem i reset C45E — 2026-11-04

Potwierdzono rzeczywisty łańcuch obsługi komunikatu C45E. Wcześniejszy test
kończył się na zastępczej metodzie wirtualnej, dlatego sam nie dowodził
wyzerowania stanu Shift. Nowy dowód wykonuje oryginalne metody odbiorcy.

## Konstrukcja i kolejność

W `4ee4f8..4ee507` aplikacja tworzy MSystemClass z własnym wskaźnikiem
i identyfikatorem `0`, ustawia pod `4ee501` vptr `59b5e4`, a następnie zeruje
pole BaseSystem+20. Konstruktor `4e9340` i bazowy `5417e0` potwierdzają
offsety: identyfikator +14, aplikacja +18. To osobny obiekt, przechowywany
w aplikacji pod +d70. Tablica aplikacji `59b5c8` nie jest tablicą BaseSystem.

| Etap | Oryginalny adres | Wynik |
| --- | --- | --- |
| Producent | 4ee900 | Przy App+20 równym 0: prostokąt, C45E, potem 14A |
| Routing aplikacji | 540540 → 540560 → 540d20 → 540cc0 | C45E trafia do aktywnego systemu o ID 0 |
| Odbiór C45E | 4eff00, vptr+20 | Przy BaseSystem+20 różnym od 0 wywołuje ponownie 4eff00 z C45D(0) |
| Odbiór C45D(0) | 4eff00 | Zapisuje 0 do BaseSystem+20 przed przekazaniem komunikatu |
| Rozsyłanie systemu | vptr+18 = 541ee0 → 541f00 | Przekazuje `[0,0,100h,3,C45D,0,0,0]` do handlerów grupy 100h |

Aktywność rejestracji musi wynosić dokładnie `1`. Wartość FFFFFFFF nie jest
traktowana jak aktywność. Flaga bit0 pierwszego wpisu handlera zatrzymuje
dalsze rozsyłanie. Kolejność rekordów pozostaje kolejnością wywołań.

App+20 i BaseSystem+20 to dwa odrębne pola dwóch obiektów. Nie wolno
zastępować ich jednym stanem klawisza. Przy zablokowanym producencie lub
nieaktywnym BaseSystem stan Shift pozostaje bez zmian. Bezpośrednie C45E
do BaseSystem zeruje stan także wtedy, gdy dalsza wysyłka do handlerów jest
zablokowana aktywnością systemu.

## Walidacja

Wykonano 42 operacje bezpośrednie i 108 przypadków łańcucha producent–odbiorca:
trzy wartości bramki aplikacji, trzy wartości stanu Shift, trzy wartości
aktywności oraz rozmiary 800×600, 1920×1080, 0×0 i −1×−1.
Porównano koperty, kolejność odbiorców, rekurencję i końcowe pola pamięci.

Pięć mutacji wyłącznie w RAM emulatora zostało wykrytych: błędny odbiorca
w tablicy metod, pominięty zapis stanu, pominięty bit zatrzymania handlerów,
odwrócona bramka producenta i błędna wartość aktywności.

Korpus: `tests/fixtures/source_base_dispatch.json`, SHA256
`b3c30aefba0ceee812619cb3d33f5961d34c67fc3ebfbedc8f2e4d7f03776316`.
Narzędzia: `tools/probe_source_base_dispatch.py` i
`tools/validate_source_base_dispatch.py`. Eksporty instrukcji i pseudokodu:
`artifacts/native-base-vtable/source`. Raport: `validation.json` w tym samym
katalogu nadrzędnym. Końcowe callbacki handlerów oraz odbiorcy prostokąta
i 14A pozostają jawnymi granicami testu; nie wykonano ich grafiki lub świata.

## Próby całego oryginału

Cztery uruchomienia w izolowanej maszynie przeszły kontrolę IA32 i kontrolny
program PE32. Oryginalny EXE załadował się pod 400000, lecz nie osiągnął
breakpointu 4eff00. Próby 03/04 potwierdziły modalne okno `Error!`, a próba 04
odczytała treść: „The registry record is corrupted. Try to reinstall the game.”
To blokada konfiguracji instalacji, nie dowód błędu badanej funkcji.

Maszyna nie miała sieci, KVM ani montowania katalogu głównego hosta. Wejścia
były tylko do odczytu, gra uruchamiała się z prywatnej kopii w gościu,
breakpoint zmieniał wyłącznie pamięć procesu. Każda próba ponownie potwierdziła
SHA256 pliku oryginału. Kod wyjścia 0 maszyny nie został uznany za sukces gry:
we wszystkich czterech próbach `source_hit=false`.

## Granice i kolejny krok

Kod C#, zasoby Unity, build Windows oraz deterministyczny świat pozostają
bez zmian. Cel nadal wynosi 1920×1080, 16:9, pełny ekran. Nie potwierdzono
pełnego App/Life/AI, Windows 11, wydajności laptopa ani końcowej oprawy.

Analiza statyczna 4ee970 wskazuje wywołanie 4ee900 w gałęzi
WM_ACTIVATEAPP (`1C`, parametr aktywności 0). Następny krok to wykonanie tej
gałęzi x86 z kontrolowanymi usługami systemowymi, zanim zostanie odwzorowana
w cyklu wejścia Unity. Naprawa konfiguracji oryginału w gościu jest osobnym
krokiem diagnostycznym; nie należy wymyślać wpisów instalatora.

Prace są wznowione i kontynuowane autonomicznie. Niczego nie publikowano,
nie generowano podglądów ani paczek ZIP.
