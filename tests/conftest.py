"""Gemeinsame Fixtures: das Handbeispiel und zwei Landschaften, an denen jede Einheit geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import izs_landscape as L  # noqa: E402
from izs_instance import hand_instance, make_instance  # noqa: E402


@pytest.fixture
def hand():
    """Drei Plätze nebeneinander (Abstände 1, 1, 2), Fluss A–B: 5, B–C: 1, A–C: 0. Handrechnung in der README."""
    return hand_instance()


@pytest.fixture(scope="session")
def land6():
    inst = make_instance("netlist", 6, 35)
    return inst, L.landscape(inst)


@pytest.fixture(scope="session")
def land8():
    inst = make_instance("uniform", 8, 35)
    return inst, L.landscape(inst)
