"""Atalho local, inclusive antes de instalar o pacote com pip -e ."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from techchallenge4.demo import main

if __name__ == "__main__":
    main()
