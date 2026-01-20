import { useState, useEffect } from 'react'
import axios from 'axios'
import type { Question, Filters, Stats, PracticeMode } from './types'
import { QuestionCard } from './components/QuestionCard'
import { QuestionManager } from './components/QuestionManager'
import { BookOpen, ChevronRight, Layout, RefreshCw, ListFilter, Tag, Trophy, AlertCircle, BarChart3, PieChart, Settings, CheckCircle2, Circle, Sparkles } from 'lucide-react'
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const API_BASE = '/api'

type TabType = 'type' | 'wrong' | 'stats' | 'admin';

function App() {
  const [filters, setFilters] = useState<Filters>({ categories: [], types: [] })
  const [selectedFilter, setSelectedFilter] = useState<{ id: string, type: 'category' | 'type' | 'wrong' } | null>(null)
  const [questions, setQuestions] = useState<Question[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<TabType>('type')
  const [stats, setStats] = useState<Stats | null>(null)
  const [streak, setStreak] = useState(0)
  const [streakMessage, setStreakMessage] = useState<string | null>(null)
  const [practiceMode, setPracticeMode] = useState<PracticeMode>('undone')

  useEffect(() => {
    fetchFilters()
    fetchStats()

    // Heartbeat mechanism to close backend when frontend is closed
    const sendHeartbeat = () => {
      axios.post(`${API_BASE}/heartbeat`).catch(() => {});
    };
    sendHeartbeat(); // Initial heartbeat
    const heartbeatInterval = setInterval(sendHeartbeat, 5000); // Every 5 seconds

    return () => clearInterval(heartbeatInterval);
  }, [])

  const fetchFilters = async () => {
    try {
      const res = await axios.get(`${API_BASE}/filters`)
      setFilters(res.data)
    } catch (err) {
      console.error('Failed to fetch filters', err)
    }
  }

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API_BASE}/stats`)
      setStats(res.data)
    } catch (err) {
      console.error('Failed to fetch stats', err)
    }
  }

  const startQuiz = async (filterId: string, filterType: 'category' | 'type' | 'wrong' | 'mode') => {
    setLoading(true)
    setSelectedFilter({ id: filterId, type: filterType === 'mode' ? 'type' : filterType })
    setStreak(0)
    setStreakMessage(null)
    try {
      let url = ''
      if (filterType === 'category') url = `${API_BASE}/questions?category=${filterId}&mode=${practiceMode}`
      else if (filterType === 'type') url = `${API_BASE}/questions?type=${filterId}&mode=${practiceMode}`
      else if (filterType === 'wrong') url = `${API_BASE}/wrong-questions`
      else if (filterType === 'mode') url = `${API_BASE}/questions?mode=${filterId}`
      
      const res = await axios.get(url)
      // For "recommend" mode, the backend already sorted/mixed them, 
      // but if the user wants random, we can still shuffle unless it's recommend mode
      let data = res.data;
      if (filterId !== 'recommend' && filterType !== 'mode') {
        data = [...res.data].sort(() => Math.random() - 0.5);
      }
      setQuestions(data)
      setCurrentIndex(0)
    } catch (err) {
      console.error('Failed to fetch questions', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAnswer = async (questionId: number, isCorrect: boolean) => {
    if (isCorrect) {
      const newStreak = streak + 1
      setStreak(newStreak)
      
      // 设置连对鼓励语
      if (newStreak >= 2) {
        let msg = ""
        if (newStreak === 2) msg = "手感不错！连对 2 题了！"
        else if (newStreak === 3) msg = "太棒了！连对 3 题，继续保持！"
        else if (newStreak === 5) msg = "火力全开！竟然连对了 5 题！"
        else if (newStreak === 10) msg = "超神了！10 连对！你是 MySQL 大神吗？"
        else if (newStreak % 5 === 0) msg = `不可思议！已经连对 ${newStreak} 题了！`
        else msg = `连对 ${newStreak} 题，势如破竹！`
        setStreakMessage(msg)
      } else {
        setStreakMessage(null)
      }
    } else {
      setStreak(0)
      setStreakMessage(null)
    }

    try {
      await axios.post(`${API_BASE}/report`, { question_id: questionId, is_correct: isCorrect })
      fetchStats() // Refresh stats after each answer
    } catch (err) {
      console.error('Failed to report answer', err)
    }
  }

  const handleRemoveWrong = async (questionId: number) => {
    try {
      await axios.delete(`${API_BASE}/wrong-questions/${questionId}`)
      // If we are currently viewing the wrong questions list, remove it from the local state too
      if (selectedFilter?.type === 'wrong') {
        const newQuestions = questions.filter(q => q.id !== questionId)
        setQuestions(newQuestions)
        
        if (newQuestions.length === 0) {
          reset() // Go back to home if no more questions
        } else if (currentIndex >= newQuestions.length) {
          setCurrentIndex(newQuestions.length - 1)
        }
      }
      fetchStats()
    } catch (err) {
      console.error('Failed to remove wrong question', err)
    }
  }

  const reset = () => {
    setSelectedFilter(null)
    setQuestions([])
    setCurrentIndex(0)
    setStreak(0)
    setStreakMessage(null)
    fetchStats() // Refresh stats when returning to main page
  }

  const renderPracticeModes = () => (
    <div className="mb-10 space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="w-5 h-5 text-blue-600" />
        <h3 className="text-lg font-bold text-gray-900">第一步：选择练习范围</h3>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          onClick={() => setPracticeMode('undone')}
          className={cn(
            "flex items-center justify-between p-4 rounded-2xl border transition-all",
            practiceMode === 'undone' 
              ? "bg-blue-50 border-blue-200 text-blue-700 shadow-sm" 
              : "bg-white border-gray-100 text-gray-600 hover:border-blue-200"
          )}
        >
          <div className="flex items-center gap-3">
            <div className={cn("p-2 rounded-lg", practiceMode === 'undone' ? "bg-blue-600 text-white" : "bg-gray-100")}>
              <BookOpen className="w-5 h-5" />
            </div>
            <div className="text-left">
              <div className="font-bold">未做题目</div>
              <div className="text-xs opacity-70">只练习还没做过的题</div>
            </div>
          </div>
          {practiceMode === 'undone' ? <CheckCircle2 className="w-5 h-5" /> : <Circle className="w-5 h-5 opacity-20" />}
        </button>

        <button
          onClick={() => setPracticeMode('done')}
          className={cn(
            "flex items-center justify-between p-4 rounded-2xl border transition-all",
            practiceMode === 'done' 
              ? "bg-blue-50 border-blue-200 text-blue-700 shadow-sm" 
              : "bg-white border-gray-100 text-gray-600 hover:border-blue-200"
          )}
        >
          <div className="flex items-center gap-3">
            <div className={cn("p-2 rounded-lg", practiceMode === 'done' ? "bg-blue-600 text-white" : "bg-gray-100")}>
              <RefreshCw className="w-5 h-5" />
            </div>
            <div className="text-left">
              <div className="font-bold">已做题目</div>
              <div className="text-xs opacity-70">复习已经完成的题目</div>
            </div>
          </div>
          {practiceMode === 'done' ? <CheckCircle2 className="w-5 h-5" /> : <Circle className="w-5 h-5 opacity-20" />}
        </button>

        <button
          onClick={() => setPracticeMode('recommend')}
          className={cn(
            "flex items-center justify-between p-4 rounded-2xl border transition-all",
            practiceMode === 'recommend' 
              ? "bg-blue-50 border-blue-200 text-blue-700 shadow-sm" 
              : "bg-white border-gray-100 text-gray-600 hover:border-blue-200"
          )}
        >
          <div className="flex items-center gap-3">
            <div className={cn("p-2 rounded-lg", practiceMode === 'recommend' ? "bg-blue-600 text-white" : "bg-gray-100")}>
              <Sparkles className="w-5 h-5" />
            </div>
            <div className="text-left">
              <div className="font-bold">智能推荐</div>
              <div className="text-xs opacity-70">优先错题与未做题</div>
            </div>
          </div>
          {practiceMode === 'recommend' ? <CheckCircle2 className="w-5 h-5" /> : <Circle className="w-5 h-5 opacity-20" />}
        </button>
      </div>

      <div className="pt-6 border-t border-gray-100 animate-in fade-in slide-in-from-top-2 duration-500">
        <div className="flex items-center gap-2 mb-4">
          <ListFilter className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-bold text-gray-900">第二步：选择题目类型</h3>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {filters.types.map((item) => (
            <button
              key={item.id}
              onClick={() => startQuiz(item.id, 'type')}
              className="group bg-white p-4 rounded-xl shadow-sm border border-gray-100 hover:border-blue-500 hover:shadow-md transition-all text-left flex flex-col gap-3"
            >
              <div className="p-2 bg-blue-50 text-blue-600 rounded-lg group-hover:bg-blue-600 group-hover:text-white transition-colors w-fit">
                <Tag className="w-4 h-4" />
              </div>
              <div className="flex items-center justify-between w-full">
                <span className="font-semibold text-gray-700">{item.name}</span>
                <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-blue-500 transition-colors" />
              </div>
            </button>
          ))}
          <button
            onClick={() => startQuiz(practiceMode, 'mode')}
            className="group bg-blue-600 p-4 rounded-xl shadow-lg shadow-blue-100 border border-blue-600 hover:bg-blue-700 transition-all text-left flex flex-col gap-3 text-white"
          >
            <div className="p-2 bg-white/20 rounded-lg w-fit">
              <Layout className="w-4 h-4" />
            </div>
            <div className="flex items-center justify-between w-full">
              <span className="font-bold">全部类型</span>
              <ChevronRight className="w-4 h-4 text-white/70" />
            </div>
          </button>
        </div>
      </div>
    </div>
  )

  const renderStats = () => {
    if (!stats) return null;
    const accuracy = stats.total_answered > 0 
      ? Math.round((stats.correct_answered / stats.total_answered) * 100) 
      : 0;

    return (
      <div className="space-y-8 animate-in fade-in duration-500">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center space-x-4">
            <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
              <BookOpen className="w-6 h-6" />
            </div>
            <div>
              <div className="text-sm text-gray-500">累计答题</div>
              <div className="text-2xl font-bold text-gray-900">{stats.total_answered}</div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center space-x-4">
            <div className="p-3 bg-green-50 text-green-600 rounded-xl">
              <Trophy className="w-6 h-6" />
            </div>
            <div>
              <div className="text-sm text-gray-500">正确率</div>
              <div className="text-2xl font-bold text-gray-900">{accuracy}%</div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center space-x-4">
            <div className="p-3 bg-red-50 text-red-600 rounded-xl">
              <AlertCircle className="w-6 h-6" />
            </div>
            <div>
              <div className="text-sm text-gray-500">错题数</div>
              <div className="text-2xl font-bold text-gray-900">{stats.wrong_count}</div>
            </div>
          </div>
        </div>

        <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
          <div className="flex items-center gap-2 mb-6">
            <BarChart3 className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-bold text-gray-900">知识点统计</h3>
          </div>
          <div className="space-y-4">
            {Object.entries(stats.cat_stats || {}).map(([cat, data]) => {
              const total = data.total || 0;
              const correct = data.correct || 0;
              const catAccuracy = total > 0 ? Math.round((correct / total) * 100) : 0;
              return (
                <div key={cat} className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium text-gray-700">{cat}</span>
                    <span className="text-gray-500">{correct}/{total} ({catAccuracy}%)</span>
                  </div>
                  <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-500 transition-all duration-1000" 
                      style={{ width: `${catAccuracy}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  const renderWrongQuestions = () => (
    <div className="text-center py-12 bg-white rounded-2xl shadow-sm border border-gray-100 w-full animate-in fade-in duration-500">
      <div className="p-4 bg-red-50 text-red-600 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
        <AlertCircle className="w-8 h-8" />
      </div>
      <h2 className="text-xl font-bold text-gray-900 mb-2">错题本</h2>
      <p className="text-gray-500 mb-8">在这里复习你之前答错的题目，查漏补缺</p>
      
      {stats && stats.wrong_count > 0 ? (
        <button 
          onClick={() => startQuiz('wrong', 'wrong')}
          className="px-8 py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 transition-all shadow-lg shadow-blue-100 flex items-center gap-2 mx-auto"
        >
          <RefreshCw className="w-5 h-5" />
          开始复习 ({stats.wrong_count} 题)
        </button>
      ) : (
        <div className="text-gray-400 italic">暂无错题，继续保持！</div>
      )}
    </div>
  )

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <header className="text-center mb-12">
          <div className="inline-flex items-center justify-center p-3 bg-blue-600 rounded-2xl mb-4 shadow-lg shadow-blue-200">
            <Layout className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">MySQL 刷题系统</h1>
          <p className="text-gray-500 mt-2">基于题库_整合.json 提供的试题进行练习</p>
        </header>

        {!selectedFilter ? (
          <div className="space-y-8">
            {/* Tabs */}
            <div className="flex bg-white p-1.5 rounded-2xl shadow-sm border border-gray-100 mb-8 w-fit mx-auto">
              <button 
                onClick={() => setActiveTab('type')}
                className={cn(
                  "px-6 py-2.5 rounded-xl font-bold transition-all flex items-center gap-2",
                  activeTab === 'type' ? "bg-blue-600 text-white shadow-lg shadow-blue-100" : "text-gray-500 hover:text-gray-700"
                )}
              >
                <Layout className="w-4 h-4" />
                题库分类
              </button>
              <button 
                onClick={() => setActiveTab('wrong')}
                className={cn(
                  "px-6 py-2.5 rounded-xl font-bold transition-all flex items-center gap-2",
                  activeTab === 'wrong' ? "bg-blue-600 text-white shadow-lg shadow-blue-100" : "text-gray-500 hover:text-gray-700"
                )}
              >
                <AlertCircle className="w-4 h-4" />
                错题本
              </button>
              <button 
                onClick={() => setActiveTab('stats')}
                className={cn(
                  "px-6 py-2.5 rounded-xl font-bold transition-all flex items-center gap-2",
                  activeTab === 'stats' ? "bg-blue-600 text-white shadow-lg shadow-blue-100" : "text-gray-500 hover:text-gray-700"
                )}
              >
                <PieChart className="w-4 h-4" />
                学习统计
              </button>
              <button 
                onClick={() => setActiveTab('admin')}
                className={cn(
                  "px-6 py-2.5 rounded-xl font-bold transition-all flex items-center gap-2",
                  activeTab === 'admin' ? "bg-blue-600 text-white shadow-lg shadow-blue-100" : "text-gray-500 hover:text-gray-700"
                )}
              >
                <Settings className="w-4 h-4" />
                题库管理
              </button>
            </div>

            {/* Content Area */}
            {activeTab === 'type' && (
              <div className="space-y-8">
                {renderPracticeModes()}
              </div>
            )}
            {activeTab === 'wrong' && renderWrongQuestions()}
            {activeTab === 'stats' && renderStats()}
            {activeTab === 'admin' && <QuestionManager />}
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-8 animate-in fade-in duration-500">
            <div className="w-full flex justify-between items-center max-w-2xl">
              <button
                onClick={reset}
                className="text-sm font-medium text-gray-500 hover:text-blue-600 flex items-center gap-1 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                返回主页
              </button>
              <div className="text-sm font-medium text-gray-400">
                正在练习: <span className="text-gray-600">
                  {selectedFilter.type === 'wrong' ? '错题复习' : 
                   `${(filters?.types || []).find(t => t.id === selectedFilter.id)?.name || 
                      (filters?.categories || []).find(c => c.id === selectedFilter.id)?.name || 
                      '全部题目'} (${
                     practiceMode === 'all' ? '全部' : 
                     practiceMode === 'done' ? '已做' : 
                     practiceMode === 'undone' ? '未做' : '智能推荐'
                   })`}
                </span>
              </div>
            </div>

            {loading ? (
              <div className="animate-pulse space-y-4 w-full max-w-2xl">
                <div className="h-64 bg-white rounded-xl shadow-sm"></div>
              </div>
            ) : questions.length > 0 ? (
              <QuestionCard
                question={questions[currentIndex]}
                currentIndex={currentIndex}
                total={questions.length}
                onAnswer={(isCorrect) => handleAnswer(questions[currentIndex].id, isCorrect)}
                streakMessage={streakMessage}
                onNext={() => {
                  setStreakMessage(null) // Clear message for next question
                  if (currentIndex < questions.length - 1) {
                    setCurrentIndex(prev => prev + 1)
                  } else {
                    reset()
                  }
                }}
                onPrevious={() => {
                  if (currentIndex > 0) {
                    setCurrentIndex(prev => prev - 1)
                  }
                }}
                onRemoveWrong={handleRemoveWrong}
                isWrongMode={selectedFilter?.type === 'wrong'}
              />
            ) : (
              <div className="text-center py-12 bg-white rounded-2xl shadow-sm border border-gray-100 w-full max-w-2xl">
                <div className="p-4 bg-orange-50 text-orange-600 rounded-full w-12 h-12 mx-auto mb-4 flex items-center justify-center">
                  <BookOpen className="w-6 h-6" />
                </div>
                <p className="text-gray-500">暂无题目</p>
                <button onClick={reset} className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                  返回首页
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App
