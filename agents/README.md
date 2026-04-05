# Agent

## How to run locally
We handle commands with `pixi` package manager. To start up the agent run `pixi run agent`. Once you get that running on localhost, you may call it like following:
```bash
curl -X POST http://localhost:8080/invocations \
    -H 'Content-Type: application/json' \
    -d '{"prompt": "I am at 351 Windsor Rd, Baulkham Hills NSW 2153, Australia? What is the closest service station near me with Diesel fuel?"}'
```

## How to deploy

### Memory
Using Terraform, we will deploy Bedrock Agentcore memory in AWS. See `terraform/agentcore/main.tf` for more details. Run:
```bash
$ terrform plan
$ terraform apply
```

### Agent
Run: `bash agents/deploy_agent/sh`