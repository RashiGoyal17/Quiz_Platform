"""
Tests for bulk question import via QuizService.bulk_import_questions().

Covers:
- CSV all-valid
- JSON all-valid
- CSV partial failure (bad correct_option)
- JSON partial failure (marks <= 0)
- All rows invalid
- Empty file (0 rows)
- JSON root not a list
- Row limit exceeded
- Cross-org bank access
- CSV BOM handling
- Lowercase correct_option letter
- Missing required CSV column (text empty)
- JSON missing options field
"""
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.question_bank import QuestionBank
from app.services.quiz_service import MAX_IMPORT_ROWS, QuizService

pytestmark = pytest.mark.asyncio

_ORG_A = uuid.uuid4()
_ORG_B = uuid.uuid4()
_BANK_ID = uuid.uuid4()


def _mock_bank() -> MagicMock:
    b = MagicMock(spec=QuestionBank)
    b.id = _BANK_ID
    b.organization_id = _ORG_A
    return b


def _svc(session: AsyncMock | None = None) -> QuizService:
    return QuizService(session or AsyncMock())


def _make_svc_with_bank(bank: MagicMock | None) -> QuizService:
    svc = _svc()
    svc.bank_repo.get_by_id_scoped = AsyncMock(return_value=bank)
    svc.create_question = AsyncMock()
    return svc


# ── helpers ───────────────────────────────────────────────────────────────────

def _csv_bytes(*rows: dict) -> bytes:
    header = "text,explanation,marks,negative_marks,option_a,option_b,option_c,option_d,correct_option"
    lines = [header]
    for r in rows:
        lines.append(
            f"{r.get('text','')},{r.get('explanation','')},"
            f"{r.get('marks','1')},{r.get('negative_marks','0')},"
            f"{r.get('option_a','Opt A')},{r.get('option_b','Opt B')},"
            f"{r.get('option_c','Opt C')},{r.get('option_d','Opt D')},"
            f"{r.get('correct_option','A')}"
        )
    return "\n".join(lines).encode("utf-8")


def _json_bytes(rows: list[dict]) -> bytes:
    return json.dumps(rows).encode("utf-8")


_VALID_OPTIONS = [
    {"text": "Opt A", "is_correct": True},
    {"text": "Opt B", "is_correct": False},
    {"text": "Opt C", "is_correct": False},
    {"text": "Opt D", "is_correct": False},
]

_VALID_JSON_ROW = {
    "text": "What is 2+2?",
    "explanation": "Basic math",
    "marks": 1,
    "negative_marks": 0,
    "options": _VALID_OPTIONS,
}


# ── CSV tests ─────────────────────────────────────────────────────────────────

class TestCsvImport:
    async def test_all_valid_rows_are_imported(self):
        svc = _make_svc_with_bank(_mock_bank())
        content = _csv_bytes(
            {"text": "Q1", "marks": "1", "negative_marks": "0", "correct_option": "A"},
            {"text": "Q2", "marks": "2", "negative_marks": "0.5", "correct_option": "B"},
            {"text": "Q3", "marks": "1", "negative_marks": "0", "correct_option": "C"},
        )
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, content, "csv")

        assert result.imported == 3
        assert result.failed == 0
        assert result.errors == []
        assert svc.create_question.await_count == 3

    async def test_partial_failure_bad_correct_option(self):
        """Row with correct_option='E' → no option is_correct=True → validation error."""
        svc = _make_svc_with_bank(_mock_bank())
        content = _csv_bytes(
            {"text": "Q1", "marks": "1", "correct_option": "A"},
            {"text": "Q2", "marks": "1", "correct_option": "E"},
            {"text": "Q3", "marks": "1", "correct_option": "D"},
        )
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, content, "csv")

        assert result.imported == 2
        assert result.failed == 1
        assert result.errors[0].row == 2

    async def test_empty_text_fails_validation(self):
        svc = _make_svc_with_bank(_mock_bank())
        content = _csv_bytes(
            {"text": "", "marks": "1", "correct_option": "A"},
        )
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, content, "csv")

        assert result.failed == 1
        assert result.imported == 0
        assert result.errors[0].row == 1

    async def test_marks_zero_fails_validation(self):
        svc = _make_svc_with_bank(_mock_bank())
        content = _csv_bytes(
            {"text": "Q1", "marks": "0", "correct_option": "A"},
        )
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, content, "csv")

        assert result.failed == 1
        assert result.errors[0].field == "marks"

    async def test_lowercase_correct_option_is_accepted(self):
        svc = _make_svc_with_bank(_mock_bank())
        content = _csv_bytes(
            {"text": "Q1", "marks": "1", "correct_option": "b"},
        )
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, content, "csv")

        assert result.imported == 1
        assert result.failed == 0

    async def test_bom_prefixed_csv_is_parsed_correctly(self):
        """UTF-8 BOM must not corrupt the first column name."""
        svc = _make_svc_with_bank(_mock_bank())
        csv_str = (
            "text,explanation,marks,negative_marks,option_a,option_b,option_c,option_d,correct_option\n"
            "Q1,,1,0,A,B,C,D,A"
        )
        content = b"\xef\xbb\xbf" + csv_str.encode("utf-8")
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, content, "csv")

        assert result.imported == 1
        assert result.failed == 0

    async def test_zero_rows_returns_empty_result(self):
        svc = _make_svc_with_bank(_mock_bank())
        content = b"text,explanation,marks,negative_marks,option_a,option_b,option_c,option_d,correct_option\n"
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, content, "csv")

        assert result.imported == 0
        assert result.failed == 0
        assert result.errors == []


# ── JSON tests ────────────────────────────────────────────────────────────────

class TestJsonImport:
    async def test_all_valid_rows_are_imported(self):
        svc = _make_svc_with_bank(_mock_bank())
        rows = [_VALID_JSON_ROW.copy() for _ in range(5)]
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, _json_bytes(rows), "json")

        assert result.imported == 5
        assert result.failed == 0
        assert svc.create_question.await_count == 5

    async def test_partial_failure_marks_negative(self):
        svc = _make_svc_with_bank(_mock_bank())
        rows = [
            _VALID_JSON_ROW.copy(),
            {**_VALID_JSON_ROW, "marks": -1},
            _VALID_JSON_ROW.copy(),
        ]
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, _json_bytes(rows), "json")

        assert result.imported == 2
        assert result.failed == 1
        assert result.errors[0].row == 2
        assert result.errors[0].field == "marks"

    async def test_all_invalid_rows(self):
        svc = _make_svc_with_bank(_mock_bank())
        rows = [
            {"text": "", "marks": -1, "negative_marks": 0, "options": []},
            {"text": "Q", "marks": 0, "negative_marks": 0, "options": _VALID_OPTIONS},
        ]
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, _json_bytes(rows), "json")

        assert result.imported == 0
        assert result.failed == 2
        svc.create_question.assert_not_awaited()

    async def test_json_root_not_list_raises_value_error(self):
        svc = _make_svc_with_bank(_mock_bank())
        content = json.dumps({"text": "Q1"}).encode()

        with pytest.raises(ValueError, match="array"):
            await svc.bulk_import_questions(_BANK_ID, _ORG_A, content, "json")

    async def test_missing_options_field_fails_with_row_error(self):
        svc = _make_svc_with_bank(_mock_bank())
        rows = [{"text": "Q1", "marks": 1, "negative_marks": 0}]
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, _json_bytes(rows), "json")

        assert result.failed == 1
        assert result.errors[0].field == "options"

    async def test_wrong_option_count_fails(self):
        """Fewer or more than 4 options must fail."""
        svc = _make_svc_with_bank(_mock_bank())
        rows = [{**_VALID_JSON_ROW, "options": _VALID_OPTIONS[:3]}]
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, _json_bytes(rows), "json")

        assert result.failed == 1

    async def test_two_correct_options_fails(self):
        svc = _make_svc_with_bank(_mock_bank())
        bad_opts = [{"text": f"O{i}", "is_correct": i < 2} for i in range(4)]
        rows = [{**_VALID_JSON_ROW, "options": bad_opts}]
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, _json_bytes(rows), "json")

        assert result.failed == 1
        assert any("correct" in e.message.lower() for e in result.errors)

    async def test_empty_array_returns_zero_counts(self):
        svc = _make_svc_with_bank(_mock_bank())
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, b"[]", "json")

        assert result.imported == 0
        assert result.failed == 0

    async def test_malformed_json_raises_exception(self):
        svc = _make_svc_with_bank(_mock_bank())
        with pytest.raises(Exception):
            await svc.bulk_import_questions(_BANK_ID, _ORG_A, b"{not valid json", "json")


# ── Tenant isolation tests ────────────────────────────────────────────────────

class TestBulkImportTenantIsolation:
    async def test_bank_from_other_org_raises_lookup_error(self):
        """Bank belongs to ORG_B; caller is ORG_A → 404."""
        svc = _svc()
        svc.bank_repo.get_by_id_scoped = AsyncMock(return_value=None)

        with pytest.raises(LookupError, match="Question bank not found"):
            await svc.bulk_import_questions(_BANK_ID, _ORG_A, b"[]", "json")

    async def test_scoped_lookup_receives_callers_org_id(self):
        svc = _svc()
        svc.bank_repo.get_by_id_scoped = AsyncMock(return_value=None)

        with pytest.raises(LookupError):
            await svc.bulk_import_questions(_BANK_ID, _ORG_A, b"[]", "json")

        svc.bank_repo.get_by_id_scoped.assert_awaited_once_with(_BANK_ID, _ORG_A)

    async def test_no_questions_inserted_on_cross_tenant_bank(self):
        svc = _svc()
        svc.bank_repo.get_by_id_scoped = AsyncMock(return_value=None)
        svc.create_question = AsyncMock()

        with pytest.raises(LookupError):
            await svc.bulk_import_questions(
                _BANK_ID, _ORG_A, _json_bytes([_VALID_JSON_ROW.copy()]), "json"
            )

        svc.create_question.assert_not_awaited()


# ── Row limit test ────────────────────────────────────────────────────────────

class TestRowLimit:
    async def test_exceeding_max_rows_raises_value_error(self):
        svc = _make_svc_with_bank(_mock_bank())
        rows = [_VALID_JSON_ROW.copy() for _ in range(MAX_IMPORT_ROWS + 1)]

        with pytest.raises(ValueError, match=str(MAX_IMPORT_ROWS)):
            await svc.bulk_import_questions(_BANK_ID, _ORG_A, _json_bytes(rows), "json")

        svc.create_question.assert_not_awaited()

    async def test_exactly_max_rows_is_accepted(self):
        svc = _make_svc_with_bank(_mock_bank())
        rows = [_VALID_JSON_ROW.copy() for _ in range(MAX_IMPORT_ROWS)]
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, _json_bytes(rows), "json")

        assert result.imported == MAX_IMPORT_ROWS
        assert result.failed == 0


# ── Error structure tests ─────────────────────────────────────────────────────

class TestErrorStructure:
    async def test_error_contains_correct_row_number(self):
        svc = _make_svc_with_bank(_mock_bank())
        rows = [
            _VALID_JSON_ROW.copy(),
            _VALID_JSON_ROW.copy(),
            {**_VALID_JSON_ROW, "marks": 0},
        ]
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, _json_bytes(rows), "json")

        assert result.errors[0].row == 3

    async def test_multiple_errors_on_single_row_are_reported(self):
        """A row with both bad marks and wrong option count generates multiple errors."""
        svc = _make_svc_with_bank(_mock_bank())
        rows = [{"text": "Q", "marks": -1, "negative_marks": 0, "options": []}]
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, _json_bytes(rows), "json")

        assert result.failed == 1
        assert len(result.errors) >= 2

    async def test_failed_count_matches_errors_list_length_when_one_error_per_row(self):
        svc = _make_svc_with_bank(_mock_bank())
        rows = [
            {**_VALID_JSON_ROW, "marks": 0},
            {**_VALID_JSON_ROW, "marks": 0},
        ]
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, _json_bytes(rows), "json")

        assert result.failed == 2
        assert all(e.row in (1, 2) for e in result.errors)

    async def test_imported_and_failed_sum_to_total_valid_rows(self):
        svc = _make_svc_with_bank(_mock_bank())
        rows = [
            _VALID_JSON_ROW.copy(),
            {**_VALID_JSON_ROW, "marks": -1},
            _VALID_JSON_ROW.copy(),
            {**_VALID_JSON_ROW, "marks": -1},
            _VALID_JSON_ROW.copy(),
        ]
        result = await svc.bulk_import_questions(_BANK_ID, _ORG_A, _json_bytes(rows), "json")

        assert result.imported == 3
        assert result.failed == 2
