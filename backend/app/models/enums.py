import enum


class UserRole(str, enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"


class AttemptStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    TIMED_OUT = "timed_out"
    ABANDONED = "abandoned"


class ProctoringEventType(str, enum.Enum):
    TAB_SWITCH = "tab_switch"
    WINDOW_BLUR = "window_blur"
    COPY_PASTE = "copy_paste"
    FULLSCREEN_EXIT = "fullscreen_exit"
    FACE_NOT_DETECTED = "face_not_detected"
    MULTIPLE_FACES = "multiple_faces"
    PHONE_DETECTED = "phone_detected"
    AUDIO_DETECTED = "audio_detected"
