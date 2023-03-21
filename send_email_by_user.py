from email.mime.text import MIMEText
from email.utils import formatdate
import smtplib
from typing import Union
from secret import OfficialGmail


class HyperLink:
    instagram = "https://www.instagram.com/_07sho.go/"

#! メール送信関数
def send_email(to_addresses:Union[str,list[str]], subject:str, body:str):
    def send_a_email(to_address:str, subject:str, body:str):
        from_address = OfficialGmail.from_gmail_addr
        #to_address = '送信先メアド(ドメインは問わない)'
        bcc = ''
        app_password = OfficialGmail.password_for_third_party
        #subject = '件名'
        #body = '内容(本文)'
        def create_message(from_addr, to_addr, bcc_addrs, subject, body):
            msg = MIMEText(body, 'html') 
            msg['Subject'] = subject
            msg['From'] = from_addr
            msg['To'] = to_addr
            msg['Bcc'] = bcc_addrs
            msg['Date'] = formatdate()
            return msg
        def send(from_addr, to_addrs, msg):
            smtpobj = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
            smtpobj.starttls()
            smtpobj.login(from_address, app_password)
            smtpobj.sendmail(from_addr, to_addrs, msg.as_string())
            smtpobj.close()
        message = create_message(from_address, to_address, bcc, subject, body)
        send(from_address, to_address, message)
    if(type(to_addresses)==list):
        # print("メール配列の値:  "+str(to_addresses))
        for to_address in to_addresses:
            send_a_email(to_address, subject, body)
            # print("bodyの値: "+ body) 
    else:
        send_a_email(to_addresses, subject, body)