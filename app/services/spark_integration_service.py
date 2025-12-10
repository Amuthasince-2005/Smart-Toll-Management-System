"""
Spark Integration Service
Real-time synchronization between Flask database and Spark cluster
Handles job submission, monitoring, and data sync
"""

import requests
import json
from datetime import datetime, timedelta
from app import db
from app.models import TollTransaction, TollPlaza, Vehicle, Wallet

class SparkIntegrationService:
    """
    Service to integrate Flask with Apache Spark
    Submits jobs, monitors execution, and syncs data
    """
    
    SPARK_UI_URL = "http://DESKTOP-9Q68UBH:4040"
    SPARK_API_URL = "http://DESKTOP-9Q68UBH:4040/api"
    
    @staticmethod
    def get_spark_status():
        """
        Get current Spark cluster status and job information
        """
        try:
            # Get Spark API status
            response = requests.get(f"{SparkIntegrationService.SPARK_API_URL}/v1/applications", timeout=5)
            
            if response.status_code == 200:
                applications = response.json()
                return {
                    'status': 'connected',
                    'url': SparkIntegrationService.SPARK_UI_URL,
                    'applications': applications,
                    'timestamp': datetime.utcnow().isoformat()
                }
        except requests.exceptions.ConnectionError:
            return {
                'status': 'disconnected',
                'message': f'Cannot connect to Spark at {SparkIntegrationService.SPARK_UI_URL}',
                'url': SparkIntegrationService.SPARK_UI_URL,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def get_spark_jobs():
        """
        Get list of all Spark jobs from the cluster
        Also includes RDD/DataFrame information as storage data
        """
        try:
            response = requests.get(
                f"{SparkIntegrationService.SPARK_API_URL}/v1/applications",
                timeout=5
            )
            
            if response.status_code == 200:
                apps = response.json()
                jobs_info = []
                storage_info = []
                
                for app in apps:
                    app_id = app.get('id')
                    app_name = app.get('name')
                    
                    # Get Jobs
                    try:
                        jobs_response = requests.get(
                            f"{SparkIntegrationService.SPARK_API_URL}/v1/applications/{app_id}/jobs",
                            timeout=5
                        )
                        if jobs_response.status_code == 200:
                            jobs = jobs_response.json()
                            jobs_info.extend([
                                {
                                    'job_id': job.get('jobId'),
                                    'app_id': app_id,
                                    'app_name': app_name,
                                    'status': job.get('status'),
                                    'submitted_time': job.get('submissionTime'),
                                    'completion_time': job.get('completionTime'),
                                    'stage_ids': job.get('stageIds', []),
                                    'num_tasks': job.get('numTasks', 0),
                                    'completed_tasks': job.get('numCompletedTasks', 0)
                                }
                                for job in jobs
                            ])
                    except:
                        pass
                    
                    # Get RDD Storage (if available)
                    try:
                        storage_response = requests.get(
                            f"{SparkIntegrationService.SPARK_API_URL}/v1/applications/{app_id}/storage/rdd",
                            timeout=5
                        )
                        if storage_response.status_code == 200:
                            rdds = storage_response.json()
                            storage_info.extend([
                                {
                                    'rdd_id': rdd.get('id'),
                                    'app_id': app_id,
                                    'app_name': app_name,
                                    'name': rdd.get('name', 'RDD'),
                                    'num_partitions': rdd.get('numPartitions', 0),
                                    'memory_used': rdd.get('memoryUsed', 0),
                                    'disk_used': rdd.get('diskUsed', 0),
                                    'cache_level': rdd.get('cacheLevel', 'NONE')
                                }
                                for rdd in rdds
                            ])
                    except:
                        pass
                
                return {
                    'success': True,
                    'jobs': jobs_info,
                    'storage': storage_info,
                    'total_jobs': len(jobs_info),
                    'total_rdds': len(storage_info),
                    'timestamp': datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'jobs': [],
                'storage': [],
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def get_transaction_summary_for_spark():
        """
        Get transaction summary data for Spark processing
        """
        try:
            transactions = TollTransaction.query.all()
            
            summary = {
                'total_transactions': len(transactions),
                'total_revenue': sum(t.amount for t in transactions) if transactions else 0,
                'date_range': {
                    'start': min(t.timestamp for t in transactions).isoformat() if transactions else None,
                    'end': max(t.timestamp for t in transactions).isoformat() if transactions else None
                },
                'by_plaza': {},
                'by_vehicle_type': {},
                'by_payment_mode': {}
            }
            
            # Group by plaza
            for txn in transactions:
                plaza_name = txn.plaza.plaza_name
                if plaza_name not in summary['by_plaza']:
                    summary['by_plaza'][plaza_name] = {'count': 0, 'revenue': 0}
                summary['by_plaza'][plaza_name]['count'] += 1
                summary['by_plaza'][plaza_name]['revenue'] += txn.amount
            
            # Group by vehicle type
            for txn in transactions:
                vtype = txn.vehicle.vehicle_type.value
                if vtype not in summary['by_vehicle_type']:
                    summary['by_vehicle_type'][vtype] = {'count': 0, 'revenue': 0}
                summary['by_vehicle_type'][vtype]['count'] += 1
                summary['by_vehicle_type'][vtype]['revenue'] += txn.amount
            
            # Group by payment mode
            for txn in transactions:
                pmode = txn.payment_mode.value
                if pmode not in summary['by_payment_mode']:
                    summary['by_payment_mode'][pmode] = {'count': 0, 'revenue': 0}
                summary['by_payment_mode'][pmode]['count'] += 1
                summary['by_payment_mode'][pmode]['revenue'] += txn.amount
            
            return {
                'success': True,
                'data': summary
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    @staticmethod
    def get_realtime_metrics():
        """
        Get real-time metrics combining Flask DB and Spark cluster
        """
        try:
            # Get database metrics
            transactions = TollTransaction.query.all()
            users = db.session.query(db.func.count(db.distinct('user_id'))).scalar() or 0
            plazas = TollPlaza.query.count()
            vehicles = Vehicle.query.count()
            
            # Get Spark status
            spark_status = SparkIntegrationService.get_spark_status()
            spark_jobs = SparkIntegrationService.get_spark_jobs()
            
            # Calculate additional metrics
            today = datetime.utcnow().date()
            today_transactions = TollTransaction.query.filter(
                db.func.date(TollTransaction.timestamp) == today
            ).all()
            
            return {
                'success': True,
                'database': {
                    'total_transactions': len(transactions),
                    'today_transactions': len(today_transactions),
                    'total_revenue': sum(t.amount for t in transactions) if transactions else 0,
                    'today_revenue': sum(t.amount for t in today_transactions) if today_transactions else 0,
                    'unique_users': users,
                    'total_plazas': plazas,
                    'total_vehicles': vehicles
                },
                'spark': {
                    'cluster_status': spark_status.get('status'),
                    'cluster_url': SparkIntegrationService.SPARK_UI_URL,
                    'active_jobs': spark_jobs.get('total_jobs', 0) if spark_jobs.get('success') else 0,
                    'jobs': spark_jobs.get('jobs', []) if spark_jobs.get('success') else []
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    @staticmethod
    def export_data_to_spark(days=7):
        """
        Export transaction data for Spark processing
        Returns data in Spark-compatible format
        """
        try:
            start_date = datetime.utcnow().date() - timedelta(days=days)
            transactions = TollTransaction.query.filter(
                db.func.date(TollTransaction.timestamp) >= start_date
            ).all()
            
            data = []
            for txn in transactions:
                data.append({
                    'txn_id': txn.txn_id,
                    'vehicle_id': txn.vehicle_id,
                    'plaza_id': txn.plaza_id,
                    'amount': float(txn.amount),
                    'timestamp': txn.timestamp.isoformat(),
                    'vehicle_type': txn.vehicle.vehicle_type.value,
                    'plaza_name': txn.plaza.plaza_name,
                    'payment_mode': txn.payment_mode.value
                })
            
            return {
                'success': True,
                'total_records': len(data),
                'data': data,
                'export_timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
