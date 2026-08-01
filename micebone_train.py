import json
import os
import random
import time
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

from micebone import image_fold, majority_with_priority


LABELS = ["g", "ug", "nr"]
EXPERT_IDS = ["047", "290", "533", "534", "580", "581", "966", "745"]
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)
TARGET_PRIORITY = ("g", "ug", "nr")


def effective_cpu_count() -> int:
    counts = [os.cpu_count() or 1]
    if hasattr(os, "sched_getaffinity"):
        counts.append(len(os.sched_getaffinity(0)))
    cpu_max = Path("/sys/fs/cgroup/cpu.max")
    if cpu_max.exists():
        quota, period = cpu_max.read_text().split()
        if quota != "max":
            counts.append(max(1, int(quota) // int(period)))
    return min(counts)


class MiceBoneDataset(Dataset):
    def __init__(self, data_root: Path, paths: list[str], targets: dict[str, int], experts: dict[str, list[int]], transform) -> None:
        self.data_root = data_root
        self.paths = paths
        self.targets = targets
        self.experts = experts
        self.transform = transform

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, index: int):
        path = self.paths[index]
        with Image.open(self.data_root / path) as image:
            pixels = self.transform(image.convert("RGB"))
        return pixels, self.targets[path], torch.tensor(self.experts[path], dtype=torch.long)


def prepare_data(root: Path):
    data_root = root / "data"
    archive = data_root / "MiceBone.zip"
    with zipfile.ZipFile(archive) as zipped:
        zipped.extractall(data_root)
        records = json.loads(zipped.read("MiceBone/annotations.json"))

    complete_votes = {}
    complete = {}
    for record in records:
        annotations = record["annotations"]
        if len({row["image_path"] for row in annotations}) == 7240:
            expert_id = "".join(character for character in str(record["name"]) if character.isdigit()).zfill(3)
            complete[expert_id] = {row["image_path"]: row["class_label"] for row in annotations}
            for row in annotations:
                complete_votes.setdefault(row["image_path"], Counter())[row["class_label"]] += 1

    if sorted(complete) != sorted(EXPERT_IDS):
        raise RuntimeError(f"complete expert IDs changed: {sorted(complete)}")
    label_to_index = {label: index for index, label in enumerate(LABELS)}
    paths = sorted(complete_votes)
    targets = {
        path: label_to_index[majority_with_priority(complete_votes[path], TARGET_PRIORITY)]
        for path in paths
    }
    experts = {
        path: [label_to_index[complete[expert_id][path]] for expert_id in EXPERT_IDS]
        for path in paths
    }
    train_paths = [path for path in paths if image_fold(path) != "fold5"]
    test_paths = [path for path in paths if image_fold(path) == "fold5"]
    if len(train_paths) != 5697 or len(test_paths) != 1543:
        raise RuntimeError("paper fold sizes were not recovered")
    return data_root, train_paths, test_paths, targets, experts


def l2d_loss(logits: torch.Tensor, targets: torch.Tensor, experts: torch.Tensor, method: str) -> torch.Tensor:
    classes = len(LABELS)
    correct = experts.eq(targets[:, None])
    expert_logits = logits[:, classes:]
    if method in {"ce", "picce_ce"}:
        log_probabilities = F.log_softmax(logits, dim=1)
        base = -log_probabilities.gather(1, targets[:, None]).squeeze(1)
        if method == "ce":
            extra = -(log_probabilities[:, classes:] * correct).sum(dim=1)
        else:
            selected = expert_logits.masked_fill(~correct, -torch.inf).argmax(dim=1)
            selected_loss = -log_probabilities.gather(1, (selected + classes)[:, None]).squeeze(1)
            extra = torch.where(correct.any(dim=1), selected_loss, torch.zeros_like(selected_loss))
    else:
        target_logits = logits.gather(1, targets[:, None]).squeeze(1)
        base = F.softplus(-target_logits) + F.softplus(logits).sum(dim=1) - F.softplus(target_logits)
        if method == "ova":
            extra = -(expert_logits * correct).sum(dim=1)
        else:
            selected = expert_logits.masked_fill(~correct, -torch.inf).argmax(dim=1)
            selected_loss = -expert_logits.gather(1, selected[:, None]).squeeze(1)
            extra = torch.where(correct.any(dim=1), selected_loss, torch.zeros_like(selected_loss))
    return (base + extra).mean()


def evaluate(model, loader, experts_count: int) -> dict:
    classifier_correct = 0
    system_correct = 0
    covered = 0
    samples = 0
    model.eval()
    with torch.no_grad():
        for pixels, targets, experts in loader:
            logits = model(pixels)
            classifier = logits[:, : len(LABELS)].argmax(dim=1)
            decision = logits.argmax(dim=1)
            defer = decision >= len(LABELS)
            expert_index = (decision - len(LABELS)).clamp(min=0)
            system = classifier.clone()
            system[defer] = experts[:, :experts_count].gather(1, expert_index[:, None])[defer, 0]
            classifier_correct += classifier.eq(targets).sum().item()
            system_correct += system.eq(targets).sum().item()
            covered += (~defer).sum().item()
            samples += targets.numel()
    return {
        "samples": samples,
        "classifier_accuracy_percent": 100 * classifier_correct / samples,
        "system_error_percent": 100 * (samples - system_correct) / samples,
        "coverage_percent": 100 * covered / samples,
    }


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)


def train_one(data, method: str, experts_count: int, seed: int, epochs: int) -> dict:
    seed_everything(seed)
    data_root, train_paths, test_paths, targets, experts = data
    train_transform = transforms.Compose(
        [
            transforms.RandomHorizontalFlip(),
            transforms.RandomResizedCrop(224, antialias=True),
            transforms.ToTensor(),
            transforms.Normalize(MEAN, STD),
        ]
    )
    test_transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize(MEAN, STD)])
    train = MiceBoneDataset(data_root, train_paths, targets, experts, train_transform)
    test = MiceBoneDataset(data_root, test_paths, targets, experts, test_transform)
    generator = torch.Generator().manual_seed(seed)
    workers = min(4, max(1, effective_cpu_count() // 2))
    train_loader = DataLoader(train, batch_size=128, shuffle=True, num_workers=workers, persistent_workers=True, generator=generator)
    test_loader = DataLoader(test, batch_size=128, shuffle=False, num_workers=workers, persistent_workers=True)
    model = models.resnet18(weights=None, num_classes=len(LABELS) + experts_count)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=5e-4)
    history = []
    started = time.monotonic()
    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        samples = 0
        for pixels, targets_batch, experts_batch in train_loader:
            optimizer.zero_grad(set_to_none=True)
            logits = model(pixels)
            loss = l2d_loss(logits, targets_batch, experts_batch[:, :experts_count], method)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * targets_batch.numel()
            samples += targets_batch.numel()
        epoch_result = {"epoch": epoch + 1, "train_loss": total_loss / samples, **evaluate(model, test_loader, experts_count)}
        history.append(epoch_result)
        print(json.dumps({"method": method, "experts": experts_count, "seed": seed, **epoch_result}), flush=True)
    return {
        "method": method,
        "experts": experts_count,
        "seed": seed,
        "epochs": epochs,
        "runtime_seconds": time.monotonic() - started,
        "history": history,
    }


def calibrate_micebone(root: Path, config: dict) -> dict:
    torch.set_num_threads(effective_cpu_count())
    data = prepare_data(root)
    training = config["micebone_training"]
    runs = [
        train_one(data, method, experts_count, seed, training["epochs"])
        for experts_count in training["expert_counts"]
        for seed in training["seeds"]
        for method in training["methods"]
    ]
    observed_epoch_seconds = sum(run["runtime_seconds"] / run["epochs"] for run in runs)
    return {
        "accepted_scientific_result": False,
        "purpose": "full-data one-epoch wall-time calibration only",
        "target": training["target"],
        "paper_faithful": {
            "model": "torchvision ResNet-18, random initialization",
            "optimizer": "AdamW",
            "learning_rate": 0.0003,
            "weight_decay": 0.0005,
            "batch_size": 128,
            "train_images": 5697,
            "test_images": 1543,
        },
        "declared_deviations": [
            "The paper does not define clean targets, tie handling, augmentation, normalization, or pretrained initialization.",
            "Complete-annotator majority with g>ug>nr priority recovers 14/16 Table 3 values after rounding and is the fixed target reconstruction.",
            "Standard ImageNet normalization/augmentation and random initialization are fixed clean-room choices.",
            "One epoch is not scientific evidence for Claims 5 or 6.",
        ],
        "runs": runs,
        "projected_100_epoch_4J_3seed_serial_hours": observed_epoch_seconds * 100 * 4 * 3 / 3600,
    }
