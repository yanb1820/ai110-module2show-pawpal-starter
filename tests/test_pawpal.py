"""
tests/test_pawpal.py — core behaviour tests for PawPal+

── Failing test scenario (for teaching) ────────────────────────────────────────
A common student mistake is assuming get_tasks() returns a copy, then checking
that mutating it doesn't affect the pet. This test WOULD FAIL because get_tasks()
returns the internal list directly, so mutations do affect the pet:

    def test_get_tasks_returns_copy():  # ← FAILS
        pet = Pet("Mochi", "dog")
        pet.add_task(Task("Walk", 30, Priority.HIGH))
        snapshot = pet.get_tasks()
        snapshot.clear()                        # mutate the returned list
        assert len(pet.get_tasks()) == 1        # AssertionError: 0 != 1

Why it fails: get_tasks() returns self._tasks directly (not a copy), so
snapshot IS the internal list. Clearing it empties the pet's task storage.
Fix: either return list(self._tasks) in get_tasks(), or don't mutate
the returned list in application code.
────────────────────────────────────────────────────────────────────────────────
"""

import pytest
from pawpal_system import Owner, Pet, Task, Scheduler, ScheduledItem, Priority, TaskType


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_task():
    return Task("Morning walk", 30, Priority.HIGH, TaskType.WALK)

@pytest.fixture
def sample_pet():
    return Pet("Mochi", "dog")

@pytest.fixture
def owner_with_pet():
    owner = Owner("Jordan", available_minutes=120)
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Morning walk", 30, Priority.HIGH, TaskType.WALK, preferred_time="morning"))
    pet.add_task(Task("Feeding",      10, Priority.HIGH, TaskType.FEEDING, preferred_time="morning"))
    owner.add_pet(pet)
    return owner


# ── Phase 2 tests (kept from before) ─────────────────────────────────────────

def test_mark_complete_changes_status(sample_task):
    assert sample_task.completed is False
    sample_task.mark_complete()
    assert sample_task.completed is True

def test_add_task_increases_count(sample_pet, sample_task):
    before = len(sample_pet.get_tasks())
    sample_pet.add_task(sample_task)
    assert len(sample_pet.get_tasks()) == before + 1

def test_scheduler_respects_available_time():
    owner = Owner("Alex", available_minutes=20)
    pet = Pet("Rex", "dog")
    pet.add_task(Task("Long walk", 60, Priority.HIGH))
    pet.add_task(Task("Feeding",   10, Priority.HIGH))
    owner.add_pet(pet)

    schedule = Scheduler(owner).build_schedule()
    titles = [item.task.title for item in schedule]

    assert "Feeding" in titles
    assert "Long walk" not in titles

def test_owner_get_all_tasks_aggregates(owner_with_pet):
    second_pet = Pet("Luna", "cat")
    second_pet.add_task(Task("Grooming", 20, Priority.LOW))
    owner_with_pet.add_pet(second_pet)

    assert len(owner_with_pet.get_all_tasks()) == 3


# ── Phase 4: sorting ──────────────────────────────────────────────────────────

def test_sorted_schedule_is_chronological():
    """sorted_schedule() must return items in ascending start-time order."""
    owner = Owner("Jordan", available_minutes=180)
    pet = Pet("Mochi", "dog")
    # Add tasks with different preferred times so they land at different anchors
    pet.add_task(Task("Grooming",    20, Priority.LOW,    preferred_time="evening"))
    pet.add_task(Task("Enrichment",  15, Priority.MEDIUM, preferred_time="afternoon"))
    pet.add_task(Task("Walk",        30, Priority.HIGH,   preferred_time="morning"))
    owner.add_pet(pet)

    s = Scheduler(owner)
    s.build_schedule()
    ordered = s.sorted_schedule()

    start_times = [item.start_minute for item in ordered]
    assert start_times == sorted(start_times)


# ── Phase 4: recurrence ───────────────────────────────────────────────────────

def test_next_occurrence_returns_none_for_once():
    """A one-time task must not generate a follow-up."""
    task = Task("Vet visit", 60, Priority.HIGH, frequency="once")
    task.mark_complete()
    assert task.next_occurrence() is None

def test_next_occurrence_returns_fresh_task_for_daily():
    """A daily task must return a new incomplete copy after completion."""
    task = Task("Feeding", 10, Priority.HIGH, frequency="daily")
    task.mark_complete()
    assert task.completed is True

    next_task = task.next_occurrence()
    assert next_task is not None
    assert next_task.completed is False
    assert next_task.title == task.title        # same task, not completed
    assert next_task is not task                # must be a new object

def test_next_occurrence_weekly():
    """Weekly tasks also produce a fresh copy."""
    task = Task("Grooming", 20, Priority.LOW, frequency="weekly")
    task.mark_complete()
    nxt = task.next_occurrence()
    assert nxt is not None
    assert nxt.completed is False


# ── Phase 4: conflict detection ───────────────────────────────────────────────

def test_detect_conflicts_finds_overlap():
    """Two items at the same start time must be flagged."""
    owner = Owner("Jordan", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    s = Scheduler(owner)
    walk    = Task("Walk",    30, Priority.HIGH)
    feeding = Task("Feeding", 10, Priority.HIGH)
    # Force both to start at 7:00 AM (420 min)
    s._schedule = [
        ScheduledItem(task=walk,    pet=pet, start_minute=420),
        ScheduledItem(task=feeding, pet=pet, start_minute=420),
    ]

    conflicts = s.detect_conflicts()
    assert len(conflicts) == 1
    assert "Walk" in conflicts[0]
    assert "Feeding" in conflicts[0]

def test_detect_conflicts_none_when_sequential():
    """Tasks that end before the next one starts must not conflict."""
    owner = Owner("Jordan", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    s = Scheduler(owner)
    s._schedule = [
        ScheduledItem(task=Task("Walk",    30, Priority.HIGH), pet=pet, start_minute=420),  # 7:00–7:30
        ScheduledItem(task=Task("Feeding", 10, Priority.HIGH), pet=pet, start_minute=450),  # 7:30–7:40
    ]

    assert s.detect_conflicts() == []


# ── edge cases ────────────────────────────────────────────────────────────────

def test_scheduler_with_no_tasks():
    """Scheduler must return an empty list when the owner has no tasks."""
    owner = Owner("Empty", available_minutes=120)
    owner.add_pet(Pet("Ghost", "cat"))   # pet exists but has no tasks
    schedule = Scheduler(owner).build_schedule()
    assert schedule == []

def test_filter_tasks_by_pet_name(owner_with_pet):
    """filter_tasks(pet_name=) must return only that pet's tasks."""
    # owner_with_pet has Mochi with 2 tasks
    results = owner_with_pet.filter_tasks(pet_name="Mochi")
    assert len(results) == 2
    assert all(pet.name == "Mochi" for pet, _ in results)

def test_filter_tasks_by_completed(owner_with_pet):
    """filter_tasks(completed=True) must return only finished tasks."""
    mochi = owner_with_pet.get_pets()[0]
    mochi.get_tasks()[0].mark_complete()

    done    = owner_with_pet.filter_tasks(completed=True)
    pending = owner_with_pet.filter_tasks(completed=False)

    assert len(done) == 1
    assert len(pending) == 1
