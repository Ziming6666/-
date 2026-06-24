# Railway 默认寻找 main.py，此处重定向到 server.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from server import app
