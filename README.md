# Gierka — przygotowanie Unreal Engine 5

Automatyzacja pobierania oficjalnych źródeł najnowszego stabilnego wydania UE5.
Silnik jest instalowany poza repozytorium projektu. Kod gry nie został jeszcze
utworzony; kompilacja silnika i wydania Windows nie została zweryfikowana.

## Wymagania

- Python 3.12 i Git.
- Dostęp używanego przez Git uwierzytelnienia do `EpicGames/UnrealEngine`.
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

Skrypt wybiera najwyższy numerycznie oficjalny tag `5.x.y-release`, przypina jego
commit i sprawdza zgodność pobranego `HEAD` oraz `Engine/Build/Build.version`.
Wersje preview/early-access i UE6 są pomijane. Istniejący katalog docelowy nie jest
nadpisywany. Skrypt korzysta ze zwykłego Git i odziedziczonej konfiguracji
uwierzytelnienia, proxy oraz weryfikacji TLS; nie zapisuje tokenów.

Błąd HTTP 403 zatrzymuje pobieranie. Dostęp konta w przeglądarce trzeba udostępnić
także środowisku wykonującemu Git. Nie umieszczaj danych logowania w repozytorium.

## Dalsze przygotowanie silnika

Pobranie źródeł jest pierwszym etapem instalacji. Zależności, wersję kompilatora,
wymagania systemowe i sposób budowania należy dobrać z oficjalnej dokumentacji
wybranego wydania: https://dev.epicgames.com/documentation/en-us/unreal-engine.

Do docelowego wydania Windows potrzebne jest stanowisko Windows z obsługiwanymi
przez wybrane UE5 wersjami MSVC i Windows SDK. Lokalny Linux nie jest stanowiskiem
walidacji Windows 11 ani pomiarów wydajności na RTX 3050 Ti.

## Weryfikacja automatyzacji

```sh
python3 -m unittest discover -s tests -v
```

Testy obejmują wybór stabilnej wersji, kontrolę pobranego commitu/metadanych oraz
ochronę istniejących plików. Korzystają z lokalnych repozytoriów testowych;
nie pobierają silnika i nie stanowią testu Unreal Engine ani gry.
