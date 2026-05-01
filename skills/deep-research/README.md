# Deep Research 
## Why
LLMs and thereby coding agents currently have a data problem. Reasoning has improved significantly but the data layer has been constrained to training data set, or sparse web data from flimsy web search and web fetch tool calls. Agents can plan research sprints, but do not have access to real-time data to make agents truly reliable, scalable and current. 

## What 
This skills, currently using Firecrawl's /agent endpoint, kicks off a deep-research loop. /agent endpoint, if hit successfully, returns a 200 along with a job id that is polled for its status currently. The skill is currently a very thin wrapper around the api endpoint, and long-term goal with this skill is to build a passable harness internally within this repo instead of relying on firecrawl. 