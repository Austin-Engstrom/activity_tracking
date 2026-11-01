# Weekly activity consistency

The Consistency folder in `measures_.tmdl` adds:

| Measure | Meaning |
|---|---|
| Active Weeks | Distinct selected local Monday-Sunday weeks containing GPS activity points |
| Weeks in Selection | Calendar weeks touched by the selected modeled dates, including inactive weeks |
| Inactive Weeks | Selected weeks minus active weeks |
| Active Week % | Active weeks divided by selected weeks |
| Active Days per Week | Active days divided by all selected weeks, including inactive weeks |
| Active Days per Active Week | Active days divided by active weeks only |
| Activities per Active Week | Distinct activities divided by active weeks |
| Longest Active Week Streak | Longest uninterrupted run of active weeks within the date selection |
| Longest Active Week Streak All Dates | Same streak ignoring date-dimension filters, preserving other filters |

Weeks start Monday in the activity's backfilled local timezone. Week-start dates,
not calendar week numbers, identify weeks so streaks cross New Year correctly.
At least one selected point makes a week active: mileage/time is not a threshold.
The dataset still excludes activities without valid GPS points. A multi-day or
multi-week activity can contribute to each day/week containing its GPS points.
The activity count numerator remains distinct, not duplicated per week.

A slicer on `dates[date]` restricts the dates used by all measures except the
explicit All Dates version. Other filters, such as activity type, gear or trail,
remain effective through the point fact. Segment-only filters retain the existing
model behavior and do not change ordinary point-based consistency measures.

Partial boundary weeks count as one week; only activity on dates actually selected
contributes. Skipped weeks break a streak even when omitted by a disjoint date
selection. Only dates present in the modeled calendar participate; it currently
spans the earliest through latest GPS point dates. These measures do not infer
activity before/after that history, fill future weeks, or imply that missing GPS
history proves inactivity. Zero-denominator averages/percentages are blank.
No current-week streak is added because an unfinished week needs a separate policy.

## Apply locally

Close Power BI, pull/check out this branch, then run:

```powershell
.\.venv\Scripts\python.exe -m src.tools.refresh_calendar
.\.venv\Scripts\python.exe -m src.tools.export_power_bi --views view_date
```

Only the small date Parquet file is refreshed. The other files stay untouched.
The normal full export and reporting rebuild also include these attributes.
Open `power_bi/gps/activity_tracking.pbip` and refresh. There are no source-table or
relationship changes and no GPS/spatial rebuild is needed.

## Power BI checks

- Put `dates[week_start_date]` on matrix rows with Activity Days, Activities,
  Active Days per Week and Active Weeks. Week rows should have 0/1 active weeks
  and 0-7 active days (only selected dates count for partial weeks).
- Add cards for Active Weeks, Active Week %, Longest Active Week Streak and
  Longest Active Week Streak All Dates. Use `dates[date]` in a Between slicer.
- Choose a known range with two active weeks, a missing week, and another active
  week: active weeks should be 3 and the longest streak 2. Expand the range and
  confirm the All Dates card does not change from the date filter alone.
- Check late December/early January. A week spanning the year boundary should
  appear once under its Monday date, not as two week-number/year combinations.
- Try a range with modeled dates but no activities: active weeks and streak are
  zero; average active days per active week is blank.

Calendar boundary/type tests and reference/dependency checks run offline. They do
not evaluate DAX; the slicer, gap and year-boundary behavior still needs Desktop
validation before merging. No report layout changes are included.

## Daily consistency

The same branch adds a **Consistency / Days** folder:

| Measure | Meaning |
|---|---|
| Active Days | Existing Activity Days count, displayed as zero when no dates qualify |
| Days in Selection | Modeled dates selected, including dates without activity |
| Inactive Days | Selected dates minus active dates |
| Active Day % | Active dates divided by selected dates |
| Activities per Active Day | Distinct selected activities divided by active dates |
| Point Miles per Active Day | Selected point miles divided by active dates |
| Point Moving Hours per Active Day | Selected point moving hours divided by active dates |
| Longest Active Day Streak | Longest consecutive run of active local dates within selection |
| Longest Active Day Streak All Dates | Same daily streak ignoring date-dimension filters only |

Weekly measures are organized under **Consistency / Weeks**. The legacy Activity
Days measure stays in Activities for compatibility and is the counting source for
Active Days. There are no additional SQL fields, exports or relationship changes
for the daily measures. If you already applied the weekly calendar update, only
pull/reopen the updated model; no repeat export is needed for the daily additions.

Daily streaks use actual local dates, so they cross months, leap days and years
without resetting. Inactive dates break a streak; an omitted date in a disjoint
selection also breaks it. Days outside the modeled calendar do not count. An
activity spanning midnight can make multiple dates active, but the activity-count
numerator still counts it once. These metrics cover GPS activities only and retain
the same segment-filter behavior as other ordinary point-based measures.

Before merging, use a date slicer with a known seven-day interval containing
activity on days 1, 2, 3 and 5: expect 4 active days, 3 inactive days, 57.1% active
days and a longest daily streak of 3. Remove day 2 from a disjoint selection and
confirm the gap breaks the streak. Compare the All Dates version while changing
only the date slicer. Ratios with no active-day denominator should be blank.
These are Desktop validation scenarios, not hardcoded targets or claims of DAX
execution by the Python test suite.
