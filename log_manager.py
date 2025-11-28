import subprocess
from PySide6.QtCore import QThread, Signal

class LogWorker(QThread):
    finished_signal = Signal(list) # Devuelve lista de líneas
    error_signal = Signal(str)

    def __init__(self, category):
        super().__init__()
        self.category = category

    def run(self):
        cmd = []

        # 1. Definir el comando según la categoría
        if self.category == "firewall":
            # Buscamos palabras clave de bloqueo en el Kernel
            # UFW usa "[UFW BLOCK]", Firewalld suele usar "FINAL_REJECT" o similar
            # -k: Kernel logs, -n 100: Últimas 100 líneas, -r: Inverso (más nuevo primero)
            cmd = ["pkexec", "journalctl", "-k", "-g", "UFW BLOCK|FINAL_REJECT|DROP", "-n", "100", "-r", "--no-pager"]

        elif self.category == "antivirus":
            # Logs de los servicios de ClamAV
            cmd = ["pkexec", "journalctl", "-u", "clamav-daemon", "-u", "clamav-clamonacc", "-u", "clamav-freshclam", "-n", "100", "-r", "--no-pager"]

        else:
            # Sistema general (limitado a nuestra app y network manager)
            cmd = ["journalctl", "-n", "100", "-r", "--no-pager"]

        try:
            # Ejecutamos el comando
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                self.error_signal.emit(f"Error {result.returncode}: {result.stderr}")
                return

            lines = result.stdout.splitlines()
            self.finished_signal.emit(lines)

        except Exception as e:
            self.error_signal.emit(str(e))
