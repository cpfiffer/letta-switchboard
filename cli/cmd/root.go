package cmd

import (
	"fmt"
	"os"

	"github.com/letta/letta-schedules-cli/internal/config"
	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "letta-schedules",
	Short: "CLI for managing Letta scheduled messages",
	Long: `A command-line interface for managing scheduled messages
for Letta AI agents. Create recurring and one-time schedules,
and view execution results.`,
}

// Execute runs the root command
func Execute() error {
	return rootCmd.Execute()
}

func init() {
	cobra.OnInitialize(initConfig)
}

func initConfig() {
	if err := config.InitConfig(); err != nil {
		fmt.Fprintf(os.Stderr, "Error initializing config: %v\n", err)
		os.Exit(1)
	}
}
