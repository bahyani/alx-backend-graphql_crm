#!/bin/bash

# Navigate to the Django project root directory
# Adjust the path to match your project structure
cd "$(dirname "$0")/../.." || exit

# Set the timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Define the log file path
LOG_FILE="/tmp/customer_cleanup_log.txt"

# Calculate the date one year ago
ONE_YEAR_AGO=$(date -d '1 year ago' '+%Y-%m-%d')

# Execute Django shell command to delete inactive customers
DELETED_COUNT=$(python manage.py shell <<EOF
from django.utils import timezone
from datetime import timedelta
from crm.models import Customer

# Calculate date one year ago
one_year_ago = timezone.now() - timedelta(days=365)

# Find customers with no orders since one year ago
inactive_customers = Customer.objects.filter(
    orders__created_at__lt=one_year_ago
).distinct() | Customer.objects.filter(orders__isnull=True)

# Count and delete
count = inactive_customers.count()
inactive_customers.delete()

print(count)
EOF
)

# Log the result with timestamp
echo "[$TIMESTAMP] Deleted $DELETED_COUNT inactive customers" >> "$LOG_FILE"
