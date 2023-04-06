import re
import os
import requests
from bs4 import BeautifulSoup
from google_play_scraper import app as google_app
import boto3
from botocore.exceptions import ClientError

# set up sender and recipient email addresses
sender = os.environ['SENDER_EMAIL']
recipients = os.environ['RECIPIENT_EMAILS'].split(',')

# replace with the URLs of the apps you want to check
urls = {"app1": "https://play.google.com/store/apps/details?id=com.gim.customer",
        "app2": "https://play.google.com/store/apps/details?id=com.gim.partner",
        "app3": "https://play.google.com/store/apps/details?id=com.engine.gim"}

# set up AWS SES client
ses_client = boto3.client('ses', region_name=os.environ['AWS_REGION'])


# dictionary of app versions
app_versions = {"app1": "2.1.34", "app2": "2.2.64", "app3": "1.1.18"}

# function to send email
def send_email(subject, body):
    try:
        response = ses_client.send_email(
            Destination={
                'ToAddresses': recipients,
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': 'UTF-8',
                        'Data': body,
                    },
                },
                'Subject': {
                    'Charset': 'UTF-8',
                    'Data': subject,
                },
            },
            Source=sender,
        )
    except ClientError as e:
        print(f"An error occurred while sending email: {e.response['Error']['Message']}")
        return False
    else:
        print("Email sent successfully.")
        return True

# check on Google Play Store for each app
def lambda_handler(event, context):
    for app, url in urls.items():
        try:
            # extract the app ID from the URL using regex
            match = re.search(r'id=([a-zA-Z0-9\.]+)', url)
            app_id = match.group(1)

            # query the Google Play Store API using the app ID
            result = google_app(app_id)
            if result["appId"] == app_id:
                latest_version = result["version"]
                current_version = app_versions[app]  # get current version from dictionary
                app_name = result["title"]
                if latest_version == current_version:
                    message = f"Dear concern,\n\n{app_name} is available on Google Play Store and it is upto date. No need to worry.\n\nRegards,\nTeam GIM"
                    print(message)
                    subject = f"{app_name} is available in Google Play Store"
                    send_email(subject, message)
                elif latest_version > current_version:
                    message = f"A new version of {app_name} ({latest_version}) is available on Google Play Store. Please update {app_name} on your device to version {latest_version}."
                    print(message)
                    # subject = f"{app_name} Update Required"
                    # send_email(subject, message)
                else:
                    message = f"You are using a newer version of {app_name} ({current_version}) than the one available on Google Play Store ({latest_version})."
                    print(message)
                    # subject = f"{app_name} Update Notification"
                    # send_email(subject, message)
            else:
                message = f"Dear concern,\n\n{app_name} is not available on Google Play Store, so please take the necessary steps to resolve this issue.\n\nRegards,\nTeam GIM"
                print(message)
                subject = f"{app_name} is not available on Google Play Store"
                send_email(subject, message)
        except Exception as e:
            message = f"An error occurred while checking on Google Play Store for {app_name}: {e}"
            print(message)
            subject = f"{app_name} Error while checking on Google Play Store"
            send_email(subject, message)

