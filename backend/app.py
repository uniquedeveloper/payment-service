from flask_cors import CORS  # Import CORS
from flask import Flask, request, jsonify, send_from_directory
from bson import ObjectId
from pymongo import MongoClient
import os
import datetime
import shutil
import pandas as pd
from pymongo import MongoClient
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

UPLOAD_FOLDER = '/path/to/upload/folder'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'docx', 'txt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_fields(updated_data):
    errors = []
    
    # Validate text fields (non-empty)
    if not updated_data.get('payee_address_line_1'):
        errors.append("payee_address_line_1 is mandatory")
    if not updated_data.get('payee_city'):
        errors.append("payee_city is mandatory")
    if not updated_data.get('payee_country'):
        errors.append("payee_country is mandatory")
    if not updated_data.get('payee_postal_code'):
        errors.append("payee_postal_code is mandatory")
    if not updated_data.get('payee_phone_number'):
        errors.append("payee_phone_number is mandatory")
    if not updated_data.get('payee_email'):
        errors.append("payee_email is mandatory")
    if not updated_data.get('currency'):
        errors.append("currency is mandatory")

    # Validate phone number (E.164 format)
    if 'payee_phone_number' in updated_data and not re.match(r'^\+?[1-9]\d{1,14}$', updated_data['payee_phone_number']):
        errors.append("payee_phone_number must be in E.164 format")

    # Validate email
    if 'payee_email' in updated_data and not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', updated_data['payee_email']):
        errors.append("payee_email is not a valid email address")

    # Validate country code (ISO 3166-1 alpha-2)
    if 'payee_country' in updated_data and len(updated_data['payee_country']) != 2:
        errors.append("payee_country must be a valid ISO 3166-1 alpha-2 country code")

    # Validate currency (ISO 4217)
    if 'currency' in updated_data and len(updated_data['currency']) != 3:
        errors.append("currency must be a valid ISO 4217 currency code")

    # Validate discount_percent and tax_percent
    if 'discount_percent' in updated_data and not (0 <= updated_data['discount_percent'] <= 100):
        errors.append("discount_percent must be between 0 and 100")
    if 'tax_percent' in updated_data and not (0 <= updated_data['tax_percent'] <= 100):
        errors.append("tax_percent must be between 0 and 100")

    # Validate due_amount (mandatory and valid)
    if 'due_amount' in updated_data and not isinstance(updated_data['due_amount'], (int, float)):
        errors.append("due_amount must be a number")
    
    # Validate due_date (date format YYYY-MM-DD)
    if 'payee_due_date' in updated_data:
        try:
            updated_data['payee_due_date'] = datetime.strptime(updated_data['payee_due_date'], '%Y-%m-%d').date()
        except ValueError:
            errors.append("payee_due_date must be in YYYY-MM-DD format")

    # Check if status is 'completed' and evidence is required
    if updated_data.get('payee_payment_status') == 'completed':
        if 'evidence' not in updated_data:
            errors.append("Evidence must be uploaded when the status is set to 'completed'")

    return errors

# MongoDB Client Setup
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/default_db')
client = MongoClient(MONGO_URI)  
db = client['payment_gateway']
payments_collection = db['payments']
evidence_folder = 'evidence_files'

# Ensure evidence folder exists
if not os.path.exists(evidence_folder):
    os.makedirs(evidence_folder)

# Helper Functions
def calculate_total_due(payment):
    # Default values if missing
    due_amount = payment.get('due_amount', 0)
    discount_percent = payment.get('discount_percent', 0)
    tax_percent = payment.get('tax_percent', 0)
    
    # Calculate total due after applying discount and tax
    total_due = due_amount * (1 - discount_percent / 100) * (1 + tax_percent / 100)
    
    # Round to two decimal places
    return round(total_due, 2)
# Routes

from bson import ObjectId

# Helper function to convert ObjectId to string
def convert_objectid_to_str(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, ObjectId):
                data[key] = str(value)  # Convert ObjectId to string
            elif isinstance(value, dict):
                convert_objectid_to_str(value)  # Recurse if it's a nested dictionary
            elif isinstance(value, list):
                for item in value:
                    convert_objectid_to_str(item)  # Recurse if it's a list of objects
    elif isinstance(data, list):
        for index, item in enumerate(data):
            convert_objectid_to_str(item)  # Recurse if it's a list of dictionaries
    return data

@app.route('/get_payments', methods=['GET'])
def get_payments():
    
    # Calculate server-side updates (due_now, overdue)
    today = datetime.date.today()
    query = {}
    
    
    # Find the payments from MongoDB with pagination
    payments_cursor = payments_collection.find(query)
    
    results = []
    for payment in payments_cursor:
        # Convert 'payee_due_date' to a datetime object if it's not already
        due_date = payment.get('payee_due_date', None)
        if isinstance(due_date, datetime.date):  # If it's already a date
            due_date = datetime.datetime.combine(due_date, datetime.datetime.min.time())

        if due_date:
            # Change payment status based on due date
            if due_date.date() == today:
                payment['payee_payment_status'] = 'due_now'
            elif due_date.date() < today:
                payment['payee_payment_status'] = 'overdue'
            else:
                payment['payee_payment_status'] = 'pending'  # Assume 'pending' if the payment is due in future

        # Calculate total_due for the payment
        payment['total_due'] = calculate_total_due(payment)

        # Append to results
        results.append(payment)

    # Convert MongoDB ObjectId fields to string
    results = convert_objectid_to_str(results)

    return jsonify(results), 200

@app.route('/update_payment', methods=['PUT'])
def update_payment():
    payment_id = request.json.get('id')
    updated_data = request.json

    # Validate fields first
    validation_errors = validate_fields(updated_data)
    if validation_errors:
        return jsonify({"errors": validation_errors}), 400

    # Handle file upload if necessary
    evidence_filename = None
    if updated_data.get('payee_payment_status') == 'completed' and 'evidence' in request.files:
        evidence_file = request.files['evidence']
        evidence_filename = upload_evidence(evidence_file)
        if not evidence_filename:
            return jsonify({"error": "Invalid file format or no file uploaded"}), 400
        updated_data['evidence'] = evidence_filename  # Save the filename for future reference

    # Calculate total_due based on due_amount, discount_percent, and tax_percent
    if 'due_amount' in updated_data:
        due_amount = updated_data['due_amount']
        discount_percent = updated_data.get('discount_percent', 0)
        tax_percent = updated_data.get('tax_percent', 0)

        discount_amount = (discount_percent / 100) * due_amount
        tax_amount = (tax_percent / 100) * due_amount
        total_due = round(due_amount - discount_amount + tax_amount, 2)
        
        updated_data['total_due'] = total_due  # Save the calculated total_due

    # Only allow editing specific fields
    editable_fields = ['payee_due_date', 'due_amount', 'payee_payment_status', 'total_due']
    update_fields = {field: updated_data[field] for field in editable_fields if field in updated_data}

    # Update the payment in the database
    result = payments_collection.update_one({'_id': payment_id}, {'$set': update_fields})

    if result.matched_count:
        return jsonify({"message": "Payment updated successfully"}), 200
    return jsonify({"error": "Payment not found"}), 404

@app.route('/delete_payment/<string:payment_id>', methods=['DELETE'])
def delete_payment(payment_id):
    # Convert payment_id to ObjectId
    try:
        payment_id = ObjectId(payment_id)
    except Exception as e:
        return jsonify({"error": "Invalid ID format"}), 400

    result = payments_collection.delete_one({'_id': payment_id})
    
    if result.deleted_count:
        return jsonify({"message": "Payment deleted successfully"}), 200
    return jsonify({"error": "Payment not found"}), 404


@app.route('/create_payment', methods=['POST'])
def create_payment():
    payment_data = request.json
    result = payments_collection.insert_one(payment_data)
    return jsonify({"id": str(result.inserted_id)}), 201

# @app.route('/upload_evidence', methods=['POST'])
def upload_evidence():
    payment_id = request.form['payment_id']
    file = request.files['file']
    
    # Validate file type
    allowed_extensions = {'pdf', 'png', 'jpg'}
    filename = "test" # secure_filename(file.filename)
    file_extension = filename.rsplit('.', 1)[1].lower()
    
    if file_extension not in allowed_extensions:
        return jsonify({"error": "Invalid file type"}), 400

    # Ensure evidence folder exists
    file_path = os.path.join(evidence_folder, f"{payment_id}_{filename}")
    file.save(file_path)
    
    # Update payment status to "completed" in MongoDB
    payments_collection.update_one({'_id': payment_id}, {'$set': {'payee_payment_status': 'completed'}})
    
    # Store the file path in MongoDB
    payments_collection.update_one({'_id': payment_id}, {'$set': {'evidence_file': file_path}})
    
    return jsonify({"message": "File uploaded successfully", "file_url": file_path}), 200

@app.route('/download_evidence', methods=['GET'])
def download_evidence():
    payment_id = request.args.get('payment_id')
    payment = payments_collection.find_one({'_id': payment_id})
    
    if not payment or 'evidence_file' not in payment:
        return jsonify({"error": "Evidence file not found"}), 404
    
    file_path = payment['evidence_file']
    
    if os.path.exists(file_path):
        return send_from_directory(directory=evidence_folder, filename=os.path.basename(file_path), as_attachment=True)
    return jsonify({"error": "File not found"}), 404


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)
