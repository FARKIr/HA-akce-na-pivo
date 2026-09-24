/*
 * Pivná karta – moderná Lovelace karta pre integráciu "Akcie na pivo"
 * Zobrazuje najvýhodnejšie ponuky piva, obchod, adresu, vzdialenosť, navigáciu a mapu.
 */

const PIVNA_KARTA_VERSION = "2.0.0";
const LEAFLET_VERSION = "1.9.4";
const LEAFLET_JS = `https://cdn.jsdelivr.net/npm/leaflet@${LEAFLET_VERSION}/dist/leaflet.js`;
const LEAFLET_CSS = `https://cdn.jsdelivr.net/npm/leaflet@${LEAFLET_VERSION}/dist/leaflet.css`;

console.info(
  `%c PIVNÁ KARTA %c v${PIVNA_KARTA_VERSION} `,
  "color:#fff;background:#d97706;font-weight:700;border-radius:3px 0 0 3px",
  "color:#d97706;background:#fef3c7;border-radius:0 3px 3px 0"
);

let leafletPromise;
function loadLeaflet() {
  if (window.L) return Promise.resolve(window.L);
  if (!leafletPromise) {
    leafletPromise = new Promise((resolve, reject) => {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = LEAFLET_CSS;
      document.head.appendChild(link);

      const script = document.createElement("script");
      script.src = LEAFLET_JS;
      script.async = true;
      script.onload = () => (window.L ? resolve(window.L) : reject(new Error("Leaflet")));
      script.onerror = () => {
        leafletPromise = undefined;
        reject(new Error("Leaflet sa nepodarilo načítať"));
      };
      document.head.appendChild(script);
    });
  }
  return leafletPromise;
}

const ALL = "__all__";

const esc = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const fmt = (value, symbol, locale = "sk-SK") =>
  value === null || value === undefined || value === ""
    ? "–"
    : `${Number(value).toLocaleString(locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${symbol}`;

const km = (value, locale = "sk-SK") =>
  value === null || value === undefined ? "" : `${Number(value).toLocaleString(locale, { maximumFractionDigits: 1 })} km`;

const shortDate = (iso) => {
  if (!iso) return "";
  const d = new Date(`${iso}T00:00:00`);
  return `${d.getDate()}. ${d.getMonth() + 1}.`;
};

class PivnaKarta extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._brand = ALL;
    this._selectedIdx = 0;
    this._map = null;
    this._marker = null;
    this._lastKey = "";
  }

  static getConfigElement() {
    return document.createElement("pivna-karta-editor");
  }

  static getStubConfig(hass) {
    const entity = Object.keys(hass.states).find(
      (id) => id.startsWith("sensor.") && Array.isArray(hass.states[id].attributes.offers) && "sort_by" in hass.states[id].attributes
    );
    return { entity: entity || "" };
  }

  setConfig(config) {
    if (!config || !config.entity) throw new Error("Zadajte entitu – senzor najlacnejšieho piva z integrácie Akcie na pivo");
    this._config = {
      title: "Kam na pivo",
      count: 5,
      show_map: true,
      show_list: true,
      show_brands: true,
      map_height: 180,
      ...config,
    };
    this._brand = this._config.brand || ALL;
    this._selectedIdx = 0;
    this._lastKey = "";
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    const state = hass.states[this._config?.entity];
    const key = state ? `${state.last_updated}|${state.state}` : "missing";
    if (key !== this._lastKey) {
      this._lastKey = key;
      this._render();
    }
  }

  getCardSize() {
    return 4 + (this._config?.show_list ? this._config.count : 0) + (this._config?.show_map ? 3 : 0);
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6, rows: "auto" };
  }

  _attrs() {
    return this._hass.states[this._config.entity]?.attributes || {};
  }

  _selection(attrs) {
    const offers = attrs.offers || [];
    const brands = attrs.brands || {};
    if (this._brand && this._brand !== ALL) {
      const list = offers.filter((o) => o.brand === this._brand);
      const best = brands[this._brand] || list[0] || null;
      return { best, list: list.length ? list : best ? [best] : [] };
    }
    return { best: offers[0] || null, list: offers };
  }

  _render() {
    if (!this._config || !this._hass) return;
    const stateObj = this._hass.states[this._config.entity];
    if (!stateObj) {
      this.shadowRoot.innerHTML = `<style>${STYLE}</style><ha-card><div class="card-container"><div class="empty-state"><ha-icon icon="mdi:alert-circle-outline"></ha-icon><div>Entita ${esc(this._config.entity)} sa nenašla</div></div></div></ha-card>`;
      return;
    }

    const attrs = this._attrs();
    const isCZ = attrs.country === "CZ";
    const locale = isCZ ? "cs-CZ" : "sk-SK";
    const symbol = attrs.currency_symbol || (isCZ ? "Kč" : "€");
    const { best, list } = this._selection(attrs);
    const count = Math.max(1, Number(this._config.count) || 5);
    const displayedList = list.slice(0, count);

    // Active selected deal for the hero section
    const currentDeal = displayedList[this._selectedIdx] || best || null;

    // Filter brands: extract all available brands from offers and attrs
    const allBrandsMap = attrs.brands || {};
    const brandNames = Object.keys(allBrandsMap).sort((a, b) => a.localeCompare(b));
    // Pick top brands that actually have deals in offers list
    const activeBrandsInOffers = Array.from(new Set((attrs.offers || []).map((o) => o.brand).filter(Boolean)));
    const topChips = activeBrandsInOffers.slice(0, 8);

    const updated = attrs.updated ? new Date(attrs.updated) : null;

    this.shadowRoot.innerHTML = `
      <style>${STYLE}</style>
      <ha-card>
        <div class="card-container">
          <!-- Header -->
          <div class="card-header">
            <div class="header-left">
              <div class="header-icon">
                <ha-icon icon="mdi:beer-outline"></ha-icon>
              </div>
              <div>
                <div class="header-title">${esc(this._config.title)}</div>
                <div class="header-meta">
                  ${attrs.country ? `<span class="country-tag">${esc(attrs.country)}</span>` : ""}
                  <span>${updated ? `Aktualizované ${updated.toLocaleString(locale, { day: "numeric", month: "numeric", hour: "2-digit", minute: "2-digit" })}` : "Čakám na dáta…"}</span>
                </div>
              </div>
            </div>
            <button class="refresh-btn" title="Aktualizovať akcie" aria-label="Aktualizovať akcie">
              <ha-icon icon="mdi:refresh"></ha-icon>
            </button>
          </div>

          <!-- Brand Filters -->
          ${this._config.show_brands && brandNames.length > 1 ? `
            <div class="filter-bar">
              <div class="filter-controls">
                <select class="brand-select" aria-label="Výber značky">
                  <option value="${ALL}" ${this._brand === ALL ? "selected" : ""}>Všetky značky (${brandNames.length})</option>
                  ${brandNames.map((b) => `<option value="${esc(b)}" ${this._brand === b ? "selected" : ""}>${esc(b)}</option>`).join("")}
                </select>
              </div>

              ${topChips.length > 1 ? `
                <div class="brand-chips-scroll" role="tablist">
                  <button class="chip ${this._brand === ALL ? "active" : ""}" data-brand="${ALL}">Všetko</button>
                  ${topChips.map((b) => `<button class="chip ${this._brand === b ? "active" : ""}" data-brand="${esc(b)}">${esc(b)}</button>`).join("")}
                </div>` : ""}
            </div>` : ""}

          <!-- Hero Deal -->
          ${currentDeal ? this._heroHtml(currentDeal, symbol, locale) : `
            <div class="empty-state">
              <ha-icon icon="mdi:tag-off-outline"></ha-icon>
              <div>Na vybrané pivo momentálne nie je žiadna akcia v okolí.</div>
            </div>`}

          <!-- Map -->
          ${currentDeal && this._config.show_map && currentDeal.latitude != null ? `
            <div class="map-wrap" id="map-container" style="height:${Number(this._config.map_height) || 180}px"></div>
          ` : ""}

          <!-- Deals Ranking -->
          ${this._config.show_list && displayedList.length > 0 ? `
            <div class="section-title">Najlepšie akcie v okolí</div>
            <div class="deals-list">
              ${displayedList.map((o, i) => this._rowHtml(o, i, symbol, locale, i === this._selectedIdx)).join("")}
            </div>` : ""}
        </div>
      </ha-card>`;

    // Event listeners
    this.shadowRoot.querySelector(".refresh-btn")?.addEventListener("click", () =>
      this._hass.callService("akce_na_pivo", "refresh", {})
    );

    const brandSelect = this.shadowRoot.querySelector(".brand-select");
    brandSelect?.addEventListener("change", (e) => {
      this._brand = e.target.value;
      this._selectedIdx = 0;
      this._render();
    });

    this.shadowRoot.querySelectorAll(".brand-chips-scroll .chip").forEach((chip) =>
      chip.addEventListener("click", () => {
        this._brand = chip.dataset.brand;
        this._selectedIdx = 0;
        this._render();
      })
    );

    this.shadowRoot.querySelectorAll(".deals-list .deal-row").forEach((row) =>
      row.addEventListener("click", () => {
        const idx = Number(row.dataset.index);
        this._selectedIdx = idx;
        this._render();
      })
    );

    // Initialize or update map
    if (currentDeal && this._config.show_map && currentDeal.latitude != null) {
      this._initMap(currentDeal);
    }
  }

  async _initMap(deal) {
    const container = this.shadowRoot.getElementById("map-container");
    if (!container) return;

    try {
      const L = await loadLeaflet();
      if (!container.isConnected) return;

      container.innerHTML = "";
      const map = L.map(container, {
        zoomControl: false,
        attributionControl: false,
        scrollWheelZoom: false,
        dragging: !L.Browser.mobile,
      });

      // CARTO Voyager tiles: clean, fast, zero access-blocked errors
      L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
        subdomains: "abcd",
        maxZoom: 19,
      }).addTo(map);

      const lat = deal.latitude;
      const lon = deal.longitude;
      map.setView([lat, lon], 14);

      const markerHtml = `<div style="
        background: #d97706; color: #fff; width: 28px; height: 28px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 13px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.35); border: 2px solid #fff;
      ">${this._selectedIdx + 1}</div>`;

      const customIcon = L.divIcon({
        className: "",
        html: markerHtml,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      L.marker([lat, lon], { icon: customIcon }).addTo(map);
      this._map = map;
    } catch {
      // Fallback clean static map if Leaflet fails
      const d = 0.006;
      container.innerHTML = `<iframe title="Mapa" loading="lazy" src="https://www.openstreetmap.org/export/embed.html?bbox=${deal.longitude - d},${deal.latitude - d / 2},${deal.longitude + d},${deal.latitude + d / 2}&layer=mapnik&marker=${deal.latitude},${deal.longitude}"></iframe>`;
    }
  }

  _heroHtml(o, symbol, locale) {
    const shop = o.store_name || o.shop;
    const validity = o.valid_from && o.valid_to
      ? `${shortDate(o.valid_from)} – ${shortDate(o.valid_to)}`
      : o.valid_to ? `do ${shortDate(o.valid_to)}` : esc(o.validity || "");

    const flags = (o.flags || []).slice(0, 4).map((f) => `<span class="tag-badge">${esc(f)}</span>`).join("");

    return `
      <div class="hero-deal">
        <div class="hero-top">
          <div>
            <div class="hero-store-badge">Odporúčaná predajňa</div>
            <div class="hero-store-name">${esc(shop)}</div>
          </div>
          ${o.discount_percent ? `<div class="hero-discount-badge">−${Number(o.discount_percent)} %</div>` : ""}
        </div>

        <div class="hero-location">
          ${o.address ? `<ha-icon icon="mdi:map-marker"></ha-icon><span>${esc(o.address)}</span>` : ""}
          ${o.distance_km != null ? `<span class="dist-badge">${km(o.distance_km, locale)}</span>` : ""}
          ${o.opening_hours ? `<span>·</span><ha-icon icon="mdi:clock-outline"></ha-icon><span>${esc(o.opening_hours)}</span>` : ""}
        </div>

        <div class="hero-body">
          ${o.image ? `<img class="hero-img" src="${esc(o.image)}" alt="" loading="lazy">` : `
            <div class="hero-img-placeholder">
              <ha-icon icon="mdi:glass-mug-variant"></ha-icon>
            </div>`}
          <div class="hero-info">
            <div class="hero-product-name">${esc(o.product)}</div>
            <div class="hero-product-meta">
              ${o.amount ? `${esc(o.amount)}` : ""}
              ${validity ? ` · Platí: ${validity}` : ""}
              ${o.loyalty ? " · Iba s kartou" : ""}
            </div>
          </div>
          <div class="hero-prices">
            <div class="hero-price-big">${fmt(o.price, symbol, locale)}</div>
            ${o.old_price ? `<div class="hero-price-old">${fmt(o.old_price, symbol, locale)}</div>` : ""}
            ${o.price_per_half_liter ? `<div class="hero-price-unit">${fmt(o.price_per_half_liter, symbol, locale)} / 0,5 l</div>` : ""}
          </div>
        </div>

        ${flags ? `<div class="hero-tags">${flags}</div>` : ""}

        <div class="hero-actions">
          ${o.navigate_url ? `<a class="action-btn primary" href="${esc(o.navigate_url)}" target="_blank" rel="noopener"><ha-icon icon="mdi:navigation-variant"></ha-icon>Navigovať</a>` : ""}
          ${o.map_url ? `<a class="action-btn" href="${esc(o.map_url)}" target="_blank" rel="noopener"><ha-icon icon="mdi:map"></ha-icon>Mapa</a>` : ""}
          ${o.url ? `<a class="action-btn" href="${esc(o.url)}" target="_blank" rel="noopener"><ha-icon icon="mdi:newspaper-variant-outline"></ha-icon>Leták</a>` : ""}
        </div>
      </div>`;
  }

  _rowHtml(o, i, symbol, locale, isActive) {
    return `
      <div class="deal-row ${isActive ? "active" : ""}" data-index="${i}">
        <div class="deal-rank">${i + 1}</div>
        ${o.image ? `<img class="deal-thumb" src="${esc(o.image)}" alt="" loading="lazy">` : `
          <div class="deal-thumb-placeholder"><ha-icon icon="mdi:glass-mug-variant"></ha-icon></div>`}
        <div class="deal-info">
          <div class="deal-name">${esc(o.product)}</div>
          <div class="deal-store">
            <span>${esc(o.store_name || o.shop)}</span>
            ${o.distance_km != null ? `<span>·</span><span>${km(o.distance_km, locale)}</span>` : ""}
          </div>
        </div>
        <div class="deal-prices">
          <div class="deal-price">${fmt(o.price, symbol, locale)}</div>
          ${o.price_per_half_liter ? `<div class="deal-unit">${fmt(o.price_per_half_liter, symbol, locale)}/0,5 l</div>` : ""}
        </div>
      </div>`;
  }
}

const STYLE = `
  :host { display: block; }
  ha-card {
    display: block;
    overflow: hidden;
    background: var(--ha-card-background, var(--card-background-color, #ffffff));
    border-radius: var(--ha-card-border-radius, 16px);
    box-shadow: var(--ha-card-box-shadow, 0 2px 8px rgba(0,0,0,0.06));
    border: var(--ha-card-border-width, 1px) solid var(--ha-card-border-color, var(--divider-color, rgba(0,0,0,0.08)));
    color: var(--primary-text-color, #1f2937);
  }
  .card-container {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }
  .header-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .header-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 38px;
    height: 38px;
    border-radius: 10px;
    background: rgba(217, 119, 6, 0.12);
    color: #d97706;
  }
  .header-icon ha-icon {
    --mdc-icon-size: 22px;
  }
  .header-title {
    font-size: 1.22em;
    font-weight: 700;
    line-height: 1.2;
    color: var(--primary-text-color);
  }
  .header-meta {
    font-size: 0.78em;
    color: var(--secondary-text-color, #6b7280);
    margin-top: 2px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .country-tag {
    font-size: 0.72em;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 6px;
    background: var(--secondary-background-color, #f3f4f6);
    color: var(--primary-text-color);
  }
  .refresh-btn {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--secondary-text-color);
    padding: 8px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s;
  }
  .refresh-btn:hover {
    background: var(--secondary-background-color, rgba(0,0,0,0.06));
    color: var(--primary-text-color);
  }

  .filter-bar {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .filter-controls {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .brand-select {
    flex: 1;
    font: inherit;
    font-size: 0.85em;
    font-weight: 600;
    padding: 7px 12px;
    border-radius: 10px;
    background: var(--secondary-background-color, #f3f4f6);
    color: var(--primary-text-color);
    border: 1px solid var(--divider-color, rgba(0,0,0,0.08));
    outline: none;
    cursor: pointer;
  }
  .brand-chips-scroll {
    display: flex;
    gap: 6px;
    overflow-x: auto;
    padding: 2px 0 6px;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
    white-space: nowrap;
  }
  .brand-chips-scroll::-webkit-scrollbar {
    display: none;
  }
  .chip {
    flex: 0 0 auto;
    border: 1px solid var(--divider-color, rgba(0,0,0,0.1));
    cursor: pointer;
    font: inherit;
    font-size: 0.8em;
    font-weight: 600;
    padding: 5px 12px;
    border-radius: 999px;
    color: var(--secondary-text-color, #4b5563);
    background: var(--secondary-background-color, #f9fafb);
    transition: all 0.15s ease;
  }
  .chip:hover {
    background: rgba(217, 119, 6, 0.08);
    color: var(--primary-text-color);
  }
  .chip.active {
    background: #d97706;
    color: #ffffff;
    border-color: #d97706;
    box-shadow: 0 2px 6px rgba(217, 119, 6, 0.25);
  }

  .hero-deal {
    background: var(--secondary-background-color, #f9fafb);
    border: 1px solid var(--divider-color, rgba(0,0,0,0.08));
    border-radius: 14px;
    padding: 16px;
    position: relative;
    overflow: hidden;
  }
  .hero-deal::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #f59e0b, #d97706);
  }
  .hero-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 6px;
  }
  .hero-store-badge {
    font-size: 0.72em;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #d97706;
  }
  .hero-store-name {
    font-size: 1.5em;
    font-weight: 800;
    line-height: 1.15;
    color: var(--primary-text-color);
    margin-top: 2px;
  }
  .hero-discount-badge {
    background: #dc2626;
    color: #ffffff;
    font-weight: 800;
    font-size: 0.85em;
    padding: 3px 8px;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(220, 38, 38, 0.25);
    white-space: nowrap;
  }
  .hero-location {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
    font-size: 0.85em;
    color: var(--secondary-text-color);
    margin-bottom: 12px;
  }
  .hero-location ha-icon {
    --mdc-icon-size: 16px;
    color: #d97706;
  }
  .dist-badge {
    background: var(--card-background-color, #ffffff);
    border: 1px solid var(--divider-color, rgba(0,0,0,0.1));
    padding: 1px 7px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.85em;
    color: var(--primary-text-color);
  }

  .hero-body {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 0;
    border-top: 1px dashed var(--divider-color, rgba(0,0,0,0.12));
    border-bottom: 1px dashed var(--divider-color, rgba(0,0,0,0.12));
  }
  .hero-img {
    width: 58px;
    height: 58px;
    object-fit: contain;
    background: #ffffff;
    border-radius: 10px;
    border: 1px solid var(--divider-color, rgba(0,0,0,0.08));
    flex-shrink: 0;
  }
  .hero-img-placeholder {
    width: 58px;
    height: 58px;
    border-radius: 10px;
    background: rgba(217, 119, 6, 0.1);
    color: #d97706;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .hero-img-placeholder ha-icon {
    --mdc-icon-size: 30px;
  }
  .hero-info {
    flex: 1;
    min-width: 0;
  }
  .hero-product-name {
    font-weight: 700;
    font-size: 1.05em;
    line-height: 1.25;
    color: var(--primary-text-color);
  }
  .hero-product-meta {
    font-size: 0.8em;
    color: var(--secondary-text-color);
    margin-top: 3px;
  }
  .hero-prices {
    text-align: right;
    flex-shrink: 0;
  }
  .hero-price-big {
    font-size: 1.55em;
    font-weight: 900;
    color: #d97706;
    white-space: nowrap;
    line-height: 1.1;
  }
  .hero-price-old {
    font-size: 0.8em;
    color: var(--secondary-text-color);
    text-decoration: line-through;
  }
  .hero-price-unit {
    font-size: 0.8em;
    color: var(--secondary-text-color);
    white-space: nowrap;
    margin-top: 2px;
  }

  .hero-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-top: 10px;
  }
  .tag-badge {
    font-size: 0.72em;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
    background: rgba(217, 119, 6, 0.12);
    color: #b45309;
  }

  .hero-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
  }
  .action-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    text-decoration: none;
    font-weight: 600;
    font-size: 0.82em;
    padding: 7px 14px;
    border-radius: 10px;
    background: var(--card-background-color, #ffffff);
    color: var(--primary-text-color);
    border: 1px solid var(--divider-color, rgba(0,0,0,0.12));
    transition: background 0.15s;
  }
  .action-btn:hover {
    background: var(--secondary-background-color, #f3f4f6);
  }
  .action-btn.primary {
    background: #d97706;
    color: #ffffff;
    border-color: #d97706;
  }
  .action-btn.primary:hover {
    background: #b45309;
  }
  .action-btn ha-icon {
    --mdc-icon-size: 16px;
  }

  .map-wrap {
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid var(--divider-color, rgba(0,0,0,0.1));
    background: var(--secondary-background-color, #f3f4f6);
  }
  .map-wrap iframe, .map-wrap .leaflet-container {
    width: 100%;
    height: 100%;
    border: none;
    display: block;
  }

  .section-title {
    font-weight: 700;
    font-size: 0.85em;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--secondary-text-color);
    margin: 4px 0 0;
  }
  .deals-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .deal-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    border-radius: 12px;
    background: var(--secondary-background-color, #f9fafb);
    border: 1px solid transparent;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .deal-row:hover {
    border-color: rgba(217, 119, 6, 0.3);
    background: var(--card-background-color, #ffffff);
  }
  .deal-row.active {
    border-color: #d97706;
    background: var(--card-background-color, #ffffff);
    box-shadow: 0 2px 8px rgba(217, 119, 6, 0.12);
  }
  .deal-rank {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 0.8em;
    background: var(--card-background-color, #ffffff);
    border: 1px solid var(--divider-color, rgba(0,0,0,0.12));
    color: var(--secondary-text-color);
    flex-shrink: 0;
  }
  .deal-row.active .deal-rank {
    background: #d97706;
    color: #ffffff;
    border-color: #d97706;
  }
  .deal-thumb {
    width: 36px;
    height: 36px;
    object-fit: contain;
    background: #fff;
    border-radius: 6px;
    flex-shrink: 0;
  }
  .deal-thumb-placeholder {
    width: 36px;
    height: 36px;
    border-radius: 6px;
    background: rgba(217, 119, 6, 0.1);
    color: #d97706;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .deal-thumb-placeholder ha-icon {
    --mdc-icon-size: 18px;
  }
  .deal-info {
    flex: 1;
    min-width: 0;
  }
  .deal-name {
    font-weight: 700;
    font-size: 0.88em;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: var(--primary-text-color);
  }
  .deal-store {
    font-size: 0.78em;
    color: var(--secondary-text-color);
    margin-top: 1px;
    display: flex;
    align-items: center;
    gap: 4px;
  }
  .deal-prices {
    text-align: right;
    flex-shrink: 0;
  }
  .deal-price {
    font-weight: 800;
    font-size: 0.95em;
    color: #d97706;
    white-space: nowrap;
  }
  .deal-unit {
    font-size: 0.72em;
    color: var(--secondary-text-color);
  }
  .empty-state {
    padding: 24px 16px;
    text-align: center;
    color: var(--secondary-text-color);
    font-weight: 500;
  }
  .empty-state ha-icon {
    --mdc-icon-size: 32px;
    color: var(--secondary-text-color);
    margin-bottom: 6px;
    display: block;
    margin-left: auto;
    margin-right: auto;
  }
`;

class PivnaKartaEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._form) this._form.hass = hass;
    else this._render();
  }

  _render() {
    if (!this._hass || !this._config) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (s) => EDITOR_LABELS[s.name] || s.name;
      this._form.addEventListener("value-changed", (ev) => {
        this._config = ev.detail.value;
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true }));
      });
      this.appendChild(this._form);
    }
    const brands = Object.keys(this._hass.states[this._config.entity]?.attributes?.brands || {});
    this._form.hass = this._hass;
    this._form.schema = [
      { name: "entity", required: true, selector: { entity: { domain: "sensor", integration: "akce_na_pivo" } } },
      { name: "title", selector: { text: {} } },
      {
        name: "brand",
        selector: {
          select: {
            mode: "dropdown",
            custom_value: true,
            options: [{ value: "", label: "Všetky značky" }, ...brands.map((b) => ({ value: b, label: b }))],
          },
        },
      },
      {
        type: "grid",
        name: "",
        schema: [
          { name: "count", selector: { number: { min: 1, max: 10, mode: "box" } } },
          { name: "map_height", selector: { number: { min: 100, max: 500, step: 10, mode: "box" } } },
          { name: "show_map", selector: { boolean: {} } },
          { name: "show_list", selector: { boolean: {} } },
          { name: "show_brands", selector: { boolean: {} } },
        ],
      },
    ];
    this._form.data = { title: "Kam na pivo", count: 5, map_height: 180, show_map: true, show_list: true, show_brands: true, ...this._config };
  }
}

const EDITOR_LABELS = {
  entity: "Senzor najlacnejšieho piva",
  title: "Nadpis",
  brand: "Predvolená značka",
  count: "Počet akcií v rebríčku",
  map_height: "Výška mapy (px)",
  show_map: "Mapa predajne",
  show_list: "Rebríček najlacnejších",
  show_brands: "Filtrovanie značiek",
};

// Registrácia custom elementov pod pivna-karta aj pivni-karta
if (!customElements.get("pivna-karta")) customElements.define("pivna-karta", PivnaKarta);
if (!customElements.get("pivni-karta")) customElements.define("pivni-karta", class extends PivnaKarta {});
if (!customElements.get("pivna-karta-editor")) customElements.define("pivna-karta-editor", PivnaKartaEditor);
if (!customElements.get("pivni-karta-editor")) customElements.define("pivni-karta-editor", class extends PivnaKartaEditor {});

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "pivna-karta")) {
  window.customCards.push({
    type: "pivna-karta",
    name: "Pivná karta",
    description: "Prehľad najlacnejšieho piva s mapou predajne a filtrami značiek.",
    preview: true,
  });
}
if (!window.customCards.some((c) => c.type === "pivni-karta")) {
  window.customCards.push({
    type: "pivni-karta",
    name: "Pivná karta (kompatibilita)",
    description: "Prehľad najlacnejšieho piva s mapou predajne a filtrami značiek.",
    preview: true,
  });
}
