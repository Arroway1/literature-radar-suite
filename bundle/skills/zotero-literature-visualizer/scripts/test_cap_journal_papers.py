# //============XJQ(本次修改：测试每个期刊的文献数量上限和稳定保留顺序）====================//
import unittest

from cap_journal_papers import cap_papers_by_journal, normalize_journal


class CapJournalPapersTests(unittest.TestCase):
    def test_normalize_journal_collapses_whitespace_and_missing_values(self) -> None:
        self.assertEqual(normalize_journal("  Magnetic   Resonance in Medicine "), "Magnetic Resonance in Medicine")
        self.assertEqual(normalize_journal(""), "Metadata missing / 未提供")

    def test_caps_each_journal_and_keeps_original_rank_order(self) -> None:
        papers = [
            {"rank": index, "journal": "Journal A", "title": f"A {index}", "publication_date": f"2026-01-{index:02d}"}
            for index in range(1, 13)
        ] + [
            {"rank": 20, "journal": "Journal B", "title": "B 1", "publication_date": "2026-01-20"},
            {"rank": 21, "journal": "Journal B", "title": "B 2", "publication_date": "2026-01-21"},
        ]

        selected, summary = cap_papers_by_journal(papers, max_per_journal=10)

        self.assertEqual(len(selected), 12)
        self.assertEqual([paper["title"] for paper in selected if paper["journal"] == "Journal A"], [f"A {i}" for i in range(1, 11)])
        self.assertEqual(summary["journals"]["Journal A"], {"before": 12, "after": 10, "removed": 2})
        self.assertLessEqual(max(summary["journals"][journal]["after"] for journal in summary["journals"]), 10)

    def test_invalid_limit_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            cap_papers_by_journal([], max_per_journal=0)


if __name__ == "__main__":
    unittest.main()

# //================XJQ(本次修改：测试每个期刊的文献数量上限和稳定保留顺序 END===============//
