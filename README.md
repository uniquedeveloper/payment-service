# Payment Dashboard System

## Overview

This project consists of a backend API implemented in Python (Flask) and a frontend UI developed using Angular 15+. The main functionalities include managing payments, handling file uploads (evidence), and performing calculations for total dues dynamically. This README provides a guide through setting up and running both the Python backend and Angular frontend.

## Features Implemented

### Backend (Python + Flask)
- Payment CRUD operations: Create, Update, Delete, and List Payments
- Evidence file upload when the payment status is marked as "completed"
- Dynamic calculations for `total_due` and payment status (`due_now`, `overdue`, etc.)
- Pagination and Filtering of payments

### Frontend (Angular 15+)
- Payment Management UI for displaying and updating payments

### Future Enhancements
- Implement validations for editing payments (due_date, due_amount, and status).
- Integrate address and currency auto-completion.
- Implement security features (authentication, authorization).
- Implement user roles for better access control (Admin, User).

## Backend Setup (Python + Flask)

### Requirements
- Python 3.8+
- MongoDB instance (local or cloud)
- `pip` (Python package manager)

### Steps to Set Up Backend

1. **Clone the repository:**
   ```bash
   git clone https://github.com/uniquedeveloper/payment-service.git
   cd payment-dashboard
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # For macOS/Linux
   ```

3. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up MongoDB:**
   - Ensure MongoDB is running locally or use a cloud instance (like MongoDB Atlas).
   - Create a database for the application.

5. **Configure MongoDB connection:**
   - Update the connection string in env file 
   ```python
   MONGO_URI = "mongodb://localhost:27017/payment_db"
   ```
6. **Run 'normalize.py' to upload data to MongoDB as a starting point:**
   ```bash
   python normalize.py
   ```

7. **Run the application:**
   ```bash
   python app.py
   ```
   The Flask server should now be running at `http://127.0.0.1:5000`.

## Frontend Setup (Angular 15+)

### Requirements
- Node.js (version 16 or higher)
- npm (Node Package Manager)

### Steps to Set Up Frontend

1. **Install required dependencies:**
   ```bash
   npm install
   ```

2. **Run the Angular app:**
   ```bash
   ng serve
   ```
   The Angular app should now be running at `http://localhost:4200`.


## Future Enhancements

- **Validation for Editing Payments:** Ensure that all required fields (due_date, due_amount, status) are validated correctly during the editing process.
- **Address and Currency Auto-Complete:** Integrate address and currency auto-complete features for smoother user experience.
- **User Authentication and Authorization:** Implement JWT-based authentication and role-based access control.
- **Improved Error Handling:** Add more detailed error messages and handling for edge cases (e.g., file upload failures).
- **Styling and UI Enhancements:** Improve UI design with more modern components, responsive layout, and better UX features.

