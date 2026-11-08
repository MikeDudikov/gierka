# Komenda41 i grupa przy normalnym ruchu pojedynczego statku

Stan:2026-11-03. Dowód źródłowy wykonuje oryginalne instrukcje x86.
Nie dodaje implementacji grup ani wejścia Unity. Bazuje na
[źródłowej drodze kursora](WORLD_COMMAND_SOURCE_EVIDENCE.md) oraz zamrożonym
`tools/probe_ship_move_order.py`,bez edycji tego pliku i C#.

## Dwa oddzielne pola

`0x49bd60 AddActorToGroup` zapisuje lokalny indeks pod `actor+0x5c`
i emituje action41 z payloadem6 B `01,<int32 group>,<byte0>`.
`ShipGetMessage0x4dc630` wywołuje najpierw bazowe
`GameObjGetMessage0x50c970`. Dla message280f/action41 z pierwszym bajtem1
instrukcja `0x50ca16` kopiuje low16 payloadu+1 do **actor+0x5e**.
Późniejszy handler statku4e2ba0 nie dodaje efektu dla tego wariantu.

W faktycznym wykonaniu payloadu `010000000000` jedyny zapis do statku to
word pod+0x5e:FFFF→0000. Zmienione bajty to+0x5e/+0x5f.
Wcześniejsze+0x5c=0 jest jawnym wejściem,zgodnym z osobno wykonanym
oryginalnym producentem pendingselection→grupa→pakiety.

Planer4a4e20 odczytuje+0x5e. Dla obcego obiektu stosuje inną gałąź,gdy
jego grupa jest−1,różni się od grupy requestera lub aktywuje się retry gate.
Wspólne0 może więc zmienić pole blokad i cache nawet przy nieruchomych statkach.
Nie wolno utożsamiać pól+0x5c/+0x5e ani pominąć konsumpcji action41.

## Sprzężony replay komendy i normalnego ruchu

[Probe](../artifacts/world-input/commands/membership-motion/probe.py)
wykonuje oryginalne GetMessage/action41,action20,promocję,Work,replan,
MoveShip i idle w istniejącym WorkOracle.
[Końcowy raport z mapami](../artifacts/world-input/commands/membership-motion/native-membership-motion-with-maps.json)
ma8 przypadków,1212 snapshotów i1192 Tick.
Dwie trasy to18,5 oraz dwa kolejne polecenia18,5→16,4 po gotowości/idle.

Dla każdej trasy porównano cztery jawne wejścia:

| Wariant | Grupa requestera5e | Grupy7 statycznych peerów | Bajt ruchu |
| --- | --- | --- | --- |
|Zamrożona referencja|−1|0|255|
|Tylko bajtUI|−1|0|0|
|Membership z peerami referencji|0 po prawdziwej komendzie41|0|0|
|Membership z nieprzypisanymi peerami|0 po prawdziwej komendzie41|−1|0|

Wyniki:

- Sam bajt0 daje identyczne raportowane pola symulacji,ścieżki,cache,RNG,
  publikacje i zapisy siatki jak bajt255:dla103 oraz200 snapshotów.
  Początkowy priorytet wynosi0;raw pending record nadal ma inny bajt25.
- Membership0 przy peerach0 pozostawia ten sam ruch i harmonogram101/197 Tick,
  te same pathhex,RNG,uporządkowane publikacje i mutacje zajętości.
  Zmienia jednak input mapy planera oraz cache. Różnice101/198 snapshotów
  dotyczą `cache_cells/cache_count/cache_exists`;końcowe cache staje się puste
  zamiast `[115,141]`. To rzeczywista zmiana polityki,nie no-op.
- Membership0 przy peerach−1 daje dokładnie te same raportowane pola,
  pathhex,RNG,cache,publikacje,zapisy siatki i **każdą komórkę mapy wejściowej**
  jak zamrożona referencja −1/0. Liczba calli pathfindera wynosi3 oraz5.
  Równość dotyczy tych dwóch wykonanych scenariuszy i opisanego statycznego świata.

Pola grup są raportowane osobno w `membership_fields`.
Porównanie nie obejmuje adresów alokacji,logów usług i dodatkowej obserwacji
samej koperty membership. Pełne oryginalne instrukcje planowania i ruchu
pozostają wykonane;stosowane są wcześniejsze jawne granice init,heap,
renderowania,visibility i arrival-notification. Nie wykonuje się pełnego
Life/FleetLife/AI ani network replay.

## Pochodzenie nieprzypisanych peerów

[Oddzielny odczyt](../artifacts/world-input/commands/membership-motion/native-ctor-groups.json)
wykonał istniejącą źródłową projekcję ctor/LoadDateBase/damage dla wszystkich
8 rzeczywistych payloadów statków. Każdy pozostawia+0x5c=−1 i+0x5e=−1.
[Probe](../artifacts/world-input/commands/membership-motion/probe_ctor_groups.py)
ma dokładnie te same wcześniejsze granice pochodnej inicjalizacji/systemu/grafiki.
Późniejsza pełna inicjalizacja misji,Message2 oraz Fleet nie są tym potwierdzone.
Peer−1 jest osobnym,jawnym kontekstem porównawczym;wcześniejszy minimalny
świat peer0 zachowuje swój zakres i dowody.

## Kontrakt dalszej integracji

Dla zdrowego source0b i nieruchomych,nieprzypisanych peerów potwierdzono
ograniczoną równoważność projekcji różnych grup w tych dwóch trasach.
UI musi zachować action41,oddzielne+0x5c/+0x5e oraz normalny bajt0.
Przyszłe jednostki we wspólnej grupie wymagają jawnych danych grupy i jej
reguł w świecie;nie można potraktować wariantu0/0 jako wcześniejszego−1/0.

Nie ustalono jeszcze kompletnego pickera/hover,drag,modified commands,
zastępowania ruchu,pozostałych statków w ruchu ani pełnego świata.
Nie zmieniano C#,nie uruchamiano Unity/Wine,nie tworzono ZIP/podglądu
ani publikacji. [Manifest dowodów](../artifacts/world-input/commands/membership-motion/evidence-manifest.json).
