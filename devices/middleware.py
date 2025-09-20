# core/middleware.py
import time
from random import random
from devices.models import ApiRequestLog

SAMPLE_RATE = 1.0  # while volume is low, log all

class ApiTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        t0 = time.perf_counter()
        response = self.get_response(request)

        if random() < SAMPLE_RATE:
            path = (request.path or "")[:256]
            # Treat "enter-api-key" endpoint as QR flow; your PNG QR view is /api_qr/<id>/
            is_qr = ("enter-api-key" in path)
            asset_id = None
            parts = path.strip("/").split("/")
            # Your API path: /api/assets/<id>/specs/ and /api/assets/<id>/enter-api-key/
            # Use the id when present
            if len(parts) >= 3 and parts[0] == "api" and parts[1] == "assets" and parts[2].isdigit():
                asset_id = int(parts[2])

            ApiRequestLog.objects.create(
                method=request.method,
                path=path,
                status_code=getattr(response, "status_code", 0),
                latency_ms=int((time.perf_counter() - t0) * 1000),
                is_qr_flow=is_qr,
                asset_id=asset_id,
            )
        return response
