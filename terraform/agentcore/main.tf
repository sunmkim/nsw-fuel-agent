provider "aws" {
  region = "us-east-1"
}

# Agentcore memory resource
resource "aws_bedrockagentcore_memory" "swarm_memory" {
  name                  = "swarm_memory"
  event_expiry_duration = 7
}