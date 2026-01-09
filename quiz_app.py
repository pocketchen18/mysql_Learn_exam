import sys
import json
import os
import random
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QStackedWidget, QRadioButton, QButtonGroup,
                             QCheckBox, QLineEdit, QTextEdit, QScrollArea, QFrame, QComboBox, QSpinBox,
                             QMessageBox, QProgressBar, QGraphicsDropShadowEffect, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve, QRectF, pyqtProperty
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QPainter, QPen, QBrush

# --- 数据管理类 ---

class QuestionManager:
    def __init__(self, json_path):
        self.json_path = json_path
        self.all_questions = []
        self.categories = set()
        self.load_data()

    def load_data(self):
        if not os.path.exists(self.json_path):
            print(f"Error: {self.json_path} not found.")
            return

        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 兼容两种格式：1. 直接是列表; 2. 字典格式 {"by_type": {...}}
                questions_list = []
                if isinstance(data, list):
                    questions_list = data
                elif isinstance(data, dict):
                    by_type = data.get("by_type", {})
                    for q_type, questions in by_type.items():
                        if q_type == "设计题":
                            continue
                        questions_list.extend(questions)
                
                for q in questions_list:
                    question_text = q.get("question", "")
                    if not question_text or not str(question_text).strip():
                        continue
                    
                    # 验证选择题是否有选项
                    q_type = q.get("type", "")
                    if q_type in ["choice", "选择题", "单选题", "多选题"]:
                        options = q.get("options", [])
                        if not options or len(options) == 0:
                            continue
                    
                    if q.get("answer") is None:
                        q["answer"] = ""
                        
                    self.all_questions.append(q)
                    
                    # 收集分类 (兼容 cat 和 category 字段)
                    cat = q.get("cat") or q.get("category")
                    if cat:
                        self.categories.add(cat)
                            
        except Exception as e:
            print(f"Error loading JSON: {e}")
            import traceback
            traceback.print_exc()
            
        self.categories = sorted(list(self.categories))

    def get_questions(self, category=None, q_type=None, count=None, shuffle=True, question_ids=None):
        filtered = self.all_questions
        if question_ids is not None:
            q_id_set = set(question_ids)
            filtered = [q for q in filtered if q.get("id") in q_id_set]
        if category and category != "全部":
            filtered = [q for q in filtered if q.get("cat") == category]
        if q_type and q_type != "全部":
            filtered = [q for q in filtered if q.get("type") == q_type]
        if shuffle:
            random.shuffle(filtered)
        if count:
            filtered = filtered[:count]
        return filtered

class UserDataManager:
    def __init__(self, data_path):
        self.data_path = data_path
        self.data = {
            "wrong_questions": [],
            "history": [],
            "total_answered": 0,
            "correct_answered": 0,
            "cat_stats": {} # { "category_name": {"total": 0, "correct": 0} }
        }
        self.load_user_data()

    def load_user_data(self):
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    for key in self.data:
                        if key in loaded_data:
                            self.data[key] = loaded_data[key]
            except Exception as e:
                print(f"Error loading user data: {e}")

    def save_user_data(self):
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving user data: {e}")

    def add_wrong_question(self, q_id):
        if q_id not in self.data["wrong_questions"]:
            self.data["wrong_questions"].append(q_id)
            self.save_user_data()

    def remove_wrong_question(self, q_id):
        if q_id in self.data["wrong_questions"]:
            self.data["wrong_questions"].remove(q_id)
            self.save_user_data()

    def record_answer(self, category, is_correct):
        self.data["total_answered"] += 1
        if is_correct:
            self.data["correct_answered"] += 1
        
        if category:
            if category not in self.data["cat_stats"]:
                self.data["cat_stats"][category] = {"total": 0, "correct": 0}
            self.data["cat_stats"][category]["total"] += 1
            if is_correct:
                self.data["cat_stats"][category]["correct"] += 1
        self.save_user_data()

    def record_session(self, total, correct):
        self.data["history"].append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": total,
            "correct": correct
        })
        self.save_user_data()

# --- 现代化 UI 组件 ---

class CircularProgress(QWidget):
    def __init__(self, value=0, size=180):
        super().__init__()
        self._value = value
        self.setFixedSize(size, size)
        
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(800)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    @pyqtProperty(float)
    def value(self):
        return self._value
        
    @value.setter
    def value(self, val):
        self._value = val
        self.update()

    def set_value(self, val):
        self.animation.stop()
        self.animation.setStartValue(self._value)
        self.animation.setEndValue(float(val))
        self.animation.start()

    def paintEvent(self, event):
        width = self.width()
        height = self.height()
        thickness = 12
        margin = 10
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(margin, margin, width - 2*margin, height - 2*margin)
        
        # 背景圆环
        pen = QPen(QColor("#F0F2F5"))
        pen.setWidth(thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 0 * 16, 360 * 16)
        
        # 进度圆环
        # 根据正确率改变颜色
        color = "#FF5252" if self._value < 60 else "#FF9F43" if self._value < 80 else "#00D28E"
        pen_progress = QPen(QColor(color))
        pen_progress.setWidth(thickness)
        pen_progress.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_progress)
        
        span_angle = int(-(self._value / 100) * 360 * 16)
        painter.drawArc(rect, 90 * 16, span_angle)
        
        # 中间文字
        painter.setPen(QColor("#333333"))
        painter.setFont(QFont("Segoe UI Bold", 28))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{int(self._value)}%")
        
        painter.setFont(QFont("Segoe UI", 10))
        painter.setPen(QColor("#666666"))
        painter.drawText(rect.adjusted(0, 45, 0, 45), Qt.AlignmentFlag.AlignCenter, "总体掌握度")


class ModernCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                border: 1px solid #F0F0F0;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 15))
        self.setGraphicsEffect(shadow)

class NavCard(QPushButton):
    def __init__(self, title, icon_text, color="#4D7CFE"):
        super().__init__()
        self.setFixedSize(200, 120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                border-radius: 15px;
                border: 1px solid #F0F0F0;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: #F8FAFF;
                border: 1px solid {color};
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        icon_lbl = QLabel(icon_text)
        icon_lbl.setFont(QFont("Segoe UI", 24))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        
        text_lbl = QLabel(title)
        text_lbl.setFont(QFont("Segoe UI Semibold", 12))
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_lbl.setStyleSheet("color: #333333; background: transparent; border: none;")
        
        layout.addWidget(icon_lbl)
        layout.addWidget(text_lbl)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 10))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

class ModernButton(QPushButton):
    def __init__(self, text, primary=False, dark=False):
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(45)
        if dark:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #1A1C2E;
                    color: white;
                    border-radius: 12px;
                    padding: 0 30px;
                    font-size: 15px;
                    font-weight: 600;
                }
                QPushButton:hover { background-color: #2D304D; }
            """)
        elif primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #4D7CFE;
                    color: white;
                    border-radius: 10px;
                    padding: 0 25px;
                    font-size: 14px;
                    font-weight: 600;
                }
                QPushButton:hover { background-color: #3D6CFE; }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    color: #333333;
                    border-radius: 10px;
                    padding: 0 20px;
                    font-size: 14px;
                    border: 1px solid #E0E0E0;
                }
                QPushButton:hover { background-color: #F5F7FA; }
            """)

class QuizApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("数据库原理刷题宝")
        self.resize(1200, 850)
        self.setStyleSheet("QMainWindow { background-color: #F7F9FC; }")
        
        # 数据初始化
        base_path = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_path, "question_bank", "题库_整合.json")
        user_data_path = os.path.join(base_path, "user_progress.json")
        
        self.qm = QuestionManager(json_path)
        self.udm = UserDataManager(user_data_path)
        
        self.current_questions = []
        self.current_idx = 0
        self.score = 0
        self.user_answers = []
        
        self.init_ui()
        self.show_home_page()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # --- 侧边栏 ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #1A1C2E;
                border: none;
            }
        """)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(20, 40, 20, 40)
        sidebar_layout.setSpacing(10)
        
        logo_lbl = QLabel("DB Quiz")
        logo_lbl.setFont(QFont("Segoe UI Bold", 24))
        logo_lbl.setStyleSheet("color: white; margin-bottom: 30px;")
        sidebar_layout.addWidget(logo_lbl)
        
        self.nav_btns = []
        nav_items = [
            ("🏠 主页", self.show_home_page),
            ("📝 练习", lambda: self.quick_start("随机")),
            ("❗ 错题本", lambda: self.quick_start("错题")),
            ("📊 统计", self.show_home_page), # 暂时也回主页
            ("⚙ 设置", self.show_config_page)
        ]
        
        for text, slot in nav_items:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(50)
            btn.setStyleSheet("""
                QPushButton {
                    color: #A0A2B1;
                    background-color: transparent;
                    border-radius: 10px;
                    text-align: left;
                    padding-left: 15px;
                    font-size: 15px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #2D304D;
                    color: white;
                }
                QPushButton:checked {
                    background-color: #4D7CFE;
                    color: white;
                }
            """)
            btn.setCheckable(True)
            btn.clicked.connect(slot)
            sidebar_layout.addWidget(btn)
            self.nav_btns.append(btn)
            
        sidebar_layout.addStretch()
        
        self.main_layout.addWidget(self.sidebar)
        
        # --- 主内容区域 ---
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(40, 30, 40, 40)
        self.content_layout.setSpacing(25)
        
        # 顶部标题
        header = QHBoxLayout()
        self.page_title = QLabel("主页")
        self.page_title.setFont(QFont("Segoe UI Bold", 26))
        self.page_title.setStyleSheet("color: #1A1C2E;")
        header.addWidget(self.page_title)
        header.addStretch()
        
        self.content_layout.addLayout(header)
        
        # 主堆栈
        self.stack = QStackedWidget()
        self.content_layout.addWidget(self.stack)
        
        # 初始化页面
        self.page_home = QWidget()
        self.page_config = QWidget()
        self.page_quiz = QWidget()
        self.page_result = QWidget()
        
        self.stack.addWidget(self.page_home)
        self.stack.addWidget(self.page_config)
        self.stack.addWidget(self.page_quiz)
        self.stack.addWidget(self.page_result)
        
        self.setup_home_page()
        self.setup_config_page()
        
        self.main_layout.addWidget(self.content_area)

    def setup_home_page(self):
        # 如果已经有布局，先清空
        if self.page_home.layout():
            self.clear_layout(self.page_home.layout())
        else:
            QVBoxLayout(self.page_home)
            
        main_layout = self.page_home.layout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 使用滚动区域包裹内容
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(30)
        
        # --- 第一行：概览统计 ---
        stats_row = QHBoxLayout()
        stats_row.setSpacing(20)
        
        self.stat_total = self.create_stat_card("累计练习", "0", "#4D7CFE")
        self.stat_wrong = self.create_stat_card("错题本", "0", "#FF5252")
        self.stat_accuracy = self.create_stat_card("正确率", "0%", "#00D28E")
        
        stats_row.addWidget(self.stat_total)
        stats_row.addWidget(self.stat_wrong)
        stats_row.addWidget(self.stat_accuracy)
        layout.addLayout(stats_row)
        
        # --- 第二行：掌握度与章节模型 ---
        mid_row = QHBoxLayout()
        mid_row.setSpacing(25)
        
        # 总体掌握度
        self.mastery_card = ModernCard()
        self.mastery_card.setFixedSize(300, 320)
        mastery_layout = QVBoxLayout(self.mastery_card)
        mastery_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.circle_progress = CircularProgress(size=200)
        mastery_layout.addWidget(self.circle_progress)
        mid_row.addWidget(self.mastery_card)
        
        # 章节模型
        self.chapter_card = ModernCard()
        chapter_layout = QVBoxLayout(self.chapter_card)
        chapter_layout.setContentsMargins(30, 25, 30, 25)
        
        chapter_title = QLabel("🏆 章节能力模型")
        chapter_title.setFont(QFont("Segoe UI Bold", 14))
        chapter_layout.addWidget(chapter_title)
        chapter_layout.addSpacing(15)
        
        self.chapter_grid = QGridLayout()
        self.chapter_grid.setSpacing(20)
        chapter_layout.addLayout(self.chapter_grid)
        mid_row.addWidget(self.chapter_card)
        
        layout.addLayout(mid_row)
        
        # --- 第三行：快捷入口 ---
        nav_label = QLabel("快捷入口")
        nav_label.setFont(QFont("Segoe UI Bold", 16))
        layout.addWidget(nav_label)
        
        nav_row = QHBoxLayout()
        nav_row.setSpacing(20)
        
        self.card_seq = NavCard("顺序练习", "📱", "#4D7CFE")
        self.card_seq.clicked.connect(lambda: self.quick_start("顺序"))
        
        self.card_rand = NavCard("随机刷题", "🔀", "#A15CFE")
        self.card_rand.clicked.connect(lambda: self.quick_start("随机"))
        
        self.card_smart = NavCard("智能推荐", "💡", "#00D28E")
        self.card_smart.clicked.connect(lambda: self.quick_start("智能"))
        
        self.card_wrong = NavCard("错题本", "❗", "#FF5252")
        self.card_wrong.clicked.connect(lambda: self.quick_start("错题"))
        
        nav_row.addWidget(self.card_seq)
        nav_row.addWidget(self.card_rand)
        nav_row.addWidget(self.card_smart)
        nav_row.addWidget(self.card_wrong)
        layout.addLayout(nav_row)
        
        # --- 第四行：全真模拟 ---
        self.btn_mock = ModernButton("🕒 开始全真模拟考试 (20题 / 限时20分钟)", dark=True)
        self.btn_mock.setFixedHeight(65)
        self.btn_mock.clicked.connect(lambda: self.quick_start("模拟"))
        layout.addWidget(self.btn_mock)
        
        # --- 第五行：最近练习历史 ---
        history_label = QLabel("最近练习历史")
        history_label.setFont(QFont("Segoe UI Bold", 16))
        layout.addWidget(history_label)
        
        self.history_card = ModernCard()
        self.history_layout = QVBoxLayout(self.history_card)
        self.history_layout.setContentsMargins(20, 10, 20, 10)
        layout.addWidget(self.history_card)
        
        layout.addStretch()
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def create_stat_card(self, title, value, color):
        card = ModernCard()
        card.setFixedHeight(100)
        l = QVBoxLayout(card)
        l.setContentsMargins(20, 15, 20, 15)
        
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #8E92A3; font-size: 13px;")
        
        v_lbl = QLabel(value)
        v_lbl.setFont(QFont("Segoe UI Bold", 24))
        v_lbl.setStyleSheet(f"color: {color};")
        
        l.addWidget(t_lbl)
        l.addWidget(v_lbl)
        
        # 存储值标签以便更新
        if title == "累计练习": self.lbl_total_val = v_lbl
        elif title == "错题本": self.lbl_wrong_val = v_lbl
        elif title == "正确率": self.lbl_acc_val = v_lbl
            
        return card

    def setup_config_page(self):
        layout = QVBoxLayout(self.page_config)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        card = ModernCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)
        
        card_layout.addWidget(QLabel("题库设置"))
        
        # 暂时简单实现
        self.combo_cat = QComboBox()
        self.combo_cat.addItem("全部")
        self.combo_cat.addItems(self.qm.categories)
        card_layout.addWidget(QLabel("选择分类:"))
        card_layout.addWidget(self.combo_cat)
        
        self.spin_count = QSpinBox()
        self.spin_count.setRange(5, 100)
        self.spin_count.setValue(20)
        card_layout.addWidget(QLabel("题目数量:"))
        card_layout.addWidget(self.spin_count)
        
        btn_start = ModernButton("开始练习", primary=True)
        btn_start.clicked.connect(self.start_custom_quiz)
        card_layout.addWidget(btn_start)
        
        layout.addWidget(card)
        layout.addStretch()

    def refresh_home_stats(self):
        try:
            # 更新概览卡片
            total_ans = self.udm.data["total_answered"]
            wrong_count = len(self.udm.data["wrong_questions"])
            correct_count = self.udm.data["correct_answered"]
            acc = (correct_count / total_ans * 100) if total_ans > 0 else 0
            
            if hasattr(self, 'lbl_total_val'): self.lbl_total_val.setText(str(total_ans))
            if hasattr(self, 'lbl_wrong_val'): self.lbl_wrong_val.setText(str(wrong_count))
            if hasattr(self, 'lbl_acc_val'): self.lbl_acc_val.setText(f"{int(acc)}%")
            
            # 更新总体掌握度
            if hasattr(self, 'circle_progress'):
                self.circle_progress.set_value(acc)
            
            # 更新章节模型
            if hasattr(self, 'chapter_grid'):
                self.clear_layout(self.chapter_grid)
                    
                # 获取所有分类并统计
                all_cats = list(self.qm.categories)
                if not all_cats:
                    all_cats = ["基础概念", "SQL查询", "事务管理", "索引优化", "数据库设计"]
                    
                for i, cat in enumerate(all_cats[:6]): # 最多显示6个
                    row = i // 2
                    col = i % 2
                    
                    cat_box = QWidget()
                    cat_l = QVBoxLayout(cat_box)
                    cat_l.setContentsMargins(0, 0, 0, 0)
                    cat_l.setSpacing(5)
                    
                    stats = self.udm.data["cat_stats"].get(cat, {"total": 0, "correct": 0})
                    cat_acc = (stats["correct"] / stats["total" ] * 100) if stats["total"] > 0 else 0
                    
                    lbl_row = QHBoxLayout()
                    cat_name = QLabel(cat)
                    cat_name.setFont(QFont("Segoe UI", 10))
                    cat_percent = QLabel(f"{int(cat_acc)}%")
                    cat_percent.setFont(QFont("Segoe UI Semibold", 10))
                    cat_percent.setStyleSheet("color: #8E92A3;")
                    lbl_row.addWidget(cat_name)
                    lbl_row.addStretch()
                    lbl_row.addWidget(cat_percent)
                    cat_l.addLayout(lbl_row)
                    
                    pbar = QProgressBar()
                    pbar.setFixedHeight(8)
                    pbar.setValue(int(cat_acc))
                    pbar.setTextVisible(False)
                    
                    # 动态颜色
                    bar_color = "#00D28E" if cat_acc >= 80 else "#4D7CFE" if cat_acc >= 60 else "#FF9F43"
                    pbar.setStyleSheet(f"""
                        QProgressBar {{ background-color: #F0F2F5; border-radius: 4px; border: none; }}
                        QProgressBar::chunk {{ background-color: {bar_color}; border-radius: 4px; }}
                    """)
                    cat_l.addWidget(pbar)
                    
                    self.chapter_grid.addWidget(cat_box, row, col)

            # 更新最近历史
            if hasattr(self, 'history_layout'):
                self.clear_layout(self.history_layout)
                
                history = self.udm.data.get("history", [])[::-1][:5] # 最近5条
                if not history:
                    lbl = QLabel("暂无练习记录")
                    lbl.setStyleSheet("color: #8E92A3; padding: 10px;")
                    self.history_layout.addWidget(lbl)
                else:
                    for item in history:
                        h_item = QWidget()
                        h_l = QHBoxLayout(h_item)
                        h_l.setContentsMargins(10, 5, 10, 5)
                        
                        date_lbl = QLabel(item.get("date", "").split(" ")[0])
                        date_lbl.setStyleSheet("color: #8E92A3;")
                        
                        is_mock = item.get("total") == 20 # 简单判断
                        type_lbl = QLabel("模拟考试" if is_mock else "专项练习")
                        type_lbl.setStyleSheet("font-weight: bold; color: #1A1C2E;")
                        
                        score_lbl = QLabel(f"得分: {item.get('correct')}/{item.get('total')}")
                        score_lbl.setStyleSheet("color: #4D7CFE; font-weight: bold;")
                        
                        h_l.addWidget(date_lbl)
                        h_l.addSpacing(20)
                        h_l.addWidget(type_lbl)
                        h_l.addStretch()
                        h_l.addWidget(score_lbl)
                        
                        self.history_layout.addWidget(h_item)
        except Exception as e:
            print(f"Error refreshing home stats: {e}")

    def update_nav_selection(self, index):
        for i, btn in enumerate(self.nav_btns):
            btn.setChecked(i == index)

    def show_home_page(self):
        try:
            self.page_title.setText("主页")
            self.update_nav_selection(0)
            self.stack.setCurrentWidget(self.page_home)
            
            # 确保主页已经初始化
            if not self.page_home.layout() or self.page_home.layout().count() == 0:
                self.setup_home_page()
            
            self.refresh_home_stats()
        except Exception as e:
            print(f"Error showing home page: {e}")

    def show_config_page(self):
        try:
            self.page_title.setText("练习设置")
            self.update_nav_selection(4)
            self.stack.setCurrentWidget(self.page_config)
        except Exception as e:
            print(f"Error showing config page: {e}")

    def start_custom_quiz(self):
        cat = self.combo_cat.currentText()
        count = self.spin_count.value()
        self.current_questions = self.qm.get_questions(category=cat, count=count)
        if not self.current_questions:
            QMessageBox.warning(self, "警告", "未找到符合条件的题目！")
            return
        self.start_quiz_session()

    def quick_start(self, mode):
        if mode == "错题":
            self.update_nav_selection(2)
            wrong_ids = self.udm.data["wrong_questions"]
            if not wrong_ids:
                QMessageBox.information(self, "提示", "错题本空空如也！")
                self.show_home_page()
                return
            self.current_questions = self.qm.get_questions(question_ids=wrong_ids, count=20, shuffle=True)
        elif mode == "模拟":
            self.current_questions = self.qm.get_questions(count=20, shuffle=True)
        elif mode == "随机":
            self.update_nav_selection(1)
            self.current_questions = self.qm.get_questions(count=20, shuffle=True)
        elif mode == "顺序":
            self.current_questions = self.qm.get_questions(count=20, shuffle=False)
        else: # 智能推荐
            # 智能逻辑：优先推荐正确率低的分类中的题目
            stats = self.udm.data.get("cat_stats", {})
            if stats:
                # 按正确率排序，取最低的几个
                sorted_cats = sorted(stats.keys(), 
                                   key=lambda c: (stats[c]["correct"]/stats[c]["total"]) if stats[c]["total"] > 0 else 0)
                target_cat = sorted_cats[0] if sorted_cats else None
                self.current_questions = self.qm.get_questions(category=target_cat, count=20, shuffle=True)
            else:
                self.current_questions = self.qm.get_questions(count=20, shuffle=True)
            
        if not self.current_questions:
            QMessageBox.warning(self, "警告", "未找到符合条件的题目！")
            return
            
        self.start_quiz_session()

    def start_quiz_session(self):
        self.current_idx = 0
        self.score = 0
        self.user_answers = []
        self.page_title.setText("正在刷题...")
        self.show_quiz_page()

    def clear_layout(self, layout):
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    self.clear_layout(item.layout())
                    item.layout().deleteLater()

    def show_quiz_page(self):
        try:
            self.stack.setCurrentWidget(self.page_quiz)
            
            if not self.page_quiz.layout():
                QVBoxLayout(self.page_quiz)
            
            self.clear_layout(self.page_quiz.layout())
            self.page_quiz.layout().setContentsMargins(0, 0, 0, 0)

            # 使用滚动区域包裹内容
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
            
            scroll_content = QWidget()
            scroll_content.setStyleSheet("background-color: transparent;")
            layout = QVBoxLayout(scroll_content)
            layout.setContentsMargins(40, 20, 40, 20)
            layout.setSpacing(20)
            
            self.page_quiz.layout().addWidget(scroll)
            scroll.setWidget(scroll_content)
            
            if not self.current_questions:
                lbl = QLabel("当前没有待做题目")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(lbl)
                return

            top_bar = QHBoxLayout()
            progress_val = int((self.current_idx + 1) / len(self.current_questions) * 100)
            pbar = QProgressBar()
            pbar.setValue(progress_val)
            pbar.setFixedHeight(10)
            pbar.setTextVisible(False)
            pbar.setStyleSheet("""
                QProgressBar { background-color: #E0E0E0; border-radius: 5px; border: none; }
                QProgressBar::chunk { background-color: #4D7CFE; border-radius: 5px; }
            """)
            
            info_lbl = QLabel(f"题目 {self.current_idx + 1} / {len(self.current_questions)}")
            info_lbl.setFont(QFont("Segoe UI Bold", 12))
            
            top_bar.addWidget(info_lbl)
            top_bar.addSpacing(20)
            top_bar.addWidget(pbar)
            layout.addLayout(top_bar)
            
            q = self.current_questions[self.current_idx]
            
            q_card = ModernCard()
            q_card_layout = QVBoxLayout(q_card)
            q_card_layout.setContentsMargins(30, 30, 30, 30)
            
            q_type_lbl = QLabel(q.get('type', '未知题型'))
            q_type_lbl.setStyleSheet("color: #4D7CFE; font-weight: bold; font-size: 13px;")
            q_card_layout.addWidget(q_type_lbl)
            
            q_text = QLabel(q.get("question", ""))
            q_text.setFont(QFont("Segoe UI Semibold", 18))
            q_text.setWordWrap(True)
            q_text.setStyleSheet("color: #1A1C2E; line-height: 1.5;")
            q_card_layout.addWidget(q_text)
            layout.addWidget(q_card)
            
            self.ans_area = QWidget()
            self.ans_layout = QVBoxLayout(self.ans_area)
            self.ans_layout.setSpacing(15)
            layout.addWidget(self.ans_area)
            
            q_type = q.get("type")
            if q_type in ["单选题", "判断题", "选择题"]:
                self.ans_group = QButtonGroup(self)
                opts = q.get("options", ["正确", "错误"]) if q_type == "判断题" else q.get("options", [])
                for i, opt in enumerate(opts):
                    text = f"{chr(65+i)}. {opt}" if q_type in ["单选题", "选择题"] else opt
                    rb = QRadioButton(text)
                    rb.setStyleSheet("""
                        QRadioButton { font-size: 15px; padding: 12px; border: 1px solid #E0E0E0; border-radius: 10px; background: white; }
                        QRadioButton:hover { background: #F8FAFF; border-color: #4D7CFE; }
                        QRadioButton::indicator { width: 0px; }
                        QRadioButton:checked { background: #4D7CFE; color: white; border-color: #4D7CFE; }
                    """)
                    self.ans_group.addButton(rb, i)
                    self.ans_layout.addWidget(rb)
            elif q_type == "多选题":
                self.checks = []
                for i, opt in enumerate(q.get("options", [])):
                    cb = QCheckBox(f"{chr(65+i)}. {opt}")
                    cb.setStyleSheet("""
                        QCheckBox { font-size: 15px; padding: 12px; border: 1px solid #E0E0E0; border-radius: 10px; background: white; }
                        QCheckBox:hover { background: #F8FAFF; border-color: #4D7CFE; }
                        QCheckBox::indicator { width: 0px; }
                        QCheckBox:checked { background: #4D7CFE; color: white; border-color: #4D7CFE; }
                    """)
                    self.checks.append(cb)
                    self.ans_layout.addWidget(cb)
            elif q_type == "填空题":
                self.edit_ans = QLineEdit()
                self.edit_ans.setPlaceholderText("在此输入答案...")
                self.edit_ans.setFixedHeight(50)
                self.edit_ans.setStyleSheet("border: 2px solid #E0E0E0; border-radius: 10px; padding: 0 15px; font-size: 16px;")
                self.ans_layout.addWidget(self.edit_ans)
            elif q_type in ["简答题", "设计题", "分析题", "编程题", "应用题"]:
                self.edit_ans = QTextEdit()
                self.edit_ans.setPlaceholderText("在此输入答案...")
                self.edit_ans.setFixedHeight(150)
                self.edit_ans.setStyleSheet("border: 2px solid #E0E0E0; border-radius: 10px; padding: 10px; font-size: 16px;")
                self.ans_layout.addWidget(self.edit_ans)
                
            self.feedback_box = QFrame()
            self.feedback_box.setVisible(False)
            self.feedback_box.setStyleSheet("border-radius: 10px; padding: 15px;")
            fb_l = QVBoxLayout(self.feedback_box)
            self.fb_lbl = QLabel()
            self.fb_lbl.setFont(QFont("Segoe UI Bold", 14))
            self.correct_lbl = QLabel()
            self.correct_lbl.setWordWrap(True)
            fb_l.addWidget(self.fb_lbl)
            fb_l.addWidget(self.correct_lbl)
            layout.addWidget(self.feedback_box)
            
            btn_l = QHBoxLayout()
            btn_l.addStretch()
            
            self.btn_back_home = ModernButton("🏠 返回主页")
            self.btn_back_home.clicked.connect(self.show_home_page)
            btn_l.addWidget(self.btn_back_home)
            
            self.btn_submit = ModernButton("确认提交", primary=True)
            self.btn_submit.clicked.connect(self.check_answer)
            btn_l.addWidget(self.btn_submit)
            
            self.btn_next = ModernButton("下一题 →")
            self.btn_next.clicked.connect(self.next_question)
            self.btn_next.setEnabled(False)
            btn_l.addWidget(self.btn_next)
            
            layout.addLayout(btn_l)
            layout.addStretch()
        except Exception as e:
            print(f"Error showing quiz page: {e}")
            QMessageBox.critical(self, "错误", f"加载题目页面失败: {e}")

    def check_answer(self):
        q = self.current_questions[self.current_idx]
        q_type = q.get("type")
        correct = q.get("answer", "")
        
        user_ans = ""
        is_ok = False
        
        if q_type in ["单选题", "判断题", "选择题"]:
            sel = self.ans_group.checkedButton()
            if sel:
                user_ans = chr(65 + self.ans_group.id(sel)) if q_type in ["单选题", "选择题"] else sel.text()
                is_ok = (user_ans == correct)
        elif q_type == "多选题":
            user_ans = "".join([chr(65+i) for i, c in enumerate(self.checks) if c.isChecked()])
            is_ok = (user_ans == correct)
        elif q_type == "填空题":
            user_ans = self.edit_ans.text().strip()
            is_ok = (user_ans == correct)
        elif q_type in ["简答题", "设计题", "分析题", "编程题", "应用题"]:
            user_ans = self.edit_ans.toPlainText().strip()
            is_ok = True # 简答题等主观题默认正确，主要通过解析对比
        else:
            is_ok = True
            
        self.udm.record_answer(q.get("cat"), is_ok)
        if not is_ok:
            self.udm.add_wrong_question(q.get("id"))
        else:
            self.udm.remove_wrong_question(q.get("id"))
            self.score += 1
            
        self.user_answers.append({"q": q, "user": user_ans, "ok": is_ok})
        
        self.feedback_box.setVisible(True)
        if is_ok:
            self.feedback_box.setStyleSheet("background-color: #E7F6ED; border: 1px solid #2ECC71;")
            self.fb_lbl.setText("🎉 回答正确！")
            self.fb_lbl.setStyleSheet("color: #27AE60;")
        else:
            self.feedback_box.setStyleSheet("background-color: #FFEBEE; border: 1px solid #FF5252;")
            self.fb_lbl.setText("❌ 回答错误")
            self.fb_lbl.setStyleSheet("color: #C0392B;")
        
        analysis = q.get('analysis')
        if not analysis:
            analysis = "暂无解析"
        self.correct_lbl.setText(f"正确答案: {correct}\n解析: {analysis}")
        
        self.btn_submit.setEnabled(False)
        self.btn_next.setEnabled(True)
        self.ans_area.setEnabled(False)

    def next_question(self):
        self.current_idx += 1
        if self.current_idx < len(self.current_questions):
            self.show_quiz_page()
        else:
            self.show_result_page()

    def show_result_page(self):
        self.page_title.setText("练习报告")
        self.stack.setCurrentWidget(self.page_result)
        
        if not self.page_result.layout():
            QVBoxLayout(self.page_result)
        
        self.clear_layout(self.page_result.layout())
        self.page_result.layout().setContentsMargins(0, 0, 0, 0)

        # 使用滚动区域包裹内容
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(25)
        
        self.page_result.layout().addWidget(scroll)
        scroll.setWidget(scroll_content)
            
        res_card = ModernCard()
        res_l = QVBoxLayout(res_card)
        res_l.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel("🏆 练习报告")
        title.setFont(QFont("Segoe UI Bold", 26))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        res_l.addWidget(title)
        res_l.addSpacing(10)
        
        acc = (self.score / len(self.current_questions) * 100) if self.current_questions else 0
        
        # 结果环形进度条
        res_circle_layout = QHBoxLayout()
        res_circle = CircularProgress(value=0, size=220)
        res_circle_layout.addStretch()
        res_circle_layout.addWidget(res_circle)
        res_circle_layout.addStretch()
        res_l.addLayout(res_circle_layout)
        res_circle.set_value(acc)
        
        msg = QLabel(f"本次练习共 {len(self.current_questions)} 题，答对 {self.score} 题")
        msg.setFont(QFont("Segoe UI", 16))
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        res_l.addWidget(msg)
        
        layout.addWidget(res_card)
        
        btn_row = QHBoxLayout()
        btn_home = ModernButton("返回主页", primary=True)
        btn_home.clicked.connect(self.show_home_page)
        btn_row.addWidget(btn_home)
        
        layout.addLayout(btn_row)
        layout.addStretch()
        
        self.udm.record_session(len(self.current_questions), self.score)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = QuizApp()
    window.show()
    sys.exit(app.exec())
