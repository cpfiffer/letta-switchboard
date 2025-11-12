import pytest
from datetime import datetime, timezone, timedelta
from scheduler import is_recurring_schedule_due, is_onetime_schedule_due


class TestRecurringScheduleDue:
    def test_new_schedule_is_due(self):
        """A newly created schedule with no last_run should be due."""
        schedule = {
            "cron": "* * * * *",
            "created_at": (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat(),
        }
        current_time = datetime.now(timezone.utc)
        
        assert is_recurring_schedule_due(schedule, current_time) is True
    
    def test_just_ran_not_due(self):
        """A schedule that just ran should not be due yet."""
        schedule = {
            "cron": "*/5 * * * *",
            "created_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            "last_run": datetime.now(timezone.utc).isoformat(),
        }
        current_time = datetime.now(timezone.utc)
        
        assert is_recurring_schedule_due(schedule, current_time) is False
    
    def test_five_minutes_ago_is_due(self):
        """A schedule with last_run 5+ minutes ago should be due (cron every 5 min)."""
        schedule = {
            "cron": "*/5 * * * *",
            "created_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            "last_run": (datetime.now(timezone.utc) - timedelta(minutes=6)).isoformat(),
        }
        current_time = datetime.now(timezone.utc)
        
        assert is_recurring_schedule_due(schedule, current_time) is True
    
    def test_daily_cron_not_due(self):
        """Daily schedule that ran today should not be due."""
        schedule = {
            "cron": "0 9 * * *",  # Every day at 9am
            "created_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            "last_run": datetime.now(timezone.utc).isoformat(),
        }
        current_time = datetime.now(timezone.utc)
        
        assert is_recurring_schedule_due(schedule, current_time) is False
    
    def test_timezone_aware_comparison(self):
        """Timezone-aware datetimes should be handled correctly."""
        schedule = {
            "cron": "*/5 * * * *",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        current_time = datetime.now(timezone.utc)
        
        # Should not raise timezone comparison errors
        is_recurring_schedule_due(schedule, current_time)


class TestOneTimeScheduleDue:
    def test_past_schedule_is_due(self):
        """Schedule in the past should be due for execution."""
        past_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        schedule = {
            "execute_at": past_time.isoformat(),
            "executed": False,
        }
        current_time = datetime.now(timezone.utc)
        
        assert is_onetime_schedule_due(schedule, current_time) is True
    
    def test_future_schedule_not_due(self):
        """Schedule in the future should not be due."""
        future_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        schedule = {
            "execute_at": future_time.isoformat(),
        }
        current_time = datetime.now(timezone.utc)
        
        assert is_onetime_schedule_due(schedule, current_time) is False
    
    def test_executed_schedule_not_due(self):
        """Already executed schedule should not be due (legacy check)."""
        past_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        schedule = {
            "execute_at": past_time.isoformat(),
            "executed": True,
        }
        current_time = datetime.now(timezone.utc)
        
        assert is_onetime_schedule_due(schedule, current_time) is False
    
    def test_timezone_est(self):
        """Schedule with EST timezone should be handled correctly."""
        # 2 hours ago EST
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)
        schedule = {
            "execute_at": past_time.isoformat(),
        }
        current_time = datetime.now(timezone.utc)
        
        assert is_onetime_schedule_due(schedule, current_time) is True
    
    def test_timezone_naive_defaults_utc(self):
        """Timezone-naive timestamps should be treated as UTC."""
        past_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        schedule = {
            "execute_at": past_time.replace(tzinfo=None).isoformat(),
        }
        current_time = datetime.now(timezone.utc)
        
        assert is_onetime_schedule_due(schedule, current_time) is True
    
    def test_exact_time_is_due(self):
        """Schedule at exactly current time should be due."""
        current_time = datetime.now(timezone.utc)
        schedule = {
            "execute_at": current_time.isoformat(),
        }
        
        assert is_onetime_schedule_due(schedule, current_time) is True
