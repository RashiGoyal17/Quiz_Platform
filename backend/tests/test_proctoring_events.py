"""
Unit tests for Phase 6B: Proctoring Events.

Tests cover:
  - log_proctoring_event: allowed types, rejected types, ownership, status, timeout
  - get_attempt_audit: proctoring_events list is populated in the response
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.attempt import Attempt
from app.models.enums import AttemptStatus, ProctoringEventType
from app.models.proctoring_event import ProctoringEvent
from app.models.quiz import Quiz
from app.models.tab_switch_log import TabSwitchLog
from app.schemas.attempt import AttemptAuditResponse, ProctoringEventResponse
from app.services.attempt_service import AttemptService, STUDENT_ALLOWED_EVENT_TYPES


# ── helpers ───────────────────────────────────────────────────────────────────

def _svc(session: AsyncMock | None = None) -> AttemptService:
    return AttemptService(session or AsyncMock())


def _make_attempt(
    student_id: uuid.UUID,
    quiz_id: uuid.UUID,
    *,
    status: AttemptStatus = AttemptStatus.IN_PROGRESS,
    started_at: datetime | None = None,
) -> MagicMock:
    a = MagicMock(spec=Attempt)
    a.id = uuid.uuid4()
    a.student_id = student_id
    a.quiz_id = quiz_id
    a.status = status
    a.started_at = started_at or datetime.now(timezone.utc)
    a.tab_switch_count = 0
    a.ip_address = None
    a.attempt_number = 1
    a.submitted_at = None
    a.score = None
    a.created_at = datetime.now(timezone.utc)
    return a


def _make_quiz(duration_minutes: int = 60) -> MagicMock:
    q = MagicMock(spec=Quiz)
    q.id = uuid.uuid4()
    q.duration_minutes = duration_minutes
    q.max_tab_switches = None
    return q


def _make_proctoring_event(
    attempt_id: uuid.UUID,
    event_type: ProctoringEventType = ProctoringEventType.WINDOW_BLUR,
    metadata: dict | None = None,
) -> MagicMock:
    e = MagicMock(spec=ProctoringEvent)
    e.id = uuid.uuid4()
    e.attempt_id = attempt_id
    e.event_type = event_type
    e.occurred_at = datetime.now(timezone.utc)
    e.event_metadata = metadata
    return e


# ── STUDENT_ALLOWED_EVENT_TYPES constant ──────────────────────────────────────

class TestAllowedEventTypesConstant:
    def test_window_blur_is_allowed(self):
        assert ProctoringEventType.WINDOW_BLUR in STUDENT_ALLOWED_EVENT_TYPES

    def test_copy_paste_is_allowed(self):
        assert ProctoringEventType.COPY_PASTE in STUDENT_ALLOWED_EVENT_TYPES

    def test_fullscreen_exit_is_allowed(self):
        assert ProctoringEventType.FULLSCREEN_EXIT in STUDENT_ALLOWED_EVENT_TYPES

    def test_tab_switch_is_not_allowed(self):
        assert ProctoringEventType.TAB_SWITCH not in STUDENT_ALLOWED_EVENT_TYPES

    def test_ai_types_are_not_allowed(self):
        ai_types = {
            ProctoringEventType.FACE_NOT_DETECTED,
            ProctoringEventType.MULTIPLE_FACES,
            ProctoringEventType.PHONE_DETECTED,
            ProctoringEventType.AUDIO_DETECTED,
        }
        assert ai_types.isdisjoint(STUDENT_ALLOWED_EVENT_TYPES)


# ── log_proctoring_event ──────────────────────────────────────────────────────

class TestLogProctoringEvent:

    def _wire(
        self,
        svc: AttemptService,
        attempt: MagicMock,
        quiz: MagicMock,
        event_return: MagicMock,
    ) -> None:
        svc.attempt_repo.get_by_id = AsyncMock(return_value=attempt)
        svc.quiz_repo.get_by_id = AsyncMock(return_value=quiz)
        svc.proctoring_event_repo.create = AsyncMock(return_value=event_return)

    # ── happy paths ───────────────────────────────────────────────────────────

    async def test_window_blur_accepted(self):
        student_id = uuid.uuid4()
        svc = _svc()
        attempt = _make_attempt(student_id, uuid.uuid4())
        quiz = _make_quiz()
        event = _make_proctoring_event(attempt.id, ProctoringEventType.WINDOW_BLUR, {"duration_ms": 800})
        self._wire(svc, attempt, quiz, event)

        result = await svc.log_proctoring_event(
            attempt.id, student_id, ProctoringEventType.WINDOW_BLUR, {"duration_ms": 800}
        )

        assert isinstance(result, ProctoringEventResponse)
        assert result.event_type == ProctoringEventType.WINDOW_BLUR.value
        assert result.metadata == {"duration_ms": 800}
        svc.proctoring_event_repo.create.assert_awaited_once()

    async def test_copy_paste_accepted(self):
        student_id = uuid.uuid4()
        svc = _svc()
        attempt = _make_attempt(student_id, uuid.uuid4())
        quiz = _make_quiz()
        event = _make_proctoring_event(attempt.id, ProctoringEventType.COPY_PASTE, {"element_type": "input"})
        self._wire(svc, attempt, quiz, event)

        result = await svc.log_proctoring_event(
            attempt.id, student_id, ProctoringEventType.COPY_PASTE, {"element_type": "input"}
        )

        assert result.event_type == ProctoringEventType.COPY_PASTE.value

    async def test_fullscreen_exit_accepted(self):
        student_id = uuid.uuid4()
        svc = _svc()
        attempt = _make_attempt(student_id, uuid.uuid4())
        quiz = _make_quiz()
        event = _make_proctoring_event(attempt.id, ProctoringEventType.FULLSCREEN_EXIT)
        self._wire(svc, attempt, quiz, event)

        result = await svc.log_proctoring_event(
            attempt.id, student_id, ProctoringEventType.FULLSCREEN_EXIT, None
        )

        assert result.event_type == ProctoringEventType.FULLSCREEN_EXIT.value

    async def test_null_metadata_accepted(self):
        student_id = uuid.uuid4()
        svc = _svc()
        attempt = _make_attempt(student_id, uuid.uuid4())
        quiz = _make_quiz()
        event = _make_proctoring_event(attempt.id, ProctoringEventType.WINDOW_BLUR, None)
        self._wire(svc, attempt, quiz, event)

        result = await svc.log_proctoring_event(
            attempt.id, student_id, ProctoringEventType.WINDOW_BLUR, None
        )

        assert result.metadata is None

    # ── rejected event types ──────────────────────────────────────────────────

    async def test_tab_switch_rejected_with_specific_message(self):
        student_id = uuid.uuid4()
        svc = _svc()
        attempt = _make_attempt(student_id, uuid.uuid4())
        quiz = _make_quiz()
        self._wire(svc, attempt, quiz, MagicMock())

        with pytest.raises(ValueError, match="tab-switch"):
            await svc.log_proctoring_event(
                attempt.id, student_id, ProctoringEventType.TAB_SWITCH, None
            )

        svc.proctoring_event_repo.create.assert_not_awaited()

    async def test_face_not_detected_rejected(self):
        student_id = uuid.uuid4()
        svc = _svc()
        attempt = _make_attempt(student_id, uuid.uuid4())
        quiz = _make_quiz()
        self._wire(svc, attempt, quiz, MagicMock())

        with pytest.raises(ValueError, match="not accepted from client"):
            await svc.log_proctoring_event(
                attempt.id, student_id, ProctoringEventType.FACE_NOT_DETECTED, None
            )

    async def test_multiple_faces_rejected(self):
        student_id = uuid.uuid4()
        svc = _svc()
        attempt = _make_attempt(student_id, uuid.uuid4())
        quiz = _make_quiz()
        self._wire(svc, attempt, quiz, MagicMock())

        with pytest.raises(ValueError, match="not accepted from client"):
            await svc.log_proctoring_event(
                attempt.id, student_id, ProctoringEventType.MULTIPLE_FACES, None
            )

    async def test_phone_detected_rejected(self):
        student_id = uuid.uuid4()
        svc = _svc()
        attempt = _make_attempt(student_id, uuid.uuid4())
        quiz = _make_quiz()
        self._wire(svc, attempt, quiz, MagicMock())

        with pytest.raises(ValueError, match="not accepted from client"):
            await svc.log_proctoring_event(
                attempt.id, student_id, ProctoringEventType.PHONE_DETECTED, None
            )

    async def test_audio_detected_rejected(self):
        student_id = uuid.uuid4()
        svc = _svc()
        attempt = _make_attempt(student_id, uuid.uuid4())
        quiz = _make_quiz()
        self._wire(svc, attempt, quiz, MagicMock())

        with pytest.raises(ValueError, match="not accepted from client"):
            await svc.log_proctoring_event(
                attempt.id, student_id, ProctoringEventType.AUDIO_DETECTED, None
            )

    # ── ownership / status guards ─────────────────────────────────────────────

    async def test_attempt_not_found_raises_lookup_error(self):
        svc = _svc()
        svc.attempt_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(LookupError, match="Attempt not found"):
            await svc.log_proctoring_event(
                uuid.uuid4(), uuid.uuid4(), ProctoringEventType.WINDOW_BLUR, None
            )

    async def test_wrong_student_raises_lookup_error(self):
        svc = _svc()
        attempt = _make_attempt(uuid.uuid4(), uuid.uuid4())  # owned by a different student
        svc.attempt_repo.get_by_id = AsyncMock(return_value=attempt)

        with pytest.raises(LookupError, match="Attempt not found"):
            await svc.log_proctoring_event(
                attempt.id, uuid.uuid4(), ProctoringEventType.WINDOW_BLUR, None
            )

    async def test_submitted_attempt_raises_value_error(self):
        student_id = uuid.uuid4()
        svc = _svc()
        attempt = _make_attempt(student_id, uuid.uuid4(), status=AttemptStatus.SUBMITTED)
        svc.attempt_repo.get_by_id = AsyncMock(return_value=attempt)

        with pytest.raises(ValueError, match="not in progress"):
            await svc.log_proctoring_event(
                attempt.id, student_id, ProctoringEventType.WINDOW_BLUR, None
            )

    async def test_abandoned_attempt_raises_value_error(self):
        student_id = uuid.uuid4()
        svc = _svc()
        attempt = _make_attempt(student_id, uuid.uuid4(), status=AttemptStatus.ABANDONED)
        svc.attempt_repo.get_by_id = AsyncMock(return_value=attempt)

        with pytest.raises(ValueError, match="not in progress"):
            await svc.log_proctoring_event(
                attempt.id, student_id, ProctoringEventType.WINDOW_BLUR, None
            )

    # ── timeout enforcement ───────────────────────────────────────────────────

    async def test_expired_attempt_triggers_timeout_and_raises(self):
        """Timer expired: _enforce_timeout_if_expired grades and raises ValueError."""
        student_id = uuid.uuid4()
        svc = _svc()
        # started_at 2 hours ago, duration 60 min → expired
        expired_started_at = datetime.now(timezone.utc) - timedelta(hours=2)
        attempt = _make_attempt(student_id, uuid.uuid4(), started_at=expired_started_at)
        quiz = _make_quiz(duration_minutes=60)

        svc.attempt_repo.get_by_id = AsyncMock(return_value=attempt)
        svc.quiz_repo.get_by_id = AsyncMock(return_value=quiz)
        # timeout_attempt calls _grade_attempt which calls get_by_attempt_with_details
        svc.attempt_question_repo.get_by_attempt_with_details = AsyncMock(return_value=[])
        # Explicitly mock create so we can assert it was never called
        svc.proctoring_event_repo.create = AsyncMock()

        with pytest.raises(ValueError, match="time has expired"):
            await svc.log_proctoring_event(
                attempt.id, student_id, ProctoringEventType.WINDOW_BLUR, None
            )

        # No proctoring event should have been created
        svc.proctoring_event_repo.create.assert_not_awaited()

    # ── ProctoringEvent ORM object is passed to repo.create ──────────────────

    async def test_correct_fields_passed_to_repo_create(self):
        """Verify that create receives a ProctoringEvent with the right fields."""
        student_id = uuid.uuid4()
        svc = _svc()
        attempt = _make_attempt(student_id, uuid.uuid4())
        quiz = _make_quiz()
        metadata = {"duration_ms": 500}
        event = _make_proctoring_event(attempt.id, ProctoringEventType.COPY_PASTE, metadata)

        svc.attempt_repo.get_by_id = AsyncMock(return_value=attempt)
        svc.quiz_repo.get_by_id = AsyncMock(return_value=quiz)

        captured: list[ProctoringEvent] = []

        async def _capture_create(entity):
            captured.append(entity)
            return event

        svc.proctoring_event_repo.create = _capture_create

        await svc.log_proctoring_event(
            attempt.id, student_id, ProctoringEventType.COPY_PASTE, metadata
        )

        assert len(captured) == 1
        created = captured[0]
        assert isinstance(created, ProctoringEvent)
        assert created.attempt_id == attempt.id
        assert created.event_type == ProctoringEventType.COPY_PASTE
        assert created.event_metadata == metadata


# ── get_attempt_audit: proctoring_events populated ───────────────────────────

class TestGetAttemptAuditProctoringEvents:

    async def test_audit_includes_empty_proctoring_events_list(self):
        """Audit response has proctoring_events: [] when no events recorded."""
        svc = _svc()
        student_id = uuid.uuid4()
        attempt = _make_attempt(student_id, uuid.uuid4())

        svc.attempt_repo.get_by_id = AsyncMock(return_value=attempt)
        svc.tab_switch_log_repo.get_by_attempt = AsyncMock(return_value=[])
        svc.proctoring_event_repo.get_by_attempt = AsyncMock(return_value=[])

        result = await svc.get_attempt_audit(attempt.id)

        assert isinstance(result, AttemptAuditResponse)
        assert result.proctoring_events == []
        svc.proctoring_event_repo.get_by_attempt.assert_awaited_once_with(attempt.id)

    async def test_audit_includes_proctoring_events_in_response(self):
        """Audit response contains all proctoring events returned by the repo."""
        svc = _svc()
        student_id = uuid.uuid4()
        attempt = _make_attempt(student_id, uuid.uuid4())

        event_blur = _make_proctoring_event(attempt.id, ProctoringEventType.WINDOW_BLUR, {"duration_ms": 200})
        event_paste = _make_proctoring_event(attempt.id, ProctoringEventType.COPY_PASTE, {"content_length": 10})

        svc.attempt_repo.get_by_id = AsyncMock(return_value=attempt)
        svc.tab_switch_log_repo.get_by_attempt = AsyncMock(return_value=[])
        svc.proctoring_event_repo.get_by_attempt = AsyncMock(return_value=[event_blur, event_paste])

        result = await svc.get_attempt_audit(attempt.id)

        assert len(result.proctoring_events) == 2
        types = {e.event_type for e in result.proctoring_events}
        assert "window_blur" in types
        assert "copy_paste" in types

    async def test_audit_proctoring_events_carry_metadata(self):
        """Metadata in each event is correctly surfaced in the audit response."""
        svc = _svc()
        student_id = uuid.uuid4()
        attempt = _make_attempt(student_id, uuid.uuid4())
        meta = {"element_type": "textarea", "content_length": 99}
        event = _make_proctoring_event(attempt.id, ProctoringEventType.COPY_PASTE, meta)

        svc.attempt_repo.get_by_id = AsyncMock(return_value=attempt)
        svc.tab_switch_log_repo.get_by_attempt = AsyncMock(return_value=[])
        svc.proctoring_event_repo.get_by_attempt = AsyncMock(return_value=[event])

        result = await svc.get_attempt_audit(attempt.id)

        assert result.proctoring_events[0].metadata == meta

    async def test_audit_not_found_raises_lookup_error(self):
        svc = _svc()
        svc.attempt_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(LookupError, match="Attempt not found"):
            await svc.get_attempt_audit(uuid.uuid4())

    async def test_audit_tab_switch_logs_still_present(self):
        """Adding proctoring_events must not break existing tab_switch_logs field."""
        svc = _svc()
        student_id = uuid.uuid4()
        attempt = _make_attempt(student_id, uuid.uuid4())

        log = MagicMock(spec=TabSwitchLog)
        log.id = uuid.uuid4()
        log.switched_at = datetime.now(timezone.utc)

        svc.attempt_repo.get_by_id = AsyncMock(return_value=attempt)
        svc.tab_switch_log_repo.get_by_attempt = AsyncMock(return_value=[log])
        svc.proctoring_event_repo.get_by_attempt = AsyncMock(return_value=[])

        result = await svc.get_attempt_audit(attempt.id)

        assert len(result.tab_switch_logs) == 1
        assert result.proctoring_events == []
