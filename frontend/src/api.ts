import type { ReviewResponse } from './types';

const BASE_URL = 'http://localhost:8000';

export async function reviewPR(prUrl: string): Promise<ReviewResponse> {
  const response = await fetch(`${BASE_URL}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pr_url: prUrl }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail ?? 'Unknown error');
  }

  return response.json();
}
