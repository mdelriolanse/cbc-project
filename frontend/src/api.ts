/**
 * API client for the Debate Platform backend
 * Base URL: http://localhost:8000
 */

const API_BASE_URL = 'http://localhost:8000';

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

export interface ArgumentMatch {
  pro_id: number;
  con_id: number;
  reason?: string | null;
}

// Error handling helper
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
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
 * Get argument match pairs (pro <-> con) as evaluated by Claude
 */
export async function getArgumentMatches(topicId: number): Promise<ArgumentMatch[]> {
  const response = await fetch(`${API_BASE_URL}/api/topics/${topicId}/match-arguments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  return handleResponse<ArgumentMatch[]>(response);
}

