package cmd

import (
	"fmt"
	"os"

	"github.com/fatih/color"
	"github.com/letta/letta-schedules-cli/internal/client"
	"github.com/letta/letta-schedules-cli/internal/config"
	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

var recurringCmd = &cobra.Command{
	Use:   "recurring",
	Short: "Manage recurring schedules",
	Long:  "Create, list, view, and delete recurring schedules for Letta agents",
}

var recurringCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create a new recurring schedule",
	RunE: func(cmd *cobra.Command, args []string) error {
		agentID, _ := cmd.Flags().GetString("agent-id")
		message, _ := cmd.Flags().GetString("message")
		role, _ := cmd.Flags().GetString("role")
		cronString, _ := cmd.Flags().GetString("cron")

		if agentID == "" || message == "" || cronString == "" {
			return fmt.Errorf("agent-id, message, and cron are required")
		}

		cfg, err := config.Load()
		if err != nil {
			return err
		}
		if err := cfg.Validate(); err != nil {
			return err
		}

		apiClient := client.NewClient(cfg.BaseURL, cfg.APIKey)
		schedule, err := apiClient.CreateRecurringSchedule(client.RecurringScheduleCreate{
			AgentID:    agentID,
			Message:    message,
			Role:       role,
			CronString: cronString,
		})
		if err != nil {
			return fmt.Errorf("failed to create schedule: %w", err)
		}

		color.Green("✓ Recurring schedule created successfully")
		fmt.Printf("\nSchedule ID: %s\n", schedule.ID)
		fmt.Printf("Agent ID:    %s\n", schedule.AgentID)
		fmt.Printf("Cron:        %s\n", schedule.CronString)
		fmt.Printf("Message:     %s\n", schedule.Message)

		return nil
	},
}

var recurringListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all recurring schedules",
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		if err := cfg.Validate(); err != nil {
			return err
		}

		apiClient := client.NewClient(cfg.BaseURL, cfg.APIKey)
		schedules, err := apiClient.ListRecurringSchedules()
		if err != nil {
			return fmt.Errorf("failed to list schedules: %w", err)
		}

		if len(schedules) == 0 {
			fmt.Println("No recurring schedules found")
			return nil
		}

		table := tablewriter.NewWriter(os.Stdout)
		table.SetHeader([]string{"Schedule ID", "Agent ID", "Cron", "Message", "Last Run"})
		table.SetAutoWrapText(false)
		table.SetAutoFormatHeaders(true)
		table.SetHeaderAlignment(tablewriter.ALIGN_LEFT)
		table.SetAlignment(tablewriter.ALIGN_LEFT)
		table.SetCenterSeparator("")
		table.SetColumnSeparator("")
		table.SetRowSeparator("")
		table.SetHeaderLine(false)
		table.SetBorder(false)
		table.SetTablePadding("\t")
		table.SetNoWhiteSpace(true)

		for _, s := range schedules {
			lastRun := "never"
			if s.LastRun != nil && *s.LastRun != "" {
				lastRun = *s.LastRun
			}
			table.Append([]string{
				s.ID,
				s.AgentID,
				s.CronString,
				truncate(s.Message, 50),
				lastRun,
			})
		}

		table.Render()
		return nil
	},
}

var recurringGetCmd = &cobra.Command{
	Use:   "get [schedule-id]",
	Short: "Get details of a recurring schedule",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		scheduleID := args[0]

		cfg, err := config.Load()
		if err != nil {
			return err
		}
		if err := cfg.Validate(); err != nil {
			return err
		}

		apiClient := client.NewClient(cfg.BaseURL, cfg.APIKey)
		schedule, err := apiClient.GetRecurringSchedule(scheduleID)
		if err != nil {
			return fmt.Errorf("failed to get schedule: %w", err)
		}

		fmt.Printf("Schedule ID:  %s\n", schedule.ID)
		fmt.Printf("Agent ID:     %s\n", schedule.AgentID)
		fmt.Printf("Cron:         %s\n", schedule.CronString)
		fmt.Printf("Message:      %s\n", schedule.Message)
		fmt.Printf("Role:         %s\n", schedule.Role)
		if schedule.LastRun != nil {
			fmt.Printf("Last Run:     %s\n", *schedule.LastRun)
		} else {
			fmt.Printf("Last Run:     never\n")
		}
		fmt.Printf("Created At:   %s\n", schedule.CreatedAt.Format("2006-01-02 15:04:05"))

		return nil
	},
}

var recurringDeleteCmd = &cobra.Command{
	Use:   "delete [schedule-id]",
	Short: "Delete a recurring schedule",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		scheduleID := args[0]

		cfg, err := config.Load()
		if err != nil {
			return err
		}
		if err := cfg.Validate(); err != nil {
			return err
		}

		apiClient := client.NewClient(cfg.BaseURL, cfg.APIKey)
		if err := apiClient.DeleteRecurringSchedule(scheduleID); err != nil {
			return fmt.Errorf("failed to delete schedule: %w", err)
		}

		color.Green("✓ Schedule deleted successfully")
		return nil
	},
}

func init() {
	rootCmd.AddCommand(recurringCmd)

	recurringCmd.AddCommand(recurringCreateCmd)
	recurringCreateCmd.Flags().String("agent-id", "", "Agent ID (required)")
	recurringCreateCmd.Flags().String("message", "", "Message to send (required)")
	recurringCreateCmd.Flags().String("role", "user", "Message role (default: user)")
	recurringCreateCmd.Flags().String("cron", "", "Cron expression (required)")

	recurringCmd.AddCommand(recurringListCmd)
	recurringCmd.AddCommand(recurringGetCmd)
	recurringCmd.AddCommand(recurringDeleteCmd)
}

func truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}
