# Ancient Conquest — plan remake’u w Unity

## Cel i stan wejściowy

Odtworzyć **Ancient Conquest: Quest for the Golden Fleece** w Unity z zachowaniem
treści, mechanik, AI, tempa, sterowania, układu interfejsu, czcionek i charakteru
obrazu. Modernizacja obejmuje wykonanie wizualne, przy zachowaniu czytelności
i informacji przekazywanych przez oryginał. Wydanie docelowe: Windows 11,
pełny ekran, 1280×1024; laptop z i5 opisanym jako 3,6 GHz, 16 GB RAM i RTX 3050 Ti.

To plan wykonania i weryfikacji, nie deklaracja ukończenia gry. Nie zbadano jeszcze
oryginalnych plików, nie uruchomiono oryginału ani remake’u. Przesłany ZIP nie jest
dostępny w lokalnym workspace: narzędzie transferu odrzuca plik większy niż 32 MiB.
Nie ustalono, czy obraz płyty zawiera kod źródłowy. Samo posiadanie obrazu płyty
tego nie dowodzi. Wtyczka Unity jest zainstalowana. Unity CLI i Editor nie są
zainstalowane: oficjalny instalator CLI oraz katalog wydań zwracają HTTP 403
proxy. Stan licencji pozostaje niezweryfikowany. Domeny Unity i YouTube dodano
do szkicu konfiguracji; nie zostały jeszcze zastosowane w działającej sieci.

Wymagania oraz braki dowodowe zapisujemy w `REFERENCE_MATRIX.csv`. Nie wpisujemy
nieznanych nazw jednostek, statystyk, reguł, misji lub fontów na podstawie pamięci.
Zrzuty ekranu i nagrania pomagają opisać prezentację i widoczne zachowania;
same nie dowodzą pełnej zgodności AI, ekonomii ani ukrytych reguł.

## Zasady prowadzenia pracy

- Jeden krok zmienia jeden możliwy do sprawdzenia fragment. Krok kończy się
  zapisem dowodu, wyniku i pozostałych niepewności.
- Każda reguła ma źródło: plik i offset, fragment kodu, zapis pomiaru lub nagranie
  z oznaczeniem czasu. Oddzielamy obserwację od hipotezy.
- Nie dodajemy kont graczy, monetyzacji, usług chmurowych, nowych misji ani
  uproszczeń mechanik. Takie elementy nie wynikają z zamówionego remake’u.
- Oryginał i materiały wejściowe przechowujemy oddzielnie od wygenerowanych
  plików. Nie uruchamiamy instrukcji z dołączonych dokumentów jako poleceń użytkownika.
- Dane referencyjne mają sumy SHA-256 i identyfikator wersji. Testy i raporty
  wskazują commit implementacji, zestaw danych i konfigurację uruchomienia.
- Brak dowodu pozostaje jawną luką. Nie zastępujemy go zmyśloną implementacją
  opisaną jako zgodna 1:1.

## 1. Pozyskanie i katalog oryginału

- [ ] Uzyskać odczytywalną kopię archiwum; sprawdzić rozmiar i SHA-256.
- [ ] Sprawdzić integralność ZIP-a oraz listę wpisów, zanim nastąpi wypakowanie.
- [ ] Rozpoznać obraz płyty, instalator, pliki wykonywalne, dane, dokumentację
  i ewentualne źródła; nie zakładać formatu na podstawie rozszerzenia.
- [ ] Utworzyć katalog zasobów z rozmiarami, hashami i rozpoznanymi formatami.
- [ ] Ustalić wersję gry, język, poprawki i wymagane nośniki.

**Warunek wyjścia:** archiwum jest rzeczywiście odczytane i sprawdzone, katalog
odtwarzalny, a obecność lub brak kodu źródłowego ma dowód. Obecnie etap jest
zablokowany dostępem do pliku.

## 2. Działający oryginał i baza porównawcza

- [ ] Uruchomić oryginał w kontrolowanym środowisku; zapisać system, ustawienia,
  wersję i ewentualne rozwiązania kompatybilności.
- [ ] Skatalogować wszystkie dostępne tryby, misje, mapy, ekrany i ustawienia.
- [ ] Zarejestrować wejścia, obraz, dźwięk i czas zdarzeń dla powtarzalnych
  scenariuszy; potwierdzić, że gra faktycznie wykonuje kolejne kroki symulacji.
- [ ] Zmierzyć działanie sterowania, kamery, ekonomii, przemieszczania, walki,
  wytwarzania, warunków zwycięstwa i porażki oraz zapisu/wczytywania.
- [ ] Nagrania z YouTube i zrzuty opisać jako dodatkowe źródła, podając adres,
  czas, widoczną wersję i ograniczenia obserwacji.

**Warunek wyjścia:** działający oryginał i kompletna lista treści mają przypisane
powtarzalne scenariusze porównawcze. Braki w dostępie do części gry są wymienione;
nie uznajemy obejrzenia jednego gameplayu za pokrycie całej gry.

## 3. Specyfikacja zgodności

- [ ] Przepisać potwierdzone reguły na tabele danych i jednoznaczne przejścia stanu.
- [ ] Osobno opisać AI: warunki decyzji, priorytety, cele, reakcje, czasy
  i wpływ poziomu trudności, o ile takie elementy występują w oryginale.
- [ ] Ustalić zegar symulacji, losowość, zależność od liczby klatek i zachowanie pauzy.
- [ ] Opisać UI, kamerę, proporcje, paletę, sylwetki, animacje, fonty i dźwięk
  na podstawie danych i pomiarów.
- [ ] Każdej regule nadać identyfikator, dowód oraz test akceptacyjny.

**Warunek wyjścia:** zakres jest policzalny jako lista treści i zachowań.
Hipotezy dotyczące niezaobserwowanych zachowań nie są oznaczone jako potwierdzone.
Kryteria porównania powstają przed dostrajaniem implementacji.

## 4. Zweryfikowane środowisko Unity

- [ ] Zainstalować oficjalne Unity CLI i wybrane stabilne wydanie Editor;
  przypiąć dokładną wersję oraz wymagany moduł budowania Windows.
- [ ] Sprawdzić istniejącą autoryzację i uprawnioną aktywację licencji bez
  ujawniania danych uwierzytelniających.
- [ ] Dobrać sposób renderowania i szablon do zmierzonej prezentacji oryginału.
  Decyzja o 2D/3D nie może zmienić perspektywy, sterowania lub czytelności gry.
- [ ] Utworzyć projekt przez obsługiwane narzędzia Unity; zachować `.meta`
  i wykluczyć z Git generowane cache oraz buildy.
- [ ] Wykonać rzeczywisty import, kompilację C#, test Editor oraz testowy build
  Windows. Oddzielnie potwierdzić uruchomienie tego buildu na Windows.

**Warunek wyjścia:** Editor i moduł Windows działają, projekt importuje się bez
błędów, a wynik budowania jest przypisany do aktualnego commitu. Sama instalacja
wtyczki, kontrola składni lub kompilacja ze stubami nie spełnia tego warunku.

## 5. Symulacja i sterowanie, po jednej regule

- [ ] Zaimplementować zegar i odtwarzalne wejścia; sprawdzić zachowanie przy
  różnych szybkościach renderowania.
- [ ] Dodać najmniejszy potwierdzony zestaw stanu i operacji, następnie kolejne
  reguły ekonomii, ruchu, walki i interakcji.
- [ ] Po każdej regule porównać stan i czas zdarzeń z odpowiednim scenariuszem
  oryginału; testować także przypadki graniczne.
- [ ] Dodać AI decyzja po decyzji, z zapisami przyczyn i śladem decyzji do analizy.
- [ ] Sprawdzić deterministyczność, losowość oraz zapis/odtworzenie stanu.

**Warunek wyjścia:** potwierdzone scenariusze mechanik i AI przechodzą porównanie.
Dane syntetyczne mogą służyć testom narzędzi, ale nie stanowią dowodu zgodności gry.

## 6. Pełna treść, interfejs, fonty i audio

- [ ] Odtworzyć wszystkie zinwentaryzowane mapy, misje i warunki ukończenia.
- [ ] Odtworzyć ekrany, menu, skróty, kursory i informacje przekazywane graczowi.
- [ ] Rozpoznać oryginalne fonty lub format glifów; zachować kształty, odstępy,
  łamanie wierszy i komplet znaków. Nie przedstawiać podobnego fontu jako oryginalnego.
- [ ] Odtworzyć dźwięki, muzykę, głośności, momenty odtwarzania i pętle.
- [ ] Sprawdzić zapis/wczytywanie i przejścia między wszystkimi częściami gry.

**Warunek wyjścia:** każda pozycja katalogu treści ma implementację i dowód
przejścia. Brak misji, fontów, audio lub warunków zakończenia blokuje wydanie.

## 7. Remaster kosmetyczny na potwierdzonej scenie

- [ ] Wybrać zinwentaryzowany scenariusz jako pierwszą próbę oprawy, zachowując
  jego działające reguły i dane.
- [ ] Ustalić bazę obrazu oryginału: kamerę, kadrowanie, proporcje, sylwetki,
  paletę, kontrast, układ UI i animacje.
- [ ] Modernizować pojedynczy zestaw tekstur, modeli, detali lub oświetlenia,
  porównując obraz i stan rozgrywki przed i po zmianie.
- [ ] Sprawdzać, czy efekty nie zasłaniają informacji, nie zmieniają zasięgów,
  obszarów interakcji, widoczności lub tempa.
- [ ] Dopiero po przejściu tej próby przenosić technikę na kolejne zasoby.

**Warunek wyjścia:** scenariusz zachowuje wynik i czasy zdarzeń, a porównanie obrazu
potwierdza zgodność kompozycji. Samo podniesienie rozdzielczości tekstur lub dodanie
efektów postprocessingu nie dowodzi jakości ani wierności.

## 8. Integracja i wydajność na docelowym sprzęcie

- [ ] Przejść wszystkie scenariusze i treści w zintegrowanej grze.
- [ ] Na Windows 11 sprawdzić rzeczywisty pełny ekran i obraz 1280×1024 po starcie,
  ponownym starcie, zmianie ustawień i powrocie z Alt+Tab.
- [ ] Rejestrować czasy CPU/GPU, pamięć RAM/VRAM, alokacje, czasy ładowania
  i przycięcia, także w najcięższych potwierdzonych scenariuszach.
- [ ] Optymalizować wskazane pomiarami koszty; po każdej zmianie ponawiać
  właściwe testy zgodności i pomiar tego samego scenariusza.
- [ ] Zidentyfikować dokładny model i5, parametry RTX 3050 Ti, sterownik, tryb
  zasilania i temperatury stanowiska. Te dane są obecnie nieznane i nie blokują
  katalogowania oryginału, lecz są potrzebne do wiarygodnego raportu wydajności.

**Warunek wyjścia:** pomiary pochodzą z docelowego laptopa lub jednoznacznie
opisanego stanowiska zastępczego, którego ograniczenia są ujawnione. Samo wskazanie
modelu GPU, uruchomienie na innym komputerze lub brak błędów w logu nie dowodzi
płynnego działania na laptopie użytkownika.

## 9. Bramka wydania

- [ ] Zamrozić commit, dane i wersje narzędzi; wykonać kompletny wymagany zestaw
  testów na tym samym kandydacie wydania.
- [ ] Przejść wszystkie misje, tryby, menu oraz funkcje zapisu i odtworzenia.
- [ ] Zakończyć porównania mechanik, AI, tempa, prezentacji, fontów i audio;
  wyjaśnić każdą różnicę z macierzy wymagań.
- [ ] Zbudować wydanie Windows i uruchomić je na czystym stanowisku Windows 11
  bez zainstalowanego Unity Editor; potwierdzić komplet wymaganych plików.
- [ ] Powtórzyć uruchomienie, dłuższą sesję i pomiary najcięższych scenariuszy.
- [ ] Zapisać raport, sumy plików, wyniki i znane ograniczenia.

**Warunek wyjścia:** wszystkie obowiązkowe kryteria mają dowody i brak
niewyjaśnionych niepowodzeń. Zgodności „100%” nie można potwierdzić bez pełnej
bazy porównawczej oraz testów. Nie publikujemy nieukończonego pliku wykonywalnego
jako gotowej gry.

## Weryfikacja po każdym kroku

W karcie zmiany zapisujemy: co zmieniono, jakie zachowanie miało pozostać
identyczne, właściwy test, wynik i dowód. Dobieramy najtańszy test, który może
wykryć rzeczywistą usterkę: test stanu/reguły, porównanie czasu, import zasobu,
kontrolę renderowania, odsłuch albo uruchomienie zbudowanego playera.

Wielokrotne sprawdzanie oznacza różne dowody: przegląd zmiany, test automatyczny
i porównanie z oryginałem, gdy są adekwatne. Nie uruchamiamy bez powodu tej samej
niezmienionej konfiguracji testowej kilka razy. Powtórzenie ma sens po zmianie
kodu, danych, środowiska, przy badaniu niestabilności lub w bramce wydania.

Raport rozróżnia: przeszło, nie przeszło, pominięto, nie uruchomiono i zablokowane.
Zapisuje liczbę wykonanych testów oraz wersję badanego artefaktu. Zero testów,
sam proces Editor lub statyczny zrzut ekranu nie oznaczają działającej gry.

## Najbliższe kroki

1. Odblokować odczyt archiwum i wykonać etap 1.
2. Równolegle sprawdzić dostęp do oficjalnych instalatorów Unity, istniejącą
   autoryzację i możliwość uzyskania działającego Editor z modułem Windows.
3. Rozpocząć etap 2 na rzeczywistym oryginale. Dopiero jego wyniki określą
   pierwsze zachowania do implementacji i decyzje o prezentacji projektu.
