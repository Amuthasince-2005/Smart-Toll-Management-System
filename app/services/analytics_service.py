"""
Analytics Service - Handles analytics and traffic data aggregation
"""

from app import db
from app.models import TollTransaction, TrafficLog, TollPlaza
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import json

class AnalyticsService:
    """
    Service class for analytics, traffic aggregation, and reporting
    """
    
    @staticmethod
    def aggregate_hourly_traffic(plaza_id, date):
        """
        Aggregate traffic data for a plaza by hour
        
        Args:
            plaza_id: ID of the toll plaza
            date: Date to aggregate (date object)
        
        Returns:
            List of hourly traffic data
        """
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = datetime.combine(date, datetime.max.time())
        
        hourly_data = db.session.query(
            func.strftime('%H', TollTransaction.timestamp).label('hour'),
            func.count(TollTransaction.txn_id).label('vehicle_count'),
            func.sum(TollTransaction.amount).label('total_revenue')
        ).filter(
            and_(
                TollTransaction.plaza_id == plaza_id,
                TollTransaction.timestamp >= start_of_day,
                TollTransaction.timestamp <= end_of_day
            )
        ).group_by(
            func.strftime('%H', TollTransaction.timestamp)
        ).all()
        
        return hourly_data
    
    @staticmethod
    def generate_traffic_logs():
        """
        Generate traffic log entries from toll transactions.
        This aggregates recent transactions into the TrafficLog table.
        Called periodically (e.g., hourly) via scheduled job or manually.
        
        Returns:
            Dictionary with aggregation result
        """
        try:
            # Get all toll plazas
            plazas = TollPlaza.query.all()
            logs_created = 0
            
            for plaza in plazas:
                # Get last 24 hours of transactions
                last_24h = datetime.utcnow() - timedelta(days=1)
                
                transactions = TollTransaction.query.filter(
                    and_(
                        TollTransaction.plaza_id == plaza.plaza_id,
                        TollTransaction.timestamp >= last_24h
                    )
                ).all()
                
                # Group by hour
                hours_data = {}
                for txn in transactions:
                    hour_key = txn.timestamp.strftime('%Y-%m-%d %H:00:00')
                    if hour_key not in hours_data:
                        hours_data[hour_key] = {'count': 0, 'revenue': 0}
                    hours_data[hour_key]['count'] += 1
                    hours_data[hour_key]['revenue'] += txn.amount
                
                # Create or update traffic log entries
                for hour_str, data in hours_data.items():
                    dt = datetime.strptime(hour_str, '%Y-%m-%d %H:%M:%S')
                    date = dt.date()
                    hour = dt.hour
                    
                    # Determine traffic level (can be refined with ML)
                    vehicle_count = data['count']
                    if vehicle_count > 100:
                        traffic_level = 'high'
                    elif vehicle_count > 50:
                        traffic_level = 'normal'
                    else:
                        traffic_level = 'low'
                    
                    # Check if log exists
                    existing_log = TrafficLog.query.filter(
                        and_(
                            TrafficLog.plaza_id == plaza.plaza_id,
                            TrafficLog.date == date,
                            TrafficLog.hour == hour
                        )
                    ).first()
                    
                    if existing_log:
                        existing_log.vehicle_count = data['count']
                        existing_log.total_revenue = data['revenue']
                        existing_log.traffic_level = traffic_level
                    else:
                        new_log = TrafficLog(
                            plaza_id=plaza.plaza_id,
                            date=date,
                            hour=hour,
                            vehicle_count=data['count'],
                            total_revenue=data['revenue'],
                            traffic_level=traffic_level
                        )
                        db.session.add(new_log)
                        logs_created += 1
            
            db.session.commit()
            return {
                'success': True,
                'message': f'Generated/updated traffic logs for {logs_created} entries',
                'logs_created': logs_created
            }
        
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error generating traffic logs: {str(e)}'
            }
    
    @staticmethod
    def get_daily_summary(plaza_id, date):
        """
        Get daily summary for a toll plaza
        
        Args:
            plaza_id: ID of the toll plaza
            date: Date to summarize
        
        Returns:
            Dictionary with daily summary
        """
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = datetime.combine(date, datetime.max.time())
        
        transactions = TollTransaction.query.filter(
            and_(
                TollTransaction.plaza_id == plaza_id,
                TollTransaction.timestamp >= start_of_day,
                TollTransaction.timestamp <= end_of_day
            )
        ).all()
        
        total_vehicles = len(transactions)
        total_revenue = sum(t.amount for t in transactions)
        
        # Group by hour
        hourly = {}
        for txn in transactions:
            hour = txn.timestamp.hour
            if hour not in hourly:
                hourly[hour] = {'count': 0, 'revenue': 0}
            hourly[hour]['count'] += 1
            hourly[hour]['revenue'] += txn.amount
        
        return {
            'date': str(date),
            'plaza_id': plaza_id,
            'total_vehicles': total_vehicles,
            'total_revenue': total_revenue,
            'hourly_breakdown': hourly,
            'peak_hour': max(hourly, key=lambda k: hourly[k]['count']) if hourly else None
        }
    
    @staticmethod
    def get_revenue_per_plaza(start_date, end_date):
        """
        Get revenue aggregated per plaza for a date range
        
        Args:
            start_date: Start date
            end_date: End date
        
        Returns:
            List of plaza revenue data
        """
        results = db.session.query(
            TollTransaction.plaza_id,
            TollPlaza.plaza_name,
            func.count(TollTransaction.txn_id).label('vehicle_count'),
            func.sum(TollTransaction.amount).label('total_revenue')
        ).join(TollPlaza).filter(
            and_(
                TollTransaction.timestamp >= datetime.combine(start_date, datetime.min.time()),
                TollTransaction.timestamp <= datetime.combine(end_date, datetime.max.time())
            )
        ).group_by(TollTransaction.plaza_id, TollPlaza.plaza_name).all()
        
        return [
            {
                'plaza_id': r[0],
                'plaza_name': r[1],
                'vehicle_count': r[2],
                'total_revenue': float(r[3]) if r[3] else 0
            }
            for r in results
        ]
    
    @staticmethod
    def detect_fraud_indicators(days=7):
        """
        Detect potential fraud patterns (repeated unpaid entries, etc.)
        
        Args:
            days: Number of days to analyze
        
        Returns:
            List of vehicles with suspicious patterns
        """
        from app.models import Vehicle
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Find vehicles with multiple failed payments
        suspicious_vehicles = []
        vehicles = Vehicle.query.all()
        
        for vehicle in vehicles:
            failed_txns = TollTransaction.query.filter(
                and_(
                    TollTransaction.vehicle_id == vehicle.vehicle_id,
                    TollTransaction.status == 'failed',
                    TollTransaction.timestamp >= cutoff_date
                )
            ).count()
            
            if failed_txns >= 3:
                suspicious_vehicles.append({
                    'vehicle_id': vehicle.vehicle_id,
                    'vehicle_number': vehicle.vehicle_number,
                    'failed_transactions': failed_txns,
                    'vehicle_type': vehicle.vehicle_type.value
                })
        
        return suspicious_vehicles
    
    @staticmethod
    def get_peak_hours(plaza_id, days=7):
        """
        Get peak traffic hours for a plaza
        
        Args:
            plaza_id: ID of the toll plaza
            days: Number of days to analyze
        
        Returns:
            List of hours sorted by vehicle count (descending)
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        results = db.session.query(
            func.strftime('%H', TollTransaction.timestamp).label('hour'),
            func.count(TollTransaction.txn_id).label('vehicle_count')
        ).filter(
            and_(
                TollTransaction.plaza_id == plaza_id,
                TollTransaction.timestamp >= cutoff_date
            )
        ).group_by(
            func.strftime('%H', TollTransaction.timestamp)
        ).order_by(db.desc('vehicle_count')).all()
        
        return [
            {'hour': int(r[0]), 'vehicle_count': r[1]}
            for r in results
        ]
