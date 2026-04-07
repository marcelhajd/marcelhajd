import csv
import os
import smtplib
import ssl
import uuid
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"
CSV_PATH = DATA_DIR / "requests.csv"

DEPARTMENTS = ["HR", "Sales", "Procurement", "Finance", "Operations", "IT", "Other"]


def ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        with CSV_PATH.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                [
                    "request_id",
                    "created_at",
                    "department",
                    "request_text",
                    "name",
                    "email",
                    "file_paths",
                ]
            )


def save_files(files, request_id: str) -> list[str]:
    saved_paths: list[str] = []
    request_folder = UPLOADS_DIR / request_id
    request_folder.mkdir(parents=True, exist_ok=True)

    for uploaded in files:
        if uploaded is None:
            continue
        safe_name = Path(uploaded.name).name
        destination = request_folder / safe_name
        with destination.open("wb") as output_file:
            output_file.write(uploaded.getbuffer())
        saved_paths.append(str(destination))
    return saved_paths


def append_request_row(
    request_id: str,
    department: str,
    request_text: str,
    name: str,
    email: str,
    file_paths: list[str],
) -> None:
    with CSV_PATH.open("a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                request_id,
                datetime.utcnow().isoformat(),
                department,
                request_text,
                name,
                email,
                "|".join(file_paths),
            ]
        )


def send_email_notification(
    *,
    legal_email: str,
    sender_email: str,
    subject: str,
    body: str,
) -> tuple[bool, str]:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}

    if not smtp_host:
        return False, "SMTP_HOST not configured; email not sent."

    message = EmailMessage()
    message["From"] = sender_email
    message["To"] = legal_email
    message["Subject"] = subject
    message.set_content(body)

    context = ssl.create_default_context()
    try:
        if use_tls:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls(context=context)
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(message)
        else:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(message)
    except smtplib.SMTPException as exc:
        return False, f"Email failed: {exc}"

    return True, "Email sent."


def build_email_body(
    *,
    request_id: str,
    department: str,
    request_text: str,
    name: str,
    email: str,
    file_paths: list[str],
) -> str:
    lines = [
        "A new legal request has been submitted.",
        "",
        f"Request ID: {request_id}",
        f"Department: {department}",
        f"Requester: {name}",
        f"Email: {email}",
        "",
        "Request details:",
        request_text,
        "",
        "Files:",
    ]
    if file_paths:
        lines.extend(file_paths)
    else:
        lines.append("No files uploaded.")
    return "\n".join(lines)


def main() -> None:
    st.set_page_config(page_title="Legal Request", page_icon="⚖️")
    st.title("Internal Legal Request")
    st.write("Submit a request to the legal team. All fields are required unless noted.")

    ensure_storage()

    with st.form("legal-request", clear_on_submit=True):
        department = st.selectbox("Department", DEPARTMENTS)
        request_text = st.text_area(
            "Describe your request",
            max_chars=1000,
            placeholder="Provide context, deadlines, and any special considerations.",
        )
        uploaded_files = st.file_uploader(
            "Upload files (optional)",
            accept_multiple_files=True,
        )
        name = st.text_input("Your name")
        email = st.text_input("Your email")
        submitted = st.form_submit_button("Send to Legal")

    if submitted:
        if not all([department, request_text, name, email]):
            st.error("Please complete all required fields before submitting.")
            return

        request_id = uuid.uuid4().hex
        file_paths = save_files(uploaded_files, request_id)
        append_request_row(
            request_id=request_id,
            department=department,
            request_text=request_text.strip(),
            name=name.strip(),
            email=email.strip(),
            file_paths=file_paths,
        )

        legal_email = os.getenv("LEGAL_EMAIL", "legal@company.com")
        sender_email = os.getenv("FROM_EMAIL", "no-reply@company.com")
        subject = f"New Legal Request - {department} - {request_id[:8]}"
        body = build_email_body(
            request_id=request_id,
            department=department,
            request_text=request_text.strip(),
            name=name.strip(),
            email=email.strip(),
            file_paths=file_paths,
        )
        sent, message = send_email_notification(
            legal_email=legal_email,
            sender_email=sender_email,
            subject=subject,
            body=body,
        )

        if sent:
            st.success("Your request has been sent to Legal.")
        else:
            st.warning(
                "Your request has been saved, but the email notification could not be sent."
            )
            st.info(message)


if __name__ == "__main__":
    main()
