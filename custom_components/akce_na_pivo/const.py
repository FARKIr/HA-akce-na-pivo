"""Constants for the Akce na pivo integration."""

from __future__ import annotations

DOMAIN = "akce_na_pivo"
NAME = "Akce na pivo"

PLATFORMS = ["sensor", "binary_sensor", "button"]

# Config / options keys
CONF_BRANDS = "brands"
CONF_LOCATION_ENTITY = "location_entity"
CONF_UPDATE_TIME = "update_time"
CONF_UPDATE_INTERVAL_HOURS = "update_interval_hours"
CONF_TOP_COUNT = "top_count"
CONF_SORT_BY = "sort_by"
CONF_MAX_DISTANCE_KM = "max_distance_km"
CONF_REQUIRE_NEARBY_STORE = "require_nearby_store"
CONF_EXCLUDE_LOYALTY = "exclude_loyalty"
CONF_INCLUDE_UPCOMING = "include_upcoming"
CONF_PRICE_ALERT = "price_alert"
CONF_EXCLUDE_NONALCOHOLIC = "exclude_nonalcoholic"
CONF_MAX_PAGES = "max_pages"

SORT_UNIT = "unit"  # cena za 0,5 l
SORT_PRICE = "price"  # cena za balení
SORT_DISTANCE = "distance"  # nejbližší obchod, pak cena
SORT_OPTIONS = [SORT_UNIT, SORT_PRICE, SORT_DISTANCE]

ALL_BRANDS = "__all__"

DEFAULT_BRANDS = ["Pilsner Urquell", "Kozel", "Gambrinus"]
DEFAULT_UPDATE_TIME = "07:00:00"
DEFAULT_UPDATE_INTERVAL_HOURS = 0
DEFAULT_TOP_COUNT = 5
DEFAULT_SORT_BY = SORT_UNIT
DEFAULT_MAX_DISTANCE_KM = 15
DEFAULT_REQUIRE_NEARBY_STORE = False
DEFAULT_EXCLUDE_LOYALTY = False
DEFAULT_INCLUDE_UPCOMING = True
DEFAULT_PRICE_ALERT = 15.0  # Kč za 0,5 l
DEFAULT_EXCLUDE_NONALCOHOLIC = False
DEFAULT_MAX_PAGES = 6

MAX_TOP_COUNT = 10

# Známé značky: zobrazovaný název -> (aliasy pro hledání v názvu produktu, slug na kupi.cz)
KNOWN_BRANDS: dict[str, tuple[tuple[str, ...], str]] = {
    "Pilsner Urquell": (("pilsner urquell", "plzensky prazdroj"), "pivo-pilsner-urquell"),
    "Gambrinus": (("gambrinus",), "pivo-gambrinus"),
    "Kozel": (("kozel",), "pivo-velkopopovicky-kozel"),
    "Radegast": (("radegast",), "pivo-radegast"),
    "Staropramen": (("staropramen",), "pivo-staropramen"),
    "Budweiser Budvar": (("budvar", "budweiser"), "pivo-budweiser-budvar"),
    "Bernard": (("bernard",), "pivo-bernard"),
    "Krušovice": (("krusovice",), "pivo-krusovice"),
    "Starobrno": (("starobrno",), "pivo-starobrno"),
    "Braník": (("branik",), "pivo-branik"),
    "Ostravar": (("ostravar",), "pivo-ostravar"),
    "Svijany": (("svijan",), "pivo-svijany"),
    "Rohozec": (("rohozec", "skalak"), "pivo-rohozec"),
    "Primátor": (("primator",), "pivo-primator"),
    "Zubr": (("zubr",), "pivo-zubr"),
    "Holba": (("holba",), "pivo-holba"),
    "Lobkowicz": (("lobkowicz",), "pivo-lobkowicz"),
    "Březňák": (("breznak",), "pivo-breznak"),
    "Samson": (("samson",), "pivo-samson"),
    "Radler": (("radler",), "pivo-radler"),
    "Birell (nealko)": (("birell",), "pivo-birell"),
    "Heineken": (("heineken",), "pivo-heineken"),
    "Plzeň (vše z Prazdroje)": (("pilsner", "gambrinus", "kozel", "radegast"), ""),
}

# Slova, podle kterých poznáme nealko pivo (porovnává se s textem bez diakritiky)
NONALCOHOLIC_WORDS = ("nealko", "birell", "alkohol free", "alcohol free", "bezalkohol")

# Názvy obchodních řetězců, jak je uvádí kupi.cz -> klíč pro vyhledání v OpenStreetMap
CHAIN_ALIASES: dict[str, tuple[str, ...]] = {
    "albert": ("albert",),
    "billa": ("billa",),
    "globus": ("globus",),
    "kaufland": ("kaufland",),
    "lidl": ("lidl",),
    "penny": ("penny",),
    "tesco": ("tesco",),
    "makro": ("makro",),
    "norma": ("norma",),
    "coop": ("coop", "jednota", "tempo", "terno"),
    "tamda": ("tamda",),
    "flop": ("flop",),
    "hruska": ("hruska",),
    "terno": ("terno",),
    "trefa": ("trefa",),
    "ratio": ("ratio",),
    "brnenka": ("brnenka",),
    "cba": ("cba",),
    "zabka": ("zabka",),
    "tesco express": ("tesco",),
    "potraviny cz": ("potraviny cz",),
    "enapo": ("enapo",),
    "rohlik": ("rohlik",),
    "kosik": ("kosik",),
    "jip": ("jip",),
    "travel free": ("travel free",),
    "tuty": ("tuty",),
}

# Zobrazované názvy řetězců – podle nich obecný parser pozná obchod v textu stránky
CHAIN_NAMES: dict[str, str] = {
    "albert": "Albert",
    "billa": "Billa",
    "globus": "Globus",
    "kaufland": "Kaufland",
    "lidl": "Lidl",
    "penny": "Penny",
    "tesco": "Tesco",
    "makro": "Makro",
    "norma": "Norma",
    "coop": "COOP",
    "tamda": "Tamda",
    "flop": "Flop",
    "hruska": "Hruška",
    "terno": "Terno",
    "trefa": "Trefa",
    "ratio": "Ratio",
    "brnenka": "Brněnka",
    "cba": "CBA",
    "zabka": "Žabka",
    "jip": "JIP",
    "travel free": "Travel Free",
    "tuty": "COOP Tuty",
    "rohlik": "Rohlik.cz",
    "kosik": "Košík.cz",
}

# Online obchody – nemají kamennou pobočku
ONLINE_SHOPS = ("rohlik", "kosik", "tesco online", "albert online", "online")

# Zdroje akcí. URL šablony: {query} = hledaný text, {slug} = značka ve tvaru "pilsner-urquell".
# Adresy mimo kupi.cz nešlo při vývoji ověřit – lze je přepsat v nastavení (vlastní URL).
CONF_SOURCES = "sources"
CONF_CUSTOM_URLS = "custom_urls"
SOURCE_KUPI = "kupi"
SOURCE_KOMPASSLEV = "kompasslev"
SOURCE_AKCNICENY = "akcniceny"
SOURCE_CENITO = "cenito"
SOURCE_CUSTOM = "custom"

SOURCES: dict[str, dict] = {
    SOURCE_KUPI: {
        "name": "Kupi.cz",
        "listing": ("https://www.kupi.cz/slevy/pivo",),
        "brand": (),
        "pages": True,
    },
    SOURCE_KOMPASSLEV: {
        "name": "Kompas Slev",
        "listing": ("https://kompasslev.cz/produkty/pivo", "https://kompasslev.cz/pivo"),
        "brand": ("https://kompasslev.cz/produkty/{slug}",),
        "pages": False,
    },
    SOURCE_AKCNICENY: {
        "name": "AkcniCeny.cz",
        "listing": (
            "https://www.akcniceny.cz/hledat/?q=pivo",
            "https://www.akcniceny.cz/vyhledavani/?q=pivo",
        ),
        "brand": (
            "https://www.akcniceny.cz/hledat/?q={query}",
            "https://www.akcniceny.cz/vyhledavani/?q={query}",
        ),
        "pages": False,
    },
    SOURCE_CENITO: {
        "name": "Cenito",
        "listing": (
            "https://cenito.cz/hledat?q=pivo",
            "https://cenito.cz/vyhledavani?q=pivo",
            "https://cenito.cz/search?q=pivo",
        ),
        "brand": (
            "https://cenito.cz/hledat?q={query}",
            "https://cenito.cz/vyhledavani?q={query}",
            "https://cenito.cz/search?q={query}",
        ),
        "pages": False,
    },
}
DEFAULT_SOURCES = [SOURCE_KUPI, SOURCE_KOMPASSLEV, SOURCE_AKCNICENY, SOURCE_CENITO]

KUPI_BASE_URL = "https://www.kupi.cz"
KUPI_SEARCH_URL = "https://www.kupi.cz/hledej?f={query}"
KUPI_PRODUCT_URL = "https://www.kupi.cz/sleva/{slug}"

# Integrace pracuje jen s Českou republikou
COUNTRY_CODE = "CZ"
CURRENCY_CODE = "CZK"
# hrubý obdélník kolem ČR (lat_min, lat_max, lon_min, lon_max); přesnou hranici řeší Overpass area
CZ_BBOX = (48.55, 51.06, 12.09, 18.86)

OVERPASS_URLS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
OSM_USER_AGENT = "HomeAssistant-AkceNaPivo/1.0 (+https://github.com/joshuaaaaa/HA-akce-na-pivo)"

STORE_CACHE_DAYS = 7
RELOCATE_DISTANCE_KM = 2.0
HISTORY_DAYS = 120

EVENT_CHEAP_BEER = f"{DOMAIN}_levne_pivo"
SERVICE_REFRESH = "refresh"
