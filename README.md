# Gierka — przygotowanie Unreal Engine 5

Automatyzacja pobierania źródeł UE5 z repozytorium Epic lub wskazanego forka GitHub.
Źródła silnika są pobierane poza repozytorium projektu. Kod gry nie został jeszcze
utworzony; kompilacja silnika i wydania Windows nie została zweryfikowana.

## Wymagania

- Python 3.12 i Git.
- Dostęp używanego przez Git uwierzytelnienia do wybranego repozytorium źródeł.
  Epic opisuje uzyskanie dostępu na https://github.com/EpicGames/Signup.
- Dostęp sieciowy do GitHub, a przy przygotowywaniu zależności także do serwerów Epic.
- Miejsce na źródła, zależności i późniejszą kompilację silnika. Pobranie źródeł
  nie potwierdza, że dysk pomieści pełny build.

## Sprawdzenie dostępu i pobranie

Z katalogu repozytorium:

```sh
python3 tools/install_unreal.py --check-access
python3 tools/install_unreal.py --destination /workspace/toolchains/UnrealEngine
```

Bez opcji `--ref` skrypt wybiera najwyższy numerycznie tag `5.x.y-release` dostępny
w wybranym repozytorium, przypina jego
commit i sprawdza zgodność pobranego `HEAD` oraz `Engine/Build/Build.version`.
Wersje preview/early-access i UE6 są pomijane. Istniejący katalog docelowy nie jest
nadpisywany. Skrypt korzysta ze zwykłego Git i odziedziczonej konfiguracji
uwierzytelnienia, proxy oraz weryfikacji TLS; nie zapisuje tokenów.

Fork `MikeDudikov/UnrealEngine` udostępnia gałąź `release`, ale nie ma tagów wydań.
Można jawnie wybrać tę gałąź albo konkretny commit:

```sh
python3 tools/install_unreal.py --repository https://github.com/MikeDudikov/UnrealEngine.git --ref release --check-access
python3 tools/install_unreal.py --repository https://github.com/MikeDudikov/UnrealEngine.git --ref f45729c0b6f097038e72b52d366a62baeca3275b --destination /workspace/UnrealEngine
```

Druga komenda służy do pierwszego pobrania do nieistniejącego katalogu. Istniejący
checkout jest zachowywany. Jawny commit/gałąź oznacza snapshot źródeł; nie stanowi
potwierdzenia najnowszej wersji upstream Epic. Brak tagów nie uruchamia
automatycznego wyboru gałęzi.

Błąd HTTP 403 zatrzymuje pobieranie. Dostęp konta w przeglądarce trzeba udostępnić
także środowisku wykonującemu Git. Nie umieszczaj danych logowania w repozytorium.

## Dalsze przygotowanie silnika

Pobranie źródeł jest pierwszym etapem instalacji. Zależności, wersję kompilatora,
wymagania systemowe i sposób budowania należy dobrać z oficjalnej dokumentacji
wybranego wydania: https://dev.epicgames.com/documentation/en-us/unreal-engine.

Do docelowego wydania Windows potrzebne jest stanowisko Windows z obsługiwanymi
przez wybrane UE5 wersjami MSVC i Windows SDK. Lokalny Linux nie jest stanowiskiem
walidacji Windows 11 ani pomiarów wydajności na RTX 3050 Ti.

## Stan zweryfikowany w środowisku chmurowym

- Pobrano `/workspace/UnrealEngine` z forka `MikeDudikov/UnrealEngine`.
- Commit `f45729c0b6f097038e72b52d366a62baeca3275b`; `Build.version` wskazuje **5.8.4**.
- Zainstalowano zgodny z manifestem SDK .NET **10.0.203**. Zweryfikowano oficjalną
  sumę SHA-512 oraz kompilację i uruchomienie osobnego programu C#.
- Pobieranie zależności przez GitDependencies zatrzymało się na HTTP 403 proxy
  dla `cdn.unrealengine.com`; edytor i UnrealBuildTool nie zostały zbudowane.
- Manifest opisuje około **85,1 GiB** domyślnych zależności oraz **30,4 GiB** cache.
  Przy około **55 GiB** wolnego dysku pełna instalacja i kompilacja wymagają
  większej przestrzeni. Zestaw ograniczony do Linux również wymaga zapasu na build.
- Aktywna polityka sieci nadal nie zawiera domen Epic zapisanych w szkicu ustawień.

Aktywacja zainstalowanego narzędzia C# w tej maszynie:

```sh
source /workspace/toolchains/env-unreal.sh
dotnet --list-sdks
```

Źródła silnika nie zostały zmienione. Lokalna reguła `.git/info/attributes` dla
pojedynczego skryptu jemalloc usuwa jedynie pozorną zmianę wynikającą z CRLF;
surowa zawartość pliku jest zgodna z blobem commitu.

## Weryfikacja automatyzacji

```sh
python3 -m unittest discover -s tests -v
```

Testy obejmują wybór stabilnej wersji, kontrolę pobranego commitu/metadanych oraz
ochronę istniejących plików. Korzystają z lokalnych repozytoriów testowych;
nie pobierają silnika i nie stanowią testu Unreal Engine ani gry.
