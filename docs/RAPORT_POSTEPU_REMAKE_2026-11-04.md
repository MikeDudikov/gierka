# Raport postępu remake’u Ancient Conquest

Stan na 4 listopada 2026. Prace zostały wstrzymane po ukończeniu bieżącego
zadania, zgodnie z ostatnią prośbą użytkownika.

Projekt jest działającym prototypem technicznym z częściowo odtworzonym
rdzeniem gry. **Pełny remake pozostaje nieukończony: nie można jeszcze
rozegrać kompletnej misji.** Najwięcej wykonanej pracy dotyczy odczytu
oryginału, prezentacji pierwszej mapy oraz ruchu i sterowania statkami.

## Co zrobiliśmy od początku

1. **Przygotowaliśmy projekt i środowisko Unity.** Działa edytor Unity 6 LTS,
   narzędzia analizy, przygotowanie zasobów oraz powtarzalne budowanie wersji
   Windows. Projekt ma ustawiony pełny ekran 1920×1080 w proporcjach 16:9.

2. **Odczytaliśmy dostarczoną płytę i uporządkowaliśmy materiały oryginału.**
   Połączono i sprawdzono wszystkie części archiwum. Rozpoznano pliki gry,
   mapy, grafiki, fonty i materiały dźwiękowe. Powstały narzędzia dekodowania
   i wprowadzania zasobów do Unity. Oryginalne dane są zachowane.

3. **Zbudowaliśmy podstawę do wiernego odtwarzania mechanik.** Nie znaleziono
   źródeł C/C++; analizujemy program oryginału i porównujemy jego zachowanie
   z C#. Powstała deterministyczna pętla symulacji oddzielona od renderowania
   Unity. Zachowujemy potwierdzoną kolejność rozkazów i aktualizacji obiektów,
   również wtedy, gdy zachowanie oryginału jest nietypowe.

4. **Uruchomiliśmy menu i briefing pierwszej misji.** Działają przejścia między
   nimi, wybór trudności i powrót do menu. Odtworzono tekst briefingu,
   podstawowe zachowanie przycisków i oryginalne kształty czcionek.

5. **Przygotowaliśmy referencyjny widok pierwszej mapy.** Unity wyświetla teren,
   pięć raf i osiem statków odczytanych z oryginalnych danych. Powstały podstawy
   pozycjonowania obiektów, zajętości pól i właściwej kolejności rysowania.
   Jest to fragment diagnostyczny, a nie ukończona pierwsza misja.

6. **Odtworzyliśmy istotną część ruchu statków.** W sprawdzonych scenariuszach
   działają wyznaczanie tras, skręcanie, rozpędzanie i hamowanie, rezerwowanie
   pól oraz przyjmowanie kolejnych rozkazów podczas ruchu. Pozycje i animacje
   są porównywane z zachowaniem oryginalnego programu.

7. **Rozwinęliśmy sterowanie i zadania floty.** W trybie referencyjnym trzech
   lokalnych statków działają zaznaczanie kliknięciem i ramką, formacje,
   zmiana celu, kolejka punktów przez Shift, przywołanie grupy przez Ctrl
   oraz znaczniki trasy. Sprawdzono osobno lewy i prawy Shift. Zadania grup
   korzystają z istniejącej pętli świata i jednej poczty rozkazów.

8. **Zbudowaliśmy zaplecze kontroli zgodności.** Mamy automatyczne porównania
   z oryginalnym kodem x86, testy stanów symulacji i przebiegów sterowania,
   testy renderowania wybranych elementów oraz zapisane punkty kontrolne.
   Ostatni build Windows skompilował się bez błędów i ostrzeżeń.

## Czego jeszcze nie ukończono

- Pełnej grywalnej misji i kampanii. Przycisk rozpoczynający właściwą
  rozgrywkę pozostaje wyłączony; funkcje świata uruchamia się w trybach testowych.
- Pełnego AI przeciwników, walki, gospodarki, produkcji oraz wszystkich
  zachowań i typów obiektów występujących w oryginale.
- Całości interfejsu, obsługi dźwięku oraz pełnego zapisu i wczytywania gry.
- Kompletnej modernizacji tekstur, modeli i efektów do docelowej jakości
  wizualnej. Obecna prezentacja bazuje w dużej części na oryginalnych grafikach;
  przygotowane tła i kierunek odświeżenia mają charakter roboczy.
- Pełnej integracji wejścia i cyklu aplikacji. Potwierdzone scenariusze
  InputSystem nie zastępują wszystkich testów fizycznej myszy i klawiatury.
- Natywnych testów Windows 11 i pomiarów na docelowym laptopie z RTX 3050 Ti.
  Dotychczasowe próby wersji Windows wykonywano w środowisku testowym Wine.

Nie ma jeszcze podstaw do deklaracji zgodności całej gry 1:1 ani gotowej
oprawy na poziomie oczekiwanym w 2026 roku.

## Stan przy zatrzymaniu

Ostatni zamknięty etap obejmuje sprawdzenie obu klawiszy Shift i rozpoznanie
kolejnego fragmentu protokołu wejścia oryginału. Niezbadanych odbiorców tego
protokołu nie podłączano do gry. Planowanej kolejnej próby natywnego startu
oryginału w maszynie wirtualnej nie rozpoczęto.

Projekt jest zapisany w `/workspace/gierka/Unity/AncientConquest`.
Kod, zasoby, wyniki testów i dokumentacja pozostają w katalogu roboczym.
Nic nowego nie opublikowano i nie utworzono kolejnej paczki ZIP.
Wznowienie pracy wymaga nowego polecenia użytkownika.
