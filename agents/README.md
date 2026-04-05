# Agent

## How to run locally
We handle commands with `pixi` package manager. To start up the agent run `pixi run agent`. Once you get that running on localhost, you may call it like following:
```bash
curl -X POST http://localhost:8080/invocations \
    -H 'Content-Type: application/json' \
    -d '{"prompt": "I am at 351 Windsor Rd, Baulkham Hills NSW 2153, Australia? What is the closest service station near me with Diesel fuel?"}'
```

## How to deploy
There are 2 components of the agent you must deploy: agent runtime and agent memory. For memory, we use Terraform, and for agent runtime, we will use the AgentCore CLI SDK.

### Memory
Using Terraform, we will deploy Bedrock Agentcore memory in AWS. See `terraform/agentcore/main.tf` for more details. Run:
```bash
$ terrform plan
$ terraform apply
```

### Agent
Run: `bash agents/deploy_agent.sh`.
The script above first configures the runtime with names, settings, memory to use, etc, and then launches it into AWS Bedrock. Then we confirm deployment status and test invoke with a simulated query.