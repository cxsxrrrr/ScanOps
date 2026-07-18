# Graph Report - .  (2026-06-12)

## Corpus Check
- 160 files · ~52,064 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 74 nodes · 39 edges · 45 communities (5 shown, 40 thin omitted)
- Extraction: 72% EXTRACTED · 28% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Vigia|Vigia]]
- [[_COMMUNITY_Bug Fixes 2026-05-25|Bug Fixes 2026-05-25]]
- [[_COMMUNITY_Vigia Frontend (index.html)|Vigia Frontend (index.html)]]
- [[_COMMUNITY_UIUX Redesign 2026-05-25|UI/UX Redesign 2026-05-25]]
- [[_COMMUNITY_Clerk JWT Validation|Clerk JWT Validation]]
- [[_COMMUNITY_Celery 5.4.0|Celery 5.4.0]]
- [[_COMMUNITY_ReportLab 4.2.2|ReportLab 4.2.2]]
- [[_COMMUNITY_AdminDashboard|AdminDashboard]]
- [[_COMMUNITY_EditOrgModal|EditOrgModal]]
- [[_COMMUNITY_EditUserModal|EditUserModal]]
- [[_COMMUNITY_OrgAnalyticsModal|OrgAnalyticsModal]]
- [[_COMMUNITY_django-cors-headers 4.6.0|django-cors-headers 4.6.0]]
- [[_COMMUNITY_django-filter 24.3|django-filter 24.3]]
- [[_COMMUNITY_openpyxl 3.1.5|openpyxl 3.1.5]]
- [[_COMMUNITY_python-decouple 3.8|python-decouple 3.8]]
- [[_COMMUNITY_Resend Email 2.0.0|Resend Email 2.0.0]]
- [[_COMMUNITY_ErrorBoundary|ErrorBoundary]]
- [[_COMMUNITY_PageTransition|PageTransition]]
- [[_COMMUNITY_TermsModal|TermsModal]]
- [[_COMMUNITY_ThemeProvider|ThemeProvider]]
- [[_COMMUNITY_useTheme|useTheme]]
- [[_COMMUNITY_useApiSetup|useApiSetup]]
- [[_COMMUNITY_DashboardLayout|DashboardLayout]]
- [[_COMMUNITY_setTokenGetter|setTokenGetter]]
- [[_COMMUNITY_signalAuthReady|signalAuthReady]]
- [[_COMMUNITY_cn|cn]]
- [[_COMMUNITY_formatDate|formatDate]]
- [[_COMMUNITY_getSeverityColor|getSeverityColor]]
- [[_COMMUNITY_getSeverityLabel|getSeverityLabel]]
- [[_COMMUNITY_getStatusColor|getStatusColor]]
- [[_COMMUNITY_getStatusLabel|getStatusLabel]]
- [[_COMMUNITY_Dashboard|Dashboard]]
- [[_COMMUNITY_JoinTeam|JoinTeam]]
- [[_COMMUNITY_Login|Login]]
- [[_COMMUNITY_PaymentCancel|PaymentCancel]]
- [[_COMMUNITY_PaymentSuccess|PaymentSuccess]]
- [[_COMMUNITY_Plans|Plans]]
- [[_COMMUNITY_Profile|Profile]]
- [[_COMMUNITY_Register|Register]]
- [[_COMMUNITY_Report|Report]]
- [[_COMMUNITY_ScanHistory|ScanHistory]]
- [[_COMMUNITY_Settings|Settings]]
- [[_COMMUNITY_TermsAndConditions|TermsAndConditions]]
- [[_COMMUNITY_URLs|URLs]]
- [[_COMMUNITY_Frontend Design Skill|Frontend Design Skill]]

## God Nodes (most connected - your core abstractions)
1. `UI/UX Redesign 2026-05-25` - 10 edges
2. `Vigia` - 7 edges
3. `Bug Fixes 2026-05-25` - 7 edges
4. `Vigia Frontend (index.html)` - 5 edges
5. `Django 5.1.5` - 3 edges
6. `BUG-002 XSS via dangerouslySetInnerHTML` - 3 edges
7. `BUG-004 Dark Mode CSS Selector Fix` - 3 edges
8. `Django REST Framework 3.15.2` - 2 edges
9. `Clerk JWT Validation` - 2 edges
10. `BUG-001 React Rules of Hooks Violation` - 2 edges

## Surprising Connections (you probably didn't know these)
- `google-generativeai 0.8.4` --used_by--> `Vigia`  [INFERRED]
  backend/requirements.txt → README.md
- `Stripe Payments` --used_by--> `Vigia`  [INFERRED]
  backend/requirements.txt → README.md
- `Bug Fixes 2026-05-25` --documents--> `Vigia`  [INFERRED]
  frontend/docs/changes/2026-05-25-bugfixes.md → README.md
- `UI/UX Redesign 2026-05-25` --documents--> `Vigia`  [INFERRED]
  frontend/docs/changes/2026-05-25-redesign.md → README.md
- `Django 5.1.5` --implements--> `Vigia`  [INFERRED]
  backend/requirements.txt → README.md

## Import Cycles
- None detected.

## Communities (45 total, 40 thin omitted)

### Community 0 - "Vigia"
Cohesion: 0.25
Nodes (8): Django 5.1.5, Django REST Framework 3.15.2, drf-spectacular 0.27.2, google-generativeai 0.8.4, psycopg2-binary 2.9.10, Stripe Payments, Cybersecurity Web Scanning Web Application, Vigia

### Community 1 - "Bug Fixes 2026-05-25"
Cohesion: 0.33
Nodes (7): BUG-001 React Rules of Hooks Violation, BUG-002 XSS via dangerouslySetInnerHTML, BUG-003 Blocking alert() Replaced by Inline UI, BUG-005 Missing HTTP Request Cancellation (AbortController), Bug Fixes 2026-05-25, src/App.jsx, src/pages/Report.jsx

### Community 2 - "Vigia Frontend (index.html)"
Cohesion: 0.29
Nodes (7): BUG-004 Dark Mode CSS Selector Fix, src/index.css, Dark Mode Theme Toggle (localStorage), Inter Font (Google Fonts), Target Audience: PYMES (SMBs), Vigia Frontend (index.html), Vite + React (main.jsx entry)

### Community 3 - "UI/UX Redesign 2026-05-25"
Cohesion: 0.38
Nodes (7): ErrorBoundary Component, framer-motion v11, PageTransition Component, Radix UI / shadcn-ui, UI/UX Redesign 2026-05-25, shadcn/ui Components (16 components), Sonner Toast System v1

### Community 4 - "Clerk JWT Validation"
Cohesion: 0.67
Nodes (3): Clerk JWT Validation, cryptography 44.0.0, PyJWT 2.10.1

## Knowledge Gaps
- **56 isolated node(s):** `ErrorBoundary`, `PageTransition`, `TermsModal`, `ThemeProvider`, `useTheme` (+51 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **40 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Vigia` connect `Vigia` to `Bug Fixes 2026-05-25`, `Vigia Frontend (index.html)`, `UI/UX Redesign 2026-05-25`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Why does `UI/UX Redesign 2026-05-25` connect `UI/UX Redesign 2026-05-25` to `Vigia`, `Bug Fixes 2026-05-25`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `Bug Fixes 2026-05-25` connect `Bug Fixes 2026-05-25` to `Vigia`, `Vigia Frontend (index.html)`, `UI/UX Redesign 2026-05-25`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `UI/UX Redesign 2026-05-25` (e.g. with `Bug Fixes 2026-05-25` and `Vigia`) actually correct?**
  _`UI/UX Redesign 2026-05-25` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `Vigia` (e.g. with `Django 5.1.5` and `google-generativeai 0.8.4`) actually correct?**
  _`Vigia` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `Bug Fixes 2026-05-25` (e.g. with `Vigia` and `UI/UX Redesign 2026-05-25`) actually correct?**
  _`Bug Fixes 2026-05-25` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `Django 5.1.5` (e.g. with `Vigia` and `psycopg2-binary 2.9.10`) actually correct?**
  _`Django 5.1.5` has 2 INFERRED edges - model-reasoned connections that need verification._