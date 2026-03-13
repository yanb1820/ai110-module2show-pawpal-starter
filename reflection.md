# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The system centers on four classes connected in a clear hierarchy:

| Class | Responsibility |
|---|---|
| `Owner` | Holds owner name, daily available minutes, and care preferences. Owns a list of `Pet` objects. |
| `Pet` | Holds pet name, species, age, and special needs. Owns a list of `Task` objects. |
| `Task` | Dataclass representing a single care action (title, duration, priority, type, preferred time). Pure data — no scheduling logic. |
| `Scheduler` | Aggregates an `Owner` (and transitively all pets + tasks) and produces a `list[ScheduledItem]` via a greedy, priority-first algorithm. Also provides a plain-English `explain_plan()` output. |

A `ScheduledItem` dataclass acts as the output unit — it pairs a `Task` with the `Pet` it belongs to and a computed start time.

Relationships:
- `Owner` 1 → * `Pet`
- `Pet` 1 → * `Task`
- `Scheduler` aggregates `Owner` → reads all pets/tasks → emits `[ScheduledItem]`

Three core user actions the system supports:
1. Add a pet (with profile info) to an owner.
2. Add/edit care tasks for a pet (duration, priority, type).
3. Generate and view a daily schedule with reasoning for each scheduled task.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
