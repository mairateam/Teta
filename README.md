# Teta: hledanost vertikály, značek a konkurence

Report hledanosti (Google Ads Keyword Planner) pro Teta drogerie, Česko. Vzhled Proficio.

- Stránka: https://<organizace>.github.io/<repo>/
- Lišta nahoře = pohledy: Vertikála (Drogerie obecně + 10 podkategorií podle tržeb v GA4),
  Značky (12 značek výrobců), Brand Teta, Konkurence (Teta, dm, Rossmann, Notino, Pilulka).
- Značky a Konkurence: přepínač značek, share of search po měsících, index a korelace s vertikálou.
- Filtr klíčových slov se ukládá do adresy, odkaz jde sdílet.

## Struktura
- `docs/index.html` – zveřejněná stránka (generovaná, data, písmo i knihovna grafů uvnitř; ručně se neupravuje).
  GitHub Pages publikuje jen složku `docs/`.
- `build_data.py` – generátor, `template.html` – šablona, `config.json` – seznam slov, podkategorií a značek.
- `raw/planner.csv` – poslední stažená data z Plánovače, `history/` – archiv zpracovaných dat a stabilní ID slov.
- `brand/` – písmo BC Novatica (Proficio).

## Aktualizace
Jednou měsíčně (15. den) se stáhnou nová data z Plánovače, přegeneruje se stránka a pushne sem.
Postup je v `UPDATE.md`.
