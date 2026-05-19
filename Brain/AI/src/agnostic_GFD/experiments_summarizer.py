import argparse
from pathlib import Path
import csv, math, statistics

def summarize_results_all_levels_raw(path_to_validation_folder: str, catastrophic_thresh: float = 0.10):
    """
    Compute all summaries (Y-level, X-level, and global) directly from raw per-file CSV data.
    Includes both grid and global metrics for Accuracy, Recall, F1, and CAF_rate.
    """

    root = Path(path_to_validation_folder)

    BASE_METRICS = [
        "grid_TP", "grid_FP", "grid_FN",
        "global_TP", "global_FP", "global_FN"
    ]

    DERIVED_METRICS = [
        "grid_Precision", "grid_Recall", "grid_F1",
        "global_Precision", "global_Recall", "global_F1",
        "CAF_rate"
    ]

    TOTAL_KEY = "TOTAL_OBJ"
    METRICS_ORDER = BASE_METRICS + DERIVED_METRICS + [TOTAL_KEY]

    def fmt(x):
        if isinstance(x, (int, float)):
            return round(x, 3)
        try:
            return round(float(x), 3)
        except Exception:
            return x

    def mean(x): return statistics.mean(x) if x else 0.0
    def std(x): return statistics.pstdev(x) if len(x) >= 2 else 0.0
    def median(x): return statistics.median(sorted(x)) if x else 0.0
    def trimmed_mean(x, p=0.1):
        if len(x) < 2:
            return mean(x)
        x = sorted(x)
        k = int(p * len(x))
        return mean(x[k:len(x) - k]) if len(x) > 2 * k else mean(x)

    def compute_summary(rows):
        """Compute summary stats for all metrics from a list of dict rows."""
        values = {m: {"abs": [], "pct": []} for m in METRICS_ORDER}

        for row in rows:
            try:
                grid_tp = float(row["grid_TP"])
                grid_fp = float(row["grid_FP"])
                grid_fn = float(row["grid_FN"])
                global_tp = float(row["global_TP"])
                global_fp = float(row["global_FP"])
                global_fn = float(row["global_FN"])
                total = float(row["TOTAL_OBJ"])
            except Exception:
                continue

            # Derived GRID metrics
            grid_prec = grid_tp / (grid_tp + grid_fp) if (grid_tp + grid_fp) > 0 else 0.0
            grid_rec = grid_tp / (grid_tp + grid_fn) if (grid_tp + grid_fn) > 0 else 0.0
            grid_f1 = 2 * grid_tp / (2 * grid_tp + grid_fp + grid_fn) if (2 * grid_tp + grid_fp + grid_fn) > 0 else 0.0

            # Derived GLOBAL metrics
            global_prec = global_tp / (global_tp + global_fp) if (global_tp + global_fp) > 0 else 0.0
            global_rec = global_tp / (global_tp + global_fn) if (global_tp + global_fn) > 0 else 0.0
            global_f1 = 2 * global_tp / (2 * global_tp + global_fp + global_fn) if (2 * global_tp + global_fp + global_fn) > 0 else 0.0

            # CAF flag
            caf = 1.0 if global_f1 < catastrophic_thresh else 0.0

            # Record everything
            metrics = {
                "grid_TP": grid_tp, "grid_FP": grid_fp, "grid_FN": grid_fn,
                "global_TP": global_tp, "global_FP": global_fp, "global_FN": global_fn,
                "grid_Precision": grid_prec, "grid_Recall": grid_rec, "grid_F1": grid_f1,
                "global_Precision": global_prec, "global_Recall": global_rec, "global_F1": global_f1,
                "CAF_rate": caf, "TOTAL_OBJ": total
            }

            for key, val in metrics.items():
                values[key]["abs"].append(val)

                if key == "TOTAL_OBJ":
                    continue  # no percent for totals

                if key in DERIVED_METRICS:
                    values[key]["pct"].append(100.0 * val)  # ← multiply only
                else:
                    if total > 0:
                        values[key]["pct"].append(100.0 * val / total)  # counts normalized by GT

        # Compute all stats
        summary = []
        for key in METRICS_ORDER:
            abs_vals = values[key]["abs"]
            pct_vals = values[key]["pct"]
            summary.append({
                "metric": key,
                "total": sum(abs_vals) ,
                "mean_abs": fmt(mean(abs_vals)),
                "std_abs": fmt(std(abs_vals)),
                "median_abs": fmt(median(abs_vals)),
                "trimmed_mean_abs": fmt(trimmed_mean(abs_vals)),
                "mean_pct": fmt(mean(pct_vals)),
                "std_pct": fmt(std(pct_vals)),
                "median_pct": fmt(median(pct_vals)),
                "trimmed_mean_pct": fmt(trimmed_mean(pct_vals)),
                "n_samples": len(abs_vals)
            })
        return summary

    def write_summary(path, summary):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
            writer.writeheader()
            writer.writerows(summary)
        print(f"[OK] Wrote {path}")

    # --- Collect raw rows for all levels ---
    global_rows = []
    for x_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        x_rows = []
        for y_dir in sorted(p for p in x_dir.iterdir() if p.is_dir()):
            y_rows = []
            for csv_file in y_dir.glob("*.csv"):
                if csv_file.name.startswith("summary"):
                    continue
                with open(csv_file, newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        y_rows.append(r)
                        x_rows.append(r)
                        global_rows.append(r)
            if y_rows:
                write_summary(y_dir / "summary.csv", compute_summary(y_rows))
        if x_rows:
            write_summary(x_dir / "summary_overall.csv", compute_summary(x_rows))
    if global_rows:
        write_summary(root / "overall_global.csv", compute_summary(global_rows))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grid construction and candy clustering")
    parser.add_argument("-s", "--summarize", type=str, required=True, help="Path to validate experiments folder.")

    args = parser.parse_args()
    summarize_results_all_levels_raw(args.summarize)