# QA Automation System — Tài liệu hệ thống

## 1. Tổng quan

Hệ thống gồm 2 component song song:

- **Component A** — QA Report Web Platform (Next.js trên Vercel): nơi lưu trữ và chia sẻ HTML report
- **Component B** — Odoo Bug Ticket System (Odoo 18 Community + custom module): nơi quản lý bug ticket tự động từ CI/CD

OCA Helpdesk 18.0 đã được vendor bước đầu trong repo để chuẩn bị tích hợp
luồng customer support. Bridge hiện tại cho phép QA tạo/link `qa.bug.ticket`
thủ công từ `helpdesk.ticket`, sau đó tạo/link `project.task` thủ công từ QA
Bug; chưa auto sync status và chưa copy attachment/evidence.

---

## 2. Workflow hệ thống

### Flow chính: CI/CD Auto Bug Ticket

```
Developer push code lên GitHub
        │
        ▼
GitHub Actions trigger
        │
        ▼
┌─────────────────────────────────┐
│  Docker Compose khởi động       │
│  - PostgreSQL 15                │
│  - Odoo 18 + qa_bug_management  │
└─────────────────────────────────┘
        │
        ▼
Chạy Odoo Python tests
(--test-tags qa_bug_management)
        │
        ├──── PASS ──────────────────► Job green, kết thúc
        │
        └──── FAIL
               │
               ▼
        parse_odoo_test_log.py
        → failures.json
        {
          "failed": N,
          "failures": [
            { "test": "...", "module": "...", "traceback": "..." }
          ]
        }
               │
               ▼
        upload_report.py
        1. Đọc HTML report
        2. Tìm ảnh evidence (src: "assets/evidence/...")
        3. Upload ảnh lên Cloudinary
        4. Rewrite src → Cloudinary HTTPS URL
        5. POST HTML lên Component A (Vercel)
        → share_url
               │
               ▼
        report_ci_failure.py
        POST /qa/ci/bug (qua Cloudflare Tunnel)
        {
          title, description, severity,
          ci_run_url, ci_commit_sha, ci_branch,
          report_share_url: <share_url>
        }
               │
               ▼
        Odoo tạo QA-BUG/xxxx tự động
        - Source: CI/CD
        - Reporter: ci-bot
        - Report URL: link về Component A
               │
               ▼
        QA Lead mở Odoo
        QA → Bug Tickets → QA-BUG/xxxx
        → Click "Open Report"
        → Xem full HTML report trên webapp
```

---

## 3. Kiến trúc từng layer

### Layer 1 — Test Runner (GitHub Actions + Docker)

| Thành phần | Chi tiết |
|---|---|
| Trigger | Push bất kỳ branch, PR vào main |
| Runtime | Ubuntu Latest (GitHub Actions runner) |
| Docker images | `odoo:18.0` + `postgres:15-alpine` |
| Test command | `odoo --test-tags qa_bug_management --stop-after-init` |
| Output | Exit code 1 nếu có test fail, log ra stdout |
| Script | `scripts/run_odoo_tests.sh` |

**Cơ chế:**
- `set -o pipefail` đảm bảo exit code từ Odoo không bị `tee` nuốt mất
- `--abort-on-container-exit` Docker Compose tự dừng khi Odoo exit
- Step dùng `continue-on-error: true` để các step sau vẫn chạy khi test fail

---

### Layer 2 — Log Parser

| Thành phần | Chi tiết |
|---|---|
| Script | `scripts/parse_odoo_test_log.py` |
| Input | Odoo test log từ Docker stdout |
| Output | `failures.json` |
| Regex | `FAIL: (?:\w+\.)*(test\w+)` (Odoo 18 format — không có ngoặc đơn) |
| Fallback | Nếu summary báo fail nhưng regex không match → tạo entry "unknown" |

**Odoo 18 log format:**
```
ERROR db odoo.addons.module.tests.TestClass: FAIL: TestClass.test_method_name
```

---

### Layer 3 — Report Upload (Component A)

| Thành phần | Chi tiết |
|---|---|
| Script | `scripts/upload_report.py` |
| Cloudinary | Upload ảnh evidence, rewrite `src:` trong HTML |
| API | `POST /api/reports` với header `X-Pipeline-Key` |
| Output | `share_url` dạng `https://<vercel-domain>/r/<id>?t=<token>` |
| Fallback | Exit 0 kể cả khi lỗi — không làm CI fail |

**Regex rewrite ảnh:**
```python
re.compile(r'\bsrc\s*:\s*"(assets/evidence/[^"]+)"')
```

---

### Layer 4 — Bug Ticket Reporter (Component B)

| Thành phần | Chi tiết |
|---|---|
| Script | `scripts/report_ci_failure.py` |
| Endpoint | `POST /qa/ci/bug` trên Odoo local |
| Auth | Header `X-CI-Key` (environment secret) |
| Network | Cloudflare Tunnel expose `localhost:8069` ra internet |
| Dedup | Cùng `ci_commit_sha` + `title` + chưa resolved → không tạo ticket mới, append description |

---

### Layer 5 — Odoo Bug Ticket System (Component B)

| Thành phần | Chi tiết |
|---|---|
| Module | `qa_bug_management` (Odoo 18 Community) |
| Model chính | `qa.bug.ticket` |
| Model phụ | `qa.bug.evidence` |
| Sequence | `QA-BUG/0001`, `QA-BUG/0002`, ... |
| Controller | `POST /qa/ci/bug` — `type='http'`, `auth='none'` |

**Model `qa.bug.ticket` — fields chính:**

| Field | Type | Mô tả |
|---|---|---|
| name | Char | Auto-sequence QA-BUG/#### |
| title | Char | Tên bug |
| severity | Selection | low / medium / high / critical |
| status | Selection | new / triaged / in_progress / fixed / wont_fix / duplicate |
| source | Selection | ci / manual / report_link |
| ci_run_url | Char | Link GitHub Actions run |
| ci_commit_sha | Char | Commit hash |
| ci_branch | Char | Branch name |
| report_share_url | Char | Link về Component A report |
| evidence_ids | One2many | Danh sách evidence |
| resolved_at | Datetime | Set tự động khi status → fixed/wont_fix/duplicate |

---

### Layer 6 — QA Report Web Platform (Component A)

| Thành phần | Chi tiết |
|---|---|
| Framework | Next.js 15.5.18 (App Router) |
| Deploy | Vercel |
| Database | Supabase PostgreSQL (pooler connection) |
| Image storage | Cloudinary |
| Auth | Share token (unguessable URL, không cần login) |

**API endpoints:**

| Endpoint | Method | Mô tả |
|---|---|---|
| `/api/health` | GET | Health check |
| `/api/reports` | POST | Tạo report mới, nhận `{title, html, payload}` |
| `/api/reports/[id]/bugs/[bugId]` | PATCH | Cập nhật note/resolution |
| `/api/reports/[id]/patches` | GET | Lấy danh sách patches |
| `/r/[reportId]?t=<token>` | GET | Xem report |

**client.js** (chạy phía browser):
- Đọc `window.__REPORT_META__` và `window.__REPORT_PATCHES__`
- Apply server-side patches vào DOM (note, resolution trong table rows)
- Intercept nút "Save" → PATCH lên backend API

---

## 4. Use cases áp dụng

### Khi nào hệ thống hữu ích

| Use case | Mô tả |
|---|---|
| Dev sửa custom Odoo module | CI phát hiện regression ngay khi push, tạo ticket tự động |
| Nhiều dev cùng làm việc | Không cần QA test tay sau mỗi PR, lỗi được detect sớm |
| Chuẩn bị upgrade Odoo | Chạy CI để kiểm tra custom module còn hoạt động sau upgrade |
| Business rule bị vi phạm | Test các rule như: không cho ngày tương lai, nhân viên inactive, v.v. |
| QA muốn trace bug | Mỗi ticket có commit SHA, branch, CI run URL, full traceback |
| Share report với team | Upload HTML report lên webapp, chia sẻ 1 link duy nhất |

### Khi nào không phù hợp

- Công ty chỉ dùng Odoo nguyên bản, không custom module
- Không có CI/CD pipeline
- Team chưa có test case nào

---

## 5. Vấn đề hiệu suất hiện tại

### Vấn đề 1 — CI chạy lâu (~8-12 phút/run)

| Bước | Thời gian ước tính | Nguyên nhân |
|---|---|---|
| Pull `odoo:18.0` | 3-5 phút | Image ~2GB, pull lại mỗi run |
| Tạo DB + install module | 2-3 phút | Odoo chạy migration từ đầu |
| Chạy test thực tế | ~20 giây | Nhanh |
| Upload report + POST Odoo | ~30 giây | Network + Cloudinary |

**Giải pháp:**

```yaml
# Cache Docker image layers
- uses: actions/cache@v4
  with:
    path: /tmp/.docker-cache
    key: odoo18-${{ hashFiles('docker-compose.test.yml') }}

- uses: docker/setup-buildx-action@v3
```

Hoặc build **pre-built image** với module đã cài sẵn, push lên GHCR:
```dockerfile
FROM odoo:18.0
COPY qa_bug_management /mnt/extra-addons/qa_bug_management
RUN odoo -d ci_base -i qa_bug_management --stop-after-init
```
→ Bỏ hoàn toàn bước install module (~2-3 phút)

---

### Vấn đề 2 — Cloudflare Tunnel phải bật tay

Hiện tại cần chạy `cloudflared tunnel --url http://localhost:8069` thủ công mỗi khi muốn CI POST được lên Odoo local.

**Giải pháp:** Cấu hình Cloudflare Tunnel chạy như system service:
```bash
cloudflared service install
```
→ Tunnel tự khởi động khi máy boot, không cần bật tay.

---

### Vấn đề 3 — Odoo chạy local, không HA

Nếu máy tắt hoặc Odoo crash → CI không POST được → ticket không tạo được.

**Giải pháp ngắn hạn:** `continue-on-error: true` trên step Report failures (đã có).

**Giải pháp dài hạn:** Host Odoo trên server (VPS/cloud) thay vì local.

---

### Vấn đề 4 — `pip install` lặp lại mỗi CI run

Mỗi step hiện tại đều `pip install requests cloudinary` từ đầu.

**Giải pháp:**
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-${{ hashFiles('pipeline/requirements.txt') }}
```

---

## 6. Hướng cải tiến tương lai

### Phase tiếp theo (ngắn hạn)

| Cải tiến | Mô tả |
|---|---|
| Migrate bug ticket về `project.task` | Dùng Project Task sẵn có của Odoo Community thay vì custom module — đơn giản hơn, ít maintain hơn |
| Auto-close ticket khi test pass lại | Khi CI pass sau khi đã có ticket → tự chuyển status → `fixed` |
| Gắn Odoo ticket với GitHub commit | Link trực tiếp từ ticket về commit trên GitHub |
| Email/activity notification | Khi ticket tạo → Odoo gửi activity cho QA Lead |

### Phase trung hạn

| Cải tiến | Mô tả |
|---|---|
| QA Orchestration Layer | Tách CI pipeline khỏi Odoo/Jira cụ thể — dùng adapter pattern để switch target dễ dàng |
| Jira sync một chiều | CI fail → tạo cả Jira ticket + Odoo ticket, lưu mapping |
| Pre-built Docker image | Image đã cài sẵn module → giảm CI time xuống ~3-4 phút |
| Cloudflare Tunnel as service | Tunnel chạy tự động, không cần bật tay |

### Phase dài hạn

| Cải tiến | Mô tả |
|---|---|
| Host Odoo trên VPS | Không phụ thuộc máy local — HA hơn |
| Dashboard bug metrics | Bug theo module, theo severity, theo developer, bug aging |
| Playwright E2E tests | Thêm layer test UI/flow ngoài unit test Python |
| Multi-module support | CI test nhiều custom module trong cùng 1 run |
| ir.attachment + iframe | Hiển thị full HTML report thẳng trong Odoo form view (không cần mở tab mới) |

---

## 7. Secrets & Environment Variables

| Variable | Nơi dùng | Mô tả |
|---|---|---|
| `QA_CI_KEY` | GitHub Secret + Odoo env | Key xác thực CI → Odoo |
| `ODOO_URL` | GitHub Secret | URL Cloudflare Tunnel của Odoo |
| `CLOUDINARY_URL` | GitHub Secret + Vercel | `cloudinary://key:secret@cloud_name` |
| `COMPONENT_A_BASE_URL` | GitHub Var | Base URL của Vercel webapp |
| `COMPONENT_A_PIPELINE_KEY` | GitHub Secret | Key xác thực upload report |
| `DATABASE_URL` | Vercel | Supabase pooler connection string |
| `PIPELINE_KEY` | Vercel | Alias của COMPONENT_A_PIPELINE_KEY |
| `BASE_URL` | Vercel | Base URL dùng để build share_url |

---

## 8. Cấu trúc repo `qa-system`

```
qa-system/
├── .github/
│   └── workflows/
│       └── ci.yml                  ← GitHub Actions pipeline
├── qa_bug_management/              ← Odoo custom module
│   ├── models/
│   │   ├── qa_bug_ticket.py
│   │   └── qa_bug_evidence.py
│   ├── controllers/
│   │   └── ci_intake.py            ← POST /qa/ci/bug
│   ├── views/
│   │   ├── qa_bug_ticket_views.xml
│   │   └── qa_bug_ticket_menu.xml
│   ├── tests/
│   │   ├── test_qa_bug_ticket.py
│   │   └── test_ci_intake.py
│   └── __manifest__.py
├── qa_helpdesk_smoke_tests/        ← CI-only same-DB smoke tests
├── qa_helpdesk_bridge/             ← Manual Helpdesk ↔ QA Bug bridge
├── addons_oca/
│   └── helpdesk/                   ← Vendored OCA Helpdesk 18.0 slice
│       ├── helpdesk_mgmt/
│       └── helpdesk_mgmt_project/
├── scripts/
│   ├── run_odoo_tests.sh           ← Chạy Docker test
│   ├── parse_odoo_test_log.py      ← Parse Odoo log → failures.json
│   ├── upload_report.py            ← Upload HTML report lên webapp
│   ├── report_ci_failure.py        ← POST failures lên Odoo
│   ├── run_oca_helpdesk_smoke_tests.sh
│   ├── run_qa_helpdesk_bridge_tests.sh
│   └── verify_oca_helpdesk_vendor.py
├── webapp/                         ← Next.js Component A
│   ├── app/
│   │   ├── api/reports/            ← POST tạo report
│   │   └── r/[reportId]/           ← Xem report
│   ├── components/
│   │   └── ReportViewer.tsx
│   ├── lib/
│   │   ├── templateAdapter.ts      ← Inject client.js vào HTML
│   │   └── db.ts
│   └── public/
│       └── static/
│           └── client.js           ← Apply patches + sync lên backend
├── bug_report_landingPage/         ← HTML report mẫu + evidence ảnh
├── docker-compose.test.yml         ← Docker config cho CI
└── odoo18.conf                     ← Config Odoo local (không commit secret)
```
