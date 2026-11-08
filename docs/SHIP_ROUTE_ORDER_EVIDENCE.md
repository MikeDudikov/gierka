# Kolejność źródłowego planowania i ruchu statku

Oryginalny `ProcShipsWork0x4ab930` może wykonać planowanie i pierwszy
`MoveShip` **w tym samym source counter**. Siedem natywnych wywołań
wykonuje całe ciała work/plannera/ruchu i zachowuje counter1. To rozszerza
wcześniejszy dowód granic dispatchera; nie jest portem całego `Life` ani
zegara aplikacji.

Dowody:

- [Oracle całego work](../artifacts/long-routes/ordering/probe_work_order.py)
  i [zamrożony raport](../artifacts/long-routes/ordering/work-order-frozen.json).
- [Oracle granicy dojazdu](../artifacts/long-routes/ordering/probe_arrived_recheck.py)
  i [pięć kontroli retry/stop](../artifacts/long-routes/ordering/arrived-recheck-validation.json).
- Eksporty oryginału: [Life](../artifacts/movement/animation/export-life/004dec40.c),
  [ProcShipsWork](../artifacts/movement/time/export/004ab930.c),
  [MoveOrderWork](../artifacts/movement/time/export/004a5f30.c),
  [ProcPostMove](../artifacts/movement/kinematics/export-nav/004a6330.c),
  [recheck](../artifacts/movement/kinematics/export-nav/004a6150.c),
  [zapis wejść retry](../artifacts/movement/kinematics/export-nav/004a6100.c).

## Pierwsze wykonanie

`Life0x4dec40` statycznie wywołuje najpierw `0x4ab720` (promocja oczekujących
poleceń), potem `0x4ab930`. W badanym `ProcShipsWork` capability `+0x261 &0x4000`
dodaje active `+0x25d |=0x400`. Active80 wywołuje `0x4a5f30`. Po jego powrocie
nie ma wymuszenia następnego ticka: active400, przy `+0x25c==0`, wywołuje
`MoveShip0x4a3f40` w tym samym wywołaniu i przy tym samym counter.

W trybie pierwszego celu `+0x593=1`, `0x4a5f30` odpytuje teren celu,
zeruje retry `+0x591`, wywołuje `0x4a6330`, a następnie `0x4a6100`.
Planner odrzuca powtórne planowanie, gdy `+0x57b` jest równy counterowi.
Po rzeczywistym szukaniu ścieżki zapisuje `+0x593=0` i `+0x57b=counter`.
`0x4a6100` zachowuje retry, tryb, cel i bieżącą komórkę w polach
`+0x562/+0x566/+0x56b/+0x56f/+0x573/+0x577`. Nie przesuwa zegara.

Oracle używa oryginalnego konstruktora i payloadu0b, oryginalnego wyliczenia
prędkości, źródłowych576 flag i ośmiu właścicieli. Active80, cel,593=1,
source counter1, pending1 oraz wind0/heading5 są jawnie przygotowanymi
wejściami. Nie wykonuje przyjęcia requestu ani początkowego `Life`.
Wszystkie ciała `4ab930/4a5f30/4a6330/4a5740` lub alternatywnej gałęzi
linii, planera i `4a3f40` wykonują oryginalne instrukcje. Granice setjmp,
alokacji, początkowych usług oraz publikacji/visibility/systemu są jawnie
przechwycone. Żaden planner, query ani ruch nie jest zastąpiony.

Dla każdego z7 celów kolejność zawiera work→MoveOrderWork→ProcPostMove→
SaveRetryInputs→MoveShip. Oba stemple planowania i ruchu wynoszą1.
Dla SW `(15,3)` ten sam call rezerwuje komórkę87, ustawia state5 i speed720,
bez pierwszego piksela. Dla celu wymagającego obrotu zapisuje frame47,
state2 i nie publikuje nowego sprite. Nie można więc opisywać osobnego
planner@1, MoveShip@2 jako pełnej pierwszej iteracji oryginału; pozostaje
to poprawny **jawny harmonogram przygotowanej diagnostyki**.

## Końcowy rekord ścieżki a cel polecenia

Nie każda uzyskana ścieżka kończy się od razu na celu active requestu.
W badanej oryginalnej ścieżce work cel `(18,2)` daje końcowy rekord `(17,2)`,
a `(16,5)` daje `(16,4)`. Natomiast `(18,4)`, `(18,5)` i `(20,4)` mają
rekord końcowego celu. To obserwacja konkretnych wykonań; ten dowód nie
odtwarza pełnego późniejszego retry takich częściowych planów.
Adapter zamrożonej trasy musi sprawdzać końcowy rekord i nie ogłaszać
przybycia do active celu wyłącznie na podstawie końca bieżącej tablicy.

## Po rzeczywistym dojeździe

Przy `+0x593=0`, `0x4a5f30` przechodzi przez `0x4a6150`. Zmiana zapamiętanych
wejść albo state0 może uruchomić recheck, lecz state2 blokuje tę drogę,
a unsigned `counter-lastPlan` musi osiągnąć `+0x57f`. Źródłowa promocja
polecenia ruchu ustawia ten interwał na25; sam konstruktor ma0.

Pięć dodatkowych kontroli jawnie instaluje poprawny stan dojazdu do `(15,3)`
po wcześniejszym oryginalnym work. Nie są one śladem kinematyki. Przy elapsed24
nie ma zlecenia końca. Przy25 oraz26, także przez zawinięcie uint32, rzeczywiste
`4a5f30→4a6150→virtual4a9e30` zapisuje pending bit8 i maskę80 pod `+0x818`.
**Active80 pozostaje wtedy ustawione.** Późniejsze rzeczywiste
`4ab720→4aa540` konsumuje ten request, usuwa active80 i pending8.
To odroczone zatrzymanie, nie synchroniczne kasowanie rozkazu przy zmianie state0.

Nie wykonano pełnego dispatchera aplikacji, całego `Life`, idle RNG,
AI, walki ani planowania dalszego świata. Te dowody nie ustalają czasu
wall-clock, FPS ani kompletnej kolejności wszystkich callbacków.
Diagnostyka może celowo zamrozić ukończoną trasę przed idle, jeżeli jawnie
zachowuje ten zakres. Dynamiczna ranga grafik ma osobny dowód:
[SOURCE_SPRITE_DEPTH_QUEUE_EVIDENCE.md](SOURCE_SPRITE_DEPTH_QUEUE_EVIDENCE.md).
