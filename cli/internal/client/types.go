package client

import (
	"encoding/json"
	"time"
)

// FlexTime is a custom time type that can parse both RFC3339 and ISO8601 without timezone
type FlexTime struct {
	time.Time
}

// UnmarshalJSON implements custom JSON unmarshaling for flexible time parsing
func (ft *FlexTime) UnmarshalJSON(b []byte) error {
	s := string(b)
	// Remove quotes
	if len(s) >= 2 && s[0] == '"' && s[len(s)-1] == '"' {
		s = s[1 : len(s)-1]
	}

	// Try parsing with timezone first (RFC3339)
	t, err := time.Parse(time.RFC3339, s)
	if err == nil {
		ft.Time = t
		return nil
	}

	// Try parsing without timezone
	t, err = time.Parse("2006-01-02T15:04:05.999999", s)
	if err == nil {
		ft.Time = t.UTC()
		return nil
	}

	// Try parsing without microseconds
	t, err = time.Parse("2006-01-02T15:04:05", s)
	if err == nil {
		ft.Time = t.UTC()
		return nil
	}

	return err
}

// MarshalJSON implements custom JSON marshaling
func (ft FlexTime) MarshalJSON() ([]byte, error) {
	return json.Marshal(ft.Time)
}

// RecurringSchedule represents a recurring schedule
type RecurringSchedule struct {
	ID         string   `json:"id"`
	AgentID    string   `json:"agent_id"`
	Message    string   `json:"message"`
	Role       string   `json:"role"`
	CronString string   `json:"cron"`
	LastRun    *string  `json:"last_run,omitempty"`
	CreatedAt  FlexTime `json:"created_at"`
}

// RecurringScheduleCreate represents the payload to create a recurring schedule
type RecurringScheduleCreate struct {
	AgentID    string `json:"agent_id"`
	Message    string `json:"message"`
	Role       string `json:"role"`
	CronString string `json:"cron"`
	APIKey     string `json:"api_key"`
}

// OneTimeSchedule represents a one-time schedule
type OneTimeSchedule struct {
	ID        string   `json:"id"`
	AgentID   string   `json:"agent_id"`
	Message   string   `json:"message"`
	Role      string   `json:"role"`
	ExecuteAt string   `json:"execute_at"`
	CreatedAt FlexTime `json:"created_at"`
}

// OneTimeScheduleCreate represents the payload to create a one-time schedule
type OneTimeScheduleCreate struct {
	AgentID   string `json:"agent_id"`
	Message   string `json:"message"`
	Role      string `json:"role"`
	ExecuteAt string `json:"execute_at"`
	APIKey    string `json:"api_key"`
}

// ExecutionResult represents the result of a schedule execution
type ExecutionResult struct {
	ScheduleID   string `json:"schedule_id"`
	ScheduleType string `json:"schedule_type"`
	RunID        string `json:"run_id"`
	AgentID      string `json:"agent_id"`
	Message      string `json:"message"`
	ExecutedAt   string `json:"executed_at"`
}
