#!/usr/bin/env python3
"""
vibereps-usage - Combine ccusage output with exercise tracking data

Shows Claude Code usage alongside exercise reps in a combined daily view.
"""

import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
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


def format_exercises(exercises):
    """Format exercise data for display."""
    if not exercises:
        return ""

    parts = []
    for exercise, reps in sorted(exercises.items()):
        # Shorten exercise names
        short = exercise.replace("_", " ").replace("jumping jacks", "JJ")
        parts.append(f"{reps} {short}")

    return ", ".join(parts)


def print_combined_table(ccusage_data, exercise_data):
    """Print combined table with ccusage data and exercises."""

    # Header
    print("=" * 130)
    print(f"{'Date':<12} {'Models':<30} {'Input':>12} {'Output':>12} {'Total':>14} {'Cost':>10} {'Exercises':<30}")
    print("=" * 130)

    total_reps = defaultdict(int)
    total_input = 0
    total_output = 0
    total_tokens = 0
    total_cost = 0.0

    # Get all dates from both sources
    all_dates = set()
    if ccusage_data and "daily" in ccusage_data:
        all_dates.update(row.get("date", "") for row in ccusage_data["daily"])
    all_dates.update(exercise_data.keys())

    # Create lookup for ccusage data
    ccusage_by_date = {}
    if ccusage_data and "daily" in ccusage_data:
        for row in ccusage_data["daily"]:
            ccusage_by_date[row.get("date", "")] = row

    for date in sorted(all_dates):
        row = ccusage_by_date.get(date, {})
        models = row.get("modelsUsed", [])
        model_str = ", ".join(
            m.replace("claude-", "").replace("-20251101", "").replace("-20250929", "")
            for m in models[:2]
        )
        if len(models) > 2:
            model_str += f" +{len(models)-2}"

        input_tokens = row.get("inputTokens", 0)
        output_tokens = row.get("outputTokens", 0)
        tokens = row.get("totalTokens", 0)
        cost = row.get("totalCost", 0)

        total_input += input_tokens
        total_output += output_tokens
        total_tokens += tokens
        total_cost += cost

        # Get exercises for this date
        exercises = exercise_data.get(date, {})
        exercise_str = format_exercises(exercises)

        # Accumulate totals
        for ex, reps in exercises.items():
            total_reps[ex] += reps

        # Format numbers
        if input_tokens:
            print(f"{date:<12} {model_str:<30} {input_tokens:>12,} {output_tokens:>12,} {tokens:>14,} ${cost:>9.2f} {exercise_str:<30}")
        else:
            print(f"{date:<12} {'-':<30} {'-':>12} {'-':>12} {'-':>14} {'-':>10} {exercise_str:<30}")

    # Totals
    print("=" * 130)
    total_exercise_str = format_exercises(dict(total_reps))
    print(f"{'Total':<12} {'':<30} {total_input:>12,} {total_output:>12,} {total_tokens:>14,} ${total_cost:>9.2f} {total_exercise_str:<30}")


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

    print_combined_table(ccusage_data, exercise_data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
