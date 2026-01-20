import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Search, Plus, Edit2, Trash2, Upload, X, Check, AlertCircle, FileJson } from 'lucide-react';
import type { Question, QuestionType } from '../types';

const API_BASE = '/api';

export const QuestionManager = () => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [categories, setCategories] = useState<string[]>([]);
  const [editingQuestion, setEditingQuestion] = useState<Partial<Question> | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [importData, setImportData] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  const fetchQuestions = useCallback(async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API_BASE}/questions`);
      if (res.data) {
        setQuestions(res.data);
        // Extract unique categories
        const cats = Array.from(new Set(res.data.map((q: Question) => q.category))).filter(Boolean) as string[];
        setCategories(cats.sort());
      }
    } catch (err) {
      console.error('Failed to fetch questions', err);
      showMsg('error', '加载题目失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchQuestions();
  }, [fetchQuestions]);

  const showMsg = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  const handleSave = async () => {
    if (!editingQuestion) return;
    try {
      if (editingQuestion.id) {
        await axios.put(`${API_BASE}/questions/${editingQuestion.id}`, editingQuestion);
        showMsg('success', '题目更新成功');
      } else {
        await axios.post(`${API_BASE}/questions`, editingQuestion);
        showMsg('success', '题目添加成功');
      }
      setEditingQuestion(null);
      fetchQuestions();
    } catch (err) {
      console.error('Failed to save question', err);
      showMsg('error', '保存失败');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这道题吗？')) return;
    try {
      await axios.delete(`${API_BASE}/questions/${id}`);
      showMsg('success', '题目已删除');
      fetchQuestions();
    } catch (err) {
      console.error('Failed to delete question', err);
      showMsg('error', '删除失败');
    }
  };

  const handleImport = async () => {
    try {
      const parsed = JSON.parse(importData);
      const questionsToImport = Array.isArray(parsed) ? parsed : [parsed];
      await axios.post(`${API_BASE}/questions/import`, { questions: questionsToImport });
      showMsg('success', `成功导入 ${questionsToImport.length} 道题目`);
      setIsImporting(false);
      setImportData('');
      fetchQuestions();
    } catch (err) {
      console.error('Failed to import', err);
      showMsg('error', '导入失败，请检查 JSON 格式');
    }
  };

  const filteredQuestions = questions.filter(q => {
    const matchesSearch = q.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         q.category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || q.category === selectedCategory;
    const matchesType = selectedType === 'all' || q.type === selectedType;
    return matchesSearch && matchesCategory && matchesType;
  });

  if (loading) return <div className="text-center py-12">加载中...</div>;

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {message && (
        <div className={`fixed top-4 right-4 p-4 rounded-lg shadow-lg flex items-center gap-2 z-50 ${
          message.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
        }`}>
          {message.type === 'success' ? <Check size={20} /> : <AlertCircle size={20} />}
          {message.text}
        </div>
      )}

      <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
        <div className="flex flex-col md:flex-row gap-3 w-full md:w-auto">
          <div className="relative w-full md:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="搜索题目..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-sm"
            />
          </div>
          
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-sm"
          >
            <option value="all">所有分类</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>

          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-3 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-sm"
          >
            <option value="all">所有类型</option>
            <option value="choice">选择题</option>
            <option value="true_false">判断题</option>
            <option value="fill">填空题</option>
            <option value="short_answer">简答题</option>
          </select>
        </div>
        <div className="flex gap-2 w-full md:w-auto">
          <button
            onClick={() => setIsImporting(true)}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-slate-100 text-slate-700 rounded-xl hover:bg-slate-200 transition-colors font-medium"
          >
            <Upload size={18} />
            导入
          </button>
          <button
            onClick={() => setEditingQuestion({ type: 'choice', category: '', question: '', options: ['', '', '', ''], answer: '', explanation: '' })}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors font-medium"
          >
            <Plus size={18} />
            添加题目
          </button>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead className="bg-slate-50 border-b border-gray-100">
              <tr>
                <th className="p-4 font-semibold text-gray-600">ID</th>
                <th className="p-4 font-semibold text-gray-600">题目</th>
                <th className="p-4 font-semibold text-gray-600">分类</th>
                <th className="p-4 font-semibold text-gray-600">类型</th>
                <th className="p-4 font-semibold text-gray-600">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {filteredQuestions.map((q) => (
                <tr key={q.id} className="hover:bg-slate-50/50 transition-colors">
                  <td className="p-4 text-gray-500 text-sm">{q.id}</td>
                  <td className="p-4">
                    <div className="text-gray-800 line-clamp-2 max-w-md">{q.question}</div>
                  </td>
                  <td className="p-4">
                    <span className="px-2 py-1 bg-blue-50 text-blue-600 rounded-lg text-xs font-medium">
                      {q.category}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="px-2 py-1 bg-slate-100 text-slate-600 rounded-lg text-xs font-medium">
                      {q.type === 'choice' ? '选择' : q.type === 'fill' ? '填空' : q.type === 'true_false' ? '判断' : '简答'}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="flex gap-2">
                      <button 
                        onClick={() => setEditingQuestion(q)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      >
                        <Edit2 size={18} />
                      </button>
                      <button 
                        onClick={() => handleDelete(q.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filteredQuestions.length === 0 && (
          <div className="p-12 text-center text-gray-400 italic">
            没有找到相关题目
          </div>
        )}
      </div>

      {/* Edit/Add Modal */}
      {editingQuestion && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="sticky top-0 bg-white border-b p-6 flex justify-between items-center z-10">
              <h3 className="text-xl font-bold text-gray-900">
                {editingQuestion.id ? '编辑题目' : '添加题目'}
              </h3>
              <button onClick={() => setEditingQuestion(null)} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-sm font-medium text-gray-700">题目类型</label>
                  <select 
                    value={editingQuestion.type}
                    onChange={(e) => setEditingQuestion({...editingQuestion, type: e.target.value as QuestionType})}
                    className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  >
                    <option value="choice">选择题</option>
                    <option value="true_false">判断题</option>
                    <option value="fill">填空题</option>
                    <option value="short_answer">简答题</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium text-gray-700">题目分类</label>
                  <input 
                    type="text"
                    value={editingQuestion.category}
                    onChange={(e) => setEditingQuestion({...editingQuestion, category: e.target.value})}
                    placeholder="例如：基础知识"
                    className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium text-gray-700">题目内容</label>
                <textarea 
                  value={editingQuestion.question}
                  onChange={(e) => setEditingQuestion({...editingQuestion, question: e.target.value})}
                  rows={3}
                  className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                />
              </div>

              {editingQuestion.type === 'choice' && (
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <label className="text-sm font-medium text-gray-700">选项 (A-Z)</label>
                    <button
                      type="button"
                      onClick={() => {
                        const newOpts = [...(editingQuestion.options || []), ''];
                        setEditingQuestion({...editingQuestion, options: newOpts});
                      }}
                      className="text-xs flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
                    >
                      <Plus size={14} />
                      添加选项
                    </button>
                  </div>
                  {editingQuestion.options?.map((opt, idx) => (
                    <div key={idx} className="flex gap-2 items-center">
                      <span className="w-6 font-bold text-gray-400">{String.fromCharCode(65 + idx)}</span>
                      <input 
                        type="text"
                        value={opt}
                        onChange={(e) => {
                          const newOpts = [...(editingQuestion.options || [])];
                          newOpts[idx] = e.target.value;
                          setEditingQuestion({...editingQuestion, options: newOpts});
                        }}
                        className="flex-1 p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                      {(editingQuestion.options?.length || 0) > 2 && (
                        <button
                          type="button"
                          onClick={() => {
                            const newOpts = (editingQuestion.options || []).filter((_, i) => i !== idx);
                            setEditingQuestion({...editingQuestion, options: newOpts});
                          }}
                          className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                          title="删除选项"
                        >
                          <Trash2 size={16} />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}

              <div className="space-y-1">
                <label className="text-sm font-medium text-gray-700">正确答案</label>
                {editingQuestion.type === 'true_false' ? (
                  <select 
                    value={editingQuestion.answer}
                    onChange={(e) => setEditingQuestion({...editingQuestion, answer: e.target.value})}
                    className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  >
                    <option value="">请选择</option>
                    <option value="√">√ (正确)</option>
                    <option value="×">× (错误)</option>
                  </select>
                ) : (
                  <input 
                    type="text"
                    value={editingQuestion.answer}
                    onChange={(e) => setEditingQuestion({...editingQuestion, answer: e.target.value})}
                    placeholder={editingQuestion.type === 'choice' ? '例如：A' : '输入答案内容'}
                    className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                )}
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium text-gray-700">解析</label>
                <textarea 
                  value={editingQuestion.explanation}
                  onChange={(e) => setEditingQuestion({...editingQuestion, explanation: e.target.value})}
                  rows={2}
                  className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                />
              </div>
            </div>
            <div className="p-6 border-t flex gap-3 justify-end bg-slate-50">
              <button 
                onClick={() => setEditingQuestion(null)}
                className="px-6 py-2 border rounded-xl hover:bg-white transition-colors"
              >
                取消
              </button>
              <button 
                onClick={handleSave}
                className="px-6 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors font-medium shadow-lg shadow-blue-100"
              >
                保存题目
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Import Modal */}
      {isImporting && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-xl shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="p-6 border-b flex justify-between items-center">
              <div className="flex items-center gap-2">
                <FileJson className="text-blue-600" />
                <h3 className="text-xl font-bold text-gray-900">批量导入题目</h3>
              </div>
              <button onClick={() => setIsImporting(false)} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-sm text-gray-500">
                请粘贴 JSON 格式的题目数据。数据应为对象数组或单个题目对象。
              </p>
              <textarea 
                value={importData}
                onChange={(e) => setImportData(e.target.value)}
                rows={10}
                placeholder={`[
  {
    "type": "choice",
    "category": "MySQL",
    "question": "什么是 SQL？",
    "options": ["A", "B", "C", "D"],
    "answer": "A",
    "explanation": "..."
  }
]`}
                className="w-full p-3 font-mono text-xs border rounded-xl focus:ring-2 focus:ring-blue-500 outline-none bg-slate-50"
              />
            </div>
            <div className="p-6 border-t flex gap-3 justify-end bg-slate-50">
              <button 
                onClick={() => setIsImporting(false)}
                className="px-6 py-2 border rounded-xl hover:bg-white transition-colors"
              >
                取消
              </button>
              <button 
                onClick={handleImport}
                disabled={!importData.trim()}
                className="px-6 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors font-medium disabled:opacity-50"
              >
                开始导入
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
