# Complete source file register

The pinned source Git tree contains 39 blobs: 32 text files and seven PNG files.
The links below identify immutable original files, not copied product content.
The [parity inventory](parity.md) assigns requirements, tasks, tests, and target dispositions to their relevant behavior.
Context-only files do not invent a new runtime feature.
All text ranges cover the complete file. PNG links provide asset provenance rather than line evidence.

| Source file and complete immutable evidence | Role and inventory coverage |
| --- | --- |
| [.dockerignore L1-L15](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/.dockerignore#L1-L15) | Build exclusions. P064/P067 uses target build rules. |
| [.env.example L1-L39](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/.env.example#L1-L39) | Config names and source setup. P065/P066 forbids a second credential setup. |
| [.github/codeql/codeql-config.yml L1](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/.github/codeql/codeql-config.yml#L1) | Static-analysis context. P067 retains target workflow authority. |
| [.github/copilot-instructions.md L1-L99](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/.github/copilot-instructions.md#L1-L99) | Source-specific contributor context. P069/P072 uses current target rules. |
| [.github/dependabot.yml L1-L19](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/.github/dependabot.yml#L1-L19) | Dependency update configuration. P065/P067 retains target streams. |
| [.github/workflows/build-and-push.yml L1-L28](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/.github/workflows/build-and-push.yml#L1-L28) | Standalone image publication. P064/P067 does not copy it. |
| [.github/workflows/codeql.yml L1-L38](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/.github/workflows/codeql.yml#L1-L38) | Source security workflow. P067 keeps target checks. |
| [.github/workflows/quality-gates.yml L1-L74](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/.github/workflows/quality-gates.yml#L1-L74) | Source test/build gates. P067/P069 requires target acceptance. |
| [.github/workflows/release.yml L1-L88](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/.github/workflows/release.yml#L1-L88) | Source release ownership. P067 uses the target release. |
| [.github/workflows/ste-lint.yml L1-L47](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/.github/workflows/ste-lint.yml#L1-L47) | Source prose gate. P067/P072 uses target tooling. |
| [.github/workflows/stranded-branch-report.yml L1-L49](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/.github/workflows/stranded-branch-report.yml#L1-L49) | Source branch report. P067 retains target ownership. |
| [.gitignore L1-L87](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/.gitignore#L1-L87) | Output/secret exclusion context. P061/P066 uses target paths and exclusions. |
| [.ste-linter.toml L1-L40](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/.ste-linter.toml#L1-L40) | Source prose configuration. P069/P072 does not replace target settings. |
| [AGENTS.md L1-L353](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/AGENTS.md#L1-L353) | Contributor standards context. Current target constitution controls this plan. |
| [Dockerfile L1-L63](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/Dockerfile#L1-L63) | Source image, labels, health, user, dependencies. P064/P065/P066/P070. |
| [LICENSE L1-L39](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/LICENSE#L1-L39) | CC BY-NC-SA-4.0 and credit. P070 preserves applicable terms. |
| [README.md L1-L77](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/README.md#L1-L77) | Feature, setup, screenshots, and license claims. P068/P070/P072. |
| [app.py L1-L436](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/app.py#L1-L436) | Entire Flask application and 13 routes. P001/P025/P038/P040/P044/P049/P061/P062/P066/P071. |
| [docker-compose.dev.yml L1-L17](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docker-compose.dev.yml#L1-L17) | One development application, no database/Redis. P062/P064. |
| [docker-compose.yml L1-L27](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docker-compose.yml#L1-L27) | One production application, port 5000 and mounts. P062/P064/P066. |
| [docs/capture_screenshots.py L1-L177](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docs/capture_screenshots.py#L1-L177) | Synthetic screenshot procedure. P068 distinguishes source evidence from parity. |
| [docs/development.md L1-L27](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docs/development.md#L1-L27) | Source development/test instructions. P069/P072 uses target commands. |
| [docs/guide.md L1-L276](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docs/guide.md#L1-L276) | Workflow/endpoint/setup/troubleshooting claims. P028/P037/P072 identifies API conflicts. |
| [docs/screenshots/01-main-dashboard.png](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docs/screenshots/01-main-dashboard.png) | Existing dashboard reference. P001-P020/P068. |
| [docs/screenshots/02-edit-guest.png](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docs/screenshots/02-edit-guest.png) | Existing edit reference. P033-P037/P068. |
| [docs/screenshots/03-add-guest-blank.png](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docs/screenshots/03-add-guest-blank.png) | Existing add reference. P021-P032/P068. |
| [docs/screenshots/04-add-guest-filled.png](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docs/screenshots/04-add-guest-filled.png) | Existing filled-add reference. P021-P032/P068. |
| [docs/screenshots/05-guest-added.png](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docs/screenshots/05-guest-added.png) | Existing list reference. P010-P014/P068, not live-write proof. |
| [docs/screenshots/06-bulk-import.png](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docs/screenshots/06-bulk-import.png) | Existing import reference. P039-P050/P068. |
| [docs/screenshots/07-csv-example.png](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docs/screenshots/07-csv-example.png) | Existing example reference. P040/P068. |
| [docs/screenshots/README.md L1-L38](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docs/screenshots/README.md#L1-L38) | Fictional-fixture screenshot provenance. P068/P072. |
| [mist_connection.py L1-L845](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/mist_connection.py#L1-L845) | Entire SDK/discovery/guest/client implementation. P003/P007/P008/P022/P025/P029/P037/P038/P052/P055-P062. |
| [requirements-dev.txt L1-L16](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/requirements-dev.txt#L1-L16) | Development dependencies. P065/P069 reconciles existing tooling. |
| [requirements.txt L1-L4](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/requirements.txt#L1-L4) | Runtime pins including SDK 0.64.0. P065 forbids a target downgrade. |
| [ruff.toml L1-L7](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/ruff.toml#L1-L7) | Source lint rules. P069 uses target gates. |
| [templates/index.html L1-L1796](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/templates/index.html#L1-L1796) | Entire CSS/HTML/JavaScript. P001-P054/P059/P060/P065/P071 covers controls and state. |
| [tests/test_application.py L1-L407](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/tests/test_application.py#L1-L407) | Flask and SDK offline tests. P022/P069. |
| [tests/test_complexity_regressions.py L1-L297](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/tests/test_complexity_regressions.py#L1-L297) | Helper and complexity behavior. P043/P052/P053/P069. |
| [tests/test_documentation.py L1-L52](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/tests/test_documentation.py#L1-L52) | Documentation consistency. P069/P072. |

No source file is copied or installed into the product by this plan.
An immutable link confirms a file and its declared range. It does not prove the file's claims are safe or current cloud contracts.
