# PostgreSQL schema

The backend creates these tables when it starts. IDs are application-generated
strings; do not rely on PostgreSQL sequences.

| Table | Required columns when inserting directly | Other stored values |
| --- | --- | --- |
| `users` | `id`, `email` | `created_at` |
| `workspaces` | `id`, `name` | `owner_id` (FK `users`), `created_at` |
| `projects` | `id`, `name` | `workspace_id` (FK `workspaces`), `created_at` |
| `courses` | `id`, `title` | `source_url`, `project_id` (FK `projects`), `raw_content` JSON, `metadata` JSON, `status`, timestamps |
| `modules` | `id`, `course_id`, `module_number`, `title` | `summary`, `content` JSON, `raw_html`, `cleaned_content` JSON, `source_url`, `status`, timestamps |
| `jobs` | `id`, `status` | `course_id`, `module_id`, pipeline progress fields, errors, `config` JSON, `checkpoint` JSON, timestamps |
| `presentations` | `id`, `title` | course/module IDs, `version`, document and blueprint JSON, QA score, output path, status, timestamps |
| `presentation_versions` | `id`, `presentation_id`, `version` | `document_json`, `created_at` |
| `slides` | `id`, `presentation_id`, `slide_number` | purpose, message, layout, component JSON, `created_at` |
| `assets` | `id` | presentation/module IDs, type, path, MIME type, metadata JSON, `created_at` |
| `qa_results` | `id`, `presentation_id`, `overall_score` | job ID, category scores, checks JSON, issues JSON, passed, `created_at` |

## Values used by the backend

`jobs.status` is a PostgreSQL enum. Valid values are: `PENDING`, `EXTRACTING`,
`ANALYZING`, `DESIGNING`, `PLANNING`, `GENERATING_ASSETS`, `RENDERING`,
`VALIDATING`, `QA`, `COMPLETED`, `FAILED`, and `RETRYING`.

The current pipeline writes these common string statuses:

- Course: `CREATED`, then `EXTRACTED`.
- Module: `PENDING` or `EXTRACTED`.
- Presentation: `DRAFT`, `RENDERING`, `PUBLISHED`, or `QA_WARNING`.

The API creates course IDs, job IDs, modules, presentations, slides, and QA
records itself. For ordinary usage, call `POST /api/v1/courses` and then
`POST /api/v1/jobs`; direct inserts are not necessary.

## Data integrity

The schema prevents duplicate module numbers per course, duplicate slide
numbers per presentation, and duplicate presentation-version numbers. It also
creates indexes for the API's course, module, presentation, job, asset, and QA
lookups.
