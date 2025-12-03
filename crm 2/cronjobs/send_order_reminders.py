#!/usr/bin/env python
"""
Script to send order reminders for pending orders from the last 7 days.
Queries GraphQL endpoint and logs results.
"""

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime, timedelta
import os
import sys

# Add the Django project to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# GraphQL endpoint
GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"

# Log file path
LOG_FILE = "/tmp/order_reminders_log.txt"

def get_pending_orders():
    """
    Query GraphQL endpoint for orders from the last 7 days.
    """
    # Set up the transport
    transport = RequestsHTTPTransport(
        url=GRAPHQL_ENDPOINT,
        use_json=True,
    )
    
    # Create a GraphQL client
    client = Client(transport=transport, fetch_schema_from_transport=True)
    
    # Calculate the date 7 days ago
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Define the GraphQL query
    query = gql("""
        query GetPendingOrders($startDate: String!) {
            orders(orderDate_Gte: $startDate) {
                id
                orderDate
                customer {
                    email
                }
            }
        }
    """)
    
    # Execute the query
    try:
        result = client.execute(query, variable_values={"startDate": seven_days_ago})
        return result.get('orders', [])
    except Exception as e:
        print(f"Error querying GraphQL endpoint: {e}")
        return []

def log_order_reminders(orders):
    """
    Log order reminders to the log file.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(f"\n[{timestamp}] Processing {len(orders)} pending orders:\n")
        
        for order in orders:
            order_id = order.get('id')
            customer_email = order.get('customer', {}).get('email', 'N/A')
            log_file.write(f"  - Order ID: {order_id}, Customer Email: {customer_email}\n")

def main():
    """
    Main function to process order reminders.
    """
    # Get pending orders from GraphQL
    orders = get_pending_orders()
    
    # Log the reminders
    if orders:
        log_order_reminders(orders)
    else:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(f"\n[{timestamp}] No pending orders found.\n")
    
    # Print confirmation message
    print("Order reminders processed!")

if __name__ == "__main__":
    main()
