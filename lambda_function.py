import json
import urllib.request
import os
import time
import boto3
from boto3.dynamodb.conditions import Key

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('chat-history')

def get_history(user_id):
    response = table.query(
        KeyConditionExpression=Key('user_id').eq(user_id),
        ScanIndexForward=False,  # newest to oldest
        Limit=6
    )
    items = response.get('Items', [])
    return list(reversed(items))  # oldest to newest

def store_message(user_id, role, content):
    table.put_item(Item={
        'user_id': user_id,
        'timestamp': int(time.time() * 1000),
        'role': role,
        'content': content
    })

def call_gemini_with_history(history):
    GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    contents = [
        {
            "role": "user" if item["role"] == "user" else "model",
            "parts": [{"text": item["content"]}]
        }
        for item in history
    ]

    data = { "contents": contents }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req) as res:
        result = json.loads(res.read())
        return result["candidates"][0]["content"]["parts"][0]["text"]


def lambda_handler(event, context):
    method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "")

    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }

    if method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({"message": "CORS preflight success"})
        }

    if method != "POST":
        return {
            "statusCode": 405,
            "headers": cors_headers,
            "body": json.dumps({"error": "Only POST requests are allowed"})
        }

    try:
        body = json.loads(event.get("body", "{}"))
        user_prompt = body.get("user_prompt")
        user_id = body.get("user_id", "default_user")  # Pass from frontend or use default

        if not user_prompt:
            return {
                "statusCode": 400,
                "headers": cors_headers,
                "body": json.dumps({"error": "Missing 'user_prompt' in request body."})
            }

        # Retrieve conversation history
        history = get_history(user_id)
        history.append({"role": "user", "content": user_prompt})

        # Call Gemini with history
        ai_reply = call_gemini_with_history(history)

        # Store messages
        store_message(user_id, "user", user_prompt)
        store_message(user_id, "bot", ai_reply)

        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({"ai_reply": ai_reply})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": str(e)})
        }
