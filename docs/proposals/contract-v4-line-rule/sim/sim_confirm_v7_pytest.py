# ruff: noqa
# NON-PRODUCTION. Read-only: the existing suite with contract v4 revision 4 patched in memory (nothing is written).
# match_posting().found then means "suggested by the résumé"; the self-reported score is a separate step (contract §2).
# Run from the repo root at fa1555e:  python <this file> [pytest args]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ".")
import sim_confirm_v7  # patches sim_supported_v6.analyse with the revision 4 rule
import sim_supported_v6_pytest  # patches the engine in memory using that rule
if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main(["-q", "-p", "no:cacheprovider", "tests", "-rf", "--tb=no", *sys.argv[1:]]))
