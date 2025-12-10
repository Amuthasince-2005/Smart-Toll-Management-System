# Smart Toll Management System - Architecture & Design Document

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER (Frontend)                   │
│  HTML/CSS/JavaScript - Bootstrap 5 Responsive UI                │
│  Login | Dashboard | Toll Booth | Admin Panel                   │
└────────────────────┬────────────────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────▼────────────────────────────────────────────┐
│                    APPLICATION LAYER (Flask)                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Routes (Blueprints)                                      │   │
│  │ - /auth (Authentication)                                │   │
│  │ - /toll (Toll Processing)                               │   │
│  │ - /dashboard (User Dashboard)                           │   │
│  │ - /admin (Admin Panel)                                  │   │
│  │ - /api (REST API)                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Services (Business Logic)                               │   │
│  │ - TollService (toll processing, calculations)           │   │
│  │ - AnalyticsService (aggregation, reports)              │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ML Integration                                          │   │
│  │ - Load trained model                                    │   │
│  │ - Make predictions                                      │   │
│  │ - Generate dynamic pricing                              │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────────┘
                     │ SQLAlchemy ORM
┌────────────────────▼────────────────────────────────────────────┐
│                    DATA LAYER (SQLite/PostgreSQL)               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Tables:                                                   │  │
│  │ - User (users, admins, operators)                        │  │
│  │ - Vehicle (vehicle details, RFID tags)                  │  │
│  │ - TollPlaza (plaza locations, lanes)                    │  │
│  │ - TollRate (rates per vehicle/time)                     │  │
│  │ - Wallet (prepaid balances)                             │  │
│  │ - TollTransaction (transaction log)                     │  │
│  │ - TrafficLog (hourly aggregated data)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
Vehicle Crossing Event
        │
        ▼
┌──────────────────────┐
│ Toll Booth Interface │
│ (Operator Input)     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Vehicle Search       │
│ (RFID/Number)        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Toll Calculation     │
│ (Service Layer)      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Payment Processing   │
│ (Wallet/Cash/UPI)    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Store Transaction    │
│ (Database)           │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Generate Receipt     │
│ (Display/Print)      │
└──────────────────────┘
```

## Database Schema

### User Table
```
user_id (PK) → name, email, phone, address
             → password_hash, role (enum), created_at
```

### Vehicle Table
```
vehicle_id (PK) → vehicle_number (UNIQUE), vehicle_type
                → rfid_tag_id (UNIQUE), user_id (FK)
                → registration_date, status
```

### TollPlaza Table
```
plaza_id (PK) → plaza_name, location
              → num_lanes, city, state
```

### TollRate Table
```
rate_id (PK) → plaza_id (FK), vehicle_type
             → from_time, to_time, time_slot
             → amount (DECIMAL)
             UNIQUE(plaza_id, vehicle_type, from_time, to_time)
```

### TollTransaction Table
```
txn_id (PK) → vehicle_id (FK), plaza_id (FK)
            → lane_no, timestamp (INDEXED)
            → amount, payment_mode
            → status, operator_id (FK)
```

### Wallet Table
```
wallet_id (PK) → user_id (FK, UNIQUE)
               → balance (DECIMAL)
               → last_updated
```

### TrafficLog Table
```
log_id (PK) → plaza_id (FK), date (INDEXED)
            → hour, vehicle_count, total_revenue
            → traffic_level, avg_speed
            UNIQUE(plaza_id, date, hour)
```

## Service Layer Architecture

### TollService
```
├── get_vehicle_by_number(vehicle_number)
│   → Search by vehicle number or RFID tag
│
├── calculate_toll_amount(plaza_id, vehicle_type, timestamp)
│   → Determine time slot (peak/normal)
│   → Look up toll rate
│   → Return toll details
│
├── process_toll_transaction(vehicle_id, plaza_id, payment_mode, ...)
│   → Validate vehicle
│   → Calculate toll
│   → Process payment
│   → Create transaction record
│   → Return receipt
│
├── _process_wallet_payment(user_id, amount)
│   → Check wallet balance
│   → Deduct amount
│   → Log wallet transaction
│
├── recharge_wallet(user_id, amount)
│   → Update wallet balance
│   → Log recharge transaction
│
└── get_vehicle_toll_history(vehicle_id, limit)
    → Fetch recent transactions
```

### AnalyticsService
```
├── aggregate_hourly_traffic(plaza_id, date)
│   → Group transactions by hour
│   → Count vehicles, sum revenue
│
├── generate_traffic_logs()
│   → Create TrafficLog table entries
│   → Determine traffic levels
│   → Bulk insert/update
│
├── get_daily_summary(plaza_id, date)
│   → Total vehicles and revenue
│   → Hourly breakdown
│   → Peak hour identification
│
├── get_revenue_per_plaza(start_date, end_date)
│   → Group by plaza
│   → Join with plaza names
│   → Calculate totals
│
└── detect_fraud_indicators(days=7)
    → Find suspicious patterns
    → Multiple failed transactions
```

## Machine Learning Pipeline

```
┌────────────────────────────────────────────────────────┐
│ Step 1: Data Preparation                               │
│ ├── Load toll_transactions.csv                         │
│ ├── Aggregate by (plaza_id, hour, day_of_week)        │
│ ├── Create is_peak_hour feature                        │
│ └── Generate vehicle_count target variable             │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│ Step 2: Feature Engineering                           │
│ ├── Plaza ID                                          │
│ ├── Hour (0-23)                                       │
│ ├── Day of Week (0-6)                                 │
│ └── Is Peak Hour (boolean)                            │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│ Step 3: Data Splitting (80/20)                        │
│ ├── Training Set: 80%                                 │
│ └── Test Set: 20%                                     │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│ Step 4: Feature Scaling                               │
│ └── StandardScaler (fit on train, transform both)     │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│ Step 5: Model Training                                │
│ └── RandomForestRegressor(n_estimators=100)          │
│    ├── max_depth=20                                   │
│    ├── min_samples_split=5                            │
│    └── random_state=42                                │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│ Step 6: Model Evaluation                              │
│ ├── Metrics: R², RMSE, MAE                            │
│ ├── Feature Importance Analysis                       │
│ └── Residual Plots                                    │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│ Step 7: Model Serialization                           │
│ └── Pickle save to models/traffic_predictor.pkl       │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│ Step 8: Flask Integration                             │
│ ├── Load model on app startup                         │
│ ├── /api/predict-traffic endpoint                     │
│ └── Return JSON predictions                           │
└────────────────────────────────────────────────────────┘
```

## Spark Analytics Pipeline

```
┌─────────────────────────────────────┐
│ CSV Data (toll_transactions.csv)    │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ Load into Spark DataFrame            │
│ (5000+ records)                      │
└────────────┬────────────────────────┘
             │
      ┌──────┴──────┬──────┬──────┐
      │             │      │      │
      ▼             ▼      ▼      ▼
┌─────────┐ ┌──────────┐ ┌────────┐ ┌────────┐
│Hourly   │ │Revenue   │ │Vehicle │ │Peak    │
│Aggreg   │ │Per Plaza │ │Type    │ │Hours   │
│(via     │ │(groupBy) │ │Dist.   │ │Detect  │
│groupBy) │ │          │ │(groupBy)│ │(top N) │
└────┬────┘ └────┬─────┘ └────┬───┘ └────┬───┘
     │           │            │          │
     └───────────┼────────────┴──────────┘
                 │
        ┌────────▼────────┐
        │ Traffic Log     │
        │ Table Creation  │
        │ (classify level)│
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │Export to CSV    │
        │(for ML training)│
        └─────────────────┘
```

## API Endpoints & Response Structure

### POST /auth/login
```json
Request:
{
  "email": "user@toll.com",
  "password": "password"
}
Response:
{
  "success": true,
  "redirect": "/dashboard/"
}
```

### POST /toll/search-vehicle
```json
Request:
{
  "vehicle_number": "DL01AB1234"
}
Response:
{
  "success": true,
  "vehicle": {
    "vehicle_id": 1,
    "vehicle_number": "DL01AB1234",
    "vehicle_type": "car",
    "owner_name": "Sample User",
    "wallet_balance": 950.50
  }
}
```

### POST /toll/process
```json
Request:
{
  "vehicle_id": 1,
  "plaza_id": 1,
  "payment_mode": "wallet",
  "lane_no": 1
}
Response:
{
  "success": true,
  "transaction_id": 101,
  "amount": 50.00,
  "vehicle_number": "DL01AB1234",
  "vehicle_type": "car",
  "timestamp": "2024-12-09T15:30:00",
  "payment_mode": "wallet"
}
```

### GET /api/predict-traffic
```json
Request:
GET /api/predict-traffic?plaza_id=1&hours_ahead=3

Response:
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
    },
    {
      "hour": 15,
      "predicted_vehicles": 120,
      "traffic_level": "high",
      "confidence": 0.72
    }
  ],
  "ml_model_used": true
}
```

## Role-Based Access Control (RBAC)

```
Admin
├── View all dashboards
├── Manage toll plazas
├── Configure toll rates
├── User management
├── Analytics & reports
├── Fraud detection
└── ML model monitoring

Toll Operator
├── Toll booth interface
├── Vehicle search
├── Process transactions
├── View receipts
└── Daily reports

Vehicle Owner (User)
├── View own vehicles
├── View wallet
├── Recharge wallet
├── View toll history
└── Download receipts
```

## Performance Optimization Strategies

### Database
- **Indexes:** timestamp, plaza_id, user_id on frequently queried columns
- **Connection Pooling:** SQLAlchemy session pool
- **Query Optimization:** Eager loading relationships, limit results

### Caching
```python
@cache.cached(timeout=300)
def get_traffic_summary(plaza_id):
    # Cache for 5 minutes
```

### Spark Configuration
```python
spark.sql.shuffle.partitions = 200  # For large datasets
spark.driver.memory = "4g"
spark.executor.memory = "4g"
```

### ML Model
- Preload model in memory on startup
- Cache scaler with model
- Use batch predictions when possible

## Security Considerations

1. **Authentication:**
   - Flask-Login for session management
   - Password hashing with Werkzeug
   - CSRF protection

2. **Authorization:**
   - Decorator-based role checking
   - Row-level access control

3. **Data Protection:**
   - Input validation and sanitization
   - SQL injection prevention (SQLAlchemy)
   - XSS protection in templates

4. **API Security:**
   - Rate limiting (optional)
   - CORS configuration
   - API key validation (optional)

## Scalability Considerations

### Current (Single Server)
- SQLite database
- Local Spark execution
- Single Python process

### Production (Distributed)
```
Load Balancer
     ├── Web Server 1 (Flask)
     ├── Web Server 2 (Flask)
     └── Web Server 3 (Flask)
              ↓
     PostgreSQL Cluster
              ↓
     Spark Cluster (distributed)
              ↓
     Redis Cache
```

## Deployment Checklist

- [ ] Change SECRET_KEY
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS/SSL
- [ ] Set environment variables
- [ ] Configure logging
- [ ] Use Gunicorn/uWSGI
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Load balancing
- [ ] CDN for static files

---

This architecture supports the complete workflow from toll collection to ML-powered analytics, scalable from development to production environments.
