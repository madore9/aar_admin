---
name: AAR Admin Portal Styling Alignment
overview: Align AAR Admin UI with my.harvard student portal styling by adopting the design system from myharvard-ui-main and Portal_Integration_Standards, tokenizing colors and components, and ensuring a11y compliance. The plan is based on the documented standards, the provided my.harvard screenshots (Identity, Course Search, Student Accounts), and the referenced Figma file.
todos: []
isProject: false
---

# AAR Admin – my.harvard Portal Styling Alignment Plan

## 1) Current state vs. portal standards

**AAR Admin today**

- **Shell:** [layout.html](aar_admin_django/django/app/plans/templates/layout.html) uses Tailwind CDN, inline theme (Inter, `myh` scale), and [aar.css](aar_admin_django/django/app/plans/static/css/aar.css) for a small set of custom buttons/badges. Preline is loaded. No portal design-system CSS.
- **Header:** [header.html](aar_admin_django/django/app/plans/templates/header.html) is a single dark bar (brand + role switcher + avatar). No left sidebar; primary nav is a horizontal tab bar in [tab_nav.html](aar_admin_django/django/app/plans/templates/partials/tab_nav.html).
- **Templates:** Widespread hardcoded hex (`#a51c30`, `#801b30`, `#fde6e6`) and ad-hoc focus rings (`focus:ring-[#a51c30]`) across 16+ template/JS files. Buttons are built with raw Tailwind (e.g. `inline-flex ... bg-[#a51c30]`) instead of design-system classes. Labels use `block text-sm font-medium ...`; inputs use custom borders/focus, not `form-label`/`form-control`. Some modals use `sr-only` and Preline `data-hs-*`/`role="tabpanel"`; toasts use `aria-live="polite"` but no `role="alert"`. No shared validation pattern (`is-invalid`, `invalid-feedback`).

**Portal / my.harvard standards (from [Portal_Integration_Standards.md](Portal_Integration_Standards.md) and screenshots)**

- **Design system:** myharvard-ui-main (Tailwind v4 + Preline) provides `_core.source(.min).css` for tokens and components. Portal shell includes `main.css` + `portal.css`; pages use design-system classes only.
- **Tokens:** Colors via CSS variables (e.g. `--color-primary: #a51c30`); use token-based classes (`bg-primary`, `text-primary`, `border-primary`) — no hardcoded hex in markup (UI-010).
- **Components:** Buttons use `btn`, `btn-primary`, `btn-white`, etc.; icon-only use `btn-icon`/`btn-icon-sm` (UI-003, UI-004). Forms use `form-label` + `form-control`; validation uses `is-invalid` + `invalid-feedback`/`invalid-feedback-text` (UI-005–UI-007). Alerts use `role="alert"` and dismiss has `sr-only` label (UI-008).
- **Layout:** 12-col grid + `md:` breakpoints (UI-011); optional left sidebar (Identity / Student Accounts style). Cards: rounded corners, subtle shadows.
- **Visual refs:** Dark header/footer, white/light content area, crimson for primary actions and active states; Inter typography; consistent iconography and spacing.

**Figma**

- The [My.Harvard Figma file](https://www.figma.com/design/v4vBPpHkIEALX0cqwCYvNA/My.Harvard--MYH-Team-Access-?node-id=72503-67302) (node `72503:67302`) is the design source for the portal. Figma MCP returned metadata only (no code/variables in this run). Use it for visual reference and component specs; implementation should follow the same tokens and patterns as in myharvard-ui-main and the standards doc.

**beta.my.harvard.edu (Course Search)**

- Use the live Course Search page as a validation target: same header/sidebar (if applicable), cards, filters, buttons, and status indicators (e.g. “Satisfied”, “In Progress”) so AAR aligns with real portal behavior and density.

---

## 2) Gap summary


| Area                   | Gap                                                               | Standard / reference                                                 |
| ---------------------- | ----------------------------------------------------------------- | -------------------------------------------------------------------- |
| **CSS source**         | AAR uses Tailwind CDN + aar.css only; no portal design-system CSS | UI-002: use portal/main CSS or equivalent tokens + component classes |
| **Color tokens**       | Hardcoded `#a51c30`, `#801b30`, `#fde6e6` in 16+ files            | UI-010: token-driven only                                            |
| **Buttons**            | Ad-hoc Tailwind button markup                                     | UI-003, UI-004: `btn`, `btn-primary`, `btn-icon`, etc.               |
| **Forms**              | Custom label/input classes                                        | UI-005: `form-label`, `form-control`                                 |
| **Validation**         | No shared invalid/error pattern                                   | UI-006, UI-007: `is-invalid`, `invalid-feedback`                     |
| **Layout / grid**      | No consistent 12-col grid                                         | UI-011: `grid grid-cols-12`, `md:`                                   |
| **Alerts / toasts**    | Toasts lack `role="alert"`; dismiss labels                        | UI-008: `role="alert"`, `sr-only` for dismiss                        |
| **Focus / a11y**       | Custom focus rings; no design-system focus                        | WCAG 2.4.7, 2.1.1: visible focus, keyboard                           |
| **Sidebar (optional)** | No left nav like Identity/Student Accounts                        | Match portal layout if product decision is “same shell”              |


---

## 3) Implementation plan

### Phase A: Design system CSS and tokens

- **A.1** Obtain design-system CSS from **myharvard-ui-main**:
  - If the repo is available (e.g. in workspace or as a dependency), use `dist/assets/css/_core.source.css` (or `_core.source.min.css`) and, if applicable, `main.min.css` / `portal.css` for tokens and components.
  - If myharvard-ui-main is not available, extract from [Portal_Integration_Standards.md](Portal_Integration_Standards.md) and portal screenshots: define the same CSS variables (e.g. `--color-primary`, `--color-primary-dark`, `--color-danger`, radius tokens) and the component classes (`btn`, `btn-primary`, `form-control`, `form-label`, `invalid-feedback`, `is-invalid`, `btn-icon`, `sr-only`) in a dedicated “portal design system” stylesheet under `plans/static/css/` (e.g. `portal-design-system.css`) so AAR does not depend on Tailwind CDN for these.
- **A.2** In [layout.html](aar_admin_django/django/app/plans/templates/layout.html): load the design-system CSS (from myharvard-ui-main or the new `portal-design-system.css`) **before** [aar.css](aar_admin_django/django/app/plans/static/css/aar.css). Keep aar.css only for AAR-specific overrides that do not conflict with tokens (or remove duplicates).
- **A.3** Ensure `:root` in the shell matches portal tokens (primary, danger, success, radii). Layout already uses Inter and a `myh` scale; align variable names with design system (e.g. `--color-primary` = Harvard crimson) so one source of truth drives both Tailwind and any custom classes.

### Phase B: Layout and shell

- **B.1** **Header:** Keep dark bar; ensure brand + nav + right-side icons match portal proportions and spacing. If the product requirement is “AAR Admin” as a module inside my.harvard”, the header may eventually be the shared portal header; for a standalone AAR app, keep current structure but style with design-system tokens (e.g. background from tokens).
- **B.2** **Optional left sidebar:** If aligning with Identity / Student Accounts layout, add a left sidebar in the shell (or a dedicated base template) with light background, user/context at top, and nav links with icons; main content stays in a right-hand content area. If not, keep horizontal tab nav but style tabs with token-based active state (e.g. `border-primary`, `text-primary`).
- **B.3** **Grid:** Use 12-col grid and `md:` breakpoints for main content (see [Portal_Integration_Standards.md](Portal_Integration_Standards.md) “Golden path” and UI-011). Audit [course_list_detail.html](aar_admin_django/django/app/plans/templates/course_lists/course_list_detail.html), [plan_detail.html](aar_admin_django/django/app/plans/templates/plans/plan_detail.html), [course_lists.html](aar_admin_django/django/app/plans/templates/course_lists/course_lists.html), [plan_list.html](aar_admin_django/django/app/plans/templates/plans/plan_list.html), and list/card layouts to introduce `grid grid-cols-12` and responsive column spans where it improves parity with portal.

### Phase C: Tokenize colors and components

- **C.1** **Replace hardcoded hex everywhere:** Replace `#a51c30`, `#801b30`, `#fde6e6` (and any other crimson/gray) with token-based utility classes or variables. Files to update include:
  - Templates: [course_lists.html](aar_admin_django/django/app/plans/templates/course_lists/course_lists.html), [course_list_detail.html](aar_admin_django/django/app/plans/templates/course_lists/course_list_detail.html), [plan_list.html](aar_admin_django/django/app/plans/templates/plans/plan_list.html), [plan_detail.html](aar_admin_django/django/app/plans/templates/plans/plan_detail.html), [tab_nav.html](aar_admin_django/django/app/plans/templates/partials/tab_nav.html), [header.html](aar_admin_django/django/app/plans/templates/header.html), [add_course_modal.html](aar_admin_django/django/app/plans/templates/plans/add_course_modal.html), [batch_add.html](aar_admin_django/django/app/plans/templates/batch/batch_add.html), [requirement_modal.html](aar_admin_django/django/app/plans/templates/plans/requirement_modal.html), [requirement_section.html](aar_admin_django/django/app/plans/templates/plans/requirement_section.html), [edit_validity_modal.html](aar_admin_django/django/app/plans/templates/plans/edit_validity_modal.html), [confirmation_modal.html](aar_admin_django/django/app/plans/templates/plans/confirmation_modal.html), [history_modal.html](aar_admin_django/django/app/plans/templates/plans/history_modal.html), [course_row.html](aar_admin_django/django/app/plans/templates/plans/course_row.html), [course_lookup.html](aar_admin_django/django/app/plans/templates/lookup/course_lookup.html), [course_list_lookup.html](aar_admin_django/django/app/plans/templates/lookup/course_list_lookup.html).
  - Static JS: [plans.js](aar_admin_django/django/app/plans/static/js/plans.js), [batch.js](aar_admin_django/django/app/plans/static/js/batch.js), [lookup.js](aar_admin_django/django/app/plans/static/js/lookup.js), [modals.js](aar_admin_django/django/app/plans/static/js/modals.js) — replace any inline hex in class names or DOM strings with design-system classes.
- **C.2** **Buttons:** Replace every primary CTA and secondary/outline button with design-system classes: `btn btn-primary`, `btn btn-white` (or `btn-secondary` per design system), etc. Use `btn-icon` / `btn-icon-sm` for icon-only actions (e.g. edit, delete, close) so hit targets and hover match portal (UI-003, UI-004).
- **C.3** **Forms:** In every form (modals, course list create/edit, batch add, course lookup, etc.): add `form-label` to `<label>` and `form-control` to `<input>`/`<textarea>`/`<select>`. Remove custom focus ring classes in favor of design-system focus (handled by `form-control` in the design system).

### Phase D: Validation and alerts (a11y-ready)

- **D.1** For forms with required fields, add `required` and associate `invalid-feedback` containers. On server-side validation errors, add `is-invalid` to the control (or wrapper) and show the corresponding `invalid-feedback` block (UI-006, UI-007).
- **D.2** Toasts: add `role="alert"` to the toast container or each toast element so screen readers announce them. Ensure any dismiss control has a visible or `sr-only` label (UI-008).
- **D.3** Modal close buttons: confirm all have `sr-only` text (e.g. “Close”) in addition to the icon; several modals already use this — verify everywhere.

### Phase E: Accessibility audit and fixes

- **E.1** **Focus:** Ensure all interactive elements (buttons, links, inputs, tabs, dropdowns) have a visible focus style from the design system (no `outline: none` without a replacement). Preline components should retain focus behavior; verify dropdown and overlay focus trap.
- **E.2** **Semantics and ARIA:** Use correct headings hierarchy (`h1` → `h2` → …), `nav` with `aria-label` where appropriate (tab_nav already has `aria-label="Tabs"`). For tabs, keep `role="tablist"`, `role="tab"`, `role="tabpanel"`, `aria-selected` (already used in add_course_modal and batch_add). Ensure dropdowns have `aria-haspopup`, `aria-expanded`, `aria-labelledby` (header role switcher already has some).
- **E.3** **Contrast and touch targets:** Verify text/background contrast (WCAG AA). Ensure buttons and icon buttons meet minimum touch target size (design-system `btn`/`btn-icon` sizes are intended to satisfy this).
- **E.4** **Live validation:** Run a quick pass with axe DevTools or similar on key pages (plan list, plan detail, course list detail, one modal) and fix any critical/serious issues.

### Phase F: Validate against portal and Figma

- **F.1** Compare AAR key screens (plan list, course list detail, one modal) side-by-side with **beta.my.harvard.edu** Course Search (and, if possible, Identity or Student Accounts) for header, spacing, card style, buttons, and typography.
- **F.2** Use the **Figma** [My.Harvard file](https://www.figma.com/design/v4vBPpHkIEALX0cqwCYvNA/My.Harvard--MYH-Team-Access-?node-id=72503-67302) to confirm tokens (colors, radii) and component specs for any ambiguous cases.

---

## 4) File and dependency notes

- **myharvard-ui-main:** Referenced in [Portal_Integration_Standards.md](Portal_Integration_Standards.md) and in [.gitignore](.gitignore); it may live outside this repo. Plan assumes either (1) design-system CSS is copied or linked from that repo, or (2) a local `portal-design-system.css` is created from the standards doc so AAR does not rely on Tailwind CDN for component styling.
- **Templates:** All listed templates under `plans/templates/` and shared partials/layout need the class and markup updates above; static JS only where they inject HTML that includes colors or button/form classes.
- **Settings:** [settings.py](aar_admin_django/django/app/aar_admin/settings.py) uses `STATICFILES_DIRS = []`; static files are under `plans/static/`. Adding a new design-system CSS file under `plans/static/css/` requires no config change if APP_DIRS is used for static discovery.

---

## 5) Success criteria

- No hardcoded hex for primary/danger/success in templates or injected HTML; all use token-based classes or variables.
- All primary/secondary and icon buttons use design-system `btn*` classes.
- All form labels and controls use `form-label` and `form-control`; invalid state uses `is-invalid` + `invalid-feedback`.
- Toasts and alerts use `role="alert"`; dismiss has accessible label.
- Focus is visible on all interactive elements; key pages pass an a11y check (e.g. axe) with no critical/serious issues.
- Visual comparison with beta.my.harvard.edu and Figma shows consistent header, cards, buttons, and typography.

