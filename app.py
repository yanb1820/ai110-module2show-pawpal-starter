import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler, Priority, TaskType

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state initialisation
#
# WHY: Streamlit reruns the entire script top-to-bottom on every interaction.
# Without this guard, `Owner(...)` would be recreated blank on every click —
# that's the classic "state reset" bug. Storing the object in st.session_state
# means it survives reruns for the lifetime of the browser session.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None   # set once the user fills in their name

# ---------------------------------------------------------------------------
# Section 1 — Owner setup
# ---------------------------------------------------------------------------
st.subheader("1. Owner")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Your name", value="Jordan")
with col2:
    available_minutes = st.number_input("Available minutes today", min_value=10, max_value=480, value=120)

if st.button("Set owner"):
    # UI action  →  backend: create an Owner and store it in session state
    st.session_state.owner = Owner(owner_name, available_minutes=available_minutes)
    st.success(f"Owner set: {owner_name} ({available_minutes} min available)")

if st.session_state.owner is None:
    st.info("Set an owner above to continue.")
    st.stop()

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Section 2 — Add a pet
# ---------------------------------------------------------------------------
st.divider()
st.subheader("2. Add a Pet")

col1, col2 = st.columns(2)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    # UI action  →  backend: create a Pet and register it with the Owner
    new_pet = Pet(pet_name, species)
    owner.add_pet(new_pet)
    st.success(f"Added {pet_name} ({species})")

pets = owner.get_pets()
if pets:
    st.write("Registered pets:", [p.name for p in pets])
else:
    st.info("No pets yet. Add one above.")

# ---------------------------------------------------------------------------
# Section 3 — Add a task to a pet
# ---------------------------------------------------------------------------
st.divider()
st.subheader("3. Add a Task")

if not pets:
    st.info("Add a pet first.")
else:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        target_pet_name = st.selectbox("For pet", [p.name for p in pets])
    with col2:
        task_title = st.text_input("Task title", value="Morning walk")
    with col3:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col4:
        priority_str = st.selectbox("Priority", ["high", "medium", "low"])

    preferred_time = st.selectbox("Preferred time (optional)", ["none", "morning", "afternoon", "evening"])

    if st.button("Add task"):
        # UI action  →  backend: find the right Pet, create a Task, attach it
        target_pet = next(p for p in pets if p.name == target_pet_name)
        target_pet.add_task(Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=Priority(priority_str),
            preferred_time=None if preferred_time == "none" else preferred_time,
        ))
        st.success(f"Added '{task_title}' to {target_pet_name}")

    # Show all tasks with a Mark Complete button per task
    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.write("All tasks:")
        for i, (pet, task) in enumerate(all_tasks):
            col_info, col_btn = st.columns([4, 1])
            status = "✓" if task.completed else "○"
            with col_info:
                st.write(
                    f"{status} **{task.title}** ({pet.name}) — "
                    f"{task.duration_minutes} min, {task.priority.value}"
                )
            with col_btn:
                if not task.completed:
                    if st.button("Done", key=f"complete_{i}"):
                        task.mark_complete()
                        st.rerun()

# ---------------------------------------------------------------------------
# Section 4 — Generate schedule
# ---------------------------------------------------------------------------
st.divider()
st.subheader("4. Generate Schedule")

if st.button("Generate schedule"):
    all_tasks = owner.get_all_tasks()
    if not all_tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        # UI action  →  backend: Scheduler walks Owner → Pet → Task chain
        scheduler = Scheduler(owner)
        scheduler.build_schedule()
        st.text(scheduler.explain_plan())
