provider "aws" {
  region = "us-east-1"
}

# Agentcore memory resource
resource "aws_bedrockagentcore_memory" "nsw_fuel_agent_memory" {
  name                  = "nsw_fuel_agent_memory"
  event_expiry_duration = 7
}

data "aws_iam_role" "bedrock_runtime" {
  name = "AmazonBedrockAgentCoreSDKRuntime-us-east-1-9245b9760a"
}

resource "aws_iam_role_policy" "bedrock_agentcore_memory_access" {
  name = "BedrockAgentCoreMemoryAccessPolicy"
  role = data.aws_iam_role.bedrock_runtime.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock-agentcore:ListMemories",
          "bedrock-agentcore:GetMemory",
          "bedrock-agentcore:CreateMemory",
          "bedrock-agentcore:UpdateMemory",
          "bedrock-agentcore:DeleteMemory"
        ]
        Resource = "arn:aws:bedrock-agentcore:us-east-1:794944452292:memory/*"
      }
    ]
  })
}