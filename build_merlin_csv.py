import re
from pathlib import Path
import pandas as pd

# Pfad zu deinem Ordner mit den Metadateien
META_DIR = Path(r"C:\Users\Küchenheld\Downloads\merlin-text-v1.2\merlin-text-v1.2\meta_ltext\german_metafn")

# Regex: CEFR-Level am Dateianfang, z.B. "B2_-_..."
LEVEL_RE = re.compile(r"^(A1|A2|B1|B2|C1|C2)_-_", re.IGNORECASE)

rows = []

for path in META_DIR.glob("*.txt"):
    fname = path.name

    # 1) Level grob aus dem Dateinamen holen (nur für Kontrolle)
    m = LEVEL_RE.match(fname)
    level_from_name = m.group(1).upper() if m else None

    with path.open(encoding="utf-8") as f:
        lines = f.read().splitlines()

    cefr_overall = None
    learner_text_lines = []
    in_text = False

    for line in lines:
        # a) Overall CEFR rating aus Metadaten
        if line.startswith("Overall CEFR rating:"):
            # z.B. "Overall CEFR rating: B2"
            cefr_overall = line.split(":", 1)[1].strip().upper()

        # b) Ab "Learner text:" beginnt der eigentliche Text
        elif line.startswith("Learner text"):
            in_text = True
            continue
        elif in_text:
            learner_text_lines.append(line)

    text = "\n".join(learner_text_lines).strip()

    if not cefr_overall:
        print(f"WARNUNG: kein Overall CEFR rating in {fname} (Level im Namen: {level_from_name})")
        continue
    if not text:
        print(f"WARNUNG: kein Lernertext in {fname}")
        continue

    rows.append({
        "id": fname,
        "cefr": cefr_overall,        # das nutzen wir fürs Training
        "cefr_from_name": level_from_name,  # optional zum Gegenchecken
        "text": text,
    })

df = pd.DataFrame(rows)
df.to_csv("merlin_de.csv", index=False, encoding="utf-8")
print("Fertig. Geschrieben: merlin_de.csv mit", len(df), "Zeilen.")
