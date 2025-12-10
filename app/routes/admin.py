"""
Admin Routes - Admin dashboard and management functions
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, TollPlaza, TollRate, Vehicle, UserRole, VehicleType, PaymentMode
from app.services.analytics_service import AnalyticsService
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            flash('Admin access required', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """
    Admin dashboard with analytics and ML predictions
    """
    # Get statistics
    total_plazas = TollPlaza.query.count()
    total_users = User.query.count()
    total_vehicles = Vehicle.query.count()
    
    # Get today's summary
    today = datetime.utcnow().date()
    plazas = TollPlaza.query.all()
    
    daily_summaries = []
    for plaza in plazas:
        summary = AnalyticsService.get_daily_summary(plaza.plaza_id, today)
        daily_summaries.append(summary)
    
    total_today_revenue = sum(s['total_revenue'] for s in daily_summaries)
    total_today_vehicles = sum(s['total_vehicles'] for s in daily_summaries)
    
    # Get revenue per plaza for last 7 days
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=7)
    revenue_per_plaza = AnalyticsService.get_revenue_per_plaza(start_date, end_date)
    
    # Detect fraud indicators
    fraud_indicators = AnalyticsService.detect_fraud_indicators(days=7)
    
    return render_template('admin/dashboard.html',
                          total_plazas=total_plazas,
                          total_users=total_users,
                          total_vehicles=total_vehicles,
                          today_revenue=total_today_revenue,
                          today_vehicles=total_today_vehicles,
                          daily_summaries=daily_summaries,
                          revenue_per_plaza=revenue_per_plaza,
                          fraud_indicators=fraud_indicators)

@admin_bp.route('/plazas')
@login_required
@admin_required
def plazas():
    """
    List and manage toll plazas
    """
    page = request.args.get('page', 1, type=int)
    plazas = TollPlaza.query.paginate(page=page, per_page=10)
    return render_template('admin/plazas.html', plazas=plazas)

@admin_bp.route('/plaza/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_plaza():
    """
    Add new toll plaza
    """
    if request.method == 'POST':
        plaza_name = request.form.get('plaza_name')
        location = request.form.get('location')
        num_lanes = request.form.get('num_lanes', '4')
        city = request.form.get('city')
        state = request.form.get('state')
        
        if not all([plaza_name, location, city, state]):
            flash('All fields are required', 'danger')
            return redirect(url_for('admin.add_plaza'))
        
        try:
            plaza = TollPlaza(
                plaza_name=plaza_name,
                location=location,
                num_lanes=int(num_lanes),
                city=city,
                state=state,
                created_at=datetime.utcnow()
            )
            db.session.add(plaza)
            db.session.commit()
            
            flash('Toll plaza added successfully!', 'success')
            return redirect(url_for('admin.plazas'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('admin/plaza_add.html')

@admin_bp.route('/rates', methods=['GET', 'POST'])
@login_required
@admin_required
def toll_rates():
    """
    Manage toll rates
    """
    if request.method == 'POST':
        plaza_id = request.form.get('plaza_id')
        vehicle_type = request.form.get('vehicle_type')
        from_time = request.form.get('from_time')
        to_time = request.form.get('to_time')
        time_slot = request.form.get('time_slot')
        amount = request.form.get('amount')
        
        try:
            # Check for duplicates
            existing = TollRate.query.filter(
                TollRate.plaza_id == int(plaza_id),
                TollRate.vehicle_type == VehicleType(vehicle_type),
                TollRate.from_time == from_time,
                TollRate.to_time == to_time
            ).first()
            
            if existing:
                flash('This rate configuration already exists', 'danger')
                return redirect(url_for('admin.toll_rates'))
            
            rate = TollRate(
                plaza_id=int(plaza_id),
                vehicle_type=VehicleType(vehicle_type),
                from_time=from_time,
                to_time=to_time,
                time_slot=time_slot,
                amount=float(amount),
                created_at=datetime.utcnow()
            )
            db.session.add(rate)
            db.session.commit()
            
            flash('Toll rate added successfully!', 'success')
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    plazas = TollPlaza.query.all()
    rates = TollRate.query.all()
    
    return render_template('admin/rates.html',
                          plazas=plazas,
                          rates=rates,
                          vehicle_types=VehicleType)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """
    List and manage users
    """
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users)

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """
    Detailed analytics page
    """
    # Get data for charts
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=30)
    
    # Get overall summary
    from app.models import TollTransaction
    transactions = TollTransaction.query.filter(
        TollTransaction.timestamp >= start_date,
        TollTransaction.timestamp <= end_date
    ).all()
    
    summary = {
        'total_transactions': len(transactions),
        'total_revenue': sum(t.amount for t in transactions) if transactions else 0,
        'total_vehicles': len(set(t.vehicle_id for t in transactions)) if transactions else 0,
        'avg_toll': (sum(t.amount for t in transactions) / len(transactions)) if transactions else 0
    }
    
    revenue_per_plaza = AnalyticsService.get_revenue_per_plaza(start_date, end_date)
    plazas = TollPlaza.query.all()
    
    # Get peak hours per plaza
    peak_hours_data = {}
    for plaza in plazas:
        peak_hours_data[plaza.plaza_id] = AnalyticsService.get_peak_hours(plaza.plaza_id)
    
    return render_template('admin/analytics.html',
                          summary=summary,
                          revenue_per_plaza=revenue_per_plaza,
                          plazas=plazas,
                          peak_hours_data=peak_hours_data,
                          start_date=start_date,
                          end_date=end_date)

@admin_bp.route('/api/daily-summary/<int:plaza_id>')
@login_required
@admin_required
def api_daily_summary(plaza_id):
    """
    API endpoint to get daily summary for a plaza
    """
    date_str = request.args.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        summary = AnalyticsService.get_daily_summary(plaza_id, date)
        return jsonify({'success': True, 'data': summary})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/generate-traffic-logs', methods=['POST'])
@login_required
@admin_required
def generate_traffic_logs():
    """
    Manually trigger traffic log generation
    Used before running ML predictions
    """
    result = AnalyticsService.generate_traffic_logs()
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'danger')
    
    return redirect(url_for('admin.analytics'))

@admin_bp.route('/spark-analytics')
@login_required
@admin_required
def spark_analytics():
    """
    Spark Analytics Dashboard - Big data processing and analysis
    """
    from ml_analytics.spark_analytics import SparkAnalytics
    from app.models import TollTransaction
    import json
    
    spark_stats = {
        'status': 'not_run',
        'hourly_traffic': [],
        'revenue_by_plaza': [],
        'vehicle_distribution': [],
        'peak_hours': [],
        'error': None
    }
    
    try:
        # Get transaction data for Spark processing
        transactions = TollTransaction.query.all()
        
        if transactions:
            # Create sample data for Spark analytics
            spark = SparkAnalytics()
            
            # Create sample DataFrame
            spark_stats['status'] = 'success'
            spark_stats['total_transactions'] = len(transactions)
            spark_stats['total_revenue'] = sum(t.amount for t in transactions)
            
            # Get plaza-wise revenue
            plaza_revenue = {}
            for txn in transactions:
                plaza_name = txn.plaza.plaza_name
                if plaza_name not in plaza_revenue:
                    plaza_revenue[plaza_name] = {'count': 0, 'revenue': 0}
                plaza_revenue[plaza_name]['count'] += 1
                plaza_revenue[plaza_name]['revenue'] += txn.amount
            
            spark_stats['revenue_by_plaza'] = [
                {'plaza': k, 'count': v['count'], 'revenue': round(v['revenue'], 2)}
                for k, v in plaza_revenue.items()
            ]
            
            # Vehicle type distribution
            vehicle_dist = {}
            for txn in transactions:
                vtype = txn.vehicle.vehicle_type.value
                vehicle_dist[vtype] = vehicle_dist.get(vtype, 0) + 1
            
            spark_stats['vehicle_distribution'] = [
                {'type': k, 'count': v} for k, v in vehicle_dist.items()
            ]
            
    except Exception as e:
        spark_stats['error'] = str(e)
        spark_stats['status'] = 'error'
    
    return render_template('admin/spark_analytics.html', spark_stats=spark_stats)

@admin_bp.route('/api/run-spark-analysis', methods=['POST'])
@login_required
@admin_required
def run_spark_analysis():
    """
    API endpoint to run Spark analysis and submit jobs to Spark cluster
    """
    try:
        from ml_analytics.spark_analytics import SparkAnalytics
        from app.models import TollTransaction
        
        # Initialize Spark in local mode (jobs will be visible in Web UI on port 4040)
        spark = SparkAnalytics(app_name="SmartTollAnalysis", use_local=True)
        
        # Get all transactions
        transactions = TollTransaction.query.all()
        
        if not transactions:
            return jsonify({
                'success': True,
                'message': 'No transactions to analyze',
                'job_count': 0
            })
        
        # Prepare transaction data for Spark
        txn_data = []
        for txn in transactions:
            txn_data.append({
                'txn_id': txn.txn_id,
                'vehicle_id': txn.vehicle_id,
                'plaza_id': txn.plaza_id,
                'amount': float(txn.amount),
                'timestamp': txn.timestamp.isoformat() if txn.timestamp else None,
                'vehicle_type': txn.vehicle.vehicle_type.value,
                'plaza_name': txn.plaza.plaza_name
            })
        
        # Create Spark DataFrame from transaction data
        df = spark.spark.createDataFrame(txn_data)
        print("[Spark] Created DataFrame with {} rows".format(len(txn_data)))
        
        # Submit analysis jobs
        job_count = 0
        
        # Job 1: Show DataFrame
        print("\n[Spark] Job 1: DataFrame Preview")
        df.show()
        job_count += 1
        
        # Job 2: Revenue aggregation by plaza
        print("\n[Spark] Job 2: Revenue Aggregation by Plaza")
        df.groupBy('plaza_name').agg({'amount': 'sum'}).show()
        job_count += 1
        
        # Job 3: Vehicle type distribution
        print("\n[Spark] Job 3: Vehicle Type Distribution")
        df.groupBy('vehicle_type').count().show()
        job_count += 1
        
        # Job 4: Count and cache
        print("\n[Spark] Job 4: Total Record Count")
        total_count = df.count()
        print(f"[Spark] Total transactions processed: {total_count}")
        job_count += 1
        
        return jsonify({
            'success': True,
            'message': f'✓ Spark analysis completed successfully! {job_count} jobs executed.',
            'job_count': job_count,
            'spark_ui_url': 'http://DESKTOP-9Q68UBH:4040',
            'transactions_processed': len(txn_data)
        })
    
    except Exception as e:
        import traceback
        print(f"[ERROR] Spark analysis failed: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error running Spark analysis: {str(e)}'
        })

@admin_bp.route('/spark-ui')
@login_required
@admin_required
def spark_ui():
    """
    Apache Spark UI - Real-time job monitoring and task execution tracking
    Shows cluster status, jobs, stages, tasks, executors, and data flow
    Connected to external Spark Web UI at http://DESKTOP-9Q68UBH:4040
    """
    spark_ui_url = "http://DESKTOP-9Q68UBH:4040"
    return render_template('admin/spark_ui.html', spark_ui_url=spark_ui_url)

@admin_bp.route('/spark-integration')
@login_required
@admin_required
def spark_integration():
    """
    Spark Integration Dashboard
    Real-time synchronization between Flask and Spark cluster
    """
    return render_template('admin/spark_integration.html')

@admin_bp.route('/api/spark-status')
@login_required
@admin_required
def api_spark_status():
    """
    Get real-time Spark cluster status
    """
    from app.services.spark_integration_service import SparkIntegrationService
    status = SparkIntegrationService.get_spark_status()
    return jsonify(status)

@admin_bp.route('/api/spark-jobs')
@login_required
@admin_required
def api_spark_jobs():
    """
    Get all Spark jobs from cluster
    """
    from app.services.spark_integration_service import SparkIntegrationService
    jobs = SparkIntegrationService.get_spark_jobs()
    return jsonify(jobs)

@admin_bp.route('/api/spark-storage')
@login_required
@admin_required
def api_spark_storage():
    """
    Get Spark RDD/Storage information
    """
    from app.services.spark_integration_service import SparkIntegrationService
    jobs_data = SparkIntegrationService.get_spark_jobs()
    # Extract storage data from jobs response
    storage = jobs_data.get('storage', [])
    return jsonify({
        'success': True,
        'storage': storage,
        'total_rdds': len(storage),
        'timestamp': jobs_data.get('timestamp')
    })

@admin_bp.route('/api/realtime-metrics')
@login_required
@admin_required
def api_realtime_metrics():
    """
    Get real-time metrics combining Flask DB and Spark cluster
    """
    from app.services.spark_integration_service import SparkIntegrationService
    metrics = SparkIntegrationService.get_realtime_metrics()
    return jsonify(metrics)

@admin_bp.route('/api/transaction-summary')
@login_required
@admin_required
def api_transaction_summary():
    """
    Get transaction summary for Spark analysis
    """
    from app.services.spark_integration_service import SparkIntegrationService
    summary = SparkIntegrationService.get_transaction_summary_for_spark()
    return jsonify(summary)

@admin_bp.route('/api/export-data/<int:days>')
@login_required
@admin_required
def api_export_data(days=7):
    """
    Export transaction data for Spark processing
    """
    from app.services.spark_integration_service import SparkIntegrationService
    data = SparkIntegrationService.export_data_to_spark(days)
    return jsonify(data)

@admin_bp.route('/ml-predictions')
@login_required
@admin_required
def ml_predictions():
    """
    ML-based Traffic Prediction Dashboard
    Provides AI-powered traffic forecasting and advanced features:
    - 24-hour traffic forecasting
    - Dynamic toll pricing
    - Anomaly detection
    - Congestion management
    - Route optimization
    """
    return render_template('admin/ml_predictions.html')

