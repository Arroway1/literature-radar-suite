# //============XJQ(本次修改：测试统一入口的 visualizer 与 weekly-email 两种模式）====================//
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from literature_radar_router import ConfigError, build_dependency_matrix, build_plan, dependency_check


BASE_CONFIG = {
    "recipient_email": "arroway1@gmail.com",
    "timezone": "Asia/Shanghai",
    "start_date": "2026-01-01",
    "output_dir": "F:\\AutopaperManage",
    "sources": ["PubMed", "Crossref", "OpenAlex", "arXiv"],
    "keyword_groups": [{"label": "MRI", "terms": ["MRI", "magnetic resonance"]}],
}


class LiteratureRadarRouterTests(unittest.TestCase):
    def test_visualizer_plan_contains_cap_translation_and_dashboard(self) -> None:
        plan = build_plan("visualizer", BASE_CONFIG, config_path="C:\\work\\daily-literature-digest.config.json")
        self.assertEqual(plan["mode"], "visualizer")
        self.assertEqual(plan["max_papers_per_journal"], 10)
        self.assertIn("translate_dashboard_zh.py", " ".join(plan["required_actions"]))
        self.assertIn("build_literature_dashboard.py", " ".join(plan["required_actions"]))

        # //============XJQ(本次修改：验证统一入口暴露完整依赖矩阵与缺失依赖处理提示)====================//
        matrix = plan["dependency_matrix"]
        self.assertEqual(matrix["paper-vault"]["role"], "optional_archive")
        self.assertEqual(matrix["sciencedirect-live-session-fetcher"]["role"], "optional_sciencedirect_fulltext")
        self.assertEqual(matrix["sciencedirect-live-session-fetcher"]["availability"], "not-installed")
        self.assertIn("browser_pdf_downloader.py", matrix["sciencedirect-live-session-fetcher"]["fallback"])
        self.assertIn("sciencedirect-live-session-fetcher", plan["dependency_check"]["missing_optional"])
        self.assertIn("是否允许安装", plan["dependency_check"]["user_prompt"])
        # //================XJQ(本次修改：验证统一入口暴露完整依赖矩阵与缺失依赖处理提示 END===============//

    # //============XJQ(本次修改：验证日报配置提示包含六个字段及 MRI 参考值)====================//
    def test_default_config_prompt_contains_six_fields_and_mri_references(self) -> None:
        plan = build_plan("visualizer", BASE_CONFIG, config_path="C:\\work\\daily-literature-digest.config.json")
        prompt = plan["config_prompt"]
        for label in ("\u65e5\u62a5\u914d\u7f6e", "\u90ae\u7bb1", "\u65f6\u533a", "\u65e5\u671f", "\u6765\u6e90", "\u5173\u952e\u8bcd", "\u8f93\u51fa\u76ee\u5f55"):
            self.assertIn(label, prompt)
        references = plan["reference_defaults"]
        self.assertEqual(references["date"]["from"], "2026-01-01")
        self.assertEqual(references["date"]["to"], "runtime_date")
        self.assertIn("PubMed", references["sources"])
        self.assertIn("MRM", references["visualizer_journals"])
        self.assertIn("npj Digital Medicine", references["visualizer_journals"])
        self.assertIn("MRI", references["keywords"])
        self.assertIn("Hemodynamics", references["keywords"])
        self.assertTrue(references["email"]["user_supplied"])
        self.assertTrue(references["timezone"]["user_supplied"])
        self.assertTrue(references["output_dir"]["user_supplied"])
    # //================XJQ(本次修改：验证日报配置提示包含六个字段及 MRI 参考值 END===============//

    def test_weekly_email_plan_requires_gmail_status_and_archive_is_optional(self) -> None:
        plan = build_plan("weekly-email", BASE_CONFIG, config_path="C:\\work\\daily-literature-digest.config.json")
        self.assertEqual(plan["mode"], "weekly-email")
        self.assertEqual(plan["recipient_email"], "arroway1@gmail.com")
        self.assertEqual(plan["email_status_values"], ["sent", "failed", "not-configured"])
        self.assertTrue(plan["paper_vault_is_optional"])
        self.assertIn("provider-oriented", plan["source_guard"])
        # //============XJQ(本次修改：确认 weekly-email 计划也携带同一份日报配置提示)====================//
        self.assertIn("config_prompt", plan)
        self.assertIn("reference_defaults", plan)
        # //================XJQ(本次修改：确认 weekly-email 计划也携带同一份日报配置提示 END===============//

    def test_weekly_email_requires_recipient(self) -> None:
        config = dict(BASE_CONFIG)
        config.pop("recipient_email")
        with self.assertRaises(ConfigError):
            build_plan("weekly-email", config, config_path="C:\\work\\daily-literature-digest.config.json")

    def test_missing_required_dependency_pauses_and_prompts_for_install(self) -> None:
        # //============XJQ(本次修改：验证必需依赖缺失时必须暂停并询问是否允许安装)====================//
        with TemporaryDirectory() as temp_dir:
            matrix = build_dependency_matrix(Path(temp_dir))
            result = dependency_check("visualizer", matrix)
        self.assertIn("nature-academic-search", result["missing_required"])
        self.assertTrue(result["must_pause_before_execution"])
        self.assertIn("是否允许安装", result["user_prompt"])
        # //================XJQ(本次修改：验证必需依赖缺失时必须暂停并询问是否允许安装 END===============//


if __name__ == "__main__":
    unittest.main()

# //================XJQ(本次修改：测试统一入口的 visualizer 与 weekly-email 两种模式 END===============//
