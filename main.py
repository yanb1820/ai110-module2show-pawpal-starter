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

# ── 3. Add tasks to each pet ─────────────────────────────────────────────────
mochi.add_task(Task("Morning walk",   30, Priority.HIGH,   TaskType.WALK,      preferred_time="morning"))
mochi.add_task(Task("Feeding",        10, Priority.HIGH,   TaskType.FEEDING,   preferred_time="morning"))
mochi.add_task(Task("Medication",      5, Priority.HIGH,   TaskType.MEDICATION))

luna.add_task(Task("Feeding",         10, Priority.HIGH,   TaskType.FEEDING,   preferred_time="morning"))
luna.add_task(Task("Enrichment toy",  15, Priority.MEDIUM, TaskType.ENRICHMENT,preferred_time="afternoon"))
luna.add_task(Task("Grooming",        20, Priority.LOW,    TaskType.GROOMING,  preferred_time="evening"))

# ── 4. Register pets with owner ──────────────────────────────────────────────
jordan.add_pet(mochi)
jordan.add_pet(luna)

# ── 5. Inspect data flow: Owner → get_all_tasks() ────────────────────────────
print("=== Data Flow: Owner.get_all_tasks() ===")
for pet, task in jordan.get_all_tasks():
    print(f"  {pet.name:6} → {task}")

# ── 6. Run scheduler ─────────────────────────────────────────────────────────
print()
scheduler = Scheduler(jordan)
scheduler.build_schedule()
print(scheduler.explain_plan())

# ── 7. Mark a task complete and inspect the change ───────────────────────────
print("\n=== Marking 'Morning walk' complete ===")
walk = mochi.get_tasks()[0]
print(f"  Before: {walk}")
walk.mark_complete()
print(f"  After:  {walk}")
