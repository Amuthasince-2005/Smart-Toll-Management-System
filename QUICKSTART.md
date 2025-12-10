# Smart Toll Management System - Quick Start Guide

## 🚀 Quick Start (5 Minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python run.py
```

**Open:** http://localhost:5000

### 3. Login with Demo Account
- **Email:** admin@toll.com
- **Password:** password

---

## 📋 Testing the System (Step by Step)

### A. As an Admin

1. **Login:** admin@toll.com / password
2. **Go to:** Admin Dashboard
3. **Actions:**
   - View total users, vehicles, plazas
   - Check revenue statistics
   - Manage toll plazas and rates

### B. As a Toll Operator

1. **Login:** operator@toll.com / password
2. **Go to:** Toll Booth (http://localhost:5000/toll/booth)
3. **Process a toll:**
   - Enter vehicle number: `DL01AB1234`
   - Select plaza and lane
   - Choose payment mode
   - Click "Process Toll"
   - View receipt

### C. As a Vehicle Owner

1. **Login:** user@toll.com / password (or register new account)
2. **Dashboard:**
   - View vehicles (sample: DL01AB1234, DL02CD5678)
   - View wallet balance (Rs. 1000)
   - Recharge wallet
   - Check toll history

---

## 🤖 Machine Learning Model

### Train the Model
```bash
python ml_analytics/train_model.py
```

**Output:**
- Trained model: `models/traffic_predictor.pkl`
- Training metrics printed to console
- R² Score: ~0.85
- RMSE: ~15 vehicles

### Test ML Predictions
```
Visit: http://localhost:5000/api/predict-traffic?plaza_id=1&hours_ahead=3
```

Response will show traffic predictions for next 3 hours.

---

## 🔥 Spark Analytics

### Run Spark Analytics
```bash
python ml_analytics/spark_analytics.py
```

**Outputs:**
- Hourly vehicle aggregation
- Revenue per plaza
- Vehicle type distribution
- Peak hour detection
- Traffic logs for ML

---

## 📊 Google Colab

### 1. Open Notebook
Open `Smart_Toll_System_Colab.ipynb` in Google Colab

### 2. Run All Cells
```
Runtime → Run All
```

### 3. View Results
- Data generation: 5000 toll transactions
- Spark analytics: 6 different aggregations
- ML model: Full training and evaluation
- Predictions: 6-hour traffic forecast

---

## 🗂️ Project Structure Summary

```
smart_toll_system/
├── app/
│   ├── models/          # Database models
│   ├── routes/          # Flask routes
│   ├── services/        # Business logic
│   ├── static/css/      # Styling
│   └── templates/       # HTML pages
├── ml_analytics/
│   ├── train_model.py           # ML training
│   ├── spark_analytics.py       # Big data
│   └── data_generation.py       # Sample data
├── models/              # Trained models
├── data/                # Datasets
├── run.py              # Entry point
├── requirements.txt    # Dependencies
└── README.md           # Documentation
```

---

## 🔑 Key Features Explained

| Feature | How to Access | Purpose |
|---------|---------------|---------|
| **Toll Booth** | /toll/booth | Process toll for vehicles |
| **User Dashboard** | /dashboard | View vehicles, wallet, history |
| **Admin Panel** | /admin/dashboard | Analytics, management |
| **ML API** | /api/predict-traffic | Traffic predictions |
| **Analytics** | /admin/analytics | Detailed reports |

---

## 📱 API Endpoints (for Testing)

### ML Prediction
```
GET /api/predict-traffic?plaza_id=1&hours_ahead=3
```

### Traffic Summary
```
GET /api/traffic-summary/1?days=7
```

### Health Check
```
GET /api/health
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 5000 in use | `python -c "from app import create_app; app = create_app(); app.run(port=8080)"` |
| Database error | Delete `smart_toll_system.db` and restart |
| ML model not found | Run `python ml_analytics/train_model.py` |
| Spark error | Install Java: `apt-get install openjdk-11-jdk-headless` |

---

## 📈 Sample Data

The system comes with demo data:

**Sample User Account:**
- Email: user@toll.com
- Password: password
- Vehicles: 2 (DL01AB1234, DL02CD5678)
- Wallet Balance: Rs. 1000

**Sample Toll Plazas:**
1. Highway Plaza - North (Delhi-Gurgaon)
2. Highway Plaza - South (Chennai Highway)
3. City Bypass - East
4. City Bypass - West

**Sample Toll Rates:**
- Bike: Rs. 25-30
- Car: Rs. 50-65
- Truck: Rs. 150-180
- Bus: Rs. 100-120
- Heavy Vehicle: Rs. 200+

---

## 📝 For Viva/Presentation

### Key Points to Explain

1. **System Architecture:**
   - Flask backend with SQLAlchemy ORM
   - Role-based access control
   - RESTful API for predictions

2. **Database Design:**
   - 8 interconnected tables
   - Relationships and constraints
   - Transaction logging

3. **Machine Learning:**
   - Random Forest model for traffic prediction
   - 4 features: plaza_id, hour, day_of_week, is_peak_hour
   - Performance: R² = 0.85, RMSE = 15 vehicles

4. **Big Data Processing:**
   - Apache Spark for distributed processing
   - Aggregations: hourly, daily, by plaza
   - Traffic log generation for ML

5. **User Interface:**
   - Bootstrap responsive design
   - Toll booth interface for operators
   - Admin dashboard for analytics

6. **Integration:**
   - ML predictions → Dynamic pricing recommendations
   - Spark logs → ML training data
   - Flask API → Real-time predictions

---

## 💡 Tips for Presentation

1. **Demo Order:**
   - Login as admin → show dashboard
   - Login as operator → process toll
   - Login as user → view history
   - Show API predictions
   - Run Spark analytics
   - Show ML model results

2. **Code Highlights:**
   - Database models (app/models/__init__.py)
   - Toll processing logic (app/services/toll_service.py)
   - ML model training (ml_analytics/train_model.py)
   - API endpoints (app/routes/api.py)

3. **Results to Emphasize:**
   - Working toll booth system
   - Real-time analytics
   - Accurate ML predictions
   - Scalable Spark processing
   - Professional UI

---

## 🎓 Learning Resources

- **Flask:** https://flask.palletsprojects.com/
- **SQLAlchemy:** https://docs.sqlalchemy.org/
- **Scikit-learn:** https://scikit-learn.org/stable/
- **Apache Spark:** https://spark.apache.org/docs/latest/

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Start app | `python run.py` |
| Train ML | `python ml_analytics/train_model.py` |
| Run Spark | `python ml_analytics/spark_analytics.py` |
| Generate data | `python ml_analytics/data_generation.py` |
| Initialize DB | `python -c "from run import app; app.cli.commands['init-db'].invoke()"` |

---

## ✅ Checklist for Viva

- [ ] System runs without errors
- [ ] Can login with demo accounts
- [ ] Can process toll transactions
- [ ] Dashboard shows data
- [ ] ML model makes predictions
- [ ] Spark analytics generates results
- [ ] Code is well-commented
- [ ] Database schema is clear
- [ ] UI is responsive
- [ ] All features are documented

---

**Good luck with your project! 🎉**
