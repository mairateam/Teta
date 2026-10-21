# Měsíční aktualizace dat (postup pro naplánovanou úlohu)

Cíl: doplnit nový měsíc z Google Keyword Planneru a zveřejnit ho. Seznam slov, podkategorie a značky
se NEMĚNÍ, berou se z `config.json`.

## 1. Seznam slov
Všechna slova = `vertical_kws[*][0]` + `znacky[*].keywords` + `konkurence[*].keywords` (bez duplicit, ~1 730 slov).
Rozděl je do dávek po 600.

## 2. Stažení z Plánovače
Pro každou dávku zavolej `mcp__Databy_MCP__google_ads__get_keyword_historical_metrics`:
- `_google_account`: `"company"`, `customer_id`: `config.customer_id` (8343406245)
- `language_id`: `"1021"`, `geo_target_ids`: `["2203"]`, `limit`: 1000, bez `start_year_month`/`end_year_month`

Výsledek je velký – nástroj vrátí odkaz `https://ai.databy.io/api/results/...` (platí 10 minut), stáhni ho hned
(`curl -sS -o raw/batchN.csv "<odkaz>"`). Pak dávky spoj do `raw/planner.csv` (jedna hlavička
`keyword,avg_monthly_searches,...`, řádky začínající `#` vynech). Počet řádků má být podobný jako minule.

## 3. Kontrola
Poslední měsíc v `monthly_search_volumes` má být předchozí kalendářní měsíc. Pokud je stejný jako v
`history/TETA.json` → `countries.vertikala.months`, Plánovač nový měsíc ještě nemá: nic necommituj a skonči.

## 4. Sestavení
```bash
NO_PROXY=localhost no_proxy=localhost npm install --silent --noproxy=localhost
python3 build_data.py      # zapíše docs/index.html a history/*.json
```
Počty slov a duplicit ve výpisu mají být podobné jako minule.

## 5. Zveřejnění
```bash
git add docs history raw
git commit -m "Aktualizace dat: přidán měsíc YYYY-MM (běh YYYY-MM-DD)"
git push origin main
```
