"""Dohledání nejbližších poboček obchodních řetězců přes OpenStreetMap."""

from __future__ import annotations

import asyncio
import logging
from math import asin, cos, radians, sin, sqrt
from typing import Any

import aiohttp

from .const import CHAIN_ALIASES, NOMINATIM_REVERSE_URL, OSM_USER_AGENT, OVERPASS_URLS
from .kupi import normalize

_LOGGER = logging.getLogger(__name__)

SHOP_TYPES = "supermarket|convenience|department_store|wholesale|beverages|alcohol|general|mall"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * asin(sqrt(a))


def format_address(tags: dict[str, str]) -> str:
    street = tags.get("addr:street") or tags.get("addr:place") or ""
    number = tags.get("addr:housenumber") or tags.get("addr:conscriptionnumber") or ""
    city = tags.get("addr:city") or ""
    postcode = tags.get("addr:postcode") or ""
    first = f"{street} {number}".strip()
    second = f"{postcode} {city}".strip()
    return ", ".join(part for part in (first, second) if part)


def store_chain(tags: dict[str, str]) -> str | None:
    text = normalize(" ".join(tags.get(key, "") for key in ("brand", "name", "operator")))
    for key in sorted(CHAIN_ALIASES, key=len, reverse=True):
        if any(alias in text for alias in CHAIN_ALIASES[key]):
            return key
    return None


async def fetch_stores(
    session: aiohttp.ClientSession, lat: float, lon: float, radius_km: float
) -> list[dict[str, Any]]:
    """Stáhne obchody v okolí (jedním dotazem) a přiřadí je k řetězcům."""
    radius_m = int(max(1.0, radius_km) * 1000)
    query = (
        "[out:json][timeout:40];"
        f'nwr["shop"~"^({SHOP_TYPES})$"](around:{radius_m},{lat},{lon});'
        "out center tags;"
    )
    last_error: Exception | None = None
    for url in OVERPASS_URLS:
        try:
            async with session.post(
                url,
                data={"data": query},
                headers={"User-Agent": OSM_USER_AGENT},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                resp.raise_for_status()
                payload = await resp.json(content_type=None)
            break
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
            last_error = err
            _LOGGER.debug("Overpass %s selhal: %s", url, err)
    else:
        raise RuntimeError(f"OpenStreetMap (Overpass) nedostupné: {last_error}")

    stores: list[dict[str, Any]] = []
    for element in payload.get("elements", []):
        tags = element.get("tags") or {}
        chain = store_chain(tags)
        if not chain:
            continue
        s_lat = element.get("lat") or (element.get("center") or {}).get("lat")
        s_lon = element.get("lon") or (element.get("center") or {}).get("lon")
        if s_lat is None or s_lon is None:
            continue
        stores.append(
            {
                "chain": chain,
                "name": tags.get("name") or tags.get("brand") or chain.title(),
                "address": format_address(tags),
                "opening_hours": tags.get("opening_hours", ""),
                "latitude": float(s_lat),
                "longitude": float(s_lon),
                "osm_id": f"{element.get('type')}/{element.get('id')}",
            }
        )
    return stores


async def reverse_geocode(session: aiohttp.ClientSession, lat: float, lon: float) -> str:
    """Adresa z Nominatimu pro pobočky, které v OSM adresu nemají."""
    try:
        async with session.get(
            NOMINATIM_REVERSE_URL,
            params={
                "format": "jsonv2",
                "lat": lat,
                "lon": lon,
                "zoom": 18,
                "accept-language": "cs",
            },
            headers={"User-Agent": OSM_USER_AGENT},
            timeout=aiohttp.ClientTimeout(total=20),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
        _LOGGER.debug("Nominatim selhal: %s", err)
        return ""
    addr = data.get("address") or {}
    street = addr.get("road") or addr.get("pedestrian") or addr.get("suburb") or ""
    number = addr.get("house_number") or ""
    city = addr.get("city") or addr.get("town") or addr.get("village") or ""
    first = f"{street} {number}".strip()
    second = f"{addr.get('postcode', '')} {city}".strip()
    return ", ".join(part for part in (first, second) if part) or data.get("display_name", "")


def nearest_store(
    stores: list[dict[str, Any]], chain: str, lat: float, lon: float
) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    for store in stores:
        if store["chain"] != chain and not (
            chain in CHAIN_ALIASES and store["chain"] in CHAIN_ALIASES[chain]
        ):
            continue
        distance = haversine_km(lat, lon, store["latitude"], store["longitude"])
        if best is None or distance < best["distance_km"]:
            best = {**store, "distance_km": round(distance, 2)}
    return best
