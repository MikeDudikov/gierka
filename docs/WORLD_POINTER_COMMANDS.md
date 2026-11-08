# Pojedynczy statek: wybór, puszczenie przycisku i pakiety ruchu

Stan: 2026-11-03. Nowy, czysty model
[ShipPointerCommands](../Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipPointerCommands.cs)
odtwarza ograniczoną ścieżkę oryginalnego source0b. Nie zmienia wcześniejszego
rdzenia ruchu. [Walidacja](../artifacts/world-input/commands/pointer-csharp-validation.json)
porównuje rzeczywiste instrukcje oryginału z kompilacją C# `/checked+ /warnaserror+`:
9 przypadków, 55 stanów i 19 sprawdzeń granic API. Dwa testy jednostkowe
przechodzą, w tym odrzucenie zmienionego, przypiętego fixture.

## Kontrakt wejścia

`CursorClassTy::ButMapXY 0x518070` przyjmuje numer zdarzenia i flagi.
Komórka pochodzi z zachowanych pól kursora+c9/cd, obliczonych wcześniej
przez hover. Puszczenie przycisku nie przelicza komórki z bieżącej pozycji myszy.
Normalne polecenie ruchu wydaje **LeftUp62**, gdy kursor ma typ7 i e6=0.
LeftDown61 nie wydaje polecenia. Źródłowa funkcja nie ma pamięci
wciśnięcia przycisku: ważny LeftUp może wybrać statek bez wcześniejszego Down.
Obsługa przeciągania i bramek mapy należy do hosta przed tym modelem.

[Rzeczywisty handler mapy51cd60](../artifacts/world-input/commands/map-release-gate/probe.py)
sprawdzono także osobno:
[raport](../artifacts/world-input/commands/map-release-gate/native-map-release-gate.json)
zawiera625 sekwencji Down→Move→Up, łącznie1880 zdarzeń z up-only i granicami
viewportu. Kontekst to tryb mapy1, normalny tryb jawny kursora0, tile64.
Dla delta x/y od−12 do12 prostokąt powstaje dokładnie wtedy, gdy
`abs(dx+1)>9 && abs(dy+1)>9`:36 przypadków. Próg jest asymetryczny:
przesunięcie co najmniej+9 albo najwyżej−11 musi wystąpić na obu osiach.
Źródło przekazuje release do518070 wyłącznie przy braku aktywnego sprite'a
prostokąta; sprawdza ten warunek przed sprzątaniem drag state.
Gdy prostokąt istnieje, zamiast release wywołuje gałąź box selection517b90.
Ten probe obserwuje granice hover/release/box selection/renderowania,
bez wykonywania ich dalszej logiki. Wspiera świadome zatrzymanie hosta
na niezaimplementowanym zaznaczaniu prostokątem.

```csharp
var commands = new ShipPointerCommands(source0bOwner);
var result = commands.ProcessRelease(
    new ShipPointerCommandInput(hover.HoveredOwner, hover.CellX, hover.CellY,
        hover.CursorType, hover.ActionMask, hover.ActionBit, hover.Blocked, enabled),
    sourceMessage, flags, canRequestMove);
hoverModel.ApplyReleaseCursor(result.CursorType, result.ActionMask,
    result.ActionBit, result.Blocked);
```

`enabled` stanowi jawny wynik bramek źródła: aktywny tryb kursora2,
ważny punkt mapy, zamknięte blokujące panele oraz normalny stan aplikacji.
Zweryfikowany zakres to normalny pojedynczy przyjazny source0b i typy0/5/6/7.
Shift/control, inne jednostki, kontekstowe cykle prawego przycisku,
prostokąt zaznaczenia i zastępowanie aktywnego ruchu wymagają osobnych modeli.
Niewspierane polecenia zgłaszają `NotSupportedException`; host podaje
`canRequestMove=false`, gdy zamrożony rdzeń ruchu nie może przyjąć zamiany.

## Wybór i anulowanie

Pierwszy przyjazny LeftUp typu5 wywołuje źródłowe518c90, następnie Fleet C453.
Ustawia selected/pending, pole252=1 i **resetuje typ kursora do0**.
Oryginalne odświeżenie CursorLife może później wyznaczyć6 nad własnym statkiem
lub7 nad wolnym morzem. LeftUp typu6 nie wydaje komendy.
Ponowny wybór przy zaznaczonej jednostce emituje najpierw C453 clear,
a następnie C453 select; wynik udostępnia obie flagi.

RightUp nad pustą mapą usuwa wybór i ustawia kursor0. Przy typie0 zachowuje
maskę E2; przy typie7 ją zeruje. E4 pozostaje zachowane. RightUp nad wybranym
własnym statkiem typu6 resetuje kursor/maskę, zachowując wybór.
Przyjazny typ5 z maską0 pozostaje bez zmian, chyba że e6 blokuje kontekst.

Usunięcie wyboru ustawia252=2, aby odtworzyć odwróconą animację selektora.
Osobna rzeczywista funkcja4e0d00 potwierdza przejście1→2→0 i usunięcie sprite'a
([stan natywny](../tests/fixtures/ship_pointer_commands.json), `selection_removal`).
Po `ShipSelectionProgression.LastStepDeletesSelector` host wywołuje
`CompleteSelectionVisualRemoval()`. Metoda dopuszcza wyłącznie !Selected
i flag2; powtórne lub przedwczesne potwierdzenie jest odrzucane.

## Grupa i dokładny payload

Oryginalne normalne polecenie idzie przez Fleet C458/action20,
pending selection→tymczasową grupę→pojedynczy aktor→serializer.
Pierwsza grupa ma indeks0. Puste wcześniejsze rekordy grup pozostają w wektorze.
Po anulowaniu, ponownym wyborze i ruchu powstaje grupa1, następnie2 itd.

| Moment | Kolejność action/payload |
| --- | --- |
| Pierwszy ruch do18,5 | 41:`010000000000`, 20:`120000000500000000` |
| Kolejny ruch w tej samej grupie | tylko20: int32 x, int32 y, byte0 |
| Ruch po ponownym wyborze, grupa1 | 41:`01ffffffff00`, 41:`010100000000`, 20:x/y/0 |

Pierwsza komenda41 usuwa poprzednie członkostwo, a druga dodaje nowe.
Stały bufor mieści trzy pakiety. `GetLastCommand` zwraca actorID0xb, action,
komórkę, grupę oraz `CapturePayload()` z niezależną kopią bajtów.
Normalny dziewiąty bajt action20 jest **0**, z4cf070. Wariant255 z4cc650
dotyczy innej gałęzi; [wcześniejszy dowód](WORLD_COMMAND_SOURCE_EVIDENCE.md)
opisuje tę różnicę.

Natychmiastowe pole UI aktora+5c zmienia się przy przypisaniu grupy49bd60.
Pole symulacji+5e zmienia się dopiero podczas rzeczywistej konsumpcji41,
instrukcją50ca16. Model zachowuje oba pola oddzielnie.
Host iteruje po `LastCommandCount` w kolejności i przed action20 wywołuje
`ConsumeMembership41(command.Group)` dla każdego41. Metoda wymaga dokładnej
kolejności i jednokrotnej konsumpcji; usunięcie−1 poprzedza nową dodatnią grupę.

## RNG i granice dowodu

[Native probe](../tools/probe_ship_pointer_commands.py) wykonuje oryginalne
518070, Fleet49ab30, konwersję grupy, serializer520c50/FIFO5593a0,
ShipGetMessage i bazowy konsument41. Hover i mapa są jawnymi wejściami.
Wykonane50e500/525300 mają **wyłączony backend audio**.
Obserwator zapisu pamięci nie odnotował ani jednego zapisu do Ship+18 RNG
we wszystkich55 stanach. Wybór, pakiety i potwierdzenie żądania nie wymagają
dodatkowego zużycia RNG w tym zakresie. Konstrukcja grafiki potwierdzenia515df0,
selektora4e0b80, loader kursora516d90 i rysowanie516640 są jawnymi granicami
renderowania. Dowód nie potwierdza działania słyszalnego backendu audio ani
całej oryginalnej pętli Life.

[Dodatkowy probe](../artifacts/world-input/commands/audio-footprint/probe.py)
potwierdza wejścia do50e500 i525300, powrót oraz brak zapisów Ship+18 przy
stanach RNG0,1,FFFFFFFF: łącznie15 operacji wyboru/ruchu/anulowania/ponownego
wyboru. [Raport](../artifacts/world-input/commands/audio-footprint/native-audio-off-footprint.json)
wykazuje, że w tym zakresie wyborowi towarzyszy tylko zmiana aktora+252,
a utworzeniu grupy tylko+5c/+5d. Nie zmieniają się pola normalnego Work.
Próbka słów stosu w raporcie jest surową obserwacją, bez twierdzenia o liczbie
argumentów prototypu. Backend pozostaje jawnie wyłączony, a renderowanie
pozostaje granicą opisaną powyżej.

Pełne sprzężenie41→20→Work oraz różnicę pomiędzy wspólną i różną grupą
opisuje [dowód membership/ruchu](WORLD_MEMBERSHIP_MOVEMENT_EVIDENCE.md).
Osobny [raport576 celów](../artifacts/world-input/commands/group-map-equivalence/native-all576.json)
porównuje oryginalne normalne planery od16,2 dla każdej komórki24×24:
requester−1/7 peerów0 oraz requester0/7 peerów−1. Wszystkie9 raportowanych
pól, w tym oba kompletne pola mapy, ścieżka, cache i RNG, są identyczne.
Promień wynosi0 dla komórki przechodniej albo1 dla blokowanej, według
rzeczywistego4999e0. Jest to dowód planowania początkowego przy statycznych
peerach; nie potwierdza wszystkich przyszłych faz Life dla dowolnej misji.

[Uzupełnienie dla grup1/2](WORLD_POSITIVE_GROUP_MOVEMENT.md) potwierdza również
wszystkie576 początkowych celów dla obu grup oraz sprzężone Work dla dwóch
tras. Wariant ponownego wyboru wykonuje rzeczywiste41 usunięcie−1,41 przypisanie2
i20 przed kolejnym Tick; wszystkie porównane stany/mapy pozostają identyczne
z referencją różnych grup. To uzasadnia ograniczoną projekcję ruchu dla
grup0/1/2 i7 nieruchomych, nieprzypisanych peerów.

Nie można utożsamić requester0/peer0 z wcześniejszym profilem różnych grup:
rzeczywisty test wykazał różnice map i cache. Projekcja starego rdzenia wymaga
jawnego zachowania zweryfikowanego profilu różnych grup.

Fixture jest przypięty SHA256 w
[validatorze](../tools/validate_ship_pointer_commands.py).
[Manifest](../artifacts/world-input/commands/pointer-evidence-manifest.json)
wiąże źródło, fixture, probe, walidację i dokumentację.
