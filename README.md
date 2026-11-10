## Farlig skolevej

Automatisering der behandler ansøgninger om befordring på farlig skolevej fra XFlow og opdaterer processen med relevant skoleinformation fra SBSYS.

## Hvad gør robotten?

1. **Henter ansøgninger** fra XFlow via `ProcessClient` – søger efter processer i aktiviteten `RPAIntegration` (proceskabelon ID 813)
2. **Udtrækker barnets CPR-nummer** fra blanketten "Elevbefordring 0.-9. klasse - oplysninger om udfylder og barnet (ny)" (sammen med "… - Vurdering (ny)")
3. **Tilføjer til arbejdskø** i Automation Server med proces-ID og CPR-nummer (CPR-nummeret er kø-referencen). `--queue` rydder først alle elementer med status `NEW`
4. **Slår borgerens sager op** i SBSYS og beholder kun sager, hvor titlen indeholder "Indskrivning Klasse"
5. **Opdaterer XFlow-processen**: skriver en nummereret liste af sagstitler i feltet `Textfield-RPA-Skole` (eller "Ingen indskrivningssager fundet i sbsys", hvis der ingen er), sætter signatur ("Behandlet af Tyra (RPA)") og behandlingsdato, og rykker processen videre til rettighedsgruppen "BKF - Mobil i Odense"
6. **Registrerer opgaven** i aktivitetssporingen (`Tracker`). Fejl af typen `WorkItemError` markerer elementet som fejlet til manuel behandling

## Forudsætninger

- Python ≥ 3.13
- [`uv`](https://docs.astral.sh/uv/) til pakkehåndtering
- Adgang til **Automation Server** (arbejdskø)
- Adgang til **XFlow** (produktion)
- Adgang til **SBSYS** (produktion)
- En **Odense SQL Server**-konto til aktivitetssporing

## Installation

```sh
uv sync
```

## Konfiguration

Kopiér `.env.example` til `.env` og udfyld følgende:

| Variabel | Beskrivelse |
|---|---|
| `ATS_URL` | URL til Automation Server API |
| `ATS_TOKEN` | API-token til Automation Server |
| `ATS_WORKQUEUE_OVERRIDE` | (valgfri) ID på arbejdskø, der overstyrer standardkøen – bruges til test |

Øvrige legitimationsoplysninger (XFlow, SBSYS, SQL Server) hentes automatisk fra Automation Server Credentials under nøglerne:
- `Xflow - produktion`
- `SBSYS - produktion`
- `Odense SQL Server`

## Kørsel

```sh
# Fyld arbejdskøen med nye ansøgninger fra XFlow
uv run python main.py --queue

# Behandl arbejdskøen
uv run python main.py
```

### Argumenter

| Argument | Beskrivelse |
|---|---|
| `--queue` | Fyld arbejdskøen og afslut (kør ingen behandling) |

## Afhængigheder

| Pakke | Formål |
|---|---|
| `automation-server-client` | Arbejdskø-håndtering |
| `xflow-client` | Integration med XFlow (hentning og opdatering af processer) |
| `sbsys` | Opslag af indskrivningssager i SBSYS |
| `odk-tools` | Aktivitetssporing |
| `kmd-nexus-client` | Hjælpefunktionen `filter_by_predicate` til søgning i blanketternes elementtræ |
| `rapidfuzz` | Fuzzy-matching af adresser (reserveret til fremtidig brug) |
| `ruff` | Linting (kun udvikling) |

## Persondatasikkerhed

Robotten behandler personoplysninger om mindreårige på vegne af Odense Kommune, herunder CPR-numre (almindelige personoplysninger jf. GDPR art. 6 og databeskyttelseslovens § 11).

- Ingen personoplysninger må lægges i dette repository — hverken som testdata, i kode eller i kommentarer
- Legitimationsoplysninger håndteres udelukkende via miljøvariabler (`.env`) og Automation Server Credentials
- `.env`-filen er ekskluderet via `.gitignore` og må aldrig committes

