# Kontrole QA obiegu rozkazów

Stan:2026-11-03. Ten dokument rozdziela helper użyty w zakończonym teście
playera od późniejszej poprawki wyboru checkpointu przy granicy stop-at.
Nie zmieniano C#,buildu,zasobów ani progów obrazu.

## Zakończone testy rzeczywistego playera

[Niezależny audyt](../artifacts/order-cycle/qa-runtime-final-independent-audit.json)
potwierdza [raport czterech sesji](../artifacts/order-cycle/runtime-final-resumed/report.json):
53 kadry1920×1080,159 regionów statków,RGBmean/max0. Sprawdzono54 pola
każdego etapu,pełne bajty ścieżki,21 rejestracji na sesję oraz1802 faktyczne
odczyty kolejności rendererów. Wszystkie zapisane PNG mają zgodne SHA256,
a ich ponownie odczytane bajty RGB zgadzają się z raportem i wzorcem.

| Scenariusz | Kadry | Końcowy counter | Zwolnione zajęcia |
| --- | ---: | ---: | ---: |
| Normalny rozkaz18,5 |12|101|8|
| Nieprzejezdny cel18,2,endpoint17,2 |10|180|8|
| Dwa rozkazy18,5→16,4 |23|197|8|
| Przerwanie z rezerwacją |8|46|9|

Każda sesja zakończyła się exit0. Endpoint17,2 nie jest oznaczony jako
osiągnięcie żądanego18,2:active80 pozostaje ustawiony,obserwację kończy
jawny limit180. Drugi request zachowuje counter101,ale ma nowy sample_index103
po publikacji idle w sample102;nie powtarza publikacji ani kroku RNG.

Zachowano63 próby obrazu,w tym10 odrzuconych. **Sześć** odrzuconych prób jest
dokładnie zgodnych z wcześniejszym checkpointem;czterech nie sklasyfikowano.
Próg globalmax≤4 i ścisłe kontrole regionów pozostały bez zmian. Porównanie
stanu,części i pełnej kolejki przed/po capture musi pozostawać identyczne,
a akceptacja obrazu musi zmieścić się w1s przy holdzie1,25s.

Osobny [pilot](../artifacts/order-cycle/qa-pilot-independent-audit.json)
potwierdza12 kadrów/36ROI. Nie jest wliczony do53 kadrów zestawu końcowego.
Restart środowiska przerwał wcześniejszy niezakończony zestaw;dowodem pełnego
zestawu jest wyłącznie katalog `runtime-final-resumed`.

## Helper i poprawka granicy stop-at

Player testowano helperem SHA256
`09da3d8365a0df18f7cab10afc64eecb0266351bdb443a2d277ba0314b5e3cf2`.
Jego dokładne41373 bajty zachowano jako
[qa-helper-used-for-runtime.py](../artifacts/order-cycle/qa-helper-used-for-runtime.py),
z [manifestem archiwizacji](../artifacts/order-cycle/qa-helper-archive.json).
Historyczny raport zachowuje ten hash,nawet gdy bieżący plik narzędzia
ma już późniejszą poprawkę.

Przegląd wykrył w czystym selektorze `stage_plan` granicę nieużywaną przez
cztery scenariusze:limit101 wypada dokładnie przy pierwszym idle. Helper
zwracał zwykłe zakończenie,a dla dwóch celów mógł dołączyć request2 przy tym
samym counter. Driver już dawał limitowi pierwszeństwo. Trzy dodane linie
wybierają teraz halted po końcowym Tick,przed zakończeniem lub nowym request.
Nie zmieniono obsługi limitu0:diagnostyka nadal zapisuje initial i request1.

Bieżący [helper](../tools/smoke_ship_order.py) ma SHA256
`12a2afab7237eb94fab0685c411a4ab07812ea0296d22ef95cff1440a7ba3d4c`.
[Porównanie fingerprintów](../artifacts/order-cycle/qa-stop-boundary-fix-validation.json)
dowodzi,że pełne checkpointy,bajty ścieżek i uporządkowane publikacje wszystkich
czterech scenariuszy pozostały identyczne:12/10/23/8 etapów.
[Wcześniejszy przegląd in-memory](../artifacts/order-cycle/qa-stop-boundary-review.json)
zachowuje wykrytą różnicę i propozycję poprawki. Pełny zestaw playera opisany
powyżej wykonał zachowany wcześniejszy helper;porównanie fingerprintów nie
jest deklaracją ponownego uruchomienia playera nowym plikiem.

## Testy kontroli

[Końcowy log](../artifacts/order-cycle/qa-controls-final.log):7 testów PASS,
0 pominięć,6,221s. [Testy](../tests/test_smoke_ship_order.py) zawierają26
jawnych uszkodzeń logu/stanu/ścieżki/kolejki/cleanup,3 negatywy obrazu
(zła faza idle,dodatkowy statek,error5) i2 negatywy capture-fence. Razem31
jawnych negatywnych kontroli. Dodatnie kontrole obejmują error4,prawidłowy
obraz i retry starego framebufferu przy niezmienionym etapie.

Siódmy test sprawdza pięć granic:normal101,dwa cele101,0,100 i102.
Przy101 kończy na sample102/Tick101,bez request2;przy102 normalny rozkaz
może zakończyć się wcześniej przy101. To regresje czystego selektora na
zamrożonym śladzie native,a nie dodatkowe sesje playera.

Odrębny wcześniejszy [pełny unittest](../artifacts/order-cycle/unittest-final.log)
wykonał182 testy bez pominięć w151,698s;nowy moduł QA uruchomiono osobno.
Nie należy opisywać tych wyników jako jednego pełnego uruchomienia189 testów.

## Granice dowodów

Windows Mono uruchomiono pod Wine/Xvfb. Nie potwierdza to natywnego Windows11,
OS input,docelowego laptopa,pełnego Life/AI/walki ani oprawy2026. Grafika
źródłowa jest wzorcem zgodności. Kadry są wewnętrznym dowodem QA;nie pokazano
nowego podglądu,nie utworzono ZIP i niczego nie publikowano.
