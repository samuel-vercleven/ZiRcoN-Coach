import os
from pathlib import Path
import sys


IS_PACKAGED = bool(getattr(sys, "frozen", False))
PROJECT_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
_override = os.getenv("ZIRCON_DATA_DIR")
DATA_ROOT = (Path(_override).resolve() if _override else
             Path(os.getenv("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "ZiRcoN-Coach" if IS_PACKAGED else PROJECT_ROOT)
DEFAULT_DB_PATH = DATA_ROOT / "database" / "zircon.db"
CACHE_ROOT = DATA_ROOT / ".cache" / "zircon"
CATALOG_ROOT = PROJECT_ROOT / "resources" / "catalogs" if IS_PACKAGED else PROJECT_ROOT / ".cache" / "zircon" / "stabilization-catalogs"
