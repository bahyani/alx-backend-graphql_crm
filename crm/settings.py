# crm/settings.py

GRAPHQL_URL = "http://127.0.0.1:8000/graphql/"  # Adjust if needed

CRONJOBS = [
    # Run every 12 hours
    ('0 */12 * * *', 'crm.cron.update_low_stock'),
]
