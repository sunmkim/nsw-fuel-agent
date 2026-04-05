# load environment variables
source .env

# configure and deploy
# agentcore configure -e agents/agent.py

# launch
agentcore launch --env NSW_API_KEY=$NSW_API_KEY --env NSW_AUTH_HEADER=$NSW_AUTH_HEADER --env OPENAI_API_KEY=$OPENAI_API_KEY --env MAPBOX_API_KEY=$MAPBOX_API_KEY --env AWS_REGION=us-east-1

# check deployment status
agentcore status

# test deployment
pixi run invoke

# to cleanup, run below command:
# agentcore destroy