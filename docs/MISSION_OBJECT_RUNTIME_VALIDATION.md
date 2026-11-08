# Kontrola diagnostycznego widoku obiektów miss000

`tools/smoke_mission_objects.py` obserwuje rzeczywisty player Windows Mono pod
lokalnym Wine11/Xvfb. Uruchamia cztery oddzielne sesje `--mission-object-reference`.
To widok źródłowego terenu z pięcioma zamrożonymi rafami, nie grywalna misja
ani wykonanie oryginalnych konstruktorów. Źródłowe grafiki pozostają referencją,
nie finalną oprawą2026.

Uruchomić **po zakończeniu nowego buildu**, z nowym katalogiem wynikowym:

```sh
.venv/bin/python tools/smoke_mission_objects.py --output artifacts/objects/runtime-<nowa-nazwa>
```

Narzędzie odmawia zastąpienia istniejących dowodów i przejęcia zajętego X11`:79`.
Każda sesja tworzy własny Xvfb/player i sprząta wyłącznie własne procesy.
Nie wstrzykuje wejścia OS, nie wywołuje metod domeny i nie kończy globalnie Wine.
Podczas testu nie wolno budować do współdzielonego katalogu playera.

## Niezależna referencja pikseli

Preflight weryfikuje źródłowy kontrakt i stałe SHA256 zdekodowanego terenu,
planarnej mapy oraz czterech payloadów obiektów:

| Payload | Bajty | SHA256 |
| --- | ---: | --- |
| ObjectSeeds.bytes |8356|448ef43d4a625439bf4d853a4d1d37cc6845ada22d6274a57be0a4ebf4383539|
| ReefFramesRgba.bytes |32768|6b033ca9c2068fa50823823066661bedff8a5a7226404c070f911142ff98707d|
| MissionDescriptor.bytes |1788|458dac3b5942c5dff55d0640cb354a3761be9c824074cb99c29a939856a03ded|
| SavedViews.bytes |80|b8a17a6b40efc364c44dc2a1470a1ace8188de20e6cf057edd6865eff04800f8|

Sprawdza45ciągłych rekordów, długości i indywidualne hashe. Bajty pięciu raf
muszą zgadzać się z hash-guarded fixture rzeczywistego wykonania x86 w
`tests/fixtures/mission_reef_seed.json`. Nie przyjmuje dowolnych pozycji z nowego
manifestu jako oczekiwanego obrazu.

RGBA terenu i atlasu są odwracane z bottom-up do porządku górny→dolny.
Checker składa pięć pełnych płaszczyzn64×64 z alfą na zdekodowanym terenie,
według referencyjnych kotwic `(cellX*64,cellY*64)`. Nie dodaje ponownie
left/top źródłowego bbox. Następnie wycina960×540 i skaluje Point2× do1920×1080.
Nie korzysta z produkcyjnych funkcji C#, aby wyliczyć obraz oczekiwany.

| Sesja | Origin komórek diagnostycznej kamery | W pełni widoczne ID raf |
| --- | --- | --- |
| reef-00000009 |0,4|9|
| reef-0000000a |9,8|10|
| reefs-00000005-00000006 |9,15|5,6|
| reef-00000021 |0,15|33|

Wszystkie pięć raf ma osobną kontrolę obrazu. Inny kadr oryginału nie jest
narzucany temu diagnostycznemu viewportowi.

## Warunki zaliczenia

- Rzeczywiste okno ma geometrię0,0,1920,1080 i loguje ExclusiveFullScreen.
- Globalny framebuffer spełnia kryteria terenu: średni błądRGBściśle<1;
  najwyżej0,5%pikseli może różnić się owięcej niż4 w dowolnym kanale.
  Jednolity obraz, shader-magenta i niewłaściwe wymiary są odrzucane.
- Każda widoczna rafa ma osobny obszar128×128. Jego średni błądRGB musi być<1,
  a osobna średnia na faktycznie pokrytych przez alfę pikselach także<1.
  Dzięki temu mały obiekt nie może zniknąć w tolerancji całego framebufferu.
- Log wymaga source45,selected45,zero wykonanych konstruktorów C#,
  wszystkich pięciu ID z oryginalnymi komórkami i wariantami, bez duplikatów.
- Źródłowy setup jest jawnie raportowany jako player1,1, savedorigin15,0,
  view9×8. Diagnostyczna kamera pozostaje osobnym kontraktem.
- Wymagane są `reference_state=1; frame=0; empty_collision_reference=True;
  simulation=False`, brak wyjątków i brak komend zwykłego menu.
- Player sam kończy diagnostykę po8s przez Application.Quit(0), z kodem0,
  właściwym markerem w logu i co najmniej6s zaobserwowanego czasu od gotowości.
  Wymuszone sprzątanie nie zamienia porażki w zaliczenie.

Checker czeka na faktycznie zaprezentowany zgodny obraz, do5s po gotowości.
Zachowuje każdy niepasujący capture i metryki; sam log nie wystarcza.
Nie stosuje crop-maskowania całego obrazu ani dobierania próbnych kolorów.
Regiony raf są dodatkowym, ostrzejszym kryterium.

## Dowody i aktualna granica

Każda sesja zapisuje launch.json,geometry.txt,logi player/Wine/Xvfb,
expected.png,rzeczywiste frame-*.png,frame-attempts.json i raport albo failure.
Raport końcowy powstaje tylko po przejściu wszystkich czterech sesji. Hashe
EXE,DLL,manifestów,payloadów i fixture nie mogą zmienić się pomiędzy sesjami.

Przygotowany checker przeszedł48dodatnich/ujemnych kontroli w czystym Pythonie:
`artifacts/objects/position/qa-helper-controls/report.json`. Dokładne referencje
przechodzą; brak każdej z pięciu raf, zły wariant, centralny pivot, podwójny
bboxoffset, pusty/magenta obraz, flip, blur i inne wymiary są odrzucane.
Odrzucane są również błędne dane setupu, brak/zmiana deklaracji raf, wykonane
konstruktory zamiast seeda, brak deklaracji pustej komórki i wyjątek w logu.
`--help` i py_compile także przeszły. Te kontrole **nie uruchamiają usług**
i nie dowodzą działania playera.

Nowy player przeszedł wszystkie cztery sesje:
`artifacts/objects/runtime-final/report.json`. Każdy pełny framebuffer ma
średni błądRGB0, maksymalny błąd0 i100%identycznych pikseli. Wszystkie pięć
regionów raf ma średni błąd0 także po ograniczeniu do pokrycia alfa.
Każde okno miało geometrię0,0,1920,1080 i ExclusiveFullScreen, a każda sesja
zakończyła się diagnostycznym timerem8s z kodem0. Nie użyto wejścia OS.

Zbadany build Windows64Mono:143756027bajtów, Unity6000.3.27f2,
0błędów/0ostrzeżeń w BuildReport. DLL Assembly-CSharp SHA256:
`086b6336947ea73315854addb4c21713b5999d94697b19be729cb8234e8f8817`.
To samo DLL obejmują cztery raporty. Obejrzano rzeczywiste kadry z rafą09
oraz parą05+06; obrazy i dokładne próby przejściowe pozostają w podkatalogach sesji.

Wynik potwierdza zamrożone referencje w diagnostycznym rendererze.
Wine/Xvfb nie zastępuje natywnego Windows11,
fizycznego wejścia, docelowego i5/16GB/RTX3050Ti ani pomiarów wydajności.
Nie zweryfikowano pełnego spawn, kolizji, dynamiki, animacji, draw order
wszystkich klas, AI, ekonomii, walki, audio i ukończenia misji.
Zwykłe menu/briefing oraz sam teren wymagają swoich testów regresyjnych.
