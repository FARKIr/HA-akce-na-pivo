"""Lovelace karty dodávané s integráciou – načítajú sa automaticky."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL, add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

CARD_FILES = ["akce-na-pivo-card.js", "pivna-karta.js"]
URL_BASE = "/akce_na_pivo"
DATA_REGISTERED = "akce_na_pivo_card_registered"


async def async_register_card(hass: HomeAssistant) -> None:
    """Sprístupní karty na /akce_na_pivo/<karta>.js a pridá ich do frontendu."""
    if hass.data.get(DATA_REGISTERED):
        return
    hass.data[DATA_REGISTERED] = True

    manifest = Path(__file__).parent.parent / "manifest.json"
    version = await hass.async_add_executor_job(
        lambda: json.loads(manifest.read_text(encoding="utf-8")).get("version", "0")
    )
    for card_file in CARD_FILES:
        path = Path(__file__).parent / card_file
        if not path.is_file():
            continue
        await hass.http.async_register_static_paths(
            [StaticPathConfig(f"{URL_BASE}/{card_file}", str(path), False)]
        )
        if DATA_EXTRA_MODULE_URL in hass.data:
            # ?v= zaistí, že prehliadač po aktualizácii integrácie načíta novú verziu karty
            add_extra_js_url(hass, f"{URL_BASE}/{card_file}?v={version}")
            _LOGGER.debug("Karta %s zaregistrovaná (v%s)", card_file, version)
        else:
            _LOGGER.warning(
                "Frontend nie je načítaný – kartu pridajte ručne ako zdroj %s/%s", URL_BASE, card_file
            )
