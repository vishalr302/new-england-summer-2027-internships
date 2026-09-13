# Contributing

Submit missing internships and companies through the repository's issue templates. Include an official application link, New England location/remote eligibility, and Summer 2027 evidence. An issue is a suggestion awaiting review, not a verified listing.

To add monitoring, edit data/companies.json or data/sources.json and run the tests plus a targeted collector run. Use stable company IDs so history survives display-name changes. Do not add login credentials, private endpoints, or personal applicant information. Record unsupported pages explicitly rather than inventing jobs.

Edit docs/readme_footer.md for documentation changes: README.md is generated. Do not manually add rows to the generated exports. Keep parser fixtures small and synthetic. Never commit full employer descriptions or downloaded source pages.

Run `python -m unittest discover -s tests -v` before opening a pull request. Describe which public endpoint you verified and whether the collector enumerates the entire board. If an API returns partial results, fail that source so it cannot incorrectly age historical jobs.
