import subprocess
from PySide6.QtCore import QThread, Signal
from firewall_detector import FirewallDetector # <--- Importar detector

class LogWorker(QThread):
    finished_signal = Signal(list)
    error_signal = Signal(str)

    def __init__(self, category):
        super().__init__()
        self.category = category
        self.detector = FirewallDetector() # Instanciamos el detector

    def run(self):
        cmd = []
        helper = "/usr/local/bin/sentinelx-helper"

        if self.category == "firewall":
            # 1. Detectar qué firewall está activo
            service = self.detector.get_active_service()

            if service == "firewalld":
                # Pedimos logs específicos de Firewalld
                cmd = ["pkexec", helper, "get-logs", "firewalld"]
            elif service == "ufw":
                # Pedimos logs específicos de UFW
                cmd = ["pkexec", helper, "get-logs", "ufw"]
            else:
                # Si no detectamos nada, intentamos un grep genérico
                cmd = ["journalctl", "-k", "-n", "50", "-r", "--no-pager"]

        elif self.category == "antivirus":
            cmd = ["pkexec", helper, "get-logs", "antivirus"]

        else:
            # Sistema general
            cmd = ["journalctl", "-n", "100", "-r", "--no-pager"]

        try:
            # Ejecutamos
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                self.error_signal.emit(f"Error {result.returncode}: {result.stderr}")
                return

            lines = result.stdout.splitlines()
            self.finished_signal.emit(lines)

        except Exception as e:
            self.error_signal.emit(str(e))
