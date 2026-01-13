#!/usr/bin/env python3
"""
configure.py - Interactive configuration for VibeReps
Allows users to select detection engine and customize settings.
"""

import json
import sys
from pathlib import Path

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{text}{Colors.NC}")


def print_option(num, name, desc, selected=False):
    marker = f"{Colors.GREEN}*{Colors.NC}" if selected else " "
    print(f"  {marker} {Colors.YELLOW}{num}{Colors.NC}) {Colors.BOLD}{name}{Colors.NC}")
    print(f"       {desc}")


def get_config_path():
    return Path(__file__).parent / "config.json"


def load_config():
    config_path = get_config_path()
    if config_path.exists():
        try:
            return json.loads(config_path.read_text())
        except json.JSONDecodeError:
            pass

    # Return default config
    return {
        "detection_engine": "mediapipe",
        "detection_engines": {
            "mediapipe": {
                "name": "MediaPipe",
                "description": "Google's MediaPipe Pose - Best accuracy, requires internet for CDN",
                "model_complexity": 1,
                "smooth_landmarks": True,
                "min_detection_confidence": 0.5,
                "min_tracking_confidence": 0.5
            },
            "tensorflow": {
                "name": "TensorFlow.js MoveNet",
                "description": "TensorFlow.js MoveNet - Fast, good accuracy, works offline after first load",
                "model_type": "lightning",
                "score_threshold": 0.3
            },
            "simple": {
                "name": "Simple Landmarks",
                "description": "Basic landmark detection - Fastest, lower accuracy, minimal resources",
                "smoothing": True,
                "confidence_threshold": 0.4
            }
        }
    }


def save_config(config):
    config_path = get_config_path()
    config_path.write_text(json.dumps(config, indent=2))
    print(f"\n{Colors.GREEN}Configuration saved to {config_path}{Colors.NC}")


def configure_detection_engine(config, non_interactive=None):
    """Configure the detection engine."""
    print_header("Detection Engine Configuration")

    engines = {
        "1": ("mediapipe", "MediaPipe Pose",
              "Best accuracy, 33 landmarks, requires internet for CDN loading"),
        "2": ("tensorflow", "TensorFlow.js MoveNet",
              "Fast & accurate, 17 keypoints, caches for offline use after first load"),
        "3": ("simple", "Simple Landmarks",
              "Lightweight, basic keypoint detection, minimal CPU/memory usage")
    }

    current = config.get("detection_engine", "mediapipe")

    print("\nChoose your detection engine:\n")

    for num, (key, name, desc) in engines.items():
        print_option(num, name, desc, selected=(key == current))

    print()

    if non_interactive is not None:
        choice = non_interactive
        print(f"  Selected: {choice}")
    else:
        choice = input(f"  Enter choice [1-3] (current: {current}): ").strip()

    if choice in engines:
        engine_key = engines[choice][0]
        config["detection_engine"] = engine_key
        print(f"\n  {Colors.GREEN}Selected: {engines[choice][1]}{Colors.NC}")
        return True
    elif choice == "":
        print(f"\n  Keeping current: {current}")
        return False
    else:
        print(f"\n  {Colors.RED}Invalid choice. Keeping current: {current}{Colors.NC}")
        return False


def configure_engine_settings(config):
    """Configure engine-specific settings."""
    engine = config.get("detection_engine", "mediapipe")
    engine_config = config.get("detection_engines", {}).get(engine, {})

    print_header(f"{engine_config.get('name', engine)} Settings")

    if engine == "mediapipe":
        print("\n  Model complexity affects accuracy vs speed:")
        print(f"    0 = Fastest, lower accuracy")
        print(f"    1 = Balanced (recommended)")
        print(f"    2 = Most accurate, slower")

        current = engine_config.get("model_complexity", 1)
        choice = input(f"\n  Model complexity [0-2] (current: {current}): ").strip()

        if choice in ("0", "1", "2"):
            config["detection_engines"]["mediapipe"]["model_complexity"] = int(choice)
            print(f"  {Colors.GREEN}Set model complexity to {choice}{Colors.NC}")

    elif engine == "tensorflow":
        print("\n  Model type:")
        print(f"    lightning = Faster, good for real-time")
        print(f"    thunder   = More accurate, slightly slower")

        current = engine_config.get("model_type", "lightning")
        choice = input(f"\n  Model type [lightning/thunder] (current: {current}): ").strip().lower()

        if choice in ("lightning", "thunder"):
            config["detection_engines"]["tensorflow"]["model_type"] = choice
            print(f"  {Colors.GREEN}Set model type to {choice}{Colors.NC}")

    elif engine == "simple":
        print("\n  Simple engine uses basic image processing.")
        print("  Smoothing helps reduce jitter but adds latency.")

        current = engine_config.get("smoothing", True)
        choice = input(f"\n  Enable smoothing? [y/n] (current: {'yes' if current else 'no'}): ").strip().lower()

        if choice in ("y", "yes"):
            config["detection_engines"]["simple"]["smoothing"] = True
            print(f"  {Colors.GREEN}Smoothing enabled{Colors.NC}")
        elif choice in ("n", "no"):
            config["detection_engines"]["simple"]["smoothing"] = False
            print(f"  {Colors.GREEN}Smoothing disabled{Colors.NC}")


def show_current_config(config):
    """Display current configuration."""
    print_header("Current Configuration")

    engine = config.get("detection_engine", "mediapipe")
    engine_config = config.get("detection_engines", {}).get(engine, {})

    print(f"\n  Detection Engine: {Colors.CYAN}{engine_config.get('name', engine)}{Colors.NC}")
    print(f"  {engine_config.get('description', '')}")

    print(f"\n  Engine Settings:")
    for key, value in engine_config.items():
        if key not in ("name", "description"):
            print(f"    {key}: {Colors.YELLOW}{value}{Colors.NC}")


def main():
    print(f"\n{Colors.GREEN}{'='*60}{Colors.NC}")
    print(f"{Colors.GREEN}           VibeReps Configuration{Colors.NC}")
    print(f"{Colors.GREEN}{'='*60}{Colors.NC}")

    config = load_config()

    # Handle command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg in ("--help", "-h"):
            print("""
Usage: configure.py [OPTIONS]

Options:
  --show              Show current configuration
  --engine ENGINE     Set detection engine (mediapipe, tensorflow, simple)
  --engine-prompt     Prompt for engine selection only
  --help, -h          Show this help

Examples:
  ./configure.py                    # Interactive configuration
  ./configure.py --show             # Show current config
  ./configure.py --engine mediapipe # Set engine directly
  ./configure.py --engine-prompt    # Quick engine selection
""")
            return 0

        elif arg == "--show":
            show_current_config(config)
            return 0

        elif arg == "--engine" and len(sys.argv) > 2:
            engine = sys.argv[2].lower()
            if engine in ("mediapipe", "tensorflow", "simple"):
                config["detection_engine"] = engine
                save_config(config)
                print(f"{Colors.GREEN}Detection engine set to: {engine}{Colors.NC}")
            else:
                print(f"{Colors.RED}Invalid engine. Choose: mediapipe, tensorflow, simple{Colors.NC}")
                return 1
            return 0

        elif arg == "--engine-prompt":
            # Quick engine selection (for install script)
            configure_detection_engine(config)
            save_config(config)
            return 0

    # Interactive mode
    show_current_config(config)

    while True:
        print_header("Options")
        print(f"  {Colors.YELLOW}1{Colors.NC}) Change detection engine")
        print(f"  {Colors.YELLOW}2{Colors.NC}) Configure engine settings")
        print(f"  {Colors.YELLOW}3{Colors.NC}) Show current configuration")
        print(f"  {Colors.YELLOW}s{Colors.NC}) Save and exit")
        print(f"  {Colors.YELLOW}q{Colors.NC}) Quit without saving")

        choice = input(f"\n  Enter choice: ").strip().lower()

        if choice == "1":
            configure_detection_engine(config)
        elif choice == "2":
            configure_engine_settings(config)
        elif choice == "3":
            show_current_config(config)
        elif choice == "s":
            save_config(config)
            print(f"\n{Colors.GREEN}Configuration complete!{Colors.NC}")
            print(f"Restart the exercise tracker to apply changes.\n")
            break
        elif choice == "q":
            print(f"\n{Colors.YELLOW}Exiting without saving.{Colors.NC}\n")
            break
        else:
            print(f"\n{Colors.RED}Invalid choice.{Colors.NC}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
