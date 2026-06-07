import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.attempt_question import AttemptQuestion
from app.models.attempt_question_option import AttemptQuestionOption
from app.models.enums import AttemptStatus, ProctoringEventType
from app.models.proctoring_event import ProctoringEvent
from app.models.quiz import Quiz
from app.models.tab_switch_log import TabSwitchLog
from app.repositories.attempt_repository import (
    AttemptAnswerRepository,
    AttemptQuestionRepository,
    AttemptRepository,
    ProctoringEventRepository,
    TabSwitchLogRepository,
)
from app.repositories.quiz_repository import QuizRepository
from app.schemas.attempt import (
    AnswerResponse,
    AttemptAdminResponse,
    AttemptAuditResponse,
    AttemptOptionResponse,
    AttemptOptionResultResponse,
    AttemptQuestionResponse,
    AttemptQuestionResultResponse,
    AttemptResponse,
    AttemptResultResponse,
    ProctoringEventResponse,
    TabSwitchLogResponse,
    TabSwitchResponse,
)

# Event types students may report from the browser.
# TAB_SWITCH has its own dedicated endpoint (/tab-switch).
# AI-detection types (FACE_NOT_DETECTED etc.) are reserved for server-side systems.
STUDENT_ALLOWED_EVENT_TYPES: frozenset[ProctoringEventType] = frozenset({
    ProctoringEventType.WINDOW_BLUR,
    ProctoringEventType.COPY_PASTE,
    ProctoringEventType.FULLSCREEN_EXIT,
})


class AttemptService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.attempt_repo = AttemptRepository(session)
        self.attempt_question_repo = AttemptQuestionRepository(session)
        self.answer_repo = AttemptAnswerRepository(session)
        self.quiz_repo = QuizRepository(session)
        self.tab_switch_log_repo = TabSwitchLogRepository(session)
        self.proctoring_event_repo = ProctoringEventRepository(session)

    # ── Internal helpers ───────────────────────────────────────────────────

    def _build_attempt_response(
        self, attempt: Attempt, questions: list[AttemptQuestion], time_limit_minutes: int
    ) -> AttemptResponse:
        aq_responses = []
        for aq in questions:
            answer = aq.answer
            opts = sorted(aq.options, key=lambda o: o.position)
            aq_responses.append(
                AttemptQuestionResponse(
                    id=aq.id,
                    question_text_snapshot=aq.question_text_snapshot,
                    position=aq.position,
                    marks=aq.marks,
                    negative_marks=aq.negative_marks,
                    options=[
                        AttemptOptionResponse(
                            id=o.id,
                            option_text_snapshot=o.option_text_snapshot,
                            position=o.position,
                        )
                        for o in opts
                    ],
                    selected_option_id=answer.selected_option_id if answer else None,
                )
            )
        return AttemptResponse(
            id=attempt.id,
            quiz_id=attempt.quiz_id,
            student_id=attempt.student_id,
            attempt_number=attempt.attempt_number,
            status=attempt.status,
            started_at=attempt.started_at,
            time_limit_minutes=time_limit_minutes,
            questions=aq_responses,
        )

    def _build_result_response(
        self,
        attempt: Attempt,
        questions: list[AttemptQuestion],
        score: Decimal,
        correct_count: int,
        incorrect_count: int,
        unanswered_count: int,
    ) -> AttemptResultResponse:
        total_possible = sum(q.marks for q in questions)
        percentage = (
            (score / Decimal(str(total_possible)) * 100).quantize(Decimal("0.01"))
            if total_possible > 0
            else Decimal("0.00")
        )

        aq_responses = []
        for aq in questions:
            answer = aq.answer
            opts = sorted(aq.options, key=lambda o: o.position)
            aq_responses.append(
                AttemptQuestionResultResponse(
                    id=aq.id,
                    question_text_snapshot=aq.question_text_snapshot,
                    position=aq.position,
                    marks=aq.marks,
                    negative_marks=aq.negative_marks,
                    options=[
                        AttemptOptionResultResponse(
                            id=o.id,
                            option_text_snapshot=o.option_text_snapshot,
                            is_correct_snapshot=o.is_correct_snapshot,
                            position=o.position,
                        )
                        for o in opts
                    ],
                    selected_option_id=answer.selected_option_id if answer else None,
                    is_correct=answer.is_correct if answer else None,
                    marks_awarded=answer.marks_awarded if answer else None,
                )
            )

        return AttemptResultResponse(
            id=attempt.id,
            quiz_id=attempt.quiz_id,
            student_id=attempt.student_id,
            attempt_number=attempt.attempt_number,
            status=attempt.status,
            started_at=attempt.started_at,
            submitted_at=attempt.submitted_at,
            score=score,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            unanswered_count=unanswered_count,
            percentage=percentage,
            questions=aq_responses,
        )

    async def _grade_attempt(self, attempt_id: UUID) -> tuple[Decimal, int, int, int]:
        """
        Score every question, write is_correct/marks_awarded onto each AttemptAnswer,
        and flush. Returns (score_floored_at_0, correct, incorrect, unanswered).
        """
        questions = await self.attempt_question_repo.get_by_attempt_with_details(attempt_id)

        total_score = Decimal("0.00")
        correct_count = 0
        incorrect_count = 0
        unanswered_count = 0

        for aq in questions:
            answer = aq.answer
            if answer is None or answer.selected_option_id is None:
                unanswered_count += 1
                if answer is not None:
                    answer.marks_awarded = Decimal("0.00")
                    answer.is_correct = None
            else:
                selected = next(
                    (o for o in aq.options if o.id == answer.selected_option_id), None
                )
                if selected and selected.is_correct_snapshot:
                    correct_count += 1
                    awarded = aq.marks
                    answer.is_correct = True
                    answer.marks_awarded = awarded
                    total_score += awarded
                else:
                    incorrect_count += 1
                    awarded = -aq.negative_marks
                    answer.is_correct = False
                    answer.marks_awarded = awarded
                    total_score += awarded

        await self.session.flush()
        return max(total_score, Decimal("0.00")), correct_count, incorrect_count, unanswered_count

    def _attempt_has_expired(self, attempt: Attempt, quiz: Quiz) -> bool:
        deadline = attempt.started_at + timedelta(minutes=quiz.duration_minutes)
        return datetime.now(timezone.utc) > deadline

    async def _enforce_timeout_if_expired(self, attempt: Attempt, quiz: Quiz) -> None:
        """Grade and mark TIMED_OUT if the attempt timer has run out. Raises ValueError."""
        if self._attempt_has_expired(attempt, quiz):
            await self.timeout_attempt(attempt.id)
            raise ValueError("Attempt time has expired")

    # ── Public methods ─────────────────────────────────────────────────────

    async def start_attempt(
        self, student_id: UUID, quiz_id: UUID, ip_address: str | None = None
    ) -> AttemptResponse:
        """
        Start or resume a quiz attempt.

        - Returns the existing IN_PROGRESS attempt if one exists (resume path).
        - On resume, enforces timeout: if timer expired, grades and raises ValueError.
        - Validates quiz is published and within its optional time window.
        - Enforces max_attempts against all prior attempts for this student+quiz.
        - Snapshots questions and options, respecting shuffle settings.
        """
        quiz = await self.quiz_repo.get_by_id(quiz_id)
        if quiz is None:
            raise LookupError("Quiz not found")
        if not quiz.is_published:
            raise ValueError("Quiz is not published")

        now = datetime.now(timezone.utc)
        if quiz.start_time and now < quiz.start_time:
            raise ValueError("Quiz has not started yet")
        if quiz.end_time and now > quiz.end_time:
            raise ValueError("Quiz has ended")

        # Resume path — check timeout before returning
        active = await self.attempt_repo.get_active_attempt(student_id, quiz_id)
        if active is not None:
            await self._enforce_timeout_if_expired(active, quiz)
            questions = await self.attempt_question_repo.get_by_attempt_with_details(active.id)
            return self._build_attempt_response(active, questions, quiz.duration_minutes)

        # Enforce attempt limit
        prior_count = await self.attempt_repo.count_student_quiz_attempts(student_id, quiz_id)
        if prior_count >= quiz.max_attempts:
            raise ValueError(
                f"Attempt limit reached ({quiz.max_attempts}). No more attempts allowed."
            )

        # Create attempt
        attempt = Attempt(
            student_id=student_id,
            quiz_id=quiz_id,
            attempt_number=prior_count + 1,
            status=AttemptStatus.IN_PROGRESS,
            ip_address=ip_address,
        )
        attempt = await self.attempt_repo.create(attempt)

        # Load quiz questions with eager options for snapshotting
        quiz_questions = await self.quiz_repo.get_quiz_questions_with_details(quiz_id)

        if quiz.shuffle_questions:
            random.shuffle(quiz_questions)

        for position, qq in enumerate(quiz_questions):
            q = qq.question
            effective_marks = (
                qq.marks_override if qq.marks_override is not None else q.marks
            )
            aq = AttemptQuestion(
                attempt_id=attempt.id,
                question_id=q.id,
                question_text_snapshot=q.text,
                position=position,
                marks=effective_marks,
                negative_marks=q.negative_marks,
            )
            self.session.add(aq)
            await self.session.flush()
            await self.session.refresh(aq)

            options = list(q.options)
            if quiz.shuffle_options:
                random.shuffle(options)

            for opt_position, opt in enumerate(options):
                self.session.add(
                    AttemptQuestionOption(
                        attempt_question_id=aq.id,
                        option_id=opt.id,
                        option_text_snapshot=opt.text,
                        is_correct_snapshot=opt.is_correct,
                        position=opt_position,
                    )
                )

        await self.session.flush()

        questions = await self.attempt_question_repo.get_by_attempt_with_details(attempt.id)
        return self._build_attempt_response(attempt, questions, quiz.duration_minutes)

    async def save_answer(
        self,
        attempt_id: UUID,
        attempt_question_id: UUID,
        selected_option_id: UUID | None,
        student_id: UUID,
    ) -> AnswerResponse:
        """
        Upsert the student's answer. Idempotent — safe to call on every keystroke.
        Enforces timeout: raises ValueError if the attempt timer has expired.
        Pass selected_option_id=null to clear a previously saved answer.
        """
        attempt = await self.attempt_repo.get_by_id(attempt_id)
        if attempt is None or attempt.student_id != student_id:
            raise LookupError("Attempt not found")
        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise ValueError("Attempt is not in progress")

        quiz = await self.quiz_repo.get_by_id(attempt.quiz_id)
        await self._enforce_timeout_if_expired(attempt, quiz)

        aq = await self.attempt_question_repo.get_by_id(attempt_question_id)
        if aq is None or aq.attempt_id != attempt_id:
            raise LookupError("Question not found in this attempt")

        if selected_option_id is not None:
            aq_with_opts = await self.attempt_question_repo.get_with_options(attempt_question_id)
            valid_ids = {opt.id for opt in aq_with_opts.options}  # type: ignore[union-attr]
            if selected_option_id not in valid_ids:
                raise ValueError("Option does not belong to this question")

        now = datetime.now(timezone.utc)
        existing = await self.answer_repo.get_by_attempt_question(attempt_question_id)

        if existing is not None:
            existing.selected_option_id = selected_option_id
            existing.answered_at = now
            await self.session.flush()
            return AnswerResponse(
                id=existing.id,
                attempt_question_id=existing.attempt_question_id,
                selected_option_id=existing.selected_option_id,
                answered_at=existing.answered_at,
            )

        answer = AttemptAnswer(
            attempt_id=attempt_id,
            attempt_question_id=attempt_question_id,
            selected_option_id=selected_option_id,
            answered_at=now,
        )
        answer = await self.answer_repo.create(answer)
        return AnswerResponse(
            id=answer.id,
            attempt_question_id=answer.attempt_question_id,
            selected_option_id=answer.selected_option_id,
            answered_at=answer.answered_at,
        )

    async def submit_attempt(self, attempt_id: UUID, student_id: UUID) -> AttemptResultResponse:
        """
        Lock the attempt, grade all answers, and return the full result.
        If the timer has already expired at submission time, marks TIMED_OUT instead
        of SUBMITTED — still grades and returns results.
        """
        attempt = await self.attempt_repo.get_by_id(attempt_id)
        if attempt is None or attempt.student_id != student_id:
            raise LookupError("Attempt not found")
        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise ValueError("Attempt is not in progress")

        quiz = await self.quiz_repo.get_by_id(attempt.quiz_id)
        final_status = (
            AttemptStatus.TIMED_OUT
            if self._attempt_has_expired(attempt, quiz)
            else AttemptStatus.SUBMITTED
        )

        score, correct, incorrect, unanswered = await self._grade_attempt(attempt_id)

        now = datetime.now(timezone.utc)
        attempt.status = final_status
        attempt.submitted_at = now
        attempt.score = score

        await self.session.flush()
        await self.session.refresh(attempt)

        questions = await self.attempt_question_repo.get_by_attempt_with_details(attempt_id)
        return self._build_result_response(attempt, questions, score, correct, incorrect, unanswered)

    async def timeout_attempt(self, attempt_id: UUID) -> None:
        """
        Transition an IN_PROGRESS attempt to TIMED_OUT and grade it.
        No-op if the attempt is already finalized.
        """
        attempt = await self.attempt_repo.get_by_id(attempt_id)
        if attempt is None:
            raise LookupError("Attempt not found")
        if attempt.status != AttemptStatus.IN_PROGRESS:
            return

        score, _, _, _ = await self._grade_attempt(attempt_id)

        now = datetime.now(timezone.utc)
        attempt.status = AttemptStatus.TIMED_OUT
        attempt.submitted_at = now
        attempt.score = score

        await self.session.flush()
        await self.session.refresh(attempt)

    async def log_tab_switch(
        self, attempt_id: UUID, student_id: UUID
    ) -> TabSwitchResponse:
        """
        Record a tab switch event and increment the counter atomically.
        If max_tab_switches is set and the new count exceeds it, marks the attempt
        ABANDONED (not graded, not submitted — admin reviews manually).
        Enforces timeout before logging.
        """
        attempt = await self.attempt_repo.get_by_id(attempt_id)
        if attempt is None or attempt.student_id != student_id:
            raise LookupError("Attempt not found")
        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise ValueError("Attempt is not in progress")

        quiz = await self.quiz_repo.get_by_id(attempt.quiz_id)
        await self._enforce_timeout_if_expired(attempt, quiz)

        # Create the log entry (switched_at set by server_default)
        self.session.add(TabSwitchLog(attempt_id=attempt_id))

        # Atomic increment — prevents race conditions on concurrent tab-switch events
        result = await self.session.execute(
            update(Attempt)
            .where(Attempt.id == attempt_id)
            .values(tab_switch_count=Attempt.tab_switch_count + 1)
            .returning(Attempt.tab_switch_count)
        )
        new_count = result.scalar_one()
        await self.session.flush()
        await self.session.refresh(attempt)

        # Enforce limit — ABANDONED, not graded
        limit_exceeded = False
        if quiz.max_tab_switches is not None and new_count > quiz.max_tab_switches:
            attempt.status = AttemptStatus.ABANDONED
            await self.session.flush()
            await self.session.refresh(attempt)
            limit_exceeded = True

        return TabSwitchResponse(
            attempt_id=attempt_id,
            tab_switch_count=new_count,
            max_tab_switches=quiz.max_tab_switches,
            limit_exceeded=limit_exceeded,
            attempt_status=attempt.status.value,
        )

    async def get_attempt_result(
        self, attempt_id: UUID, requester_id: UUID
    ) -> AttemptResultResponse:
        """
        Return the graded result for a completed attempt.
        Students can view SUBMITTED, TIMED_OUT, and ABANDONED results.
        """
        attempt = await self.attempt_repo.get_by_id(attempt_id)
        if attempt is None or attempt.student_id != requester_id:
            raise LookupError("Attempt not found")
        if attempt.status == AttemptStatus.IN_PROGRESS:
            raise ValueError("Attempt has not been submitted yet")

        questions = await self.attempt_question_repo.get_by_attempt_with_details(attempt_id)

        correct = sum(1 for q in questions if q.answer and q.answer.is_correct is True)
        incorrect = sum(1 for q in questions if q.answer and q.answer.is_correct is False)
        unanswered = sum(
            1 for q in questions
            if q.answer is None or q.answer.selected_option_id is None
        )
        score = attempt.score or Decimal("0.00")

        return self._build_result_response(attempt, questions, score, correct, incorrect, unanswered)

    async def list_attempts_admin(
        self,
        quiz_id: UUID | None = None,
        student_id: UUID | None = None,
        status: AttemptStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Attempt]:
        return await self.attempt_repo.get_all_filtered(
            quiz_id=quiz_id,
            student_id=student_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def log_proctoring_event(
        self,
        attempt_id: UUID,
        student_id: UUID,
        event_type: ProctoringEventType,
        metadata: dict[str, Any] | None,
    ) -> ProctoringEventResponse:
        """
        Record a proctoring event for an IN_PROGRESS attempt.

        Only WINDOW_BLUR, COPY_PASTE, and FULLSCREEN_EXIT are accepted from
        students. TAB_SWITCH must go through /tab-switch. AI-detection types
        are reserved for server-side systems.

        Enforces ownership, IN_PROGRESS status, and timeout.
        """
        attempt = await self.attempt_repo.get_by_id(attempt_id)
        if attempt is None or attempt.student_id != student_id:
            raise LookupError("Attempt not found")
        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise ValueError("Attempt is not in progress")

        quiz = await self.quiz_repo.get_by_id(attempt.quiz_id)
        await self._enforce_timeout_if_expired(attempt, quiz)

        if event_type not in STUDENT_ALLOWED_EVENT_TYPES:
            if event_type == ProctoringEventType.TAB_SWITCH:
                raise ValueError("Tab switch events must use the /tab-switch endpoint")
            raise ValueError(
                f"Event type '{event_type.value}' is not accepted from client submissions"
            )

        event = ProctoringEvent(
            attempt_id=attempt_id,
            event_type=event_type,
            event_metadata=metadata,
        )
        event = await self.proctoring_event_repo.create(event)
        return ProctoringEventResponse.model_validate(event)

    async def get_attempt_audit(self, attempt_id: UUID) -> AttemptAuditResponse:
        """Return full audit trail: attempt metadata, tab switch log, and proctoring events."""
        attempt = await self.attempt_repo.get_by_id(attempt_id)
        if attempt is None:
            raise LookupError("Attempt not found")

        logs = await self.tab_switch_log_repo.get_by_attempt(attempt_id)
        events = await self.proctoring_event_repo.get_by_attempt(attempt_id)

        return AttemptAuditResponse(
            attempt=AttemptAdminResponse.model_validate(attempt),
            tab_switch_logs=[TabSwitchLogResponse.model_validate(log) for log in logs],
            proctoring_events=[ProctoringEventResponse.model_validate(e) for e in events],
        )
