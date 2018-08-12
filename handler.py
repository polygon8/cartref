import boto3
from botocore.exceptions import ClientError
import json
import os
import requests
import time
import uuid
import decimal

client = boto3.client('ses')
sender = os.environ['SENDER_EMAIL']
subject = os.environ['EMAIL_SUBJECT']
configset = os.environ['CONFIG_SET']
charset = 'UTF-8'

dynamodb = boto3.resource('dynamodb')

def send_mail(event, context):
    print(event)
    response = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data={
           'secret': os.environ['RECAPTCHA'],
           'response': event['recaptcha']
        }
    )
    print(response.json())

    if response.json()['success']:
        try:
            data = event['body']
            content = 'Message from {}'.format(data['email'])
            save_email(data)
            response = send_mail_to_user(data, content)
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print('Email sent! Message Id:'),
            print(response['MessageId'])
        return 'Email sent!'

def list(event, context):
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    result = table.scan()

    return {
        "statusCode": 200,
        "body": result['Items']
    }

def save_email(data):
    timestamp = int(time.time() * 1000)
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    item = {
        'id': str(uuid.uuid1()),
        'email': data['email'],
        'createdAt': timestamp,
        'updatedAt': timestamp
    }
    table.put_item(Item=item)
    return

def send_mail_to_user(data, content):
    return client.send_email(
        Source=sender,
        Destination={
            'ToAddresses': [
                data['email'],
            ],
        },
        Message={
            'Subject': {
                'Charset': charset,
                'Data': subject
            },
            'Body': {
                'Html': {
                    'Charset': charset,
                    'Data': content
                },
                'Text': {
                    'Charset': charset,
                    'Data': content
                }
            }
        }
    )
