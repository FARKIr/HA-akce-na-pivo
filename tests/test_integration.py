# """Test nastavení integrace v Home Assistantu (spustí se, jen když je HA nainstalovaný)."""

# import re
# from unittest.mock import patch

# import pytest

# pytest.importorskip("pytest_homeassistant_custom_component")

# from homeassistant import config_entries  # noqa: E402
# from homeassistant.core import HomeAssistant  # noqa: E402
# from homeassistant.data_entry_flow import FlowResultType  # noqa: E402

# from custom_components.akce_na_pivo.const import DOMAIN, EVENT_CHEAP_BEER  # noqa: E402

# from .test_generic import KOMPAS_LIKE  # noqa: E402
# from .test_kupi import HTML  # noqa: E402

# KOMPAS_PU = """
# <div class="card"><h3>Pilsner Urquell 0,5 l</h3><span>Kaufland</span><b>19,90 Kč</b><i>23.9. - 29.9.</i></div>
# """

# OVERPASS = {
#     "elements": [
#         {
#             "type": "node",
#             "id": 1,
#             "lat": 50.08,
#             "lon": 14.43,
#             "tags": {
#                 "shop": "supermarket",
#                 "brand": "Albert",
#                 "name": "Albert Supermarket",
#                 "addr:street": "Vodičkova",
#                 "addr:housenumber": "10",
#                 "addr:city": "Praha",
#                 "addr:postcode": "11000",
#             },
#         },
#         {
#             "type": "way",
#             "id": 2,
#             "center": {"lat": 50.10, "lon": 14.50},
#             "tags": {
#                 "shop": "supermarket",
#                 "brand": "Lidl",
#                 "name": "Lidl",
#                 "addr:street": "Kolbenova",
#                 "addr:housenumber": "5",
#                 "addr:city": "Praha",
#             },
#         },
#         {
#             "type": "node",
#             "id": 3,
#             "lat": 50.09,
#             "lon": 14.45,
#             "tags": {"shop": "supermarket", "brand": "Penny", "name": "Penny"},
#         },
#         # pobočky v zahraničí se musí zahodit (Penny v DE je blíž než ta v Praze)
#         {
#             "type": "node",
#             "id": 4,
#             "lat": 50.088,
#             "lon": 14.422,
#             "tags": {"shop": "supermarket", "brand": "Penny", "addr:country": "DE"},
#         },
#         {
#             "type": "node",
#             "id": 5,
#             "lat": 48.2,
#             "lon": 16.37,
#             "tags": {"shop": "supermarket", "brand": "Albert"},
#         },
#     ]
# }


# @pytest.fixture(autouse=True)
# def auto_enable(enable_custom_integrations):
#     # bez pauz mezi požadavky (se zmrazeným časem by asyncio.sleep nikdy neskončil)
#     with (
#         patch("custom_components.akce_na_pivo.coordinator.REQUEST_DELAY", 0),
#         patch("custom_components.akce_na_pivo.coordinator.NOMINATIM_DELAY", 0),
#     ):
#         yield


# async def test_flow_and_setup(hass: HomeAssistant, aioclient_mock, hass_client, freezer) -> None:
#     freezer.move_to("2026-09-23 10:00:00+02:00")
#     hass.config.latitude, hass.config.longitude = 50.087, 14.421
#     aioclient_mock.get("https://www.kupi.cz/slevy/pivo", text=HTML)
#     aioclient_mock.get("https://www.kupi.cz/slevy/pivo?page=2", text="<html></html>")
#     aioclient_mock.get("https://www.kupi.cz/hledej?f=Moje+Pivo", text="<html></html>")
#     aioclient_mock.get("https://kompasslev.cz/produkty/pivo", text=KOMPAS_LIKE)
#     aioclient_mock.get("https://kompasslev.cz/produkty/pilsner-urquell", text=KOMPAS_PU)
#     # ostatní adresy (AkcniCeny, Cenito, neznámé značky) neexistují
#     aioclient_mock.get(
#         re.compile(r"^https://(www\.akcniceny\.cz|cenito\.cz|kompasslev\.cz)/"), status=404
#     )
#     aioclient_mock.post("https://overpass-api.de/api/interpreter", json=OVERPASS)
#     aioclient_mock.get(
#         "https://nominatim.openstreetmap.org/reverse",
#         json={
#             "address": {
#                 "road": "Seifertova",
#                 "house_number": "1",
#                 "city": "Praha",
#                 "postcode": "13000",
#             }
#         },
#     )
#     events = []
#     hass.bus.async_listen(EVENT_CHEAP_BEER, events.append)

#     result = await hass.config_entries.flow.async_init(
#         DOMAIN, context={"source": config_entries.SOURCE_USER}
#     )
#     assert result["type"] is FlowResultType.FORM
#     result = await hass.config_entries.flow.async_configure(
#         result["flow_id"], {"name": "Pivo", "country": "CZ"}
#     )
#     assert result["step_id"] == "settings"
#     result = await hass.config_entries.flow.async_configure(
#         result["flow_id"],
#         {
#             "brands": ["Pilsner Urquell", "Birell (nealko), Moje Pivo"],
#             "sources": ["kupi", "kompasslev", "akcniceny", "cenito"],
#             "custom_urls": "",
#             "update_time": "07:30:00",
#             "update_interval_hours": 0,
#             "top_count": 5,
#             "sort_by": "unit",
#             "max_distance_km": 15,
#             "require_nearby_store": False,
#             "price_alert": 18,
#             "include_upcoming": True,
#             "exclude_loyalty": False,
#             "exclude_nonalcoholic": False,
#             "max_pages": 3,
#         },
#     )
#     assert result["type"] is FlowResultType.CREATE_ENTRY
#     assert result["options"]["brands"] == ["Pilsner Urquell", "Birell (nealko)", "Moje Pivo"]
#     await hass.async_block_till_done()

#     cheapest = hass.states.get("sensor.pivo_nejlevnejsi_pivo") or hass.states.get(
#         "sensor.pivo_cheapest_beer"
#     )
#     assert cheapest is not None, [s.entity_id for s in hass.states.async_all()]
#     top = cheapest.attributes["offers"]
#     # Birell 14,90 Kč/0,5 l, Pilsner Urquell 24,90 Kč; Lidl multipack začíná až zítra
#     assert [o["shop"] for o in top] == ["Penny Market", "Kaufland", "Albert Hypermarket"]
#     assert top[1]["source"] == "kompasslev"
#     assert cheapest.attributes["source_names"]["kompasslev"] == "Kompas Slev"
#     assert float(cheapest.state) == 14.9
#     assert top[0]["address"] == "Seifertova 1, 13000 Praha"
#     assert top[0]["latitude"] == 50.09  # ne bližší Penny v DE
#     overpass_query = next(
#         c[2]["data"] for c in aioclient_mock.mock_calls if "overpass" in str(c[1])
#     )
#     assert 'area["ISO3166-1"="CZ"]' in overpass_query
#     assert top[2]["address"] == "Vodičkova 10, 11000 Praha"
#     assert top[2]["distance_km"] < 2
#     assert "Končí dnes" in top[0]["flags"]
#     assert cheapest.attributes["upcoming"][0]["shop"] == "Lidl"

#     rank1 = [s for s in hass.states.async_all("sensor") if s.attributes.get("rank") == 1]
#     assert rank1 and rank1[0].attributes["latitude"] == 50.09

#     binary = hass.states.async_all("binary_sensor")[0]
#     assert binary.state == "on"
#     assert len(events) == 1 and events[0].data["shop"] == "Penny Market"

#     count = [s for s in hass.states.async_all("sensor") if "matching_by_source" in s.attributes][0]
#     sources = count.attributes["sources"]
#     assert sources["kupi"]["offers"] == 3
#     assert sources["kompasslev"]["offers"] == 3
#     assert sources["cenito"]["offers"] == 0 and sources["cenito"]["errors"]

#     # karta dodávaná s integrací
#     client = await hass_client()
#     resp = await client.get("/akce_na_pivo/akce-na-pivo-card.js")
#     assert resp.status == 200
#     assert "akce-na-pivo-card" in await resp.text()

#     # telefon v zahraničí -> vzdálenosti se počítají od domova v ČR
#     coordinator = hass.config_entries.async_entries(DOMAIN)[0].runtime_data
#     hass.states.async_set("person.test", "not_home", {"latitude": 45.8, "longitude": 15.97})
#     with_entity = {**coordinator.options, "location_entity": "person.test"}
#     with patch.object(type(coordinator), "options", new=property(lambda self: with_entity)):
#         lat, lon, source = coordinator.current_location()
#     assert (lat, lon) == (50.087, 14.421) and "mimo CZ" in source

#     # opakovaná aktualizace nesmí znovu poslat stejnou událost
#     await hass.services.async_call(DOMAIN, "refresh", {}, blocking=True)
#     await hass.async_block_till_done()
#     assert len(events) == 1

#     # options flow
#     entry = hass.config_entries.async_entries(DOMAIN)[0]
#     result = await hass.config_entries.options.async_init(entry.entry_id)
#     assert result["type"] is FlowResultType.FORM
#     assert await hass.config_entries.async_unload(entry.entry_id)


# SK_HTML = """
# <div class="offer">
#   <h3>Zlatý Bažant 12% svetlý ležiak 0,5 l</h3>
#   <span class="shop">Kaufland</span>
#   <span class="price-old">1,19 €</span> <span class="price">0,69 €</span>
#   <span>platí od 22. 9. do 28. 9.</span>
# </div>
# <div class="offer">
#   <h3>Šariš 10 svetlé pivo 6 x 0,5 l</h3>
#   <span class="shop">COOP Jednota</span>
#   <span class="price">€ 4,49</span>
#   <span>22.9. - 28.9.</span>
# </div>
# """

# SK_OVERPASS = {
#     "elements": [
#         {
#             "type": "node",
#             "id": 10,
#             "lat": 48.15,
#             "lon": 17.11,
#             "tags": {
#                 "shop": "supermarket",
#                 "brand": "Kaufland",
#                 "addr:street": "Trnavská cesta",
#                 "addr:housenumber": "41",
#                 "addr:city": "Bratislava",
#                 "addr:postcode": "82108",
#             },
#         },
#         {
#             "type": "node",
#             "id": 11,
#             "lat": 48.14,
#             "lon": 17.10,
#             "tags": {
#                 "shop": "supermarket",
#                 "brand": "COOP Jednota",
#                 "name": "COOP Jednota",
#                 "addr:street": "Obchodná",
#                 "addr:housenumber": "1",
#                 "addr:city": "Bratislava",
#             },
#         },
#         # pobočka v ČR se pro Slovensko nepoužije
#         {
#             "type": "node",
#             "id": 12,
#             "lat": 48.16,
#             "lon": 17.10,
#             "tags": {"shop": "supermarket", "brand": "Kaufland", "addr:country": "CZ"},
#         },
#     ]
# }


# async def test_slovakia(hass: HomeAssistant, aioclient_mock, freezer) -> None:
#     freezer.move_to("2026-09-23 10:00:00+02:00")
#     hass.config.latitude, hass.config.longitude = 48.148, 17.107  # Bratislava
#     aioclient_mock.get(
#         "https://www.zlacnene.sk/akciovy-tovar/napoje-alkoholicke/pivo/", text=SK_HTML
#     )
#     aioclient_mock.get(re.compile(r"^https://"), status=404)
#     aioclient_mock.post("https://overpass-api.de/api/interpreter", json=SK_OVERPASS)

#     result = await hass.config_entries.flow.async_init(
#         DOMAIN, context={"source": config_entries.SOURCE_USER}
#     )
#     result = await hass.config_entries.flow.async_configure(
#         result["flow_id"], {"name": "Pivo SK", "country": "SK"}
#     )
#     assert result["step_id"] == "settings"
#     source_options = [o["value"] for o in result["data_schema"].schema["sources"].config["options"]]
#     assert "zlacnene" in source_options and "kupi" not in source_options
#     result = await hass.config_entries.flow.async_configure(
#         result["flow_id"],
#         {
#             "brands": ["Zlatý Bažant", "Šariš"],
#             "sources": source_options,
#             "update_time": "07:00:00",
#             "update_interval_hours": 0,
#             "top_count": 5,
#             "sort_by": "unit",
#             "max_distance_km": 15,
#             "require_nearby_store": False,
#             "price_alert": 0.7,
#             "include_upcoming": True,
#             "exclude_loyalty": False,
#             "exclude_nonalcoholic": False,
#             "max_pages": 1,
#         },
#     )
#     assert result["type"] is FlowResultType.CREATE_ENTRY
#     assert result["options"]["country"] == "SK"
#     await hass.async_block_till_done()

#     cheapest = hass.states.get("sensor.pivo_sk_cheapest_beer")
#     assert cheapest is not None
#     assert cheapest.attributes["unit_of_measurement"] == "EUR"
#     assert cheapest.attributes["currency_symbol"] == "€"
#     top = cheapest.attributes["offers"]
#     # 0,69 € za 0,5 l vs. multipack 4,49 € / 6 = 0,75 € za 0,5 l
#     assert [o["shop"] for o in top] == ["Kaufland", "COOP"]
#     assert top[0]["price"] == 0.69 and top[0]["old_price"] == 1.19
#     assert (top[0]["valid_from"], top[0]["valid_to"]) == ("2026-09-22", "2026-09-28")
#     assert top[0]["address"] == "Trnavská cesta 41, 82108 Bratislava"
#     assert top[1]["price"] == 4.49 and top[1]["price_per_half_liter"] == 0.75
#     assert all(o["currency"] == "EUR" for o in top)
#     assert "Pod limitem 0.7 €/0,5 l" in top[0]["flags"]

#     query = next(c[2]["data"] for c in aioclient_mock.mock_calls if "overpass" in str(c[1]))
#     assert 'area["ISO3166-1"="SK"]' in query



import json
from datetime import date

from akce_na_pivo.generic import dedupe, detect_chain, parse_generic
from akce_na_pivo.kupi import parse_offers

from .test_kupi import HTML as KUPI_HTML

TODAY = date(2026, 9, 23)

KOMPAS_LIKE = """
<html><body>
<nav><a href="/letaky/lidl">Lidl</a> <a href="/letaky/kaufland">Kaufland</a></nav>
<div class="products">
  <div class="product-card">
    <a href="/produkt/kozel-11"><img src="/img/kozel.jpg" alt="Velkopopovický Kozel 11 0,5 l"></a>
    <h3 class="product-card__title">Velkopopovický Kozel 11 světlý ležák 0,5 l</h3>
    <div class="product-card__store"><img src="/logos/kaufland.svg" alt="Kaufland"></div>
    <div class="price"><span class="price__old">22,90 Kč</span> <strong>13,90 Kč</strong></div>
    <div class="validity">23.9. - 29.9.</div>
  </div>
  <div class="product-card">
    <h3 class="product-card__title">Gambrinus Originál 10 plech 6 x 0,5 l</h3>
    <div class="product-card__store">Lidl</div>
    <div class="price">-30 % <strong>89,90 Kč</strong></div>
    <small>59,93 Kč / 1 l</small>
    <div class="validity">platí do 27. 9.</div>
    <p>Jen s aplikací Lidl Plus</p>
  </div>
</div>
</body></html>
"""


def test_html_cards():
    offers = parse_generic(KOMPAS_LIKE, "https://kompasslev.cz/produkty/pivo", TODAY, "kompasslev")
    assert len(offers) == 2, offers
    kozel, gambrinus = sorted(offers, key=lambda o: o["product"], reverse=True)
    assert kozel["product"] == "Velkopopovický Kozel 11 světlý ležák 0,5 l"
    assert kozel["shop"] == "Kaufland"
    assert kozel["price"] == 13.9
    assert kozel["old_price"] == 22.9
    assert kozel["discount_percent"] == 39
    assert kozel["price_per_half_liter"] == 13.9
    assert kozel["valid_to"] == "2026-09-29"
    assert kozel["url"] == "https://kompasslev.cz/produkt/kozel-11"
    assert kozel["image"] == "https://kompasslev.cz/img/kozel.jpg"
    assert kozel["source"] == "kompasslev"

    assert gambrinus["shop"] == "Lidl"
    assert gambrinus["price"] == 89.9
    assert gambrinus["pieces"] == 6
    assert gambrinus["price_per_half_liter"] == 14.98
    assert gambrinus["discount_percent"] == 30
    assert gambrinus["loyalty"]
    assert gambrinus["valid_to"] == "2026-09-27"


def test_next_data():
    data = {
        "props": {
            "pageProps": {
                "offers": [
                    {
                        "productName": "Pilsner Urquell 0,5 l",
                        "actionPrice": 21.9,
                        "originalPrice": 32.9,
                        "shop": {"name": "Albert Hypermarket"},
                        "validFrom": "2026-09-23",
                        "validTo": "2026-09-29",
                        "slug": "/akce/pilsner",
                    },
                    {"name": "Menu", "price": None},
                ]
            }
        }
    }
    html = f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(data)}</script>'
    offers = parse_generic(html, "https://cenito.cz/hledat?q=pivo", TODAY, "cenito")
    assert len(offers) == 1
    offer = offers[0]
    assert offer["shop"] == "Albert Hypermarket" and offer["chain"] == "albert"
    assert offer["price"] == 21.9 and offer["old_price"] == 32.9
    assert offer["valid_to"] == "2026-09-29"
    assert offer["url"] == "https://cenito.cz/akce/pilsner"


def test_jsonld_itemlist_with_store_in_url():
    data = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "item": {
                    "@type": "Product",
                    "name": "Radegast Rázná 10 0,5 l",
                    "offers": {"@type": "Offer", "price": "11.90", "priceValidUntil": "2026-09-27"},
                },
            }
        ],
    }
    html = f'<script type="application/ld+json">{json.dumps(data)}</script>'
    offers = parse_generic(
        html, "https://kompasslev.cz/produkty/pivo?store=penny-market", TODAY, "kompasslev"
    )
    assert len(offers) == 1
    assert offers[0]["shop"] == "Penny" and offers[0]["price"] == 11.9


def test_dedupe_across_sources():
    kupi = parse_offers(KUPI_HTML, "https://www.kupi.cz/slevy/pivo", TODAY)
    other = [dict(kupi[0], id="x", source="kompasslev", sources=["kompasslev"])]
    merged = dedupe(kupi + other)
    assert len(merged) == len(kupi)
    assert merged[0]["sources"] == ["kupi", "kompasslev"]


def test_detect_chain():
    assert detect_chain("coop-diskont") == "COOP"
    assert detect_chain("Penny Market") == "Penny"
    assert detect_chain("Normální pivo") is None
    assert detect_chain("TRAVEL FREE") == "Travel Free"


def test_foreign_currency_is_skipped():
    data = [
        {"name": "Zlatý Bažant 0,5 l", "price": 0.99, "currency": "EUR", "shop": "Lidl"},
        {"name": "Kozel 11 0,5 l", "price": 15.9, "currency": "CZK", "shop": "Lidl"},
    ]
    html = f'<script type="application/json">{json.dumps({"items": data})}</script>'
    offers = parse_generic(html, "https://example.cz/pivo", TODAY, "custom")
    assert [o["product"] for o in offers] == ["Kozel 11 0,5 l"]

    ld = {
        "@type": "Product",
        "name": "Pilsner Urquell",
        "offers": {
            "@type": "Offer",
            "price": "1.49",
            "priceCurrency": "EUR",
            "seller": {"name": "Tesco"},
        },
    }
    html = f'<script type="application/ld+json">{json.dumps(ld)}</script>'
    assert parse_generic(html, "https://example.sk/pivo", TODAY, "custom") == []


def test_slovak_prices_in_euro():
    html = """
    <div class="item"><h2>Corgoň 10% svetlé pivo 0,5 l</h2><p>Lidl</p>
      <del>0,89 €</del> <b>0,55 €</b> <small>1,10 €/l</small> <p>zajtra končí</p></div>
    <div class="item"><h2>Kozel 11 0,5 l</h2><p>Billa</p><b>19,90 Kč</b></div>
    """
    offers = parse_generic(html, "https://www.kimbino.sk/produkty/pivo/", TODAY, "kimbino", "SK")
    assert len(offers) == 1  # cena v Kč se na Slovensku nebere
    offer = offers[0]
    assert offer["shop"] == "Lidl" and offer["currency"] == "EUR"
    assert offer["price"] == 0.55 and offer["old_price"] == 0.89
    assert offer["valid_to"] == "2026-09-24"
    # a naopak – v Česku se euro nebere
    assert [o["shop"] for o in parse_generic(html, "https://x.cz", TODAY, "custom", "CZ")] == [
        "Billa"
    ]
