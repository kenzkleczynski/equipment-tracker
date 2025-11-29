from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGODB_URI'), tlsAllowInvalidCertificates=True)
db = client['equipment_tracker']
employees = db['employees']

# Clear existing employees (fresh start)
employees.delete_many({})

# Add test employees
test_employees = [
    {"name": "Mackenzie", "pin": "1234"},
    {"name": "Lucy", "pin": "5678"},
    {"name": "Staff Member", "pin": "9999"}
]

employees.insert_many(test_employees)
print("✅ Employees added to database!")

# Show what we added
for emp in employees.find():
    print(f"  - {emp['name']}: PIN {emp['pin']}")