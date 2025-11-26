/**
 * API client for the Debate Platform backend
 * Base URL: http://localhost:8000
 */

const API_BASE_URL = 'http://localhost:8080';

// Types matching backend models
export interface TopicCreate {
  question: string;
  created_by: string;
}

export interface TopicResponse {
  topic_id: number;
  question: string;
  created_by: string;
  created_at?: string;
}

export interface TopicListItem {
  id: number;
  question: string;
  pro_count: number;
  con_count: number;
  created_by?: string;
  created_at?: string;
  pro_avg_validity?: number | null;
  con_avg_validity?: number | null;
  controversy_level?: string | null;
}

export interface ArgumentCreate {
  side: 'pro' | 'con';
  title: string;
  content: string;
  sources?: string;
  author: string;
}

export interface ArgumentResponse {
  id: number;
  topic_id: number;
  side: 'pro' | 'con';
  title: string;
  content: string;
  sources?: string;
  author: string;
  created_at: string;
  validity_score?: number | null;
  validity_reasoning?: string | null;
  validity_checked_at?: string | null;
  key_urls?: string[] | null;
  votes?: number | null;
}

export interface TopicDetailResponse {
  id: number;
  question: string;
  pro_arguments: ArgumentResponse[];
  con_arguments: ArgumentResponse[];
  overall_summary?: string | null;
  consensus_view?: string | null;
  timeline_view?: Array<{ period: string; description: string }> | null;
}

export interface ArgumentCreateResponse {
  argument_id: number;
}

export interface SummaryResponse {
  overall_summary: string;
  consensus_view: string;
  timeline_view: Array<{ period: string; description: string }>;
}

export interface ValidityVerdictResponse {
  validity_score: number;
  reasoning: string;
  key_urls: string[];
  source_count: number;
}

export interface ArgumentMatch {
  pro_id: number;
  con_id: number;
  reason?: string | null;
}

// Error handling helper
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    // Extract the detail object - it might be nested or flat
    const detail = errorData.detail || errorData;
    const errorMessage = typeof detail === 'string' ? detail : (detail.message || detail.error || `HTTP error! status: ${response.status}`);
    const error: any = new Error(errorMessage);
    error.status = response.status;
    error.response = { data: { detail: detail }, status: response.status };
    error.detail = detail; // Store the full detail object for easy access
    throw error;
  }
  return response.json();
}

// API Functions

/**
 * Create a new debate topic
 * POST /api/topics
 */
export async function createTopic(data: TopicCreate): Promise<TopicResponse> {
  const response = await fetch(`${API_BASE_URL}/api/topics`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  return handleResponse<TopicResponse>(response);
}

/**
 * Get all topics with pro/con argument counts
 * GET /api/topics
 */
export async function getTopics(): Promise<TopicListItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/topics`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return handleResponse<TopicListItem[]>(response);
}

/**
 * Get a single topic with all its arguments and analysis
 * GET /api/topics/{topic_id}
 */
export async function getTopic(topicId: number): Promise<TopicDetailResponse> {
  const response = await fetch(`${API_BASE_URL}/api/topics/${topicId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return handleResponse<TopicDetailResponse>(response);
}

/**
 * Add an argument to a topic
 * POST /api/topics/{topic_id}/arguments
 */
export async function createArgument(
  topicId: number,
  data: ArgumentCreate
): Promise<ArgumentCreateResponse> {
  const response = await fetch(`${API_BASE_URL}/api/topics/${topicId}/arguments`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  return handleResponse<ArgumentCreateResponse>(response);
}

/**
 * Get arguments for a topic
 * GET /api/topics/{topic_id}/arguments?side=pro|con|both
 */
export async function getArguments(
  topicId: number,
  side?: 'pro' | 'con' | 'both'
): Promise<ArgumentResponse[]> {
  const queryParam = side ? `?side=${side}` : '';
  const response = await fetch(`${API_BASE_URL}/api/topics/${topicId}/arguments${queryParam}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return handleResponse<ArgumentResponse[]>(response);
}

/**
 * Generate Claude analysis for a topic
 * POST /api/topics/{topic_id}/generate-summary
 */
export async function generateSummary(topicId: number): Promise<SummaryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/topics/${topicId}/generate-summary`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return handleResponse<SummaryResponse>(response);
}

/**
 * Verify a single argument's validity
 * POST /api/arguments/{argument_id}/verify
 */
export async function verifyArgument(argumentId: number): Promise<ValidityVerdictResponse> {
  const response = await fetch(`${API_BASE_URL}/api/arguments/${argumentId}/verify`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return handleResponse<ValidityVerdictResponse>(response);
}

/**
 * Verify all arguments for a topic
 * POST /api/topics/{topic_id}/verify-all
 */
export async function verifyAllArguments(topicId: number): Promise<{
  total_arguments: number;
  verified: number;
  failed: number;
  results: Array<{
    argument_id: number;
    title: string;
    validity_score?: number;
    status: string;
    error?: string;
  }>;
}> {
  const response = await fetch(`${API_BASE_URL}/api/topics/${topicId}/verify-all`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return handleResponse(response);
}

/**
 * Get arguments sorted by validity score
 * GET /api/topics/{topic_id}/arguments/verified?side=pro|con
 */
export async function getArgumentsSortedByValidity(
  topicId: number,
  side?: 'pro' | 'con'
): Promise<ArgumentResponse[]> {
  const queryParam = side ? `?side=${side}` : '';
  const response = await fetch(`${API_BASE_URL}/api/topics/${topicId}/arguments/verified${queryParam}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return handleResponse<ArgumentResponse[]>(response);
}

/**
 * Get argument matches (pro/con pairs that rebut each other)
 * POST /api/topics/{topic_id}/match-arguments
 */
export async function getArgumentMatches(topicId: number): Promise<ArgumentMatch[]> {
  const response = await fetch(`${API_BASE_URL}/api/topics/${topicId}/match-arguments`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return handleResponse<ArgumentMatch[]>(response);
}

/**
 * Upvote an argument
 * POST /api/arguments/{argument_id}/upvote
 */
export async function upvoteArgument(argumentId: number): Promise<{ argument_id: number; votes: number }> {
  const response = await fetch(`${API_BASE_URL}/api/arguments/${argumentId}/upvote`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return handleResponse<{ argument_id: number; votes: number }>(response);
}

/**
 * Downvote an argument
 * POST /api/arguments/{argument_id}/downvote
 */
export async function downvoteArgument(argumentId: number): Promise<{ argument_id: number; votes: number }> {
  const response = await fetch(`${API_BASE_URL}/api/arguments/${argumentId}/downvote`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return handleResponse<{ argument_id: number; votes: number }>(response);
}

