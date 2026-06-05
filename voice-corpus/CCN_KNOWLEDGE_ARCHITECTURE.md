# CCN Knowledge Architecture
## The Conscious Christianity Information System
**Author:** Pastor Carlos "M.C. DaNova" Villanueva Cortés  
**Ministry:** Conscious Culture NOW! (CCN)  
**System:** N.O.A.H. — Networked Orchestration Automation Hub  
**Date Established:** June 1, 2026  

---

## Purpose

An organized mind is a hallmark of Conscious Christianity.  
Just as Jesus taught through parables — structured, purposeful, layered —  
our knowledge system must reflect that same divine order.

This architecture governs how all CCN content is classified,  
retrieved, and applied by Hermes and future N.O.A.H. agents.

*"Let all things be done decently and in order."*  
— 1 Corinthians 14:40 KJV

---

## The Five Dimensions

### DIMENSION 1 — Time
**Field:** `date_published` (YYYYMMDD integer) | `year` (YYYY integer)  
**Purpose:** Hermes knows the difference between old thinking and current revelation.  
Early content is historical context. Recent content is active ministry.  
Time-awareness prevents Hermes from presenting past positions as current ones.

```
2025 → Early CCN formation period
2026 → Current operational ministry
```

---

### DIMENSION 2 — Source Type (The Dewey Layer)
**Field:** `content_type` | `content_label`  
**Purpose:** Every piece of knowledge knows what it is and where it came from.

| content_type | content_label | Description |
|---|---|---|
| `book` | Superposición Book 1 | Published theological fiction — primary voice |
| `magazine` | La Fortaleza Magazine PR | Monthly CCN magazine — Issues 1-14+ |
| `video_transcript` | YouTube / Video Transcript | Spoken ministry — episodes, testimonies |
| `blog` | faaaith.org Blog | Written theological commentary |
| `website` | faaaith.org Website | Ministry platform content |
| `testimony` | Personal Testimony | Direct personal narrative *(future)* |
| `archive` | Web Archive | Historical web captures |
| `profile` | Speaker / Author Profile | Third-party platform presence |
| `reference` | Reference Material | Supporting documents |

---

### DIMENSION 3 — Language
**Field:** `language`  
**Purpose:** Bilingual ministry requires bilingual intelligence.  
Content stays in its original language — never merged, never auto-translated.  
Agents are configured per audience, not per document.

| Value | Meaning |
|---|---|
| `EN` | English content |
| `ES` | Spanish content |
| `UNK` | Unknown / decorative / too short to detect |

---

### DIMENSION 4 — Subject *(Planned — Phase 2)*
**Field:** `topic`  
**Purpose:** Filter retrieval by theological or ministry domain.  
Agents specialized in one domain pull only relevant knowledge.

| topic | Description |
|---|---|
| `theology` | KJV Bible doctrine, spiritual warfare, quantum faith |
| `economics` | CCN economic models, Puerto Rico development |
| `hip-hop` | HIP HOP iz HOPE, culture redemption, MC DaNova |
| `quantum` | Superposition theory, quantum entanglement framework |
| `testimony` | Personal narrative, DaNova story |
| `puerto-rico` | Island-specific content, La Fortaleza context |
| `automation` | N.O.A.H., Hermes, Kingdom OS |

---

### DIMENSION 5 — Authority Level *(Planned — Phase 2)*
**Field:** `authority`  
**Purpose:** Not all content carries equal weight.  
DaNova's own words carry primary authority.  
Interviews and third-party coverage are secondary.  
Reference material is contextual only.

| authority | Description |
|---|---|
| `primary` | Carlos DaNova's direct words — books, blogs, video |
| `secondary` | Interviews, magazine features about CCN |
| `reference` | Supporting research, external sources |

---

## Implementation Status

| Dimension | Status | Notes |
|---|---|---|
| Time | ✅ Active | `date_published` + `year` in ChromaDB |
| Source Type | ✅ Active | `content_type` + `content_label` in ChromaDB |
| Language | ✅ Active | `language` in ChromaDB |
| Subject | 🔜 Phase 2 | Requires manual tagging or LLM classification |
| Authority | 🔜 Phase 2 | Requires manual tagging per source |

---

## Agent Usage Guidelines

**Social / Marketing Agent**
→ Pull from: `magazine`, `blog`, `video_transcript`  
→ Language: match audience (EN or ES)  
→ Authority: `primary` preferred  

**Theology / Teaching Agent**
→ Pull from: `book`, `blog`, `video_transcript`  
→ Topic filter: `theology`, `quantum`  
→ Authority: `primary` only  

**Operations / Business Agent**
→ Pull from: `website`, `magazine`, `reference`  
→ Topic filter: `economics`, `automation`  

**All Agents**
→ Respect Time dimension — weight recent content higher  
→ Never mix EN and ES in same response unless bilingual output requested  
→ Always cite `content_label` and `source_url` when available  

---

## File Location
`/root/hermes-ccnow/voice-corpus/CCN_KNOWLEDGE_ARCHITECTURE.md`  
`/root/.hermes/memories/CCN_KNOWLEDGE_ARCHITECTURE.md` *(copy for Hermes memory)*

---

*Conscious Culture NOW! — Building Kingdom intelligence with divine order.*  
*4 JESUS 4 PROFIT — Rapture or Revival*
