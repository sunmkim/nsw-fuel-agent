provider "aws" {
  region = "us-east-1"
}

# Agentcore memory resource
resource "aws_bedrockagentcore_memory" "nsw_fuel_agent_memory" {
  name                  = "nsw_fuel_agent_memory"
  event_expiry_duration = 7
}