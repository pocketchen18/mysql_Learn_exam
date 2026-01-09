export type QuestionType = 'choice' | 'fill' | 'true_false' | 'short_answer';

export type Question = {
  id: number;
  type: QuestionType;
  category: string;
  question: string;
  options: string[];
  answer: string;
  explanation: string;
};

export interface FilterItem {
  id: string;
  name: string;
}

export interface Filters {
  categories: FilterItem[];
  types: FilterItem[];
}

export interface Stats {
  total_answered: number;
  correct_answered: number;
  wrong_count: number;
  cat_stats: Record<string, { total: number; correct: number }>;
}
