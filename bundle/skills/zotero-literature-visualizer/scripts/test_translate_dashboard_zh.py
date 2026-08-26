# //============XJQ(本次修改：测试 dashboard ZH 字段必须是中文且不泄漏英文原文）====================//
import unittest

from translate_dashboard_zh import (
    contains_cjk,
    fallback_zh,
    translate_bundle,
)


class TranslateDashboardZhTests(unittest.TestCase):
    def test_bundle_translates_each_evidence_field(self) -> None:
        source = {
            "topic": "Topic: Artificial intelligence improves MRI reconstruction.",
            "method": "Method clues: deep learning and segmentation.",
            "data": "Data clues: 48 participants.",
            "findings": "Findings: the model improved sensitivity.",
            "limits": "Limitations: external validation is needed.",
        }

        def fake_translator(text: str) -> str:
            return "中文翻译：" + text.replace("Topic:", "主题：").replace("Method clues:", "方法线索：").replace("Data clues:", "数据线索：").replace("Findings:", "结果证据：").replace("Limitations:", "局限线索：")

        translated = translate_bundle(source, translator=fake_translator)
        self.assertEqual(set(translated), set(source))
        for field, value in translated.items():
            self.assertTrue(contains_cjk(value), field)
            self.assertNotIn(source[field], value)

    def test_failed_translation_is_chinese_only_fallback(self) -> None:
        source = {"topic": "Topic: English title and abstract evidence."}

        def failing_translator(_: str) -> str:
            raise RuntimeError("network unavailable")

        translated = translate_bundle(source, translator=failing_translator)
        self.assertTrue(contains_cjk(translated["topic"]))
        self.assertNotIn("English title", translated["topic"])
        self.assertEqual(translated["topic"], fallback_zh("topic"))


if __name__ == "__main__":
    unittest.main()

# //================XJQ(本次修改：测试 dashboard ZH 字段必须是中文且不泄漏英文原文 END===============//
