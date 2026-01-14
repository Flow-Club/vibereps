#!/usr/bin/env python3
"""
vibereps-usage - Combine ccusage output with exercise tracking data

Shows Claude Code usage alongside exercise reps in a combined daily view.
Matches ccusage table format with added exercise columns.
"""

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


def load_exercise_data():
    """Load exercise data from local JSONL file."""
    log_file = Path.home() / ".vibereps" / "exercises.jsonl"

    if not log_file.exists():
        return {}

    # Group by date and exercise type
    by_date = defaultdict(lambda: defaultdict(int))

    with open(log_file) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                ts = entry.get("timestamp", "")
                date = ts.split("T")[0] if "T" in ts else ts[:10]
                exercise = entry.get("exercise", "unknown")
                reps = entry.get("reps", 0)
                # Skip internal states and zero-rep entries
                if exercise.startswith("_") or reps <= 0:
                    continue
                by_date[date][exercise] += reps
            except (json.JSONDecodeError, KeyError):
                continue

    return dict(by_date)


def get_ccusage_data(args):
    """Run ccusage and get JSON output."""
    try:
        cmd = ["npx", "ccusage", "daily", "--json"] + args
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        pass
    return None


def format_model_name(model: str) -> str:
    """Shorten model name for display."""
    return (model
            .replace("claude-", "")
            .replace("-20251101", "")
            .replace("-20250929", "")
            .replace("-20251001", ""))


def format_exercise_short(exercise: str) -> str:
    """Shorten exercise name for display."""
    abbrevs = {
        "jumping_jacks": "JJ",
        "standing_crunches": "crunches",
        "calf_raises": "calves",
        "side_stretches": "stretches",
        "high_knees": "knees",
        "torso_twists": "twists",
        "arm_circles": "arms",
        "shoulder_shrugs": "shrugs",
        "chin_tucks": "chins",
    }
    return abbrevs.get(exercise, exercise)


def format_exercises(exercises: dict) -> str:
    """Format exercise data for display."""
    if not exercises:
        return ""
    parts = []
    for exercise, reps in sorted(exercises.items(), key=lambda x: -x[1]):
        short = format_exercise_short(exercise)
        parts.append(f"{reps} {short}")
    return ", ".join(parts)


def print_table(ccusage_data, exercise_data):
    """Print combined table matching ccusage format with exercise columns."""

    # Column widths
    DATE_W = 10
    MODEL_W = 33
    INPUT_W = 9
    OUTPUT_W = 9
    CACHE_C_W = 13
    CACHE_R_W = 12
    TOTAL_W = 13
    COST_W = 11
    EXERCISE_W = 25

    # Box drawing characters
    TL, TR, BL, BR = "┌", "┐", "└", "┘"
    H, V = "─", "│"
    LT, RT, TT, BT, X = "├", "┤", "┬", "┴", "┼"

    def hline(left, mid, right):
        return (left + H * (DATE_W + 2) + mid + H * (MODEL_W + 2) + mid +
                H * (INPUT_W + 2) + mid + H * (OUTPUT_W + 2) + mid +
                H * (CACHE_C_W + 2) + mid + H * (CACHE_R_W + 2) + mid +
                H * (TOTAL_W + 2) + mid + H * (COST_W + 2) + mid +
                H * (EXERCISE_W + 2) + right)

    def row(date, model, inp, out, cache_c, cache_r, total, cost, exercises):
        return (f"{V} {date:<{DATE_W}} {V} {model:<{MODEL_W}} {V} "
                f"{inp:>{INPUT_W}} {V} {out:>{OUTPUT_W}} {V} "
                f"{cache_c:>{CACHE_C_W}} {V} {cache_r:>{CACHE_R_W}} {V} "
                f"{total:>{TOTAL_W}} {V} {cost:>{COST_W}} {V} "
                f"{exercises:<{EXERCISE_W}} {V}")

    # Header
    print(hline(TL, TT, TR))
    print(row("Date", "Models", "Input", "Output", "Cache Create", "Cache Read",
              "Total", "Cost", "Exercises"))
    print(hline(LT, X, RT))

    # Collect all dates
    all_dates = set()
    ccusage_by_date = {}

    if ccusage_data and "daily" in ccusage_data:
        for day in ccusage_data["daily"]:
            date = day.get("date", "")
            all_dates.add(date)
            ccusage_by_date[date] = day

    all_dates.update(exercise_data.keys())

    # Totals
    total_input = 0
    total_output = 0
    total_cache_c = 0
    total_cache_r = 0
    total_tokens = 0
    total_cost = 0.0
    total_exercises = defaultdict(int)

    sorted_dates = sorted(all_dates)

    for i, date in enumerate(sorted_dates):
        day = ccusage_by_date.get(date, {})
        exercises = exercise_data.get(date, {})

        # Accumulate totals
        input_tokens = day.get("inputTokens", 0)
        output_tokens = day.get("outputTokens", 0)
        cache_create = day.get("cacheCreationTokens", 0)
        cache_read = day.get("cacheReadTokens", 0)
        tokens = day.get("totalTokens", 0)
        cost = day.get("totalCost", 0)

        total_input += input_tokens
        total_output += output_tokens
        total_cache_c += cache_create
        total_cache_r += cache_read
        total_tokens += tokens
        total_cost += cost

        for ex, reps in exercises.items():
            total_exercises[ex] += reps

        # Get models
        models = [format_model_name(m) for m in day.get("modelsUsed", [])]
        exercise_str = format_exercises(exercises)

        # First row with data
        first_model = f"- {models[0]}" if models else "-"
        print(row(
            date,
            first_model,
            f"{input_tokens:,}" if input_tokens else "",
            f"{output_tokens:,}" if output_tokens else "",
            f"{cache_create:,}" if cache_create else "",
            f"{cache_read:,}" if cache_read else "",
            f"{tokens:,}" if tokens else "",
            f"${cost:,.2f}" if cost else "",
            exercise_str
        ))

        # Additional model rows
        for model in models[1:]:
            print(row("", f"- {model}", "", "", "", "", "", "", ""))

        # Separator between days (except last)
        if i < len(sorted_dates) - 1:
            print(hline(LT, X, RT))

    # Total row
    print(hline(LT, X, RT))
    total_exercise_str = format_exercises(dict(total_exercises))
    print(row(
        "Total",
        "",
        f"{total_input:,}",
        f"{total_output:,}",
        f"{total_cache_c:,}",
        f"{total_cache_r:,}",
        f"{total_tokens:,}",
        f"${total_cost:,.2f}",
        total_exercise_str
    ))
    print(hline(BL, BT, BR))


def main():
    # Pass through args to ccusage (like --since, --until)
    args = sys.argv[1:]

    # Check for --exercises-only flag
    exercises_only = "--exercises-only" in args
    if exercises_only:
        args.remove("--exercises-only")

    exercise_data = load_exercise_data()

    if exercises_only:
        ccusage_data = None
    else:
        ccusage_data = get_ccusage_data(args)

    if not ccusage_data and not exercise_data:
        print("No data found. Complete some exercises or run ccusage first.")
        return 1

    print_table(ccusage_data, exercise_data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
