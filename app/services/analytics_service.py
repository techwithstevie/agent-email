import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional

class AnalyticsService:
    def __init__(self, analytics_file='app/analytics_data.json'):
        self.analytics_file = analytics_file
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Load analytics data from file"""
        default_data = {
            'emails_sent': 0,
            'emails_received': 0,
            'emails_scheduled': 0,
            'response_times': [],
            'email_categories': defaultdict(int),
            'daily_activity': defaultdict(int),
            'top_contacts': defaultdict(int),
            'template_usage': defaultdict(int),
            'activity_log': []
        }
        
        if os.path.exists(self.analytics_file):
            try:
                with open(self.analytics_file, 'r') as f:
                    loaded_data = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    for key, value in default_data.items():
                        if key not in loaded_data:
                            loaded_data[key] = value
                        elif isinstance(value, defaultdict):
                            loaded_data[key] = defaultdict(int, loaded_data.get(key, {}))
                    return loaded_data
            except Exception as e:
                print(f"Error loading analytics data: {e}")
                return default_data
        
        return default_data
    
    def _save_data(self):
        """Save analytics data to file"""
        try:
            # Convert defaultdicts to regular dicts for JSON serialization
            save_data = {}
            for key, value in self.data.items():
                if isinstance(value, defaultdict):
                    save_data[key] = dict(value)
                else:
                    save_data[key] = value
            
            with open(self.analytics_file, 'w') as f:
                json.dump(save_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving analytics data: {e}")
    
    def track_email_sent(self, to: str, category: str = 'general', template_id: str = None):
        """Track when an email is sent"""
        self.data['emails_sent'] += 1
        self.data['email_categories'][category] += 1
        self.data['top_contacts'][to] += 1
        
        if template_id:
            self.data['template_usage'][template_id] += 1
        
        # Track daily activity
        today = datetime.now().strftime('%Y-%m-%d')
        self.data['daily_activity'][today] += 1
        
        # Log activity
        self.data['activity_log'].append({
            'timestamp': datetime.now().isoformat(),
            'action': 'email_sent',
            'to': to,
            'category': category,
            'template_id': template_id
        })
        
        self._save_data()
    
    def track_email_received(self, from_addr: str, category: str = 'general'):
        """Track when an email is received"""
        self.data['emails_received'] += 1
        self.data['email_categories'][category] += 1
        self.data['top_contacts'][from_addr] += 1
        
        # Track daily activity
        today = datetime.now().strftime('%Y-%m-%d')
        self.data['daily_activity'][today] += 1
        
        # Log activity
        self.data['activity_log'].append({
            'timestamp': datetime.now().isoformat(),
            'action': 'email_received',
            'from': from_addr,
            'category': category
        })
        
        self._save_data()
    
    def track_email_scheduled(self, to: str, scheduled_time: str):
        """Track when an email is scheduled"""
        self.data['emails_scheduled'] += 1
        self.data['top_contacts'][to] += 1
        
        # Log activity
        self.data['activity_log'].append({
            'timestamp': datetime.now().isoformat(),
            'action': 'email_scheduled',
            'to': to,
            'scheduled_time': scheduled_time
        })
        
        self._save_data()
    
    def track_response_time(self, response_time_minutes: float):
        """Track email response time in minutes"""
        self.data['response_times'].append(response_time_minutes)
        self._save_data()
    
    def get_analytics_summary(self) -> Dict:
        """Get overall analytics summary"""
        total_emails = self.data['emails_sent'] + self.data['emails_received']
        avg_response_time = None
        if self.data['response_times']:
            avg_response_time = sum(self.data['response_times']) / len(self.data['response_times'])
        
        return {
            "success": True,
            "summary": {
                "total_emails": total_emails,
                "emails_sent": self.data['emails_sent'],
                "emails_received": self.data['emails_received'],
                "emails_scheduled": self.data['emails_scheduled'],
                "average_response_time_minutes": avg_response_time,
                "unique_contacts": len(self.data['top_contacts'])
            }
        }
    
    def get_email_categories(self) -> Dict:
        """Get email distribution by category"""
        return {
            "success": True,
            "categories": dict(self.data['email_categories'])
        }
    
    def get_daily_activity(self, days: int = 30) -> Dict:
        """Get daily email activity for specified number of days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        activity_data = {}
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            activity_data[date_str] = self.data['daily_activity'].get(date_str, 0)
            current_date += timedelta(days=1)
        
        return {
            "success": True,
            "daily_activity": activity_data,
            "period": f"{days} days"
        }
    
    def get_top_contacts(self, limit: int = 10) -> Dict:
        """Get top contacts by email frequency"""
        sorted_contacts = sorted(
            self.data['top_contacts'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return {
            "success": True,
            "top_contacts": [
                {"email": contact, "count": count}
                for contact, count in sorted_contacts
            ]
        }
    
    def get_template_usage(self) -> Dict:
        """Get template usage statistics"""
        return {
            "success": True,
            "template_usage": dict(self.data['template_usage'])
        }
    
    def get_activity_log(self, limit: int = 50) -> Dict:
        """Get recent activity log"""
        recent_activities = self.data['activity_log'][-limit:]
        return {
            "success": True,
            "activity_log": recent_activities
        }
    
    def get_hourly_activity(self) -> Dict:
        """Get email activity by hour of day"""
        hourly_activity = defaultdict(int)
        
        for log in self.data['activity_log']:
            try:
                timestamp = datetime.fromisoformat(log['timestamp'])
                hour = timestamp.hour
                hourly_activity[hour] += 1
            except:
                continue
        
        return {
            "success": True,
            "hourly_activity": dict(hourly_activity)
        }
    
    def get_analytics_trends(self, days: int = 7) -> Dict:
        """Get analytics trends for comparison"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        previous_start = start_date - timedelta(days=days)
        
        current_period_emails = 0
        previous_period_emails = 0
        
        for date_str, count in self.data['daily_activity'].items():
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
                if start_date <= date <= end_date:
                    current_period_emails += count
                elif previous_start <= date < start_date:
                    previous_period_emails += count
            except:
                continue
        
        trend_percentage = 0
        if previous_period_emails > 0:
            trend_percentage = ((current_period_emails - previous_period_emails) / previous_period_emails) * 100
        
        return {
            "success": True,
            "trends": {
                "current_period_emails": current_period_emails,
                "previous_period_emails": previous_period_emails,
                "trend_percentage": round(trend_percentage, 2),
                "period_days": days
            }
        }
    
    def reset_analytics(self) -> Dict:
        """Reset all analytics data"""
        self.data = {
            'emails_sent': 0,
            'emails_received': 0,
            'emails_scheduled': 0,
            'response_times': [],
            'email_categories': defaultdict(int),
            'daily_activity': defaultdict(int),
            'top_contacts': defaultdict(int),
            'template_usage': defaultdict(int),
            'activity_log': []
        }
        self._save_data()
        return {"success": True, "message": "Analytics data reset"}