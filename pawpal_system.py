"""
PawPal+ — backend logic layer.

UML relationships:
    Owner  1 ──< *  Pet
    Pet    1 ──< *  Task
    Scheduler aggregates Owner + Pet + [Task] → Schedule
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskType(str, Enum):
    WALK = "walk"
    FEEDING = "feeding"
    MEDICATION = "medication"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Task  (dataclass — lightweight, no custom __init__ needed)
# ---------------------------------------------------------------------------

@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority
    task_type: TaskType = TaskType.OTHER
    preferred_time: Optional[str] = None   # e.g. "morning", "evening"
    notes: str = ""
    completed: bool = False

    def is_urgent(self) -> bool:
        """Return True when this task must appear in any daily plan."""
        return self.priority == Priority.HIGH

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def __repr__(self) -> str:
        status = "✓" if self.completed else "○"
        return (
            f"Task({status} {self.title!r}, {self.duration_minutes}min, "
            f"{self.priority.value}, type={self.task_type.value})"
        )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

class Pet:
    def __init__(
        self,
        name: str,
        species: str,
        age_years: float = 0.0,
        special_needs: Optional[list[str]] = None,
    ) -> None:
        self.name = name
        self.species = species
        self.age_years = age_years
        self.special_needs: list[str] = special_needs or []
        self._tasks: list[Task] = []

    # -- task management -------------------------------------------------

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        self._tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove the first task whose title matches (case-insensitive)."""
        self._tasks = [t for t in self._tasks if t.title.lower() != title.lower()]

    def get_tasks(self) -> list[Task]:
        """Return all tasks assigned to this pet."""
        return self._tasks

    def __repr__(self) -> str:
        return f"Pet({self.name!r}, species={self.species!r}, age={self.age_years})"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    def __init__(
        self,
        name: str,
        available_minutes: int = 120,
        preferences: Optional[list[str]] = None,
    ) -> None:
        self.name = name
        self.available_minutes = available_minutes          # total free time today
        self.preferences: list[str] = preferences or []   # e.g. ["morning walks", "no evening meds"]
        self._pets: list[Pet] = []

    # -- pet management --------------------------------------------------

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self._pets.append(pet)

    def get_pets(self) -> list[Pet]:
        """Return all pets registered to this owner."""
        return self._pets

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (pet, task) pair across all pets — used by Scheduler."""
        return [(pet, task) for pet in self._pets for task in pet.get_tasks()]

    def __repr__(self) -> str:
        return f"Owner({self.name!r}, available={self.available_minutes}min, pets={len(self._pets)})"


# ---------------------------------------------------------------------------
# ScheduledItem  (one slot in the final plan)
# ---------------------------------------------------------------------------

@dataclass
class ScheduledItem:
    task: Task
    pet: Pet
    start_minute: int       # minutes from midnight, e.g. 480 = 8:00 AM
    reason: str = ""

    @property
    def end_minute(self) -> int:
        return self.start_minute + self.task.duration_minutes

    def time_label(self) -> str:
        """Human-readable start time, e.g. '8:00 AM'."""
        h, m = divmod(self.start_minute, 60)
        period = "AM" if h < 12 else "PM"
        h12 = h % 12 or 12
        return f"{h12}:{m:02d} {period}"

    def __repr__(self) -> str:
        return (
            f"ScheduledItem({self.task.title!r} for {self.pet.name!r} "
            f"@ {self.time_label()}, +{self.task.duration_minutes}min)"
        )


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Builds a daily care schedule for one owner and one (or more) pets.

    Strategy:
        1. Collect all tasks across all owner's pets.
        2. Sort by priority (HIGH first), then duration (shorter first).
        3. Greedily assign tasks until available_minutes is exhausted.
        4. Respect preferred_time hints when placing start times.
    """

    # Anchor start minutes for preferred-time slots
    _TIME_ANCHORS: dict[str, int] = {
        "morning": 7 * 60,    # 7:00 AM
        "afternoon": 13 * 60, # 1:00 PM
        "evening": 18 * 60,   # 6:00 PM
    }
    _DEFAULT_START = 8 * 60   # 8:00 AM

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self._schedule: list[ScheduledItem] = []

    # -- public API ------------------------------------------------------

    def build_schedule(self) -> list[ScheduledItem]:
        """Generate and return the daily schedule."""
        self._schedule = []

        # Owner.get_all_tasks() is the single access point: Scheduler never
        # reaches into Pet directly — it always goes through Owner.
        candidates: list[tuple[Pet, Task]] = self.owner.get_all_tasks()

        priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        candidates.sort(key=lambda pt: (priority_order[pt[1].priority], pt[1].duration_minutes))

        minutes_used = 0
        next_start = {**self._TIME_ANCHORS, "default": self._DEFAULT_START}

        for pet, task in candidates:
            if minutes_used + task.duration_minutes > self.owner.available_minutes:
                continue

            slot = task.preferred_time or "default"
            start = next_start.get(slot, self._DEFAULT_START)

            item = ScheduledItem(task=task, pet=pet, start_minute=start, reason=self._build_reason(task))
            self._schedule.append(item)

            next_start[slot] = start + task.duration_minutes
            minutes_used += task.duration_minutes

        return self._schedule

    def explain_plan(self) -> str:
        """Return a human-readable explanation of the schedule."""
        if not self._schedule:
            return "No schedule generated yet. Call build_schedule() first."

        lines = [f"Daily plan for {self.owner.name}\n" + "=" * 40]
        for item in sorted(self._schedule, key=lambda x: x.start_minute):
            lines.append(
                f"  {item.time_label()}  [{item.task.priority.value.upper()}]  "
                f"{item.task.title} ({item.task.duration_minutes} min) — {item.pet.name}\n"
                f"    ↳ {item.reason}"
            )
        total = sum(i.task.duration_minutes for i in self._schedule)
        lines.append(f"\nTotal scheduled: {total} min / {self.owner.available_minutes} min available")
        return "\n".join(lines)

    # -- private helpers -------------------------------------------------

    def _build_reason(self, task: Task) -> str:
        """Generate a plain-English justification for scheduling this task."""
        reasons = []
        if task.priority == Priority.HIGH:
            reasons.append("high priority — must be done today")
        elif task.priority == Priority.MEDIUM:
            reasons.append("medium priority — fits within available time")
        else:
            reasons.append("low priority — included because time permits")

        if task.preferred_time:
            reasons.append(f"preferred in the {task.preferred_time}")

        if task.task_type == TaskType.MEDICATION:
            reasons.append("medication tasks are time-sensitive")

        return "; ".join(reasons)

    def __repr__(self) -> str:
        return f"Scheduler(owner={self.owner.name!r}, items={len(self._schedule)})"
