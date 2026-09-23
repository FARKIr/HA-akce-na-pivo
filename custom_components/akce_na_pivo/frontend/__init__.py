"""Lovelace karta dodávaná s integrací – načte se automaticky."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL, add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

CARD_FILE = "akce-na-pivo-card.js"
URL_BASE = "/akce_na_pivo"
DATA_REGISTERED = "akce_na_pivo_card_registered"


async def async_register_card(hass: HomeAssistant) -> None:
    """Zpřístupní kartu na /akce_na_pivo/akce-na-pivo-card.js a přidá ji do frontendu."""
    if hass.data.get(DATA_REGISTERED):
        return
    hass.data[DATA_REGISTERED] = True

    path = Path(__file__).parent / CARD_FILE
    manifest = Path(__file__).parent.parent / "manifest.json"
    version = await hass.async_add_executor_job(
        lambda: json.loads(manifest.read_text(encoding="utf-8")).get("version", "0")
    )
    await hass.http.async_register_static_paths(
        [StaticPathConfig(f"{URL_BASE}/{CARD_FILE}", str(path), False)]
    )
    if DATA_EXTRA_MODULE_URL not in hass.data:
        _LOGGER.warning(
            "Frontend není načtený – kartu přidejte ručně jako zdroj %s/%s", URL_BASE, CARD_FILE
        )
        return
    # ?v= zajistí, že prohlížeč po aktualizaci integrace načte novou verzi karty
    add_extra_js_url(hass, f"{URL_BASE}/{CARD_FILE}?v={version}")
    _LOGGER.debug("Karta akce-na-pivo-card zaregistrována (v%s)", version)
