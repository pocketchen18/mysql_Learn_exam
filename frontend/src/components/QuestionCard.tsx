import React, { useState } from 'react';
import type { Question } from '../types';
import { CheckCircle2, XCircle, Info } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface QuestionCardProps {
  question: Question;
  onNext: () => void;
  onPrevious: () => void;
  onAnswer?: (isCorrect: boolean) => void;
  currentIndex: number;
  total: number;
}

export const QuestionCard = ({
  question,
  onNext,
  onPrevious,
  onAnswer,
  currentIndex,
  total,
}: QuestionCardProps) => {
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [fillAnswer, setFillAnswer] = useState('');
  const [showResult, setShowResult] = useState(false);

  const isCorrect = () => {
    if (!question) return false;
    if (question.type === 'choice') {
      const optionIndex = question.options.indexOf(selectedOption || '');
      const answerMap: Record<string, number> = { A: 0, B: 1, C: 2, D: 3, E: 4 };
      const correctAnswerIndex = answerMap[question.answer];
      return correctAnswerIndex !== undefined && correctAnswerIndex === optionIndex;
    }
    if (question.type === 'true_false') {
      return selectedOption === question.answer;
    }
    if (question.type === 'fill') {
      return fillAnswer.trim() === question.answer.trim();
    }
    return true;
  };

  const handleSubmit = () => {
    setShowResult(true);
    if (onAnswer) {
      onAnswer(isCorrect());
    }
  };

  const handleNext = () => {
    setSelectedOption(null);
    setFillAnswer('');
    setShowResult(false);
    onNext();
  };

  const renderQuestionContent = () => {
    switch (question.type) {
      case 'choice':
        return (
          <div className="grid gap-3">
            {question.options.map((option, idx) => {
              const letter = String.fromCharCode(65 + idx);
              const isSelected = selectedOption === option;
              const isAnswer = question.answer === letter;

              return (
                <button
                  key={idx}
                  disabled={showResult}
                  onClick={() => setSelectedOption(option)}
                  className={cn(
                    "flex items-center p-4 rounded-lg border-2 transition-all text-left",
                    !showResult && "hover:border-blue-400 hover:bg-blue-50 border-gray-100",
                    !showResult && isSelected && "border-blue-500 bg-blue-50",
                    showResult && isAnswer && "border-green-500 bg-green-50 text-green-700",
                    showResult && isSelected && !isAnswer && "border-red-500 bg-red-50 text-red-700",
                    showResult && !isAnswer && !isSelected && "border-gray-100 opacity-50"
                  )}
                >
                  <span className="w-8 h-8 flex items-center justify-center rounded-full bg-white border border-gray-200 mr-3 shrink-0 font-bold">
                    {letter}
                  </span>
                  <span>{option}</span>
                </button>
              );
            })}
          </div>
        );
      case 'true_false':
        return (
          <div className="grid grid-cols-2 gap-4">
            {['√', '×'].map((option) => {
              const isSelected = selectedOption === option;
              const isAnswer = question.answer === option;
              return (
                <button
                  key={option}
                  disabled={showResult}
                  onClick={() => setSelectedOption(option)}
                  className={cn(
                    "flex items-center justify-center p-6 rounded-lg border-2 transition-all text-2xl font-bold",
                    !showResult && "hover:border-blue-400 hover:bg-blue-50 border-gray-100",
                    !showResult && isSelected && "border-blue-500 bg-blue-50",
                    showResult && isAnswer && "border-green-500 bg-green-50 text-green-700",
                    showResult && isSelected && !isAnswer && "border-red-500 bg-red-50 text-red-700",
                    showResult && !isAnswer && !isSelected && "border-gray-100 opacity-50"
                  )}
                >
                  {option}
                </button>
              );
            })}
          </div>
        );
      case 'fill':
        return (
          <div className="space-y-4">
            <input
              type="text"
              value={fillAnswer}
              disabled={showResult}
              onChange={(e) => setFillAnswer(e.target.value)}
              placeholder="请输入答案..."
              className={cn(
                "w-full p-4 rounded-lg border-2 transition-all outline-none",
                !showResult ? "border-gray-200 focus:border-blue-500" : (
                  isCorrect() ? "border-green-500 bg-green-50" : "border-red-500 bg-red-50"
                )
              )}
            />
          </div>
        );
      case 'short_answer':
        return (
          <div className="space-y-4">
            <textarea
              value={fillAnswer}
              disabled={showResult}
              onChange={(e) => setFillAnswer(e.target.value)}
              placeholder="请输入你的回答..."
              rows={4}
              className={cn(
                "w-full p-4 rounded-lg border-2 transition-all outline-none resize-none",
                !showResult ? "border-gray-200 focus:border-blue-500" : "border-gray-100 bg-gray-50"
              )}
            />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="w-full max-w-2xl bg-white rounded-xl shadow-lg p-6 space-y-6">
      <div className="flex justify-between items-center text-sm text-gray-500 border-b pb-4">
        <div className="flex gap-2">
          <span className="font-medium px-3 py-1 bg-blue-50 text-blue-600 rounded-full">
            {question.category}
          </span>
          <span className="font-medium px-3 py-1 bg-slate-100 text-slate-600 rounded-full">
            {question.type === 'choice' ? '选择题' : 
             question.type === 'fill' ? '填空题' : 
             question.type === 'true_false' ? '判断题' : 
             question.type === 'short_answer' ? '简答题' : question.type}
          </span>
        </div>
        <span>{currentIndex + 1} / {total}</span>
      </div>

      <div className="text-lg font-medium text-gray-800 leading-relaxed whitespace-pre-wrap">
        {question.question}
      </div>

      {renderQuestionContent()}

      {showResult && (
        <div className={cn(
          "p-4 rounded-lg flex items-start space-x-3",
          question.type === 'short_answer' ? "bg-blue-50 text-blue-800" : (
            isCorrect() ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"
          )
        )}>
          {question.type === 'short_answer' ? (
            <Info className="w-6 h-6 shrink-0" />
          ) : (
            isCorrect() ? (
              <CheckCircle2 className="w-6 h-6 shrink-0" />
            ) : (
              <XCircle className="w-6 h-6 shrink-0" />
            )
          )}
          <div className="flex-1">
            <div className="font-bold">
              {question.type === 'short_answer' ? '参考答案：' : (isCorrect() ? '回答正确！' : '回答错误')}
            </div>
            <div className="mt-1 whitespace-pre-wrap">{question.type === 'short_answer' ? question.answer : `正确答案：${question.answer}`}</div>
            {question.explanation && (
              <div className="mt-2 text-sm opacity-90 flex items-start gap-1 pt-2 border-t border-current/10">
                <Info className="w-4 h-4 shrink-0 mt-0.5" />
                <span>解析：{question.explanation}</span>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="flex justify-between pt-6 border-t">
        <button
          onClick={onPrevious}
          disabled={currentIndex === 0}
          className="px-6 py-2 rounded-lg font-medium text-gray-600 hover:bg-gray-100 disabled:opacity-50 transition-colors"
        >
          上一题
        </button>
        {!showResult ? (
          <button
            onClick={handleSubmit}
            disabled={
              (question.type === 'choice' || question.type === 'true_false') ? !selectedOption : !fillAnswer
            }
            className="px-8 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {question.type === 'short_answer' ? '显示答案' : '提交'}
          </button>
        ) : (
          <button
            onClick={handleNext}
            className="px-8 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            {currentIndex === total - 1 ? '重新开始' : '下一题'}
          </button>
        )}
      </div>
    </div>
  );
};
