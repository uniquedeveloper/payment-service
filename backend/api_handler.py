from flask_cors import CORS  # Import CORS
from flask import Flask, request, jsonify, send_from_directory
from pymongo import MongoClient
import os
import datetime
import shutil
import pandas as pd
from pymongo import MongoClient
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
# CORS(app, resources={r"/get_payments": {"origins": "http://192.168.2.32:8080"}})

# @app.route('/')
# def serve_frontend():
#     return send_from_directory(os.path.join(app.static_folder, 'index.html'))

# Simple API endpoint
@app.route('/api/greet', methods=['GET'])
def greet():
    name = request.args.get('name', 'World')
    return jsonify({"message": f"Hello, {name}!"})

# MongoDB Client Setup
client = MongoClient('mongodb+srv://patelmukti17:FPSHVinNbzdLzari@cluster0.og4zz.mongodb.net/payment_gateway')  # Replace with your MongoDB URI if different
# client = MongoClient("mongodb+srv://patelmukti17:FPSHVinNbzdLzari@cluster0.og4zz.mongodb.net/")
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
    result = payments_collection.update_one({'_id': payment_id}, {'$set': updated_data})
    
    if result.matched_count:
        return jsonify({"message": "Payment updated successfully"}), 200
    return jsonify({"error": "Payment not found"}), 404

@app.route('/delete_payment', methods=['DELETE'])
def delete_payment():
    payment_id = request.args.get('id')
    result = payments_collection.delete_one({'_id': payment_id})
    
    if result.deleted_count:
        return jsonify({"message": "Payment deleted successfully"}), 200
    return jsonify({"error": "Payment not found"}), 404

@app.route('/create_payment', methods=['POST'])
def create_payment():
    payment_data = request.json
    result = payments_collection.insert_one(payment_data)
    return jsonify({"id": str(result.inserted_id)}), 201

@app.route('/upload_evidence', methods=['POST'])
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
