import streamlit as st
import requests
from envyaml import EnvYAML
import logic

config = EnvYAML('config.yml')

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.logged_in_user = "None"
    st.session_state.logged_in_role = "guest"

def login():
    st.set_page_config(page_title="Securia Login", layout="wide")
    st.title("Securia Login")
    left, right = st.columns(2)
    with left:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Log in", use_container_width=True) or password:
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
                    userinfo = logic.fetch_logged_in_user(username, token)
                    st.session_state.token = token
                    st.session_state.logged_in = True
                    st.session_state.logged_in_user = username
                    st.session_state.logged_in_role = userinfo[0]['role']
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password. Please try again.")
            except requests.exceptions.RequestException as e:
                st.error(f"An error occurred: {e}")
        if st.button("Register"):
            pass
    with right:
        st.image(f"{config['api']['static_content_root']}/login_logo-min.png")

def logout():
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.rerun()

def about():
    st.set_page_config(page_title="About Securia", layout="wide")
    st.write(f"Version: {config['general']['version']}")

# Authentication
login_page = st.Page(login, title="Log in", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

# Reports (More historic things)
legacy_dashboard = st.Page("reports/explorer.py", title="Dashboard", icon=":material/dashboard:", default=True)
alerts = st.Page("reports/alerts.py", title="Alerts", icon=":material/notification_important:")

# Live (focus on the last 30 minutes?)
cameras_live = st.Page("views/cameras_live.py", title="Cameras", icon=":material/live_tv:")
cameras_old = st.Page("views/cams_old.py", title="Cameras OLD", icon=":material/live_tv:")
view_detections = st.Page("views/view_detections.py", title="Detections", icon=":material/detection_and_zone:")

# AI Tools
search = st.Page("ai_tools/search.py", title="Search", icon=":material/search:")
the_guard = st.Page("ai_tools/the_guard.py", title="The Guard", icon=":material/guardian:")
the_analyst = st.Page("ai_tools/the_analyst.py", title="The Analyst", icon=":material/eyeglasses:")

# Admin
users = st.Page("admin/users.py", title="Users", icon=":material/manage_accounts:")
profile = st.Page("admin/profile.py", title="Profile", icon=":material/manage_accounts:")
recorders = st.Page("admin/recorders.py", title="Recorders", icon=":material/folder_managed:")
channels = st.Page("admin/channels.py", title="Channels", icon=":material/folder_managed:")
images = st.Page("admin/images.py", title="Image Explorer", icon=":material/construction:")
detections = st.Page("admin/detections.py", title="Detection Explorer", icon=":material/construction:")
# detection_objects = st.Page("admin/detection_objects.py", title="Detection Objects", icon=":material/construction:")

# Info
about = st.Page(about, title="About", icon=":material/info:")

if st.session_state.logged_in:
    pg = st.navigation(
        {
            "Account": [profile, logout_page],
            "Quick Views": [cameras_live, cameras_old, view_detections],
            "Reports": [alerts],
            "AI Tools (Coming Soon)": [search, the_guard, the_analyst],
            "Admin": [users, recorders, channels, images, detections],
            "About": [about]
        }
    )
else:
    pg = st.navigation([login_page])

pg.run()
