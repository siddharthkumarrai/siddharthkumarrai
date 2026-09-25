"""Assemble README.md for the GitHub profile.

Run: python tools/build_readme.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# --- README template: part 1 — two-column display (ASCII + description) --------
P1 = """
<div>
  <picture>
    <source media="(max-width: 640px)" srcset="./assets/siddharth-face-scan-mobile.gif">
    <source media="(max-width: 1024px)" srcset="./assets/siddharth-face-scan-tablet.gif">
    <img src="./assets/siddharth-face-scan.gif" alt="ASCII biometric face scan of Siddharth Kumar Rai" width="440" align="left">
  </picture>
  <h2>Siddharth Kumar Rai</h2>
      <p><b>Product Engineer · Agentic AI &amp; Full-Stack · IoT &amp; Edge Automation</b></p>
</div>

<p>
        Final-semester <b>BCA</b> student (IGNOU, Grade A++) freelancing as
        <b>Product Engineer · Electronics &amp; IoT</b> at <b>acreativestudios</b>.
        I don't just write code — I build complete, intelligent ecosystems from
        the ground up: <b>AI pipelines</b>, <b>backend systems</b>,
        <b>hardware automation</b> and <b>UI architecture</b>, all working
        together end to end.
      </p>
      <p>
        <b>Currently building</b><br/>
        🤖 <b>Sidd-V2</b> — local-first autonomous AI agent<br/>
        🦾 <b>VIEON</b> — tri-node embodied AI (ESP32 + Android + PC)<br/>
        🧩 <b>SkillsLMS</b> — full-stack learning platform
      </p>
      <p>
        <b>./scan --biometric</b> — live ASCII scan rendered from
        <code>assets/sidd image.jpeg</code> · regenerate:
        <code>python tools/generate_face_ascii.py</code><br/>
        📍 Greater Delhi Area, India · ✅ <b>open_to_work</b>
      </p>
      <p>
        <a href="https://github.com/siddharthkumarrai">GitHub</a> ·
        <a href="https://www.linkedin.com/in/siddharth-kumar-rai/">LinkedIn</a> ·
        <a href="https://siddyadav.vercel.app/">Portfolio</a> ·
        <a href="https://instagram.com/siddharthkumarrai777">Instagram</a> ·
        <a href="mailto:siddharthkumarrairai@gmail.com">Email</a>
      </p>
<br clear="all"/>

---
"""

# --- part 2 — whoami ----------------------------------------------------------
P2 = """
### `./whoami`

```text
siddharth@world:~$ whoami
> ready_to_build --mode=agentic

📍 Location   : Greater Delhi Area, India
🎓 Education  : BCA (Software Technology), IGNOU — Grade A++
🎯 Focus      : Agentic AI · Full-Stack Dev · IoT Automation
💼 Currently  : Product Engineer (Freelance) @ acreativestudios
🔗 Portfolio  : siddyadav.vercel.app
📧 Email      : siddharthkumarrairai@gmail.com
✅ status     : open_to_work
```

---
"""
# --- part 3 — about + stack --------------------------------------------------
P3 = """
### `./about`

<div align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&duration=3000&pause=700&color=45F5C7&center=true&vCenter=true&width=680&lines=Hi+there!+I%27m+Siddharth+Kumar+Rai;Software+Developer+%26+Creative+Technologist;Let%27s+build+intelligent+ecosystems" alt="Hi there, I am Siddharth Kumar Rai">
</div>

> I don't just write code — I build complete, intelligent ecosystems from the
> ground up: **AI pipelines**, **backend systems**, **hardware automation**,
> and **UI architecture**, all working together.
>
> Final-semester **BCA** student (IGNOU), freelancing as **Product Engineer ·
> Electronics & IoT** at **acreativestudios**. Community Leader at
> **CodeWithSidd**. Open to full-time roles.

```text
current_focus :
  - Agentic AI ..... LangChain · LangGraph · ChromaDB
  - Data / API ..... NumPy · Pandas · FastAPI
  - Product ........ Sidd-V2  (autonomous local-first AI agent)
  - Product ........ VIEON    (tri-node embodied AI · ESP32 + Android + PC)
  - Product ........ SkillsLMS (full-stack learning platform)
  - Building ....... reusable UI component library (WIP)
```

---

### `./stack`

<p align="center">
  <img src="https://skillicons.dev/icons?i=js,ts,react,nextjs,nodejs,express,python,fastapi,docker,git,github,mongodb,postgres,redis,linux,vercel&perline=8" alt="Core stack">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/LangChain-45F5C7?style=for-the-badge&logo=langchain&logoColor=black" alt="LangChain">
  <img src="https://img.shields.io/badge/LangGraph-45F5C7?style=for-the-badge&logo=langchain&logoColor=black" alt="LangGraph">
  <img src="https://img.shields.io/badge/ChromaDB-FF6B4A?style=for-the-badge&logoColor=white" alt="ChromaDB">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/GraphQL-E10098?style=for-the-badge&logo=graphql&logoColor=white" alt="GraphQL">
  <img src="https://img.shields.io/badge/React_Native-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React Native">
  <img src="https://img.shields.io/badge/Rust-000000?style=for-the-badge&logo=rust&logoColor=white" alt="Rust">
  <img src="https://img.shields.io/badge/ESP32-000000?style=for-the-badge&logoColor=white" alt="ESP32">
</p>

---
"""

# --- part 4 — experience + featured builds -----------------------------------
P4 = """
### `./experience`

| Role | Company | Duration |
| :-- | :-- | :-- |
| **Product Engineer · Electronics & IoT** (Freelance) | acreativestudios | Feb 2025 – Present |
| Web Development Intern | Arista Vault Mw (Arivation Fashiontech) | Mar 2025 – Jun 2025 |
| Web Developer (Freelance) | Agnus Media | May 2024 – Jul 2024 |
| Backend Developer Intern | Sponsorgram | Mar 2024 – May 2024 |

---

### `./featured-builds`

<h3 align="center">🧩 SkillsLMS</h3>
      <p align="center">Full-stack modern learning management system.</p>
      <p align="center">
        <a href="https://skillslms.vercel.app"><img src="https://img.shields.io/badge/-Live-45F5C7?style=flat-square&logo=vercel&logoColor=black" alt="Live"></a>
        <a href="https://github.com/siddharthkumarrai/LMS"><img src="https://img.shields.io/badge/-Repo-9aa7a3?style=flat-square&logo=github&logoColor=white" alt="Repo"></a>
      </p>

---

<h3 align="center">🤖 Sidd-V2</h3>
      <p align="center">Local-first autonomous AI agent — Android edge node + Rust WebSocket server.</p>
      <p align="center">
        <a href="https://github.com/siddharthkumarrai/sidd-v2-assets"><img src="https://img.shields.io/badge/-Model%20Assets-9aa7a3?style=flat-square&logo=github&logoColor=white" alt="Model assets"></a>
      </p>

---

<h3 align="center">🦾 VIEON</h3>
      <p align="center">Tri-node embodied AI — ESP32 humanoid + Android + PC.</p>
      <p align="center">
        <a href="https://github.com/siddharthkumarrai/-VIEON-Voice-Integrated-Embodied-Omni-Network"><img src="https://img.shields.io/badge/-Repo-9aa7a3?style=flat-square&logo=github&logoColor=white" alt="Repo"></a>
      </p>

---
"""

# --- part 5 — stats, contact, footer -----------------------------------------
P5 = """
### `./stats`

<p align="center">
  <img src="./profile-summary-card-output/tokyonight/3-stats.svg" height="165" alt="GitHub stats">
  <img src="./profile-summary-card-output/tokyonight/2-most-commit-language.svg" height="165" alt="Top languages">
</p>

<p align="center">
  <img src="./profile-summary-card-output/tokyonight/1-repos-per-language.svg" height="165" alt="Repos per language">
  <img src="./profile-summary-card-output/tokyonight/4-productive-time.svg" height="165" alt="Productive time">
</p>

<p align="center">
  <img src="https://streak-stats.demolab.com/?user=siddharthkumarrai&theme=tokyonight&hide_border=true" alt="GitHub streak">
</p>

---

### `./contact`

```text
github   : github.com/siddharthkumarrai
linkedin : linkedin.com/in/siddharth-kumar-rai
web      : siddyadav.vercel.app
email    : siddharthkumarrairai@gmail.com
```

---

<div align="center">
  <p><i>"Build things. Break things. Learn why."</i></p>
  <sub>scanned in ASCII · © 2026 Siddharth Kumar Rai</sub>
  <br/>
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:0a0f14,50:0d151c,100:101922&height=110&section=footer" alt="footer wave" width="100%">
</div>
"""


# ---------------------------------------------------------------------------
def main() -> None:
    readme = P1 + P2 + P3 + P4 + P5
    out = ROOT / "README.md"
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(readme)
    fences = sum(1 for ln in readme.splitlines() if ln.startswith("```"))
    print(
        f"wrote {out.name}: {len(readme)} chars, "
        f"{len(readme.splitlines())} lines, {fences} fence markers"
    )


if __name__ == "__main__":
    main()
