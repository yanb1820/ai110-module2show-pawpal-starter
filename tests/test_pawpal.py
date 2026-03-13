"""
tests/test_pawpal.py — core behaviour tests for PawPal+
"""

import pytest
from pawpal_system import Owner, Pet, Task, Scheduler, Priority, TaskType


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


# ── test 1: mark_complete() changes completed status ─────────────────────────

def test_mark_complete_changes_status(sample_task):
    assert sample_task.completed is False
    sample_task.mark_complete()
    assert sample_task.completed is True


# ── test 2: adding a task increases the pet's task count ─────────────────────

def test_add_task_increases_count(sample_pet, sample_task):
    before = len(sample_pet.get_tasks())
    sample_pet.add_task(sample_task)
    assert len(sample_pet.get_tasks()) == before + 1


# ── test 3: scheduler only includes tasks that fit within available time ──────

def test_scheduler_respects_available_time():
    owner = Owner("Alex", available_minutes=20)
    pet = Pet("Rex", "dog")
    pet.add_task(Task("Long walk", 60, Priority.HIGH))   # 60 min — won't fit
    pet.add_task(Task("Feeding",   10, Priority.HIGH))   # 10 min — fits
    owner.add_pet(pet)

    schedule = Scheduler(owner).build_schedule()
    titles = [item.task.title for item in schedule]

    assert "Feeding" in titles
    assert "Long walk" not in titles


# ── test 4: owner.get_all_tasks() aggregates across all pets ─────────────────

def test_owner_get_all_tasks_aggregates(owner_with_pet):
    second_pet = Pet("Luna", "cat")
    second_pet.add_task(Task("Grooming", 20, Priority.LOW))
    owner_with_pet.add_pet(second_pet)

    all_tasks = owner_with_pet.get_all_tasks()
    # 2 from Mochi + 1 from Luna = 3
    assert len(all_tasks) == 3
