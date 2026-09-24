# 🍺 Akcie na pivo – Home Assistant

Integrácia pre Home Assistant, ktorá každý deň (alebo v čase, ktorý si nastavíte) zistí,
**kde je najlacnejšie pivo v akcii**, nájde **najbližšiu predajňu** daného obchodu k vášmu
domovu alebo k polohe vášho telefónu a ukáže ju **na mape**. Súčasťou je samostatná
Lovelace karta `akce-na-pivo-card`.

- **Česko 🇨🇿 alebo Slovensko 🇸🇰**: krajinu vyberiete pri pridaní integrácie.
- Ceny z viacerých webov s letákovými akciami (Albert, Billa, Globus, Kaufland, Lidl, Penny, Tesco,
  Makro, Norma, COOP, JIP, Hruška, na Slovensku COOP Jednota, Terno, Fresh, Kraj, Metro…).
  Rovnaká akcia nájdená na viacerých weboch sa zlúči.
- Predajne, adresy a otváracie hodiny z OpenStreetMap (Overpass + Nominatim)

## Česko, alebo Slovensko

Pri pridaní integrácie si najskôr zvolíte **krajinu**:

| | 🇨🇿 Česko | 🇸🇰 Slovensko |
|---|---|---|
| Weby s akciami | Kupi.cz, Kompas Slev, AkcniCeny.cz, Cenito | Zlacnene.sk, Kimbino.sk, Letakomat.sk, KdeJeAkcia.sk, Kompas Zliav, Kupino.sk, AkčnéLetáky.sk, Promotheus.sk |
| Mena senzorov | CZK (Kč) | EUR (€) |
| Predvolené značky | Pilsner Urquell, Kozel, Gambrinus | Zlatý Bažant, Šariš, Corgoň |
| Predvolený limit za 0,5 l | 15 Kč | 0,70 € |

- Predajne z OpenStreetMap sa načítavajú **iba vnútri hraníc zvolenej krajiny** (Overpass
  `area["ISO3166-1"="CZ"/"SK"]`). Pri hraniciach sa tak neponúkne predajňa v susednej krajine.
- Keď je sledovaný telefón alebo osoba mimo zvolenej krajiny, vzdialenosti sa počítajú od domova HA.
- Ponuky v inej mene (Kč na Slovensku, € v Česku) sa zahodia.
- **Chcete obe krajiny?** Pridajte integráciu dvakrát – raz pre Česko a raz pre Slovensko.
  Každá bude mať vlastné senzory aj kartu. Keď bývate blízko hraníc, nastavte pri slovenskej
  variante dostatočnú **vzdialenosť predajní** (až 50 km). Obchody sa potom hľadajú na Slovensku
  v tomto okruhu od vášho domova v ČR (alebo naopak).
- Slovenské značky v zozname: Zlatý Bažant, Šariš, Corgoň, Topvar, Smädný mních, Kelt, Steiger,
  Martiner, Urpiner, Popper (a samozrejme české značky alebo vlastné).

## Zdroje akcií

| Zdroj | Ako sa číta | Východiskové adresy |
|---|---|---|
| **Kupi.cz** | vlastný parser stránok kupi.cz + JSON-LD | `/slevy/pivo` (stránkovanie), `/sleva/pivo-<značka>`, `/hledej?f=<značka>` |
| **Kompas Slev** | všeobecný parser | `kompasslev.cz/produkty/pivo`, `kompasslev.cz/produkty/<značka>` |
| **AkcniCeny.cz** | všeobecný parser | vyhľadávanie `pivo` / `<značka>` |
| **Cenito** | všeobecný parser | vyhľadávanie `pivo` / `<značka>` |
| 🇸🇰 **Zlacnene.sk** | všeobecný parser | `/akciovy-tovar/napoje-alkoholicke/pivo/`, `/akciovy-tovar/znacka-<značka>/` |
| 🇸🇰 **Kimbino.sk** | všeobecný parser | `/produkty/pivo/`, `/produkty/<značka>/` |
| 🇸🇰 **Letakomat.sk** | všeobecný parser | `/hladat/?q=pivo`, `/hladat/?q=<značka>` |
| 🇸🇰 **KdeJeAkcia.sk** | všeobecný parser | `/kde-je-pivo-v-akcii`, `/kde-je-<značka>-v-akcii` |
| 🇸🇰 **Kompas Zliav** | všeobecný parser | `kompaszliav.sk/produkty/pivo`, `/produkty/<značka>` |
| 🇸🇰 **Kupino.sk** | všeobecný parser | `/akcia/pivo`, `/akcia/<značka>` |
| 🇸🇰 **AkčnéLetáky.sk** | všeobecný parser | `/akcie/Pivo`, `/akcie/<značka>` |
| 🇸🇰 **Promotheus.sk** | všeobecný parser | `promotheus.sk/pivo`, `promotheus.sk/<značka>` |
| **Vlastná URL** | všeobecný parser | ľubovoľné stránky zadané v nastavení |

Zdroje zapínate a vypínate v nastaveniach integrácie. **Všeobecný parser** skúša postupne:
1. štruktúrované dáta schema.org (JSON-LD `Product` / `Offer` / `ItemList`),
2. JSON vložený do stránky (Next.js `__NEXT_DATA__` a iný `application/json`),
3. heuristiku nad HTML: nájde najmenší blok stránky, v ktorom je cena (€ na Slovensku alebo Kč v Česku) a názov reťazca,
   a z neho vezme názov produktu, starú cenu, zľavu, platnosť a odkaz.

> ⚠️ Weby sa pri vývoji nedali priamo otvoriť, takže parser nebol testovaný na ich skutočnom
> obsahu. Slovenské adresy a adresa Kompas Slev sú overené cez vyhľadávač. Adresy
> AkcniCeny.cz a Cenito sú odhad. Keď niektorý zdroj nič nevracia, pozrite sa na atribút
> `sources` senzora **Počet akcií**. Ukazuje pre každý zdroj počet akcií, funkčnú URL a chyby.
> Správnu adresu potom zadajte do **Vlastné URL**. Adresa, ktorá vráti 404, sa týždeň neskúša.

**Vlastná URL** (jedna na riadok) môže obsahovať zástupné znaky:
- `{query}` = názov značky (`Pilsner+Urquell`), pri „všetkých pivách“ `pivo`
- `{slug}` = značka v tvare `pilsner-urquell` alebo `zlaty-bazant`

```text
https://kompaszliav.sk/produkty/pivo?store=kaufland
https://www.nejaky-web.sk/hladat?q={query}
```

## Čo dokáže

| Funkcia | Popis |
|---|---|
| Výber značiek | Výber zo zoznamu (Zlatý Bažant, Šariš, Corgoň, Urpiner, Pilsner Urquell, Kozel, Radegast, Staropramen, Budvar…), **vlastná značka** (napíšte ju a potvrďte Enterom, dá sa zadať aj viac značiek oddelených čiarkou), alebo **„Všetky pivá v akcii“** |
| Čas kontroly | Denná kontrola v zadaný čas, voliteľne navyše každých N hodín. Kedykoľvek ručne: tlačidlo **Aktualizovať akcie** alebo služba `akce_na_pivo.refresh` |
| Poloha | Domov HA, alebo entita `person` / `device_tracker` / `zone` (GPS telefónu). Keď sa pohnete o viac ako 2 km, najbližšie predajne sa prepočítajú |
| TOP N | Počet zobrazených najlacnejších ponúk volíte v nastaveniach (1–10, predvolených 5) |
| Mapa a adresa | Pri každej ponuke je najbližšia predajňa: adresa, vzdialenosť, GPS, otváracie hodiny a odkazy na Mapy.com a navigáciu |

### Ďalšie ukazovatele, že je pivo naozaj lacné

- **Cena za 0,5 l**: prepočet aj pri multipackoch (`8 × 0,5 l`), plechovkách 0,33 l a fľašiach / PET 1,5 l. Podľa toho sa štandardne radí.
- **Najlacnejšie za posledných 120 dní**: integrácia si ukladá históriu cien a označí ponuku, ktorá je na historickom minime.
- **Lacnejšie než priemer**: o koľko €/0,5 l je ponuka lacnejšia než priemer všetkých akcií na rovnakú značku.
- **Zľava ≥ 30 %** a odhad pôvodnej ceny.
- **Pod limitom**: nastavíte si cenu za 0,5 l, dostanete udalosť `akce_na_pivo_levne_pivo` a zapne sa binárny senzor.
- **Končí dnes / zajtra**, **Platí od…** (pripravované akcie z nových letákov), **Len s vernostnou kartou** (Lidl Plus, Clubcard, Moja Billa…), **Multipack**.
- Filtre: vynechať nealko, vynechať akcie iba s kartou, zobraziť iba obchody s predajňou v okolí (limit km).

## Inštalácia integrácie

### HACS
1. HACS → Integrácie → ⋮ → *Vlastné repozitáre* → zadajte URL vášho forku repozitára, kategória *Integrácia*.
2. Nainštalujte **Akcie na pivo** a reštartujte Home Assistant.

### Ručne
Skopírujte adresár `custom_components/akce_na_pivo` do vášho `/config/custom_components/` a reštartujte HA.

Potom: **Nastavenia → Zariadenia a služby → Pridať integráciu → Akcie na pivo**.
Všetko sa dá neskôr zmeniť cez **Konfigurovať**.

## Karty (súčasť custom component)

Integrácia obsahuje dve Lovelace karty v priečinku `frontend/`:

### 1. Karta Akcie na pivo (`custom:akce-na-pivo-card`)
Základná karta s interaktívnou Leaflet mapou a prehľadom obchodov.

```yaml
type: custom:akce-na-pivo-card
entity: sensor.akce_na_pivo_nejlevnejsi_pivo
title: 🍺 Najlacnejšie pivo
count: 5            # koľko ponúk zobraziť (1–10)
sort: ""            # "" = podľa integrácie, alebo unit | price | distance
show_map: true
map_height: 240
show_images: true
show_address: true
show_flags: true
show_source: true   # štítok, z ktorého webu akcia pochádza
show_upcoming: false
```

### 2. Pivná karta (`custom:pivna-karta`)
Dizajnová karta na pivnom pozadí s penou, stúpajúcimi bublinkami, prepínaním značiek, hrdinským zobrazením „Dnes choď do“, mapou predajne a rebríčkom.

```yaml
type: custom:pivna-karta
entity: sensor.akce_na_pivo_nejlevnejsi_pivo
title: Kam na pivo
count: 5
show_brands: true
show_map: true
map_height: 180
show_list: true
bubbles: true
```

Obe karty integrácia automaticky zaregistruje vo frontende. Keby sa karta v ponuke neobjavila, pridajte zdroj ručne:
**Nastavenia → Ovládacie panely → ⋮ → Zdroje** → URL `/akce_na_pivo/pivna-karta.js` (alebo `/config/www/pivna-karta.js`), typ *JavaScript modul*.


## Entity

| Entita | Stav | Poznámka |
|---|---|---|
| `sensor.*_nejlevnejsi_pivo` | cena za 0,5 l (alebo za balenie) | atribút `offers` = TOP N, `upcoming`, `brands`, `location`; zdroj dát pre kartu |
| `sensor.*_nejlevnejsi_pivo_za_0_5_l` | € (Kč)/0,5 l | vhodné do grafu histórie |
| `sensor.*_pivo_1` … `_pivo_N` | cena balenia | majú `latitude`/`longitude`, takže ich zobrazí aj štandardná karta Mapa |
| `sensor.*_<značka>` | cena | najlacnejšia akcia každej vybranej značky |
| `sensor.*_kam_po_pivo` | **názov obchodu**, napr. `Kaufland` | kam ísť po celkovo najlacnejšie pivo; atribúty `address`, `distance_km`, `navigate_url`, `product`, `price` a pripravený súhrn `summary` („Kaufland, Trnavská cesta 41, Bratislava (1,2 km): Zlatý Bažant 12 0,5 l za 0,79 € – 0,79 €/0,5 l“) |
| `sensor.*_kam_po_<značka>` | **názov obchodu** | kam ísť po konkrétnu vybranú značku |
| `binary_sensor.*_levne_pivo_pod_limitem` | on/off | je v akcii pivo pod limitom? |
| `button.*_aktualizovat_akce` | – | okamžitá aktualizácia |
| `sensor.*_pocet_akci` | počet | diagnostika: stav každého zdroja (akcie, funkčné URL, chyby) |

### Príklad automatizácie – každé ráno, kam ísť na pivo

```yaml
automation:
  - alias: Kam po pivo
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: notify.mobile_app_telefon
        data:
          title: "🍺 Dnes choď do: {{ states('sensor.akce_na_pivo_kam_po_pivo') }}"
          message: "{{ state_attr('sensor.akce_na_pivo_kam_po_pivo', 'summary') }}"
          data:
            url: "{{ state_attr('sensor.akce_na_pivo_kam_po_pivo', 'navigate_url') }}"
```

### Príklad automatizácie – upozornenie pri cene pod limitom

```yaml
automation:
  - alias: Lacné pivo v akcii
    trigger:
      - platform: event
        event_type: akce_na_pivo_levne_pivo
    action:
      - service: notify.mobile_app_telefon
        data:
          title: "🍺 {{ trigger.event.data.product }}"
          message: >
            {{ trigger.event.data.shop }} za {{ trigger.event.data.price }} {{ trigger.event.data.currency }}
            ({{ trigger.event.data.price_per_half_liter }} {{ trigger.event.data.currency }}/0,5 l),
            {{ trigger.event.data.address }} – {{ trigger.event.data.distance_km }} km,
            platí do {{ trigger.event.data.valid_to }}
```

### Štandardná karta Mapa

```yaml
type: map
entities:
  - sensor.akce_na_pivo_pivo_1
  - sensor.akce_na_pivo_pivo_2
  - sensor.akce_na_pivo_pivo_3
  - zone.home
```

## Poznámky

- Integrácia sťahuje verejné stránky šetrne: zopár stránok raz denne, s pauzami medzi požiadavkami.
  Chyba jedného zdroja neovplyvní ostatné. Keď kupi.cz zmení vzhľad stránok, bude potrebné upraviť
  `kupi.py`. Ostatné weby číta všeobecný parser `generic.py`.
- XML feed kupi.cz je určený pre obchodných partnerov, nie pre verejné použitie, preto ho integrácia nepoužíva.
- Kupi.cz uvádza akcie za celý reťazec. Pobočka na mape je **najbližšia predajňa daného reťazca**,
  konkrétna akcia sa tam ale môže líšiť (napríklad hypermarket vs. supermarket).
- Predajne z OpenStreetMap sa ukladajú do vyrovnávacej pamäte na 7 dní a obnovia sa pri zmene polohy.

## Vývoj a testovanie

```bash
pip install beautifulsoup4 pytest
pytest tests/test_kupi.py tests/test_generic.py   # parsery bez Home Assistantu
pip install pytest-homeassistant-custom-component
pytest tests                                      # vrátane testu integrácie
```
