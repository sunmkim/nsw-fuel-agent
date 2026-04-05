# Evaluations

## Strands Evals
Agent evaluations were created using the [Strands Evals SDK](https://github.com/strands-agents/evals)


## Agent Evaluations

There are 5 experiments we ran on the NSW fuel agent to help evaluate it:
1. Clarification
2. Location
3. Fuel infomation
4. Station look-up
5. Directions

## Structure
```
├── evals
│   ├── README.md
│   ├── cases.py        <-- Example cases to test out our experiments
│   ├── experiments.py  <-- Experiments to run our cases
│   └── eval.py         <-- Script to execute our evals
```

Below is an example screenshot of location evaluation:
![evals](/images/evals.png)