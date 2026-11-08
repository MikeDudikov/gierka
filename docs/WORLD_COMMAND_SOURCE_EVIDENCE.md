# Źródłowe zwolnienie przycisku i polecenie pojedynczego statku

Stan:2026-11-03. Jest to dowód źródłowy,bez nowej implementacji wejścia Unity.
Oryginalny EXE SHA256:
`cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021`.

## Zdarzenie i zapamiętany cel

`MapaTy::GetMessage0x51cd60` w trybie1/2,po sprawdzeniu viewportu i braku
aktywnego sprite'a przeciągania (`map+0x489<0`),wywołuje
`CursorClassTy::ButMapXY0x518070` dla LeftUp0x62 lub RightUp0x64.
Normalny ruch typu kursora7 (`CUR_SEA`) jest akcją **LeftUp**.
RightUp nie emituje normalnego action20;anuluje/resetuje lub przełącza kontekst.

ButMapXY otrzymuje tylko kod zdarzenia i flagi. Współrzędne akcji pochodzą
z `cursor+0xc9/+0xcd`,zapamiętanych przez wcześniejsze przetworzenie Move.
Nie należy wyznaczać celu na nowo wyłącznie z pozycji release ani dodawać
w tym leafie nieobecnego latcha wcześniejszego LeftDown.

`0x518d40` tworzy kopertę0xc458:action low16 pod+0x14,surowy selector
`cursor+0xef` pod+0x16,payload pointer+0x18,flagi zdarzenia+0x1c.
Wysyła ją do pierwszego slotu vtable odbiorcy `app+0x3219`,czyli tutaj
`FleetClassTy::GetMessage0x49ab30`. Selector nie jest actorID;normalna
ścieżka action20 nie używa go do wskazania pojedynczego odbiorcy.

## Rzeczywista ścieżka pending selection→grupa→pakiety

[Probe](../artifacts/world-input/commands/single-actor/probe_pending_selection.py)
wykonał oryginalne instrukcje następującej ścieżki:

```text
518070 ButMapXY →518d40 c458 →49ab30 FleetMessage →49e230
→49ca60 ConvertPendingSelection →49b990 temporarygroup
→49bd60 AddActorToGroup →49de70 →4ccc30 →4cc500
→4cc970(count1) →4cc8c0 →4cc7d0 →4cf070 →520c50 →5593a0
```

[Raport](../artifacts/world-input/commands/single-actor/native-pending-selection.json)
ma6 przypadków dodatnich:18,5;20,4;18,2;16,1;0,0;23,23.
Dla każdego pojedynczy actorID11 dostaje dokładnie kliknięte X/Y.
Trzy kontrole ujemne cursor mode0/1/3 nie emitują pakietu i nie zmieniają grupy.

Wejściem jest jawnie przygotowana pendingselection jednego source0b:
class200,ownerSide1,ownerPlayer1,slot właściciela `1*4+1=5`,group−1.
Ustawiono też ludzki descriptor slot5=1 i pojedyncze bieżące zaznaczenie.
To surowy stan kontekstu,nie wykonanie kliknięcia wybierającego ani kompletnych
konstruktorów świata. Typ kursora7 i uprawnienie do wejścia w handler są
wejściami;przypadki16,1/18,2 dowodzą wyłącznie kopii celu,nie dopuszczenia
tego kursora przez pełny hover ani dojazdu statku.

Źródło tworzy grupę0,przypisuje ją lokalnie do actor+0x5c,zeruje pendingselection
i dopisuje dwa pakiety FIFO do PlaySystem+0x2e:

1. Action41 (`')'`) z payloadem6 B `010000000000`:przynależność do grupy0.
2. Action20 z payloadem9 B:little-endian int32 X,int32 Y,**bajt0**.

`0x4cc970` ma osobną gałąź dla jednego członka. Wywołuje ona `0x4cf070`,
które zeruje dziewiąty bajt. Inna,fallbackowa funkcja `0x4cc650` wpisuje255;
nie jest ona dowodem wartości dla tej pojedynczej ścieżki UI.
Frozen `ShipMoveOrder.RequestCellMove` przyjmuje oba bajty0/255,lecz sam ten
fakt nie dowodzi zgodności całego wejścia ani efektów członkostwa grupowego.

SetCtrlCmd0x520c50 i append0x5593a0 wykonują rzeczywiste instrukcje:
actorID pod+8,action pod+0xc,payload pointer pod+0xd,dane pod+0x11.
Drugi pakiet ma26 B. To inny rekord niż26-bajtowy pending ruchu statku.

Przechwycono wyłącznie normalny setjmp,CRT malloc/realloc oraz granice
renderowania confirm sprite/odświeżenia kursora. Oryginalne wrappery
alokacji558f80/557700/558fd0 wykonują własne zerowanie i kopię.
Nie przechwytywano wyboru grupy,przypisania celu ani serializacji pakietów.
Wstępny nieudany przebieg z błędnym modelem zerowania alokatora pozostawiono
w pending-run.log;końcowy używa prawdziwego wrappera558f80.

## Granice i następny krok

Nie odtworzono jeszcze pickera/pełnego hover,kliknięcia zaznaczenia,drag,
modified flags,busy replacement,network replay ani konsumpcji obu pakietów
przez pełne Life. Nie należy pomijać action41 i zakładać,że źródłowy
statek nadal ma group−1. Dotychczasowa projekcja ruchu ma taki jawny kontrakt;
połączenie wejścia wymaga osobnego dowodu konsekwencji grupy0.

Brak nowego C#,buildu,usług Unity/Wine,ZIP,podglądu lub publikacji.
Dowody dotyczą oryginalnego x86 w emulatorze,a nie uruchomienia pełnej gry.
