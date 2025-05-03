import smtplib
import sys

import base64
from datetime import datetime

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from cryptography.fernet import Fernet
from urllib.parse import quote

sys.path.append("../")
sys.path.append("../pytavia_core"    )

from pytavia_core import config

#dont change below the standart
def send() :    
    try:
        # Create the email headers
        my_email= "bersihinyabang@gmail.com"
        ur_pass = "mxfk ezha kgjh sixk"

        with smtplib.SMTP_SSL('smtp.gmail.com',465) as connection:
            connection.login(user=my_email,password=ur_pass)
            connection.sendmail(from_addr=my_email,to_addrs="gomgom223@gmail.com",msg="Subject:apa kabar mas broa")
          
    except Exception as e:
        print(f'Error: {e}')
    return 
# end def

def send_verification_email(params):
    try:
        # Your Gmail credentials
        my_email = "bersihinyabang@gmail.com"
        my_password = "mxfk ezha kgjh sixk"  # Replace with your actual password
        receiver_email = params["email"]  
        # Email content
        subject = "Verification Email your dating account"
        body = "Your verification code is: "+params["unique_4_number"]
        sender_name = "Datingapp Team's"

        # Setup the MIME
        message = MIMEMultipart()
        message['From'] = my_email
        message['To'] = receiver_email
        message['Subject'] = subject

        # Attach the body to the email
        message.attach(MIMEText(body, 'plain'))

        # Create SMTP session for sending the mail
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(my_email, my_password)
            smtp.sendmail(my_email, receiver_email, message.as_string())
            print("Verification email sent successfully.")
            return True  # Return True if email sent successfully

    except Exception as e:
        print(f'Error sending email: {e}')
        return False  # Return False if there was an error



def attach_send(params):
    to_email   = params["to"       ]
    subject    = params["subject"  ]
    filename   = params["filename" ]
    attachment = params["pdf"      ]
    message    = params["html"     ]

    pdfAttachment = MIMEApplication(attachment, _subtype = 'pdf')
    pdfAttachment.add_header('content-disposition', 'attachment',
        filename=(filename))

    msg = MIMEMultipart('mixed')
    msg['Subject'] = subject
    msg['To'     ] = to_email
    msg['From'   ] = "bersihinyabang@gmail.com"

    html_email    = MIMEText(message, 'html')
    msg.attach( html_email )
    msg.attach( pdfAttachment )

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login   ("bersihinyabang@gmail.com", "qwertytrewq123")
    server.sendmail("bersihinyabang@gmail.com", to_email , msg.as_string())
    server.quit()
# end def


def send_reset_password_via_email(params):
    try:
        # Use a securely stored key (DO NOT regenerate every time)
        SECRET_KEY = b'KD1wZ6X1zRb9-jVnTr_a3C_sPlkDdGo5aMu8Hq4FR3A='  # Replace with your own securely stored key
        fernet = Fernet(SECRET_KEY)

        my_email = "bersihinyabang@gmail.com"
        my_password = "mxfk ezha kgjh sixk"
        receiver_email = params["email"]
        contact_url = "https://adventmatch.com/contact"

        # Combine email + timestamp for extra validation during decryption
        payload = f"{receiver_email}|{datetime.now().isoformat()}"
        encrypted_payload = fernet.encrypt(payload.encode()).decode()

        # 🔒 Encode token safely for URL (avoid incorrect padding issues)
        token_encoded = quote(encrypted_payload)

        # 🔗 Reset link
        reset_link = f"https://adventmatch.com/resetpassword?token_reset_ps={token_encoded}"

        # ✉️ Email content
        subject = "Reset Your Password - adventmatch.com"
        body = f"""
        <html>
        <body>
            <hr><b>Reset your password at adventmatch.com</b>
            <br /><br />Hello! You requested to reset your password. Click the button below:
            <br /><br />
            <a href='{reset_link}' style='padding: 10px 28px; color: #fff; background:#7A32B2; text-decoration: none; border-radius: 5px;'>
                Reset Password
            </a>
            <br /><br /><b>Can't see the button?</b> Paste this link into your browser:
            <br />{reset_link}
            <br /><br />If you did not request this, you can safely ignore this email.
            <br /><br />Need help? <a href='{contact_url}'>Contact us</a>.
        </body>
        </html>
        """

        message = MIMEMultipart()
        message['From'] = my_email
        message['To'] = receiver_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'html'))

        # 📤 Send email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(my_email, my_password)
            smtp.sendmail(my_email, receiver_email, message.as_string())
            print("Reset password email sent successfully.")
            return "success"

    except Exception as e:
        print(params)
        print(f'Error sending email: {e}')
        return "failed"

