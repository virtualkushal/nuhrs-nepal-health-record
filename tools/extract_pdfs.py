from pypdf import PdfReader

for name in ["final_report (3).pdf", "main (7).pdf"]:
    r = PdfReader("/docs/" + name)
    out = "/docs/" + name.replace(".pdf", ".txt").replace(" ", "_")
    with open(out, "w", encoding="utf-8") as f:
        for i, page in enumerate(r.pages):
            f.write(f"--- PAGE {i+1} ---\n" + (page.extract_text() or "") + "\n")
    print(name, "->", len(r.pages), "pages")
