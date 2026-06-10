# Public Failure Case Ingestion

This folder is a quarantine pipeline for public engineering experience. Public
content should not go directly into runbooks, failure patterns, or golden packets.

## Layers

- `raw/`: API responses or source metadata captured from official APIs.
- `extracted/`: short structured summaries produced from raw data. These files
  avoid long quotes and preserve source URLs.
- `reviewed/`: human-reviewed case summaries that may be considered for
  promotion.

## Compliance principles

- Respect robots.txt and platform terms.
- Use official APIs first. Use GitHub REST API or `gh` for GitHub, and Stack
  Exchange API for Stack Exchange.
- Preserve source URLs and source titles.
- Do not collect personal privacy data.
- Do not collect secrets, tokens, keys, cookies, or credentials.
- Do not copy large forum posts or long issue bodies into this repository.
- Treat forum experience as candidate evidence by default, not as a confirmed
  root cause.
- Promote to failure pattern or golden packet only after human review.

## Suggested workflow

1. Fetch source metadata into `raw/`.
2. Run `extract_failure_case.py` to create a short structured summary in
   `extracted/`.
3. Review the summary manually and move approved cases to `reviewed/`.
4. Run `dedupe_failure_cases.py` before promotion.
5. Run `promote_case_to_pattern.py` only for cases whose
   `review.review_status` is `reviewed`.
