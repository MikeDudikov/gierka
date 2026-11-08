# Wybór trzech lokalnych statków — 2026-11-03

Nowy tryb diagnostyczny pozwala zaznaczać lokalne statki0b,0c,0d kliknięciem
i ramką,z obsługą Shift/Ctrl oraz oryginalnymi obrysami i paskami zdrowia.
Cały widok zajmuje1920×1080,16:9. Jest to wybór tymczasowej floty (`pending`),
przed nadaniem jej numeru grupy i wydaniem rozkazu. **Pełna gra pozostaje
w budowie;normalny Start nadal jest wyłączony.**

```text
AncientConquestReference.exe --ship-pointer-reference --ship-pointer-fleet-selection --terrain-origin-x 9 --terrain-origin-y 0
```

Dotychczasowa diagnostyka samego0b pozostaje dostępna bez dodatkowej flagi.
W nowym trybie rozkazy ruchu są jawnie blokowane do czasu przeniesienia
źródłowego planowania grupy. Nie przypisano pozostałym statkom uproszczonych,
niezweryfikowanych tras.

## Zachowanie i granice

- Zwykłe kliknięcie zastępuje wybór. Shift przełącza wskazany statek,gdy
  bieżący rodzaj kursora dopuszcza wybór. Ramka z Shift dodaje kandydatów,
  zachowuje kolejność istniejących członków i ponownie wysyła zaznaczenie
  do całego tymczasowego zbioru. Pusta ramka zachowuje wybór.
- Ctrl w oryginale wybiera istniejącą grupę wskazanego aktora. Tutaj wszystkie
  trzy statki mają początkowe UI/simulation group−1,więc Ctrl wybiera jeden
  statek. Przywoływanie już przypisanej grupy nie jest jeszcze zaimplementowane.
- Dla wielu statków źródłowy hover zmienia odpowiedź6 na5 i ogranicza maskę
  akcji. Sprawdzono wszystkie osiem podzbiorów lokalnych statków. Nie używa
  się reguły „każdy wybrany statek zawsze ma kursor6”.
- Prawy przycisk na pustej mapie czyści wybór. Kontekstowe akcje prawego
  przycisku i walka pozostają poza tym trybem. Wybrana flota przy obcym statku
  dostaje nieaktywny kontekst diagnostyczny;nie jest to ukończony kursor walki.
- Obrysy56/64/72 używają oryginalnych płaszczyzn60/68/76 pikseli i pasków
  zdrowia34/42/50×4. W playerze lokalne statki wykorzystują rozmiary56 i72;
  rozmiar64 ma dowód źródłowy i jest przygotowany dla dalszej integracji.
- Animacja odznaczania usuwa najpierw pasek,a następnie obrys. Ponowne
  zaznaczenie i odtworzenie obiektu zachowują fazę oraz źródłowy cykl życia.
- Usunięte węzły zachowują pozycję i głębokość w kolejce. Nowy obrys może
  użyć dawnego slotu ramki. Rozróżnienie normalnego sprite’a i callbacku
  paska wpływa na remisy głębokości1020;nie sortuje się ich ponownie po ID.

Przy trzech lokalnych statkach pozostałych pięć jest obcych. Wszystkie ciała
poza0b są statycznymi referencjami,a0b wykonuje tylko zweryfikowane idle.
NoFog,pozostałe sloty świata puste,audio wyłączone. Brak wspólnego ruchu,
walki,pełnego Life i finalnej oprawy2026. Obrazy są referencją wierności.

## Implementacja

`ShipPendingSelection` jest właścicielem uporządkowanego tymczasowego wyboru
i jego zdarzeń C453. `ShipPointerReference` stosuje te zdarzenia do
`ShipFleetVisualReference`,który utrzymuje osobny przebieg zaznaczenia dla
każdego aktora. `ShipPointerHover` ma opcjonalne odczyty zbioru;dotychczasowy
konstruktor i ścieżka0b zachowują swoje zachowanie.

`SourceSpriteSlotQueue` odtwarza normalne węzły,callbacki,usuwanie i ponowne
użycie slotów. Na potrzeby kolejności referencji zaczyna od21 żywych węzłów
świata. `ShipSelectionProgression` obsługuje trzy potwierdzone wielkości,
z domyślną56 dla poprzedniej diagnostyki. Nie zmieniono rdzenia ruchu.

Dziewiąty zestaw Resources,`ShipFleetVisualsGenerated`,zawiera33 obrazy
w atlasie640×400/1024000B. Źródła i każdy istniejący payload są chronione
hashami. Staging jest idempotentny i odmawia cichego nadpisania zmienionych
zasobów. Manifest ma SHA256`c9b399020f4f8c974496fd445230f918ce5a249df61da58da4faed67cf69647a`,
a atlas`441afbc4aad4297550bba5a455271d2e2bf69b7774122a8a3578f03bfe881e25`.
Scena,prefaby,pakiety,ustawienia renderowania i poprzednie stagingi nie wymagały
zmian. Nowy replay wymaga obu flag trybu i nie może mieszać się ze starymi replayami.

## Walidacja

| Sprawdzenie | Wynik |
| --- | --- |
| Tymczasowa flota C#/x86 |1710 przypadków;zastąpienie,Shift,Ctrl,pusta ramka,usuwanie ostatniego członka i kolejność callbacków |
| Hover C#/x86 |9280 stanów;wszystkie8 podzbiorów;lokalne kadłuby,pusta i zablokowana mapa |
| Sloty C#/x86 |24 scenariusze/2376 stanów;rzeczywiste55d670/55dc20/55d960/55ed60;callbacki i recykling |
| Animacja obrysu C#/x86 |21 scenariuszy/1221 stanów dla56/64/72;checked+/warnaserror |
| Oryginalne piksele |30 klatek/180 buforów RLE;6 buforów pasków zdrowia z rzeczywistą inicjalizacją50c890 i rysowaniem50c650 |
| Discovery |241PASS,0 pominięć,348.857s;obejmuje5 nowych testów źródłowych/stagingu |
| Osobne QA protokołu |2PASS,64.831s;6 celowo błędnych zapisów odrzuconych |
| Końcowy player |46 etapów/47 zdarzeń/11 operacji wyboru;licznik idle0…43;pełny obraz RGBmean/max0 |
| Próby obrazu |50 prób,46 przyjętych;4 odrzucone;96 PNG łącznie z46 wzorcami |
| Regresje tego samego DLL |Ramka0b30 kadrów;ruch0b25 kadrów/126 wierszy motion;menu27 etapów/5 obrazów/6 komend;exit0 |
| Windows64Mono |Unity6000.3.27f2;148048747B;0 błędów/0 ostrzeżeń |
| Integralność |66 C#/121 unikalnych meta;9 stagingów;9 źródeł oryginału SHA zgodnych;C# niezmienione po buildzie |

DLL:`c2839d9d4a34446534811d984c7e680d815fb25989532d73059a9607575fcb58`.
`ShipMoveOrder` zachowuje SHA`caa73d42265622175b3b9d44c4125972beae0d682c768d8ca263dbc1b9561cd9`.
241 testów discovery oraz2 później dodane testy QA wykonano osobno;nie jest to
243 testów w jednym discovery. Teraz discovery znajduje243 testy.

Wzorzec playera wykonuje oryginalny kursor,Fleet,Ship,przebieg obrysów
oraz natywne operacje slotów. Pozycje i sortowanie są porównywane z odczytami
rzeczywistych rendererów Unity. MouseState i KeyboardState pochodzą wyłącznie
z`InputSystem.QueueStateEvent`;nie jest to dowód wejścia OS,natywnego Windows11,
fokusu,wydajności laptopa ani pełnego schedulera gry.

Pierwsza próba została odrzucona:przygotowanie dodatkowego wzorca opóźniło
odczyt tak,że obraz etapu`all-up` odpowiadał dokładnie następnemu`all-phase0`.
Zachowano źródło helpera,logi i obrazy. Przeniesienie przygotowania przed start
playera oraz dodatkowa kontrola granicy etapu rozwiązały problem bez zmiany
kodu gry. Tych niepełnych prób nie wlicza się do końcowych46 etapów.

Nie stwierdzono nowego wyjątku Unity. Znane ograniczenia Wine dotyczące
GPU fence,myszy systemowej i audio hosta pozostają opisane w poprzednich
raportach. Nie ponawiano pięciu wcześniejszych nieudanych prób utraty fokusu.

## Artefakty i wznowienie

[Build](../artifacts/fleet-selection/build-report.json),
[testy](../artifacts/fleet-selection/full-tests-01.log),
[QA protokołu](../artifacts/fleet-selection/qa-targeted-tests.log),
[player](../artifacts/fleet-selection/runtime-final/report.json),
[regresje](../artifacts/fleet-selection/regressions.json),
[audyt](../artifacts/fleet-selection/final-audit.json),
[diagnoza opóźnienia QA](../artifacts/fleet-selection/presentation-delay-diagnosis.json),
[milestone](evidence/milestone-20261103-fleet-selection.json).

```bash
.venv/bin/python -m tools.stage_ship_fleet_visuals --replace-generated
.venv/bin/python -m unittest tests.test_ship_fleet_selection tests.test_smoke_ship_fleet -v
.venv/bin/python -m tools.smoke_ship_fleet --output artifacts/<fresh-directory>
```

Unity/Wine/Xvfb uruchamiać kolejno na własnym display79 i świeżych ścieżkach.
Nie budować podczas działania playera. Następny etap:przydział grupy,
serializacja membership i wspólnego ruchu,formacja oraz planowanie zajętości
tej samej grupy. Zmiany pozostają lokalne;bez publikacji,ZIP i podglądu
przeznaczonego do prezentacji.
