# Evaluate ClearMed against a golden set of complex -> simple medical text pairs.
#
# Setup:   pip install -r eval/requirements.txt
# Run:     python eval/evaluate.py   (backend must be running; set BACKEND_URL if remote)
#
# Metrics:
#   ROUGE-L   — n-gram overlap with the reference simplification
#   BERTScore — semantic similarity to the reference (F1)
#   Readability delta — Flesch reading-ease after minus before (higher = easier)

import argparse
import json
import os
from pathlib import Path

import requests
from rouge_score import rouge_scorer

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
GOLDEN_SET_PATH = Path(__file__).parent / "golden_set.json"
RESULTS_PATH = Path(__file__).parent / "results.json"
# BERTScore defaults to roberta-large, which is unnecessarily memory-intensive
# for this local evaluation suite. DistilBERT is much lighter while retaining a
# semantic-similarity signal suitable for comparing runs on the same benchmark.
BERTSCORE_MODEL = os.getenv("BERTSCORE_MODEL", "distilbert-base-uncased")
BERTSCORE_NUM_LAYERS = 6
# Long structured outputs can still consume substantial RAM in large batches.
# A small batch keeps the evaluation usable on typical Windows laptops.
BERTSCORE_BATCH_SIZE = int(os.getenv("BERTSCORE_BATCH_SIZE", "4"))


def call_simplify(text: str) -> dict:
    """Call the /simplify endpoint and return the parsed JSON response."""
    response = requests.post(
        f"{BACKEND_URL}/simplify",
        json={"text": text},
        timeout=90,
    )
    response.raise_for_status()
    return response.json()


def compute_rouge_l(candidate: str, reference: str) -> float:
    """Compute ROUGE-L F1 between a candidate and reference string."""
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    scores = scorer.score(reference, candidate)
    return scores["rougeL"].fmeasure


def load_completed_entries(golden_set: list[dict]) -> dict[int, dict]:
    """Return usable entries from a previous results file, keyed by id."""
    if not RESULTS_PATH.exists():
        return {}

    try:
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            previous_entries = json.load(f).get("entries", [])
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Could not read existing results; starting fresh: {exc}")
        return {}

    expected_references = {
        entry["id"]: entry["reference_simple"] for entry in golden_set
    }
    completed: dict[int, dict] = {}
    for entry in previous_entries:
        entry_id = entry.get("id")
        if (
            entry_id in expected_references
            and entry.get("reference_simple") == expected_references[entry_id]
            and entry.get("simplified_text")
        ):
            completed[entry_id] = entry
    return completed


def backend_is_available() -> bool:
    """Check the API once before retrying incomplete evaluation entries."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        response.raise_for_status()
        return response.json().get("status") == "ok"
    except (requests.RequestException, ValueError) as exc:
        print(f"Backend is unavailable at {BACKEND_URL}: {exc}")
        print("Start the backend, then rerun this command.")
        return False


def main(resume: bool = False, recompute_bert: bool = False) -> None:
    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        golden_set = json.load(f)

    completed_entries = load_completed_entries(golden_set) if resume else {}
    if completed_entries:
        print(f"Resuming from {len(completed_entries)} completed entries.\n")

    needs_backend = any(entry["id"] not in completed_entries for entry in golden_set)
    if needs_backend and not backend_is_available():
        return

    per_entry_results: list[dict] = []
    failed_entries: list[dict] = []

    print(f"Running evaluation against {BACKEND_URL} …\n")

    for entry in golden_set:
        entry_id = entry["id"]
        complex_text = entry["complex"]
        reference_simple = entry["reference_simple"]

        existing = completed_entries.get(entry_id)
        if existing:
            print(f"  [{entry_id}] Reusing completed result.")
            per_entry_results.append(existing)
            continue

        print(f"  [{entry_id}] Calling /simplify …")
        try:
            result = call_simplify(complex_text)
        except requests.RequestException as exc:
            print(f"  [{entry_id}] ERROR: {exc}")
            failed_entries.append({"id": entry_id, "error": str(exc)})
            continue

        simplified_text = result.get("simplified", "")
        fk_before = result.get("readability_before")
        fk_after = result.get("readability_after")

        rouge_l = compute_rouge_l(simplified_text, reference_simple)

        per_entry_results.append(
            {
                "id": entry_id,
                "rouge_l": rouge_l,
                "readability_before": fk_before,
                "readability_after": fk_after,
                "readability_delta": (
                    fk_after - fk_before
                    if fk_before is not None and fk_after is not None
                    else None
                ),
                "simplified_text": simplified_text,
                "reference_simple": reference_simple,
            }
        )

    if not per_entry_results:
        print("No successful responses — aborting evaluation.")
        return

    if recompute_bert:
        for entry in per_entry_results:
            entry.pop("bert_score_f1", None)

    # Score only entries that are new or whose previous BERTScore is missing.
    entries_needing_bert = [
        entry for entry in per_entry_results if entry.get("bert_score_f1") is None
    ]
    if entries_needing_bert:
        print("\nComputing BERTScore …")
        # Keep this import lazy: ROUGE/readability-only paths and --help should
        # not load Transformers or its model dependencies.
        from bert_score import score as bert_score

        candidates = [entry["simplified_text"] for entry in entries_needing_bert]
        references = [entry["reference_simple"] for entry in entries_needing_bert]
        _, _, f1 = bert_score(
            candidates,
            references,
            model_type=BERTSCORE_MODEL,
            num_layers=BERTSCORE_NUM_LAYERS,
            batch_size=BERTSCORE_BATCH_SIZE,
            lang="en",
            verbose=False,
        )
        for entry_result, bert_f1 in zip(entries_needing_bert, f1.tolist()):
            entry_result["bert_score_f1"] = bert_f1

    # Aggregate means
    mean_rouge_l = sum(e["rouge_l"] for e in per_entry_results) / len(per_entry_results)
    mean_bert_f1 = sum(e["bert_score_f1"] for e in per_entry_results) / len(per_entry_results)

    rb_vals = [e["readability_before"] for e in per_entry_results if e["readability_before"] is not None]
    ra_vals = [e["readability_after"] for e in per_entry_results if e["readability_after"] is not None]
    mean_rb = sum(rb_vals) / len(rb_vals) if rb_vals else None
    mean_ra = sum(ra_vals) / len(ra_vals) if ra_vals else None
    mean_delta = (mean_ra - mean_rb) if mean_rb is not None and mean_ra is not None else None

    # Print summary table.
    # Readability = Flesch reading-ease (higher = easier to read); delta > 0 is good.
    col_w = 11
    print("\n" + "=" * 68)
    print("EVALUATION SUMMARY  (readability = Flesch reading-ease, higher = easier)")
    print("=" * 68)
    header = (
        f"{'ID':<5}"
        f"{'ROUGE-L':>{col_w}}"
        f"{'BERT F1':>{col_w}}"
        f"{'Read Before':>{col_w+1}}"
        f"{'Read After':>{col_w}}"
        f"{'Delta':>{col_w}}"
    )
    print(header)
    print("-" * 68)
    for e in per_entry_results:
        rb = f"{e['readability_before']:.1f}" if e["readability_before"] is not None else "N/A"
        ra = f"{e['readability_after']:.1f}" if e["readability_after"] is not None else "N/A"
        dl = f"{e['readability_delta']:+.1f}" if e["readability_delta"] is not None else "N/A"
        print(
            f"{e['id']:<5}"
            f"{e['rouge_l']:>{col_w}.4f}"
            f"{e['bert_score_f1']:>{col_w}.4f}"
            f"{rb:>{col_w+1}}"
            f"{ra:>{col_w}}"
            f"{dl:>{col_w}}"
        )
    print("-" * 68)
    mean_rb_str = f"{mean_rb:.1f}" if mean_rb is not None else "N/A"
    mean_ra_str = f"{mean_ra:.1f}" if mean_ra is not None else "N/A"
    mean_dl_str = f"{mean_delta:+.1f}" if mean_delta is not None else "N/A"
    print(
        f"{'MEAN':<5}"
        f"{mean_rouge_l:>{col_w}.4f}"
        f"{mean_bert_f1:>{col_w}.4f}"
        f"{mean_rb_str:>{col_w+1}}"
        f"{mean_ra_str:>{col_w}}"
        f"{mean_dl_str:>{col_w}}"
    )
    print("=" * 68)

    # Write results JSON
    output = {
        "summary": {
            "mean_rouge_l": mean_rouge_l,
            "mean_bert_score_f1": mean_bert_f1,
            "bert_score_model": BERTSCORE_MODEL,
            "bert_score_batch_size": BERTSCORE_BATCH_SIZE,
            "mean_readability_before": mean_rb,
            "mean_readability_after": mean_ra,
            "mean_readability_delta": mean_delta,
            "num_entries": len(per_entry_results),
            "num_failed": len(failed_entries),
        },
        "entries": per_entry_results,
        "failed_entries": failed_entries,
    }
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults written to {RESULTS_PATH}")
    if failed_entries:
        print("Failed IDs: " + ", ".join(str(entry["id"]) for entry in failed_entries))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate ClearMed simplifications.")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="reuse successful entries from eval/results.json and retry the rest",
    )
    parser.add_argument(
        "--recompute-bert",
        action="store_true",
        help="recalculate BERTScore for all completed entries without rerunning /simplify",
    )
    args = parser.parse_args()
    main(resume=args.resume, recompute_bert=args.recompute_bert)
