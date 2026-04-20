# Experiments Guide (Part 1 + Part 2)

This folder provides reproducible scripts for the assignment workflow:
1. Part 1 heuristic benchmark.
2. Part 2 lightweight LLM evaluation.

## Agents Implemented

- Heuristic agent:
  - `PyCatan.Agents.AlexPelochoJaimeHeuristicAgent.AlexPelochoJaimeHeuristicAgent`
- LLM-assisted agent:
  - `PyCatan.Agents.AlexPelochoJaimeLLMAgent.AlexPelochoJaimeLLMAgent`

## Script 1: Part 1 benchmark

Run from repository root:

```bash
python3 experiments/benchmark_part1.py \
  --agent-class PyCatan.Agents.AlexPelochoJaimeHeuristicAgent.AlexPelochoJaimeHeuristicAgent \
  --mode both \
  --games-per-position 40 \
  --max-standard-permutations 80 \
  --workers 8 \
  --allow-dirty
```

Output artifacts are written to `experiments/results/`:
- `*_matches.csv`
- `*_summary.csv`
- `*_metadata.json`

Reproducibility fields include git commit, command, python version, and timestamps.

## Script 2: Part 2 lightweight LLM evaluation

Run from repository root:

```bash
python3 experiments/evaluate_llm_light.py \
  --agent-class Shiyi_Catan.AlexPelochoJaimeLLMAgent.AlexPelochoJaimeLLMAgent \
  --model-config ollama=llama3.1:8b \
  --model-config bedrock=anthropic.claude-3-haiku-20240307-v1:0 \
  --model-config upv=gpt-4o-mini \
  --prompt-variants compact_json,resource_focus,safe_legal \
  --games-per-config 8
```

Output artifacts are written to `experiments/results/`:
- `*_summary.csv`
- `*_metadata.json`

You can point to any compatible LLM agent class with `--agent-class`.
Example default value:
- `PyCatan.Agents.AlexPelochoJaimeLLMAgent.AlexPelochoJaimeLLMAgent`

## Environment Variables for LLM providers

### Ollama

Optional:
- `CATAN_OLLAMA_BASE_URL` (default `http://127.0.0.1:11434`)

### AWS Bedrock

Optional:
- `CATAN_BEDROCK_REGION` (default `eu-west-1`)

Standard AWS auth environment is expected (`AWS_ACCESS_KEY_ID`, etc).

### UPV API

Required:
- `CATAN_UPV_CHAT_ENDPOINT`
- `CATAN_UPV_API_KEY`

## Prompt Variants

Implemented variants:
- `compact_json`
- `resource_focus`
- `safe_legal`

Each variant uses strict JSON output with `action_index` over legal actions.

## Notes

- The LLM agent includes safe fallback to heuristics when provider calls fail or return invalid JSON.
- For final report comparisons, keep the same game budget across prompt/model settings.
- If you need strict clean-run enforcement, omit `--allow-dirty` in `benchmark_part1.py`.
