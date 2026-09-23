"""Načte čisté moduly integrace bez nutnosti instalovat Home Assistant."""

import importlib
import sys
import types
from pathlib import Path

PKG = "akce_na_pivo"
PATH = Path(__file__).resolve().parent.parent / "custom_components" / PKG

if PKG not in sys.modules:
    package = types.ModuleType(PKG)
    package.__path__ = [str(PATH)]
    sys.modules[PKG] = package
    importlib.import_module(f"{PKG}.const")
    importlib.import_module(f"{PKG}.kupi")
