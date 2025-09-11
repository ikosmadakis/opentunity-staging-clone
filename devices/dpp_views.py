# devices/dpp_views.py
import socket
import ipaddress
from urllib.parse import urlsplit

import requests
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from devices.auth import APIKeyAuthentication
from devices.models import (
    Asset,
    Classification,
    Manufacturer,
    Deployment,
    Communication,
    CommunicationProtocol,
    Flexibility,
    Regulation,
    ContentContributor,
)


# ---------- SSRF-safe fetch helpers ----------

PRIVATE_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _is_private_ip(ip: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
        return any(ip_obj in net for net in PRIVATE_NETS)
    except ValueError:
        return True  # treat unknown as unsafe


def _validate_http_https(url: str):
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise ValueError("URL must be http(s)")
    if not parts.netloc:
        raise ValueError("URL has no host")
    # Resolve host and block private/loopback/etc
    try:
        infos = socket.getaddrinfo(parts.hostname, None)
    except Exception as e:
        raise ValueError(f"URL host cannot be resolved: {e}")
    ips = {i[4][0] for i in infos if i and i[4]}
    if not ips:
        raise ValueError("No IPs resolved for host")
    for ip in ips:
        if _is_private_ip(ip):
            raise ValueError("Blocked private/loopback address")


def _fetch_json_with_limits(url, timeout=6, max_bytes=512 * 1024):
    """Fetch JSON with a size cap, SSRF checks, and without double-consuming the stream."""
    import json  # keep at top-level if you prefer
    _validate_http_https(url)
    with requests.get(url, timeout=timeout, stream=True) as r:
        r.raise_for_status()
        enc = r.encoding or "utf-8"
        raw = bytearray()
        for chunk in r.iter_content(8192):
            if not chunk:
                continue
            raw.extend(chunk)
            if len(raw) > max_bytes:
                raise requests.RequestException("DPP payload too large")
    try:
        return json.loads(raw.decode(enc))
    except Exception as e:
        # Last-resort parse with utf-8 replacement to avoid hard failures on odd encodings
        try:
            return json.loads(raw.decode("utf-8", errors="replace"))
        except Exception:
            raise requests.RequestException(f"Invalid JSON from DPP: {e}")



# ---------- small mapping helpers ----------

def _dget(obj, dotted, default=None):
    """Safe dot-path getter for nested dicts."""
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def _first_non_empty(dpp, keys, default=None):
    for k in keys:
        v = _dget(dpp, k)
        if isinstance(v, str):
            v = v.strip()
        if v not in (None, "", [], {}):
            return v
    return default


def _normalize_ifaces(lst):
    """Map DPP 'interfaces' to your communication 'supported_com_types' values."""
    if not isinstance(lst, list):
        return []
    out = []
    for x in lst:
        s = str(x).strip()
        if not s:
            continue
        # Keep simple; you can refine later
        if s.lower() in ("wi-fi", "wifi"):
            out.append("WIFI")
        elif s.lower() == "ethernet":
            out.append("ETHERNET")
        elif s.upper() in ("RS485", "RS-485"):
            out.append("RS485")
        elif s.upper() == "CAN":
            out.append("CAN")
        else:
            out.append(s)  # keep unknowns as-is
    # de-dup while preserving order
    seen = set()
    dedup = []
    for v in out:
        if v not in seen:
            seen.add(v)
            dedup.append(v)
    return dedup


def _ensure_required_fks_from_dpp(dpp):
    """
    Build/get ALL required FK records with safe defaults so Asset insert never violates NOT NULLs.
    """
    # Classification: prefer your own taxonomy; fallback to DPP product.category; else "BATTERY SYSTEM"
    classification_name = _first_non_empty(
        dpp,
        ["product.category"],
        default="BATTERY SYSTEM",
    )
    classification, _ = Classification.objects.get_or_create(type=str(classification_name).strip())

    # Manufacturer: prefer DPP economicOperator.name; else "Unknown"
    manufacturer_name = _first_non_empty(
        dpp,
        ["economicOperator.name"],
        default="Unknown",
    )
    manufacturer, _ = Manufacturer.objects.get_or_create(name=str(manufacturer_name).strip())

    # Deployment is optional in schema; only set if we can infer something
    # DPP doesn't have a clean "deployment", but you had "Indoor/garage" under technicalData.installation.site
    deployment_val = _first_non_empty(
        dpp,
        ["technicalData.installation.site"],
        default=None,
    )
    deployment = None
    if deployment_val:
        deployment, _ = Deployment.objects.get_or_create(primary_environment=str(deployment_val).strip())

    # Communication (NOT NULL): from DPP technicalData.interfaces → supported_com_types
    com_types = _normalize_ifaces(_dget(dpp, "technicalData.interfaces", []))
    comm_payload = {"supported_com_types": com_types}
    communication, _ = Communication.objects.get_or_create(type=comm_payload)

    # CommunicationProtocol (NOT NULL): DPP mock doesn’t spell this out → keep empty list default
    proto_payload = {"supported_com_protocols": []}
    communication_protocol, _ = CommunicationProtocol.objects.get_or_create(type=proto_payload)

    # Flexibility (NOT NULL): your dataset commonly uses "Downward & Upward" — keep that as safe default
    flexibility, _ = Flexibility.objects.get_or_create(type="Downward & Upward")

    # Regulation (NOT NULL): your dataset uses "ON/OFF, LINEAR" — keep that default
    regulation, _ = Regulation.objects.get_or_create(type="ON/OFF, LINEAR")

    return {
        "classification": classification,
        "manufacturer": manufacturer,
        "deployment": deployment,  # may be None (allowed)
        "communication": communication,
        "communication_protocol": communication_protocol,
        "flexibility": flexibility,
        "regulation": regulation,
    }


def _asset_envelope(request, asset):
    """
    Return your existing JSON payload with ot_qr & enter_api_key URLs.
    """
    # Import here to avoid top-level import conflicts / linter warnings
    from devices.serializers import AssetSerializer

    data = AssetSerializer(asset).data
    return {
        "asset_id": asset.id,
        "data": data,
        "ot_qr": f"https://{request.get_host()}/api_qr/{asset.id}/",
        "enter_api_key": f"https://{request.get_host()}/api/assets/{asset.id}/enter-api-key/",
    }


# ---------- Views ----------

class DPPResolveView(APIView):
    """
    GET /api/dpp/resolve?url=<DPP_URL>
    Auth: APIKeyAuthentication (any active key)
    -> 200 with envelope if asset exists (matched by dpp_url), else 404.
    """
    authentication_classes = [APIKeyAuthentication]

    def get(self, request):
        dpp_url = request.query_params.get("url", "").strip()
        if not dpp_url:
            return Response({"detail": "Missing 'url'."}, status=status.HTTP_400_BAD_REQUEST)

        asset = Asset.objects.filter(dpp_url=dpp_url).order_by("id").first()
        if not asset:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(_asset_envelope(request, asset), status=status.HTTP_200_OK)


class DPPImportView(APIView):
    """
    POST /api/dpp/import
    Body: { "dpp_url": "<URL>" }
    Auth: APIKeyAuthentication; ONLY EO (MANUFACTURER) may import (write).
    Upsert on dpp_url globally (prevent duplicates).
    """
    authentication_classes = [APIKeyAuthentication]

    def post(self, request):
        if not request.user or not request.user.is_authenticated:
            return Response({"detail": "Unauthorized."}, status=status.HTTP_401_UNAUTHORIZED)

        # Verify role
        contributor, _ = ContentContributor.objects.get_or_create(user=request.user)
        if contributor.role != "MANUFACTURER":
            return Response(
                {"detail": "Only Manufacturer/Economic Operator can import DPP records."},
                status=status.HTTP_403_FORBIDDEN
            )

        dpp_url = (request.data or {}).get("dpp_url", "").strip()
        if not dpp_url:
            return Response({"detail": "Missing 'dpp_url' in body."}, status=status.HTTP_400_BAD_REQUEST)

        # If already present, return existing asset (idempotent)
        asset = Asset.objects.filter(dpp_url=dpp_url).order_by("id").first()
        if asset:
            env = _asset_envelope(request, asset)
            env["created"] = False
            return Response(env, status=status.HTTP_200_OK)

        # Pull remote JSON (SSRF-safe, bounded)
        try:
            dpp = _fetch_json_with_limits(dpp_url)
        except ValueError as e:
            return Response({"detail": f"Invalid DPP URL: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except requests.HTTPError as e:
            return Response({"detail": f"DPP server error: {e}"}, status=status.HTTP_502_BAD_GATEWAY)
        except requests.RequestException as e:
            return Response({"detail": f"Network error: {e}"}, status=status.HTTP_504_GATEWAY_TIMEOUT)

        # Prepare all required FK records up-front (using safe defaults where DPP is silent)
        fks = _ensure_required_fks_from_dpp(dpp)

        # Choose a reasonable model_name from DPP
        model_name = _first_non_empty(
            dpp,
            ["product.itemLevel.model", "product.modelName", "product.id"],
            default="Unknown Model",
        )

        with transaction.atomic():
            asset = Asset.objects.create(
                model_name=str(model_name),
                classification=fks["classification"],
                manufacturer=fks["manufacturer"],
                deployment=fks["deployment"],  # may be None
                communication=fks["communication"],
                communication_protocol=fks["communication_protocol"],
                flexibility=fks["flexibility"],
                regulation=fks["regulation"],
                dpp_url=dpp_url,
                description="Imported from DPP.",
                record_contributor=contributor,
            )

        env = _asset_envelope(request, asset)
        env["created"] = True
        return Response(env, status=status.HTTP_201_CREATED)


class DPPAssetView(APIView):
    """
    GET /api/dpp/asset?url=<DPP_URL>&auto_import=true|false
    Auth: APIKeyAuthentication

    - If found -> 200 envelope
    - If not found and auto_import=true and caller is EO -> import then 201
    """
    authentication_classes = [APIKeyAuthentication]

    def get(self, request):
        dpp_url = request.query_params.get("url", "").strip()
        auto_import = request.query_params.get("auto_import", "false").lower() in ("1", "true", "yes")

        if not dpp_url:
            return Response({"detail": "Missing 'url'."}, status=status.HTTP_400_BAD_REQUEST)

        # Try resolve by URL
        asset = Asset.objects.filter(dpp_url=dpp_url).order_by("id").first()
        if asset:
            return Response(_asset_envelope(request, asset), status=status.HTTP_200_OK)

        if not auto_import:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        # Only EO (Manufacturer) can auto-import
        contributor, _ = ContentContributor.objects.get_or_create(user=request.user)
        if contributor.role != "MANUFACTURER":
            return Response(
                {"detail": "Only Manufacturer/Economic Operator can auto-import DPP records."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Fetch DPP
        try:
            dpp = _fetch_json_with_limits(dpp_url)
        except ValueError as e:
            return Response({"detail": f"Invalid DPP URL: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except requests.HTTPError as e:
            return Response({"detail": f"DPP server error: {e}"}, status=status.HTTP_502_BAD_GATEWAY)
        except requests.RequestException as e:
            return Response({"detail": f"Network error: {e}"}, status=status.HTTP_504_GATEWAY_TIMEOUT)

        # Prepare all required FK records up-front (using safe defaults where DPP is silent)
        fks = _ensure_required_fks_from_dpp(dpp)

        # Choose a reasonable model_name from DPP
        model_name = _first_non_empty(
            dpp,
            ["product.itemLevel.model", "product.modelName", "product.id"],
            default="Unknown Model",
        )

        with transaction.atomic():
            # Re-check (race)
            existing = Asset.objects.filter(dpp_url=dpp_url).order_by("id").first()
            if existing:
                return Response(_asset_envelope(request, existing), status=status.HTTP_200_OK)

            asset = Asset.objects.create(
                model_name=str(model_name),
                classification=fks["classification"],
                manufacturer=fks["manufacturer"],
                deployment=fks["deployment"],  # may be None
                communication=fks["communication"],
                communication_protocol=fks["communication_protocol"],
                flexibility=fks["flexibility"],
                regulation=fks["regulation"],
                dpp_url=dpp_url,
                description="Imported from DPP.",
                record_contributor=contributor,
            )

        return Response(_asset_envelope(request, asset), status=status.HTTP_201_CREATED)
