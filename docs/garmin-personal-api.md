# Garmin Personal API exploration

This initial read-only collector exports raw samples and a field/type inventory.
It does not load the reporting database, merge Strava activities, or choose source precedence.

1. Create a Personal API key through Garmin Connect Web. Save it in the repository's ignored `.env` file as `GARMIN_PERSONAL_API_KEY=...`. Never commit the key.
2. From the repository root, use the existing Python environment:

   ```sh
   .venv/bin/python -m src.tools.garmin_probe --start-date 2026-11-03 --end-date 2026-11-04
   ```

3. Review `exports/garmin/<run>/inventory.json` for endpoint outcomes and field types. Raw responses in the same folder contain personal health data. `exports/` is already ignored by Git.

The initial probe requests daily summaries, sleep, HRV, daily heart rate, Body Battery reports, and up to ten activity summaries over 1–7 days. Activity results are deliberately a sample, not a complete historical import. Partial endpoint failures are recorded and return a nonzero exit code. Authentication must succeed before collection starts. Tokens stay in memory; each execution obtains a new one. Garmin's live token endpoint returned a plain-text token; the collector supports this response as well as a JSON access token.

## Validation and scope

On November 5, 2026, a local run for November 3–4 completed all ten sample requests without endpoint errors and returned three activity summaries. Authentication and data access are verified for that account and window; older history and other accounts remain untested. Raw responses stay in ignored local exports and are not PR artifacts.

Run the offline checks with:

```sh
.venv/bin/python tests/unit/test_garmin_probe.py
```

This collector is the first integration milestone. Follow-up work should review the existing star schema and Power BI dependencies, compare matched Garmin and Strava workouts, and decide field ownership before adding database migrations or broad backfills. Strava is the preferred source for gear assignments and Strava-defined segment efforts. Garmin GPS and recorded measurements remain candidates pending comparison, including timestamp alignment.

Garmin documents Personal API tokens as valid for up to 24 hours and configurable key expiration up to one year. Personal access is for your own data; a future service for other users needs the appropriate Garmin developer program.

References:

- https://developer.garmin.com/gc-developer-program/personal/personal-faq
- https://developer.garmin.com/gc-developer-program/personal/swagger-docs/

Endpoint definitions verified against Garmin's published OpenAPI document on November 5, 2026. Live metric availability depends on the account, device, and recorded data. Training readiness and recovery time have not been confirmed as dedicated endpoints.
