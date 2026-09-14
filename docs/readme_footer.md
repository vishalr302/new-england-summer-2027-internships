## How it works

The tracker reads the raw [SimplifyJobs Summer 2027 README](https://github.com/SimplifyJobs/Summer2027-Internships) and the [Vansh & Ouckah Summer 2027 list](https://github.com/vanshb03/Summer2027-Internships), plus configurable public GitHub tables, then checks public company job boards. Simplify/Pitt CSC retain credit for their original collection; this project does not modify their repository. Sources are observations and may be incomplete.

README locations show New England options; full original locations remain in the exports. State names and uppercase postal abbreviations are the main geographic signals. Common New England cities and metro labels are fallbacks; explicit out-of-region locations override city-only matches. Nationwide remote jobs are excluded without a New England location or eligibility signal. City-only names can be ambiguous and should be checked by applicants.

Titles or explicit internship metadata must identify a student opportunity. Summer 2027 wording earns high confidence; a dedicated Summer 2027 source or a dated summer recruiting signal can earn medium confidence (◇). Other seasons and low-confidence roles are excluded. Graduation-year mentions alone do not qualify. Technology categories use editable title keywords, with explicit technical descriptions used for otherwise generic internship titles. Nontechnical roles are excluded from the displayed list.

Tracking parameters are removed before URL comparison. Matching company, role, and location also collapses duplicates, preferring direct company records. This intentionally conservative approach can miss renamed roles or conflate identical titles at the same location; inspect the application page. Every job keeps its first/last seen dates. It becomes inactive only after three complete successful checks of all its known sources find it absent. Source outages freeze missing counts, so stale roles may remain visible; `last_seen` is available in the exports.

## Broader web discovery

The company watchlist now includes employers discovered through broader web searches, beyond the two GitHub lists. Individual official postings are also rechecked from [data/web_postings.json](data/web_postings.json). See [discovery coverage and limitations](docs/discovery.md). Scheduled updates check configured sources; they do not run a general internet search.

## Run locally

Requires Python 3.11 or newer:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m src.main --github-only
python -m src.main
```

Use `python -m src.main --company Klaviyo` to diagnose a company without aging other sources. All paths resolve relative to the project. Generated files are README.md, data/jobs.json, data/jobs.csv, and data/source_status.json. Dates are UTC; the new-role badge uses an internal timestamp for a real rolling 24-hour window.

## Automation

[Update internships](.github/workflows/update_jobs.yml) runs approximately every six hours and on manual dispatch. It tests the code, refreshes sources sequentially, and commits changed exports with the repository's GitHub token. No secret API keys are required. GitHub schedules can be delayed and may disable after prolonged inactivity; the manual action remains available. The workflow needs Contents: read and write permissions and runs only on the default branch. Its concurrency group prevents overlapping writers.

## Add a company or source

Edit [data/companies.json](data/companies.json). Set `company`, a stable `id`, `ats`, and either its public board `identifier` or `careers_url`. Supported ATS types: `greenhouse`, `lever`, `ashby`, `smartrecruiters`, `workable`, `recruitee`, and isolated experimental `workday`. Generic pages use `generic`. See [collector configuration](docs/collectors.md) for examples and limitations. Disabled entries remain a transparent watchlist, not claimed coverage.

Add GitHub tables to [data/sources.json](data/sources.json), with `name`, raw `url`, and `season: "summer-2027"` only if the source is explicitly dedicated to that cycle. The parser supports HTML tables and standard Markdown tables with company, role, location, application, and optional age columns. Test unfamiliar formats before enabling them.

## Contribute

Open an **Add an internship** or **Suggest a company** issue, or submit a pull request with the official application URL and location/cycle evidence. See [CONTRIBUTING.md](CONTRIBUTING.md). Issues are reviewed; they are not automatically promoted into verified listings.

## Limits and responsible collection

Public boards are checked with timeouts, sequential requests, delays, and bounded retries. HTML pages honor robots.txt. Authentication, CAPTCHAs, anti-bot walls, and private endpoints are never bypassed. Generic scraping cannot reliably enumerate JavaScript-only boards. Experimental Workday configurations vary by tenant; partial pagination or parser failures are treated as source failures. A source failure never proves that a job has closed.

This list is not exhaustive and is not affiliated with employers or Simplify. **Job information can change. Confirm all details and apply through the employer's official careers page.**
