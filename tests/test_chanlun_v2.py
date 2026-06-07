import tempfile
import unittest
from pathlib import Path

from chanlun_v2_app import analyzer, report, storage
from chanlun_v2_app.bi_service import create_bi
from chanlun_v2_app.models import Bi, KLine
from chanlun_v2_app.storage import load_bis, load_klines, merge_klines, save_bis, save_config, save_klines


def sample_klines(count=12):
    return [
        KLine(
            dt=f"2026-06-01 {index:02d}:00:00",
            open=100 + index,
            high=102 + index,
            low=98 + index,
            close=101 + index,
            volume=1000 + index,
        )
        for index in range(count)
    ]


class ChanlunV2Test(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmpdir.name)
        self.originals = {
            "storage_kline": storage.KLINE_CSV,
            "storage_bi": storage.BI_CSV,
            "storage_config": storage.CONFIG_JSON,
            "storage_history": storage.HISTORY_JSON,
            "analyzer_segments": analyzer.SEGMENTS_JSON,
            "analyzer_zhongshu": analyzer.ZHONGSHU_JSON,
            "analyzer_signals": analyzer.SIGNALS_JSON,
            "report_data_dir": report.DATA_DIR,
        }
        storage.KLINE_CSV = self.data_dir / "csi852_30min.csv"
        storage.BI_CSV = self.data_dir / "csi852_bi.csv"
        storage.CONFIG_JSON = self.data_dir / "config.json"
        storage.HISTORY_JSON = self.data_dir / "history.json"
        analyzer.SEGMENTS_JSON = self.data_dir / "segments.json"
        analyzer.ZHONGSHU_JSON = self.data_dir / "zhongshu.json"
        analyzer.SIGNALS_JSON = self.data_dir / "signals.json"
        report.DATA_DIR = self.data_dir

    def tearDown(self):
        storage.KLINE_CSV = self.originals["storage_kline"]
        storage.BI_CSV = self.originals["storage_bi"]
        storage.CONFIG_JSON = self.originals["storage_config"]
        storage.HISTORY_JSON = self.originals["storage_history"]
        analyzer.SEGMENTS_JSON = self.originals["analyzer_segments"]
        analyzer.ZHONGSHU_JSON = self.originals["analyzer_zhongshu"]
        analyzer.SIGNALS_JSON = self.originals["analyzer_signals"]
        report.DATA_DIR = self.originals["report_data_dir"]
        self.tmpdir.cleanup()

    def test_merge_klines_keeps_latest_same_time(self):
        old = [KLine("2026-06-01 10:00:00", 1, 2, 0.5, 1.5, 100)]
        new = [KLine("2026-06-01 10:00:00", 3, 4, 2, 3.5, 200)]
        merged = merge_klines(old, new)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].close, 3.5)

    def test_save_and_load_csv(self):
        save_klines(sample_klines(3))
        self.assertEqual(len(load_klines()), 3)

    def test_create_bi_requires_five_klines_and_shared_endpoint(self):
        save_klines(sample_klines(10))
        with self.assertRaises(ValueError):
            create_bi("2026-06-01 00:00:00", "2026-06-01 03:00:00", 98, 105)
        first = create_bi("2026-06-01 00:00:00", "2026-06-01 05:00:00", 98, 107)
        self.assertEqual(first.kline_count, 6)
        with self.assertRaises(ValueError):
            create_bi("2026-06-01 06:00:00", "2026-06-01 09:00:00", 108, 111)
        second = create_bi("2026-06-01 05:00:00", "2026-06-01 09:00:00", 107, 111)
        self.assertEqual(second.index, 2)

    def test_analyzer_builds_segment_zhongshu_and_signals(self):
        save_klines(sample_klines(10))
        save_bis(
            [
                Bi(1, "下", "1", "2", 5, 100, 90),
                Bi(2, "上", "2", "3", 5, 90, 110),
                Bi(3, "下", "3", "4", 5, 105, 95),
            ]
        )
        result = analyzer.analyze_and_save()
        self.assertEqual(result["segments"][0]["方向"], "向上")
        self.assertEqual(result["zhongshu"][0]["ZD"], 95)
        self.assertEqual(result["zhongshu"][0]["ZG"], 100)
        self.assertEqual(result["signals"][0]["类型"], "一卖")

    def test_report_writes_local_and_obsidian_files(self):
        save_klines(sample_klines(10))
        save_bis(
            [
                Bi(1, "下", "1", "2", 5, 100, 90),
                Bi(2, "上", "2", "3", 5, 90, 110),
                Bi(3, "下", "3", "4", 5, 105, 95),
            ]
        )
        vault = self.data_dir / "vault"
        save_config({"obsidian_vault": str(vault)})
        result = report.generate_report()
        self.assertTrue(Path(result["local_path"]).exists())
        self.assertTrue(Path(result["obsidian_path"]).exists())
        content = Path(result["local_path"]).read_text(encoding="utf-8")
        self.assertIn("## 六、操作建议", content)


if __name__ == "__main__":
    unittest.main()

