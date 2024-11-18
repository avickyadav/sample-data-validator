import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import dotenv

dotenv.load_dotenv()

HOST = os.getenv('SMTP_HOST')
PORT = os.getenv('SMTP_PORTSMTP_PORT')
FROM_EMAIL = os.getenv('FROM_EMAIL')
TO_EMAIL = os.getenv('TO_EMAIL')
PASSWORD = os.getenv('MAIL_PASSWORD')
PASSED_SUBJECT = os.getenv('PASSED_SUBJECT')
FAILED_SUBJECT = os.getenv('FAILED_SUBJECT')
PASSED_MESSAGE = os.getenv('PASSED_MESSAGE')
FAILED_MESSAGE = os.getenv('FAILED_MESSAGE')

directory = os.getenv('EXCEL_FILES_DIRECTORY')


def create_email_message(from_email, to_email, subject, message, attachment_path):
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    if attachment_path:
        with open(attachment_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
            msg.attach(part)

    return msg


def check_file_exists(file_path):
    if os.path.exists(file_path):
        return True
    else:
        return False


def send_email(smtp_host, smtp_port, from_email, password, to_email, msg):
    """Send an email using SMTP."""
    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        status_code, response = smtp.ehlo()
        print(f"Echoing SMTP: {status_code}, {response}")

        status_codettl, responsettl = smtp.starttls()
        print(f"Start TLS connection: {status_codettl}, {responsettl}")

        status_codelogin, responselogin = smtp.login(from_email, password)
        print(f"Logging response: {status_codelogin}, {responselogin}")

        smtp.sendmail(from_addr=from_email, to_addrs=to_email, msg=msg.as_string())
        smtp.quit()


def mail_file(file_path, status):
    if status == 'passed':
        subject = PASSED_SUBJECT
        message = PASSED_MESSAGE
    else:
        subject = FAILED_SUBJECT
        message = FAILED_MESSAGE
    if check_file_exists(file_path):
        print(f"The file exists: {file_path}")
        email_msg = create_email_message(FROM_EMAIL, TO_EMAIL, subject, message, file_path)
        send_email(HOST, PORT, FROM_EMAIL, PASSWORD, TO_EMAIL, email_msg)
    else:
        print(f"The file does not exist: {file_path}")


if __name__ == '__main__':
    file_name = os.getenv('RIALTO_TABLE_NAME')
    mail_file(file_name, 'failed')
