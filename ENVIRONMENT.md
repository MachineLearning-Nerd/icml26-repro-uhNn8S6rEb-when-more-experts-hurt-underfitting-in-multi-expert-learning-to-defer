# Environment and reproduction boundary

## Exact theory/proof contract

- Command recorded by the release branch: <code>uv run --frozen python run.py</code>
- Runtime: Python 3.12 with <code>uv.lock</code>
- Theory/proof compute: CPU-compatible exact checks
- Canonical source branch: <code>release/universal-theory-certificates</code>
- Primary result: <code>.openresearch/artifacts/verifier_output.json</code>
- Independent result: <code>.openresearch/artifacts/independent_checker_output.json</code>

The exact checker reports:

    PASS: Claims 1-3 verified; Claims 4-5 falsified; assumptions, source cells, and exact fractions checked

The independent checker reports:

    PASS: independent implementations reconstructed Claims 1-5, including both exact counterexamples

The proof scripts <code>proof_certificates.py</code>,
<code>independent_proof_check.py</code>, and
<code>verify_proof_certificates.py</code> are preserved on the same release
branch.

## MiceBone calibration contract

The recorded full-data calibration used the Hugging Face <code>cpu-upgrade</code>
flavor, the container
<code>ghcr.io/astral-sh/uv:python3.12-bookworm-slim</code>, and no CUDA
device. The environment artifact reports 64 visible CPUs with an effective
quota of 8 and a calibration-stage runtime of about 805.10 seconds.

The accepted-as-calibration-only training cell was:

- J=2, CE, seed 260217144;
- one epoch, not the paper's 100 epochs;
- ResNet-18 with random initialization;
- AdamW, learning rate 0.0003, weight decay 0.0005;
- batch size 128 and channels-last CPU format;
- 5,697 training images and 1,543 test images;
- one-epoch training runtime 489.0306 seconds.

Its recorded metrics were 61.3091% classifier accuracy, 18.4705% system
error, and 30.2657% coverage. The artifact explicitly sets
<code>accepted_scientific_result</code> to false.

## Why Claim 6 is not reported as reproduced

The declared campaign contains 48 cells: four expert counts, four methods,
and three seeds. The campaign record states that the initial jobs were
canceled for resource/time reasons, no accepted artifact bundles completed,
and publication was not performed. The projected serial cost for the
source-faithful 100-epoch 4J, three-seed campaign was approximately 163.01
hours.

The target reconstruction and the runtime calibration are useful audit
evidence. They do not supply the complete aggregate needed by the Claim 6
verdict rule, so no empirical pass or fail is inferred.
