import streamlit as st
from auth import (register_user, login_user, delete_account,
                  get_all_users, make_admin, remove_admin,
                  has_submitted_survey, get_next_participant_number)
from devices import add_device, get_user_devices, delete_device, scan_device, get_device_vulnerabilities
from db import get_connection

# --- Page Configuration ---
st.set_page_config(
    page_title="IoT Device Vulnerability Tracker",
    page_icon="🔒",
    layout="wide"
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #f0f2f6;
    }

    /* All buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
        border: none;
        padding: 0.5rem 1rem;
    }

    /* Primary button — blue */
    .stButton > button[kind="primary"],
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #1a73e8 !important;
        color: white !important;
    }

    .stButton > button[kind="primary"]:hover {
        background-color: #1557b0 !important;
    }

    /* Input fields — always visible border */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #c0c0c0 !important;
        background-color: white !important;
        padding: 0.5rem;
    }

    .stTextInput > div > div > input:focus {
        border: 2px solid #1a73e8 !important;
        box-shadow: 0 0 0 2px rgba(26,115,232,0.2) !important;
    }

    /* Device card */
    .device-card {
        background-color: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 5px solid #1a73e8;
    }

    /* Header style */
    h1 { color: #1a237e; font-weight: 700; }
    h2, h3 { color: #283593; }

    /* Metric boxes */
    [data-testid="metric-container"] {
        background-color: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    /* Hide Streamlit menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Session State Setup ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "page" not in st.session_state:
    st.session_state.page = "login"


# --- Helper Function to change pages ---
def go_to(page):
    st.session_state.page = page


# --- Login Page ---
def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align:center; font-size:1.8rem;'>🔒 IoT Device Vulnerability Tracker</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#666; margin-bottom:2rem;'>Monitor and manage your IoT device security</p>", unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("Login to your account")

        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")

        if st.button("Login", use_container_width=True, type="primary"):
            if username and password:
                success, result = login_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.user_id = result["id"]
                    st.session_state.username = result["username"]
                    st.session_state.is_admin = result["is_admin"]
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error(result)
            else:
                st.warning("Please enter your username and password.")

        st.markdown("---")
        st.markdown("<p style='text-align:center;'>Don't have an account?</p>", unsafe_allow_html=True)
        if st.button("Register here", use_container_width=True):
            go_to("register")
            st.rerun()


# --- Register Page ---
def show_register():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align:center; font-size:1.8rem;'>🔒 IoT Device Vulnerability Tracker</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#666; margin-bottom:2rem;'>Create your free account</p>", unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("Create a new account")

        username = st.text_input("👤 Username")
        email = st.text_input("📧 Email")
        password = st.text_input("🔑 Password", type="password")
        confirm_password = st.text_input("🔑 Confirm Password", type="password")

        if st.button("Register", use_container_width=True, type="primary"):
            if username and email and password and confirm_password:
                if password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    success, message = register_user(username, email, password)
                    if success:
                        st.success(message)
                        go_to("login")
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.warning("Please fill in all fields.")

        st.markdown("---")
        st.markdown("<p style='text-align:center;'>Already have an account?</p>", unsafe_allow_html=True)
        if st.button("Login here", use_container_width=True):
            go_to("login")
            st.rerun()


# --- Dashboard Page ---
def show_dashboard():
    st.markdown(f"<h1>👋 Welcome, {st.session_state.username}!</h1>", unsafe_allow_html=True)

    if st.session_state.is_admin:
        st.info("🔑 You are logged in as an Admin.")

    st.markdown("---")
    st.markdown("<h2>📱 Your Registered IoT Devices</h2>", unsafe_allow_html=True)

    devices = get_user_devices(st.session_state.user_id)

    if not devices:
        st.info("You have no devices registered yet. Add your first device!")
    else:
        for device in devices:
            st.markdown(f"""
                <div class='device-card'>
                    <h3 style='margin:0; color:#1a237e;'>
                        📱 {device['manufacturer']} — {device['model']}
                    </h3>
                    <p style='margin:0; color:#666; font-size:0.85rem;'>
                        Added on: {device['created_at'].strftime('%d %b %Y')}
                    </p>
                </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🔍 Scan for Vulnerabilities",
                             key=f"scan_{device['id']}",
                             use_container_width=True,
                             type="primary"):
                    with st.spinner("Scanning for vulnerabilities..."):
                        success, results = scan_device(
                            device["id"],
                            device["manufacturer"],
                            device["model"]
                        )
                    if success:
                        st.success(f"✅ Found {len(results)} vulnerabilities!")
                        st.rerun()
                    else:
                        st.error("Scan failed. Please try again.")

            with col2:
                if st.button("🗑️ Delete Device",
                             key=f"delete_{device['id']}",
                             use_container_width=True):
                    delete_device(device["id"], st.session_state.user_id)
                    st.success("Device deleted.")
                    st.rerun()

            vulnerabilities = get_device_vulnerabilities(device["id"])
            if vulnerabilities:
                st.markdown("**🔎 Vulnerabilities Found:**")
                for v in vulnerabilities:
                    show_vulnerability_card(v)

            st.markdown("---")

    # Add Device Button
    if st.button("➕ Add New Device", use_container_width=True, type="primary"):
        go_to("add_device")
        st.rerun()

    st.markdown("---")

    # Survey button — normal users only
    if not st.session_state.is_admin:
        already_submitted = has_submitted_survey(st.session_state.user_id)
        if already_submitted:
            st.success("✅ You have already completed the usability survey. Thank you!")
        else:
            if st.button("📋 Take Usability Survey", use_container_width=True):
                go_to("sus")
                st.rerun()

    # Admin only buttons
    if st.session_state.is_admin:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 View SUS Results",
                         use_container_width=True,
                         type="primary"):
                go_to("sus_results")
                st.rerun()
        with col2:
            if st.button("👥 Manage Users", use_container_width=True):
                go_to("manage_users")
                st.rerun()

    st.markdown("---")

    # Logout and Delete Account
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.is_admin = False
            st.session_state.page = "login"
            st.rerun()
    with col2:
        if not st.session_state.is_admin:
            if st.button("❌ Delete My Account", use_container_width=True):
                go_to("delete_account")
                st.rerun()


# --- Add Device Page ---
def show_add_device():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1>➕ Add a New Device</h1>", unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("Enter your IoT device details")
        st.markdown("<p style='color:#666;'>Enter the manufacturer and model of your device. No technical knowledge required!</p>", unsafe_allow_html=True)

        manufacturer = st.text_input("🏭 Manufacturer (e.g. Samsung, Philips, TP-Link)")
        model = st.text_input("📱 Model (e.g. Smart TV, Hue Bridge, Archer C7)")

        if st.button("Add Device", use_container_width=True, type="primary"):
            if manufacturer and model:
                success, device_id = add_device(
                    st.session_state.user_id,
                    manufacturer,
                    model
                )
                if success:
                    st.success("✅ Device added successfully!")
                    go_to("dashboard")
                    st.rerun()
                else:
                    st.error(device_id)
            else:
                st.warning("Please enter both manufacturer and model.")

        st.markdown("---")
        if st.button("⬅️ Back to Dashboard", use_container_width=True):
            go_to("dashboard")
            st.rerun()


# --- Delete Account Page ---
def show_delete_account():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1>❌ Delete My Account</h1>", unsafe_allow_html=True)
        st.markdown("---")
        st.warning("⚠️ This will permanently delete your account and ALL your data. This cannot be undone!")
        st.info("📋 Note: If you have completed the usability survey, your anonymous survey response will be kept for research purposes.")
        st.write("Are you sure you want to delete your account?")

        if st.button("Yes, Delete My Account", use_container_width=True):
            success, message = delete_account(st.session_state.user_id)
            if success:
                st.success(message)
                st.session_state.logged_in = False
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.is_admin = False
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error(message)

        if st.button("No, Go Back", use_container_width=True):
            go_to("dashboard")
            st.rerun()


# --- SUS Questionnaire Page ---
def show_sus():
    if st.session_state.is_admin:
        st.error("⛔ Admins cannot take the survey.")
        if st.button("⬅️ Back to Dashboard", use_container_width=True):
            go_to("dashboard")
            st.rerun()
        return

    if has_submitted_survey(st.session_state.user_id):
        st.success("✅ You have already completed the survey. Thank you for your participation!")
        if st.button("⬅️ Back to Dashboard", use_container_width=True):
            go_to("dashboard")
            st.rerun()
        return

    st.markdown("<h1>📋 Usability Questionnaire</h1>", unsafe_allow_html=True)
    st.markdown("---")
    st.info("Please rate your experience using the IoT Device Vulnerability Tracker. For each statement, select an option from **Strongly Disagree** to **Strongly Agree**.")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        questions = [
            "1. I think that I would like to use this system frequently.",
            "2. I found the system unnecessarily complex.",
            "3. I thought the system was easy to use.",
            "4. I think that I would need the support of a technical person to use this system.",
            "5. I found the various functions in this system were well integrated.",
            "6. I thought there was too much inconsistency in this system.",
            "7. I would imagine that most people would learn to use this system very quickly.",
            "8. I found the system very cumbersome to use.",
            "9. I felt very confident using the system.",
            "10. I needed to learn a lot of things before I could get going with this system."
        ]

        labels = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]
        answers = []

        for q in questions:
            st.markdown(f"""
                <div style='background:white; padding:1rem; border-radius:10px;
                margin-bottom:0.5rem; box-shadow:0 1px 4px rgba(0,0,0,0.06);'>
                    <b>{q}</b>
                </div>
            """, unsafe_allow_html=True)
            answer = st.radio(
                q,
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: labels[x - 1],
                horizontal=True,
                label_visibility="collapsed",
                index=None
            )
            answers.append(answer)
            st.write("")

        st.markdown("---")

        if st.button("Submit Survey", use_container_width=True, type="primary"):
            if None in answers:
                st.warning("⚠️ Please answer all questions before submitting.")
            else:
                score = calculate_sus_score(answers)
                participant_number = get_next_participant_number()
                success = save_sus_result(
                    st.session_state.user_id,
                    participant_number,
                    answers,
                    score
                )
                if success:
                    st.success("✅ Thank you for your participation!")
                    st.info("Your feedback is valuable and will help us improve the IoT Device Vulnerability Tracker.")
                    st.rerun()
                else:
                    st.error("Something went wrong. Please try again.")

        st.markdown("---")
        if st.button("⬅️ Back to Dashboard", use_container_width=True):
            go_to("dashboard")
            st.rerun()


# --- SUS Score Calculator ---
def calculate_sus_score(answers):
    total = 0
    for i, answer in enumerate(answers):
        if i % 2 == 0:
            total += answer - 1
        else:
            total += 5 - answer
    return total * 2.5


# --- Save SUS Result to Database ---
def save_sus_result(user_id, participant_number, answers, score):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sus_results
            (user_id, participant_number, q1, q2, q3, q4, q5,
             q6, q7, q8, q9, q10, sus_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, participant_number,
              answers[0], answers[1], answers[2], answers[3], answers[4],
              answers[5], answers[6], answers[7], answers[8], answers[9],
              score))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving SUS result: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# --- SUS Results Page (Admin only) ---
def show_sus_results():
    if not st.session_state.is_admin:
        st.error("⛔ Access denied. This page is for admins only.")
        return

    st.markdown("<h1>📊 SUS Results Summary</h1>", unsafe_allow_html=True)
    st.markdown("---")

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT participant_number, q1, q2, q3, q4, q5,
                   q6, q7, q8, q9, q10, sus_score, submitted_at
            FROM sus_results
            ORDER BY participant_number ASC
        """)
        results = cursor.fetchall()

        if not results:
            st.info("No SUS results yet.")
        else:
            scores = [r[11] for r in results]
            average = sum(scores) / len(scores)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("👥 Total Participants", len(results))
            with col2:
                st.metric("📊 Average SUS Score", f"{average:.1f} / 100")
            with col3:
                if average >= 80:
                    st.metric("🏆 Overall Rating", "Good ✅")
                elif average >= 70:
                    st.metric("🏆 Overall Rating", "OK 🟡")
                else:
                    st.metric("🏆 Overall Rating", "Needs Improvement 🔴")

            st.markdown("---")
            st.markdown("**Individual Results:**")

            question_labels = [
                "Q1: Use frequently",
                "Q2: Unnecessarily complex",
                "Q3: Easy to use",
                "Q4: Need technical support",
                "Q5: Well integrated",
                "Q6: Too inconsistent",
                "Q7: Learn quickly",
                "Q8: Cumbersome to use",
                "Q9: Felt confident",
                "Q10: Needed to learn a lot"
            ]

            for r in results:
                with st.expander(f"👤 Participant {r[0]} — Score: {r[11]:.1f} / 100 | {r[12].strftime('%d %b %Y %H:%M')}"):
                    labels = ["Strongly Disagree", "Disagree",
                              "Neutral", "Agree", "Strongly Agree"]
                    for i, label in enumerate(question_labels):
                        answer_value = r[i + 1]
                        st.write(f"- **{label}:** {labels[answer_value - 1]} ({answer_value})")
                    st.markdown(f"**✅ Final SUS Score: {r[11]:.1f} / 100**")

            st.markdown("---")
            st.info("💡 To print results: Press Ctrl+P in your browser to print this page.")

    except Exception as e:
        st.error(f"Error loading results: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    st.markdown("---")
    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        go_to("dashboard")
        st.rerun()


# --- Manage Users Page (Admin only) ---
def show_manage_users():
    if not st.session_state.is_admin:
        st.error("⛔ Access denied. This page is for admins only.")
        return

    st.markdown("<h1>👥 Manage Users</h1>", unsafe_allow_html=True)
    st.markdown("---")

    users = get_all_users()

    if not users:
        st.info("No users found.")
    else:
        for user in users:
            role_colour = "#1a73e8" if user["is_admin"] else "#666"
            role_label = "🔑 Admin" if user["is_admin"] else "👤 User"

            st.markdown(f"""
                <div style='background:white; padding:1rem 1.5rem;
                border-radius:10px; margin-bottom:0.5rem;
                box-shadow:0 2px 6px rgba(0,0,0,0.07);
                border-left: 4px solid {role_colour};'>
                    <b style='font-size:1.05rem;'>{user['username']}</b>
                    <span style='color:#666;'> — {user['email']}</span>
                    <span style='color:{role_colour}; font-weight:600;'> — {role_label}</span>
                    <br><small style='color:#999;'>
                        Registered: {user['created_at'].strftime('%d %b %Y')}
                    </small>
                </div>
            """, unsafe_allow_html=True)

            if user["id"] != st.session_state.user_id:
                col1, col2 = st.columns([1, 1])
                with col1:
                    if not user["is_admin"]:
                        if st.button("⬆️ Make Admin",
                                     key=f"admin_{user['id']}",
                                     use_container_width=True):
                            success, message = make_admin(user["id"])
                            if success:
                                st.success(message)
                                st.rerun()
                    else:
                        if st.button("⬇️ Remove Admin",
                                     key=f"remove_{user['id']}",
                                     use_container_width=True):
                            success, message = remove_admin(user["id"])
                            if success:
                                st.success(message)
                                st.rerun()
                with col2:
                    if st.button("🗑️ Delete User",
                                 key=f"del_user_{user['id']}",
                                 use_container_width=True):
                        success, message = delete_account(user["id"])
                        if success:
                            st.success("User deleted.")
                            st.rerun()
                        else:
                            st.error(message)

            st.markdown("")

    st.markdown("---")
    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        go_to("dashboard")
        st.rerun()


# --- Vulnerability Card ---
def show_vulnerability_card(v):
    icons = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🟢",
        "UNKNOWN": "⚪"
    }
    icon = icons.get(v["severity"], "⚪")

    with st.expander(f"{icon} {v['cve_id']} — {v['severity']}"):
        st.markdown(f"""
            <div style='padding:0.5rem;'>
                <p><b>📝 Summary:</b> {v['plain_summary']}</p>
                <p><b>✅ Recommended Action:</b> {v['recommendation']}</p>
                <p><b>📖 Full Description:</b> {v['description']}</p>
            </div>
        """, unsafe_allow_html=True)


# --- Main App Router ---
if not st.session_state.logged_in:
    if st.session_state.page == "register":
        show_register()
    else:
        show_login()
else:
    if st.session_state.page == "dashboard":
        show_dashboard()
    elif st.session_state.page == "add_device":
        show_add_device()
    elif st.session_state.page == "delete_account":
        show_delete_account()
    elif st.session_state.page == "sus":
        show_sus()
    elif st.session_state.page == "sus_results":
        show_sus_results()
    elif st.session_state.page == "manage_users":
        show_manage_users()
    else:
        show_dashboard()