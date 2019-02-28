import time 

import smtplib
from email.MIMEText import MIMEText

def sendEmail(keyState, mailClient):
    """Send an email. 

    Input:
    -keyState: keyState object from alerts_main
    -mailClient: str, the mail server to connect to
    """
    import smtplib
    from email.MIMEText import MIMEText

    # Adds the time to the text
    text = keyState.msg + '\n\nEmail sent on ' + time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()) + '\n'

    severity = keyState.severity

    recipients = keyState.emailAddresses

    sender = recipients[0]

    subject = "{} alert on {}" % (severity, keyState.actorKey)
    msg = MIMEText("{}\n\n{}" % (subject, text))

    msg['Subject'] = subject

    msg['From'] = "%sAlerts (SDSS-IV %s Alerts)" % (2 * (severity.capitalize(), ))

    msg['Reply-to'] = sender

    msg['To'] = ', '.join(recipients)

    # Send mail through the mail server
    try:
        s = smtplib.SMTP()
        s.connect(mailClient)
        # Send the email - real from, real to, extra headers and content ...
        s.sendmail(sender, recipients, msg.as_string())
    except Exception, e:
        logging.warn("Sending email warning: %s %s" % (msg, e))
    finally:
        s.close()