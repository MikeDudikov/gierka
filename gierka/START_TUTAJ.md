# Pobieranie pełnej paczki dla Claude Code

To kompletna paczka **6211051481 bajtów**. Jest podzielona na sześć części
przechowywanych w Git LFS. Podział nie usuwa ani nie zmienia żadnych plików;
po scaleniu otrzymasz dokładnie pierwotne archiwum6,2GB.

Nie używaj „Download ZIP” jako zamiennika paczki: archiwum kodu GitHub może
zawierać tylko wskaźniki LFS. Skrypty poniżej pobierają rzeczywiste dane.

## Windows — najprościej

Otwórz PowerShell w katalogu, w którym chcesz zapisać paczkę, i wykonaj:

```powershell
Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/MikeDudikov/gierka/gierka/gierka/Pobierz-paczke.ps1' -OutFile 'Pobierz-paczke.ps1'
powershell -ExecutionPolicy Bypass -File '.\Pobierz-paczke.ps1'
```

Skrypt pobierze sześć części, zweryfikuje każdą z nich, scali archiwum i sprawdzi
jego końcową sumę. Nie wymaga instalowania Git LFS. Domyślnie zapisuje pliki
w podkatalogu `AncientConquest-paczka` bieżącego katalogu.

## Linux / WSL2 / Python

```sh
curl -fL https://raw.githubusercontent.com/MikeDudikov/gierka/gierka/gierka/pobierz_paczke.py -o pobierz_paczke.py
python3 pobierz_paczke.py
```

Pobieranie można wznowić. Gotowych części ze zgodną sumą skrypt nie pobiera drugi raz.
Alternatywnie pobierz ręcznie wszystkie pliki `.part001`…`.part006` z katalogu
[paczka](paczka), a potem scal je w tej kolejności. Nie rozpakowuj pojedynczych części.

Oryginalna suma SHA256 archiwum:

```text
fa850d9df733e7ab8f0e295377ebbe2a255a0a25cbae1767e5372fdbc5a95060
```

## Kontynuacja w Claude Code

Rozpakuj gotowy `AncientConquest-ClaudeCode-2026-11-04.tar.gz` w Linux/WSL2:

```sh
tar -xzf AncientConquest-ClaudeCode-2026-11-04.tar.gz --no-same-owner
```

Otwórz `AncientConquest-ClaudeCode/gierka` w Claude Code i przeczytaj
`CLAUDE.md` oraz `handoff/START_TUTAJ.md`. Katalog `toolchains` zostaw obok
`gierka`. Gotowe polecenie kontynuacji jest w `handoff/POLECENIE_DLA_CLAUDE.txt`.

Paczka zawiera kod, dane źródłowe, testy, dowody i narzędzia analityczne.
Pełna gra nie jest ukończona; znana blokada instalatora w Wine jest opisana
w przekazaniu. Unity Editor i aktywację trzeba odtworzyć na nowej maszynie.
