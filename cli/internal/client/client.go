package client

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// Client handles communication with the Letta Schedules API
type Client struct {
	BaseURL    string
	APIKey     string
	HTTPClient *http.Client
}

// NewClient creates a new API client
func NewClient(baseURL, apiKey string) *Client {
	return &Client{
		BaseURL: baseURL,
		APIKey:  apiKey,
		HTTPClient: &http.Client{
			Timeout: 60 * time.Second, // Increased for Modal cold starts
		},
	}
}

// doRequest executes an HTTP request
func (c *Client) doRequest(method, path string, body interface{}) ([]byte, error) {
	var reqBody io.Reader
	if body != nil {
		jsonData, err := json.Marshal(body)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal request body: %w", err)
		}
		reqBody = bytes.NewBuffer(jsonData)
	}

	req, err := http.NewRequest(method, c.BaseURL+path, reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	if c.APIKey != "" {
		req.Header.Set("Authorization", "Bearer "+c.APIKey)
	}

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(respBody))
	}

	return respBody, nil
}

// Recurring Schedule methods

func (c *Client) CreateRecurringSchedule(schedule RecurringScheduleCreate) (*RecurringSchedule, error) {
	schedule.APIKey = c.APIKey
	respBody, err := c.doRequest("POST", "/schedules/recurring", schedule)
	if err != nil {
		return nil, err
	}

	var result RecurringSchedule
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &result, nil
}

func (c *Client) ListRecurringSchedules() ([]RecurringSchedule, error) {
	respBody, err := c.doRequest("GET", "/schedules/recurring", nil)
	if err != nil {
		return nil, err
	}

	var schedules []RecurringSchedule
	if err := json.Unmarshal(respBody, &schedules); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return schedules, nil
}

func (c *Client) GetRecurringSchedule(scheduleID string) (*RecurringSchedule, error) {
	respBody, err := c.doRequest("GET", "/schedules/recurring/"+scheduleID, nil)
	if err != nil {
		return nil, err
	}

	var schedule RecurringSchedule
	if err := json.Unmarshal(respBody, &schedule); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &schedule, nil
}

func (c *Client) DeleteRecurringSchedule(scheduleID string) error {
	_, err := c.doRequest("DELETE", "/schedules/recurring/"+scheduleID, nil)
	return err
}

// One-time Schedule methods

func (c *Client) CreateOneTimeSchedule(schedule OneTimeScheduleCreate) (*OneTimeSchedule, error) {
	schedule.APIKey = c.APIKey
	respBody, err := c.doRequest("POST", "/schedules/one-time", schedule)
	if err != nil {
		return nil, err
	}

	var result OneTimeSchedule
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &result, nil
}

func (c *Client) ListOneTimeSchedules() ([]OneTimeSchedule, error) {
	respBody, err := c.doRequest("GET", "/schedules/one-time", nil)
	if err != nil {
		return nil, err
	}

	var schedules []OneTimeSchedule
	if err := json.Unmarshal(respBody, &schedules); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return schedules, nil
}

func (c *Client) GetOneTimeSchedule(scheduleID string) (*OneTimeSchedule, error) {
	respBody, err := c.doRequest("GET", "/schedules/one-time/"+scheduleID, nil)
	if err != nil {
		return nil, err
	}

	var schedule OneTimeSchedule
	if err := json.Unmarshal(respBody, &schedule); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &schedule, nil
}

func (c *Client) DeleteOneTimeSchedule(scheduleID string) error {
	_, err := c.doRequest("DELETE", "/schedules/one-time/"+scheduleID, nil)
	return err
}

// Results methods

func (c *Client) ListResults() ([]ExecutionResult, error) {
	respBody, err := c.doRequest("GET", "/results", nil)
	if err != nil {
		return nil, err
	}

	var results []ExecutionResult
	if err := json.Unmarshal(respBody, &results); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return results, nil
}

func (c *Client) GetResult(scheduleID string) (*ExecutionResult, error) {
	respBody, err := c.doRequest("GET", "/results/"+scheduleID, nil)
	if err != nil {
		return nil, err
	}

	var result ExecutionResult
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &result, nil
}
