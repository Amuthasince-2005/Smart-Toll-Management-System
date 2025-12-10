"""
API Routes - REST API endpoints for ML predictions and data
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import UserRole, TollPlaza, TrafficLog
from datetime import datetime, timedelta
import os
import pickle
import json

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Load trained ML model (if available)
ML_MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'traffic_predictor.pkl')
ml_model = None

try:
    if os.path.exists(ML_MODEL_PATH):
        with open(ML_MODEL_PATH, 'rb') as f:
            ml_model = pickle.load(f)
        print(f"[{datetime.now()}] ML Model loaded successfully from {ML_MODEL_PATH}")
except Exception as e:
    print(f"[{datetime.now()}] Warning: Could not load ML model - {str(e)}")

@api_bp.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'ml_model_loaded': ml_model is not None
    })

@api_bp.route('/predict-traffic', methods=['GET', 'POST'])
@login_required
def predict_traffic():
    """
    Predict traffic for a toll plaza
    
    Parameters:
        plaza_id: ID of the toll plaza
        hours_ahead: Number of hours ahead to predict (default: 1)
        date: Date to predict for (YYYY-MM-DD, default: today)
        hour: Hour of day (0-23, optional, default: current hour)
    
    Returns:
        JSON with prediction result
    """
    # Authorization check
    if current_user.role not in [UserRole.ADMIN, UserRole.TOLL_OPERATOR]:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        plaza_id = request.args.get('plaza_id') or request.json.get('plaza_id')
        hours_ahead = int(request.args.get('hours_ahead', 1))
        date_str = request.args.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
        
        plaza_id = int(plaza_id)
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Validate plaza
        plaza = TollPlaza.query.get(plaza_id)
        if not plaza:
            return jsonify({'success': False, 'message': 'Plaza not found'}), 404
        
        # If ML model is loaded, use it for predictions
        if ml_model:
            predictions = _get_ml_predictions(plaza_id, date, hours_ahead)
        else:
            # Fallback: Use historical data or simple heuristics
            predictions = _get_historical_baseline(plaza_id, date, hours_ahead)
        
        return jsonify({
            'success': True,
            'plaza_id': plaza_id,
            'plaza_name': plaza.plaza_name,
            'date': str(date),
            'hours_ahead': hours_ahead,
            'predictions': predictions,
            'ml_model_used': ml_model is not None
        })
    
    except ValueError as e:
        return jsonify({'success': False, 'message': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@api_bp.route('/traffic-summary/<int:plaza_id>', methods=['GET'])
@login_required
def traffic_summary(plaza_id):
    """
    Get traffic summary for a plaza
    
    Parameters:
        days: Number of days to include (default: 7)
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.TOLL_OPERATOR]:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        days = int(request.args.get('days', 7))
        plaza = TollPlaza.query.get(plaza_id)
        
        if not plaza:
            return jsonify({'success': False, 'message': 'Plaza not found'}), 404
        
        cutoff_date = datetime.utcnow().date() - timedelta(days=days)
        
        logs = TrafficLog.query.filter(
            TrafficLog.plaza_id == plaza_id,
            TrafficLog.date >= cutoff_date
        ).order_by(TrafficLog.date.desc(), TrafficLog.hour.desc()).all()
        
        # Calculate statistics
        total_vehicles = sum(log.vehicle_count for log in logs)
        total_revenue = sum(log.total_revenue for log in logs)
        avg_vehicles_per_hour = total_vehicles / len(logs) if logs else 0
        
        # Traffic level breakdown
        traffic_levels = {'low': 0, 'normal': 0, 'high': 0}
        for log in logs:
            traffic_levels[log.traffic_level] += 1
        
        return jsonify({
            'success': True,
            'plaza_id': plaza_id,
            'plaza_name': plaza.plaza_name,
            'period_days': days,
            'statistics': {
                'total_vehicles': total_vehicles,
                'total_revenue': total_revenue,
                'avg_vehicles_per_hour': round(avg_vehicles_per_hour, 2),
                'traffic_levels': traffic_levels
            },
            'recent_logs': [
                {
                    'date': str(log.date),
                    'hour': log.hour,
                    'vehicle_count': log.vehicle_count,
                    'total_revenue': log.total_revenue,
                    'traffic_level': log.traffic_level
                }
                for log in logs[:24]  # Last 24 records
            ]
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@api_bp.route('/pricing-recommendation/<int:plaza_id>', methods=['GET'])
@login_required
def pricing_recommendation(plaza_id):
    """
    Get dynamic pricing recommendation based on traffic predictions
    
    Returns pricing recommendation: Low/Normal/High tariff
    """
    if current_user.role != UserRole.ADMIN:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        plaza = TollPlaza.query.get(plaza_id)
        if not plaza:
            return jsonify({'success': False, 'message': 'Plaza not found'}), 404
        
        # Get predictions for next few hours
        predictions = _get_ml_predictions(
            plaza_id,
            datetime.utcnow().date(),
            hours_ahead=6
        )
        
        # Calculate recommendation based on average predicted traffic
        avg_vehicle_count = sum(p['predicted_vehicles'] for p in predictions) / len(predictions) if predictions else 0
        
        if avg_vehicle_count > 150:
            recommendation = 'High'
            multiplier = 1.3
            reason = 'High traffic predicted'
        elif avg_vehicle_count > 75:
            recommendation = 'Normal'
            multiplier = 1.0
            reason = 'Normal traffic predicted'
        else:
            recommendation = 'Low'
            multiplier = 0.8
            reason = 'Low traffic predicted'
        
        return jsonify({
            'success': True,
            'plaza_id': plaza_id,
            'plaza_name': plaza.plaza_name,
            'recommendation': recommendation,
            'tariff_multiplier': multiplier,
            'reason': reason,
            'avg_predicted_vehicles': round(avg_vehicle_count, 2),
            'next_hours_predictions': predictions
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# ============================================================================
# Helper Functions for Predictions
# ============================================================================

def _get_ml_predictions(plaza_id, date, hours_ahead=6):
    """
    Get predictions using trained ML model
    
    Args:
        plaza_id: ID of the toll plaza
        date: Date to predict for
        hours_ahead: Number of hours to predict
    
    Returns:
        List of predictions
    """
    global ml_model
    
    if not ml_model:
        return _get_historical_baseline(plaza_id, date, hours_ahead)
    
    try:
        import numpy as np
        
        predictions = []
        current_hour = datetime.utcnow().hour
        
        for i in range(hours_ahead):
            hour = (current_hour + i + 1) % 24
            
            # Prepare features for ML model
            # Assuming model expects: [plaza_id, hour, day_of_week, is_peak]
            day_of_week = date.weekday()
            is_peak = 1 if (7 <= hour < 10) or (17 <= hour < 20) else 0
            
            features = np.array([[plaza_id, hour, day_of_week, is_peak]])
            
            try:
                predicted_vehicles = max(0, int(ml_model.predict(features)[0]))
                traffic_level = _determine_traffic_level(predicted_vehicles)
                
                predictions.append({
                    'hour': hour,
                    'predicted_vehicles': predicted_vehicles,
                    'traffic_level': traffic_level,
                    'confidence': 0.75  # Placeholder confidence score
                })
            except:
                # If prediction fails, use baseline
                baseline = _get_hourly_baseline(plaza_id, hour)
                traffic_level = _determine_traffic_level(baseline)
                predictions.append({
                    'hour': hour,
                    'predicted_vehicles': baseline,
                    'traffic_level': traffic_level,
                    'confidence': 0.5
                })
        
        return predictions
    
    except Exception as e:
        print(f"ML prediction error: {str(e)}")
        return _get_historical_baseline(plaza_id, date, hours_ahead)

def _get_historical_baseline(plaza_id, date, hours_ahead=6):
    """
    Get baseline predictions from historical data
    """
    predictions = []
    current_hour = datetime.utcnow().hour
    
    for i in range(hours_ahead):
        hour = (current_hour + i + 1) % 24
        baseline = _get_hourly_baseline(plaza_id, hour)
        traffic_level = _determine_traffic_level(baseline)
        
        predictions.append({
            'hour': hour,
            'predicted_vehicles': baseline,
            'traffic_level': traffic_level,
            'confidence': 0.5
        })
    
    return predictions

def _get_hourly_baseline(plaza_id, hour):
    """
    Get average vehicle count for a specific hour from historical data
    """
    from app.models import TrafficLog
    
    # Get average for this hour from last 30 days
    cutoff_date = datetime.utcnow().date() - timedelta(days=30)
    
    logs = TrafficLog.query.filter(
        TrafficLog.plaza_id == plaza_id,
        TrafficLog.hour == hour,
        TrafficLog.date >= cutoff_date
    ).all()
    
    if logs:
        return int(sum(log.vehicle_count for log in logs) / len(logs))
    
    # Default baseline based on hour
    if 7 <= hour < 10 or 17 <= hour < 20:
        return 100  # Peak hours
    elif 11 <= hour < 16:
        return 50   # Off-peak
    else:
        return 20   # Night hours

def _determine_traffic_level(vehicle_count):
    """
    Determine traffic level based on vehicle count
    """
    if vehicle_count > 150:
        return 'high'
    elif vehicle_count > 75:
        return 'normal'
    else:
        return 'low'
