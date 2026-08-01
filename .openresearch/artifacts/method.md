# Claim 6 preregistered method

The accepted MiceBone reproduction uses the official 7,240-image archive,
folds 1–4 for training (5,697 images), fold 5 for testing (1,543 images), and
experts `047, 290, 533, 534, 580, 581, 966, 745` in the paper's order.
Targets are the majority of the eight complete annotators with ties resolved
by the dataset class order `g > ug > nr`; this reconstructs Table 3 before any
model result is observed.

Each CE, PiCCE-CE, OvA, and PiCCE-OvA model is a randomly initialized
torchvision ResNet-18 trained for 100 epochs with AdamW (`lr=3e-4`, weight
decay `5e-4`) and batch size 128. Training uses deterministic seeds
`260217144, 260217145, 260217146`, standard ImageNet normalization,
random-resized-crop and horizontal-flip augmentation, and no GPU. Every
method/seed/expert-count combination runs as its own HF `cpu-upgrade` shard
because the effective allocation is eight CPU cores.

The primary endpoint is final-epoch test classifier accuracy. For each method
and expert count, the three seeds are averaged. Vanilla degradation requires
strict decreases at every adjacent count and at least a two-point drop from
2 to 8 experts. PiCCE stability requires a range of at most two points across
the four counts. At eight experts, each PiCCE mean must exceed its vanilla
counterpart. Paired differences and 95% t intervals are reported but are not
used to retune this frozen rule.

The paper does not specify target construction, tie handling, augmentation,
normalization, initialization, or seeds. These clean-room choices and the two
residual Table 3 discrepancies are retained as limitations. This MiceBone
panel does not by itself establish the caption's statement across every other
dataset.
