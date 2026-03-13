"""
main.py — demo script showing the full data flow:
    Owner → Pet → Task → Scheduler → ScheduledItem
"""

from pawpal_system import Owner, Pet, Task, Scheduler, Priority, TaskType

# ── 1. Create owner ──────────────────────────────────────────────────────────
jordan = Owner("Jordan", available_minutes=120)

# ── 2. Create two pets ───────────────────────────────────────────────────────
mochi = Pet("Mochi", species="dog", age_years=3)
luna  = Pet("Luna",  species="cat", age_years=5)

# ── 3. Add tasks ─────────────────────────────────────────────────────────────
#    Mix of priorities, times, and frequencies to exercise all features
mochi.add_task(Task("Morning walk",   30, Priority.HIGH,   TaskType.WALK,      preferred_time="morning",   frequency="daily"))
mochi.add_task(Task("Feeding",        10, Priority.HIGH,   TaskType.FEEDING,   preferred_time="morning",   frequency="daily"))
mochi.add_task(Task("Medication",      5, Priority.HIGH,   TaskType.MEDICATION,                            frequency="daily"))

luna.add_task(Task("Feeding",         10, Priority.HIGH,   TaskType.FEEDING,   preferred_time="morning",   frequency="daily"))
luna.add_task(Task("Enrichment toy",  15, Priority.MEDIUM, TaskType.ENRICHMENT,preferred_time="afternoon"))
luna.add_task(Task("Grooming",        20, Priority.LOW,    TaskType.GROOMING,  preferred_time="evening",   frequency="weekly"))

jordan.add_pet(mochi)
jordan.add_pet(luna)

# ── 4. Data flow: Owner.get_all_tasks() ──────────────────────────────────────
print("=== Data Flow: Owner.get_all_tasks() ===")
for pet, task in jordan.get_all_tasks():
    print(f"  {pet.name:6} → {task}")

# ── 5. Build and display schedule ────────────────────────────────────────────
print()
scheduler = Scheduler(jordan)
scheduler.build_schedule()
print(scheduler.explain_plan())

# ── 6. Sorted schedule ───────────────────────────────────────────────────────
print("\n=== Sorted Schedule ===")
for item in scheduler.sorted_schedule():
    print(f"  {item.time_label()}  {item.task.title} ({item.pet.name})")

# ── 7. Conflict detection — no conflicts expected in normal schedule ──────────
print("\n=== Conflict Detection (normal schedule) ===")
conflicts = scheduler.detect_conflicts()
if conflicts:
    for w in conflicts:
        print(f"  ⚠ {w}")
else:
    print("  No conflicts detected.")

# ── 8. Force a conflict to verify detection works ────────────────────────────
print("\n=== Conflict Detection (forced overlap) ===")
from pawpal_system import ScheduledItem
forced = Scheduler(jordan)
forced._schedule = [
    ScheduledItem(mochi.get_tasks()[0], mochi, start_minute=7*60,  reason="test"),   # 7:00–7:30
    ScheduledItem(mochi.get_tasks()[1], mochi, start_minute=7*60,  reason="test"),   # 7:00–7:10  ← overlap
    ScheduledItem(luna.get_tasks()[0],  luna,  start_minute=7*60,  reason="test"),   # 7:00–7:10  ← overlap
]
for w in forced.detect_conflicts():
    print(f"  ⚠ {w}")

# ── 9. Filtering ─────────────────────────────────────────────────────────────
print("\n=== Filter: only Mochi's tasks ===")
for pet, task in jordan.filter_tasks(pet_name="Mochi"):
    print(f"  {task}")

# ── 10. Mark a task complete, then filter for pending vs done ─────────────────
mochi.get_tasks()[0].mark_complete()   # Morning walk → done

print("\n=== Filter: completed tasks ===")
for pet, task in jordan.filter_tasks(completed=True):
    print(f"  {pet.name}: {task}")

print("\n=== Filter: pending tasks ===")
for pet, task in jordan.filter_tasks(completed=False):
    print(f"  {pet.name}: {task}")

# ── 11. Recurring task: next_occurrence() ────────────────────────────────────
print("\n=== Recurring Task: next_occurrence() ===")
walk = mochi.get_tasks()[0]
print(f"  Completed:       {walk}")
print(f"  Next occurrence: {walk.next_occurrence()}")

grooming = luna.get_tasks()[2]
grooming.mark_complete()
print(f"\n  Completed:       {grooming}")
print(f"  Next occurrence: {grooming.next_occurrence()}")

once_task = Task("Vet visit", 60, Priority.HIGH, frequency="once")
print(f"\n  One-time task:   {once_task}")
print(f"  Next occurrence: {once_task.next_occurrence()}")  # → None
