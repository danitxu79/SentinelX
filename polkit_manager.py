import os
import subprocess
import sys

# Rutas
POLKIT_RULE_PATH = "/etc/polkit-1/rules.d/49-sentinelx.rules"
HELPER_PATH = "/usr/local/bin/sentinelx-helper"

# --- VERSIÓN 14 (Universal Log Fix) ---
CURRENT_RULE_VERSION = 14

# 1. REGLA POLKIT (Sin cambios)
POLKIT_RULE_CONTENT = """/* Regla instalada por SentinelX (v14) */
polkit.addRule(function(action, subject) {
    var is_admin = subject.isInGroup("wheel") || subject.isInGroup("sudo");

    if (is_admin) {
        if (action.id.indexOf("org.fedoraproject.FirewallD1") == 0) {
            return polkit.Result.YES;
        }
        if (action.id == "org.freedesktop.policykit.exec") {
            var program = action.lookup("program");
            if (program == "/usr/bin/firewall-cmd" ||
                program == "/usr/sbin/firewall-cmd" ||
                program == "/usr/bin/ufw" ||
                program == "/usr/sbin/ufw" ||
                program == "/usr/bin/freshclam" ||
                program == "/usr/local/bin/sentinelx-helper" ||
                program == "/usr/bin/systemctl" ||
                program == "/bin/systemctl") {
                return polkit.Result.YES;
            }
        }
    }
});
"""

# 2. SCRIPT HELPER (Búsqueda Universal)
HELPER_CONTENT = r"""#!/bin/bash
# SentinelX Helper Script v14

COMMAND="$1"
ARG1="$2"
ARG2="$3"

case "$COMMAND" in
    "enable-on-access")
        CONF_PATH="$ARG1"
        WATCH_PATH="$ARG2"
        if [ -z "$CONF_PATH" ] || [ -z "$WATCH_PATH" ]; then exit 1; fi
        sed -i '/^OnAccess/d' "$CONF_PATH"
        echo "OnAccessIncludePath $WATCH_PATH" >> "$CONF_PATH"
        echo "OnAccessPrevention yes" >> "$CONF_PATH"
        echo "OnAccessExcludeUname root" >> "$CONF_PATH"
        echo "OnAccessExtraScanning yes" >> "$CONF_PATH"
        ;;

    "disable-on-access")
        CONF_PATH="$ARG1"
        if [ -z "$CONF_PATH" ]; then exit 1; fi
        sed -i '/^OnAccess/d' "$CONF_PATH"
        ;;

    "get-logs")
        LOG_TYPE="$ARG1"

        if [ "$LOG_TYPE" == "firewalld" ]; then
            # BÚSQUEDA UNIVERSAL: Buscamos la cadena "IN=" que siempre aparece en logs de red
            # También buscamos FINAL_REJECT por si acaso.
            journalctl -k -g "IN=.*OUT=|FINAL_REJECT|HOST_DENIED" -n 100 -r --no-pager || true

        elif [ "$LOG_TYPE" == "ufw" ]; then
            journalctl -k -g "\[UFW BLOCK\]" -n 100 -r --no-pager || true

        elif [ "$LOG_TYPE" == "antivirus" ]; then
            journalctl -u clamav-daemon -u clamav-clamonacc -u clamav-freshclam -n 100 -r --no-pager || true
        fi
        ;;

    *)
        echo "Comando desconocido"
        exit 1
        ;;
esac
"""

class PolkitManager:
    def get_current_version(self):
        return CURRENT_RULE_VERSION

    def install_rule(self):
        print(f"Instalando sistema de seguridad v{CURRENT_RULE_VERSION}...")

        setup_cmds = [
            f"cat << 'EOF' > {HELPER_PATH}\n{HELPER_CONTENT}\nEOF",
            f"chmod +x {HELPER_PATH}",
            f"cat << 'EOF' > {POLKIT_RULE_PATH}\n{POLKIT_RULE_CONTENT}\nEOF",
            "systemctl restart polkit"
        ]

        full_cmd = "\n".join(setup_cmds)
        cmd = ["pkexec", "sh", "-c", full_cmd]

        try:
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
        except Exception as e:
            print(f"Error setup: {e}")
            return False
