# 🍺 Akce na pivo – Home Assistant

Integrace pro Home Assistant, která každý den (nebo v čase, který si nastavíte) zjistí,
**kde je nejlevnější pivo v akci**, najde **nejbližší pobočku** daného obchodu k vašemu
domovu nebo k poloze vašeho telefonu a ukáže ji **na mapě**. Součástí je samostatná
Lovelace karta `akce-na-pivo-card`.

- Ceny z [kupi.cz](https://www.kupi.cz/slevy/pivo), tedy z letáků Albert, Billa, Globus, Kaufland,
  Lidl, Penny, Tesco, Makro, Norma, COOP…
- Pobočky, adresy a otevírací doby z OpenStreetMap (Overpass + Nominatim)

## Co umí

| Funkce | Popis |
|---|---|
| Výběr značek | Výběr ze seznamu (Pilsner Urquell, Kozel, Gambrinus, Radegast, Staropramen, Budvar, Bernard, Svijany…), **vlastní značka** (napište ji a potvrďte Enterem, jde zadat i víc značek oddělených čárkou), nebo **„Všechna piva v akci“** |
| Čas kontroly | Denní kontrola v zadaný čas, volitelně navíc každých N hodin. Kdykoli ručně: tlačítko **Aktualizovat akce** nebo služba `akce_na_pivo.refresh` |
| Poloha | Domov HA, nebo entita `person` / `device_tracker` / `zone` (GPS telefonu). Když se posunete o víc než 2 km, nejbližší pobočky se přepočítají |
| TOP N | Počet zobrazených nejlevnějších nabídek volíte v nastavení (1–10, výchozí 5) |
| Mapa a adresa | U každé nabídky je nejbližší pobočka: adresa, vzdálenost, GPS, otevírací doba a odkazy na Mapy.com a navigaci |

### Další ukazatele, že je pivo opravdu levné

- **Cena za 0,5 l**: přepočet i u multipacků (`8 × 0,5 l`), plechovek 0,33 l a PET 1,5 l. Podle toho se standardně řadí.
- **Nejlevněji za posledních 120 dní**: integrace si ukládá historii cen a označí nabídku, která je na historickém minimu.
- **Levnější než průměr**: o kolik Kč/0,5 l je nabídka levnější než průměr všech akcí na stejnou značku.
- **Sleva ≥ 30 %** a odhad původní ceny.
- **Pod limitem**: nastavíte si cenu za 0,5 l a dostanete událost `akce_na_pivo_levne_pivo` a zapne se binární senzor.
- **Končí dnes / zítra**, **Platí od…** (připravované akce z nových letáků), **Jen s věrnostní kartou** (Lidl Plus, Clubcard, Můj Albert…), **Multipack**.
- Filtry: vynechat nealko, vynechat akce jen s kartou, zobrazit jen obchody s pobočkou v okolí (limit km).

## Instalace integrace

### HACS
1. HACS → Integrace → ⋮ → *Vlastní repozitáře* → `https://github.com/joshuaaaaa/HA-akce-na-pivo`, kategorie *Integrace*.
2. Nainstalujte **Akce na pivo** a restartujte Home Assistant.

### Ručně
Zkopírujte `custom_components/akce_na_pivo` do `/config/custom_components/` a restartujte HA.

Potom: **Nastavení → Zařízení a služby → Přidat integraci → Akce na pivo**.
Všechno jde později změnit přes **Konfigurovat**.

## Instalace karty (samostatně)

1. Zkopírujte `www/akce-na-pivo-card.js` do `/config/www/akce-na-pivo-card.js`.
2. **Nastavení → Ovládací panely → ⋮ → Zdroje → Přidat zdroj**
   - URL: `/local/akce-na-pivo-card.js`
   - Typ: *JavaScript modul*
3. Obnovte prohlížeč (Ctrl+F5) a přidejte kartu **Akce na pivo**. Má i grafický editor.

```yaml
type: custom:akce-na-pivo-card
entity: sensor.akce_na_pivo_nejlevnejsi_pivo
title: 🍺 Nejlevnější pivo
count: 5            # kolik nabídek zobrazit (1–10)
sort: ""            # "" = podle integrace, nebo unit | price | distance
show_map: true
map_height: 240
show_images: true
show_address: true
show_flags: true
show_upcoming: false
```

Klepnutím na nabídku se na mapě zvýrazní obchod a objeví se odkazy **Mapy.com**,
**Navigovat** a **Leták**. Mapa používá Leaflet z CDN. Když se nenačte, karta
zobrazí vložený OpenStreetMap.

## Entity

| Entita | Stav | Poznámka |
|---|---|---|
| `sensor.*_nejlevnejsi_pivo` | cena za 0,5 l (nebo za balení) | atribut `offers` = TOP N, `upcoming`, `brands`, `location`; zdroj dat pro kartu |
| `sensor.*_nejlevnejsi_pivo_za_0_5_l` | Kč/0,5 l | vhodné do grafu historie |
| `sensor.*_pivo_1` … `_pivo_N` | cena balení | mají `latitude`/`longitude`, takže je zobrazí i standardní karta Mapa |
| `sensor.*_<značka>` | cena | nejlevnější akce každé vybrané značky |
| `binary_sensor.*_levne_pivo_pod_limitem` | on/off | je v akci pivo pod limitem? |
| `button.*_aktualizovat_akce` | – | okamžitá aktualizace |
| `sensor.*_pocet_akci` | počet | diagnostika |

### Příklad automatizace – upozornění do mobilu

```yaml
automation:
  - alias: Levné pivo
    trigger:
      - platform: event
        event_type: akce_na_pivo_levne_pivo
    action:
      - service: notify.mobile_app_telefon
        data:
          title: "🍺 {{ trigger.event.data.product }}"
          message: >
            {{ trigger.event.data.shop }} za {{ trigger.event.data.price }} Kč
            ({{ trigger.event.data.price_per_half_liter }} Kč/0,5 l),
            {{ trigger.event.data.address }} – {{ trigger.event.data.distance_km }} km,
            platí do {{ trigger.event.data.valid_to }}
```

### Standardní karta Mapa

```yaml
type: map
entities:
  - sensor.akce_na_pivo_pivo_1
  - sensor.akce_na_pivo_pivo_2
  - sensor.akce_na_pivo_pivo_3
  - zone.home
```

## Poznámky

- Integrace stahuje veřejné stránky kupi.cz šetrně: několik stránek jednou denně, s pauzami mezi požadavky.
  Když kupi.cz změní vzhled stránek, parser (`kupi.py`) bude potřeba upravit. Jako záložní zdroj
  slouží strukturovaná data (JSON-LD) na stránce produktu.
- Kupi.cz uvádí akce za celý řetězec. Pobočka na mapě je **nejbližší prodejna daného řetězce**,
  konkrétní akce se tam ale může lišit (třeba hypermarket vs. supermarket).
- Pobočky z OpenStreetMap se ukládají do mezipaměti na 7 dní a obnoví se, když se změní poloha.

## Vývoj

```bash
pip install beautifulsoup4 pytest
pytest tests/test_kupi.py            # parser bez Home Assistantu
pip install pytest-homeassistant-custom-component
pytest tests                         # včetně testu integrace
```
