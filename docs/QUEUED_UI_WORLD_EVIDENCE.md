# Shift podczas ruchu — dowód UI i świata,2026-11-04

Kontynuując integrację świata, wykonano następny krok: niezależny dowód
UI518070 i pełnej pętli świata dla przejścia100/1→100/2→100/1.
Nie odblokowano jeszcze Shift w adapterze InputSystem.

12scenariuszy obejmuje cztery pozycje floty w rejestrze i żądania po10,25
lub100krokach ruchu. W tym samym zatrzymanym liczniku następują: Shift do
(18,6), Shift do(16,4), powtórzenie pierwszego punktu.60kroków później
zwykły klik do(18,5) przywraca100/1. Świat kontynuuje do200.

Źródłowe UI i świat działają w dwóch silnikach x86. Do UI przekazuje się
rzeczywiste komórki,58c,5e,licznik i wiek grupy. Pakiety, nagłówki i punkty
muszą zgadzać się z bezpośrednim wejściem floty. Cele członków nie są
przenoszone z UI do świata. Ruch, poczta, zadania i310 wykonują się w świecie.

W każdym przypadku liczba nowych pakietów to[3,0,0,3]. Utworzenie100/2
wysyła20 dla trzech statków; append i duplikat niczego nie wysyłają;
zwykły klik zastępuje task, zachowuje wiek i wysyła wynik formacji100/1.
Pełne C#odtwarza te same żądania, bez dostarczania pakietów x86 po starcie.

Wynik:2400klatek,48żądań,2448wierszy świata i7344stany aktorów.
Porównano także pełne310, logiczną trasę i przypisania normalnej formacji.
2testyPASS/0skip107.791s, w tym świeże wykonanie wszystkich12scenariuszy.
To obok8testów integracji świata188.276s. Discovery330testów,bez fullrun.

Fixture `queued_ui_world.json` SHA256:
`7431c964531c4a15472404c3612795cf974f9218c3e9ef922a36a248a2087b0c`.
Shipping DLL161a875ab0612b2945560d7adcd5f8922e45f56c144e6379b1b96cae683a517e
daje ten sam wynik. Raporty: `artifacts/queued-ui-evidence`.

## Znaczniki trasy — znalezione źródło

Odczyt4ced80/4ced10 doprowadził do zasobu WPMOVE w `controlm.dkx/dkd`,
a nie w archiwumOBJECTS. Descriptor type8 ma offset286428,924B,
21części,1klatkę i logiczne36×29. Ostatnia część to `_WPMOVE`, poprzednie
to po10cyfr `_WPNUM0`..`_WPNUM9` dla dziesiątek i jedności.
Source mask zawiera0x100000 i bity cyfr dla numerów1..99;
źródłowa pozycja to cellX*64+14,cellY*64+18.

Istniejący zweryfikowany dekoder odczytał wszystkie części bez generowania
obrazów. Indeksy, offsety i SHA są w `wp-move-resource-discovery.json`.
Nie wykonano graficznego konstruktora lub renderowania markera. Nie wolno
uznać odkrycia zasobu za gotowe wiązanie Unity lub dowód pixel/RGB.

Następnie: adapter z jawnym kontekstem pamięci fali oraz obsługa Shift
na podstawie tego dowodu, wraz z markerami i rzeczywistą próbą InputSystem.
117 nie może stać się nieudokumentowanym domyślnym słowem Windows.
PełnyLife/AI/Start,edycja składu300/311 i raport40 pozostają osobnymi etapami.
Bez PNG, ZIP, publikacji, aplikacji konfiguracji i nowych agentów.
