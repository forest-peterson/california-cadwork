# P6 XML for schedule transfer

What `scripts/cpm_blocks.py` reads from a Primavera P6 XML file, and the conventions to follow when writing one.

## Layout

- The root element is `APIBusinessObjects`, with a namespace that carries the P6 version. The script ignores namespaces, so any version reads the same way.
- Global calendars sit directly under the root. Each `Project` holds its own `Calendar`, `WBS`, `Activity`, `Relationship` and `ScheduleOptions` elements.
- Elements point at each other by `ObjectId`, a number unique within the file. `Id` is the code people see.

## Units and formats

- Dates are ISO 8601 local time without an offset, such as `2030-04-01T08:00:00`.
- Durations and lags are in hours. Divide by the calendar's `HoursPerDay` to get days.
- Work times give the first and the last working minute, so an 08:00 to 17:00 day with a lunch hour is written as `08:00:00`–`11:59:00` and `13:00:00`–`16:59:00`.
- An empty value is written with `xsi:nil="true"`.

## Project

| Field | Use |
|---|---|
| `Id`, `Name` | identify the project |
| `DataDate` | the forward pass starts here (`PlannedStartDate` when it is empty) |
| `MustFinishByDate` | the backward pass starts here; when empty, from the latest early finish |
| `ActivityDefaultCalendarObjectId` | the calendar for lags when lags use the project default calendar |

## ScheduleOptions (inside Project)

| Field | Values the script handles |
|---|---|
| `ComputeTotalFloatType` | `Finish Float = Late Finish - Early Finish` (assumed when missing), `Start Float = Late Start - Early Start`, `Smallest of Start Float and Finish Float` |
| `RelationshipLagCalendar` | `Predecessor Activity Calendar` (assumed when missing), `Successor Activity Calendar`, `24 Hour Calendar`, `Project Default Calendar` |
| `MakeOpenEndedActivitiesCritical` | `1` sets late finish to early finish for activities without successors |
| `UseExpectedFinishDates` | `1` with expected finish dates present stops the script |
| `LevelResourcesDuringScheduling` | `1` adds a warning, because leveled dates will not match CPM dates |

## Activity

| Field | Use |
|---|---|
| `ObjectId`, `Id`, `Name`, `WBSObjectId` | identity |
| `Type` | `Task Dependent`, `Resource Dependent`, `Start Milestone`, `Finish Milestone` are scheduled; `Level of Effort` and `WBS Summary` are left out, and stop the script if they carry logic |
| `Status` | `Not Started` is scheduled, `Completed` is left out, `In Progress` stops the script |
| `CalendarObjectId` | the activity's calendar |
| `RemainingDuration` | hours |
| `PrimaryConstraintType` / `PrimaryConstraintDate`, and the `Secondary` pair | `Start On`, `Start On or After`, `Start On or Before`, `Finish On`, `Finish On or After`, `Finish On or Before`; any other type stops the script |
| `RemainingEarlyStartDate`, `RemainingEarlyFinishDate`, `RemainingLateStartDate`, `RemainingLateFinishDate` | P6's calculated dates, used only for the check |

## Relationship

| Field | Use |
|---|---|
| `PredecessorActivityObjectId`, `SuccessorActivityObjectId` | the two activities |
| `Type` | `Finish to Start`, `Start to Start`, `Finish to Finish`, `Start to Finish` |
| `Lag` | hours, negative for a lead |

## Calendar

| Field | Use |
|---|---|
| `ObjectId`, `Name`, `Type` | `Type` is `Global`, `Project` or `Resource` |
| `BaseCalendarObjectId` | a calendar whose holidays and exceptions this one inherits. The script merges them, and this calendar's own entry wins on the same date. `--base-exceptions ignore` turns the merge off |
| `HoursPerDay` | converts hours to days |
| `StandardWorkWeek` / `StandardWorkHours` | one entry per `DayOfWeek`, holding `WorkTime` start and finish pairs; a nil `WorkTime` means no work that day |
| `HolidayOrExceptions` / `HolidayOrException` | a `Date` plus `WorkTime`: nil means a nonwork day, and start and finish pairs give that day's working hours |

## Writing a file

Give every element a unique `ObjectId` and point each reference at one. P6 can require more fields on import than the script reads, so import a hand-written file into P6 once before relying on it as a transfer.
