# Kroki Integration — GUI Management

## What This Is

Eine Home Assistant Custom Integration, die Diagram-as-Code-Markup (GraphViz, Mermaid, PlantUML, etc.) via einen Kroki-Server in Bilder rendert und als HA Image-Entitäten bereitstellt. Nutzer können damit dynamische, template-basierte Diagramme in Dashboards und Automationen einsetzen.

## Core Value

Kroki-Diagramm-Entitäten müssen vollständig über die Home Assistant GUI erstellt, bearbeitet und gelöscht werden können — ohne YAML bearbeiten zu müssen.

## Requirements

### Validated

- ✓ Kroki-Server-Verbindung via Config Flow (UI) — existing
- ✓ YAML-basierte Diagramm-Entitäten mit Jinja2-Templates — existing
- ✓ Automatisches Re-Rendering bei Entity-State-Änderungen — existing
- ✓ SHA256-basierter LRU-Disk-Cache für gerenderte Bilder — existing
- ✓ SVG- und PNG-Output — existing
- ✓ Unterstützung aller 28+ Kroki-Diagrammtypen — existing
- ✓ YAML-Reload ohne HA-Neustart — existing
- ✓ Fehler-Placeholder-SVG bei Render-Fehlern — existing
- ✓ Options Flow für Default-Format und Cache-Größe — existing
- ✓ Mehrere Kroki-Server konfigurierbar — existing

### Active

- [ ] Diagramm-Entitäten über die GUI anlegen (Config Entry pro Diagramm)
- [ ] Diagramm-Entitäten über die GUI bearbeiten (Name, Typ, Source, Format)
- [ ] Diagramm-Entitäten über die GUI löschen
- [ ] Server-Auswahl beim Erstellen eines Diagramms (Dropdown aller konfigurierten Server)
- [ ] Volle Jinja2-Template-Unterstützung in GUI-erstellten Diagrammen
- [ ] Live-Vorschau im Options Flow beim Bearbeiten
  - ✓ Frontend-Panel mit Editor und Live-Vorschau nebeneinander — Validated in Phase 02: Custom Panel
  - ✓ Diagrammtyp-Auswahl im Panel — Validated in Phase 02: Custom Panel
  - ✓ Entity-Browser im Panel zum Einfügen von Entity-States in Templates — Validated in Phase 02: Custom Panel
- [ ] YAML-Modus bleibt parallel voll funktionsfähig

### Out of Scope

- Entity-Picker / Autocomplete im HA Options Flow — HA Config Flow UI unterstützt keine benutzerdefinierten Widgets
- Panel für Mobile — Desktop-first, Mobile-Optimierung ist ein späterer Milestone
- Migration bestehender YAML-Diagramme in Config Entries — Koexistenz statt Migration

## Current Milestone: v2.0 GUI Entity Management

**Goal:** Kroki-Diagramm-Entitäten vollständig über die Home Assistant GUI anlegen, bearbeiten und löschen — ohne YAML bearbeiten zu müssen.

**Target features:**
- Config Subentries: Diagramme per UI anlegen/bearbeiten/löschen
- TemplateSelector mit Full-Screen-Editor für Diagram-Source
- Jinja2-Template-Unterstützung in GUI-Diagrammen
- Server-Zuweisung per Subentry (Diagramm gehört zu Server-Config-Entry)
- YAML-Modus bleibt vollständig funktionsfähig (paralleler Pfad)
- Custom Panel mit Split-Pane Editor + Live-Vorschau nebeneinander

## Context

- **Brownfield:** Bestehende Integration mit funktionierendem YAML-Modus, Config Flow für Server, Tests und CI
- **HA-Ökosystem:** Config Entries sind der HA-Standard für UI-konfigurierte Entitäten. Diagramme werden als separate Config Entries oder Sub-Entries gespeichert
- **Architektur-Herausforderung:** Aktuell kommt `async_setup_platform` (YAML) zum Einsatz. GUI-Diagramme müssen über `async_setup_entry` und Platform-Forwarding laufen — zwei parallele Pfade für die Image-Platform
- **Frontend-Panel:** HA unterstützt Custom Panels via `async_register_panel`. Das Panel braucht eigenes JS/HTML, das mit der HA-Frontend-API und dem Kroki-Server kommuniziert

## Constraints

- **HA API:** Config Flow UI ist auf Standard-Form-Elemente beschränkt (Textfelder, Dropdowns, Checkboxen) — kein Code-Editor-Widget nativ möglich
- **Kompatibilität:** YAML-Modus muss unverändert weiter funktionieren
- **HA Version:** Minimum 2024.7.0 (HACS-Deklaration)
- **Priorität:** CRUD via GUI ist Kernfunktion, Panel ist Erweiterung

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| GUI-Diagramme als Config Entries | HA-Standard für UI-konfigurierte Entitäten, persistiert automatisch | — Pending |
| Server-Auswahl via Dropdown | Bei mehreren Servern soll der Nutzer frei wählen können | — Pending |
| YAML und GUI koexistieren | Bestehende YAML-Nutzer nicht brechen, beide Wege haben Vorteile | — Pending |
| Panel + Options Flow für Vorschau | Options Flow für Quick-Edit, Panel für komfortables Arbeiten mit Editor | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-02 — Phase 02 complete: sidebar panel with split-pane editor, live preview, and entity browser delivered*
