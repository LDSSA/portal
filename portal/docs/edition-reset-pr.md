# Add admin-managed edition resets and database snapshots

The portal previously had no coordinated new-edition reset, and deleting an instructor
could cascade into their units. This change adds a superuser-operated, previewed reset
that preserves curriculum and selected organizers while clearing prior-edition activity.
It also provides independent database snapshots and controlled deletion of saved dumps.

## Changelog

### Admin controls

- Add **Edition management → Edition resets** with permanent operation history and a
  dedicated preparation/control page, restricted server-side to active staff superusers.
- Display environment, database identity, deployed release, maintenance state and the
  exact temporary server backup path. Detect database settings automatically.
- Add an expandable **ⓘ** information panel containing the complete model policy below,
  session behavior, rollback/recovery information and backup/storage limitations.
- Add maintenance entry, organizer selection, a final preview with per-model delete/retain
  counts, explicit account-deletion review, and CSRF-protected reset confirmation.
- Preselect existing organizers for retention; always retain the initiating administrator
  and configured service accounts. Review non-student registrations explicitly before
  confirming. No independent per-model deletion toggles are provided.
- Add background operation status/result pages. A queued operation continues without the
  browser. Repeated confirmation of the same operation does not rerun a completed reset.
- Leave the portal prepared and publicly closed after success, with a separate confirmed
  **Open prepared edition** action and basic curriculum/calendar readiness checks.

### Reset execution and account relationships

- Add the `edition_management` app, explicit model policy, preview fingerprinting,
  transactional executor, persistent database gate, operation reports and grading-job registry.
- Clear all historical activity in both admission modes, including exam submissions,
  application/selection state, enrollment emails, simulator schedules and **all
  `capstone.Datapoint` and `capstone.DueDatapoint` records**.
- Preserve every existing specialization, unit, hackathon definition, capstone definition
  and admission challenge. Clear all unit instructor assignments and close course submission
  switches. Preserve dates, checksums and other reusable curriculum metadata.
- Delete non-retained users together with their database tokens and account credentials.
  Token ownership alone does not protect an otherwise deselected account.
- Preserve retained credentials unchanged. Clear retained organizers' historical student
  role, registration completion, conduct acceptance, scholarship/preference/ticket fields
  and progression flags; preserve their organizer roles and identity fields. Configured
  service accounts are excluded from participant-role normalization.
- Clear sessions, whitelist entries and email confirmations; retain surviving admin history.
- Assert empty activity tables, exact retained-user identities, unchanged retained tokens,
  preserved curriculum identities and unchanged fields outside the explicit reset policy
  before committing. Commit the successful report with the reset transaction.
- Change `Unit.instructor` to nullable/blank `SET_NULL`; existing instructor assignments
  survive deployment. Handle unassigned instructors in unit creation and templates.
- Add reverse generic relations on users and hackathon teams, so deleting either through
  Django also deletes their linked hackathon submissions. Reset explicitly clears even
  pre-existing orphaned generic submissions.

### Snapshots

- Add **Save snapshot**, independent of reset, and **Back up before reset**, checked by
  default. A backup failure prevents a backup-enabled reset from deleting records.
- Generate PostgreSQL custom-format dumps using the connected environment's settings,
  UTC timestamp/UUID filenames, private file permissions and a database-scoped temporary
  directory under `/tmp/ldsa-portal-backups/`.
- Validate each archive with `pg_restore --list`; record SHA-256, size and filename;
  clean failed partial files. Do not expose database passwords in command arguments or reports.
- Add authenticated **Download dump to this computer** links. Remote storage paths are
  clearly distinguished from browser downloads.
- Add **Delete saved dumps…**, requiring a centered confirmation dialog and server-side
  confirmation. Delete generated dump/partial files only; skip unrelated files and symlinks.
  Preserve operation history and mark removed downloads unavailable.

### Maintenance and background work

- Add PostgreSQL shared/exclusive advisory locking around portal HTTP requests, scheduler
  activity, enrollment-email delivery, simulator outbound requests/results, grading launches
  and mutating portal management commands.
- Track external graders and discover existing legacy grading containers; block reset
  while grading is pending, running or cannot be verified complete.
- Add a dedicated worker with release heartbeat and single-worker locking. Reject stale
  previews, incompatible releases and concurrent queued/running operations.
- Preserve the paused state after reset failure. On worker restart, mark interrupted runs
  failed without replaying already committed successful operations.
- Continue to exclude uploaded files, S3 objects, GitHub resources and external secrets from
  reset and purge. No reset-triggered email or grading launch is introduced.

### Configuration and deployment

- Preserve the current admission mode and calendar rather than guessing future dates.
  Close registration, payment and course-access switches. Mode/calendar review remains in
  existing configuration screens, separate from destructive reset.
- Extract the existing Batch 10 no-exam calendar command into a shared service, retain its
  command interface, and prevent it reopening public access while the edition is prepared.
- Add `academy/0016_alter_unit_instructor` and `edition_management/0001_initial` migrations.
  Neither migration clears existing edition data.
- Add `migrate-portal`, `check-edition-readiness` and `run-edition-resets` management commands.
- Serialize deployments by branch; run one release-specific Kubernetes migration Job
  before updating web/workers; require migration success and completed deployment before
  enabling that release's reset controls.
- Keep the legacy optional Redis StatefulSets outside the deployment readiness gate. Helm
  applies the chart without waiting for Redis, while the workflow explicitly waits for the
  migration Job and the `ldsa-portal` Django deployment. Redis itself is not reconfigured.
- Change production web startup to verify migrations instead of applying them; add startup
  migration checks for scheduler/simulator and the new edition worker.
- Add the worker sidecar and shared temporary backup volume. Enforce one application pod
  and use `Recreate` deployment strategy to keep downloads and worker ownership consistent.
- Apply the same code independently to development and production. Deploying/merging does
  not reset either database or copy data between them; each reset requires its own admin action.

## Complete reset policy

| Model | Reset behavior | Details |
| --- | --- | --- |
| `academy.Grade` | Clear all | Remove previous-edition activity in both admission modes. |
| `academy.GradeDeadlineDecision` | Clear all | Remove previous-edition activity in both admission modes. |
| `academy.Specialization` | Keep all | Preserve reusable configuration. |
| `academy.Unit` | Keep all; configure | Keep every unit, clear instructor, close submissions; preserve dates, checksum and curriculum metadata. |
| `account.EmailAddress` | Selective / configure | Keep records associated with retained accounts. |
| `account.EmailConfirmation` | Clear all | Remove previous-edition activity in both admission modes. |
| `admin.LogEntry` | Selective / configure | Keep surviving audit entries; entries owned by deleted users cascade away. |
| `applications.Application` | Clear all | Remove previous-edition activity in both admission modes. |
| `applications.Challenge` | Keep all | Keep reusable exam definitions; old exam attempts are always deleted. |
| `applications.Submission` | Clear all | Remove previous-edition activity in both admission modes. |
| `auth.Group` | Keep all | Preserve reusable configuration. |
| `auth.Permission` | Keep all | Preserve reusable configuration. |
| `authtoken.Token` | Selective / configure | Keep retained users' tokens unchanged. Delete tokens belonging to deleted users. |
| `capstone.Capstone` | Keep all; configure | Keep definitions and scoring references; close all three report submission switches. |
| `capstone.Datapoint` | Clear all | Delete all source points associated with historical simulator runs, even when populated. |
| `capstone.DueDatapoint` | Clear all | Delete all scheduled points, requests and results, even when populated. |
| `capstone.Report` | Clear all | Remove previous-edition activity in both admission modes. |
| `capstone.Simulator` | Clear all | Remove previous-edition activity in both admission modes. |
| `capstone.StudentApi` | Clear all | Remove previous-edition activity in both admission modes. |
| `constance.Constance` | Selective / configure | Keep dates, mode and unrelated configuration; disable public registration, payments and course access. |
| `contenttypes.ContentType` | Keep all | Preserve reusable configuration. |
| `hackathons.Attendance` | Clear all | Remove previous-edition activity in both admission modes. |
| `hackathons.Hackathon` | Keep all; configure | Keep definitions and files; set status to closed. Preserve dates and scoring settings. |
| `hackathons.Submission` | Clear all | Remove previous-edition activity in both admission modes. |
| `hackathons.Team` | Clear all | Remove previous-edition activity in both admission modes. |
| `selection.EnrollmentEmail` | Clear all | Remove previous-edition activity in both admission modes. |
| `selection.Selection` | Clear all | Remove previous-edition activity in both admission modes. |
| `selection.SelectionDocument` | Clear all | Remove previous-edition activity in both admission modes. |
| `selection.SelectionLogs` | Clear all | Remove previous-edition activity in both admission modes. |
| `sessions.Session` | Clear all | Remove previous-edition activity in both admission modes. |
| `sites.Site` | Keep all | Preserve reusable configuration. |
| `socialaccount.SocialAccount` | Selective / configure | Keep records associated with retained accounts. |
| `socialaccount.SocialApp` | Keep all | Preserve reusable configuration. |
| `socialaccount.SocialToken` | Selective / configure | Keep records associated with retained accounts. |
| `users.User` | Selective / configure | Keep the operator, configured service accounts and selected organizers; delete all other users and their database credentials. |
| `users.UserWhitelist` | Clear all | Remove previous-edition activity in both admission modes. |
| `authtoken.TokenProxy` | No separate operation | Proxy of Token; not another table. |
| `django_migrations` | Keep all | Migration history is never reset. |
| `edition_management.*` | Keep | Operational gate, reset/backup history and job tracking survive. |

## Operational notes

- Snapshots are temporary pod files: download required backups before pod replacement or
  dump cleanup. The database archive excludes uploaded files. Archive validation is not an
  environment-specific restore drill.
- The administrator still chooses retained organizers and confirms deletion of listed
  accounts. The system cannot infer which organizers left or whether a registration is a test.
- The reset detects existing settings, preserves dates/mode, and uses a UUID and reset
  generation; it does not ask for arbitrary database IDs, paths, credentials or a future calendar.
- Reset completion and opening the next edition are separate. Review calendar, materials
  and integrations before opening. Reverting code does not restore deleted data.
- All separately operated writers must run the updated code. Direct shell/SQL writes and
  legacy external processes must be stopped during reset.
- This implementation targets PostgreSQL and a single application pod. Recreate deployments
  cause a brief service interruption. PostgreSQL dump-client/server compatibility is checked
  by the backup operation failing safely if incompatible.

See [Edition reset operations](edition-reset.md) for the workflow, commands, migrations,
snapshot handling and recovery procedure.

## Validation

Validation uses disposable local PostgreSQL databases, without touching development or
production data. It covers both admission modes, populated simulator point tables,
nullable instructor behavior and generic cascades, retained credentials and mixed roles,
stale previews, duplicate confirmation, transaction rollback, failed backups, superuser/CSRF
checks, grading discovery, separate-connection advisory locking, worker interruption,
legacy schema migration preservation, and a real snapshot download and isolated restore.

- **149 tests passed**, including 23 edition-management tests and a real PostgreSQL dump/restore.
- Django system checks: no issues. `makemigrations --check --dry-run`: no missing migrations.
- Ruff lint and formatting checks passed for changed Python files; `git diff --check` passed.
- Helm lint passed with deployment values; both development and production charts rendered
  and parsed, including the migration Job and three application containers.
- Deployment workflow YAML and embedded shell syntax were checked.
- CI explicitly installs PostgreSQL client tools for snapshot tests; test settings mock
  both course and admissions graders so tests do not require live grading infrastructure.
- Existing Django/Jupyter deprecation warnings remain. No cluster deployment, live database
  reset or production restoration was performed.
