import streamlit as st

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    if st.button("Log in"):
        st.session_state.logged_in = True
        st.rerun()

def logout():
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.rerun()

# Authentication
login_page = st.Page(login, title="Log in", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

# Reports (More historic things)
legacy_dashboard = st.Page("reports/explorer.py", title="Dashboard", icon=":material/dashboard:", default=True)
alerts = st.Page("reports/alerts.py", title="Alerts", icon=":material/notification_important:")

# Live (focus on the last 30 minutes?)
live_cams = st.Page("views/live_cams.py", title="Cameras", icon=":material/live_tv:")
detections = st.Page("views/live_detections.py", title="Detections", icon=":material/detection_and_zone:")

# Tools
search = st.Page("tools/search.py", title="Search", icon=":material/search:")
llm = st.Page("tools/llm.py", title="The Guard", icon=":material/guardian:")

if st.session_state.logged_in:
    pg = st.navigation(
        {
            "Account": [logout_page],
            "Live": [live_cams, detections],
            "Reports": [alerts, legacy_dashboard],
            "Tools": [search, llm],
        }
    )
else:
    pg = st.navigation([login_page])

pg.run()