# Edition reset operations

The admin entry is **Edition management → Edition resets → Prepare new edition**.
Only active staff superusers can access the controls, reports or snapshot downloads.
The feature operates exclusively on the database connected to that environment.
Development and production retain independent contents, account choices and reset history.

## Deployment and migrations

The deployment workflow builds the release image, publishes the environment's configuration,
runs a release-specific Kubernetes migration Job, waits for success, replaces the application
and workers, and marks that release ready. Deployment never queues a reset.

The Helm release intentionally does not wait for every chart dependency. In particular, the
legacy optional Redis StatefulSets have historically remained unavailable and do not gate a
portal release. Deployment readiness is instead based on successful database migration and
the explicit `ldsa-portal` Django deployment rollout. This change does not repair or otherwise
reconfigure Redis.

The migrations are:

- `academy/0016_alter_unit_instructor`: allows blank/NULL instructor values and uses Django
  `SET_NULL` on account deletion. Existing assignments and grades survive migration.
- `edition_management/0001_initial`: creates the operational gate, operation history and
  external-grading-job tracking tables. It does not delete edition data.

Existing pending migrations are applied in dependency order by `migrate-portal`.
Web, scheduler and simulator startup check that migrations are complete. The new
`run-edition-resets` worker processes only explicitly queued operations.
The admin refuses reset execution when migrations, release readiness or the matching
worker heartbeat are missing. No migration runs inside an admin request or after a reset.

The Django and edition worker containers use the mounted grader configuration through
explicit paths: `KUBECONFIG=/home/django/.kube/config`,
`AWS_CONFIG_FILE=/home/django/.aws/config` and
`AWS_SHARED_CREDENTIALS_FILE=/home/django/.aws/credentials`. This is required because the
system `django` user has `HOME=/nonexistent`; relying on home-directory discovery would make
the external-grader safety check fail before a reset can enter maintenance.

Deploy and test on development first. Merge the tested code and migration files into `main`
to deploy production. Then prepare a fresh preview and separately trigger the production
reset in production admin. No database contents or retained-user selections are transferred.

The chart currently requires one application pod. Web and worker share a temporary
`emptyDir` volume; `Recreate` prevents overlapping old/new workers with different local
backup directories. This introduces a brief deployment interruption. The pod volume's
supplementary group permits the non-root containers to write backups.

For a local installation, using that installation's own settings:

```sh
python manage.py migrate-portal
python manage.py check-edition-readiness --deployment-complete
python manage.py run-edition-resets
```

Run the worker separately from the web server. Upgrade any independently operated simulator
or scheduler processes before using reset; legacy processes and ad hoc database/shell writes
do not participate in the maintenance protocol. Do not run them during reset.

## Admin workflow

1. Check the prominently displayed environment, database, release and server backup directory.
   Expand **ⓘ What does resetting this database do?** for the complete model policy.
2. Optionally use **Save snapshot**, independently of reset. Its result page offers
   **Download dump to this computer**.
3. Choose **Enter maintenance and prepare reset**. In-flight portal work must finish first.
   Unfinished or unverifiable grading jobs block preparation, including legacy external
   graders discovered from their running containers. A busy gate asks you to retry.
4. Select organizers to retain. Existing organizers are preselected; the operator and
   configured service accounts are always retained. Ordinary student/applicant accounts are
   deleted. Deselected organizers also lose their database credentials.
5. Review the final preview: deletion/retention counts, accounts retained/deleted, and
   flagged non-student registrations. The administrator must explicitly confirm that all
   listed accounts may be removed. If a genuine incoming registration appears, cancel;
   the software cannot infer whether it is a test account.
6. Leave **Back up before reset** checked to create a fresh snapshot before any deletion.
   A missing/unusable server directory or failed dump prevents deletion. Unchecking it
   deliberately relies on your separately secured backup.
7. Confirm and execute. The worker continues if the browser closes. Changed records or
   changed deployment invalidate the preview. Duplicate submission of the same run does
   not execute it twice.
8. Sign in again after completion: all sessions were removed. Review the permanent report.
   The portal is now **prepared**, with public activity closed.
9. Configure/review the next edition's calendar, admission mode and course availability in
   their existing admin sections. Choose **Open prepared edition** only after review.
   Empty curriculum and invalid/expired admission calendars block opening.

There is no model-by-model deletion switch. Connection details, paths, release, current
admission mode and existing records are detected automatically. Each reset receives a UUID
and database-local generation. The reset does not invent the next edition's dates or change
its admission mode: it preserves existing configuration and closes public gates. There is
no automatic transfer of Batch 10 dates into later editions. Calendar review is separate
from destructive cleanup. `configure_edition` remains the explicit Batch 10 no-exam calendar
command; it uses the extracted calendar service, requires its known curriculum and keeps
public gates closed when the portal is prepared. Exam calendars remain editable in Constance.

## Snapshots and cleanup

Default server location:

```text
/tmp/ldsa-portal-backups/<database-identity-hash>/
```

The exact resolved path is shown in admin. Filenames are
`portal-<UTC creation timestamp>-<operation UUID>.dump`. The path is server-managed;
no arbitrary browser-provided path or shell command is accepted. The worker runs PostgreSQL
`pg_dump --format=custom`, validates the archive directory with `pg_restore --list`, and
records size and SHA-256. Dumps are private files (0600) inside a private database directory
(0700). Failed incomplete dumps are cleaned up. Database credentials are not command-line
arguments or report contents. The image's PostgreSQL client must support the server version;
client incompatibility fails the backup and aborts a backup-enabled reset.

The result page's authenticated download saves a copy on the administrator's computer.
A server path is not a path on that computer. Server dumps are **temporary**: replacing the
pod loses them. Download them before deployment or deletion. Dumps contain sensitive account
information and database-held credentials; store downloaded copies securely.

**Delete saved dumps…** opens a centered confirmation dialog. Confirming queues deletion
of generated dump/partial files in this database's directory only. Unrelated files,
subdirectories and symbolic links are not followed or deleted. Historical reports remain,
with their downloads marked unavailable. Purging cannot be undone.

Runtime archive validation is not a restore drill. Test recovery separately into an isolated
database. The automated tests exercise a real dump and restoration, but each environment's
backup still needs its own operational recovery validation. Database dumps exclude uploaded
files, S3 objects, repositories and external secrets.

## Concurrency, failure and recovery

A PostgreSQL shared/exclusive advisory gate spans HTTP requests and session writes,
scheduler work, email delivery, simulator network calls/results, grading launch and the
portal's mutating edition/user/capstone management commands. Maintenance prevents new work.
External graders are tracked and scanned before deletion. Monitoring failure blocks reset
rather than assuming a grader finished. Do not manually mark jobs finished without verifying
their containers have stopped; investigate stuck grade statuses before entering maintenance.

The reset runs in one database transaction after any requested backup succeeds. It empties
explicit activity querysets, clears all unit instructors, closes course definitions, deletes
unretained users, normalizes retained organizers' participant fields, and closes public
switches. It checks empty tables, retained users/tokens, curriculum identities and all
preserved curriculum/configuration values. The successful report and prepared state commit
with those changes. No sequence reset, `flush`, outgoing email or uploaded-file cleanup runs.

A failed reset rolls back business data and leaves maintenance active. Correct the cause and
prepare a new preview, or cancel preparation to resume the previous edition. On restart the
worker marks interrupted runs failed and does not replay committed successes. Inspect an
interrupted snapshot directory before purging partial files. A failed deployment migration
Job must be diagnosed and recreated before retrying the same release; never bypass migration
or release-readiness checks to run a reset.

After a successful reset, reverting code cannot recover deleted records. Restore that
environment's independently secured backup using an operator-controlled recovery procedure
with writers stopped. Review the restored maintenance state/history before starting workers.
There is deliberately no automatic restore button. Reversing the instructor migration is
unsafe while units have NULL instructors; restoration is not schema reversal.

## Complete model policy

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
