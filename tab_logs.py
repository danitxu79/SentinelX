from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QComboBox, QPushButton, QTextEdit, QFrame)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt

import locales
from log_manager import LogWorker

class LogsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- CABECERA ---
        lbl_title = QLabel("📜 " + locales.get_text("logs_title"))
        lbl_title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(lbl_title)

        # --- BARRA DE HERRAMIENTAS ---
        toolbar = QHBoxLayout()

        # Selector de Categoría
        self.combo_type = QComboBox()
        self.combo_type.addItem(locales.get_text("logs_category_firewall"), "firewall")
        self.combo_type.addItem(locales.get_text("logs_category_antivirus"), "antivirus")
        self.combo_type.addItem(locales.get_text("logs_category_system"), "system")
        self.combo_type.setFixedWidth(250)
        self.combo_type.currentIndexChanged.connect(self.load_logs)
        toolbar.addWidget(self.combo_type)

        toolbar.addStretch()

        # Botón Refrescar
        self.btn_refresh = QPushButton("🔄 " + locales.get_text("logs_btn_refresh"))
        self.btn_refresh.clicked.connect(self.load_logs)
        toolbar.addWidget(self.btn_refresh)

        # Botón Limpiar
        btn_clear = QPushButton("🧹 " + locales.get_text("logs_btn_clear"))
        btn_clear.clicked.connect(lambda: self.log_viewer.clear())
        toolbar.addWidget(btn_clear)

        layout.addLayout(toolbar)

        # --- VISOR DE LOGS ---
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        # Estilo Terminal Hacker
        self.log_viewer.setStyleSheet("""
            QTextEdit {
                background-color: #0c0c0c;
                color: #00ff00;
                font-family: "Consolas", "Monospace";
                font-size: 12px;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.log_viewer)

        self.setLayout(layout)

        # Carga inicial (pero dejamos un pequeño delay para que no pida pass al arrancar la app entera)
        # Lo haremos manual la primera vez o conectado al showEvent

    def showEvent(self, event):
        """Cargar logs automáticamente al entrar en la pestaña"""
        super().showEvent(event)
        # Solo cargar si está vacío para no spamear sudo
        if not self.log_viewer.toPlainText():
            self.load_logs()

    def load_logs(self):
        category = self.combo_type.currentData()

        self.log_viewer.clear()
        self.log_viewer.append(f"⏳ {locales.get_text('logs_loading')}")
        self.btn_refresh.setEnabled(False)

        self.worker = LogWorker(category)
        self.worker.finished_signal.connect(self.display_logs)
        self.worker.error_signal.connect(self.display_error)
        self.worker.start()

    def display_logs(self, lines):
        self.btn_refresh.setEnabled(True)
        self.log_viewer.clear()

        if not lines:
            self.log_viewer.append(f"ℹ️ {locales.get_text('logs_empty')}")
            return

        for line in lines:
            # Colorear un poco la salida para que sea legible
            if "BLOCK" in line or "REJECT" in line or "DROP" in line:
                # Rojo para bloqueos
                self.log_viewer.append(f'<span style="color:#ff5555;">{line}</span>')
            elif "FOUND" in line: # Virus
                self.log_viewer.append(f'<span style="color:#ff5555; font-weight:bold;">{line}</span>')
            else:
                self.log_viewer.append(f'<span style="color:#00ff00;">{line}</span>')

    def display_error(self, error_msg):
        self.btn_refresh.setEnabled(True)
        self.log_viewer.append(f'<span style="color:orange;">⚠️ {locales.get_text("logs_error")}</span>')
        self.log_viewer.append(f'<span style="color:gray;">{error_msg}</span>')
