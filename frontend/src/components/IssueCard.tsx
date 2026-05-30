import type { Issue, Severity } from '../types';

const SEVERITY_STYLES: Record<
  Severity,
  { badge: string; border: string; label: string }
> = {
  critical: {
    badge: 'bg-red-100 text-red-700',
    border: 'border-red-200',
    label: 'Critical',
  },
  warning: {
    badge: 'bg-amber-100 text-amber-700',
    border: 'border-amber-200',
    label: 'Warning',
  },
  suggestion: {
    badge: 'bg-blue-100 text-blue-700',
    border: 'border-blue-200',
    label: 'Suggestion',
  },
};

interface Props {
  issue: Issue;
  index: number;
}

export function IssueCard({ issue, index }: Props) {
  const styles = SEVERITY_STYLES[issue.severity] ?? SEVERITY_STYLES.suggestion;

  return (
    <div
      className={`rounded-xl border ${styles.border} bg-white p-5 shadow-sm`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-400">
            #{index + 1}
          </span>
          <h3 className="font-semibold text-gray-900">{issue.title}</h3>
        </div>
        <span
          className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold ${styles.badge}`}
        >
          {styles.label}
        </span>
      </div>

      <p className="mt-1 text-xs text-gray-400 font-mono">{issue.file}</p>

      <div className="mt-3 space-y-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">
            Issue
          </p>
          <p className="mt-0.5 text-sm text-gray-700">{issue.explanation}</p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">
            Fix
          </p>
          <p className="mt-0.5 text-sm text-gray-700">{issue.fix}</p>
        </div>
      </div>
    </div>
  );
}
