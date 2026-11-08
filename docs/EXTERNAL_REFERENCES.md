# Zewnętrzne materiały referencyjne

Stan: 2026-11-02. W tej sesji **nie pozyskano ani nie obejrzano gameplayu
z YouTube**. Nie przypisujemy niezweryfikowanych nagrań do dostarczonego wydania
gry i nie wyprowadzamy z metadanych reguł AI, ekonomii ani tempa.

## Próba odczytu

Sprawdzono publiczne wyszukiwanie:

- [Ancient Conquest: Quest for the Golden Fleece — gameplay](https://www.youtube.com/results?search_query=Ancient+Conquest+Quest+for+the+Golden+Fleece+gameplay).
- Krótsze zapytanie `Ancient Conquest gameplay`, aby rozpoznać odpowiedź proxy.

Druga próba, wykonana poza sandboxem poleceń z zachowaniem platformowego proxy
i weryfikacji TLS, zakończyła się `CONNECT tunnel failed, response 403`
(`curl` kod 56). Odpowiedź proxy miała status `HTTP/1.1 403 Forbidden` i nagłówek
`server: envoy`, czas `2026-11-02 00:41:51 UTC`. Nie uzyskano treści wyników.

Jednocześnie odczyt konfiguracji środowiska raportował aktualną, egzekwowaną
politykę zawierającą `www.youtube.com`, `youtube.com` i `i.ytimg.com`.
Sam ten wpis nie dowodzi działającego dostępu. Przyczyna rozbieżności nie została
ustalona; nie zmieniano konfiguracji ani nie obchodzono odmowy proxy.

Po rzeczywistej zmianie polityki na **unrestricted**, przy aktualnym statusie
`connected` i `enforced`, ponowiono oba zapytania na tej samej maszynie.
YouTube nadal odrzucał tunel proxy: `CONNECT 403`, kod `curl` 56, czas odpowiedzi
`2026-11-02 00:51:32 UTC`. To wynik po zmianie sieci, a nie ponowne przytoczenie
wcześniejszego błędu. Nowe dowody: `youtube-response-open-headers.txt` i
`reference-access-status-unrestricted.json` w `artifacts/references/`.

Ograniczone próby niezależnych źródeł również nie dały zweryfikowanego materiału
tej gry: wyszukiwanie Steam zwróciło inne tytuły; wskazana ścieżka GOG przekierowała
do ogólnego katalogu; Google i DuckDuckGo wymagały interakcji przeglądarki,
a wyszukiwanie MobyGames zwróciło HTTP 403. Bing zwrócił niepowiązane wyniki
słownikowe mimo pełnego tytułu w zapytaniu. Nie przypisano tych wyników do gry.
Nie instalowano downloaderów, nie wykonywano skryptów serwisów i nie pobrano
nieograniczonych plików wideo.

Dowody lokalne: `artifacts/references/youtube-response-headers.txt` oraz
`artifacts/references/reference-access-status.json`. Materiały te nie są
nagraniami ani zrzutami rozgrywki.

## Zakres dalszej weryfikacji

Po przywróceniu dostępu każde wybrane nagranie powinno mieć zapisany pełny URL,
tytuł, kanał, datę publikacji i długość, a obserwacje — konkretne znaczniki czasu.
Miniatura nie jest obejrzanym gameplayem. Ekrany i zachowania należy porównać
z zasobami dostarczonej płyty; nagranie innego wydania lub łatki wymaga takiego
oznaczenia. Widoczny przebieg nie potwierdza pełnej zgodności ukrytych reguł AI.

Do tej pory podstawą analizy pozostają dane płyty opisane w
[ORIGINAL_CATALOGUE.md](ORIGINAL_CATALOGUE.md), statyczna referencja menu w
[UI_REFERENCE.md](UI_REFERENCE.md) oraz jawne ograniczenia uruchomienia
[ORIGINAL_RUNTIME.md](ORIGINAL_RUNTIME.md).
