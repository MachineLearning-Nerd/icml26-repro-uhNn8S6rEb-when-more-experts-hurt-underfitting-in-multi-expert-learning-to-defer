import hashlib
import json
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

from PIL import Image


URL = "https://zenodo.org/records/8115942/files/MiceBone.zip?download=1"
EXPECTED_MD5 = "8a4026c22f07373f022d9ab4818089ec"
EXPECTED_BYTES = 680_507_926
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}


def download(path: Path) -> tuple[str, int]:
    request = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 ICML-reproduction/1.0"})
    digest = hashlib.md5(usedforsecurity=False)
    total = 0
    with urllib.request.urlopen(request, timeout=120) as response, path.open("wb") as output:
        while chunk := response.read(8 * 1024 * 1024):
            output.write(chunk)
            digest.update(chunk)
            total += len(chunk)
    return digest.hexdigest(), total


def audit_micebone(root: Path) -> dict:
    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)
    archive = data_dir / "MiceBone.zip"
    md5, size = download(archive)
    if md5 != EXPECTED_MD5 or size != EXPECTED_BYTES:
        raise RuntimeError(f"MiceBone archive mismatch: md5={md5}, bytes={size}")

    with zipfile.ZipFile(archive) as zipped:
        corrupt_member = zipped.testzip()
        if corrupt_member is not None:
            raise RuntimeError(f"CRC failure in {corrupt_member}")
        members = [entry for entry in zipped.infolist() if not entry.is_dir()]
        suffix_counts = Counter(Path(entry.filename).suffix.lower() for entry in members)
        top_levels = Counter(Path(entry.filename).parts[0] for entry in members)
        image_names = [entry.filename for entry in members if Path(entry.filename).suffix.lower() in IMAGE_SUFFIXES]
        metadata = []
        for entry in members:
            suffix = Path(entry.filename).suffix.lower()
            if suffix in IMAGE_SUFFIXES or entry.file_size > 20_000_000:
                continue
            payload = zipped.read(entry)
            try:
                preview = payload.decode("utf-8-sig")[:10_000]
                encoding = "utf-8"
            except UnicodeDecodeError:
                preview = payload[:256].hex()
                encoding = "binary-hex"
            metadata.append(
                {
                    "name": entry.filename,
                    "bytes": entry.file_size,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "preview_encoding": encoding,
                    "preview": preview,
                }
            )

    return {
        "source_url": URL,
        "record_id": 8115942,
        "archive_bytes": size,
        "archive_md5": md5,
        "expected_archive_bytes": EXPECTED_BYTES,
        "expected_archive_md5": EXPECTED_MD5,
        "zip_crc_all_members_pass": True,
        "file_count": len(members),
        "suffix_counts": dict(sorted(suffix_counts.items())),
        "top_level_counts": dict(sorted(top_levels.items())),
        "image_count": len(image_names),
        "image_name_first_50": image_names[:50],
        "image_name_last_50": image_names[-50:],
        "metadata_files": metadata,
        "paper_contract": {
            "images": 7240,
            "classes": 3,
            "annotators": 79,
            "complete_annotators": ["047", "290", "533", "534", "580", "581", "966", "745"],
            "train_images": 5697,
            "test_images": 1543,
        },
    }


def image_label(path: str) -> str:
    return Path(path).name.split("#", 1)[0]


def image_fold(path: str) -> str:
    return next(part for part in Path(path).parts if part.startswith("fold"))


def inspect_annotations(root: Path) -> dict:
    archive = root / "data" / "MiceBone.zip"
    with zipfile.ZipFile(archive) as zipped:
        records = json.loads(zipped.read("MiceBone/annotations.json"))
        image_names = [
            entry.filename
            for entry in zipped.infolist()
            if Path(entry.filename).suffix.lower() in IMAGE_SUFFIXES
        ]
        geometry = []
        for index in [0, len(image_names) // 4, len(image_names) // 2, 3 * len(image_names) // 4, len(image_names) - 1]:
            with zipped.open(image_names[index]) as payload, Image.open(payload) as image:
                geometry.append({"name": image_names[index], "size": list(image.size), "mode": image.mode})

    fold_counts = Counter(image_fold(path) for path in image_names)
    class_counts = Counter(image_label(path) for path in image_names)
    full_annotators = []
    annotation_counts = Counter()
    for record in records:
        annotations = record.get("annotations", [])
        name = str(record.get("name", ""))
        annotation_counts[len(annotations)] += 1
        predictions = {row["image_path"]: row["class_label"] for row in annotations}
        if len(predictions) != len(image_names):
            continue
        train_paths = [path for path in image_names if image_fold(path) != "fold5"]
        test_paths = [path for path in image_names if image_fold(path) == "fold5"]
        train_correct = sum(predictions[path] == image_label(path) for path in train_paths)
        test_correct = sum(predictions[path] == image_label(path) for path in test_paths)
        full_annotators.append(
            {
                "name": name,
                "annotation_count": len(predictions),
                "train_correct": train_correct,
                "train_total": len(train_paths),
                "train_accuracy_percent": 100 * train_correct / len(train_paths),
                "test_correct": test_correct,
                "test_total": len(test_paths),
                "test_accuracy_percent": 100 * test_correct / len(test_paths),
                "class_label_counts": dict(sorted(Counter(predictions.values()).items())),
            }
        )

    return {
        "annotation_record_count": len(records),
        "annotation_count_histogram": {str(key): value for key, value in sorted(annotation_counts.items())},
        "unique_image_count": len(image_names),
        "fold_counts": dict(sorted(fold_counts.items())),
        "class_counts_from_filename": dict(sorted(class_counts.items())),
        "sample_image_geometry": geometry,
        "complete_annotator_count": len(full_annotators),
        "complete_annotators": sorted(full_annotators, key=lambda row: row["name"]),
        "privacy": "user_mail fields were neither copied nor emitted",
    }


def majority(counter: Counter) -> tuple[str, bool]:
    highest = max(counter.values())
    winners = sorted(label for label, count in counter.items() if count == highest)
    return winners[0], len(winners) > 1


def resolve_targets(root: Path) -> dict:
    archive = root / "data" / "MiceBone.zip"
    with zipfile.ZipFile(archive) as zipped:
        records = json.loads(zipped.read("MiceBone/annotations.json"))

    all_votes = {}
    full_votes = {}
    partial_votes = {}
    complete = []
    for record in records:
        annotations = record.get("annotations", [])
        is_complete = len({row["image_path"] for row in annotations}) == 7240
        if is_complete:
            complete.append(record)
        for row in annotations:
            path = row["image_path"]
            label = row["class_label"]
            all_votes.setdefault(path, Counter())[label] += 1
            target = full_votes if is_complete else partial_votes
            target.setdefault(path, Counter())[label] += 1

    paths = sorted(all_votes)
    target_sets = {
        "filename": {path: image_label(path) for path in paths},
        "all_majority": {path: majority(all_votes[path])[0] for path in paths},
        "complete_annotator_majority": {path: majority(full_votes[path])[0] for path in paths},
        "partial_annotator_majority": {path: majority(partial_votes[path])[0] for path in paths},
    }
    split_paths = {
        "train": [path for path in paths if image_fold(path) != "fold5"],
        "test": [path for path in paths if image_fold(path) == "fold5"],
    }
    paper_order = ["047", "290", "533", "534", "580", "581", "966", "745"]
    expected_train = [84.64, 85.01, 87.43, 88.13, 81.73, 85.96, 87.05, 85.45]
    expected_test = [84.64, 84.71, 86.33, 85.68, 79.59, 84.64, 87.88, 84.90]
    complete_by_id = {
        "".join(character for character in str(record["name"]) if character.isdigit()).zfill(3): record
        for record in complete
    }
    experts = []
    for index, expert_id in enumerate(paper_order):
        record = complete_by_id[expert_id]
        predictions = {row["image_path"]: row["class_label"] for row in record["annotations"]}
        metrics = {}
        for split, selected_paths in split_paths.items():
            for target_name, targets in target_sets.items():
                correct = sum(predictions[path] == targets[path] for path in selected_paths)
                metrics[f"{split}_{target_name}_accuracy_percent"] = 100 * correct / len(selected_paths)

            loo_majority_correct = 0
            loo_complete_correct = 0
            empirical_agreement = 0.0
            loo_empirical_agreement = 0.0
            for path in selected_paths:
                predicted = predictions[path]
                all_without = all_votes[path].copy()
                all_without[predicted] -= 1
                if all_without[predicted] == 0:
                    del all_without[predicted]
                full_without = full_votes[path].copy()
                full_without[predicted] -= 1
                if full_without[predicted] == 0:
                    del full_without[predicted]
                loo_majority_correct += predicted == majority(all_without)[0]
                loo_complete_correct += predicted == majority(full_without)[0]
                empirical_agreement += all_votes[path][predicted] / sum(all_votes[path].values())
                loo_empirical_agreement += all_without[predicted] / sum(all_without.values())
            metrics[f"{split}_leave_one_out_all_majority_accuracy_percent"] = 100 * loo_majority_correct / len(selected_paths)
            metrics[f"{split}_leave_one_out_complete_majority_accuracy_percent"] = 100 * loo_complete_correct / len(selected_paths)
            metrics[f"{split}_empirical_draw_expected_accuracy_percent"] = 100 * empirical_agreement / len(selected_paths)
            metrics[f"{split}_leave_one_out_empirical_draw_expected_accuracy_percent"] = 100 * loo_empirical_agreement / len(selected_paths)

        experts.append(
            {
                "expert_id": expert_id,
                "paper_train_accuracy_percent": expected_train[index],
                "paper_test_accuracy_percent": expected_test[index],
                "candidate_target_metrics": metrics,
            }
        )

    annotation_counts = Counter(sum(counter.values()) for counter in all_votes.values())
    return {
        "image_count": len(paths),
        "per_image_annotation_count_histogram": {str(key): value for key, value in sorted(annotation_counts.items())},
        "filename_vs_all_majority_agreement_percent": 100 * sum(target_sets["filename"][path] == target_sets["all_majority"][path] for path in paths) / len(paths),
        "all_majority_tie_count": sum(majority(all_votes[path])[1] for path in paths),
        "partial_majority_tie_count": sum(majority(partial_votes[path])[1] for path in paths),
        "complete_majority_tie_count": sum(majority(full_votes[path])[1] for path in paths),
        "experts": experts,
        "privacy": "user_mail fields were neither copied nor emitted",
    }
