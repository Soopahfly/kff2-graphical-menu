#!/usr/bin/env python3
"""Compatibility entry point for the expanded Home regression suite."""
import argparse,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('menu',type=Path);a=p.parse_args()
subprocess.run([sys.executable,Path(__file__).with_name('test_home_features.py'),'--upstream',a.menu.resolve().parent.parent],check=True)
