"""
Configuração do Celery Worker
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Broker e Backend
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Timezone
timezone = 'America/Sao_Paulo'
enable_utc = True

# Serialização
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']

# Concorrência
worker_concurrency = 2  # 2 workers simultâneos (ajustar conforme necessidade)
worker_prefetch_multiplier = 1  # Pegar 1 task por vez (evita sobrecarga)

# Timeout
task_time_limit = 600  # 10 minutos max por task
task_soft_time_limit = 540  # 9 minutos soft limit

# Retry
task_acks_late = True
task_reject_on_worker_lost = True

# Logs
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'
