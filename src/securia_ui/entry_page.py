import streamlit as st
import requests
from envyaml import EnvYAML

config = EnvYAML('config.yml')

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.set_page_config(page_title="Securia Login", layout="wide")
    st.title("Securia Login")
    left, right = st.columns(2)
    with left:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Log in", use_container_width=True):
            try:
                data = {
                    "grant_type": "password",
                    "username": username,
                    "password": password,
                    "scope": "api",
                    "client_id": "client_id",
                    "client_secret": "client_secret"
                }
                response = requests.post(f"{config['api']['uri']}/token", data=data)

                if response.status_code == 200:
                    # Successful login
                    token = response.json().get("access_token")
                    st.session_state.token = token
                    st.session_state.logged_in = True
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password. Please try again.")
            except requests.exceptions.RequestException as e:
                st.error(f"An error occurred: {e}")
        if st.button("Register"):
            pass
    with right:
        st.image('http://localhost:8501/app/static/login_logo.png')

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
live_detections = st.Page("views/live_detections.py", title="Detections", icon=":material/detection_and_zone:")

# Tools
search = st.Page("tools/search.py", title="Search", icon=":material/search:")
llm = st.Page("tools/llm.py", title="The Guard", icon=":material/guardian:")

# Admin
users = st.Page("admin/users.py", title="Users", icon=":material/construction:")
recorders = st.Page("admin/recorders.py", title="Recorders", icon=":material/construction:")
channels = st.Page("admin/channels.py", title="Channels", icon=":material/construction:")
images = st.Page("admin/images.py", title="Images", icon=":material/construction:")
detections = st.Page("admin/detections.py", title="Detections", icon=":material/construction:")

if st.session_state.logged_in:
    pg = st.navigation(
        {
            "Account": [logout_page],
            "Live": [live_cams, live_detections],
            "Reports": [alerts, legacy_dashboard],
            "Tools": [search, llm],
            "Admin": [users, recorders, channels, images, detections]
        }
    )
else:
    pg = st.navigation([login_page])

pg.run()