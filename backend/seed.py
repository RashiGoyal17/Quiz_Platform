"""
Deterministic, idempotent seed script for the Quiz Platform.

Usage:
    python seed.py           # seed everything
    python seed.py --verify  # only verify counts, do not insert

Seed structure:
    Organizations  : 2  (Alpha Tech Academy, Beta Engineering Institute)
    Admins         : 2  (one per org)
    Students       : 20
    Question Banks : 4  (2 per org)
    Questions      : 24 (6 per bank)
    Quizzes        : 4  (2 per org, each published, 6 questions each)

All primary-key UUIDs are hardcoded so re-runs are idempotent.
Emails / slugs are also unique-constrained sentinels for the same reason.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.enums import UserRole
from app.models.organization import Organization
from app.models.question import Question
from app.models.question_bank import QuestionBank
from app.models.question_option import QuestionOption
from app.models.quiz import Quiz
from app.models.quiz_question import QuizQuestion
from app.models.user import User
from app.utils.password import hash_password

# ── Deterministic UUIDs ───────────────────────────────────────────────────────

ORG_ALPHA_ID = uuid.UUID("aaaa0001-0000-0000-0000-000000000001")
ORG_BETA_ID  = uuid.UUID("bbbb0001-0000-0000-0000-000000000001")

ADMIN_ALPHA_ID = uuid.UUID("aaaa0002-0000-0000-0000-000000000001")
ADMIN_BETA_ID  = uuid.UUID("bbbb0002-0000-0000-0000-000000000001")

BANK_ALPHA_DSA_ID = uuid.UUID("aaaa0010-0000-0000-0000-000000000001")
BANK_ALPHA_AI_ID  = uuid.UUID("aaaa0011-0000-0000-0000-000000000001")
BANK_BETA_DE_ID   = uuid.UUID("bbbb0010-0000-0000-0000-000000000001")
BANK_BETA_SD_ID   = uuid.UUID("bbbb0011-0000-0000-0000-000000000001")

QUIZ_ALPHA_1_ID = uuid.UUID("aaaa0020-0000-0000-0000-000000000001")
QUIZ_ALPHA_2_ID = uuid.UUID("aaaa0021-0000-0000-0000-000000000001")
QUIZ_BETA_1_ID  = uuid.UUID("bbbb0020-0000-0000-0000-000000000001")
QUIZ_BETA_2_ID  = uuid.UUID("bbbb0021-0000-0000-0000-000000000001")

# Student IDs: s01 … s20
def _student_id(n: int) -> uuid.UUID:
    return uuid.UUID(f"cccc{n:04d}-0000-0000-0000-000000000001")

# Question IDs: encode bank_letter (1-4) and index into a deterministic UUID
# Format: 0000<bank><idx:04d>-0000-0000-0000-000000000001
_BANK_NUM = {"a": "1", "b": "2", "c": "3", "d": "4"}

def _qid(bank_letter: str, idx: int) -> uuid.UUID:
    bn = _BANK_NUM[bank_letter]
    # 8 hex digits for the first segment
    first = f"{bn}{idx:07d}"  # e.g. "10000001"
    return uuid.UUID(f"{first}-0000-0000-0000-000000000001")


# ── Data definitions ──────────────────────────────────────────────────────────

@dataclass
class OptionDef:
    text: str
    is_correct: bool


@dataclass
class QuestionDef:
    id: uuid.UUID
    text: str
    explanation: str
    marks: Decimal
    negative_marks: Decimal
    options: list[OptionDef]


@dataclass
class OrgDef:
    id: uuid.UUID
    name: str
    slug: str


@dataclass
class AdminDef:
    id: uuid.UUID
    email: str
    username: str
    full_name: str
    password: str
    org_id: uuid.UUID


@dataclass
class BankDef:
    id: uuid.UUID
    name: str
    description: str
    org_id: uuid.UUID
    admin_id: uuid.UUID
    questions: list[QuestionDef] = field(default_factory=list)


@dataclass
class QuizDef:
    id: uuid.UUID
    title: str
    description: str
    duration_minutes: int
    org_id: uuid.UUID
    admin_id: uuid.UUID
    question_ids: list[uuid.UUID]


# ── Organization & admin definitions ─────────────────────────────────────────

ORGS = [
    OrgDef(ORG_ALPHA_ID, "Alpha Tech Academy", "alpha-tech-academy"),
    OrgDef(ORG_BETA_ID,  "Beta Engineering Institute", "beta-engineering-institute"),
]

ADMINS = [
    AdminDef(ADMIN_ALPHA_ID, "admin@alpha.dev", "admin_alpha", "Alex Chen",    "Alpha@Admin123!", ORG_ALPHA_ID),
    AdminDef(ADMIN_BETA_ID,  "admin@beta.dev",  "admin_beta",  "Priya Sharma", "Beta@Admin123!",  ORG_BETA_ID),
]

STUDENTS = [
    ("student01@example.com", "student01", "Liam Torres"),
    ("student02@example.com", "student02", "Emma Nguyen"),
    ("student03@example.com", "student03", "Noah Patel"),
    ("student04@example.com", "student04", "Olivia Kim"),
    ("student05@example.com", "student05", "Ava Ramirez"),
    ("student06@example.com", "student06", "Elijah Singh"),
    ("student07@example.com", "student07", "Sophia Brown"),
    ("student08@example.com", "student08", "James Wilson"),
    ("student09@example.com", "student09", "Isabella Davis"),
    ("student10@example.com", "student10", "Benjamin Martinez"),
    ("student11@example.com", "student11", "Mia Anderson"),
    ("student12@example.com", "student12", "Lucas Thompson"),
    ("student13@example.com", "student13", "Charlotte Jackson"),
    ("student14@example.com", "student14", "Henry White"),
    ("student15@example.com", "student15", "Amelia Harris"),
    ("student16@example.com", "student16", "Alexander Clark"),
    ("student17@example.com", "student17", "Evelyn Lewis"),
    ("student18@example.com", "student18", "Daniel Robinson"),
    ("student19@example.com", "student19", "Abigail Walker"),
    ("student20@example.com", "student20", "Jackson Hall"),
]


# ── Question Bank: Alpha — DSA & Programming ──────────────────────────────────

def _o(text: str, correct: bool) -> OptionDef:
    return OptionDef(text=text, is_correct=correct)


BANK_ALPHA_DSA = BankDef(
    id=BANK_ALPHA_DSA_ID,
    name="DSA & Programming",
    description="Data Structures, Algorithms, Python, Java, C++ — interview and assessment questions",
    org_id=ORG_ALPHA_ID,
    admin_id=ADMIN_ALPHA_ID,
    questions=[
        QuestionDef(
            id=_qid("a", 1),
            text="What is the worst-case time complexity of QuickSort?",
            explanation="QuickSort degrades to O(n²) when the pivot is always the smallest or largest element (e.g., sorted input with naive pivot selection).",
            marks=Decimal("2"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("O(n log n)", False),
                _o("O(n²)", True),
                _o("O(n)", False),
                _o("O(log n)", False),
            ],
        ),
        QuestionDef(
            id=_qid("a", 2),
            text="Which data structure is used internally by Python's `dict`?",
            explanation="Python dictionaries are implemented as hash tables, providing average O(1) lookup, insert, and delete.",
            marks=Decimal("1"),
            negative_marks=Decimal("0.25"),
            options=[
                _o("Balanced BST", False),
                _o("Hash table", True),
                _o("Skip list", False),
                _o("Trie", False),
            ],
        ),
        QuestionDef(
            id=_qid("a", 3),
            text="In Python, what does the `__slots__` declaration do in a class?",
            explanation="__slots__ prevents the creation of a per-instance __dict__, reducing memory overhead for classes with many instances.",
            marks=Decimal("2"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("Defines allowed method names", False),
                _o("Restricts attribute creation to a fixed set, saving memory", True),
                _o("Makes all attributes read-only", False),
                _o("Enables multiple inheritance", False),
            ],
        ),
        QuestionDef(
            id=_qid("a", 4),
            text="What is the space complexity of merge sort on an array of n elements?",
            explanation="Merge sort requires O(n) auxiliary space for the temporary arrays used during the merge step.",
            marks=Decimal("2"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("O(1)", False),
                _o("O(log n)", False),
                _o("O(n)", True),
                _o("O(n log n)", False),
            ],
        ),
        QuestionDef(
            id=_qid("a", 5),
            text="Which of the following correctly describes a Python generator?",
            explanation="A generator is a function that uses `yield` to lazily produce values one at a time, enabling memory-efficient iteration.",
            marks=Decimal("1.5"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("A function that returns a list of all computed values at once", False),
                _o("A function using `yield` that lazily produces values on demand", True),
                _o("A built-in class for parallel execution", False),
                _o("A decorator that caches function results", False),
            ],
        ),
        QuestionDef(
            id=_qid("a", 6),
            text="In C++, what is the difference between `new` and `malloc`?",
            explanation="`new` calls constructors and is type-safe; `malloc` allocates raw bytes and does not invoke constructors. `new` throws on failure; `malloc` returns NULL.",
            marks=Decimal("2"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("`new` allocates on the stack; `malloc` allocates on the heap", False),
                _o("`new` calls constructors and is type-safe; `malloc` only allocates raw bytes", True),
                _o("`malloc` is faster in all cases because it skips type checking", False),
                _o("Both are identical; `new` is just a C++ alias for `malloc`", False),
            ],
        ),
    ],
)

# ── Question Bank: Alpha — AI / Machine Learning ──────────────────────────────

BANK_ALPHA_AI = BankDef(
    id=BANK_ALPHA_AI_ID,
    name="AI / Machine Learning",
    description="ML, Deep Learning, Generative AI, LLMs, RAG, and AI Agents",
    org_id=ORG_ALPHA_ID,
    admin_id=ADMIN_ALPHA_ID,
    questions=[
        QuestionDef(
            id=_qid("b", 1),
            text="What is the vanishing gradient problem in deep neural networks?",
            explanation="During backpropagation, gradients can become exponentially small in early layers (especially with sigmoid/tanh), making those layers learn very slowly or not at all.",
            marks=Decimal("2"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("Gradients grow too large and cause weight overflow", False),
                _o("Gradients become too small in early layers, slowing or stopping learning", True),
                _o("The loss function reaches a local minimum and stops updating", False),
                _o("Dropout randomly zeroes gradients during training", False),
            ],
        ),
        QuestionDef(
            id=_qid("b", 2),
            text="In the context of Large Language Models, what does 'temperature' control?",
            explanation="Temperature scales the logits before applying softmax. Higher temperature → flatter distribution → more random outputs; lower temperature → sharper distribution → more deterministic outputs.",
            marks=Decimal("1.5"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("The number of tokens generated per second", False),
                _o("The randomness / diversity of generated text", True),
                _o("The maximum context window length", False),
                _o("The learning rate during fine-tuning", False),
            ],
        ),
        QuestionDef(
            id=_qid("b", 3),
            text="Which technique does Retrieval-Augmented Generation (RAG) use to ground LLM responses?",
            explanation="RAG retrieves relevant document chunks from a vector database using semantic similarity search and injects them into the LLM prompt as context, reducing hallucination.",
            marks=Decimal("2"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("Fine-tuning the model on domain-specific data", False),
                _o("Injecting retrieved document chunks into the prompt as context", True),
                _o("Increasing the model's temperature to explore more responses", False),
                _o("Using chain-of-thought prompting without external data", False),
            ],
        ),
        QuestionDef(
            id=_qid("b", 4),
            text="What is the primary role of the 'ReAct' framework in AI agent design?",
            explanation="ReAct (Reasoning + Acting) interleaves chain-of-thought reasoning traces with action steps (tool calls), allowing the agent to observe tool results and reason about next steps iteratively.",
            marks=Decimal("2"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("It enables LLMs to learn from reinforcement feedback in real time", False),
                _o("It interleaves reasoning traces with tool-use actions in a loop", True),
                _o("It compresses prompt tokens to fit larger contexts", False),
                _o("It parallelises multiple LLM calls for speed", False),
            ],
        ),
        QuestionDef(
            id=_qid("b", 5),
            text="Which metric is most appropriate for evaluating a binary classification model with highly imbalanced classes?",
            explanation="Accuracy is misleading on imbalanced datasets. F1-score (harmonic mean of precision and recall) or AUROC better captures performance across classes.",
            marks=Decimal("1.5"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("Raw accuracy", False),
                _o("F1-score or AUROC", True),
                _o("Mean squared error", False),
                _o("Perplexity", False),
            ],
        ),
        QuestionDef(
            id=_qid("b", 6),
            text="What differentiates a vector database from a traditional relational database?",
            explanation="Vector databases store high-dimensional embeddings and support approximate nearest-neighbour (ANN) search by semantic similarity, whereas relational databases use exact predicate matching on structured data.",
            marks=Decimal("2"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("Vector databases store data in rows and columns like RDBMS", False),
                _o("Vector databases support ANN similarity search on high-dimensional embeddings", True),
                _o("Vector databases guarantee ACID transactions by default", False),
                _o("Vector databases replace SQL with graph query languages", False),
            ],
        ),
    ],
)

# ── Question Bank: Beta — Data Engineering & Databases ────────────────────────

BANK_BETA_DE = BankDef(
    id=BANK_BETA_DE_ID,
    name="Data Engineering & Databases",
    description="SQL, PostgreSQL, database design, normalization, and data pipeline concepts",
    org_id=ORG_BETA_ID,
    admin_id=ADMIN_BETA_ID,
    questions=[
        QuestionDef(
            id=_qid("c", 1),
            text="What does the SQL keyword `EXPLAIN ANALYZE` do in PostgreSQL?",
            explanation="`EXPLAIN ANALYZE` executes the query and returns the actual execution plan with real run times and row counts, unlike plain `EXPLAIN` which only estimates.",
            marks=Decimal("2"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("Displays table schema definitions", False),
                _o("Executes the query and shows the actual query plan with run times", True),
                _o("Optimizes indexes automatically based on query patterns", False),
                _o("Returns only the estimated query plan without executing", False),
            ],
        ),
        QuestionDef(
            id=_qid("c", 2),
            text="Which normal form eliminates transitive functional dependencies?",
            explanation="Third Normal Form (3NF) requires that every non-key attribute depends only on the primary key, not on other non-key attributes (transitive dependency).",
            marks=Decimal("1.5"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("First Normal Form (1NF)", False),
                _o("Second Normal Form (2NF)", False),
                _o("Third Normal Form (3NF)", True),
                _o("Boyce-Codd Normal Form (BCNF)", False),
            ],
        ),
        QuestionDef(
            id=_qid("c", 3),
            text="In Apache Kafka, what is the role of a 'consumer group'?",
            explanation="A consumer group allows multiple consumers to share the work of reading from a topic's partitions — each partition is assigned to exactly one consumer in the group, enabling parallel processing.",
            marks=Decimal("2"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("It stores messages durably on disk across brokers", False),
                _o("It distributes topic partitions across consumers for parallel processing", True),
                _o("It compresses messages before transmission to producers", False),
                _o("It manages schema versions for Avro/Protobuf messages", False),
            ],
        ),
        QuestionDef(
            id=_qid("c", 4),
            text="What is the key difference between OLTP and OLAP systems?",
            explanation="OLTP (Online Transaction Processing) handles high-volume, short transactional queries optimised for writes. OLAP (Online Analytical Processing) handles complex aggregation queries on large datasets optimised for reads.",
            marks=Decimal("1.5"),
            negative_marks=Decimal("0.25"),
            options=[
                _o("OLTP is used for batch analytics; OLAP for real-time transactions", False),
                _o("OLTP is optimised for short write-heavy transactions; OLAP for complex read-heavy analytics", True),
                _o("Both are identical; the terms are interchangeable", False),
                _o("OLAP stores data in row format; OLTP in columnar format", False),
            ],
        ),
        QuestionDef(
            id=_qid("c", 5),
            text="Which SQL clause is used to filter results AFTER a GROUP BY aggregation?",
            explanation="`HAVING` filters groups after aggregation, whereas `WHERE` filters rows before aggregation. You must use `HAVING` to filter on aggregate functions like COUNT, SUM, AVG.",
            marks=Decimal("1"),
            negative_marks=Decimal("0.25"),
            options=[
                _o("WHERE", False),
                _o("HAVING", True),
                _o("FILTER", False),
                _o("ON", False),
            ],
        ),
        QuestionDef(
            id=_qid("c", 6),
            text="What is a 'surrogate key' in database design?",
            explanation="A surrogate key is a system-generated identifier (e.g., auto-increment integer or UUID) with no business meaning, used as a primary key instead of a natural key.",
            marks=Decimal("1.5"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("A composite key made from two or more natural attributes", False),
                _o("A system-generated primary key with no business meaning", True),
                _o("A foreign key that references another table's primary key", False),
                _o("An indexed column used to speed up WHERE clause queries", False),
            ],
        ),
    ],
)

# ── Question Bank: Beta — System Design & Cloud ───────────────────────────────

BANK_BETA_SD = BankDef(
    id=BANK_BETA_SD_ID,
    name="System Design & Cloud",
    description="Distributed systems, REST APIs, Docker, Kubernetes, microservices, and cloud architecture",
    org_id=ORG_BETA_ID,
    admin_id=ADMIN_BETA_ID,
    questions=[
        QuestionDef(
            id=_qid("d", 1),
            text="In the CAP theorem, which two properties can a distributed system guarantee simultaneously during a network partition?",
            explanation="The CAP theorem states you can only guarantee two of Consistency, Availability, and Partition Tolerance. During a partition you must choose between Consistency (CP) or Availability (AP).",
            marks=Decimal("2"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("Consistency + Availability", False),
                _o("Consistency + Partition Tolerance OR Availability + Partition Tolerance", True),
                _o("All three simultaneously", False),
                _o("Partition Tolerance alone is sufficient", False),
            ],
        ),
        QuestionDef(
            id=_qid("d", 2),
            text="What does a Docker `ENTRYPOINT` instruction do, and how does it differ from `CMD`?",
            explanation="`ENTRYPOINT` sets the executable that always runs; `CMD` provides default arguments that can be overridden at `docker run`. If both are set, `CMD` arguments are passed to `ENTRYPOINT`.",
            marks=Decimal("2"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("ENTRYPOINT sets the base image; CMD sets environment variables", False),
                _o("ENTRYPOINT sets the fixed executable; CMD provides overridable default arguments", True),
                _o("Both are identical; ENTRYPOINT is the newer syntax for CMD", False),
                _o("ENTRYPOINT runs only during image build; CMD runs at container start", False),
            ],
        ),
        QuestionDef(
            id=_qid("d", 3),
            text="Which HTTP status code should a REST API return when a resource is successfully created?",
            explanation="201 Created is the correct status for a successful POST that creates a new resource. The response should include a Location header pointing to the new resource.",
            marks=Decimal("1"),
            negative_marks=Decimal("0.25"),
            options=[
                _o("200 OK", False),
                _o("201 Created", True),
                _o("204 No Content", False),
                _o("202 Accepted", False),
            ],
        ),
        QuestionDef(
            id=_qid("d", 4),
            text="What is the purpose of a message queue (e.g., RabbitMQ) in a microservices architecture?",
            explanation="Message queues decouple producers from consumers, enabling asynchronous communication, load levelling, and resilience — producers don't wait for consumers and the system tolerates downstream slowness.",
            marks=Decimal("2"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("To provide a shared SQL database between services", False),
                _o("To decouple services via asynchronous message passing, improving resilience", True),
                _o("To replace REST APIs with binary protocols", False),
                _o("To store service configuration in a centralised registry", False),
            ],
        ),
        QuestionDef(
            id=_qid("d", 5),
            text="What is horizontal scaling (scale-out) and when is it preferred over vertical scaling?",
            explanation="Horizontal scaling adds more machine instances; vertical scaling upgrades a single machine. Horizontal is preferred for stateless services requiring high availability, as vertical has hardware limits.",
            marks=Decimal("1.5"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("Adding more CPU/RAM to a single machine; preferred for stateful databases", False),
                _o("Adding more machine instances; preferred for stateless services needing high availability", True),
                _o("Both terms mean the same thing in cloud environments", False),
                _o("Horizontal scaling applies only to storage, not compute", False),
            ],
        ),
        QuestionDef(
            id=_qid("d", 6),
            text="In Kubernetes, what is the role of a `Service` object?",
            explanation="A Kubernetes Service provides a stable DNS name and virtual IP for a set of Pods selected by labels, enabling load-balanced access regardless of Pod restarts or IP changes.",
            marks=Decimal("2"),
            negative_marks=Decimal("0.5"),
            options=[
                _o("It defines the container image and resource limits for a Pod", False),
                _o("It provides a stable network endpoint and load balancing for a set of Pods", True),
                _o("It stores secrets and configuration for deployments", False),
                _o("It schedules Pods onto specific nodes based on affinity rules", False),
            ],
        ),
    ],
)

ALL_BANKS = [BANK_ALPHA_DSA, BANK_ALPHA_AI, BANK_BETA_DE, BANK_BETA_SD]

# ── Quiz definitions ──────────────────────────────────────────────────────────

QUIZZES = [
    QuizDef(
        id=QUIZ_ALPHA_1_ID,
        title="Alpha: DSA & Python Fundamentals",
        description="Covers time complexity, data structures, Python internals, and C++ memory management.",
        duration_minutes=30,
        org_id=ORG_ALPHA_ID,
        admin_id=ADMIN_ALPHA_ID,
        question_ids=[
            _qid("a", 1), _qid("a", 2), _qid("a", 3),
            _qid("a", 4), _qid("a", 5), _qid("a", 6),
        ],
    ),
    QuizDef(
        id=QUIZ_ALPHA_2_ID,
        title="Alpha: AI & ML Concepts",
        description="Tests understanding of deep learning, LLMs, RAG, vector databases, and AI agents.",
        duration_minutes=30,
        org_id=ORG_ALPHA_ID,
        admin_id=ADMIN_ALPHA_ID,
        question_ids=[
            _qid("b", 1), _qid("b", 2), _qid("b", 3),
            _qid("b", 4), _qid("b", 5), _qid("b", 6),
        ],
    ),
    QuizDef(
        id=QUIZ_BETA_1_ID,
        title="Beta: Databases & Data Engineering",
        description="SQL, normalization, Kafka, OLAP vs OLTP, and database design patterns.",
        duration_minutes=25,
        org_id=ORG_BETA_ID,
        admin_id=ADMIN_BETA_ID,
        question_ids=[
            _qid("c", 1), _qid("c", 2), _qid("c", 3),
            _qid("c", 4), _qid("c", 5), _qid("c", 6),
        ],
    ),
    QuizDef(
        id=QUIZ_BETA_2_ID,
        title="Beta: System Design & Cloud Architecture",
        description="CAP theorem, Docker, REST APIs, Kubernetes, microservices, and scaling strategies.",
        duration_minutes=25,
        org_id=ORG_BETA_ID,
        admin_id=ADMIN_BETA_ID,
        question_ids=[
            _qid("d", 1), _qid("d", 2), _qid("d", 3),
            _qid("d", 4), _qid("d", 5), _qid("d", 6),
        ],
    ),
]


# ── Seed helpers ──────────────────────────────────────────────────────────────

async def _exists(session: AsyncSession, model, pk: uuid.UUID) -> bool:
    return await session.get(model, pk) is not None


async def _email_exists(session: AsyncSession, email: str) -> bool:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none() is not None


async def _slug_exists(session: AsyncSession, slug: str) -> bool:
    result = await session.execute(select(Organization).where(Organization.slug == slug))
    return result.scalar_one_or_none() is not None


# ── Seed functions ────────────────────────────────────────────────────────────

async def seed_organizations(session: AsyncSession) -> dict[str, int]:
    created = skipped = 0
    for org in ORGS:
        if await _slug_exists(session, org.slug):
            skipped += 1
            continue
        session.add(Organization(id=org.id, name=org.name, slug=org.slug, is_active=True))
        created += 1
    await session.flush()
    return {"created": created, "skipped": skipped}


async def seed_admins(session: AsyncSession) -> dict[str, int]:
    created = skipped = 0
    for a in ADMINS:
        if await _email_exists(session, a.email):
            skipped += 1
            continue
        session.add(User(
            id=a.id,
            email=a.email,
            username=a.username,
            hashed_password=hash_password(a.password),
            full_name=a.full_name,
            role=UserRole.ADMIN,
            is_active=True,
            organization_id=a.org_id,
        ))
        created += 1
    await session.flush()
    return {"created": created, "skipped": skipped}


async def seed_students(session: AsyncSession) -> dict[str, int]:
    created = skipped = 0
    for i, (email, username, full_name) in enumerate(STUDENTS, start=1):
        if await _email_exists(session, email):
            skipped += 1
            continue
        session.add(User(
            id=_student_id(i),
            email=email,
            username=username,
            hashed_password=hash_password("Student@Pass123!"),
            full_name=full_name,
            role=UserRole.STUDENT,
            is_active=True,
            organization_id=None,
        ))
        created += 1
    await session.flush()
    return {"created": created, "skipped": skipped}


async def seed_question_banks(session: AsyncSession) -> dict[str, int]:
    created = skipped = 0
    for bank in ALL_BANKS:
        if await _exists(session, QuestionBank, bank.id):
            skipped += 1
            continue
        session.add(QuestionBank(
            id=bank.id,
            name=bank.name,
            description=bank.description,
            creator_id=bank.admin_id,
            organization_id=bank.org_id,
        ))
        created += 1
    await session.flush()
    return {"created": created, "skipped": skipped}


async def seed_questions(session: AsyncSession) -> dict[str, int]:
    created = skipped = 0
    for bank in ALL_BANKS:
        for q in bank.questions:
            if await _exists(session, Question, q.id):
                skipped += 1
                continue
            session.add(Question(
                id=q.id,
                question_bank_id=bank.id,
                text=q.text,
                explanation=q.explanation,
                marks=q.marks,
                negative_marks=q.negative_marks,
            ))
            await session.flush()
            for pos, opt in enumerate(q.options):
                session.add(QuestionOption(
                    question_id=q.id,
                    text=opt.text,
                    is_correct=opt.is_correct,
                    position=pos,
                ))
            created += 1
    await session.flush()
    return {"created": created, "skipped": skipped}


async def seed_quizzes(session: AsyncSession) -> dict[str, int]:
    created = skipped = 0
    for qz in QUIZZES:
        if await _exists(session, Quiz, qz.id):
            skipped += 1
            continue
        session.add(Quiz(
            id=qz.id,
            creator_id=qz.admin_id,
            organization_id=qz.org_id,
            title=qz.title,
            description=qz.description,
            duration_minutes=qz.duration_minutes,
            is_published=True,
            shuffle_questions=False,
            shuffle_options=False,
            max_attempts=3,
            proctoring_enabled=False,
        ))
        await session.flush()

        for pos, qid in enumerate(qz.question_ids):
            result = await session.execute(
                select(QuizQuestion).where(
                    QuizQuestion.quiz_id == qz.id,
                    QuizQuestion.question_id == qid,
                )
            )
            if result.scalar_one_or_none() is None:
                session.add(QuizQuestion(
                    quiz_id=qz.id,
                    question_id=qid,
                    position=pos,
                    marks_override=None,
                ))
        created += 1
    await session.flush()
    return {"created": created, "skipped": skipped}


# ── Verification ──────────────────────────────────────────────────────────────

async def verify(session: AsyncSession) -> None:
    from sqlalchemy import func

    async def count(model) -> int:
        result = await session.execute(select(func.count()).select_from(model))
        return result.scalar_one()

    orgs    = await count(Organization)
    users   = await count(User)
    banks   = await count(QuestionBank)
    qs      = await count(Question)
    opts    = await count(QuestionOption)
    quizzes = await count(Quiz)
    qq      = await count(QuizQuestion)

    admins   = (await session.execute(
        select(func.count()).select_from(User).where(User.role == UserRole.ADMIN)
    )).scalar_one()
    students = (await session.execute(
        select(func.count()).select_from(User).where(User.role == UserRole.STUDENT)
    )).scalar_one()

    print("\n-- Verification ----------------------------------------")
    print(f"  Organizations : {orgs}  (expected >= 2)")
    print(f"  Admins        : {admins}  (expected >= 2)")
    print(f"  Students      : {students}  (expected >= 20)")
    print(f"  Question Banks: {banks}  (expected >= 4)")
    print(f"  Questions     : {qs}  (expected >= 20)")
    print(f"  Options       : {opts}  (expected = questions x4 = {qs * 4})")
    print(f"  Quizzes       : {quizzes}  (expected >= 4)")
    print(f"  Quiz-Questions : {qq}  (expected >= {len(QUIZZES) * 5}")
    print("-------------------------------------------------------\n")

    failures = []
    if orgs < 2:     failures.append(f"Expected >= 2 organizations, got {orgs}")
    if admins < 2:   failures.append(f"Expected >= 2 admins, got {admins}")
    if students < 20: failures.append(f"Expected >= 20 students, got {students}")
    if banks < 4:    failures.append(f"Expected >= 4 question banks, got {banks}")
    if qs < 20:      failures.append(f"Expected >= 20 questions, got {qs}")
    if opts != qs * 4: failures.append(f"Expected {qs * 4} options (4 per question), got {opts}")
    if quizzes < 4:  failures.append(f"Expected >= 4 quizzes, got {quizzes}")
    if qq < len(QUIZZES) * 5: failures.append(f"Expected >= {len(QUIZZES) * 5} quiz-questions, got {qq}")

    if failures:
        print("VERIFICATION FAILED:")
        for f in failures:
            print(f"  FAIL: {f}")
    else:
        print("  PASS: All verification checks passed.")


# ── Main ──────────────────────────────────────────────────────────────────────

async def run_seed(verify_only: bool = False) -> None:
    async with AsyncSessionLocal() as session:
        if verify_only:
            await verify(session)
            return

        print("Seeding Quiz Platform...\n")

        steps = [
            ("Organizations",   seed_organizations),
            ("Admins",          seed_admins),
            ("Students",        seed_students),
            ("Question Banks",  seed_question_banks),
            ("Questions",       seed_questions),
            ("Quizzes",         seed_quizzes),
        ]

        for label, fn in steps:
            result = await fn(session)
            print(f"  {label:<20} created={result['created']}  skipped={result['skipped']}")

        await session.commit()
        print("\n  PASS: Seed complete — database committed.\n")

        await verify(session)

    print("Credentials summary:")
    print("  Org Alpha admin : admin@alpha.dev  / Alpha@Admin123!")
    print("  Org Beta  admin : admin@beta.dev   / Beta@Admin123!")
    print("  Students        : student01@example.com … student20@example.com / Student@Pass123!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed the Quiz Platform database")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify counts; do not insert anything",
    )
    args = parser.parse_args()
    asyncio.run(run_seed(verify_only=args.verify))
