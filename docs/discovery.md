# Broader web discovery

On September 13, 2026, discovery was expanded beyond the two GitHub lists using public web searches covering all six New England states, technology roles, regional employers, university career pages, and ATS-hosted postings. Search-result snippets and aggregator locations are leads, not verified jobs. Employers do not have to be headquartered in New England: an actual regional job location is what matters.

## What is monitored automatically

- `data/companies.json` contains recurring board configurations. New entries record `discovered_via` and `evidence_url`, distinguishing independent web discovery from official application links found in existing listings.
- `data/web_postings.json` contains individual employer pages discovered on the web when full-board collection is unavailable. These are fetched again on every full refresh, with JobPosting JSON-LD preferred. A confirmed 404/410 counts as absence; request failures and anti-bot responses do not.
- GitHub Actions rechecks configured sources every six hours. It does **not** execute a general web search engine or crawl the entire internet. Broad discovery is a separate manual step; newly verified boards and posting URLs become recurring sources.
- New Workday configurations use a `2027` query to keep broad employer-board collection within reasonable request limits. This can miss year-omitted postings; the configuration states that limitation.

## Example independent discoveries

- [Walleye Capital student board](https://job-boards.greenhouse.io/walleyecapital-external-students): quantitative development and research in Boston.
- [Secretariat](https://job-boards.greenhouse.io/secretariatadvisorsllc): engineering-science opportunities in Boston.
- [Interactive Brokers careers](https://www.interactivebrokers.com/en/general/about/careers-splash.php): migrated from Greenhouse to Dayforce; retained as a disabled watchlist entry until collection is supported.
- [Gartner IT internship](https://jobs.gartner.com/jobs/job/113095-summer-2027-it-intern-may-2028-graduates/): Stamford, Connecticut; public Workday board added.
- [IAT network operations internship](https://iatinsurancegroup.wd1.myworkdayjobs.com/en-US/iat/job/Cheshire-CT/Network-Operations-Internship_JR100371): Cheshire, Connecticut.
- [Avangrid technology, cyber and data internship](https://iberdrola.wd3.myworkdayjobs.com/en-US/Iberdrola/job/XMLNAME-2027-Technology--Cyber---Data-Internship-Program_R-32747): employer-listed Connecticut and Maine options.
- [BerryDunn technology assurance internship](https://careers-berrydunn.icims.com/jobs/4021/summer-2027-internship---technology-assurance/job?in_iframe=1): Portland, Maine.

These links document discovery, not permanent availability. Current collection results are in `data/source_status.json`.

## Repeatable search approach

Search each of Massachusetts, Rhode Island, Connecticut, New Hampshire, Vermont, and Maine using variations of:

```text
"summer 2027" internship software STATE
"2027" internship "machine learning" STATE
"2027" internship data cybersecurity STATE
"intern" CITY site:job-boards.greenhouse.io
"intern" CITY site:jobs.ashbyhq.com
"intern" CITY site:jobs.lever.co
```

Follow leads to official employer URLs, check geographic and cycle evidence, and add the public board identifier or specific posting page. Verify the collector before claiming coverage. Include university/public job directories in discovery, but do not assume that a nationwide remote posting is specifically available in a state merely because an aggregator labels it with a local city.

The public README now excludes uncategorized/nontechnical opportunities. Technical titles qualify directly; generic internship titles need explicit technical description evidence. Older nontechnical records remain in historical exports until normal retirement rules apply. No finite search provides exhaustive internet-wide coverage.
