import json
import os
import urllib.parse
import boto3
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

TABLE_NAME = os.environ.get('TABLE_NAME', 'table-projet2')
TOPIC_ARN = os.environ.get('TOPIC_ARN')

def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)
    results = []

    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        size = record['s3']['object'].get('size', 0)
        event_time = record['eventTime']

        # 1. Extraction et stockage des metadonnees dans DynamoDB
        table.put_item(Item={
            'id': key,
            'bucket': bucket,
            'sizeBytes': size,
            'eventTime': event_time,
            'processedAt': datetime.now(timezone.utc).isoformat()
        })

        # 2. Notification via SNS
        if TOPIC_ARN:
            sns.publish(
                TopicArn=TOPIC_ARN,
                Subject='Fichier traite avec succes',
                Message=(
                    f'Fichier: {key}\n'
                    f'Bucket: {bucket}\n'
                    f'Taille: {size} octets\n'
                    f'Traite le: {event_time}'
                )
            )
        else:
            print('ATTENTION: TOPIC_ARN non defini, notification ignoree')

        results.append({'key': key, 'size': size})

    return {
        'statusCode': 200,
        'body': json.dumps({'processed': results})
    }
