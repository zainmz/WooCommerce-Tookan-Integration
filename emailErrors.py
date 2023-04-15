import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def sendMail(error, order_id):
    # SMTP server information
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587  # For starttls
    smtp_username = 'email.com'
    smtp_password = 'qpassword'

    # Email information
    from_address = 'email@email.com'
    to_address = 'email@email.com'
    subject = 'ERROR - Tookan Task Push System!'
    body = 'Hello\n An Error has been found\n' + 'Order ID:' + str(order_id) + "\n\n" + error
    # Create the message object
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Create the SMTP connection and send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(from_address, to_address.split(','), msg.as_string())

    print('Email sent!')
