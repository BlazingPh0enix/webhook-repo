from flask import Flask, jsonify, request, render_template
from pymongo import MongoClient, DESCENDING
import json
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

connection_uri = os.getenv("MONGODB_CONNECTION_STRING")
client = MongoClient(connection_uri)
db = client["webhook_db"]
collection = db["webhook_collection"]

def format_timestamp(timestamp):
    try:
        if isinstance(timestamp, str) and timestamp.endswith('Z'):
            timestamp = timestamp[:-1] + '+00:00'
        dt = datetime.fromisoformat(timestamp)
        dt_utc = dt.astimezone(timezone.utc)
        day = dt_utc.day
        if 4 <= day <= 20 or 24 <= day <= 30:
            suffix = 'th'
        else:
            suffix = ['st', 'nd', 'rd'][day % 10 - 1]
        formatted_date = dt_utc.strftime(f"{day}{suffix} %B %Y - %I:%M %p UTC")
        return formatted_date
    except Exception:
        return timestamp

@app.route('/')
def index():
    try:
        actions = list(collection.find().sort("timestamp", DESCENDING).limit(10))

        formatted_actions = []
        for action in actions:
            formatted_action = {
                'id': str(action['_id']),
                'action': action['action'],
                'author': action['author'],
                'timestamp': action['timestamp'],
                'from_branch': action.get('from_branch', ''),
                'to_branch': action.get('to_branch', ''),
                'repository': action.get('repository', ''),
                'formatted_timestamp': action.get('formatted_timestamp', '')
            }
            formatted_actions.append(formatted_action)

        return render_template('index.html', actions=formatted_actions)
    except Exception as e:
        return render_template('index.html', actions=[], error=str(e))

@app.route('/api/actions', methods=['GET'])
def get_actions():
    try:
        actions = list(collection.find().sort("timestamp", DESCENDING))
        for action in actions:
            action['_id'] = str(action['_id'])
        return jsonify({'success': True, 'actions': actions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        payload = request.json
        event_type = request.headers.get('X-GitHub-Event')
        if not payload or not event_type:
            return jsonify({"status": "error", "message": "Invalid payload or event type"}), 400
        
        if event_type == 'push':
            action_data = process_push_event(payload)
        elif event_type == 'pull_request':
            action_data = process_pull_request_event(payload)
        else:
            print(f"Unhandled event type: {event_type}")
            return jsonify({"status": "ignored", "message": f"Event type {event_type} not handled"}), 200
        
        if action_data:
            result = collection.insert_one(action_data)
            print(f"Action stored with ID: {result.inserted_id}")
            return jsonify({'message': 'Webhook processed successfully'}), 200
        
        return jsonify({'message': 'No action data to process'}), 200
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({"error": 'Internal Server Error'}), 500

def process_push_event(payload):
    try:
        author = payload.get('pusher', {}).get('name', 'Unknown')
        request_id = payload.get('head_commit', {}).get('id', 'Unknown')
        ref = payload.get('ref', '')
        to_branch = ref.split('/')[-1] if ref.startswith('refs/heads/') else ref
        timestamp = payload.get('head_commit', {}).get('timestamp', timezone.utc)
        formatted_time = format_timestamp(timestamp)
        message = f'"{author}" pushed to "{to_branch}" on {formatted_time}'

        action_data = {
            'request_id': request_id,
            'author': author,
            'action': 'PUSH',
            'from_branch': '',
            'to_branch': to_branch,
            'timestamp': timestamp,
            'message': message
        }
        return action_data
    except Exception as e:
        print(f"Error processing push event: {e}")
        return None

def process_pull_request_event(payload):
    try:
        request_id = payload.get('pull_request', {}).get('id', 'Unknown')
        pr_data = payload.get('pull_request', {})
        action = payload.get('action', 'Unknown')
        author = pr_data.get('user', {}).get('login', 'Unknown')
        from_branch = pr_data.get('head', {}).get('ref', 'Unknown')
        to_branch = pr_data.get('base', {}).get('ref', 'Unknown')

        if action == 'opened':
            timestamp = pr_data.get('created_at', timezone.utc)
            formatted_time = format_timestamp(timestamp)
            action_type = 'PULL_REQUEST'
            message = f'"{author}" submitted a pull request from "{from_branch}" to "{to_branch}" on {formatted_time}'
        elif action == 'closed' and pr_data.get('merged', False):
            timestamp = pr_data.get('merged_at', pr_data.get('created_at', timezone.utc))
            formatted_time = format_timestamp(timestamp)
            action_type = 'MERGE'
            message = f'"{author}" merged branch "{from_branch}" to "{to_branch}" on {formatted_time}'
        else:
            return None

        action_data = {
            'request_id': request_id,
            'author': author,
            'action': action_type,
            'from_branch': from_branch,
            'to_branch': to_branch,
            'timestamp': timestamp,
            'message': message
        }
        return action_data
    except Exception as e:
        print(f"Error processing pull request event: {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True)