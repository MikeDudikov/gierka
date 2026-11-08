# Obsługa myszy w ograniczonej scenie statków

Stan: 2026-11-03. `--ship-pointer-reference` włącza diagnostykę jednego
sterowanego statku 0b. Zwykły Start nadal jest wyłączony. Pełna gra,
wszystkie jednostki i docelowa oprawa 2026 pozostają do wykonania.

## Połączenie wejścia ze światem

`WorldPointerInput` odbiera rzeczywiste zdarzenia `InputSystem.onEvent`.
Przetwarza zmianę położenia przed krawędziami przycisków i zachowuje
kolejność Down/Up, również wewnątrz jednego update. Scena diagnostyczna ma
1920×1080, pełny viewport i skalę2:1; piksel logiczny źródła zajmuje2×2
piksele ekranu. Pozycja świata to początek kamery plus pozycja logiczna.
Testowana kamera zaczyna się w komórce9,0, czyli w pikselu576,0.

Zdarzenie HD, które pozostaje w tym samym pikselu logicznym, nie wykonuje
źródłowego Move ani rysowania kursora. Faktyczne Move wykonuje kolejno
hover, ewentualną zmianę typu z rysowaniem w poprzedniej pozycji kursora,
a następnie obowiązkowe rysowanie w nowej pozycji. Cursor Life pomija
drugi draw, jeśli zmianę typu już narysowano. To dwa różne źródłowe przebiegi.
Poza mapą Move nadal przesuwa kursor; przyciski nie wydają rozkazów.

`ShipPointerHover` używa istniejącego pickera, opublikowanej pozycji,
stored frame i oryginalnych masek. Zachowuje źródłowe bramki SCREEN/WORLD,
cache komórki i ponowne sprawdzenie nieruchomego kursora podczas Life.
Dowód: [WORLD_POINTER_HOVER_EVIDENCE.md](WORLD_POINTER_HOVER_EVIDENCE.md).

Utrata fokusu, usunięcie lub wyłączenie urządzenia anuluje stan przycisków
bez wysyłania sztucznego Up. Ponowne uzbrojenie wymaga fizycznego zwolnienia
przycisków; przy unieważnionym cache mapy konieczna jest także zmiana
piksela logicznego. Ta polityka adaptera zapobiega rozkazowi z przytrzymania
sprzed anulowania. Nie jest dowodem identycznego pełnego window-proc oryginału.

## Zaznaczenie i rozkaz

Zwolnienie lewego przycisku nad przyjaznym 0b zaznacza statek. Zwolnienie
lewego przycisku z kursorem SEA7 wydaje rozkaz z zapamiętanej komórki.
Prawe zwolnienie na pustym miejscu usuwa zaznaczenie, a na zaznaczonym
statku resetuje kursor, pozostawiając wybór. Sam Down nie wydaje rozkazu.

Producent zachowuje osobne członkostwo UI5c i konsumenta symulacji5e.
Pierwszy ruch serializuje action41(group0), potem action20(X,Y,byte0).
Po usunięciu i ponownym wyborze powstaje następna grupa; kolejność może
wynosić41(-1),41(group1),20. Host konsumuje membership przed ruchem.
Nie podmieniono ziarna RNG: wykonane źródłowe selection/ACK przy wyłączonym
audio nie zapisują Ship+18. Szczegóły i granice:
[WORLD_POINTER_COMMANDS.md](WORLD_POINTER_COMMANDS.md),
[WORLD_POSITIVE_GROUP_MOVEMENT.md](WORLD_POSITIVE_GROUP_MOVEMENT.md).

Fizyczny core `ShipMoveOrder` pozostał bez zmian. Jego projekcja planera
dotyczy różnych grup statku sterowanego i siedmiu nieruchomych statków.
Nie jest to implementacja wspólnego planowania całej floty. Wymiana celu
podczas trwającego ruchu, zmodyfikowane komendy i wybór innych statków
pozostają poza jawnym zakresem tego trybu.

Próg przeciągnięcia zachowuje `abs(dx+1)>9 AND abs(dy+1)>9`. Aktywny
prostokąt zatrzymuje zwykły rozkaz i jest jawnie oznaczany jako nieobsługiwana
jeszcze selekcja ramką. Nie sprowadzono przeciągania do przypadkowego ruchu.

## Grafika i zegary

`ShipSelectionProgression` aktualizuje zaznaczenie przed każdą publikacją
kadłuba i w osobnej źródłowej gałęzi GetMessage0. Pierwsze zaznaczenie
tworzy niewidoczny selector; animacja ujawnia go później. Pasek zdrowia
znika przy rozpoczęciu animacji cofania zaznaczenia.

Ósmy staging dostarcza29 źródłowych obrazów w atlasie1024×128: zaznaczenie,
warianty kursorów, potwierdzenie rozkazu i pełny pasek zdrowia34×4.
Weryfikowane są hash atlasu i każdej płaszczyzny. Są to zasoby referencyjne,
nie ukończona modernizacja graficzna. Szczegóły:
[SHIP_POINTER_VISUAL_EVIDENCE.md](SHIP_POINTER_VISUAL_EVIDENCE.md).

Selector i pasek są osobnymi węzłami źródłowego depth1020. W tej scenie
następują po34 rendererach świata: pasek ma order44, selector45.
Po usunięciu paska selector ma44. Potwierdzenie ma46, a kursor jest ostatnim
SpriteRendererem z order32767, przypiętym do logicznej pozycji ekranu.
Korzysta z tego samego materiału URP i filtrowania Point co świat.
Systemowy kursor jest przywracany przy cleanup.

Ruch używa istniejącego zegara40ms z maksymalnie jednym krokiem. Cursor Life
ma osobną bramkę40ms w Unity Update, zgodnie ze zwykłym tempem aplikacji
przy przygotowanej szybkości5. Nie jest wywoływany przy każdej klatce renderera.
Źródłowe bramki animacji korzystają z przechwyconych milisekund.
[Dowód schedulera](POINTER_APP_CADENCE_EVIDENCE.md) rozróżnia BaseSystem/UI
od PlaySystem. Adapter40ms jest ograniczonym zegarem diagnostyki: pełna
polityka Sleep, pilna kolejka i kolejność wszystkich systemów nie zostały
przeniesione. Nie deklarujemy dokładnej kadencji całego RunApp.
Zatrzymania QA zamrażają symulację i UI, aby umożliwić stabilny odczyt obrazu.
Jawne przesunięcie czasu wizualnego w replay nie zmienia fazy zegara fizyki.

## Uruchomienie diagnostyki

```text
AncientConquestReference.exe --ship-pointer-reference --terrain-origin-x 9 --terrain-origin-y 0
```

`--ship-pointer-input-replay` dodaje urządzenie testowe i wysyła wyłącznie
`QueueStateEvent`; nie wywołuje domenowych metod zaznaczenia lub ruchu.
Opcja `--ship-pointer-replay-two-orders` dodaje drugi cel. Replay kończy
program przez Application.Quit. Jest to test prawdziwej ścieżki InputSystem,
ale nie sprzętowej myszy, natywnego Windows11 ani docelowego laptopa.

Aktualne wyniki kompilacji i playera: [VALIDATION.md](VALIDATION.md).
