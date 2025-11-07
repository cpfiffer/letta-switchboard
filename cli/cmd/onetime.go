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

var onetimeCmd = &cobra.Command{
	Use:   "onetime",
	Short: "Manage one-time schedules",
	Long:  "Create, list, view, and delete one-time schedules for Letta agents",
}

var onetimeCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create a new one-time schedule",
	RunE: func(cmd *cobra.Command, args []string) error {
		agentID, _ := cmd.Flags().GetString("agent-id")
		message, _ := cmd.Flags().GetString("message")
		role, _ := cmd.Flags().GetString("role")
		executeAt, _ := cmd.Flags().GetString("execute-at")

		if agentID == "" || message == "" || executeAt == "" {
			return fmt.Errorf("agent-id, message, and execute-at are required")
		}

		cfg, err := config.Load()
		if err != nil {
			return err
		}
		if err := cfg.Validate(); err != nil {
			return err
		}

		apiClient := client.NewClient(cfg.BaseURL, cfg.APIKey)
		schedule, err := apiClient.CreateOneTimeSchedule(client.OneTimeScheduleCreate{
			AgentID:   agentID,
			Message:   message,
			Role:      role,
			ExecuteAt: executeAt,
		})
		if err != nil {
			return fmt.Errorf("failed to create schedule: %w", err)
		}

		color.Green("✓ One-time schedule created successfully")
		fmt.Printf("\nSchedule ID:  %s\n", schedule.ID)
		fmt.Printf("Agent ID:     %s\n", schedule.AgentID)
		fmt.Printf("Execute At:   %s\n", schedule.ExecuteAt)
		fmt.Printf("Message:      %s\n", schedule.Message)

		return nil
	},
}

var onetimeListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all one-time schedules",
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		if err := cfg.Validate(); err != nil {
			return err
		}

		apiClient := client.NewClient(cfg.BaseURL, cfg.APIKey)
		schedules, err := apiClient.ListOneTimeSchedules()
		if err != nil {
			return fmt.Errorf("failed to list schedules: %w", err)
		}

		if len(schedules) == 0 {
			fmt.Println("No one-time schedules found")
			return nil
		}

		table := tablewriter.NewWriter(os.Stdout)
		table.SetHeader([]string{"Schedule ID", "Agent ID", "Execute At", "Message"})
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
			table.Append([]string{
				s.ID,
				s.AgentID,
				s.ExecuteAt,
				truncate(s.Message, 50),
			})
		}

		table.Render()
		return nil
	},
}

var onetimeGetCmd = &cobra.Command{
	Use:   "get [schedule-id]",
	Short: "Get details of a one-time schedule",
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
		schedule, err := apiClient.GetOneTimeSchedule(scheduleID)
		if err != nil {
			return fmt.Errorf("failed to get schedule: %w", err)
		}

		fmt.Printf("Schedule ID:  %s\n", schedule.ID)
		fmt.Printf("Agent ID:     %s\n", schedule.AgentID)
		fmt.Printf("Execute At:   %s\n", schedule.ExecuteAt)
		fmt.Printf("Message:      %s\n", schedule.Message)
		fmt.Printf("Role:         %s\n", schedule.Role)
		fmt.Printf("Created At:   %s\n", schedule.CreatedAt.Format("2006-01-02 15:04:05"))

		return nil
	},
}

var onetimeDeleteCmd = &cobra.Command{
	Use:   "delete [schedule-id]",
	Short: "Delete a one-time schedule",
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
		if err := apiClient.DeleteOneTimeSchedule(scheduleID); err != nil {
			return fmt.Errorf("failed to delete schedule: %w", err)
		}

		color.Green("✓ Schedule deleted successfully")
		return nil
	},
}

func init() {
	rootCmd.AddCommand(onetimeCmd)

	onetimeCmd.AddCommand(onetimeCreateCmd)
	onetimeCreateCmd.Flags().String("agent-id", "", "Agent ID (required)")
	onetimeCreateCmd.Flags().String("message", "", "Message to send (required)")
	onetimeCreateCmd.Flags().String("role", "user", "Message role (default: user)")
	onetimeCreateCmd.Flags().String("execute-at", "", "ISO 8601 timestamp (e.g., 2025-11-07T10:00:00Z) (required)")

	onetimeCmd.AddCommand(onetimeListCmd)
	onetimeCmd.AddCommand(onetimeGetCmd)
	onetimeCmd.AddCommand(onetimeDeleteCmd)
}
