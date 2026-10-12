import hashlib
import json
from pathlib import Path


FIXTURE_DIR = Path(__file__).resolve().parents[2] / "src" / "xsagent" / "llm" / "fixtures"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_prose_fixture_hash_golden():
    path = FIXTURE_DIR / "prose_chapter.md"
    assert _sha256(path) == "07644eab2dd1e0b39b27406921193c4479d9a6a848d984c0780809cec612dc3f"


def test_bible_sync_fixture_hash_golden():
    path = FIXTURE_DIR / "bible_sync.json"
    assert _sha256(path) == "f7d74f1d64c380043604d8119b45fc9af49bc1ae3adbd6b3603ff220e395dce9"


def test_drift_findings_fixture_hash_golden():
    path = FIXTURE_DIR / "drift_findings.json"
    assert _sha256(path) == "9294d538089b9daf452353616d613f120459af01402dc9597d864bd6e5f10b93"


def test_fixture_json_contracts():
    bible_sync = json.loads((FIXTURE_DIR / "bible_sync.json").read_text(encoding="utf-8"))
    drift_findings = json.loads((FIXTURE_DIR / "drift_findings.json").read_text(encoding="utf-8"))

    assert isinstance(bible_sync.get("updates"), list)
    assert bible_sync.get("risk_level") in {"low", "medium", "high"}
    assert isinstance(drift_findings.get("findings"), list)

    goal = json.loads((FIXTURE_DIR / "goal_verdict.json").read_text(encoding="utf-8"))
    checkpoint = json.loads((FIXTURE_DIR / "checkpoint.json").read_text(encoding="utf-8"))
    assert goal.get("satisfied") is True
    assert isinstance(goal.get("gaps"), list)
    assert checkpoint.get("summary")
    assert isinstance(checkpoint.get("open_loops"), list)
