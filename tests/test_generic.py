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
