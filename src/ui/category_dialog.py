"""分类管理对话框"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.data_storage import Category
from src.core.task_manager import TaskManager


class CategoryDialog(QDialog):
    """管理分类的增删改"""

    def __init__(self, task_manager: TaskManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.task_manager = task_manager
        self.setWindowTitle("分类管理")
        self.setMinimumSize(420, 360)
        self._build_ui()
        self._reload()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["名称", "颜色", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        btn_add = QPushButton("新增分类")
        btn_add.clicked.connect(self._on_add)
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_add)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _reload(self) -> None:
        self.table.setRowCount(0)
        for row, cat in enumerate(self.task_manager.list_categories()):
            self.table.insertRow(row)
            name_item = QTableWidgetItem(cat.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            color_item = QTableWidgetItem("")
            color_item.setFlags(color_item.flags() & ~Qt.ItemIsEditable)
            color_item.setBackground(QColor(cat.color))
            color_item.setText(cat.color)
            color_item.setForeground(QColor("#FFFFFF"))
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, color_item)

            actions = QWidget()
            h = QHBoxLayout(actions)
            h.setContentsMargins(4, 0, 4, 0)
            btn_edit = QPushButton("编辑")
            btn_del = QPushButton("删除")
            btn_edit.clicked.connect(lambda _, c=cat: self._on_edit(c))
            btn_del.clicked.connect(lambda _, c=cat: self._on_delete(c))
            h.addWidget(btn_edit)
            h.addWidget(btn_del)
            self.table.setCellWidget(row, 2, actions)

    # ----- 操作 -----

    def _on_add(self) -> None:
        name, color = self._prompt("新增分类", "", "#3B82F6")
        if name is None:
            return
        if not name.strip():
            return
        try:
            self.task_manager.upsert_category(name.strip(), color)
        except Exception as e:
            print("add category failed:", e)
        self._reload()

    def _on_edit(self, cat: Category) -> None:
        name, color = self._prompt("编辑分类", cat.name, cat.color)
        if name is None:
            return
        if not name.strip():
            return
        try:
            self.task_manager.upsert_category(name.strip(), color, cat.id)
        except Exception as e:
            print("update category failed:", e)
        self._reload()

    def _on_delete(self, cat: Category) -> None:
        from PySide6.QtWidgets import QMessageBox

        if QMessageBox.question(self, "删除分类", f"确定删除分类「{cat.name}」吗？\n关联任务将归到「未分类」。") != QMessageBox.Yes:
            return
        self.task_manager.delete_category(cat.id)
        self._reload()

    def _prompt(self, title: str, name: str, color: str) -> tuple[Optional[str], str]:
        from PySide6.QtWidgets import QDialogButtonBox, QFormLayout, QLineEdit

        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        form = QFormLayout(dlg)
        name_edit = QLineEdit(name)
        color_btn = QPushButton(color)
        color_btn.setStyleSheet(f"background-color:{color}; color:#fff;")

        def pick_color() -> None:
            c = QColorDialog.getColor(QColor(color_btn.text()), self, "选择颜色")
            if c.isValid():
                color_btn.setText(c.name().upper())
                color_btn.setStyleSheet(f"background-color:{c.name()}; color:#fff;")

        color_btn.clicked.connect(pick_color)
        form.addRow("名称", name_edit)
        form.addRow("颜色", color_btn)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)
        if dlg.exec() == QDialog.Accepted:
            return name_edit.text().strip(), color_btn.text().strip()
        return None, color
