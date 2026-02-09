import json
import argparse
from pathlib import Path

import torch

from .data_loader import CryptoDataLoader
from .vm import StackVM
from .backtest import MemeBacktest
from .config import ModelConfig


def main():
    parser = argparse.ArgumentParser(description="Backtest a saved formula.")
    parser.add_argument(
        "--formula_file",
        type=str,
        default="best_meme_strategy.json",
        help="Path to the JSON file containing formula tokens",
    )
    args = parser.parse_args()

    path = Path(args.formula_file)
    if not path.exists():
        print(f"[Error] Formula file not found: {path}")
        return

    try:
        formula = json.loads(path.read_text())
    except Exception as e:
        print(f"[Error] Failed to load formula: {e}")
        return

    print(f"Using device: {ModelConfig.DEVICE}")
    print(f"Loaded formula tokens: {formula}")

    loader = CryptoDataLoader()
    loader.load_data()

    vm = StackVM()
    res = vm.execute(formula, loader.feat_tensor)
    if res is None:
        print("[Error] VM execution returned None (invalid formula).")
        return

    bt = MemeBacktest()
    score, avg_ret = bt.evaluate(res, loader.raw_data_cache, loader.target_ret)
    print(f"Backtest finished.\nScore: {score:.4f}\nAverage return: {avg_ret:.6f}")


if __name__ == "__main__":
    main()