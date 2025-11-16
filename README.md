# Fuel Agent for New South Wales

## About
This is an agent that gives information on live fuel pricing across NSW service stations.
The agent utilizes [Fuel API](https://api.nsw.gov.au/Product/Index/22) published by NSW Department of Customer Service.


## Architecture
This is a multi-agent system that utilizes the "agent as tool" pattern, where there is a primary "orchestrator" agent that calls a more specialized agent that is domain-specific to retrieving fuel prices.

It also makes use of [Mapbox MCP server](https://docs.mapbox.com/api/guides/mcp-server/)