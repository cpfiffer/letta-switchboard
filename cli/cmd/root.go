package cmd

import (
	"fmt"
	"os"

	"github.com/letta/letta-switchboard-cli/internal/config"
	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "letta-switchboard",
	Short: "CLI for routing messages to Letta agents",
	Long: `Letta Switchboard - Route messages to Letta AI agents
Send messages immediately or schedule for later. Create recurring
schedules and view execution results.`,
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
