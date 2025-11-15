# devices/completeness.py
from typing import Any, Dict, Iterable

# === ADFJ (trim/add as you like) ============================================
# For clarity I only include a focused subset here. You can paste your full ADFJ.
ADFJ: Dict[str, Iterable[Dict[str, Any]]] = {
    "asset": [
        {"name":"dpp_url", "characterization":"recommended", "weight":0.7},
        {"name":"opentunity_did", "characterization":"optional", "weight":0.0},
        {"name":"gtin", "characterization":"recommended", "weight":0.7},
        {"name":"manufacturer", "characterization":"mandatory", "weight":1.0},
        {"name":"vendor", "characterization":"mandatory", "weight":1.0},
        {"name":"model_name", "characterization":"mandatory", "weight":1.0},
        {"name":"batch_name", "characterization":"optional", "weight":0.3},
        {"name":"serial_number", "characterization":"optional", "weight":0.3},
        {"name":"eprel_url", "characterization":"recommended", "weight":0.7},
        {"name":"deployment", "characterization":"recommended", "weight":0.7},
        {"name":"classification", "characterization":"mandatory", "weight":1.0},
        {"name":"description", "characterization":"optional", "weight":0.3},
        {"name":"commissioning_date", "characterization":"optional", "weight":0.3},
        {"name":"compliance_checklist", "characterization":"recommended", "weight":0.7},
        {"name":"release_year", "characterization":"optional", "weight":0.3},
        {"name":"flexibility", "characterization":"mandatory", "weight":1.0},
        {"name":"communication", "characterization":"mandatory", "weight":1.0},
        {"name":"communication_protocol", "characterization":"mandatory", "weight":1.0},
        {"name":"modbus_register_map", "characterization":"mandatory", "weight":1.0},
        {"name":"dacq_actuation", "characterization":"optional", "weight":0.3},
        {"name":"devices_attribute", "characterization":"optional", "weight":0.3},
        {"name":"dacq_attributes", "characterization":"optional", "weight":0.3},
        {"name":"control_actuation", "characterization":"mandatory", "weight":1.0},
        {"name":"regulation", "characterization":"mandatory", "weight":1.0},
        {"name":"regulation_response_time_upward", "characterization":"mandatory", "weight":1.0},
        {"name":"regulation_response_time_downward", "characterization":"mandatory", "weight":1.0},
        {"name":"regulation_response_time_unit", "characterization":"mandatory", "weight":1.0},
        {"name":"regulation_response_time_accuracy", "characterization":"mandatory", "weight":1.0},
        {"name":"maximum_upward_regulation", "characterization":"mandatory", "weight":1.0},
        {"name":"maximum_downward_regulation", "characterization":"mandatory", "weight":1.0},
        {"name":"minimum_regulation_step", "characterization":"mandatory", "weight":1.0},
        {"name":"ip_rating", "characterization":"optional", "weight":0.3},
        {"name":"storage_temperature", "characterization":"optional", "weight":0.3},
        {"name":"operating_temperature_range", "characterization":"optional", "weight":0.3},
        {"name":"relative_humidity_range", "characterization":"optional", "weight":0.3},
        {"name":"dimensions", "characterization":"optional", "weight":0.3},
        {"name":"weight", "characterization":"optional", "weight":0.3},
        {"name":"form_factor", "characterization":"optional","weight":0.3},
    ],
    "electrical_specs": [
        {"name":"phase_configuration", "characterization":"mandatory", "weight":1.0},
        {"name":"frequency", "characterization":"mandatory", "weight":1.0},
        {"name":"voltage_nominal", "characterization":"mandatory", "weight":1.0},
        {"name":"voltage_tolerance_df", "characterization":"mandatory", "weight":1.0},
        {"name":"current_nominal_df", "characterization":"mandatory", "weight":1.0},
        {"name":"current_min_df", "characterization":"mandatory", "weight":1.0},
        {"name":"current_max_df", "characterization":"mandatory", "weight":1.0},
        {"name":"inrush_current_max_df", "characterization":"mandatory", "weight":1.0},
        {"name":"power_consumption_nominal_df", "characterization":"mandatory", "weight":1.0},
        {"name":"power_consumption_max_df", "characterization":"mandatory", "weight":1.0},
        {"name":"standby_power_consumption", "characterization":"mandatory", "weight":1.0},
        {"name":"power_consumption_units", "characterization":"mandatory", "weight":1.0},
        {"name":"voltage_regulation_uf", "characterization":"mandatory", "weight":1.0},
        {"name":"voltage_range_uf", "characterization":"mandatory", "weight":1.0},
        {"name":"output_current_nominal_uf", "characterization":"mandatory", "weight":1.0},
        {"name":"output_current_max_uf", "characterization":"mandatory", "weight":1.0},
        {"name":"power_output_nominal_uf", "characterization":"mandatory", "weight":1.0},
        {"name":"power_output_max_uf", "characterization":"mandatory", "weight":1.0},
        {"name":"power_factor", "characterization":"mandatory", "weight":1.0},
        {"name":"energy_class", "characterization":"mandatory", "weight":1.0},
    ],
    "bess_specs": [
        {"name":"bess_application", "characterization":"recommended", "weight":0.7},
        {"name":"cell_type", "characterization":"recommended", "weight":0.7},
        {"name":"voltage_nominal", "characterization":"mandatory", "weight":1.0},
        {"name":"voltage_range", "characterization":"mandatory", "weight":1.0},
        {"name":"capacity", "characterization":"mandatory", "weight":1.0},
        {"name":"maximum_charge_current", "characterization":"mandatory", "weight":1.0},
        {"name":"maximum_discharge_current", "characterization":"mandatory", "weight":1.0},
        {"name":"cycle_life", "characterization":"recommended", "weight":0.7},
        {"name":"energy_rating_nominal", "characterization":"mandatory", "weight":1.0},
        {"name":"energy_rating_nominal_units", "characterization":"mandatory", "weight":1.0},
        {"name":"energy_rating_usable", "characterization":"mandatory", "weight":1.0},
        {"name":"energy_rating_usable_units", "characterization":"mandatory", "weight":1.0},
        {"name":"c_rate", "characterization":"recommended", "weight":1.0},
        {"name":"round_trip_efficiency", "characterization":"recommended", "weight":0.7},
        {"name":"battery_management_system", "characterization":"mandatory", "weight":1.0},
        {"name":"degradation_rate", "characterization":"recommended", "weight":0.7}
    ],
    "inverter_specs": [
        {"name":"nominal_active_power_kw", "characterization":"recommended","weight":1.0},
        {"name":"max_apparent_feed_in_power_kva","characterization":"recommended","weight":0.7},
        {"name":"power_factor",            "characterization":"recommended","weight":0.7},
    ],
    "pv_module_specs": [
        {"name":"voc","characterization":"recommended","weight":0.7},
        {"name":"isc","characterization":"recommended","weight":0.7},
        {"name":"vmpp","characterization":"recommended","weight":0.7},
        {"name":"impp","characterization":"recommended","weight":0.7},
    ],
    "scc_specs": [
        {"name":"model_name","characterization":"optional","weight":0.3},
        {"name":"voltage_input","characterization":"recommended","weight":0.7},
    ],
    "energy_meter_specs": [
        {"name":"phase_configuration", "characterization":"mandatory", "weight":1.0},
        {"name":"frequency", "characterization":"mandatory", "weight":1.0},
        {"name":"voltage_nominal", "characterization":"mandatory", "weight":1.0},
        {"name":"voltage_tolerance_df", "characterization":"mandatory", "weight":1.0},
        {"name":"current_nominal_df", "characterization":"mandatory", "weight":1.0},
        {"name":"current_min_df", "characterization":"mandatory", "weight":1.0},
        {"name":"current_max_df", "characterization":"mandatory", "weight":1.0},
        {"name":"standby_power_consumption", "characterization":"mandatory", "weight":1.0},
        {"name":"power_consumption_nominal_df", "characterization":"mandatory", "weight":1.0},
    	{"name":"power_consumption_units", "characterization":"mandatory", "weight":1.0},
        {"name":"accuracy_class", "characterization":"mandatory", "weight":1.0},
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
