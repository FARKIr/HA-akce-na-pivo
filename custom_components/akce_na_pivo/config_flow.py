"""Nastavení integrace Akce na pivo přes UI."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    ALL_BRANDS,
    CONF_BRANDS,
    CONF_EXCLUDE_LOYALTY,
    CONF_EXCLUDE_NONALCOHOLIC,
    CONF_INCLUDE_UPCOMING,
    CONF_LOCATION_ENTITY,
    CONF_MAX_DISTANCE_KM,
    CONF_MAX_PAGES,
    CONF_PRICE_ALERT,
    CONF_REQUIRE_NEARBY_STORE,
    CONF_SORT_BY,
    CONF_TOP_COUNT,
    CONF_UPDATE_INTERVAL_HOURS,
    CONF_UPDATE_TIME,
    DEFAULT_BRANDS,
    DEFAULT_EXCLUDE_LOYALTY,
    DEFAULT_EXCLUDE_NONALCOHOLIC,
    DEFAULT_INCLUDE_UPCOMING,
    DEFAULT_MAX_DISTANCE_KM,
    DEFAULT_MAX_PAGES,
    DEFAULT_PRICE_ALERT,
    DEFAULT_REQUIRE_NEARBY_STORE,
    DEFAULT_SORT_BY,
    DEFAULT_TOP_COUNT,
    DEFAULT_UPDATE_INTERVAL_HOURS,
    DEFAULT_UPDATE_TIME,
    DOMAIN,
    KNOWN_BRANDS,
    MAX_TOP_COUNT,
    NAME,
    SORT_OPTIONS,
)


def _schema(values: dict[str, Any], include_name: bool) -> vol.Schema:
    brand_options = [selector.SelectOptionDict(value=ALL_BRANDS, label="🍺 Všechna piva v akci")]
    brand_options += [selector.SelectOptionDict(value=b, label=b) for b in KNOWN_BRANDS]
    # vlastní značky zadané dříve musí zůstat mezi možnostmi
    for brand in values.get(CONF_BRANDS, []):
        if brand != ALL_BRANDS and brand not in KNOWN_BRANDS:
            brand_options.append(selector.SelectOptionDict(value=brand, label=brand))

    fields: dict[Any, Any] = {}
    if include_name:
        fields[vol.Required(CONF_NAME, default=values.get(CONF_NAME, NAME))] = str

    location = values.get(CONF_LOCATION_ENTITY)
    fields.update(
        {
            vol.Required(
                CONF_BRANDS, default=values.get(CONF_BRANDS, DEFAULT_BRANDS)
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=brand_options,
                    multiple=True,
                    custom_value=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            (
                vol.Optional(CONF_LOCATION_ENTITY, description={"suggested_value": location})
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["person", "device_tracker", "zone"])
            ),
            vol.Required(
                CONF_UPDATE_TIME, default=values.get(CONF_UPDATE_TIME, DEFAULT_UPDATE_TIME)
            ): selector.TimeSelector(),
            vol.Required(
                CONF_UPDATE_INTERVAL_HOURS,
                default=values.get(CONF_UPDATE_INTERVAL_HOURS, DEFAULT_UPDATE_INTERVAL_HOURS),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=24,
                    step=1,
                    unit_of_measurement="h",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_TOP_COUNT, default=values.get(CONF_TOP_COUNT, DEFAULT_TOP_COUNT)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1, max=MAX_TOP_COUNT, step=1, mode=selector.NumberSelectorMode.SLIDER
                )
            ),
            vol.Required(
                CONF_SORT_BY, default=values.get(CONF_SORT_BY, DEFAULT_SORT_BY)
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(options=SORT_OPTIONS, translation_key=CONF_SORT_BY)
            ),
            vol.Required(
                CONF_MAX_DISTANCE_KM,
                default=values.get(CONF_MAX_DISTANCE_KM, DEFAULT_MAX_DISTANCE_KM),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=50,
                    step=1,
                    unit_of_measurement="km",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_REQUIRE_NEARBY_STORE,
                default=values.get(CONF_REQUIRE_NEARBY_STORE, DEFAULT_REQUIRE_NEARBY_STORE),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_PRICE_ALERT, default=values.get(CONF_PRICE_ALERT, DEFAULT_PRICE_ALERT)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=100,
                    step=0.1,
                    unit_of_measurement="Kč",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_INCLUDE_UPCOMING,
                default=values.get(CONF_INCLUDE_UPCOMING, DEFAULT_INCLUDE_UPCOMING),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_EXCLUDE_LOYALTY,
                default=values.get(CONF_EXCLUDE_LOYALTY, DEFAULT_EXCLUDE_LOYALTY),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_EXCLUDE_NONALCOHOLIC,
                default=values.get(CONF_EXCLUDE_NONALCOHOLIC, DEFAULT_EXCLUDE_NONALCOHOLIC),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_MAX_PAGES, default=values.get(CONF_MAX_PAGES, DEFAULT_MAX_PAGES)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1, max=20, step=1, mode=selector.NumberSelectorMode.BOX
                )
            ),
        }
    )
    return vol.Schema(fields)


def _clean(user_input: dict[str, Any]) -> dict[str, Any]:
    data = dict(user_input)
    brands: list[str] = []
    for raw in data.get(CONF_BRANDS, []):
        # vlastní hodnotu lze zadat i jako "Značka1, Značka2"
        for brand in str(raw).split(","):
            brand = brand.strip()
            if brand and brand not in brands:
                brands.append(brand)
    data[CONF_BRANDS] = brands
    for key in (CONF_UPDATE_INTERVAL_HOURS, CONF_TOP_COUNT, CONF_MAX_PAGES):
        if key in data:
            data[key] = int(data[key])
    if not data.get(CONF_LOCATION_ENTITY):
        data.pop(CONF_LOCATION_ENTITY, None)
    return data


class AkceNaPivoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Průvodce nastavením."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            data = _clean(user_input)
            if not data[CONF_BRANDS]:
                errors[CONF_BRANDS] = "no_brands"
            else:
                title = data.pop(CONF_NAME, NAME)
                return self.async_create_entry(title=title, data={}, options=data)
        return self.async_show_form(
            step_id="user", data_schema=_schema(user_input or {}, include_name=True), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return AkceNaPivoOptionsFlow()


class AkceNaPivoOptionsFlow(OptionsFlow):
    """Změna nastavení."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            data = _clean(user_input)
            if not data[CONF_BRANDS]:
                errors[CONF_BRANDS] = "no_brands"
            else:
                return self.async_create_entry(data=data)
        values = {**self.config_entry.data, **self.config_entry.options, **(user_input or {})}
        return self.async_show_form(
            step_id="init", data_schema=_schema(values, include_name=False), errors=errors
        )
