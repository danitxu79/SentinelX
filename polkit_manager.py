import os
import subprocess
import sys

# Ruta del archivo de reglas
POLKIT_RULE_PATH = "/etc/polkit-1/rules.d/49-sentinelx.rules"

# --- CONTENIDO DE LA REGLA ACTUALIZADO ---
# Ahora autoriza tanto D-Bus como la ejecución directa del comando (pkexec)
POLKIT_RULE_CONTENT = """/* Regla instalada por SentinelX */
polkit.addRule(function(action, subject) {
    // Definimos quién es administrador (Manjaro/Arch usa 'wheel', Debian/Ubuntu usa 'sudo')
    var is_admin = subject.isInGroup("wheel") || subject.isInGroup("sudo");

    if (is_admin) {
        // 1. Permitir acceso a la API D-Bus de Firewalld
        if (action.id.indexOf("org.fedoraproject.FirewallD1") == 0) {
            return polkit.Result.YES;
        }

        // 2. Permitir ejecutar los comandos específicos vía pkexec
        // La ID para pkexec es siempre 'org.freedesktop.policykit.exec'
        if (action.id == "org.freedesktop.policykit.exec") {
            // Miramos qué programa se intenta ejecutar
            var program = action.lookup("program");

            // Autorizamos solo firewall-cmd y ufw
            if (program == "/usr/bin/firewall-cmd" ||
                program == "/usr/sbin/firewall-cmd" ||
                program == "/usr/bin/ufw" ||
                program == "/usr/sbin/ufw") {
                return polkit.Result.YES;
            }
        }
    }
});
"""

class PolkitManager:
    def install_rule(self):
        """
        Instala la regla usando pkexec.
        """
        print("Intentando instalar regla Polkit mejorada...")

        # Usamos sh -c para escribir el archivo con permisos de root
        cmd = ["pkexec", "sh", "-c", f"cat > {POLKIT_RULE_PATH}"]

        try:
            # 1. Ejecutamos el comando pasándole el contenido nuevo
            subprocess.run(
                cmd,
                input=POLKIT_RULE_CONTENT.encode('utf-8'),
                check=True
            )

            print("Regla actualizada correctamente.")

            # 2. Reiniciar polkit para aplicar cambios inmediatamente
            subprocess.run(["pkexec", "systemctl", "restart", "polkit"], stderr=subprocess.DEVNULL)

            return True

        except subprocess.CalledProcessError as e:
            print(f"Error instalando regla (Cancelado o Fallido): {e}")
            return False
        except Exception as e:
            print(f"Error inesperado: {e}")
            return False
