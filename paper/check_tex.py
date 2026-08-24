"""Static sanity check on the LaTeX source (no TeX toolchain required)."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
src = (HERE / "main.tex").read_text(encoding="utf-8")
# inline \input{...} files so labels/tables defined there are seen
for inc in re.findall(r"\\input\{([^}]+)\}", src):
    f = HERE / (inc if inc.endswith(".tex") else inc + ".tex")
    if f.exists():
        src += "\n" + f.read_text(encoding="utf-8")
bib = (HERE / "custom.bib").read_text(encoding="utf-8")

ok = True
print("begin/end document:", src.count(r"\begin{document}"), src.count(r"\end{document}"))

for env in ["table", "table*", "figure", "figure*", "tabular", "itemize", "abstract"]:
    b = len(re.findall(r"\\begin\{" + re.escape(env) + r"\}", src))
    e = len(re.findall(r"\\end\{" + re.escape(env) + r"\}", src))
    flag = "OK" if b == e else "*** MISMATCH ***"
    if b != e:
        ok = False
    print(f"  {env:9} begin={b} end={e}  {flag}")

nb, nc = src.count("{"), src.count("}")
print("braces balanced:", nb == nc, nb, nc)
ok &= (nb == nc)

labs = set(re.findall(r"\\label\{([^}]+)\}", src))
refs = set(re.findall(r"\\ref\{([^}]+)\}", src))
print("undefined refs:", refs - labs or "none")
print("unused labels:", labs - refs or "none")
ok &= not (refs - labs)

keys = set()
for c in re.findall(r"\\cite[a-z]*\{([^}]+)\}", src):
    keys.update(k.strip() for k in c.split(","))
bibkeys = set(re.findall(r"@\w+\{([^,]+),", bib))
print("cited keys missing from bib:", keys - bibkeys or "none")
print("bib entries never cited:", bibkeys - keys or "none")
ok &= not (keys - bibkeys)

for f in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", src):
    p = HERE / f
    exists = p.exists() or p.with_suffix(".pdf").exists()
    print(f"  graphic {f}: {'found' if exists else '*** MISSING ***'}")
    ok &= exists

print("\nRESULT:", "PASS" if ok else "FAIL")
