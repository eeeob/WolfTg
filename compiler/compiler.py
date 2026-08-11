from pathlib import Path
from types import ModuleType

import importlib.util
import requests
import json

BASE_URL = "https://wolf-tg.com"
BASE = Path(__file__).parent.parent.parent

ERRORS = (BASE / "compiler/errors/source.json", f"{BASE_URL}/api/json_erros", 5, "start")
SCHEMA = (BASE / "compiler/schema/source.json", f"{BASE_URL}/api/schema_erros", 5, "start")



def import_module_from_path(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from: {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module

def start():
    for file, url, timeout, func_name in (ERRORS, SCHEMA):
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
        except Exception as e:
            print(e)
            continue

        file.write_text(
            json.dumps(r.json(), indent=4, ensure_ascii=False, sort_keys=True), 
            encoding="utf-8"
        )

        try:
            module = import_module_from_path(file.with_name("compiler.py"))
            getattr(module, func_name)()
        except Exception as e:
            print(e)



if __name__ == "__main__":
    start()



