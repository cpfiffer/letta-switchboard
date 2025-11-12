package config

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/spf13/viper"
)

const (
	ConfigDirName  = ".letta-switchboard"
	ConfigFileName = "config"
)

// Config holds the CLI configuration
type Config struct {
	APIKey  string `mapstructure:"api_key"`
	BaseURL string `mapstructure:"base_url"`
}

// GetConfigDir returns the config directory path
func GetConfigDir() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("failed to get home directory: %w", err)
	}
	return filepath.Join(home, ConfigDirName), nil
}

// InitConfig initializes the configuration
func InitConfig() error {
	configDir, err := GetConfigDir()
	if err != nil {
		return err
	}

	// Create config directory if it doesn't exist
	if err := os.MkdirAll(configDir, 0755); err != nil {
		return fmt.Errorf("failed to create config directory: %w", err)
	}

	viper.SetConfigName(ConfigFileName)
	viper.SetConfigType("yaml")
	viper.AddConfigPath(configDir)

	// Set defaults
	viper.SetDefault("base_url", "https://letta--switchboard-api.modal.run")

	// Read config file if it exists
	if err := viper.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
			return fmt.Errorf("failed to read config: %w", err)
		}
	}

	return nil
}

// Load loads the current configuration
func Load() (*Config, error) {
	var cfg Config
	if err := viper.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("failed to unmarshal config: %w", err)
	}
	return &cfg, nil
}

// SetAPIKey sets the API key in the config
func SetAPIKey(apiKey string) error {
	viper.Set("api_key", apiKey)
	return saveConfig()
}

// SetBaseURL sets the base URL in the config
func SetBaseURL(baseURL string) error {
	viper.Set("base_url", baseURL)
	return saveConfig()
}

// saveConfig saves the current configuration to disk
func saveConfig() error {
	configDir, err := GetConfigDir()
	if err != nil {
		return err
	}

	configPath := filepath.Join(configDir, ConfigFileName+".yaml")
	if err := viper.WriteConfigAs(configPath); err != nil {
		return fmt.Errorf("failed to write config: %w", err)
	}

	return nil
}

// Validate checks if the configuration is valid
func (c *Config) Validate() error {
	if c.APIKey == "" {
		return fmt.Errorf("API key not set. Run 'letta-switchboard config set-api-key <key>'")
	}
	if c.BaseURL == "" {
		return fmt.Errorf("base URL not set. Run 'letta-switchboard config set-url <url>'")
	}
	return nil
}
