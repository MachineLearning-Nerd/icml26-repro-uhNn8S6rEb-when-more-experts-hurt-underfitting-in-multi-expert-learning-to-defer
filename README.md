# When More Experts Hurt: clean-room reproduction

OpenResearch workspace for **When More Experts Hurt: Underfitting in
Multi-Expert Learning to Defer** (arXiv:2602.17144, OpenReview: uhNn8S6rEb).

Every experiment uses the frozen environment and the same command:

```text
uv run --frozen python run.py
```

Research computation is run only on Hugging Face `cpu-upgrade`. The baseline
performs exact theorem checks; descendants add dataset experiments without
changing the command or dependency lock.

Current evaluator entrypoint: [current verification](pages/current-verification.md).
