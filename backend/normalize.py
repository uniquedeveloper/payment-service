from flask import Flask, request, jsonify
import pandas as pd
from pymongo import MongoClient
import datetime
import re
import os

app = Flask(__name__)

# MongoDB setup
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/default_db')
client = MongoClient(MONGO_URI)
db = client['payment_gateway']  # Replace with your database name

# Function to normalize the CSV data
# Function to normalize the CSV data
def normalize_data(df):
    # Convert 'payee_added_date_utc' to UTC timestamp
    df['payee_added_date_utc'] = pd.to_datetime(df['payee_added_date_utc'], errors='coerce', utc=True)

    # Convert 'payee_due_date' to datetime format (using .dt to convert to datetime)
    df['payee_due_date'] = pd.to_datetime(df['payee_due_date'], errors='coerce').dt.normalize()

    # Normalize 'payee_payment_status' to valid statuses
    valid_payment_statuses = ['completed', 'due_now', 'overdue', 'pending']
    df['payee_payment_status'] = df['payee_payment_status'].apply(
        lambda x: x if x in valid_payment_statuses else None)

    # Validate mandatory fields
    mandatory_fields = ['payee_address_line_1', 'payee_city', 'payee_country', 'payee_postal_code', 'payee_phone_number', 'payee_email', 'currency', 'due_amount']
    for field in mandatory_fields:
        print(field, df['payee_country'])
        if df[field].isnull().any():
            raise ValueError(f"Missing mandatory field: {field}")

    # Validate phone number (E.164 format)
    def validate_phone_number(phone):
        # E.164 format example: +14155552671
        return bool(re.match(r'^\+?[1-9]\d{1,14}$', str(phone)))

    df['payee_phone_number'] = df['payee_phone_number'].apply(lambda x: x if validate_phone_number(x) else None)

    # Validate email format
    df['payee_email'] = df['payee_email'].apply(lambda x: x if '@' in str(x) else None)

    # Validate currency (ISO 4217 codes)
    valid_currencies = ['USD', 'EUR', 'GBP', 'INR', 'AUD']  # Extend as needed
    df['currency'] = df['currency'].apply(lambda x: x if x in valid_currencies else None)

    # Handle optional fields (discount_percent, tax_percent) - fill NaN with 0
    df['discount_percent'] = pd.to_numeric(df['discount_percent'], errors='coerce').fillna(0)
    df['tax_percent'] = pd.to_numeric(df['tax_percent'], errors='coerce').fillna(0)

    # Calculate total_due based on due_amount, discount_percent, and tax_percent
    df['total_due'] = df['due_amount'] * (1 - df['discount_percent'] / 100) * (1 + df['tax_percent'] / 100)

    # Round to 2 decimal places
    df['due_amount'] = df['due_amount'].round(2)
    df['total_due'] = df['total_due'].round(2)

    return df

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    try:
        # Read the CSV file into a DataFrame, skip blank lines
        df = pd.read_csv(file, skip_blank_lines=True)

        # Remove rows with missing mandatory fields
        mandatory_fields = ['payee_address_line_1', 'payee_city', 'payee_country', 'payee_postal_code', 'payee_phone_number', 'payee_email', 'currency', 'due_amount']
        df.dropna(subset=mandatory_fields, inplace=True)

        # Normalize the data using the normalize_data function
        df = normalize_data(df)

        # Convert DataFrame to dictionary format for MongoDB insertion
        records = df.to_dict(orient='records')

        # Insert into MongoDB
        collection_name = "payments"
        collection = db[collection_name]  # Use the specified collection
        collection.insert_many(records)

        return jsonify({"message": "Data successfully uploaded and normalized."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
