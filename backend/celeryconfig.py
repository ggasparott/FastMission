import os
import ssl

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# SSL config para Upstash (rediss://)
if broker_url.startswith("rediss://"):
    broker_use_ssl = {
        "ssl_cert_reqs": ssl.CERT_NONE
    }
    result_backend_transport_options = {
        "ssl_cert_reqs": ssl.CERT_NONE
    }

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "America/Sao_Paulo"
enable_utc = True