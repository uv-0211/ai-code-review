export type Severity = 'critical' | 'warning' | 'suggestion';

export interface Issue {
  title: string;
  severity: Severity;
  file: string;
  explanation: string;
  fix: string;
}

export interface ReviewResponse {
  issues: Issue[];
  diff_length: number;
}
