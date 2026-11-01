# Ancient Conquest — remake w Unity

Cel: zachować pełną treść i zachowanie oryginalnej gry, modernizując kosmetycznie
oprawę. Platforma docelowa: Windows 11, pełny ekran 1280×1024, laptop i5 3,6 GHz,
16 GB RAM i RTX 3050 Ti.

## Bieżący etap

Przygotowanie analizy oryginału. Plan małych etapów i bramki ukończenia znajdują
się w [docs/REMAKE_PLAN.md](docs/REMAKE_PLAN.md), a wymagania i luki dowodowe w
[docs/REFERENCE_MATRIX.csv](docs/REFERENCE_MATRIX.csv).

Nie utworzono jeszcze projektu Unity ani implementacji gry. Nie przeanalizowano
archiwum oryginału: załącznik przekracza limit transferu 32 MiB. Nie potwierdzono
obecności kodu źródłowego, formatów zasobów, fontów, reguł lub AI.

Zainstalowana oficjalna wtyczka Unity dostarcza instrukcje dla agenta. Pobranie
Unity CLI z `https://unity.com/install.sh` oraz odczyt oficjalnego katalogu wydań
z `services.api.unity.com` są blokowane przez proxy HTTP 403. Domeny instalacji
Unity i materiałów referencyjnych zapisano w szkicu konfiguracji; wymaga on
zastosowania i publikacji w ustawieniach środowiska. Status licencji nie został
potwierdzony przez działający CLI.

## Pierwszy krok: katalog oryginalnego ZIP-a

Po udostępnieniu lokalnej kopii archiwum:

```sh
mkdir -p artifacts
python3 tools/inventory_original.py /sciezka/do/oryginalu.zip --output artifacts/inventory.json
python3 tools/inventory_original.py /sciezka/do/oryginalu.zip --verify-contents --output artifacts/inventory-verified.json
```

Pierwsza komenda odczytuje metadane i hash ZIP-a; integralność zawartości pozostaje
`not_checked`. Druga strumieniowo sprawdza CRC i SHA-256 wpisów, z limitem 2 GiB
rozpakowanych danych. Limit można jawnie ustawić opcją `--max-expanded-bytes`.
Nieukończona weryfikacja kończy się błędem. Istniejące raporty nie są nadpisywane.

Narzędzie nie wypakowuje ani nie uruchamia plików. Rozszerzenia wskazują jedynie
kandydatów na obrazy płyty, źródła, programy i fonty; nie dowodzą formatu lub
użyteczności zasobu. Oryginały można trzymać lokalnie w ignorowanym
`reference/raw/`, a raporty w ignorowanym `artifacts/`.

## Narzędzia analizy i kontrola

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r tools/requirements-analysis.txt
.venv/bin/python -m unittest discover -s tests -v
```

W obecnym środowisku zależności są już w `/workspace/toolchains/media-analysis`:
pycdlib do ISO, pefile do nagłówków plików Windows i Pillow do grafik. Testy ZIP
używają przygotowanych danych testowych; nie są testami oryginału ani remake’u.

Narzędzia są pierwszym etapem pozyskania danych. Uruchomienie Unity, wierna
symulacja, cała treść, remaster oprawy i testy na docelowym laptopie pozostają
osobnymi wymaganymi etapami planu.
