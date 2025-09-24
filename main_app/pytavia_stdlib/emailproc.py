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
        subject = "Verification Code - comes.id"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #FFDE59; font-size: 28px; margin: 0;">comes.id</h1>
                    <p style="color: #666; font-size: 16px; margin: 5px 0;">Your Dating Adventure Starts Here</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; margin-bottom: 20px;">
                    <h2 style="color: #333; margin-top: 0;">Email Verification</h2>
                    <p>Hello! Thank you for joining comes.id. To complete your account setup, please use the verification code below:</p>
                    
                    <div style="text-align: center; margin: 25px 0;">
                        <div style="display: inline-block; background: #FFDE59; color: #333; padding: 15px 30px; border-radius: 8px; font-size: 24px; font-weight: bold; letter-spacing: 3px;">
                            {params["unique_4_number"]}
                        </div>
                    </div>
                    
                    <p style="margin-bottom: 0;">Enter this code in the verification field to activate your account.</p>
                </div>
                
                <div style="text-align: center; color: #666; font-size: 14px;">
                    <p>This code will expire in 10 minutes for security reasons.</p>
                    <p>If you didn't create an account with comes.id, please ignore this email.</p>
                </div>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <div style="text-align: center; color: #999; font-size: 12px;">
                    <p>© 2024 comes.id - Connecting Hearts, Creating Stories</p>
                </div>
            </div>
        </body>
        </html>
        """
        sender_name = "comes.id Team"

        # Setup the MIME
        message = MIMEMultipart()
        message['From'] = my_email
        message['To'] = receiver_email
        message['Subject'] = subject

        # Attach the body to the email
        message.attach(MIMEText(body, 'html'))

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

