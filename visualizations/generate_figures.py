"""
Generate all figures using the CognitiveVizualizer with dummy data.
Saves to visualizations/figures/ as PNG (300 DPI), PDF, and SVG.
"""

import os
import numpy as np
import pandas as pd

from visualization import CognitiveVizualizer


def main() -> None:
    out_dir = os.path.join(os.path.dirname(__file__), 'figures')
    viz = CognitiveVizualizer(style='paper', dpi=300)
    viz.save_all_figures(out_dir)
    print(f"Saved figures to: {out_dir}")


if __name__ == "__main__":
    np.random.seed(42)
    main()


