# Collector configuration

Every collector returns the same dictionaries; filtering and history are shared. A zero-match result is distinct from a request/parser failure. Source status is written after every completed run. A functioning board can yield zero qualifying jobs.

```json
{"company": "Example", "id": "example", "ats": "greenhouse", "identifier": "example", "careers_url": "https://job-boards.greenhouse.io/example", "enabled": true}
```

Use the exact employer board identifier, not a guessed company slug. Lever EU boards additionally use `"region": "eu"`. Available collectors and references:

| Type | Public endpoint | Notes |
| --- | --- | --- |
| greenhouse | boards-api.greenhouse.io/v1/boards/ID/jobs?content=true | [Job Board API](https://developers.greenhouse.io/job-board.html); full board |
| lever | api.lever.co/v0/postings/ID | [Postings API](https://github.com/lever/postings-api); paginated |
| ashby | api.ashbyhq.com/posting-api/job-board/ID | [Posting API](https://developers.ashbyhq.com/docs/public-job-posting-api); full board |
| smartrecruiters | api.smartrecruiters.com/v1/companies/ID/postings | [Posting API](https://developers.smartrecruiters.com/docs/posting-api); public postings only |
| workable | www.workable.com/api/accounts/ID?details=true | [Public careers endpoint](https://help.workable.com/hc/en-us/articles/115012771647-Using-the-Workable-API-to-create-a-careers-page); no SPI/private token |
| recruitee | ID.recruitee.com/api/offers/ | [Offers API](https://docs.recruitee.com/reference/offers); published offers |
| workday | HOST/wday/cxs/TENANT/SITE/jobs | Experimental public careers interface; internship search, pagination and relevant details |
| generic | careers_url | JobPosting JSON-LD first, then configured HTML cards |

Workday requires `tenant`, `site`, and an employer's `careers_url` on its `myworkdayjobs.com` host. Its default search uses `intern`, which may omit co-ops and summer analysts. Configure `search_text` and `facets` for verified tenant filters; RTX uses its internship/co-op employment facet with an empty search. `max_jobs` defaults to 3,000; reaching the cap fails the source rather than exporting a partial board. This interface has no stable cross-tenant guarantee.

Generic HTML fallback uses explicit selectors:

```json
{
  "company": "Example", "id": "example", "ats": "generic",
  "careers_url": "https://example.com/careers",
  "selectors": {"job": ".job-card", "title": ".title", "link": "a.apply", "location": ".location"}
}
```

This reads one configured page by default. Add a `next` CSS selector for same-host pagination (up to 30 pages); MIT Lincoln Laboratory uses this mode. Configure a complete board or individual structured posting pages. It does not execute JavaScript, crawl an entire domain, or bypass protections. Do not default all jobs to company headquarters: headquarters are not proof of a job's location.

## Improving coverage

Prioritize verified campus boards and Workday tenants, additional parser fixtures, explicit remote-state eligibility, and employer requisition-ID matching. Enable accounts after checking the official employer link. Preserve disabled watchlist entries with a reason. Inspect data/source_status.json after configuration changes.
