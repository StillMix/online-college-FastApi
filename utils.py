import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(to_email: str, code: str):
    sender_email = "baranhikov888@gmail.com"
    sender_password = (
        "iiry lmje wpjx ycez"  # Это пароль для приложения, который вы получили
    )

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = "Verification Code"

    body = f"Your verification code is: {code}"
    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, message.as_string())
        server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")
