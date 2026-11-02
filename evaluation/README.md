# AgentTutor research evaluation

This directory contains reproducible evaluation utilities and benchmark inputs.
It does not contain pre-populated results: benchmark outcomes must come from an
actual run and must include the model, prompt, dataset, configuration, and
sample size used.

## Conditions

The supported comparison labels follow the master build prompt:

- **A** — basic LLM assistant
- **B** — Socratic prompting without structured state
- **C** — TreeInstruct baseline
- **D** — TreeInstruct with documented AgentTutor extensions
- **E** — full AgentTutor workflow

## Summarizing recorded outcomes

Create a JSON array containing one object per problem. The metric utility
accepts fields such as `bug_fix_success`, `tests_passed`,
`verifier_correct`, `question_relevant`, `repeated_turn`, `turns`,
`latency_ms`, and `token_usage`. Missing fields are omitted from the summary;
they are not treated as failures or successes.

```powershell
python evaluation/experiments/runner.py `
  --input path\to\recorded-results.json `
  --experiment treeinstruct-comparison `
  --condition E `
  --output path\to\report.json
```

The resulting report is suitable for storing in an `EvaluationRun` record.
The runner only summarizes supplied observations; it does not invoke an LLM or
claim statistical significance.