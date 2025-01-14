from flask import Flask, request, jsonify, send_from_directory
from pymongo import MongoClient
import os
import datetime
import shutil
# from werkzeug.utils import secure_filename

# Initialize Flask App
app = Flask(__name__)

# MongoDB Client Setup
client = MongoClient("mongodb://localhost:27017")
db = client['payment_db']
payments_collection = db['payments']
evidence_folder = 'evidence_files'

# Ensure evidence folder exists
if not os.path.exists(evidence_folder):
    os.makedirs(evidence_folder)

# Helper Functions
def calculate_total_due(payment):
    return payment['due_amount'] * (1 + payment['tax'] - payment['discount'])

# Routes

@app.route('/get_payments', methods=['GET'])
def get_payments():
    # Filters and pagination
    filters = request.args.to_dict()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Calculate server-side updates (due_now, overdue)
    today = datetime.date.today()
    query = {}
    
    if 'payee_due_date' in filters:
        query['payee_due_date'] = {'$lte': today}
        
    payments_cursor = payments_collection.find(query).skip((page - 1) * per_page).limit(per_page)
    
    results = []
    for payment in payments_cursor:
        # Change status based on due date
        if payment['payee_due_date'].date() == today:
            payment['payee_payment_status'] = 'due_now'
        elif payment['payee_due_date'].date() < today:
            payment['payee_payment_status'] = 'overdue'
        
        # Add total_due calculation
        payment['total_due'] = calculate_total_due(payment)
        results.append(payment)

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

if __name__ == "__main__":
    app.run(debug=True)
