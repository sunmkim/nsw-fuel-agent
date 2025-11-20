# we will use agentcore starter toolkit to deploy our agent

# configure and deplpoy
uv run agentcore configure -e agent.py
uv run agentcore launch \
    --env NSW_API_KEY='api-key-here' \
    --env NSW_AUTH_HEADER='Basic auth-header-key-here' \
    --env OPENAI_API_KEY='api-key-here' \
    --env MAPBOX_API_KEY='api-key-here' \
    --env AWS_REGION='us-east-1'

# check deployment status
uv run agentcore status

# test deployment
uv run agentcore invoke '{"prompt": "Hello. What can you do?"}'

# to cleanup, run below command:
# agentcore destroy