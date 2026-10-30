# Przegląd wiadomości

Poranny przegląd wiadomości w pięciu kategoriach: Europa, Świat, Polska, Kraków, Kultura (muzea, sztuka, film, muzyka, książki, teatr, historia – polska i zagraniczna).

- `docs/` – aplikacja (PWA) publikowana przez GitHub Pages; wydania w `docs/data/RRRR-MM-DD.json`
- `scripts/zrodla.py` – lista źródeł RSS i słowa kluczowe (kategorie, tematy)
- `scripts/generuj.py` – pobiera kanały, wybiera wiadomości, zapisuje wydanie, trzyma dzisiejsze + 3 poprzednie
- `.github/workflows/wydanie.yml` – codziennie przed 7:00 czasu warszawskiego

Tryb Claude: dodaj w repozytorium sekret `ANTHROPIC_API_KEY` (Settings → Secrets and variables → Actions).
Wtedy Claude wybiera najważniejsze i różnorodne wiadomości oraz pisze polskie streszczenia na podstawie leadów.
Bez klucza działa tryb RSS (oryginalne leady, część po angielsku).

Ręczne wydanie: zakładka Actions → „Poranne wydanie” → Run workflow, albo lokalnie `python scripts/generuj.py`.
