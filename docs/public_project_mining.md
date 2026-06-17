# Public Embedded Project Mining

This workflow discovers public embedded repositories and extracts project-structure signals without defaulting to full clones.

## Boundaries

- Use official APIs or public datasets; do not scrape GitHub HTML pages.
- Read `GITHUB_TOKEN` from the environment only.
- Default to candidate metadata and manifest snapshots, not full repository copies.
- Respect rate limits with small limits, delay, cache, and resumable JSONL outputs.
- Do not collect secrets, private repositories, customer logs, or personal data.
- Treat mined data as discovery input, not verified failure evidence.

## Lightweight Discovery

```bash
python scripts/research/mine_github_projects.py \
  --query "zephyr prj.conf embedded firmware" \
  --query "esp-idf sdkconfig firmware" \
  --limit 100 \
  --delay 2 \
  --out research/project_corpus/candidates.jsonl
```

For CI or dry planning:

```bash
python scripts/research/mine_github_projects.py --dry-run
```

## Relevance Scoring

```bash
python scripts/research/score_embedded_relevance.py \
  --input research/project_corpus/candidates.jsonl \
  --out research/project_corpus/candidates_scored.jsonl \
  --min-score 20
```

Signals include Zephyr, ESP-IDF, PlatformIO, STM32Cube, FreeRTOS, embedded Linux, Cortex-M, and TinyML markers.

## Manifest Snapshot

```bash
python scripts/research/fetch_project_snapshot.py \
  --repo owner/name \
  --out-dir research/project_corpus/snapshots \
  --max-files 80
```

This saves manifest-like files such as `west.yml`, `prj.conf`, `sdkconfig`, `platformio.ini`, `.ioc`, `FreeRTOSConfig.h`, `Kconfig`, `Kbuild`, `CMakeLists.txt`, DTS/DTSI, overlays, and config files.

## Signal Extraction

```bash
python scripts/research/extract_project_signals.py \
  --snapshot-dir research/project_corpus/snapshots/owner__name \
  --out research/project_corpus/signals/owner__name.json
```

## Corpus Index

```bash
python scripts/research/build_project_corpus.py \
  --candidates research/project_corpus/candidates_scored.jsonl \
  --signals-dir research/project_corpus/signals \
  --out-csv research/project_corpus/embedded_project_index.csv \
  --out-jsonl research/project_corpus/embedded_project_index.jsonl
```

Use the resulting corpus to improve project adapters, examples, and failure-pattern coverage.
