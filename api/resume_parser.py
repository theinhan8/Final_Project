from docx import Document
import PyPDF2
import re

def parse_resume(file_path):
    data = {
        "personal": {},
        "education": [],
        "experience": [],
        "skills": {},
        "projects": []
    }

    # -----------------------------
    # Extract text from PDF or DOCX
    # -----------------------------
    if file_path.endswith(".pdf"):
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    else:
        doc = Document(file_path)
        text = "\n".join(p.text for p in doc.paragraphs)

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # -----------------------------
    # Section detection
    # -----------------------------
    section = None
    buffer = []

    def flush_experience():
        """Parses a job block into structured data."""
        if not buffer:
            return
        entry = {
            "header": buffer[0],
            "details": buffer[1:]
        }
        data["experience"].append(entry)

    def flush_education():
        if buffer:
            data["education"].append(" ".join(buffer))

    def flush_project():
        if buffer:
            data["projects"].append(" ".join(buffer))

    for line in lines:

        # Detect section headers
        if line.upper() in ["PERSONAL INFORMATION", "PERSONAL"]:
            section = "personal"
            continue
        elif line.upper() == "EDUCATION":
            section = "education"
            buffer = []
            continue
        elif line.upper() in ["WORK EXPERIENCE", "EXPERIENCE"]:
            section = "experience"
            buffer = []
            continue
        elif line.upper() == "SKILLS":
            section = "skills"
            continue
        elif line.upper() == "PROJECTS":
            section = "projects"
            buffer = []
            continue

        # -----------------------------
        # PERSONAL INFORMATION SECTION
        # -----------------------------
        if section == "personal":
            key_val = line.split(":", 1)
            if len(key_val) == 2:
                key = key_val[0].strip()
                val = key_val[1].strip()
                data["personal"][key] = val
            continue

        # -----------------------------
        # EDUCATION SECTION
        # -----------------------------
        if section == "education":
            if re.match(r".*\d{4}", line):  # line containing dates
                flush_education()
                buffer = [line]
            else:
                buffer.append(line)
            continue

        # -----------------------------
        # EXPERIENCE SECTION
        # -----------------------------
        if section == "experience":
            # Detect start of new job by date pattern
            if re.search(r"\d{4}", line):
                flush_experience()
                buffer = [line]
            else:
                buffer.append(line)
            continue

        # -----------------------------
        # SKILLS SECTION
        # -----------------------------
        if section == "skills":
            if ":" in line:
                key, val = line.split(":", 1)
                data["skills"][key.strip()] = [v.strip() for v in val.split(",")]
            continue

        # -----------------------------
        # PROJECTS SECTION
        # -----------------------------
        if section == "projects":
            if "Technologies Used:" in line:
                buffer.append(line)
                flush_project()
                buffer = []
            else:
                buffer.append(line)
            continue

    # Flush remaining buffers
    flush_education()
    flush_experience()
    flush_project()

    return data
