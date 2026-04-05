# we will use agentcore starter toolkit to deploy our agent

# configure and deploy
pixi run configure
pixi run launch

# check deployment status
pixi run status

# test deployment
pixi run invoke

# to cleanup, run below command:
# agentcore destroy