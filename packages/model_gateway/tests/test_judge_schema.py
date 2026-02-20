from __future__ import annotations

from model_gateway.judge_schema import JudgeVerdict, extract_first_json_object


class TestExtractFirstJsonObject:
    def test_simple_json(self):
        text = '{"decision": "allow"}'
        result = extract_first_json_object(text)
        assert result == '{"decision": "allow"}'

    def test_json_with_surrounding_text(self):
        text = 'Here is my analysis: {"decision": "block", "confidence": 0.9} end'
        result = extract_first_json_object(text)
        assert '"decision": "block"' in result

    def test_nested_json(self):
        text = '{"outer": {"inner": "value"}}'
        result = extract_first_json_object(text)
        assert result == text

    def test_no_json(self):
        result = extract_first_json_object("no json here")
        assert result is None

    def test_empty_string(self):
        result = extract_first_json_object("")
        assert result is None

    def test_unclosed_brace(self):
        result = extract_first_json_object('{"unclosed": true')
        assert result is None

    def test_multiple_objects_returns_first(self):
        text = '{"first": 1} {"second": 2}'
        result = extract_first_json_object(text)
        assert result == '{"first": 1}'

    def test_markdown_fenced(self):
        text = '```json\n{"decision": "allow", "confidence": 0.8}\n```'
        result = extract_first_json_object(text)
        assert '"decision": "allow"' in result


class TestJudgeVerdict:
    def test_defaults(self):
        v = JudgeVerdict()
        assert v.decision == "manual_review"
        assert v.confidence == 0.5

    def test_from_dict(self):
        v = JudgeVerdict.model_validate({
            "decision": "block",
            "confidence": 0.95,
            "confirmed_findings": ["SK-001"],
            "false_positives": [],
            "notes": "bad code",
        })
        assert v.decision == "block"
        assert v.confidence == 0.95
        assert v.confirmed_findings == ["SK-001"]
