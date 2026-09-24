# 2026/27 rollout and course operation

## Scope

One active edition is supported. This change does not delete historical records,
restore backups, deploy code, change production configuration, or publish GitHub
materials. Preserve the existing edition dump and uploaded files before the normal
annual reset. A database dump alone does not contain uploaded files.

The local instructor and student repositories are `../batch-instructors` and
`../batch-students`. Their READMEs now contain the supplied 2026/27 dates. The
workspace is a separate private repository created by each student, not another
central LDSA repository. Its exact name is `STUDENT_REPO_NAME` in the deployed
portal environment; the profile page now displays it. Do not change that name
without coordinating the student guides and grader configuration.

## Apply the calendar after preparing the edition

Use the migrations and scheduler deployment procedure in [admissions-modes.md](admissions-modes.md).
Retain or import specialization/unit/hackathon metadata before configuring dates.
The `create-spec` and `create-unit` commands exist for metadata creation. Every unit
needs its assigned instructor, specialization, matching published notebooks and
real checksum. **Do not use an invented checksum as evidence that grading is ready.**
All SLU01–19 plus SLU32/64 must belong to S01, and BLU01–15 to S02–06 in groups of three.

Hackathon 2 is confirmed for **20 December 2026**. Both new signups and
registration completion close at the end of **15 October**, leaving 16 October
for the final scholarship interviews. Payments remain open through 17 October.

Preview first, then apply the reviewed calendar:

```sh
python manage.py configure_edition
python manage.py configure_edition --apply
```

This sets the no-exam default, scheduled registration/payment gates, academy
access date, all six specialization dates and all six hackathon dates. It resets
hackathons to `closed` only when there are no grades, hackathon submissions,
teams or attendance records. It never removes records. Existing accounts keep
their admissions mode; prepare the edition before accepting applicants. Preview
is read-only; `--apply` is an explicit operational action, not part of deployment.

The prepared calendar interprets date ranges as whole Lisbon calendar days:

| Activity | Opens, Europe/Lisbon | Closes, exclusive, Europe/Lisbon | Manual permission |
| --- | --- | --- | --- |
| New no-exam accounts | 24 Sep 2026 00:00 | 16 Oct 2026 00:00 | `ACCOUNT_ALLOW_REGISTRATION` and `NO_EXAM_REGISTRATION_OPEN` |
| Existing applicants' registration steps | 24 Sep 2026 00:00 | 16 Oct 2026 00:00 | `NO_EXAM_REGISTRATION_OPEN` |
| Payment documents | 12 Oct 2026 00:00 | 18 Oct 2026 00:00 | `ADMISSIONS_ACCEPTING_PAYMENT_PROFS` |
| Paid students' course access | 18 Oct 2026 00:00 | No scheduled end | `NO_EXAM_ACADEMY_ACCESS_OPEN` |

Dates are interpreted as complete Lisbon calendar days. No production dates
have been applied. Closing at 00:00 the next day includes the entire final day,
without a gap for fractional seconds. These September/October instants are one
hour ahead of UTC. On 25 October Lisbon changes to UTC; on 28 March 2027 it changes
back to UTC+1. Conversion uses `Europe/Lisbon`, never a fixed UTC offset.

| Specialization | Submission release date | Certificate deadline (end of Lisbon day) | Hackathon |
| --- | --- | --- | --- |
| S01 | 25 Oct 2026 | 21 Nov 2026 | 22 Nov 2026 |
| S02 | 23 Nov 2026 | 19 Dec 2026 | 20 Dec 2026 |
| S03 | 5 Jan 2027 | 31 Jan 2027 | 1 Feb 2027 |
| S04 | 2 Feb 2027 | 28 Feb 2027 | 1 Mar 2027 |
| S05 | 2 Mar 2027 | 27 Mar 2027 | 28 Mar 2027 |
| S06 | 29 Mar 2027 | 24 Apr 2027 | 25 Apr 2027 |

Release dates above govern the portal's submission button; GitHub publication is
separate. Instructors can edit each unit's **available on**, **due date**, **open**
and **required for certificate** fields in Academy → Units. `open=False` overrides
the release date. Late submissions remain possible while a unit is open. They
are marked late and do not automatically count toward certification.

Introductory session/setup week, bootcamp classes, scholarship interviews and
capstone milestones are staff-operated events. The command does not schedule
meetings, send Slack invitations, publish notebooks, or configure detailed
capstone report/API deadlines. The supplied capstone range is documented as
3 May–28 June 2027; its detailed milestones require the usual capstone setup.

## Progression and certification

* SLU01–17 are mandatory S01 units, including SLU01–03. SLU18, SLU19, SLU32 and
  SLU64 are optional. A passing exercise score is at least 16/20 with status `graded`.
* In no-exam mode, passing every mandatory S01 unit by its deadline is required
  for Hackathon 1 and later activities. Failing this requirement leaves S01
  results and support accessible, but later units, hackathons and capstone are
  blocked. Timely submissions still being graded must finish before access opens.
* Once Hackathon 1 is marked complete, missing its attendance also blocks further
  progression. Correcting an erroneous attendance record restores eligibility.
* Later mandatory unit deadlines and Hackathon 6 affect certification. Missing
  them does not by itself stop continued study. The existing allowance of at most
  one missed non-mandatory hackathon is preserved.
* Certificate eligibility ignores future hackathons and not-yet-due units. Timely
  grading in progress is provisionally pending, not a failure. Eligibility is
  recalculated on course-list access, grading results, overrides and hourly by
  the scheduler. This flag is **eligibility**, not automatic certificate issuance
  or a replacement for final capstone assessment.
* Exam admission tests, selection/draw and staff finalization remain distinct
  from no-exam enrollment. Exam hackathon eligibility is calculated for that
  hackathon's specialization rather than the specialization of the last callback.

## Superuser deadline exceptions

Open **Django admin → Academy → Grades**, find the submission and edit:

1. **Deadline valid override**: Yes accepts a late submission for deadline purposes;
   No invalidates its deadline qualification; Unknown returns to the recorded
   automatic result.
2. **Deadline override reason**: explain the incident. A blank or whitespace-only
   reason prevents saving an override change, including resetting to automatic.
3. Save. The original **created** timestamp and **on time** value are read-only and
   unchanged. The actor and decision time are recorded. Every change has an
   append-only admin history entry under **Grade deadline decisions**.

Only active superusers can make these decisions. Ordinary staff cannot edit the
fields; grader callbacks cannot overwrite them. A deadline exception does not
turn a failed grading run or a score below 16 into a pass. A valid passing
exception counts in the course dashboard, specialization completion,
certification and S01 progression. Reversing it recomputes those results.

Existing grades keep their recorded `on_time` values during migration. If someone
edited that flag before this change, the new migration cannot reconstruct the
original value or invent a historical justification.

## Enrollment operation

Applicants confirm the link in their email, complete their profile and steps 1–3,
then receive normal payment instructions or enter scholarship review. No-exam
normal applicants need no exam approval or draw. Scholarship refusal ends
admission; it never converts to a normal ticket. Scholarship interviews remain
staff-operated, scheduled for 12–16 October.

Payment instructions may be issued before 12 October; document submission opens
on 12 October. Staff can verify already-submitted payments after 17 October.
No automatic rejection deletes applications at the cutoff. New documents are
blocked by the calendar; a justified operational extension requires changing the
calendar in Constance. Granting additional-proof requests after the cutoff does
not silently extend the document window. Staff should resolve those requests
before closure or deliberately extend it.

Accepted no-exam payments activate student accounts. The academy switch and date
still gate course access. Students then fill in GitHub username and Slack ID,
create their private workspace, add their portal public deploy key and push
notebooks before grading. Instructor accounts are provisioned by a superuser in
Django admin; the public instructor signup shortcut is closed.

## Hackathon 1 operation

After checking S01 results and exceptions, use the instructor hackathon admin:
`closed → marking_presences → generating_teams → ready → submissions_open →
submissions_closed → complete`. Mark actual attendance, generate teams, verify
scoring script/data, then open submissions. Date alone does not operate these
states. Attendance initialization is automatic when marking presences opens.
Small cohorts are supported; invalid sizes or insufficient capacity report an
error. Team regeneration is blocked once submissions exist. A student without a
team cannot bypass the team submission limit with an individual submission.
Individual practice after completion remains supported.

## Deferred operational verification

Live grader images, Kubernetes callbacks and GitHub publication were not executed,
as requested. The instructor repo's release workflow builds graders and updates
checksums; its sync workflow publishes selected folders to the student repo.
`repo-sync/config.yml` currently targets S06, so publication of S01 must explicitly
include SLU01–03 as course units as well as the remaining S01 material. Do not
publish instructor solutions or hidden material accidentally. The configuration
was not changed to trigger a release.

Production still requires the updated image, migrations, scheduler, prepared
edition metadata/calendar and final end-to-end verification. No production
readiness claim follows solely from local regression tests.

## Verification record

The completed local implementation passed **111 tests** against an isolated
PostgreSQL 18 database. This includes exam/no-exam admission flows, concurrent
enrollment/payment operations, migrations, calendar boundaries, Lisbon DST,
optional units, S01/Hackathon 1 progression, deadline overrides and hackathon
operation. Django system checks pass and `makemigrations --check --dry-run`
reports no missing migrations. Whitespace checks pass in all three edited
repositories. These checks did not send production emails or run live graders.

Final confirmed dates: both signup and registration completion end on
15 October 2026; scholarship interviews may continue on 16 October; payment
ends on 17 October; Hackathon 2 is 20 December 2026. The calendar command uses
exclusive midnight cutoffs immediately after those final days.
