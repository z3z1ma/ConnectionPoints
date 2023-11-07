"""
ConnectionPoints is a web app that allows users to create challenges and rewards

Environment variables:
SENDGRID_API_KEY: API key for SendGrid
SENDGRID_FROM_EMAIL: Email address to send emails from
AWS_ACCESS_KEY_ID: AWS access key ID
AWS_SECRET_ACCESS_KEY: AWS secret access key

Components:
database: DynamoDB
"""
import os
import random
import secrets
import typing as t

import streamlit as st
import streamlit_authenticator as stauth
from pynamodb.exceptions import DoesNotExist
from pynamodb.models import Model as _Model
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from connection_points.models import AuthConfig, Challenge, Party, Reward, User


def setup() -> AuthConfig:
    """
    Perform initial setup of the database and authentication.

    This operation is idempotent. It will only create the tables if they
    do not already exist. It will only create the auth config if it does
    not already exist. This allows the app to bootstrap itself.
    """
    for dao in t.cast(t.List[_Model], [Challenge, Party, Reward, User, AuthConfig]):
        if not dao.exists():
            dao.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)

    try:
        auth_conf = AuthConfig.get(AuthConfig.COOKIE_NAME)
    except DoesNotExist:
        auth_conf = AuthConfig(key=secrets.token_urlsafe(32))
        auth_conf.save()

    return auth_conf


with st.spinner("Loading..."):
    auth_conf = setup()
    user_creds = {
        "usernames": {
            u.name: {"email": u.email, "name": u.displayName, "password": u.password}
            for u in User.scan()
        }
    }
    existing_usernames = list(user_creds["usernames"].keys())


authenticator = stauth.Authenticate(
    user_creds,
    AuthConfig.COOKIE_NAME,
    auth_conf.key,
    int(auth_conf.expiry_days),
)

title_area, point_area, name_area = st.columns([3, 1, 1], gap="large")
title_area.title("ConnectionPoints")

if (
    st.session_state["authentication_status"] is None
    or st.session_state["authentication_status"] is False
):
    tab_login, tab_register, tab_forgot_password = st.tabs(
        ["Login", "Register", "Forgot password"]
    )
    with tab_login:
        authenticator.login("Login", "main")
        if st.session_state["authentication_status"] is False:
            st.error(
                "Username/password is incorrect. If you are a new user, please register."
            )
        else:
            st.warning("Please enter your username and password.")
    with tab_register:
        try:
            if authenticator.register_user("Register user", preauthorization=False):
                new_user = set(existing_usernames) ^ set(user_creds["usernames"].keys())
                if len(new_user) == 0:
                    raise Exception("User already exists?")
                new_user = new_user.pop()
                info = user_creds["usernames"][new_user]
                User(
                    email=info["email"],
                    name=new_user,
                    displayName=info["name"],
                    password=info["password"],
                    parties=[],
                ).save()
                st.success("User registered successfully. Please login.", icon="✅")
        except Exception as e:
            err = str(e)
            if "Username already taken" in err:
                err += ". Please try again with a different username. If you are a returning user, please login."
            st.error(err, icon="❌")
    with tab_forgot_password:
        try:
            (
                existing_username,
                existing_email,
                new_password,
            ) = authenticator.forgot_password("Forgot password")
            if existing_username:
                st.success("New password to be sent securely")
                user = User.get(existing_email)
                user.password = user_creds["usernames"][existing_username]["password"]
                user.save()
                SendGridAPIClient(os.environ.get("SENDGRID_API_KEY")).send(
                    Mail(
                        from_email=os.environ.get("SENDGRID_FROM_EMAIL"),
                        to_emails=existing_email,
                        subject="ConnectionPoints Password Reset",
                        html_content=f"Your new password is {new_password}.",
                    )
                )
            else:
                st.error("Username not found")
        except Exception as e:
            st.error(e)
        st.warning("Please enter your username")
elif st.session_state["authentication_status"]:
    username = st.session_state["username"]
    user = User.name_index.scan(User.name == username).next()

    point_area.metric("Points", 100, 200)
    with name_area:
        st.write(f"**{user.displayName}** 👋")
        authenticator.logout("Logout", key="logout_btn")

    tab_challenges, tab_rewards, tab_approve, tab_party, tab_setting = st.tabs(
        ["Challenges", "Rewards", "Award", "Party", "Settings"]
    )

    column_challenges = list(tab_challenges.columns(2, gap="large"))

    for i, challenge in enumerate(
        [
            "⭐️  Clean the house",
            "⭐️  Do the dishes",
            "⭐️  Take out the trash",
            "🟢  Do the laundry",
            "⭐️  Change the sheets",
            "🟢  Clean the bathroom",
        ]
    ):
        this = column_challenges[i % 2]
        this.markdown(f"#### {challenge}")
        c1, c2 = this.columns(2)
        c1.metric(
            "Points",
            random.sample(range(1, 100), 1)[0],
            help="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        )
        c2.text("")
        c2.button("Accept", challenge)

    with tab_challenges.form("add_challenge"):
        tab_challenges.write("Add a challenge")
        challenge_name = tab_challenges.text_input("Name")
        challenge_points = tab_challenges.text_input("Points")
        challenge_desc = tab_challenges.text_input("Description")
