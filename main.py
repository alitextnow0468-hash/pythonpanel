import sys
import random
import sqlite3
import os
from datetime import datetime
import jdatetime
import qtawesome as qta

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QSpinBox, QGroupBox, QGridLayout, QFrame
)
from PySide6.QtCore import Qt, QTimer, QRectF, QSize
from PySide6.QtGui import QFont, QFontDatabase, QPainter, QColor, QPen, QPixmap

# ==================== تنظیمات قابل ویرایش ====================
COMPANY_NAME = "مجموعه / شرکت شما"
MAIN_TITLE = "پنل مدیریت نیروی انسانی آتیه مهر طوس"
# ========================================================

class AnalogClock(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(65, 65)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height())
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(side / 65.0, side / 65.0)

        painter.setPen(QPen(QColor("#1e40af"), 2.5))
        painter.setBrush(QColor("#f8fafc"))
        painter.drawEllipse(QRectF(-30, -30, 60, 60))

        time = datetime.now()
        hour = time.hour % 12
        minute = time.minute
        second = time.second

        painter.setPen(QPen(QColor("#1e40af"), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.save()
        painter.rotate(30.0 * (hour + minute / 60.0))
        painter.drawLine(0, 0, 0, -16)
        painter.restore()

        painter.setPen(QPen(QColor("#334155"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.save()
        painter.rotate(6.0 * minute)
        painter.drawLine(0, 0, 0, -22)
        painter.restore()

        painter.setPen(QPen(QColor("#ef4444"), 1.5))
        painter.save()
        painter.rotate(6.0 * second)
        painter.drawLine(0, 4, 0, -25)
        painter.restore()

        painter.setBrush(QColor("#1e40af"))
        painter.drawEllipse(QRectF(-2.5, -2.5, 5, 5))


class HRPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(MAIN_TITLE)
        self.setGeometry(50, 30, 1320, 760)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.employees = []
        self.existing_codes = set()
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        self.setup_font()
        self.init_ui()
        self.apply_styles()
        self.update_header_date()

        self.init_database()
        self.load_employees_from_db()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_header_date)
        self.timer.start(60000)

    # ==================== فونت سراسری ====================
    def setup_font(self):
        font_path = os.path.join(self.base_dir, "resources", "Vazirmatn-Regular.ttf")
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            app_font = QFont(font_family, 11)
            QApplication.setFont(app_font)

    # ==================== دیتابیس ====================
    def init_database(self):
        os.makedirs("data", exist_ok=True)
        self.db_path = os.path.join(self.base_dir, "data", "hrm.db")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                code TEXT PRIMARY KEY,
                last_name TEXT NOT NULL,
                national_id TEXT,
                id_number TEXT,
                marital TEXT,
                children INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)

        # اضافه کردن فیلدهای جدید
        columns_to_add = [
            ("position", "TEXT"),
            ("base_salary", "INTEGER DEFAULT 166255500"),
            ("employment_year", "INTEGER"),
            ("employment_month", "INTEGER"),
            ("employment_day", "INTEGER")
        ]
        for col_name, col_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE employees ADD COLUMN {col_name} {col_type}")
            except:
                pass

        conn.commit()
        conn.close()

    def load_employees_from_db(self):
        self.employees.clear()
        self.existing_codes.clear()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT code, last_name, national_id, id_number, position, base_salary, 
                   marital, children, employment_year, employment_month, employment_day 
            FROM employees
        """)
        for row in cursor.fetchall():
            emp = {
                "code": row[0],
                "last_name": row[1],
                "national_id": row[2],
                "id_number": row[3],
                "position": row[4] or "",
                "base_salary": row[5] or 166255500,
                "marital": row[6],
                "children": row[7],
                "employment_year": row[8],
                "employment_month": row[9] or 1,
                "employment_day": row[10] or 1
            }
            self.employees.append(emp)
            self.existing_codes.add(row[0])
        conn.close()
        self.refresh_personnel_table()

    def save_employee_to_db(self, emp):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO employees 
            (code, last_name, national_id, id_number, position, base_salary, marital, children,
             employment_year, employment_month, employment_day, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            emp["code"], emp["last_name"], emp["national_id"], emp.get("id_number", ""),
            emp.get("position", ""), emp.get("base_salary", 166255500),
            emp.get("marital", ""), emp.get("children", 0),
            emp.get("employment_year"), emp.get("employment_month"), emp.get("employment_day"),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()

    def delete_employee_from_db(self, code):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM employees WHERE code = ?", (code,))
        conn.commit()
        conn.close()

    # ==================== رابط کاربری ====================
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        self.background_label = QLabel(central)
        self.background_label.setScaledContents(True)
        bg_path = os.path.join(self.base_dir, "resources", "background.png")
        if not os.path.exists(bg_path):
            bg_path = os.path.join(self.base_dir, "resources", "background.jpg")
        if os.path.exists(bg_path):
            pix = QPixmap(bg_path)
            self.background_label.setPixmap(pix)
            self.background_label.lower()

        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #1e40af; border-radius: 8px; padding: 8px;")
        header_layout = QHBoxLayout(header_frame)

        self.logo_label = QLabel()
        logo_path = os.path.join(self.base_dir, "resources", "logo.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaled(55, 55, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pix)
        header_layout.addWidget(self.logo_label)

        title_layout = QVBoxLayout()
        main_title = QLabel(MAIN_TITLE)
        main_title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        company_label = QLabel(COMPANY_NAME)
        company_label.setStyleSheet("color: #bae6fd; font-size: 13px;")
        title_layout.addWidget(main_title)
        title_layout.addWidget(company_label)
        header_layout.addLayout(title_layout)

        header_layout.addStretch()

        self.date_label = QLabel()
        self.date_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        self.clock = AnalogClock()
        header_layout.addWidget(self.date_label)
        header_layout.addWidget(self.clock)

        btn_exit = QPushButton("خروج")
        btn_exit.setFixedSize(75, 32)
        btn_exit.setStyleSheet("""
            background-color: #dc2626; 
            color: white; 
            border-radius: 6px; 
            font-weight: bold;
            font-size: 13px;
        """)
        btn_exit.clicked.connect(self.close)
        header_layout.addWidget(btn_exit)

        main_layout.addWidget(header_frame)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.create_home_tab()
        self.create_register_tab()
        self.create_list_tab()

        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.tabs.tabBar().hide()

    def on_tab_changed(self, index):
        if index == 0:
            self.tabs.tabBar().hide()
        else:
            self.tabs.tabBar().show()

    def resizeEvent(self, event):
        if hasattr(self, 'background_label') and self.background_label.pixmap():
            self.background_label.setGeometry(self.centralWidget().rect())
        super().resizeEvent(event)

    def update_header_date(self):
        jdate = jdatetime.datetime.now()
        persian_months = ["فروردین", "اردبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                          "مهر", "آبان", "آذر", "دی", "بهمن", "اسخند"]
        weekdays = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
        weekday_name = weekdays[jdate.weekday()]
        self.date_label.setText(f"امروز {weekday_name} {jdate.day} {persian_months[jdate.month-1]} {jdate.year} می‌باشد")

    # ==================== تب خانه ====================
    def create_home_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(50, 20, 50, 20)
        layout.setSpacing(10)

        logo_label = QLabel()
        logo_path = os.path.join(self.base_dir, "resources", "logo2.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pix)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo_label)

        desc = QLabel("تنظیم قراردادهای کار، پیمانکاری و مشاوره\nقبول نمایندگی در هیئت‌های تشخیص و حل اختلاف اداره کار و تامین اجتماعی")
        desc.setStyleSheet("font-size: 15px; color: #334155; line-height: 1.6;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(15)

        contact_title = QLabel("تماس با ما")
        contact_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e40af;")
        contact_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(contact_title)

        p1 = QLabel("۰۹۱۵۱۱۵۳۷۹۸")
        p1.setStyleSheet("font-size: 20px; color: #1e40af; font-weight: bold;")
        p1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(p1)

        p2 = QLabel("۰۹۱۵۸۱۵۳۵۳۰")
        p2.setStyleSheet("font-size: 20px; color: #1e40af; font-weight: bold;")
        p2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(p2)

        layout.addStretch()

        btn = QPushButton(qta.icon('fa5s.sign-in-alt', color='white'), "ورود به پنل")
        btn.setMinimumHeight(48)
        btn.setIconSize(QSize(20, 20))
        btn.setStyleSheet("font-size: 15px; background-color: #1e40af; color: white; border-radius: 8px;")
        btn.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        layout.addWidget(btn)

        self.tabs.addTab(tab, "خانه")

    def create_register_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 10, 15, 10)

        title = QLabel("ثبت نیروی جدید")
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #1e40af; margin-bottom: 8px;")
        layout.addWidget(title)

        form_group = QGroupBox()
        grid = QGridLayout(form_group)
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(10)

        grid.addWidget(QLabel("نام خانوادگی:"), 0, 0)
        self.last_name = QLineEdit()
        grid.addWidget(self.last_name, 0, 1)

        grid.addWidget(QLabel("کد ملی (۱۰ رقم):"), 0, 2)
        self.national_id = QLineEdit()
        self.national_id.setMaxLength(10)
        self.national_id.textChanged.connect(self.auto_fill_personnel_code)
        grid.addWidget(self.national_id, 0, 3)

        grid.addWidget(QLabel("شماره شناسنامه:"), 1, 0)
        self.id_number = QLineEdit()
        grid.addWidget(self.id_number, 1, 1)

        grid.addWidget(QLabel("سمت شغلی:"), 1, 2)
        self.position = QLineEdit()
        grid.addWidget(self.position, 1, 3)

        grid.addWidget(QLabel("حقوق پایه ثابت ماهیانه (ریال):"), 2, 0)
        self.base_salary = QLineEdit()
        self.base_salary.setText("166255500")
        grid.addWidget(self.base_salary, 2, 1)

        grid.addWidget(QLabel("کد پرسنلی:"), 2, 2)
        self.personnel_code = QLineEdit()
        self.personnel_code.setReadOnly(True)
        grid.addWidget(self.personnel_code, 2, 3)

        grid.addWidget(QLabel("تاریخ استخدام (شمسی):"), 3, 0)
        date_layout = QHBoxLayout()
        self.emp_day = QSpinBox()
        self.emp_day.setRange(1, 31)
        self.emp_day.setValue(1)

        self.emp_month = QComboBox()
        persian_months = ["فروردین", "اردبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                          "مهر", "آبان", "آذر", "دی", "بهمن", "اسخند"]
        self.emp_month.addItems(persian_months)
        current_jdate = jdatetime.datetime.now()
        self.emp_month.setCurrentIndex(current_jdate.month - 1)

        self.emp_year = QSpinBox()
        self.emp_year.setRange(1330, 1420)
        self.emp_year.setValue(current_jdate.year)

        date_layout.addWidget(self.emp_day)
        date_layout.add(QLabel("/"))
        date_layout.addWidget(self.emp_month)
        date_layout.add(QLabel("/"))
        date_layout.addWidget(self.emp_year)
        grid.addLayout(date_layout, 3, 1)

        grid.addWidget(QLabel("وضعیت تاهل:"), 3, 2)
        self.marital_status = QComboBox()
        self.marital_status.addItems(["مجرد", "متاهل"])
        self.marital_status.currentTextChanged.connect(self.toggle_children)
        grid.addWidget(self.marital_status, 3, 3)

        grid.addWidget(QLabel("تعداد فرزند:"), 4, 0)
        self.children_count = QSpinBox()
        self.children_count.setRange(0, 12)
        self.children_count.setVisible(False)
        grid.addWidget(self.children_count, 4, 1)

        layout.addWidget(form_group)

        btn_save = QPushButton(qta.icon('fa5s.save', color='white'), "ثبت نیروی جدید")
        btn_save.setMinimumHeight(44)
        btn_save.setIconSize(QSize(18, 18))
        btn_save.clicked.connect(self.register_employee)
        layout.addWidget(btn_save)

        layout.addStretch()
        self.tabs.addTab(tab, "ثبت نیروی جدید")

    def auto_fill_personnel_code(self):
        national_id = self.national_id.text().strip()
        if national_id.isdigit():
            self.personnel_code.setText(national_id)

    def toggle_children(self, text):
        self.children_count.setVisible(text == "متاهل")

    def register_employee(self):
        last_name = self.last_name.text().strip()
        national_id = self.national_id.text().strip()
        code = self.personnel_code.text().strip()

        if not last_name or not national_id or not code:
            QMessageBox.warning(self, "خطا", "نام خانوادگی و کد ملی الزامی است")
            return

        if not national_id.isdigit() or len(national_id) != 10:
            QMessageBox.warning(self, "خطا", "کد ملی باید دقیقاً ۱۰ رقم باشد")
            return

        if any(emp["national_id"] == national_id for emp in self.employees):
            QMessageBox.warning(self, "خطا", "این کد ملی قبلاً ثبت شده است")
            return

        try:
            base_salary = int(self.base_salary.text().replace(",", ""))
        except:
            base_salary = 166255500

        emp = {
            "code": code,
            "last_name": last_name,
            "national_id": national_id,
            "id_number": self.id_number.text().strip(),
            "position": self.position.text().strip(),
            "base_salary": base_salary,
            "marital": self.marital_status.currentText(),
            "children": self.children_count.value() if self.marital_status.currentText() == "متاهل" else 0,
            "employment_year": self.emp_year.value(),
            "employment_month": self.emp_month.currentIndex() + 1,
            "employment_day": self.emp_day.value()
        }

        self.employees.append(emp)
        self.existing_codes.add(code)
        self.save_employee_to_db(emp)

        self.refresh_personnel_table()
        self.clear_form()
        QMessageBox.information(self, "ثبت شد", f"نیرو با کد ملی {national_id} ذخیره شد")

    def clear_form(self):
        self.last_name.clear()
        self.national_id.clear()
        self.id_number.clear()
        self.personnel_code.clear()
        self.position.clear()
        self.base_salary.setText("166255500")
        self.marital_status.setCurrentIndex(0)
        self.children_count.setValue(0)

    def create_list_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 10, 12, 10)

        title = QLabel("لیست نیروها")
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #1e40af; margin-bottom: 8px;")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "کد پرسنلی", "نام خانوادگی", "کد ملی", "سمت", "حقوق پایه", "تاریخ استخدام", "ویرایش", "حذف"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self.tabs.addTab(tab, "لیست نیروها")

    def refresh_personnel_table(self):
        self.table.setRowCount(0)
        persian_months = ["فروردین", "اردبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                          "مهر", "آبان", "آذر", "دی", "بهمن", "اسخند"]

        for emp in self.employees:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(emp["code"]))
            self.table.setItem(row, 1, QTableWidgetItem(emp["last_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(emp["national_id"]))
            self.table.setItem(row, 3, QTableWidgetItem(emp.get("position", "")))
            self.table.setItem(row, 4, QTableWidgetItem(f"{emp.get('base_salary', 0):,}"))

            month_idx = emp.get('employment_month') or 1
            emp_date = f"{emp.get('employment_day', '')} {persian_months[month_idx-1]} {emp.get('employment_year', '')}"
            self.table.setItem(row, 5, QTableWidgetItem(emp_date))

            btn_edit = QPushButton(qta.icon('fa5s.edit', color='#1e40af'), "ویرایش")
            btn_edit.setFixedSize(75, 26)
            btn_edit.setIconSize(QSize(15, 15))
            btn_edit.clicked.connect(lambda checked, r=row: self.edit_employee(r))
            self.table.setCellWidget(row, 6, btn_edit)

            btn_del = QPushButton(qta.icon('fa5s.trash-alt', color='#dc2626'), "حذف")
            btn_del.setFixedSize(65, 26)
            btn_del.setIconSize(QSize(15, 15))
            btn_del.clicked.connect(lambda checked, r=row: self.delete_employee(r))
            self.table.setCellWidget(row, 7, btn_del)

    def edit_employee(self, row):
        emp = self.employees[row]
        QMessageBox.information(self, "ویرایش", f"ویرایش {emp['last_name']}\n(در مرحله بعدی کامل می‌شود)")

    def delete_employee(self, row):
        emp = self.employees[row]
        if QMessageBox.question(self, "حذف", f"حذف {emp['last_name']}؟") == QMessageBox.StandardButton.Yes:
            self.existing_codes.discard(emp["code"])
            self.delete_employee_from_db(emp["code"])
            del self.employees[row]
            self.refresh_personnel_table()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f1f5f9; }
            QTabWidget::pane { border: 2px solid #1e40af; background: white; border-radius: 6px; }
            QTabBar::tab { background: #1e40af; color: white; padding: 10px 25px; font-weight: bold; }
            QTabBar::tab:selected { background: #2563eb; }
            QGroupBox { border: 1.5px solid #64748b; border-radius: 6px; padding: 10px; }
            QPushButton { background-color: #1e40af; color: white; border-radius: 5px; font-weight: bold; padding: 6px 12px; }
            QPushButton:hover { background-color: #2563eb; }
            QLineEdit, QComboBox, QSpinBox { padding: 6px; border: 1px solid #64748b; border-radius: 4px; }
            QTableWidget { gridline-color: #94a3b8; font-size: 12px; alternate-background-color: #f8fafc; }
            QHeaderView::section { background-color: #1e40af; color: white; padding: 8px; font-weight: bold; }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HRPanel()
    window.showFullScreen()
    sys.exit(app.exec())