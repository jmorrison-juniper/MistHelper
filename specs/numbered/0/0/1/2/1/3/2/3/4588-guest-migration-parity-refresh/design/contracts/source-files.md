# Source file register

The pinned source Git tree at `0213240c` holds 39 blobs. Of these, 32 are text files and 7 are PNG files. The tree also holds 7 directory entries. Each row gives the blob SHA from the GitHub tree listing (R68), the byte size, the role, and the inventory IDs. Links use the base in [research section 4](../research.md#4-source-evidence-mistguestauthorizations-at-0213240c).

No source file is copied or installed by this plan. An immutable link confirms that a file and its declared range exist. It does not prove that the file's claims are safe or current.

| # | Source path | Blob SHA | Bytes | Role | Inventory IDs |
| --- | --- | --- | --- | --- | --- |
| 1 | `.dockerignore` | 655fb7172aa0f344a45959ed5dff293ba6b10222 | 130 | Build exclusions | P064, P067 |
| 2 | `.env.example` | b5f5ba2e21ba59c45f6a0e5818fd45c8e66227c8 | 1296 | Configuration names. Values are not copied. | P065, P066 |
| 3 | `.github/codeql/codeql-config.yml` | f27b3504b2dea94ffd0a72c16de57bed57c2355b | 53 | Static analysis configuration | P067 |
| 4 | `.github/copilot-instructions.md` | 18d28bb66c96e4663d64368c3305e760e7c46fa8 | 6102 | Source contributor context | P069, P072 |
| 5 | `.github/dependabot.yml` | 6c046d185b38ad40d8fe032b88675d1c22d4a10c | 422 | Dependency update configuration | P065, P067 |
| 6 | `.github/workflows/build-and-push.yml` | bef39442109f5f3be3389408763c9a64b2e816af | 756 | Image publication | P064, P067 |
| 7 | `.github/workflows/codeql.yml` | b72a3b28735785bf0b2799d36345d9333d1b6ebd | 1265 | Security analysis workflow | P067 |
| 8 | `.github/workflows/quality-gates.yml` | f80fbd4192fa71e275a8fec871503e801997f9ec | 2329 | Test and build gates | P067, P069 |
| 9 | `.github/workflows/release.yml` | dc0b1805c8d701ad07e34c301d081f3e77b69d42 | 2587 | Release workflow | P067 |
| 10 | `.github/workflows/ste-lint.yml` | 73d067bb43c10fed599447ce812035b3a28fd1b1 | 2101 | Prose gate | P067, P072 |
| 11 | `.github/workflows/stranded-branch-report.yml` | eb9ff950a174efeb707c59883d6ba2f7b0462c84 | 1861 | Branch report | P067 |
| 12 | `.gitignore` | ca5613621fd0ba13a5580b17950f2bbbd761ce0c | 767 | Output and secret exclusions | P061, P066 |
| 13 | `.ste-linter.toml` | 926f8663a22b660d3501e26be3eaf94c281b35cc | 2433 | Prose configuration | P069, P072 |
| 14 | `AGENTS.md` | 44a9afffb5bd6f774973a845d27343e4e528b6ad | 18482 | Generic standards. This blob equals the target `AGENTS.md` blob (R32). | Context only |
| 15 | `Dockerfile` | 439d32810479f4eca790622a4a3777ebab02a51d | 2153 | Image, labels, health check, user, and dependencies | P064, P065, P066, P070 |
| 16 | `LICENSE` | bbea5fed78ca98720c6590d4151de423714ea6de | 1663 | CC BY-NC-SA 4.0 license | P070 |
| 17 | `README.md` | f92e7f65b8215d30cade46c58046ff0367514b9d | 2858 | Feature statement, screenshots, and license link | P068, P070, P072 |
| 18 | `app.py` | 270eb700e43fed1fae6ccdf8a28e7f57c9d316f8 | 14997 | Flask application and 13 routes | P001, P025, P038, P040, P044, P049, P061, P062, P066, P071 |
| 19 | `docker-compose.dev.yml` | 229d1a0d30e23605b243ba839df45ca918bada3a | 439 | Development service with no database | P062, P064 |
| 20 | `docker-compose.yml` | 7a9206c460da9cda84f708c3e8f54694840aa4bb | 868 | Production service with port 5000 | P062, P064, P066 |
| 21 | `docs/capture_screenshots.py` | 02b49d7680410c6dc0106d9daf443cb9055f7703 | 6592 | Synthetic screenshot procedure | P068 |
| 22 | `docs/development.md` | 60bddb578f5340aff4db8f94e1847568d14b65f3 | 1104 | Development instructions | P069, P072 |
| 23 | `docs/guide.md` | 439dfae00662a1ba2297aa45123e14570fa66f7a | 9596 | Workflow, endpoint, and troubleshooting claims | P028, P037, P072 |
| 24 | `docs/screenshots/01-main-dashboard.png` | 4e77dcf02173bac73b9cbe473b9c989ba63dbc85 | 109491 | Dashboard reference image | P001 to P020, P068 |
| 25 | `docs/screenshots/02-edit-guest.png` | 642d3bd66bf414d028a802dda6e0a74890d41b73 | 120157 | Edit reference image | P033 to P037, P068 |
| 26 | `docs/screenshots/03-add-guest-blank.png` | 90ba1a47926d4381d5f319b728cd4bc6c9701fa2 | 113880 | Blank add reference image | P021 to P032, P068 |
| 27 | `docs/screenshots/04-add-guest-filled.png` | 573cf49e8d3c6e877e0222ea85f4562cdb26a15e | 116347 | Filled add reference image | P021 to P032, P068 |
| 28 | `docs/screenshots/05-guest-added.png` | ba212fc8696909394b2b51e62508894f6d8fbf53 | 129060 | List reference image. It is not proof of a live write. | P010 to P014, P068 |
| 29 | `docs/screenshots/06-bulk-import.png` | 58dc8c8aea3b8c8039f408b70d563d442cccfab8 | 140326 | Import reference image | P039 to P050, P068 |
| 30 | `docs/screenshots/07-csv-example.png` | 87b466ede58adf9c8a3890e68289872b635282d1 | 155928 | CSV example reference image | P040, P068 |
| 31 | `docs/screenshots/README.md` | 4b650c915c60b90f7965a13882d507214f3d8490 | 1715 | Fictional-fixture provenance | P068, P072 |
| 32 | `mist_connection.py` | 72d6226a6bfb5cf85178108b94e6bde8495b4d0f | 31909 | SDK calls, discovery, guest methods, and client search | P003, P007, P008, P022, P025, P029, P037, P038, P052 to P062 |
| 33 | `requirements-dev.txt` | 7be79ae77fb9ba9efe1dc7538b4c9162a6c32753 | 540 | Development dependencies | P065, P069 |
| 34 | `requirements.txt` | e3c62ee4fd6bd48c8cb94af0c8d6d0fdb5df01a7 | 130 | Runtime pins | P065 |
| 35 | `ruff.toml` | 9113a53f98e7965a5c5ab383ad7286bfa84d0ea5 | 248 | Lint rules | P069 |
| 36 | `templates/index.html` | ef954198c1768b4e2d57cddd3aeaf93c6caddf95 | 80427 | CSS, HTML, and JavaScript for the dashboard and dialogs | P001 to P060, P071 |
| 37 | `tests/test_application.py` | eb879e2a1f7f0923fdd749a476827f149452e6ec | 16031 | Flask and SDK offline tests | P022, P069 |
| 38 | `tests/test_complexity_regressions.py` | faef64c444f85e580788d18588f03dce7ac7ff4a | 12371 | Helper and complexity tests | P043, P052, P053, P069 |
| 39 | `tests/test_documentation.py` | f43e249ce8b336f800f69e3d50f32a51f9874769 | 2358 | Documentation consistency tests | P069, P072 |

Totals: 39 blobs. Seven blobs are PNG files (rows 24 to 30). The remaining 32 blobs are text files.
