from django.apps import AppConfig
import sys
import os

class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitoring' # Ensure this matches your app folder name

    def ready(self):
        # 1. Only run if we are the main process (prevents double-start)
        # 2. Skip if we are running management commands (migrate, makemigrations, etc.)
        
        # Check if we are running a management command
        is_manage_py = any(arg in sys.argv for arg in ['migrate', 'makemigrations', 'collectstatic', 'shell'])
        
        if os.environ.get('RUN_MAIN') == 'true' and not is_manage_py:
            from . import updater
            try:
                updater.start()
            except Exception as e:
                # Log the error but don't crash the whole app
                print(f"Scheduler failed to start: {e}")