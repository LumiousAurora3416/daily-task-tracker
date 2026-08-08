"""任务添加/编辑对话框"""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.core.data_storage import Task
from src.core.task_manager import TaskManager
from src.utils.constants import (
    DEFAULT_POMODORO_WORK,
    TASK_TYPE_HABIT,
    TASK_TYPE_LABELS,
    TASK_TYPE_POMODORO,
    TASK_TYPE_TODO,
    WEEKDAY_LABELS,
)


class TaskDialog(QDialog):
    """新建或编辑任务"""

    def __init__(self, task_manager: TaskManager, parent: Optional[QWidget] = None, task: Optional[Task] = None):
        super().__init__(parent)
        self.task_manager = task_manager
        self._task = task
        self.setWindowTitle("编辑任务" if task else "添加任务")
        self.setMinimumWidth(420)
        self._build_ui()
        if task:
            self._fill(task)

    # ----- UI -----

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("例如：投递 5 份简历")
        form.addRow("任务名称", self.title_edit)

        # 类型单选
        type_row = QHBoxLayout()
        self.type_group = QButtonGroup(self)
        self.type_radios = {}
        for key in (TASK_TYPE_TODO, TASK_TYPE_HABIT, TASK_TYPE_POMODORO):
            from PySide6.QtWidgets import QRadioButton

            rb = QRadioButton(TASK_TYPE_LABELS[key])
            rb.setProperty("type", key)
            self.type_group.addButton(rb)
            self.type_radios[key] = rb
            type_row.addWidget(rb)
        type_row.addStretch()
        type_widget = QWidget()
        type_widget.setLayout(type_row)
        form.addRow("任务类型", type_widget)
        self.type_radios[TASK_TYPE_TODO].setChecked(True)

        # 分类下拉
        self.category_combo = QComboBox()
        for c in self.task_manager.list_categories():
            self.category_combo.addItem(c.name, c.name)
        form.addRow("所属分类", self.category_combo)

        # 提醒时间
        time_row = QHBoxLayout()
        self.reminder_check = QCheckBox("定时提醒")
        self.reminder_check.toggled.connect(self._on_reminder_toggled)
        self.time_combo = QComboBox()
        self.time_combo.setEditable(True)
        for h in range(24):
            for m in (0, 30):
                self.time_combo.addItem(f"{h:02d}:{m:02d}")
        self.time_combo.setCurrentText("09:00")
        self.time_combo.setEnabled(False)
        time_row.addWidget(self.reminder_check)
        time_row.addWidget(self.time_combo, 1)
        time_widget = QWidget()
        time_widget.setLayout(time_row)
        form.addRow("提醒", time_widget)

        # 重复周期
        repeat_row = QHBoxLayout()
        self.day_checks: list[QCheckBox] = []
        for iso in range(1, 8):
            cb = QCheckBox(WEEKDAY_LABELS[iso - 1])
            cb.setProperty("iso", iso)
            repeat_row.addWidget(cb)
            self.day_checks.append(cb)
        repeat_row.addStretch()
        repeat_widget = QWidget()
        repeat_widget.setLayout(repeat_row)
        form.addRow("重复周期", repeat_widget)

        # 专注时长
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 180)
        self.duration_spin.setValue(DEFAULT_POMODORO_WORK)
        self.duration_spin.setSuffix(" 分钟")
        form.addRow("专注时长", self.duration_spin)

        layout.addLayout(form)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_reminder_toggled(self, on: bool) -> None:
        self.time_combo.setEnabled(on)

    def _fill(self, task: Task) -> None:
        self.title_edit.setText(task.title)
        self.type_radios[task.type].setChecked(True)
        idx = self.category_combo.findData(task.category)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        if task.reminder_time:
            self.reminder_check.setChecked(True)
            self.time_combo.setCurrentText(task.reminder_time)
        for cb in self.day_checks:
            iso = cb.property("iso")
            cb.setChecked(iso in task.repeat_days)
        self.duration_spin.setValue(task.duration)

    # ----- 提交 -----

    def build_task(self) -> Task:
        # 选中的类型
        task_type = TASK_TYPE_TODO
        for key, rb in self.type_radios.items():
            if rb.isChecked():
                task_type = key
                break
        repeat_days = [cb.property("iso") for cb in self.day_checks if cb.isChecked()]
        reminder_time = self.time_combo.currentText().strip() if self.reminder_check.isChecked() else None
        return Task(
            id=self._task.id if self._task else 0,
            title=self.title_edit.text().strip(),
            category=self.category_combo.currentData(),
            type=task_type,
            reminder_time=reminder_time,
            repeat_days=repeat_days,
            duration=self.duration_spin.value(),
            is_enabled=self._task.is_enabled if self._task else True,
        )

    @staticmethod
    def new_task(task_manager: TaskManager, parent: Optional[QWidget] = None) -> Optional[Task]:
        dlg = TaskDialog(task_manager, parent)
        if dlg.exec() == QDialog.Accepted:
            t = dlg.build_task()
            if not t.title:
                return None
            task_manager.add_task(
                title=t.title,
                task_type=t.type,
                category=t.category,
                reminder_time=t.reminder_time,
                repeat_days=t.repeat_days,
                duration=t.duration,
                is_enabled=t.is_enabled,
            )
            return t
        return None

    @staticmethod
    def edit_task(task_manager: TaskManager, task: Task, parent: Optional[QWidget] = None) -> Optional[Task]:
        dlg = TaskDialog(task_manager, parent, task)
        if dlg.exec() == QDialog.Accepted:
            t = dlg.build_task()
            if not t.title:
                return None
            task_manager.update_task(t)
            return t
        return None
