# devices/kpi.py
from django.utils import timezone
from datetime import timedelta
from devices.models import ApiRequestLog, ScanSession
import math

def _percentile(values, p=0.95):
    if not values: return None
    v = sorted(values); k = (len(v)-1)*p
    f = math.floor(k); c = math.ceil(k)
    return v[f] if f==c else int(v[f] + (v[c]-v[f])*(k-f))

def compute_kpis(hours=48, qr_type=None):
    since = timezone.now() - timedelta(hours=hours)

    # API Success Rate & P95 (all endpoints)
    api_qs = ApiRequestLog.objects.filter(ts__gte=since)
    total = api_qs.count()
    ok2xx = api_qs.filter(status_code__gte=200, status_code__lt=300).count()
    api_success_pct = (ok2xx/total*100.0) if total else None
    lat_vals = list(api_qs.values_list("latency_ms", flat=True))
    p95_ms = _percentile(lat_vals, 0.95) if lat_vals else None

    # QR KPIs
    ss = ScanSession.objects.filter(ts__gte=since)
    if qr_type in ("OT", "DPP"):
        ss = ss.filter(qr_type=qr_type)
    tested = ss.count()
    delivered = ss.filter(success=True).count()
    acked = ss.filter(ack=True).count()
    qr_delivery_pct = (delivered/tested*100.0) if tested else None
    qr_e2e_pct = (acked/tested*100.0) if tested else None

    return {
        "window_h": hours,
        "qr_type": qr_type or "ALL",
        "qr_functionality_pct": qr_delivery_pct,  # delivery success
        "qr_e2e_success_pct": qr_e2e_pct,        # EMS ACK
        "api_success_pct": api_success_pct,
        "p95_ms": p95_ms,
        "counts": {
            "qr_tested": tested,
            "qr_delivered": delivered,
            "qr_acked": acked,
            "api_total": total,
        }
    }
