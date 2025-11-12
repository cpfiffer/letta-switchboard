package cmd

import (
	"fmt"
	"os"

	"github.com/letta/letta-switchboard-cli/internal/client"
	"github.com/letta/letta-switchboard-cli/internal/config"
	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

var resultsCmd = &cobra.Command{
	Use:   "results",
	Short: "View schedule execution results",
	Long:  "List and view execution results for scheduled messages",
}

var resultsListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all execution results",
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		if err := cfg.Validate(); err != nil {
			return err
		}

		apiClient := client.NewClient(cfg.BaseURL, cfg.APIKey)
		results, err := apiClient.ListResults()
		if err != nil {
			return fmt.Errorf("failed to list results: %w", err)
		}

		if len(results) == 0 {
			fmt.Println("No execution results found")
			return nil
		}

		table := tablewriter.NewWriter(os.Stdout)
		table.SetHeader([]string{"Schedule ID", "Type", "Agent ID", "Run ID", "Executed At"})
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

		for _, r := range results {
			table.Append([]string{
				r.ScheduleID,
				r.ScheduleType,
				r.AgentID,
				r.RunID,
				r.ExecutedAt,
			})
		}

		table.Render()
		return nil
	},
}

var resultsGetCmd = &cobra.Command{
	Use:   "get [schedule-id]",
	Short: "Get execution result for a specific schedule",
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
		result, err := apiClient.GetResult(scheduleID)
		if err != nil {
			return fmt.Errorf("failed to get result: %w", err)
		}

		fmt.Printf("Schedule ID:   %s\n", result.ScheduleID)
		fmt.Printf("Schedule Type: %s\n", result.ScheduleType)
		fmt.Printf("Agent ID:      %s\n", result.AgentID)
		fmt.Printf("Run ID:        %s\n", result.RunID)
		fmt.Printf("Message:       %s\n", result.Message)
		fmt.Printf("Executed At:   %s\n", result.ExecutedAt)

		return nil
	},
}

func init() {
	rootCmd.AddCommand(resultsCmd)
	resultsCmd.AddCommand(resultsListCmd)
	resultsCmd.AddCommand(resultsGetCmd)
}
