export type UserRole = "admin" | "student";

export interface UserInfo {
  id: string;
  email: string;
  name: string;
  role: UserRole;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserInfo;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  role: UserRole;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface LogoutRequest {
  refresh_token: string;
}

export interface ApiErrorResponse {
  detail: string;
}

export interface QuestionBank {
  id: string;
  name: string;
  description: string | null;
  creator_id: string;
  created_at: string;
  updated_at: string;
}

export interface QuestionBankCreateRequest {
  name: string;
  description?: string | null;
}

export interface QuestionBankUpdateRequest {
  name?: string;
  description?: string | null;
}

export interface QuestionOption {
  id: string;
  text: string;
  is_correct: boolean;
  position: number;
}

/** Raw shape returned by the question endpoints (mirrors QuestionResponse). */
export interface QuestionRecord {
  id: string;
  question_bank_id: string;
  text: string;
  explanation: string | null;
  marks: number;
  negative_marks: number;
  options: QuestionOption[];
  created_at: string;
  updated_at: string;
}

/**
 * Normalized question shape used across the admin UI (and intended for reuse
 * by the future Quiz Builder), joined with its parent bank's name.
 */
export interface Question {
  id: string;
  text: string;
  explanation: string | null;
  questionBankId: string;
  questionBankName: string;
  marks: number;
  negativeMarks: number;
  options: QuestionOption[];
  createdAt: string;
}

export interface OptionInput {
  text: string;
  is_correct: boolean;
}

export interface QuestionCreateRequest {
  text: string;
  explanation?: string | null;
  marks: number;
  negative_marks: number;
  options: OptionInput[];
}

export interface QuestionUpdateRequest {
  text?: string;
  explanation?: string | null;
  marks?: number;
  negative_marks?: number;
  options?: OptionInput[];
}

export interface Quiz {
  id: string;
  creator_id: string;
  title: string;
  description: string | null;
  duration_minutes: number;
  start_time: string | null;
  end_time: string | null;
  is_published: boolean;
  shuffle_questions: boolean;
  shuffle_options: boolean;
  max_attempts: number;
  proctoring_enabled: boolean;
  max_tab_switches: number | null;
  created_at: string;
  updated_at: string;
}

export interface QuizCreateRequest {
  title: string;
  description?: string | null;
  duration_minutes: number;
  start_time?: string | null;
  end_time?: string | null;
  shuffle_questions?: boolean;
  shuffle_options?: boolean;
  max_attempts?: number;
  proctoring_enabled?: boolean;
  max_tab_switches?: number | null;
}

export interface QuizUpdateRequest {
  title?: string;
  description?: string | null;
  duration_minutes?: number;
  start_time?: string | null;
  end_time?: string | null;
  shuffle_questions?: boolean;
  shuffle_options?: boolean;
  max_attempts?: number;
  proctoring_enabled?: boolean;
  max_tab_switches?: number | null;
}

export interface QuizQuestion {
  quiz_id: string;
  question_id: string;
  position: number;
  marks_override: number | null;
  question: QuestionRecord;
}

export interface AddQuestionToQuizRequest {
  question_id: string;
  position: number;
  marks_override?: number | null;
}

/** Slim quiz shape returned by GET /quizzes/available — strips admin-only fields. */
export interface QuizAvailable {
  id: string;
  title: string;
  description: string | null;
  duration_minutes: number;
  start_time: string | null;
  end_time: string | null;
  max_attempts: number;
  proctoring_enabled: boolean;
}

export interface StartAttemptRequest {
  quiz_id: string;
}

export interface AttemptOptionRecord {
  id: string;
  option_text_snapshot: string;
  position: number;
}

export interface AttemptQuestionRecord {
  id: string;
  question_text_snapshot: string;
  position: number;
  marks: number;
  negative_marks: number;
  options: AttemptOptionRecord[];
  selected_option_id: string | null;
}

export interface AttemptResponse {
  id: string;
  quiz_id: string;
  student_id: string;
  attempt_number: number;
  status: string;
  started_at: string;
  time_limit_minutes: number;
  questions: AttemptQuestionRecord[];
}

export interface StudentAnalytics {
  student_id: string;
  total_attempts: number;
  submitted_count: number;
  timed_out_count: number;
  abandoned_count: number;
  in_progress_count: number;
  average_score: number | null;
  best_score: number | null;
  average_percentage: number | null;
  best_percentage: number | null;
}

export interface AttemptHistoryItem {
  attempt_id: string;
  quiz_id: string;
  quiz_title: string;
  attempt_number: number;
  status: string;
  score: number | null;
  started_at: string;
  submitted_at: string | null;
}

export interface StudentHistoryResponse {
  items: AttemptHistoryItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface StudentHistoryParams {
  limit?: number;
  offset?: number;
  quizId?: string;
}

export interface RecentActivityItem {
  attempt_id: string;
  student_id: string;
  student_username: string;
  quiz_id: string;
  quiz_title: string;
  status: string;
  score: number | null;
  started_at: string;
  submitted_at: string | null;
}

export interface AttemptAdminItem {
  id: string;
  quiz_id: string;
  student_id: string;
  attempt_number: number;
  status: string;
  started_at: string;
  submitted_at: string | null;
  score: number | null;
  tab_switch_count: number;
  ip_address: string | null;
  created_at: string;
}

export interface AdminAttemptFilters {
  status?: string;
  quizId?: string;
  studentId?: string;
  limit?: number;
  offset?: number;
}

export interface TabSwitchLog {
  id: string;
  switched_at: string;
}

export interface AttemptAuditResponse {
  attempt: AttemptAdminItem;
  tab_switch_logs: TabSwitchLog[];
  proctoring_events: ProctoringEventResponse[];
}

export interface AdminDashboard {
  total_users: number;
  total_students: number;
  total_admins: number;
  active_users: number;
  total_quizzes: number;
  published_quizzes: number;
  total_attempts: number;
  in_progress_attempts: number;
  submitted_attempts: number;
  timed_out_attempts: number;
  abandoned_attempts: number;
  total_tab_switches: number;
  average_tab_switches_per_attempt: number | null;
  total_proctoring_events: number;
  recent_attempts: RecentActivityItem[];
}

export interface SaveAnswerRequest {
  attempt_question_id: string;
  selected_option_id: string | null;
}

export interface AnswerResponse {
  id: string;
  attempt_question_id: string;
  selected_option_id: string | null;
  answered_at: string | null;
}

export interface AttemptOptionResultRecord {
  id: string;
  option_text_snapshot: string;
  is_correct_snapshot: boolean;
  position: number;
}

export interface AttemptQuestionResultRecord {
  id: string;
  question_text_snapshot: string;
  position: number;
  marks: number;
  negative_marks: number;
  options: AttemptOptionResultRecord[];
  selected_option_id: string | null;
  is_correct: boolean | null;
  marks_awarded: number | null;
}

export interface AttemptResultResponse {
  id: string;
  quiz_id: string;
  student_id: string;
  attempt_number: number;
  status: string;
  started_at: string;
  submitted_at: string | null;
  score: number;
  correct_count: number;
  incorrect_count: number;
  unanswered_count: number;
  percentage: number;
  questions: AttemptQuestionResultRecord[];
}

export interface TabSwitchResponse {
  attempt_id: string;
  tab_switch_count: number;
  max_tab_switches: number | null;
  limit_exceeded: boolean;
  attempt_status: string;
}

export type StudentProctoringEventType = "window_blur" | "copy_paste" | "fullscreen_exit";

export interface ProctoringEventRequest {
  event_type: StudentProctoringEventType;
  metadata?: Record<string, unknown> | null;
}

export interface ProctoringEventResponse {
  id: string;
  attempt_id: string;
  event_type: string;
  occurred_at: string;
  metadata: Record<string, unknown> | null;
}

export interface BulkImportRowError {
  row: number;
  field: string | null;
  message: string;
}

export interface BulkImportResponse {
  imported: number;
  failed: number;
  errors: BulkImportRowError[];
}
