"""
Django-crontab job functions for CRM application.
"""

from datetime import datetime
import requests


def log_crm_heartbeat():
    """
    Logs a heartbeat message every 5 minutes to confirm CRM application health.
    Optionally queries the GraphQL hello field to verify endpoint responsiveness.
    """
    # Get current timestamp in DD/MM/YYYY-HH:MM:SS format
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    # Log file path
    log_file = '/tmp/crm_heartbeat_log.txt'
    
    # Default message
    message = f"{timestamp} CRM is alive"
    
    # Optional: Query GraphQL endpoint to verify it's responsive
    try:
        graphql_url = "http://localhost:8000/graphql"
        query = {
            "query": "{ hello }"
        }
        response = requests.post(graphql_url, json=query, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'hello' in data['data']:
                message += f" - GraphQL endpoint responsive: {data['data']['hello']}"
        else:
            message += f" - GraphQL endpoint returned status {response.status_code}"
    except Exception as e:
        message += f" - GraphQL endpoint check failed: {str(e)}"
    
    # Append to log file
    with open(log_file, 'a') as f:
        f.write(message + '\n')
