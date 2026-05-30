import { useState } from 'react';
import { reviewPR } from './api';
import { IssueCard } from './components/IssueCard';
import type { Issue } from './types';

type Status = 'idle' | 'loading' | 'done' | 'error';

export default function App() {
  const [prUrl, setPrUrl] = useState('');
  const [issues, setIssues] = useState<Issue[]>([]);
  const [status, setStatus] = useState<Status>('idle');
  const [errorMsg, setErrorMsg] = useState('');
  const [diffLength, setDiffLength] = useState(0);

  async function handleReview() {
    setStatus('loading');
    setIssues([]);
    setErrorMsg('');

    try {
      const data = await reviewPR(prUrl);
      setIssues(data.issues);
      setDiffLength(data.diff_length);
      setStatus('done');
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : 'Unknown error');
      setStatus('error');
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-12">
      <div className="mx-auto max-w-2xl space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Code Reviewer</h1>
          <p className="mt-1 text-sm text-gray-500">Paste link to GitHub PR</p>
        </div>

        <div className="flex gap-2">
          <input
            className="flex-1 rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm shadow-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
            placeholder="https://github.com/owner/repo/pull/123"
            value={prUrl}
            onChange={(e) => setPrUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleReview()}
            disabled={status === 'loading'}
          />
          <button
            className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            onClick={handleReview}
            disabled={status === 'loading' || !prUrl.trim()}
          >
            {status === 'loading' ? 'Analyzing...' : 'Review'}
          </button>
        </div>

        {status === 'error' && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {errorMsg}
          </div>
        )}

        {status === 'done' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-gray-700">
                {issues.length === 0
                  ? 'No issues found!'
                  : `Issues found: ${issues.length}`}
              </h2>
              <span className="text-xs text-gray-400">
                {diffLength.toLocaleString()} symbols in diff
              </span>
            </div>

            <div className="space-y-3">
              {issues.map((issue, i) => (
                <IssueCard key={i} issue={issue} index={i} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
