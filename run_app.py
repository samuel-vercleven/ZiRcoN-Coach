import json
import os
from pathlib import Path
import re
import sys
import traceback


def main():
    try:
        from app.application import ZirconCoachApplication
        return ZirconCoachApplication().run()
    except Exception:
        # Preserve startup diagnostics even in a windowed build without a console.
        detail = re.sub(r'RGAPI-[A-Za-z0-9-]+', '<clé masquée>', traceback.format_exc())
        root = Path(os.environ.get('ZIRCON_DATA_DIR') or (Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'ZiRcoN-Coach'))
        log = root / 'logs' / 'startup-error.log'
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(detail, encoding='utf-8')
        if '--smoke-output' in sys.argv:
            output = Path(sys.argv[sys.argv.index('--smoke-output') + 1])
            output.write_text(json.dumps({'passed': False, 'error': detail}), encoding='utf-8')
        elif '--smoke-check' not in sys.argv:
            from PySide6.QtWidgets import QApplication, QMessageBox
            app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, 'ZiRcoN Coach', 'Le démarrage n’a pas pu être terminé. Tes données n’ont pas été remplacées. Réessaie après avoir extrait tout le ZIP. Un journal de démarrage est disponible dans ton dossier de données.')
        if sys.stderr is not None:
            sys.stderr.write(detail)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
