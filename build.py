import html
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG_FILE = ROOT / "build.json"
TEMPLATE_FILE = ROOT / "index.html"
OUTPUT_FILE = ROOT / "build" / "index.html"
COMPETITIONS_DIR = ROOT / "natjecanja"
LEVELS = (
    ("s", "Školsko", "skolsko"),
    ("z", "Županijsko", "zupanijsko"),
    ("d", "Državno", "drzavno"),
)
GRADES = (5, 6, 7, 8)
TYPES = (("z", "zadaci", "Zadaci"), ("r", "rjesenja", "Rješenja"))
FIRST_COMPETITION_YEAR = 1957


def load_range() -> tuple[int, int]:
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError(f"{CONFIG_FILE.name} must contain a JSON object.")

    start = config.get("start")
    end = config.get("end")
    if isinstance(start, bool) or not isinstance(start, int):
        raise ValueError(f"{CONFIG_FILE.name}: start must be an integer.")
    if isinstance(end, bool) or not isinstance(end, int):
        raise ValueError(f"{CONFIG_FILE.name}: end must be an integer.")
    if start > end:
        raise ValueError(f"{CONFIG_FILE.name}: start must not be greater than end.")
    return start, end


def year_label(competition: int) -> str:
    year = FIRST_COMPETITION_YEAR + competition
    return f"{year}./{year + 1}. ({competition}.)"


def filename(year: int, level: str, grade: int, file_type: str) -> str:
    return f"tk_{year}_{level}_{grade}r_{file_type}.pdf"


def make_table(years: list[str], existing: set[str]) -> str:
    parts = ['<thead><tr><th rowspan="2">Godina</th>']
    for level, name, _ in LEVELS:
        parts.append(
            f'<th colspan="4"><label><input type="checkbox" data-lvl="{level}"> '
            f'{html.escape(name)}</label></th>'
        )
    parts.append("</tr><tr>")
    for level, _, _ in LEVELS:
        for grade in GRADES:
            parts.append(
                f'<th><label><input type="checkbox" data-lvl="{level}" '
                f'data-gr="{grade}"> {grade}.</label></th>'
            )
    parts.append("</tr></thead><tbody>")

    for label in years:
        year = int(label[:4])
        escaped_label = html.escape(label, quote=True)
        parts.append(
            f'<tr><td><label><input type="checkbox" data-yr="{escaped_label}"> '
            f'{html.escape(label)}</label></td>'
        )
        for level, level_name, level_slug in LEVELS:
            for grade in GRADES:
                parts.append('<td align="center">')
                for file_type, type_slug, type_name in TYPES:
                    name = filename(year, level_slug, grade, type_slug)
                    key = f"{label}|{level}|{grade}|{file_type}"
                    if name in existing:
                        escaped_name = html.escape(name, quote=True)
                        parts.append(
                            '<span class="file-option"><label>'
                            f'<input type="checkbox" data-file="{key}">'
                            f'<a href="natjecanja/{escaped_name}" target="_blank" '
                            f'title="{type_name}, {grade}. razred, '
                            f'{html.escape(level_name.lower())}, '
                            f'{html.escape(label, quote=True)}">'
                            f'{file_type.upper()}</a></label></span>'
                        )
                    else:
                        parts.append('<span class="file-option">–</span>')
                parts.append("</td>")
        parts.append("</tr>")
    parts.append("</tbody>")
    return "\n".join(parts)


def main() -> None:
    start, end = load_range()
    competitions = range(end, start - 1, -1)
    years = [year_label(competition) for competition in competitions]
    available: list[str] = []
    existing_names: set[str] = set()

    for competition in competitions:
        year = FIRST_COMPETITION_YEAR + competition
        label = year_label(competition)
        for level, _, level_slug in LEVELS:
            for grade in GRADES:
                for file_type, type_slug, _ in TYPES:
                    name = filename(year, level_slug, grade, type_slug)
                    if (ROOT / "natjecanja" / name).is_file():
                        existing_names.add(name)
                        available.append(f"{label}|{level}|{grade}|{file_type}")

    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    output = (
        template.replace("<!-- GENERATED_TABLE -->", make_table(years, existing_names))
        .replace("__GENERATED_YEARS__", json.dumps(years, ensure_ascii=False))
        .replace("__GENERATED_FILES__", json.dumps(available, ensure_ascii=False))
    )
    if "__GENERATED_" in output or "<!-- GENERATED_TABLE -->" in output:
        raise ValueError("The index template has an unfilled generated-content marker.")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(COMPETITIONS_DIR, OUTPUT_FILE.parent / "natjecanja", dirs_exist_ok=True)
    OUTPUT_FILE.write_text(output, encoding="utf-8")
    print(
        f"Created {OUTPUT_FILE.relative_to(ROOT)} "
        f"for competition numbers {start}–{end}; "
        f"found {len(available)} files."
    )


if __name__ == "__main__":
    main()
