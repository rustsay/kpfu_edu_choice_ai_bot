import json
from collections import defaultdict
from pathlib import Path

# Скрипт группирует программы по полю "institute" и сохраняет результат.

BASE_DIR = Path(__file__).resolve().parent
SRC = BASE_DIR / "kfu_programs.json"
OUT = BASE_DIR / "kfu_programs_by_institute.json"

def group_by_institute(data):
    grouped = {}
    temp = defaultdict(list)
    for prog in data.get("programs", []):
        inst = prog.get("institute", "Unknown Institute")
        temp[inst].append(prog)
    for inst, progs in temp.items():
        # Собираем уникальные города для института (может быть несколько филиалов)
        cities = sorted({p.get("city", "") for p in progs if p.get("city")})
        grouped[inst] = {
            "name": inst,
            "cities": cities,
            "programs": progs
        }
    return {"institutes": grouped}

def main():
    src_text = SRC.read_text(encoding="utf-8")
    data = json.loads(src_text)
    result = group_by_institute(data)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    # Краткая сводка
    print(f"Grouped {len(data.get('programs', []))} programs into {len(result['institutes'])} institutes.")
    print(f"Output written to: {OUT}")

if __name__ == "__main__":
    main()