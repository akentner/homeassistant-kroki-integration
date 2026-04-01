import { LitElement, html, css } from "https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js";

const DIAGRAM_TYPES = [
  "actdiag", "blockdiag", "bpmn", "bytefield", "c4plantuml", "d2", "dbml", "ditaa", "erd",
  "excalidraw", "graphviz", "mermaid", "nomnoml", "nwdiag", "packetdiag", "pikchr", "plantuml",
  "rackdiag", "seqdiag", "structurizr", "svgbob", "symbolator", "tikz", "umlet",
  "vega", "vegalite", "wavedrom", "wireviz",
];

class KrokiPanel extends LitElement {
  static properties = {
    hass: {},
    _diagramType: { state: true },
    _source: { state: true },
    _outputFormat: { state: true },
    _previewUrl: { state: true },
    _previewError: { state: true },
    _entities: { state: true },
    _entityFilter: { state: true },
    _previewLoading: { state: true },
  };

  static styles = css`
    :host {
      display: flex;
      flex-direction: column;
      height: 100%;
      padding: 16px;
      box-sizing: border-box;
      font-family: var(--paper-font-body1_-_font-family, sans-serif);
    }
    .toolbar {
      display: flex;
      gap: 8px;
      align-items: center;
      margin-bottom: 12px;
      flex-wrap: wrap;
    }
    .toolbar select {
      padding: 6px 8px;
      border-radius: 4px;
      border: 1px solid var(--divider-color, #ccc);
      background: var(--card-background-color, white);
      color: var(--primary-text-color, black);
      font-size: 14px;
    }
    .toolbar button {
      padding: 6px 14px;
      border-radius: 4px;
      border: none;
      background: var(--primary-color, #03a9f4);
      color: white;
      cursor: pointer;
      font-size: 14px;
    }
    .toolbar button:disabled {
      opacity: 0.5;
      cursor: default;
    }
    .main {
      display: flex;
      gap: 16px;
      flex: 1;
      min-height: 0;
    }
    .editor-pane {
      display: flex;
      flex-direction: column;
      flex: 1;
      min-width: 0;
    }
    .editor-pane textarea {
      flex: 1;
      font-family: monospace;
      font-size: 13px;
      padding: 8px;
      border: 1px solid var(--divider-color, #ccc);
      border-radius: 4px;
      resize: none;
      background: var(--code-editor-background-color, #1e1e1e);
      color: var(--code-editor-foreground-color, #d4d4d4);
    }
    .preview-pane {
      display: flex;
      flex-direction: column;
      flex: 1;
      min-width: 0;
    }
    .preview-pane img {
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
      border: 1px solid var(--divider-color, #ccc);
      border-radius: 4px;
    }
    .preview-error {
      color: var(--error-color, #db4437);
      font-size: 13px;
      padding: 8px;
    }
    .entity-browser {
      width: 220px;
      display: flex;
      flex-direction: column;
      border: 1px solid var(--divider-color, #ccc);
      border-radius: 4px;
      padding: 8px;
    }
    .entity-browser input {
      width: 100%;
      padding: 4px 6px;
      margin-bottom: 6px;
      border: 1px solid var(--divider-color, #ccc);
      border-radius: 4px;
      box-sizing: border-box;
      font-size: 12px;
    }
    .entity-list {
      flex: 1;
      overflow-y: auto;
      font-size: 12px;
    }
    .entity-item {
      cursor: pointer;
      padding: 3px 4px;
      border-radius: 3px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .entity-item:hover {
      background: var(--secondary-background-color, #f5f5f5);
    }
  `;

  constructor() {
    super();
    this._diagramType = "mermaid";
    this._source = "graph TD\n  A --> B";
    this._outputFormat = "svg";
    this._previewUrl = "";
    this._previewError = null;
    this._entities = [];
    this._entityFilter = "";
    this._previewLoading = false;
  }

  connectedCallback() {
    super.connectedCallback();
    this._loadEntities();
  }

  render() {
    return html`
      <div class="toolbar">
        <select @change=${(e) => (this._diagramType = e.target.value)}>
          ${DIAGRAM_TYPES.map(
            (t) => html`<option value=${t} ?selected=${t === this._diagramType}>${t}</option>`,
          )}
        </select>
        <select @change=${(e) => (this._outputFormat = e.target.value)}>
          <option value="svg" ?selected=${"svg" === this._outputFormat}>SVG</option>
          <option value="png" ?selected=${"png" === this._outputFormat}>PNG</option>
        </select>
        <button @click=${this._renderPreview} ?disabled=${this._previewLoading}>
          ${this._previewLoading ? "Rendering…" : "Render"}
        </button>
      </div>
      <div class="main">
        <div class="editor-pane">
          <textarea
            .value=${this._source}
            @input=${(e) => (this._source = e.target.value)}
            spellcheck="false"
            placeholder="Enter diagram source…"
          ></textarea>
        </div>
        <div class="preview-pane">
          ${this._previewError
            ? html`<div class="preview-error">${this._previewError}</div>`
            : this._previewUrl
              ? html`<img src=${this._previewUrl} alt="diagram preview" />`
              : html`<div style="color: var(--secondary-text-color); padding: 8px;">Click Render to preview</div>`}
        </div>
        <div class="entity-browser">
          <strong style="font-size:12px;margin-bottom:4px;">Entities</strong>
          <input
            type="text"
            placeholder="Filter…"
            .value=${this._entityFilter}
            @input=${(e) => (this._entityFilter = e.target.value)}
          />
          <div class="entity-list">
            ${this._entities
              .filter(
                (e) =>
                  e.entity_id.includes(this._entityFilter) ||
                  e.name.toLowerCase().includes(this._entityFilter.toLowerCase()),
              )
              .map(
                (e) => html`
                  <div
                    class="entity-item"
                    @click=${() => this._insertEntity(e.entity_id)}
                    title=${e.name}
                  >
                    ${e.entity_id}
                  </div>
                `,
              )}
          </div>
        </div>
      </div>
    `;
  }

  async _renderPreview() {
    if (!this.hass) return;
    this._previewLoading = true;
    this._previewError = null;
    try {
      const result = await this.hass.connection.sendMessagePromise({
        type: "kroki/render",
        diagram_type: this._diagramType,
        source: this._source,
        output_format: this._outputFormat,
      });
      this._previewUrl = result.data_url;
    } catch (err) {
      this._previewError = err.message || String(err);
      this._previewUrl = "";
    } finally {
      this._previewLoading = false;
    }
  }

  async _loadEntities() {
    if (!this.hass) return;
    try {
      const result = await this.hass.connection.sendMessagePromise({ type: "kroki/get_entities" });
      this._entities = result.entities;
    } catch (_) {
      this._entities = [];
    }
  }

  _insertEntity(entityId) {
    const template = `{{ states('${entityId}') }}`;
    const textarea = this.shadowRoot.querySelector("textarea");
    if (textarea) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      this._source = this._source.slice(0, start) + template + this._source.slice(end);
      // Schedule cursor placement after re-render
      this.updateComplete.then(() => {
        const ta = this.shadowRoot.querySelector("textarea");
        if (ta) ta.setSelectionRange(start + template.length, start + template.length);
      });
    } else {
      this._source += template;
    }
  }
}

customElements.define("kroki-panel", KrokiPanel);
