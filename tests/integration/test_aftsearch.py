import subprocess
import os


THIS_DIR = os.path.dirname(__file__)
AFTQUERY_PATH = os.path.join(THIS_DIR, os.pardir, os.pardir, "aftquery")


def test_afrsearch_help():
    return_code = subprocess.call(["python", os.path.join(AFTQUERY_PATH, "aftsearch.py"), "--help"])
    assert return_code == 0
