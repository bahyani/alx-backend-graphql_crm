"""
Django-crontab job functions for CRM application.
"""

from datetime import datetime
import requests
from django.conf import settings


def update_low_stock():
    url = settings.GRAPHQL_URL  # You will define this in settings.py

    query = """
    mutation {
        updateLowStockProducts {
            message
            updatedProducts {
                name
                stock
            }
        }
    }
    """

    response = requests.post(url, json={"query": query})
    data = response.json()

    log_path = "/tmp/low_stock_updates_log.txt"

    with open(log_path, "a") as file:
        file.write("\n\n=== Update Run: " + str(datetime.now()) + " ===\n")

        try:
            updated = data["data"]["updateLowStockProducts"]["updatedProducts"]
            for product in updated:
                file.write(f"{product['name']} → New Stock: {product['stock']}\n")

            file.write("Status: SUCCESS\n")

        except Exception as e:
            file.write("Error: " + str(e) + "\n")
            file.write("Raw response: " + str(data) + "\n")


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
