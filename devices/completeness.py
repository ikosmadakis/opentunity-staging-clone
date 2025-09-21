# devices/completeness.py
from typing import Any, Dict, Iterable

# === ADFJ (trim/add as you like) ============================================
# For clarity I only include a focused subset here. You can paste your full ADFJ.
ADFJ: Dict[str, Iterable[Dict[str, Any]]] = {
    "asset": [
        {"name":"manufacturer", "characterization":"mandatory",  "weight":1.0},
        {"name":"model_name",   "characterization":"mandatory",  "weight":1.0},
        {"name":"classification","characterization":"mandatory", "weight":1.0},
        {"name":"flexibility",  "characterization":"mandatory",  "weight":1.0},
        {"name":"communication","characterization":"mandatory",  "weight":1.0},
        {"name":"communication_protocol","characterization":"mandatory","weight":1.0},
        {"name":"modbus_register_map","characterization":"mandatory","weight":1.0},
        {"name":"serial_number","characterization":"recommended","weight":0.7},
        {"name":"deployment",   "characterization":"recommended","weight":0.7},
        {"name":"ip_rating",    "characterization":"recommended","weight":0.5},
        {"name":"dimensions",   "characterization":"optional",   "weight":0.3},
        {"name":"weight",       "characterization":"optional",   "weight":0.3},
        {"name":"dpp_url",      "characterization":"recommended","weight":0.7},
    ],
    "electrical_specs": [
        {"name":"phase_configuration","characterization":"recommended","weight":0.6},
        {"name":"frequency",         "characterization":"recommended","weight":0.6},
        {"name":"voltage_nominal",   "characterization":"recommended","weight":0.7},
        {"name":"current_max_df",    "characterization":"recommended","weight":0.6},
        {"name":"power_factor",      "characterization":"recommended","weight":0.5},
    ],
    "bess_specs": [
        {"name":"voltage_nominal",        "characterization":"mandatory","weight":1.0},
        {"name":"energy_rating_usable",   "characterization":"mandatory","weight":1.0},
        {"name":"energy_rating_usable_units","characterization":"mandatory","weight":0.9},
        {"name":"maximum_discharge_current","characterization":"recommended","weight":0.7},
        {"name":"round_trip_efficiency",  "characterization":"recommended","weight":0.6},
    ],
    "inverter_specs": [
        {"name":"nominal_active_power_kw", "characterization":"recommended","weight":0.7},
        {"name":"max_apparent_feed_in_power_kva","characterization":"recommended","weight":0.7},
        {"name":"power_factor",            "characterization":"recommended","weight":0.5},
    ],
    "pv_module_specs": [
        {"name":"voc","characterization":"recommended","weight":0.6},
        {"name":"isc","characterization":"recommended","weight":0.6},
        {"name":"vmpp","characterization":"recommended","weight":0.6},
        {"name":"impp","characterization":"recommended","weight":0.6},
    ],
    "scc_specs": [
        {"name":"model_name","characterization":"optional","weight":0.3},
        {"name":"voltage_input","characterization":"recommended","weight":0.5},
    ],
    "energy_meter_specs": [
        {"name":"accuracy_class","characterization":"recommended","weight":0.5},
        {"name":"voltage_nominal","characterization":"recommended","weight":0.6},
    ],
}
# ============================================================================

def _has_value(v: Any) -> bool:
    """Treat '', None, {}, [], and zero-length text as missing. JSON/text
    fields rendered as '{}'/'[]' are also considered missing."""
    if v is None:
        return False
    if isinstance(v, (list, tuple, dict)) and len(v) == 0:
        return False
    if isinstance(v, str):
        s = v.strip()
        if not s or s in ("{}", "[]", "—"):
            return False
    return True

def _score_block(obj: Any, fields: Iterable[Dict[str, Any]]) -> tuple[float, float]:
    w_have = 0.0
    w_all  = 0.0
    for f in fields:
        name = f["name"]
        w    = float(f["weight"])
        v    = getattr(obj, name, None)
        if _has_value(v):
            w_have += w
        w_all += w
    return w_have, w_all

def completeness_score(asset) -> float:
    """
    SCOFU: 100 * sum(weights provided) / sum(weights applicable)
    'Applicable' = core asset fields + spec blocks that exist on this asset.
    """
    provided, total = _score_block(asset, ADFJ["asset"])

    # Only score spec blocks that are present for this asset
    if getattr(asset, "elec_specs", None):
        p, t = _score_block(asset.elec_specs, ADFJ["electrical_specs"]); provided += p; total += t
    if getattr(asset, "bess_specs", None):
        p, t = _score_block(asset.bess_specs, ADFJ["bess_specs"]); provided += p; total += t
    if getattr(asset, "inverter_specs", None):
        p, t = _score_block(asset.inverter_specs, ADFJ["inverter_specs"]); provided += p; total += t
    if getattr(asset, "pv_module_specs", None):
        p, t = _score_block(asset.pv_module_specs, ADFJ["pv_module_specs"]); provided += p; total += t
    if getattr(asset, "scc_specs", None):
        p, t = _score_block(asset.scc_specs, ADFJ["scc_specs"]); provided += p; total += t
    if getattr(asset, "meter_specs", None):
        p, t = _score_block(asset.meter_specs, ADFJ["energy_meter_specs"]); provided += p; total += t

    if total == 0:
        return 0.0
    return round(100.0 * provided / total, 1)
