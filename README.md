# Courtroom AI — Watch a Legal Case Play Out, Argument by Argument

## What is this, in one sentence?

You type in a complaint — like you're filing a police report or a legal grievance — and this system runs it through an entire simulated Indian court proceeding: intake, legal research, internal strategy, prosecution vs. defense arguments, a judge's verdict, and a final written report, with every step appearing live as it's written.

```
  📝 "Someone crashed into my shop and ran off..."
            │
            ▼
   ⚖️  Full simulated proceeding
            │
            ▼
  📰 Verdict + confidence score + full report
```

This isn't a real legal system and doesn't give real legal advice — it's a simulation that shows *how* a case would likely be reasoned through, using India's current criminal law framework (the Bharatiya Nyaya Sanhita, Bharatiya Nagarik Suraksha Sanhita, and Bharatiya Sakshya Adhiniyam — the 2023 laws that replaced the old IPC, CrPC, and Evidence Act).

---

## The idea a user should really appreciate: nobody writes the whole case at once

Instead of asking one AI to "write a courtroom drama," this system breaks the job into ten separate roles — each one a focused, narrow task, done by a different "agent" that only sees what it needs to see. This mirrors how a real proceeding actually unfolds: a case doesn't leap straight from a complaint to a verdict — it goes through people who each add one piece.

```
📝 Complaint
   │
   ▼
📂 Case Manager       →  pulls out who's accused, who's the victim, what happened
   │
   ▼
📚 Legal Research      →  finds the relevant laws & precedents (with live web search)
   │
   ▼
🧭 Consultant          →  a first read on how strong the case looks
   │
   ▼
⚔️ Prosecutor (Round 1) →  opening argument for guilt
   │
   ▼
🛡️ Defense (Round 1)    →  opening rebuttal
   │
   ▼
⚔️ Prosecutor (Round 2) →  closing argument
   │
   ▼
🛡️ Defense (Round 2)    →  closing rebuttal
   │
   ▼
⚖️ Judge               →  verdict, reasoning, confidence score, likely punishment
   │
   ▼
🖋️ Reporter            →  turns everything into one final case report
   │
   ▼
🏛️ Top Consultant       →  a closing strategic/executive-level take on the whole case
```

Each box above is a separate, focused call — the "Case Manager" never argues anyone's guilt, and the "Judge" never invents facts that weren't established earlier. Everyone works from the same growing case file, so the story stays internally consistent from the first line to the verdict.

---

## Two kinds of answers: structured facts vs. persuasive writing

A detail worth understanding: not every agent answers the same way.

| Style | Used by | What comes out |
|---|---|---|
| **Structured** | Case Manager, Legal Research, Judge | Clean, predictable fields — like a form: "accused: ___, victim: ___, verdict: Guilty, confidence: 78" |
| **Free-form prose** | Consultant, Top Consultant, Prosecutor, Defense, Reporter | Actual written argument or narrative, like a real filed brief |

This split exists because some outputs *need* to be reliable and predictable (you don't want a "verdict" field to sometimes come back as a paragraph instead of one clear word), while persuasive legal argument reads badly if it's forced into rigid boxes — a prosecutor's closing argument needs to flow like actual advocacy, not a filled-out form.

---

## Meet the agents

**📂 Case Manager** — the intake officer. Reads your raw, messy complaint and turns it into a clean case file: who's accused, who's the alleged victim, what's alleged to have happened, what offences seem to apply, and — importantly — what information is *missing* that the case will need later. This agent explicitly does **not** judge guilt or innocence; its only job is turning your free text into structured facts.

**📚 Legal Research** — given the case facts, this agent identifies which statutory sections might apply, digs up precedent cases, and notes any evidentiary issues — assisted by live web search, so it isn't limited to whatever it memorized during training.

**🧭 Consultant** — an internal, quick strategic read: how strong does this case look, from either side's perspective, before the formal arguments even start?

**🏛️ Top Consultant** — a second, deeper pass at the *end* of the whole case — an executive-level advisory review of everything that happened, not just the opening take.

**⚔️ Prosecutor** and **🛡️ Defense** — each argue their side across two rounds (an opening argument and a closing rebuttal), the way a real trial builds toward its conclusion rather than being decided in one shot.

**⚖️ Judge** — reads everything that came before (the facts, the research, both sides' arguments) and delivers a structured verdict: Guilty / Not Guilty / Partially Liable, the reasoning behind it, which legal sections were applied, the likely punishment if guilty, and a confidence score from 0–100 — because real judicial reasoning is rarely 100% certain, and pretending otherwise would be misleading.

**🖋️ Reporter** — takes the verdict and the entire case history and writes it up as a single polished, readable case report — the kind of document you could actually hand someone to explain what happened and why.

---

## Watching it happen live, not waiting for one big answer

The system streams each agent's output to you the moment it's ready — you see the Case Manager's findings appear first, then Legal Research, then each argument round, then the verdict — instead of staring at a loading spinner for a minute and getting one giant wall of text at the end. This uses a streaming technology (Server-Sent Events) so the frontend can display progress in real time, agent card by agent card.

---

## The two halves: simulation engine vs. the screen you look at

Just like a real courtroom has "what happens" and "how it's reported to the public," this project cleanly separates:

- **The backend** owns the entire simulation: the sequence of agents (built using a tool called LangGraph, which manages "who runs after whom" as a state machine), every prompt, every AI call, and the tracing that records what happened.
- **The frontend** is only a window into that simulation — it takes your typed complaint, sends it to the backend, and renders whatever comes back, live, as agent cards. It also lets you export the final report and view a scoring dashboard.

```
   🎨 Frontend (what you see)          ⚙️ Backend (what actually runs the case)
   ┌────────────────────┐              ┌──────────────────────────────┐
   │ Complaint box       │──HTTP/SSE──▶│ LangGraph pipeline of agents  │
   │ Live agent cards     │◀───────────│ Groq (the AI that writes)      │
   │ Report export         │            │ Tavily (live legal web search)  │
   │ Metrics dashboard      │            │ Langfuse (traces every call)     │
   └────────────────────┘              └──────────────────────────────┘
```

Because of this split, the backend could be reused by a totally different interface later — a command-line tool, a different app — without touching any of the actual legal-reasoning logic.

---

## Two very different kinds of "quality check" — worth not confusing

This project tracks quality in two separate, unrelated ways:

1. **Observability (Langfuse tracing)** — every single AI call, from every agent, is automatically logged: the exact prompt sent, the exact response, how long it took, and how many tokens it used. This is a *technical* record of what happened during one run — useful for debugging or understanding cost/latency, not for judging whether the *legal reasoning* was any good.

2. **Metrics dashboard (local scoring)** — a separate, non-AI scoring system that looks at a *finished* simulation and rates it on completeness, coherence, and rough legal accuracy, using simple local heuristics rather than another AI call judging the first AI's work.

In short: tracing tells you *what happened*; the metrics dashboard tells you *how good the result was*. They answer different questions and shouldn't be confused with each other.

---

## Why a fixed sequence, not a "choose your own adventure" AI

Some AI systems let the model freely decide what to do next at every step. This one deliberately doesn't — the order (Case Manager → Legal Research → Consultant → arguments → Judge → Reporter → Top Consultant) is fixed and always the same, because a courtroom proceeding *is* a fixed sequence in real life. You don't get a defense rebuttal before the case facts are even established. Removing that unpredictability makes every run reliably structured and easy to follow, at the cost of never letting the AI "skip ahead" or improvise the order — which is exactly the trade-off you'd want for something meant to resemble an actual legal process.

---

## What this is genuinely useful for

- Seeing how a set of facts might be argued from both sides, before you ever set foot near a real legal process
- Understanding which statutory sections and precedents an AI thinks are relevant to a fact pattern, with citations you can go verify yourself
- Watching multi-step AI reasoning unfold transparently, one accountable role at a time, rather than as an opaque single response

## What it is not

- Not a source of actual legal advice — always consult a real lawyer for real legal matters
- Not a database of guaranteed-accurate case law — the "Legal Research" agent does live web searches, but its findings should be verified independently
- Not a predictor of real court outcomes — it's a structured simulation meant to illustrate how legal reasoning chains together, not a forecasting tool

## License

This project is licensed under the Apache License 2.0.

If you use or redistribute this project, you must preserve the copyright notice and license, and indicate any modifications made.