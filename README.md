# webhook-repo

This repository contains a Flask application that receives GitHub webhook events and stores them in MongoDB. It also provides a web interface to view recent actions.

## Prerequisites

- Python 3.8 or higher
- [pip](https://pip.pypa.io/en/stable/)
- [MongoDB](https://www.mongodb.com/) instance (local or cloud, e.g., MongoDB Atlas)
- GitHub repository (for webhook integration)

## Setup Instructions

1. **Clone the repository**

```sh
git clone <this-repo-url>
cd webhook-repo
```

2. **Create and activate a virtual environment (optional but recommended)**

```sh
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies**

```sh
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file in the root of the `webhook-repo` directory with the following content:

```
MONGODB_CONNECTION_STRING=<your-mongodb-connection-string>
```

Replace `<your-mongodb-connection-string>` with your actual MongoDB URI.

5. **Run the Flask app**

```sh
python app.py
```

The app will start on `http://127.0.0.1:5000/` by default.

6. **Set up the GitHub webhook using ngrok**

- Download and install [ngrok](https://ngrok.com/).
- Start ngrok to tunnel your local Flask server:

```sh
ngrok http 5000
```

- Copy the HTTPS forwarding URL provided by ngrok (e.g., `https://abcd1234.ngrok.io`).
- Go to your GitHub repository settings > Webhooks > Add webhook.
- Set the Payload URL to `https://<your-ngrok-subdomain>.ngrok.io/webhook`
- Set Content type to `application/json`
- Choose events you want to send (e.g., push, pull request)
- Save the webhook

## Viewing Actions

- Open `http://127.0.0.1:5000/` in your browser to see the latest actions received from GitHub.

## Notes

- Ensure your MongoDB instance is running and accessible from your machine.
- For GitHub webhooks to reach your local server, you must use ngrok or a similar tunneling service.
- The app only displays the most recent actions within the last 24 hours and avoids duplicates.
