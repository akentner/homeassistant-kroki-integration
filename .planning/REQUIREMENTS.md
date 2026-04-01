# Requirements — Milestone v2.0: GUI Entity Management

**Version:** v2.0
**Status:** Active
**Last updated:** 2026-04-01

---

## Milestone Requirements

### GUI CRUD (Config Subentries)

- [x] **CRUD-01**: User kann ein Diagramm-Subentry unter einem Kroki-Server-Config-Entry anlegen
- [x] **CRUD-02**: User kann ein bestehendes Diagramm-Subentry bearbeiten (Name, Typ, Source, Format)
- [ ] **CRUD-03**: User kann ein Diagramm-Subentry löschen; die zugehörige Image-Entität verschwindet
- [x] **CRUD-04**: Formular zeigt Inline-Fehler bei ungültigen Eingaben (z.B. unbekannter Typ, Serverfehler)
- [x] **CRUD-05**: Alle UI-Labels, Beschreibungen und Fehler sind in `strings.json` vollständig hinterlegt

### Entity-Konfiguration

- [x] **CFG-01**: User wählt Diagrammtyp aus einem Dropdown (alle 28+ unterstützten Typen)
- [x] **CFG-02**: User gibt Diagram-Source in einem TemplateSelector-Feld ein (mehrzeilig, Full-Screen-Editor)
- [x] **CFG-03**: User wählt Output-Format (SVG/PNG) pro Diagramm; Default vom Server-Entry geerbt
- [x] **CFG-04**: Jedes GUI-Diagramm erhält eine stabile `unique_id` = `subentry_id` (nie vom Namen abgeleitet)

### Template-Support

- [x] **TPL-01**: GUI-Diagramme unterstützen Jinja2-Templates — automatisches Re-Rendering bei Entity-State-Änderungen
- [x] **TPL-02**: TemplateSelector-Feld bietet Full-Screen-Editor mit Syntax-Highlighting

### YAML-Koexistenz

- [x] **YAML-01**: YAML-konfigurierte Diagramme funktionieren parallel zu GUI-Diagrammen ohne Änderung oder Migration

### Custom Panel

- [ ] **PANEL-01**: Kroki-Sidebar-Panel ist in HA registriert und über die Seitenleiste erreichbar
- [ ] **PANEL-02**: Panel zeigt Editor (textarea, Monospace) und Live-Vorschau nebeneinander (Split-Pane)
- [ ] **PANEL-03**: User kann Diagrammtyp im Panel per Dropdown wählen
- [ ] **PANEL-04**: Panel rendert bei Änderungen eine Live-Vorschau via Kroki-Server (WebSocket-Backend)
- [ ] **PANEL-05**: User kann Entity-IDs aus einem Entity-Browser in die Template-Source einfügen

### Service-Erweiterung

- [ ] **SVC-01**: HA-Service `kroki.force_render` ermöglicht manuelles Neu-Rendern einer bestimmten Entität

---

## Future Requirements (deferred)

- Migration bestehender YAML-Diagramme in Config Entries (Koexistenz ist ausreichend)
- CodeMirror-Integration im Panel (nach LitElement+textarea MVP)
- Mobile-Optimierung des Panels (Desktop-first für v2.0)

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Entity-Picker / Autocomplete in Config Flow | HA Config Flow UI unterstützt keine Custom Widgets |
| YAML-zu-GUI-Migration | Koexistenz statt Migration; kein User-Request |
| Bidirektionale YAML-GUI-Sync | Maintenance-Trap, Konflikte unvermeidbar |
| Multiple Diagramme pro Subentry | 1:1 Granularität ist korrektes HA-Pattern |
| Panel-first Approach (ohne Config Flow) | Config Flow CRUD muss zuerst funktionieren |

---

## Traceability

| REQ-ID | Phase | Status |
|--------|-------|--------|
| CRUD-01 | Phase 1 | Complete |
| CRUD-02 | Phase 1 | Complete |
| CRUD-03 | Phase 1 | Pending |
| CRUD-04 | Phase 1 | Complete |
| CRUD-05 | Phase 1 | Complete |
| CFG-01 | Phase 1 | Complete |
| CFG-02 | Phase 1 | Complete |
| CFG-03 | Phase 1 | Complete |
| CFG-04 | Phase 1 | Complete |
| TPL-01 | Phase 1 | Complete |
| TPL-02 | Phase 1 | Complete |
| YAML-01 | Phase 1 | Complete |
| PANEL-01 | Phase 2 | Pending |
| PANEL-02 | Phase 2 | Pending |
| PANEL-03 | Phase 2 | Pending |
| PANEL-04 | Phase 2 | Pending |
| PANEL-05 | Phase 2 | Pending |
| SVC-01 | Phase 3 | Pending |
