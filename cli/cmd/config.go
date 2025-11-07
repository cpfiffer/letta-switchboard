package cmd

import (
	"fmt"

	"github.com/fatih/color"
	"github.com/letta/letta-schedules-cli/internal/config"
	"github.com/spf13/cobra"
)

var configCmd = &cobra.Command{
	Use:   "config",
	Short: "Manage CLI configuration",
	Long:  "Configure API credentials and settings for the Letta Schedules CLI",
}

var setAPIKeyCmd = &cobra.Command{
	Use:   "set-api-key [api-key]",
	Short: "Set the Letta API key",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		apiKey := args[0]
		if err := config.SetAPIKey(apiKey); err != nil {
			return fmt.Errorf("failed to set API key: %w", err)
		}
		color.Green("✓ API key set successfully")
		return nil
	},
}

var setURLCmd = &cobra.Command{
	Use:   "set-url [url]",
	Short: "Set the API base URL",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		url := args[0]
		if err := config.SetBaseURL(url); err != nil {
			return fmt.Errorf("failed to set base URL: %w", err)
		}
		color.Green("✓ Base URL set successfully")
		return nil
	},
}

var showConfigCmd = &cobra.Command{
	Use:   "show",
	Short: "Show current configuration",
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return fmt.Errorf("failed to load config: %w", err)
		}

		fmt.Println("Current configuration:")
		fmt.Printf("  Base URL: %s\n", cfg.BaseURL)
		if cfg.APIKey != "" {
			fmt.Printf("  API Key:  %s...%s\n", cfg.APIKey[:8], cfg.APIKey[len(cfg.APIKey)-4:])
		} else {
			fmt.Println("  API Key:  (not set)")
		}

		configDir, _ := config.GetConfigDir()
		fmt.Printf("\nConfig file: %s/config.yaml\n", configDir)

		return nil
	},
}

func init() {
	rootCmd.AddCommand(configCmd)
	configCmd.AddCommand(setAPIKeyCmd)
	configCmd.AddCommand(setURLCmd)
	configCmd.AddCommand(showConfigCmd)
}
