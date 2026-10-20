import unittest

from pipeline import prepare, validate


SOURCE = "https://xhslink.cn/o/example"


class PipelineTests(unittest.TestCase):
    def test_prepare_success(self):
        raw = {
            "code": 200,
            "data": {
                "success": True,
                "code": 0,
                "data": [{"note_list": [{
                    "id": "abc", "title": "上海小店", "desc": "云朵咖啡适合看书。",
                    "images_list": [{"url": "https://example.com/image.jpg"}],
                }]}],
            },
        }
        note = prepare(raw, SOURCE)
        self.assertEqual(note["note_id"], "abc")
        self.assertEqual(len(note["image_urls"]), 1)
        self.assertEqual(note["source_url"], SOURCE)

    def test_prepare_rejects_failed_payload(self):
        with self.assertRaises(ValueError):
            prepare({"code": 200, "data": {"success": False}}, SOURCE)

    def test_validate_grounded_result(self):
        note = {"title": "上海小店", "body": "云朵咖啡适合看书。", "source_url": SOURCE}
        result = {"places": [{
            "place_name": "云朵咖啡", "city": "上海", "place_kind": "poi",
            "features": ["适合看书"], "recommendation": "适合看书",
            "evidence": "云朵咖啡适合看书", "source_url": SOURCE,
        }]}
        self.assertEqual(validate(note, result), [])

    def test_validate_rejects_invention_and_wrong_source(self):
        note = {"title": "上海小店", "body": "云朵咖啡适合看书。", "source_url": SOURCE}
        result = {"places": [{
            "place_name": "虚构餐馆", "city": "上海", "place_kind": "poi",
            "features": ["米其林"], "recommendation": "很好吃",
            "evidence": "云朵咖啡适合看书", "source_url": "https://example.com/wrong",
        }]}
        errors = validate(note, result)
        self.assertTrue(any("place_name" in error for error in errors))
        self.assertTrue(any("source_url" in error for error in errors))
        self.assertTrue(any("recommendation" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
