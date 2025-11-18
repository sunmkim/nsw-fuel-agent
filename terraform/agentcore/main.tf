provider "aws" {
  region = "us-east-1"
}

# Agentcore memory resource
resource "aws_bedrockagentcore_memory" "fuel_assistant_memory" {
  name                  = "fuel_assistant_memory"
  event_expiry_duration = 7
}