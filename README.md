# Smart Toll Management System

## Project Overview

A comprehensive **Smart Toll Management System** built with Flask, Python, Machine Learning (Scikit-learn), and Big Data (Apache Spark). This system automates toll collection and provides advanced analytics and traffic predictions.

### Key Features

- **User Management**: Admin, Toll Operators, and Vehicle Owners with role-based access
- **Vehicle Management**: Register vehicles with RFID/FASTag support
- **Toll Collection**: Interactive toll booth interface for seamless transaction processing
- **Wallet System**: Digital wallet for FASTag payments
- **Analytics Dashboard**: Real-time traffic and revenue analytics
- **Machine Learning**: Traffic prediction models for dynamic pricing
- **Big Data Processing**: Apache Spark for large-scale data aggregation
- **Responsive UI**: Bootstrap-based responsive web interface

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.8+, Flask 2.3 |
| **Database** | SQLite (development), PostgreSQL (production) |
| **ML/AI** | Scikit-learn, Random Forest Regressor |
| **Big Data** | Apache Spark (PySpark) |
| **Data Processing** | Pandas, NumPy |
| **Frontend** | HTML5, CSS3, Bootstrap 5, JavaScript |
| **Authentication** | Flask-Login, Werkzeug |

---

## Project Structure

```
smart_toll_system/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── models/
│   │   └── __init__.py      # Database models (User, Vehicle, Toll, etc.)
│   ├── routes/
│   │   ├── auth.py          # Authentication routes
│   │   ├── toll.py          # Toll booth interface
│   │   ├── dashboard.py     # User dashboard
│   │   ├── admin.py         # Admin panel
│   │   ├── user.py          # User profile
│   │   └── api.py           # REST API endpoints (ML predictions)
│   ├── services/
│   │   ├── toll_service.py       # Toll transaction logic
│   │   └── analytics_service.py  # Analytics & reporting
│   ├── static/
│   │   └── css/
│   │       └── style.css        # Styling
│   └── templates/
│       ├── base.html            # Base template
│       ├── auth/
│       │   ├── login.html
│       │   └── register.html
│       ├── dashboard/
│       │   └── home.html
│       └── toll/
│           └── booth.html
├── ml_analytics/
│   ├── train_model.py       # ML model training
│   ├── spark_analytics.py   # Spark analytics
│   └── data_generation.py   # Sample data generation
├── models/
│   └── traffic_predictor.pkl  # Trained ML model (after training)
├── data/
│   └── toll_transactions.csv  # Sample transaction data
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

---

## Installation & Setup

### Step 1: Clone/Download Project

```bash
# Navigate to project directory
cd c:\Users\Admin\OneDrive\Desktop\sf\smart_toll_system
```

### Step 2: Create Virtual Environment (Recommended)

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Initialize Database

```bash
# Run the Flask app initialization
python run.py
```

Or use Flask CLI:
```bash
# In the project root directory
set FLASK_APP=run.py  # Windows
flask init-db         # Create and populate database
```

---

## Running the Application

### Local Development Server

```bash
# Method 1: Direct execution
python run.py

# Method 2: Using Flask CLI
set FLASK_APP=run.py
flask run
```

The application will be available at: **http://localhost:5000**

### Default Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@toll.com | password |
| Toll Operator | operator@toll.com | password |
| User | user@toll.com | password |

---

## ML Model Training

### Step 1: Generate Sample Data

```bash
python ml_analytics/data_generation.py
```

This creates `data/toll_transactions.csv` with 10,000 sample records.

### Step 2: Train ML Model

```bash
python ml_analytics/train_model.py
```

**Output:**
- Trained model saved to `models/traffic_predictor.pkl`
- Training metrics displayed (R² Score, RMSE, MAE)
- Feature importance analysis

### Step 3: Verify Model Integration

The trained model is automatically loaded by the Flask app when available.

Test the prediction endpoint:
```
GET /api/predict-traffic?plaza_id=1&hours_ahead=3
```

---

## Spark Analytics (Big Data Processing)

### Local Spark Setup

```bash
# Run Spark analytics with sample data
python ml_analytics/spark_analytics.py
```

**Analytics Performed:**
- Hourly vehicle aggregation
- Revenue per plaza
- Vehicle type distribution
- Peak hour detection
- Traffic log creation

**Output:** CSV files in `data/traffic_logs/`

### Google Colab Integration

See the Google Colab notebook (`Smart_Toll_System_Colab.ipynb`) for:
- PySpark setup in Colab
- Distributed data processing
- ML model training
- Results visualization

---

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/logout` - Logout

### Toll Processing
- `POST /toll/booth` - Toll booth interface
- `POST /toll/search-vehicle` - Search vehicle by number/RFID
- `POST /toll/process` - Process toll transaction
- `GET /toll/receipt/<txn_id>` - Get transaction receipt

### User Dashboard
- `GET /dashboard/` - User dashboard
- `GET /dashboard/vehicles` - View vehicles
- `POST /dashboard/vehicle/add` - Add new vehicle
- `GET /dashboard/wallet` - View wallet
- `GET /dashboard/toll-history` - Transaction history

### Admin Panel
- `GET /admin/dashboard` - Admin dashboard with analytics
- `GET /admin/plazas` - Manage toll plazas
- `GET /admin/rates` - Manage toll rates
- `GET /admin/users` - User management
- `GET /admin/analytics` - Detailed analytics

### ML/Analytics API
- `GET /api/health` - Health check
- `GET /api/predict-traffic` - Traffic prediction (uses ML model)
- `GET /api/traffic-summary/<plaza_id>` - Traffic summary
- `GET /api/pricing-recommendation/<plaza_id>` - Dynamic pricing suggestion

---

## Database Schema

### User Table
```
user_id, name, email, phone, address, password_hash, role, created_at
```

### Vehicle Table
```
vehicle_id, vehicle_number, vehicle_type, rfid_tag_id, user_id, 
registration_date, status, created_at
```

### TollPlaza Table
```
plaza_id, plaza_name, location, num_lanes, city, state, created_at
```

### TollRate Table
```
rate_id, plaza_id, vehicle_type, from_time, to_time, time_slot, amount
```

### TollTransaction Table
```
txn_id, vehicle_id, plaza_id, lane_no, timestamp, amount, 
payment_mode, status, operator_id, notes
```

### Wallet Table
```
wallet_id, user_id, balance, last_updated
```

### TrafficLog Table (for ML)
```
log_id, plaza_id, date, hour, vehicle_count, total_revenue, 
traffic_level, avg_speed, created_at
```

---

## Machine Learning Model Details

### Traffic Predictor Model

**Model Type:** Random Forest Regressor

**Purpose:** Predict vehicle count for toll plazas (used for traffic forecasting and dynamic pricing)

**Features Used:**
- `plaza_id` - Toll plaza identifier
- `hour` - Hour of day (0-23)
- `day_of_week` - Day of week (0-6)
- `is_peak_hour` - Binary indicator for peak hours (7-10 AM, 5-8 PM)

**Target Variable:**
- `vehicle_count` - Number of vehicles crossing in an hour

**Performance Metrics (Example):**
- Test R² Score: 0.85+
- Test RMSE: ~15 vehicles
- Test MAE: ~10 vehicles

### Model Training Pipeline

```
Raw Data (CSV)
    ↓
Data Preprocessing (Pandas)
    ↓
Feature Engineering
    ↓
Train/Test Split (80/20)
    ↓
Model Training (sklearn RandomForest)
    ↓
Evaluation & Metrics
    ↓
Model Serialization (pickle)
    ↓
Flask API Integration
```

### Using Predictions

The API endpoint `/api/predict-traffic` returns:
```json
{
    "success": true,
    "plaza_id": 1,
    "plaza_name": "Highway Plaza - North",
    "predictions": [
        {
            "hour": 14,
            "predicted_vehicles": 85,
            "traffic_level": "normal",
            "confidence": 0.75
        }
    ],
    "ml_model_used": true
}
```

---

## Using with Google Colab

### Setup in Colab

1. **Install Dependencies:**
```python
!pip install flask flask-sqlalchemy scikit-learn pyspark pandas numpy
```

2. **Mount Google Drive (for data files):**
```python
from google.colab import drive
drive.mount('/content/drive')
```

3. **Upload Project:**
- Upload the project ZIP to Google Drive
- Or clone from GitHub

4. **Run in Colab:**
```python
import os
os.chdir('/content/drive/My Drive/smart_toll_system')
exec(open('ml_analytics/train_model.py').read())
exec(open('ml_analytics/spark_analytics.py').read())
```

### Spark in Colab

```python
# Install Java for Spark
!apt-get update
!apt-get install -y openjdk-11-jdk-headless

# Spark will work in local mode automatically
from pyspark.sql import SparkSession
spark = SparkSession.builder.master("local[*]").appName("Toll").getOrCreate()
```

---

## Features Explained

### 1. Toll Booth Interface
- **Vehicle Search**: Enter vehicle number or RFID tag
- **Toll Calculation**: Automatic calculation based on vehicle type and time slot
- **Payment Processing**: Support for wallet (FASTag), cash, and UPI
- **Receipt Generation**: Instant digital receipt with transaction details

### 2. Admin Dashboard
- **Real-time Analytics**: Vehicle count, revenue per plaza, peak hours
- **Fraud Detection**: Identify suspicious transaction patterns
- **Toll Rate Management**: Configure rates per vehicle type and time slot
- **User Management**: View and manage all system users

### 3. ML Predictions
- **Traffic Forecasting**: Predict vehicle count for future hours
- **Dynamic Pricing**: Recommend toll rates based on traffic predictions
- **Trend Analysis**: Historical traffic pattern analysis

### 4. Spark Analytics
- **Hourly Aggregation**: Process millions of transactions in seconds
- **Revenue Breakdown**: By plaza, vehicle type, payment mode
- **Peak Hour Detection**: Identify high-traffic periods
- **Traffic Logs**: Generate ML training data

---

## Development Workflow

### Creating a New Route

```python
# app/routes/new_route.py
from flask import Blueprint, render_template
from flask_login import login_required

new_bp = Blueprint('new', __name__, url_prefix='/new')

@new_bp.route('/page')
@login_required
def page():
    return render_template('new/page.html')

# Register in app/__init__.py
app.register_blueprint(new_bp)
```

### Adding a Service

```python
# app/services/new_service.py
class NewService:
    @staticmethod
    def do_something():
        # Business logic here
        pass

# Use in routes
from app.services.new_service import NewService
result = NewService.do_something()
```

### Database Migrations

```python
# Modify models in app/models/__init__.py
# Then in Flask shell:
db.session.commit()
db.create_all()
```

---

## Testing

### Manual Testing

1. **Register a new user:**
   - Navigate to `/auth/register`
   - Fill in details
   - Login with credentials

2. **Test toll processing:**
   - Login as Toll Operator
   - Go to `/toll/booth`
   - Search for vehicle (e.g., DL01AB1234)
   - Process transaction

3. **Test ML predictions:**
   - Go to Admin Dashboard
   - Visit `/api/predict-traffic?plaza_id=1`
   - View prediction results

### Unit Testing (Optional)

```bash
pytest tests/
```

---

## Troubleshooting

### Issue: Database Error

**Solution:**
```bash
# Reset database
rm smart_toll_system.db
flask init-db
```

### Issue: PySpark not installing

**Solution:**
```bash
# Ensure Java is installed (required for Spark)
java -version

# Install specific PySpark version
pip install pyspark==3.4.0
```

### Issue: Port 5000 already in use

**Solution:**
```bash
# Use different port
python -c "from app import create_app; app = create_app(); app.run(port=8080)"
```

### Issue: ML model not loaded

**Solution:**
- Ensure `models/traffic_predictor.pkl` exists
- Run `python ml_analytics/train_model.py` to train the model

---

## Performance Optimization

### Database
- Use connection pooling in production
- Add database indexes on frequently queried columns
- Consider PostgreSQL for production

### Caching
```python
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/traffic-summary/<plaza_id>')
@cache.cached(timeout=300)
def traffic_summary(plaza_id):
    # Cached for 5 minutes
    pass
```

### Spark Configuration
```python
spark = SparkSession.builder \
    .appName("Toll") \
    .config("spark.sql.shuffle.partitions", "200") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .getOrCreate()
```

---

## Deployment

### Production Checklist

- [ ] Change `SECRET_KEY` in `app/__init__.py`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS
- [ ] Set up SSL certificates
- [ ] Configure logging
- [ ] Use production WSGI server (Gunicorn, uWSGI)
- [ ] Set up monitoring and alerts
- [ ] Configure backups

### Gunicorn Deployment

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

---

## Future Enhancements

1. **Mobile App Integration**
   - Android/iOS native apps for vehicle owners
   - Real-time notification system

2. **Advanced Analytics**
   - Anomaly detection for fraud
   - Seasonal traffic patterns
   - Predictive maintenance for toll booths

3. **Integration**
   - RTO (Vehicle Registration) database integration
   - Bank/Payment gateway integration (Razorpay, PayU)
   - Real-time GPS tracking for vehicles

4. **Scalability**
   - Microservices architecture
   - Kubernetes deployment
   - Distributed database replication

---

## References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Scikit-learn](https://scikit-learn.org/)
- [Apache Spark](https://spark.apache.org/)
- [PySpark Documentation](https://spark.apache.org/docs/latest/api/python/)

---

## License

This project is for educational purposes. Modify and use as needed for your B.E. / B.Tech project submission.

---

## Support & Documentation

For more details on specific features:
- Check code comments in each file
- Review the docstrings in Python files
- Explore the API endpoints in `app/routes/api.py`
- See database models in `app/models/__init__.py`

**Created:** 2024
**Last Updated:** December 2024
