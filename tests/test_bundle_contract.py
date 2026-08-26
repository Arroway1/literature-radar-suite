# //============XJQ(本次修改：先验证统一 Skill 发布包的清单、目录边界和个人数据隔离契约)====================//
import json
import unittest
from pathlib import Path


SUITE_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = SUITE_ROOT / "bundle-manifest.json"
EXPECTED_INCLUDED = {
    "literature-radar-hub",
    "nature-academic-search",
    "zotero-literature-visualizer",
    "daily-literature-digest",
    "paper-vault",
    "paper-close-reading",
}


class LiteratureRadarSuiteContractTests(unittest.TestCase):
    def test_manifest_and_included_skill_snapshots_are_complete(self) -> None:
        self.assertTrue(MANIFEST_PATH.is_file(), "bundle-manifest.json is required")
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["suite_name"], "literature-radar-suite")
        self.assertEqual(set(entry["name"] for entry in manifest["included"]), EXPECTED_INCLUDED)
        bundle_root = (SUITE_ROOT / manifest["bundle_root"]).resolve()
        self.assertEqual(bundle_root, (SUITE_ROOT / "bundle" / "skills").resolve())

        for entry in manifest["included"]:
            relative = Path(entry["path"])
            self.assertFalse(relative.is_absolute())
            skill_dir = (SUITE_ROOT / relative).resolve()
            self.assertTrue(skill_dir.is_relative_to(bundle_root))
            self.assertTrue((skill_dir / "SKILL.md").is_file(), entry["name"])

    def test_unavailable_optional_dependency_is_not_faked(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        missing = {entry["name"]: entry for entry in manifest["optional_missing"]}
        self.assertEqual(missing["sciencedirect-live-session-fetcher"]["status"], "not-installed")
        self.assertNotIn("path", missing["sciencedirect-live-session-fetcher"])
        self.assertFalse((SUITE_ROOT / "bundle" / "skills" / "sciencedirect-live-session-fetcher").exists())

    def test_bundle_contains_no_personal_runtime_artifacts(self) -> None:
        forbidden_names = {"daily-literature-digest.config.json", "cookies", "browser-profile"}
        for path in (SUITE_ROOT / "bundle").rglob("*"):
            if path.is_file():
                self.assertNotIn(path.name.lower(), forbidden_names)
                self.assertFalse(path.suffix.lower() == ".pdf", path)
                self.assertNotIn("password", path.name.lower())
                self.assertNotIn("token", path.name.lower())

    def test_hub_snapshot_documents_suite_sync_boundary(self) -> None:
        hub_text = (SUITE_ROOT / "bundle" / "skills" / "literature-radar-hub" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("literature-radar-suite", hub_text)
        self.assertIn("Gmail connector/MCP", hub_text)
        self.assertIn("不会同步", hub_text)

    def test_manifest_and_readme_define_cross_agent_install_boundary(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        compatibility = manifest["agent_compatibility"]
        self.assertIn("SKILL.md", compatibility["portable_contract"])
        self.assertIn("Codex", compatibility["adapters"])
        self.assertIn("other_agents", compatibility)
        readme = (SUITE_ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("TargetSkillsRoot", readme)
        self.assertIn("不支持", readme)


if __name__ == "__main__":
    unittest.main()

# //================XJQ(本次修改：先验证统一 Skill 发布包的清单、目录边界和个人数据隔离契约 END===============//
