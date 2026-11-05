"""Inspect a small Garmin Personal API sample without changing reporting data."""

import argparse
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys

import requests
from dotenv import load_dotenv

BASE = "https://personal.connectapi.garmin.com"
TOKEN_PATH = "/personalapitoken-service/personal-api/personal-api-key/token"


class GarminError(RuntimeError):
    """A sanitized error that never includes credentials or response bodies."""


class GarminClient:
    def __init__(self, api_key, session=None):
        if not api_key or not api_key.strip():
            raise GarminError("Set GARMIN_PERSONAL_API_KEY in your local .env file.")
        self.api_key = api_key.strip()
        self.session = session or requests.Session()
        self.token = None

    def _request(self, method, path, **kwargs):
        try:
            response = self.session.request(
                method, BASE + path, timeout=45, allow_redirects=False, **kwargs
            )
        except requests.RequestException:
            raise GarminError("Garmin request failed; check network access.") from None
        if not 200 <= response.status_code < 300:
            raise GarminError(f"Garmin returned HTTP {response.status_code}.")
        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError:
            if path == TOKEN_PATH and response.headers.get("Content-Type", "").split(";")[0] == "text/plain":
                token = response.text.strip()
                if len(token.split(".")) == 3 and not any(c.isspace() for c in token):
                    return {"access_token": token}
            raise GarminError("Garmin returned an unexpected non-JSON response.") from None

    def authenticate(self):
        data = self._request(
            "POST", TOKEN_PATH,
            headers={"Authorization": "ApiKey " + self.api_key},
        )
        token = data.get("access_token") if isinstance(data, dict) else None
        if not isinstance(token, str) or not token:
            raise GarminError("Token response has an unexpected shape; authentication needs review.")
        self.token = token

    def get(self, path, params=None):
        if self.token is None:
            self.authenticate()
        return self._request(
            "GET", path, params=params,
            headers={"Authorization": "Bearer " + self.token},
        )


def field_inventory(value, prefix="", result=None):
    """Describe field paths and types without including personal values."""
    result = {} if result is None else result
    result.setdefault(prefix or "$", set()).add(type(value).__name__)
    if isinstance(value, dict):
        for key, child in value.items():
            field_inventory(child, f"{prefix}.{key}" if prefix else key, result)
    elif isinstance(value, list):
        for child in value:
            field_inventory(child, prefix + "[]", result)
    return result


def write_private_json(path, value):
    with open(path, "x", encoding="utf-8", opener=lambda p, f: os.open(p, f, 0o600)) as stream:
        json.dump(value, stream, indent=2)


def collect(client, start, end, output):
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    report = {"start_date": str(start), "end_date": str(end), "samples": []}
    jobs = []
    for offset in range((end - start).days + 1):
        day = str(start + timedelta(days=offset))
        jobs.extend([
            (f"daily_{day}", "/usersummary-service/usersummary/daily", {"calendarDate": day}),
            (f"sleep_{day}", "/sleep-service/sleep/dailySleep", {"date": day}),
            (f"hrv_{day}", f"/hrv-service/hrv/{day}", None),
            (f"heart_rate_{day}", "/wellness-service/wellness/dailyHeartRate", {"date": day}),
        ])
    jobs.extend([
        ("body_battery", "/wellness-service/wellness/bodyBattery/reports/daily",
         {"startDate": str(start), "endDate": str(end)}),
        ("activities_sample", "/activitylist-service/activities/search/activities",
         {"startDate": str(start), "endDate": str(end), "start": 0, "limit": 10}),
    ])
    for name, path, params in jobs:
        entry = {"sample": name, "endpoint": path}
        try:
            data = client.get(path, params)
            write_private_json(output / (name + ".json"), data)
            fields = field_inventory(data)
            entry.update(status="ok" if data is not None else "no_data",
                         fields={key: sorted(types) for key, types in fields.items()})
        except GarminError as exc:
            entry.update(status="error", error=str(exc))
        report["samples"].append(entry)
    write_private_json(output / "inventory.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", type=date.fromisoformat, required=True)
    parser.add_argument("--end-date", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    if not 0 <= (args.end_date - args.start_date).days <= 6:
        parser.error("Choose an inclusive range of 1 to 7 days for this initial probe.")
    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env")
    try:
        client = GarminClient(os.getenv("GARMIN_PERSONAL_API_KEY"))
        client.authenticate()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        output = root / "exports" / "garmin" / stamp
        report = collect(client, args.start_date, args.end_date, output)
    except GarminError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    failures = sum(item["status"] == "error" for item in report["samples"])
    print(f"Saved Garmin samples and field inventory to {output}")
    print(f"Endpoint failures: {failures}; inspect inventory.json for details.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
