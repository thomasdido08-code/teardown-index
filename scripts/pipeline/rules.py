"""Classification rules used by the scoring pipeline.

Three kinds of decision are needed for every GUR entry:

  family   which weapon family a weapon belongs to (e.g. 21 Shahed-136
           airframes -> one "Shahed-136 / Geran-2" family)
  owner    which parent group owns the manufacturer, and where that group is
           headquartered under the parent-group and strict-ownership methods
  tier     which Common High Priority List tier the part falls in

Edition 1 recorded these decisions per name in the 30 October 2026 snapshot.
They are kept as reviewed lookup tables in data/pipeline/ (families.csv,
owners.csv, tiers.csv). The rules below are used only for names that are not
in a lookup table yet: new weapons, new manufacturers, new part names. Every
name classified by rule is reported by score.py so it can be checked and
added to the lookup table by hand.
"""
import re

EU = {"Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic", "Denmark", "Estonia",
      "Finland", "France", "Germany", "Greece", "Hungary", "Ireland", "Italy", "Latvia", "Lithuania",
      "Luxembourg", "Malta", "Netherlands", "Poland", "Portugal", "Romania", "Slovakia", "Slovenia",
      "Spain", "Sweden"}
SPLIT = {"France–Italy": ("France", "Italy")}  # STMicroelectronics: split evenly between its two state shareholders
EUROPE = EU | {"Switzerland", "Great Britain", "Norway"}
# For the European groups table only: subsidiaries kept as separate parent
# groups in owners.csv but owned by a larger group.
GROUP_MERGE = {"Freescale Semiconductor": "NXP Semiconductors"}
# Display names used in edition 1 for groups whose GUR spelling differs.
GROUP_LABEL = {"U-blox": "u-blox", "EPCOS AG": "EPCOS", "Wurth Elektronik": "Würth Elektronik",
               "TT electronics Semelab": "TT Electronics"}

# ---------------------------------------------------------------- tiers
# Common High Priority List tiers, simplified to four weights:
#   1 integrated circuits, 2 navigation and radio modules,
#   3 discrete and passive parts, 4 everything else.
# Checked in order 2 -> 1 -> 3, so a "GNSS chip" is a navigation part.
TIER2 = r"gnss|gps|glonass|beidou|navigation module|navigation receiver|satellite navigation|antenna|modem|" \
        r"radio module|rf module|wi-?fi|bluetooth|lora|\blte\b|gsm|gprs|3g|4g|saw filter|" \
        r"surface acoustic|band ?pass filter|emi filter|interference filter|line filter|\bfilter\b"
TIER1 = r"microcircuit|microcontroller|microprocessor|processor|\bdsp\b|memory|\bram\b|sram|dram|eeprom|flash|" \
        r"fpga|\bpld\b|cpld|plis|programmable gate|integrated circuit|\bic\b|chip|amplifier|transceiver|" \
        r"line driver|driver/receiver|regulator|reference voltage|voltage reference|analog-to-digital|" \
        r"digital-to-analog|\badc\b|\bdac\b|codec|multiplexer|comparator|isolator|synthesi[sz]er|" \
        r"clock (?:generator|buffer|driver|multiplexer)|pwm controller|ethernet controller|controller|" \
        r"\blogic\b|buffer|configuration device"
TIER3 = r"transistor|mosfet|capacitor|diode|rectifier|resistor|inductor|inductance|choke|coil|transformer|" \
        r"relay|connector|plug|socket|optocoupler|oscillator|resonator|quartz|crystal|fuse|switch|" \
        r"converter|stabili[sz]er|power supply|power module|accelerometer|gyroscope|current sensor|camera"

_T2, _T1, _T3 = (re.compile(p, re.I) for p in (TIER2, TIER1, TIER3))


def keyword_tier(part_name):
    n = part_name or ""
    if _T2.search(n):
        return 2
    if _T1.search(n):
        return 1
    if _T3.search(n):
        return 3
    return 4


# ---------------------------------------------------------------- families
_STRIP = re.compile(r"\(.*?\)|№\s*\S+|tail number\s*\S+|serial\s*\S+|\b(uav|drone|unmanned aerial vehicle)\b", re.I)


def keyword_family(weapon):
    """Fallback for a weapon not in families.csv: drop serial numbers, tail
    numbers and bracketed notes, so repeat teardowns of one model merge."""
    s = _STRIP.sub(" ", weapon or "")
    s = re.sub(r"[\"'“”«»]", "", s)
    return re.sub(r"\s+", " ", s).strip() or weapon


# ---------------------------------------------------------------- owners
def keyword_owner(manufacturer, hq):
    """Fallback for a manufacturer not in owners.csv: the firm is its own
    parent and its home is GUR's listed headquarters."""
    if not manufacturer or manufacturer.strip().lower() in ("not identified", "unidentified", "n/a"):
        return "Not identified", "Unidentified", "Unidentified"
    home = hq_country(manufacturer, hq)
    return manufacturer, home, home


def hq_country(manufacturer, hq):
    """GUR's listed headquarters, as used by the 'hq' method. A part whose
    manufacturer GUR could not identify is unidentified whatever country GUR
    lists; 'China, Taiwan' is read as China, the first country named."""
    if not manufacturer or manufacturer.strip().lower() in ("not identified", "unidentified"):
        return "Unidentified"
    hq = (hq or "").strip()
    if not hq:
        return "Unidentified"
    return hq.split(",")[0].strip() if hq.startswith("People's Republic of China,") else hq


# ---------------------------------------------------------------- dates
_GUR_YEAR = re.compile(r"\b(19[89]\d|20[0-2]\d)\b")
_DATE_TOKEN = re.compile(r"^#?(\d\d)(\d\d)(?:[A-Z]{1,3})?$")
_BARE_TOKEN = re.compile(r"^#?(\d\d)(\d\d)$")


def gur_year(text):
    """Year from GUR's own production-date field, e.g. 'January (3rd week) 2023'."""
    m = _GUR_YEAR.search(text or "")
    return int(m.group(1)) if m else None


def marking_year(marking, latest=(26, 44)):
    """Year from a YYWW date code in the marking, e.g. '2303A3' or '#2244'.

    Rules, stricter than edition 1:
      - the first line (the part number) is skipped; on a one-line marking
        the first token is skipped instead;
      - a date code is a token of exactly four digits, optionally preceded
        by '#' and followed by up to three capital letters; on a one-line
        marking, where part numbers and date codes sit side by side, only a
        bare four-digit token counts (so 'MAX 1623EAP' is not dated);
      - YY must be 05-26 and WW 01-53, and the date cannot be after the
        snapshot (week 44 of 2026);
      - the first valid code is used.
    Returns None when no code is found.
    """
    if not marking:
        return None
    lines = [l for l in marking.replace("\r", "").split("\n") if l.strip()]
    if not lines:
        return None
    one_line = len(lines) == 1
    if not one_line:
        tokens = [t for l in lines[1:] for t in re.split(r"[\s,;:/-]+", l.strip())]
    else:
        tokens = re.split(r"[\s,;]+", lines[0].strip())[1:]
    for t in tokens:
        m = (_BARE_TOKEN if one_line else _DATE_TOKEN).match(t)
        if not m:
            continue
        yy, ww = int(m.group(1)), int(m.group(2))
        if 5 <= yy <= 26 and 1 <= ww <= 53 and (yy, ww) <= latest:
            return 2000 + yy
    return None
