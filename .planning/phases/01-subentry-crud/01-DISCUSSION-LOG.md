# Phase 1: Subentry CRUD - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-01
**Phase:** 01-subentry-crud
**Areas discussed:** Template-Validierung, Output-Format-Feld, Entity-Naming, Cache-Sharing

---

## Template-Validierung

| Option | Description | Selected |
|--------|-------------|----------|
| Syntax prüfen im Form | async_step_user kompiliert Template, Inline-Fehler bei ungültiger Syntax. Gültige Templates mit nicht-existenten Entity-Refs werden akzeptiert. | ✓ |
| Keine Validierung im Form | Jede Source wird akzeptiert. Fehler erscheinen nach dem Speichern als Error-SVG. | |
| Syntax + Server-Render | Erst Syntax prüfen, dann live gegen Kroki rendern. Blockiert Flow 1-3s. | |

**User's choice:** Syntax prüfen im Form

| Option | Description | Selected |
|--------|-------------|----------|
| Generisch: invalid_template | Einfacher Fehlerkey, kurze Meldung. | |
| Mit Fehlerdetail | Jinja2 Exception-Message als Beschreibung. | ✓ |

**User's choice:** Mit Fehlerdetail — Jinja2-Fehlermeldung soll vollständig angezeigt werden.

---

## Output-Format-Feld

| Option | Description | Selected |
|--------|-------------|----------|
| Immer sichtbar, 3 Optionen | Dropdown: "Server Default", "SVG", "PNG". | ✓ |
| Immer sichtbar, 2 Optionen | Nur "SVG" und "PNG", kein Server Default. | |
| Nur in Reconfigure sichtbar | Beim Anlegen wird Server-Default übernommen. | |

**User's choice:** 3 Optionen mit "Server Default" als erster Option.

| Option | Description | Selected |
|--------|-------------|----------|
| Vom Server-Entry erben | options.default_output_format des parent Entry wird vorausgewählt. | ✓ |
| Immer SVG | Hartcodierter Default. | |

**User's choice:** Server-Default vorbefüllen beim Öffnen des Forms.

---

## Entity-Naming

| Option | Description | Selected |
|--------|-------------|----------|
| Akzeptabel — entity_id ändert sich nicht | unique_id = subentry_id (stabil). entity_id bleibt bei Umbenennung unverändert. | ✓ |
| Umbenennung soll auch entity_id ändern | Bricht Dashboard-Referenzen. | |
| Noch klären | — | |

**User's choice:** Akzeptiertes Verhalten — entity_id bleibt stabil, Entity-Name ändert sich sichtbar.

| Option | Description | Selected |
|--------|-------------|----------|
| Name, mit Placeholder-Beispiel | Label "Name", Placeholder "Network Overview". | ✓ |
| Title (HA-native) | Label "Title" — konsistenter mit HA-Terminologie. | |
| Ich entscheide | Claude wählt. | |

**User's choice:** "Name" als Label mit beschreibendem Placeholder.

---

## Cache-Sharing

| Option | Description | Selected |
|--------|-------------|----------|
| Ja, shared per Server-URL | Eine KrokiCache-Instanz pro Server Config Entry, in hass.data. | ✓ |
| Nein, separate Caches | Separate Instanzen für YAML und GUI. | |

**User's choice:** Shared Cache in hass.data[DOMAIN][entry_id].

| Option | Description | Selected |
|--------|-------------|----------|
| In async_setup_entry | Cache und Client werden beim Setup des Server-Entry erstellt. | ✓ |
| Lazy bei erstem Zugriff | Cache erst bei erstem Entitäts-Zugriff erstellt. | |

**User's choice:** Cache in async_setup_entry erstellen und in hass.data ablegen.

---

## Claude's Discretion

- Config entry MINOR_VERSION bump nach Hinzufügen des Platform Forwardings
- strings.json Format für Selector-Keys
- Test-Coverage-Strategie für die neue Subentry-Logik
- `from_subentry` Classmethod-Signatur und Implementierungsdetails

## Deferred Ideas

Keine — Diskussion blieb im Phase-Scope.
