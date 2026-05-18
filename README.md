## Farlig skolevej

Automatisering der behandler ansøgninger om befordring på farlig skolevej fra XFlow og opdaterer processen med relevant skoleinformation fra SBSYS.

## Hvad gør robotten?

1. **Henter ansøgninger** fra XFlow via `ProcessClient` – søger efter processer i aktiviteten `RPAIntegration` (proceskabelon ID 810)
2. **Udtrækker data** fra ansøgningens blanketter: barnets adresse, klassetrin og CPR-nummer
3. **Tilføjer til arbejdskø** i Automation Server til efterfølgende behandling
4. **Slår borgerens indskrivningssag op** i SBSYS for at finde den relevante "Indskrivning Klasse"-sag
5. **Opdaterer XFlow-processen** med sagsoplysninger og behandlingsdato, og rykker processen videre

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
| `rapidfuzz` | Fuzzy-matching af adresser (reserveret til fremtidig brug) |

## Persondatasikkerhed

Robotten behandler personoplysninger om mindreårige på vegne af Odense Kommune, herunder CPR-numre (almindelige personoplysninger jf. GDPR art. 6 og databeskyttelseslovens § 11).

- Ingen personoplysninger må lægges i dette repository — hverken som testdata, i kode eller i kommentarer
- Legitimationsoplysninger håndteres udelukkende via miljøvariabler (`.env`) og Automation Server Credentials
- `.env`-filen er ekskluderet via `.gitignore` og må aldrig committes

