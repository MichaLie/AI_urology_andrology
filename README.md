# AI in Urology and Andrology Reproducibility Repository

This repository contains the minimum public data and code required to reproduce the review workflow outputs shared with the article.

## Layout

- `data/`: core input tables and minimal workflow metadata
- `assets/`: image panels required for the translation/collaboration figure
- `scripts/`: retrieval, screening, and figure/table generation scripts

Generated figure files are not stored in the repository. They are created when the scripts are run.

## Core data

- `screening_database.csv`: screened PubMed-indexed record set without abstract text
- `included_records.csv`: final included record set
- `screening_counts.json`: counts required to rebuild the screening flow diagram
- `pubmed_search_strings.csv`: PubMed search strings
- `top_journals.csv`: journal count table
- `readiness_matrix.csv`: readiness assignments by clinical task
- `reporting_frameworks.csv`: reporting and governance framework table
- `readiness_anchor_sources.csv`: anchor evidence source table

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Rebuild outputs

```bash
python3 scripts/build_prisma_flow_diagram.py
python3 scripts/build_publication_trends_figure.py
python3 scripts/build_review_burden_assets.py
python3 scripts/build_readiness_map_figure.py
python3 scripts/build_translation_collaboration_figure.py
python3 scripts/build_anchor_evidence_matrix.py
```

## Retrieval and screening

```bash
python3 scripts/pubmed_harvest.py --email your_email@example.com
python3 scripts/ai_screening.py --input ../data/screening_master.csv --output ../data/screening_master_screened.csv
```

## Notes

- The public screening table does not include abstracts.
- The translation/collaboration figure depends on the two panel images in `assets/`.
