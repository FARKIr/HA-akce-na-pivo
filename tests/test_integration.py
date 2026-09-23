"""Test nastavení integrace v Home Assistantu (spustí se, jen když je HA nainstalovaný)."""

import pytest

pytest.importorskip("pytest_homeassistant_custom_component")

from homeassistant import config_entries  # noqa: E402
from homeassistant.core import HomeAssistant  # noqa: E402
from homeassistant.data_entry_flow import FlowResultType  # noqa: E402

from custom_components.akce_na_pivo.const import DOMAIN, EVENT_CHEAP_BEER  # noqa: E402

from .test_kupi import HTML  # noqa: E402

OVERPASS = {
    "elements": [
        {
            "type": "node",
            "id": 1,
            "lat": 50.08,
            "lon": 14.43,
            "tags": {
                "shop": "supermarket",
                "brand": "Albert",
                "name": "Albert Supermarket",
                "addr:street": "Vodičkova",
                "addr:housenumber": "10",
                "addr:city": "Praha",
                "addr:postcode": "11000",
            },
        },
        {
            "type": "way",
            "id": 2,
            "center": {"lat": 50.10, "lon": 14.50},
            "tags": {
                "shop": "supermarket",
                "brand": "Lidl",
                "name": "Lidl",
                "addr:street": "Kolbenova",
                "addr:housenumber": "5",
                "addr:city": "Praha",
            },
        },
        {
            "type": "node",
            "id": 3,
            "lat": 50.09,
            "lon": 14.45,
            "tags": {"shop": "supermarket", "brand": "Penny", "name": "Penny"},
        },
    ]
}


@pytest.fixture(autouse=True)
def auto_enable(enable_custom_integrations):
    yield


async def test_flow_and_setup(hass: HomeAssistant, aioclient_mock) -> None:
    hass.config.latitude, hass.config.longitude = 50.087, 14.421
    aioclient_mock.get("https://www.kupi.cz/slevy/pivo", text=HTML)
    aioclient_mock.get("https://www.kupi.cz/slevy/pivo?page=2", text="<html></html>")
    aioclient_mock.get("https://www.kupi.cz/hledej?f=Moje+Pivo", text="<html></html>")
    aioclient_mock.post("https://overpass-api.de/api/interpreter", json=OVERPASS)
    aioclient_mock.get(
        "https://nominatim.openstreetmap.org/reverse",
        json={
            "address": {
                "road": "Seifertova",
                "house_number": "1",
                "city": "Praha",
                "postcode": "13000",
            }
        },
    )
    events = []
    hass.bus.async_listen(EVENT_CHEAP_BEER, events.append)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Pivo",
            "brands": ["Pilsner Urquell", "Birell (nealko), Moje Pivo"],
            "update_time": "07:30:00",
            "update_interval_hours": 0,
            "top_count": 5,
            "sort_by": "unit",
            "max_distance_km": 15,
            "require_nearby_store": False,
            "price_alert": 18,
            "include_upcoming": True,
            "exclude_loyalty": False,
            "exclude_nonalcoholic": False,
            "max_pages": 3,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"]["brands"] == ["Pilsner Urquell", "Birell (nealko)", "Moje Pivo"]
    await hass.async_block_till_done()

    cheapest = hass.states.get("sensor.pivo_nejlevnejsi_pivo") or hass.states.get(
        "sensor.pivo_cheapest_beer"
    )
    assert cheapest is not None, [s.entity_id for s in hass.states.async_all()]
    top = cheapest.attributes["offers"]
    # Birell 14,90 Kč/0,5 l, Pilsner Urquell 24,90 Kč; Lidl multipack začíná až zítra
    assert [o["shop"] for o in top] == ["Penny Market", "Albert Hypermarket"]
    assert float(cheapest.state) == 14.9
    assert top[0]["address"] == "Seifertova 1, 13000 Praha"
    assert top[1]["address"] == "Vodičkova 10, 11000 Praha"
    assert top[1]["distance_km"] < 2
    assert "Končí dnes" in top[0]["flags"]
    assert cheapest.attributes["upcoming"][0]["shop"] == "Lidl"

    rank1 = [s for s in hass.states.async_all("sensor") if s.attributes.get("rank") == 1]
    assert rank1 and rank1[0].attributes["latitude"] == 50.09

    binary = hass.states.async_all("binary_sensor")[0]
    assert binary.state == "on"
    assert len(events) == 1 and events[0].data["shop"] == "Penny Market"

    # opakovaná aktualizace nesmí znovu poslat stejnou událost
    await hass.services.async_call(DOMAIN, "refresh", {}, blocking=True)
    await hass.async_block_till_done()
    assert len(events) == 1

    # options flow
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert await hass.config_entries.async_unload(entry.entry_id)
