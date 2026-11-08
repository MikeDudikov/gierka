# Integracja100/2 i zdarzeń310 w świecie — 2026-11-04

Zadanie100/2 wykonuje się teraz w istniejącym `ShipWorldStep`, przez tego
samego właściciela `ShipFleetMembership.Group.Task`. Nie dodano zegara,
menedżera grup, ECS, Update ani drugiej kopii członkostwa lub zajętości.
`SingleStepClock`, aktor, task i grid pozostają bez zmian w tym etapie.

## Kolejność x86

`Begin` wybiera ten sam krok40ms. Następnie, po kontrolach wejścia,
wykonywane są PrepareMail521500, SendMail522850 i rejestr542200.
Work grupy100/1 lub100/2 występuje w rzeczywistej pozycji floty.
Po każdym Tick aktora wynik4a49af/4a4a67 jest przekazywany do4a1700
poprzez istniejący UIgroup i indeks członka. Nie czekamy do końca pętli.

Przekazanie wyniku zaraz po Tick jest udokumentowaną granicą synchronizacji:
w ograniczonym Promote/Work nikt wewnątrz aktora nie odczytuje zdarzeń grupy.
Zachowuje ona kolejność względem następnego obiektu rejestru i Work floty.
Rozkaz20 wygenerowany przez grupę trafia do tej samej kolejki2e. Dostarczenie
następuje dopiero w kolejnej fazie poczty, bez dodatkowego flush.

Oryginał wykonuje4a1700 także dla100/1. Kod produkcyjny nie wybiera więc
obsługi310 na podstawie obecności kontekstu fali ani flagi diagnostycznej.
Grupa bez tasku w reprezentowanej ścieżce ma wyczyszczony wektor zdarzeń;
istniejący właściciel odrzuca takie zgłoszenie zgodnie ze swoją granicą.

## Jawny kontekst pamięci

Dodano przeciążenie `TryAdvance` przyjmujące `IReadOnlyList<short>`:
słowo signed16 sprzed każdej potencjalnej alokacji fali w bieżącym kroku,
w kolejności REJESTRU aktorów. Przed wykonaniem kopiuje wejście. Przy wizycie
floty mapuje słowa przez istniejące indeksy do kolejności członków grupy
i przekazuje stan, licznik, pending oraz kontekst do `WorkQueuedTask`.

Nie ma domyślnego117 lub0. Stare przeciążenie nadal obsługuje100/1,
a dla100/2 bez kontekstu odrzuca krok. Nieprawidłowy rozmiar kontekstu,
teren lub nieobsługiwane zdarzenie300/311 są odrzucane przed zmianą licznika,
poczty, tasku, aktorów i poprzedniego ukończonego odczytu diagnostycznego.
Nieprzyjęty poprawny krok nadal czyści odczyty tego podejścia jak wcześniej.

117 pozostaje jedynie wejściem z ograniczonego profilu oryginalnego CRT
w Wine. Odczyt spoza bufora w4cebc7 nie został poprawiony lub zastąpiony
wartością sterty CLR. Nie udowodniono uniwersalnego słowa Windows/pełnej gry.

## Pełne porównanie

Do wcześniejszych46scenariuszy dodano4nowe z grupami(13,11) i(13,12,11),
flotą przed/po statkach oraz słowami rejestru[32767,117,-32768]. Pierwszy
przebieg emituje odpowiednio tylko13 lub13,12. Zamiana kolejności rejestru
i członków jest wykrywana. Fixture `queued_world_mixed.json` SHA256:
`318e79be7d5af12ea4bc6e783a2263268cc662396ce574515dbb0a251184ee95`.

Wynik:50scenariuszy,5536klatek i16608stanów aktorów. Testuje rzeczywiste
C#taski, pocztę, rejestr, ruch, całe zdarzenia32B, trasy, nagłówki i publikacje.
Po starcie nie podaje C#pakietów z oryginału. To pełniejsza walidacja niż
wcześniejsze odtwarzanie samych aktorów sterowanych pakietami x86.

Osobny korpus100/1 wykonuje prawdziwe4a1700:31scenariuszy,1796klatek,
5388stanów. `normal_world_arrivals.json` SHA256:
`b3259f41b711fc7739eb920803aefdf7f248ef16a4f2a84c4ce62150be22e8d1`.
Porównanie obejmuje wszystkie310, bez filtrowania.

Historyczne fixture świata, restore i UI miały jawne ret-boundary dla4a1700.
Pozostają niezmienione i sprawdzają ten sam starszy zakres. Wyłącznie ich
testowe obserwatory pomijają nowo dostępne310; stan gry nie jest filtrowany
lub modyfikowany. `TRACE310` w próbie100/1 i pełny odczyt K w próbie100/2
sprawdzają nowe rekordy w całości. Nie zastąpiono oczekiwanych wyników danymi C#.

8testów PASS,0skip,188.276s:4nowe,3regresje świata i1287przypadków zegara.
Są10kontroli API, w tym błąd wejścia po już wykonanym kroku. Trzy nowe mutanty
wykrywają utratę310, błędną kolejność słów oraz przedwczesny odbiór20;
pięć wcześniejszych sprawdza pocztę, rejestr i stemple. Świeżo wykonano
dodatkowe korpusy x86 i historyczną gałąź świata. Log: `tests.log`.

Build Windows64Mono w Unity6000.3.27f2:152977451B,0warnings/0errors,
1920×1080,16:9,ExclusiveFullScreen. DLL:
`161a875ab0612b2945560d7adcd5f8922e45f56c144e6379b1b96cae683a517e`.
Raporty są w `artifacts/queued-world-integration`. Zamrożono275plików projektu.
Zmiana runtime to wyłącznie ShipWorldStep;72pozostałe C# bez zmian.

Player-first/last przeszły po30checkpointów,90stanów,300części,
1020odczytów kolejki,229publikacji i12pakietów;exit0. To regresja100/1
i dotychczasowego InputSystem, nie uruchomienie Shift w adapterze.
Nowy pełny świat100/2 sprawdzono na shippingDLL w testach Mono.
Znane ComputeBufferGC i komunikaty headlessALSA/debuggera pozostają.

## Granice i następne kroki

W zweryfikowanym zakresie kod jest zgodny z `SingleStepClock` i nie narusza
deterministycznego stanu. Prawdziwy Ship::Life nadal ma granicę wywołania
oryginalnych Promote/Work. Nie jest to dowód pełnej gry, AI, oprawy2026,
natywnegoWindows11, wydajności laptopa lub wszystkich historii sterty.

UI Shift pozostaje zablokowane do osobnego dowodu podczas ruchu oraz
podłączenia jawnego kontekstu do adaptera. Kolejny krok rozpoczęto przez
`probe_queued_ui_world.py`: źródłowe UI i świat porównują Shift, dopisywanie,
duplikat i powrót do100/1. Edycja składu300/311 i raport40 pozostają osobno.
Bez nowych PNG, ZIP, publikacji, aplikacji konfiguracji i nowych agentów.

Ten kolejny dowód już zakończono: [QUEUED_UI_WORLD_EVIDENCE.md](QUEUED_UI_WORLD_EVIDENCE.md).
12scenariuszy/2400klatek/48żądań/7344stany zgodne x86/C#/shippingDLL,
2testyPASS107.791s. Znaleziono też oryginalny21-częściowy WPMOVE w controlm.
Łącznie10testów w dwóch zestawach,330discovery bezfullrun.
