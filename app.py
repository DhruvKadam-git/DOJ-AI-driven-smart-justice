import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import google.generativeai as genai
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_socketio import SocketIO
from flask_mail import Mail, Message
from pymongo import MongoClient
from google.cloud import speech
import base64
import io
import firebase_admin
from firebase_admin import credentials, auth
from functools import wraps
from dotenv import load_dotenv
import time
import random
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Allow all origins by default
socketio = SocketIO(app, cors_allowed_origins="http://127.0.0.1:5500")

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Rate limiting variables
request_timestamps = []
MAX_REQUESTS_PER_MINUTE = 10  # Conservative limit to stay under free tier
RATE_LIMIT_WINDOW = 60  # seconds

# Configure Google Generative AI with the API key
load_dotenv()  # Load environment variables from .env file
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logging.error("GOOGLE_API_KEY is not set. Exiting.")
    exit(1)

try:
    genai.configure(api_key=api_key)
except Exception as e:
    logging.error(f"Error configuring Generative AI: {e}")
    exit(1)

# Load the Gemini Pro model
try:
    model = genai.GenerativeModel("models/gemini-1.5-pro")
    chat = model.start_chat(history=[])
except Exception as e:
    logging.error(f"Error loading Gemini Pro model: {e}")
    exit(1)

# Fallback responses for when API is rate limited
FALLBACK_RESPONSES = [
    "I apologize, but I'm currently experiencing high traffic. Please try again in a moment, or you can check our knowledge base for immediate assistance.",
    "Due to high demand, I'm temporarily unavailable. Please visit our knowledge base section for legal information, or try again shortly.",
    "I'm currently processing many requests. Please wait a moment and try again, or explore our legal resources in the meantime.",
    "The system is experiencing high usage. Please try again in a few seconds, or contact our support team for immediate assistance.",
    "I'm temporarily unavailable due to high traffic. Please check back in a moment or use our knowledge base for quick answers."
]

def check_rate_limit():
    """Check if we're within rate limits"""
    global request_timestamps
    current_time = time.time()
    
    # Remove timestamps older than the rate limit window
    request_timestamps = [ts for ts in request_timestamps if current_time - ts < RATE_LIMIT_WINDOW]
    
    # Check if we're under the limit
    if len(request_timestamps) >= MAX_REQUESTS_PER_MINUTE:
        return False
    
    # Add current timestamp
    request_timestamps.append(current_time)
    return True

def get_fallback_response():
    """Get a random fallback response"""
    return random.choice(FALLBACK_RESPONSES)

def retry_with_backoff(func, max_retries=3):
    """Retry function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Rate limited, waiting {wait_time:.2f} seconds before retry {attempt + 1}")
                time.sleep(wait_time)
            else:
                raise e
    return None

bcrypt = Bcrypt(app)

# In-memory user storage with predefined users and admin credentials
users = {
    "admin": {
        "email": "admin@example.com",
        "password": bcrypt.generate_password_hash("admin123").decode('utf-8'),
        "role": "admin"
    },
    "user1": {
        "email": "user1@example.com",
        "password": bcrypt.generate_password_hash("user123").decode('utf-8'),
        "role": "user"
    },
    "user2": {
        "email": "user2@example.com",
        "password": bcrypt.generate_password_hash("user456").decode('utf-8'),
        "role": "user"
    }
}

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('EMAIL_USER')  # Your email address

mail = Mail(app)

# MongoDB connection setup
mongo_uri = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')  # Use your MongoDB URI
client = MongoClient(mongo_uri)
db = client['knowledge_base_db']  # Replace with your database name
knowledge_base_collection = db['CRUD']  # Replace with your collection name

# Initialize Firebase Admin SDK with the correct path
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    service_account_path = os.path.join(current_dir, "login2-cc64e-firebase-adminsdk-fbsvc-7424c37ec0.json")
    logger.debug(f"Looking for service account file at: {service_account_path}")
    
    if not os.path.exists(service_account_path):
        logger.error(f"Service account file not found at: {service_account_path}")
        raise FileNotFoundError(f"Service account file not found at: {service_account_path}")
    
    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred)
    logger.debug("Firebase Admin SDK initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Firebase Admin SDK: {e}")
    raise

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_token' not in session:
            return redirect(url_for('login'))
        try:
            # Verify the Firebase token
            decoded_token = auth.verify_id_token(session['user_token'])
            # Store user info in session if needed
            session['user_id'] = decoded_token['uid']
            session['email'] = decoded_token.get('email', '')
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    """Render the main index page after successful login."""
    try:
        # Get user info from session
        user_id = session.get('user_id')
        email = session.get('email')
        logger.debug(f"Rendering index for user: {email}")
        return render_template('index.html', user_email=email)
    except Exception as e:
        logger.error(f"Error rendering index: {e}")
        return redirect(url_for('login'))

@app.route('/admin')
def admin():
    """Render the admin dashboard if the user is an admin."""
    if 'username' in session and session['role'] == 'admin':
        return render_template('admin.html')
    return redirect(url_for('index'))

@app.route('/admin/<section>')
def admin_section(section):
    """Render dynamic sections of the admin page."""
    valid_sections = ['dashboard', 'live-consultancy', 'chat-room', 'user-management', 'settings', 'reports']
    
    if 'username' in session and session['role'] == 'admin':
        if section in valid_sections:
            return render_template(f'admin_{section}.html')
        else:
            return "Section not found", 404
    
    return redirect(url_for('index'))

@app.route('/user_home')
def user_home():
    """Render the user dashboard if the user is authenticated."""
    if 'username' in session and session['role'] == 'user':
        return render_template('index.html')
    return redirect(url_for('index'))

@app.route('/login', methods=['GET'])
def login():
    """Render the login page."""
    if 'user_token' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET'])
def register():
    """Render the registration page."""
    if 'user_token' in session:
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/verify-token', methods=['POST'])
def verify_token():
    """Verify Firebase token and set up session."""
    try:
        token = request.json.get('token')
        if not token:
            return jsonify({'success': False, 'error': 'No token provided'}), 400

        # Verify the Firebase token
        decoded_token = auth.verify_id_token(token)
        
        # Set session variables
        session['user_token'] = token
        session['user_id'] = decoded_token['uid']
        session['email'] = decoded_token.get('email', '')
        
        logger.debug(f"Token verified for user: {session['email']}")
        return jsonify({
            'success': True,
            'redirect': url_for('index')
        })
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 401

@app.route('/logout')
def logout():
    """Clear session and redirect to login page."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/chat', methods=['POST'])
def chat_response():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"response": "Please provide a message to get a response."})

    # Check rate limit first
    if not check_rate_limit():
        logger.warning("Rate limit exceeded, returning fallback response")
        return jsonify({
            "response": get_fallback_response(),
            "rate_limited": True,
            "retry_after": RATE_LIMIT_WINDOW
        })

    try:
        # Use retry logic with exponential backoff
        def make_api_call():
            response = chat.send_message(user_message, stream=False)
            return " ".join([chunk.text for chunk in response])
        
        bot_message = retry_with_backoff(make_api_call)
        
        if bot_message is None:
            # If all retries failed, return fallback response
            logger.error("All retry attempts failed, returning fallback response")
            return jsonify({
                "response": get_fallback_response(),
                "api_error": True
            })
        
        return jsonify({"response": bot_message})
        
    except Exception as e:
        logging.error(f"Error getting response from Gemini Pro: {e}")
        
        # Check if it's a rate limit error
        if "429" in str(e):
            return jsonify({
                "response": get_fallback_response(),
                "rate_limited": True,
                "retry_after": RATE_LIMIT_WINDOW
            })
        
        # For other errors, return a generic error message
        return jsonify({
            "response": "I'm experiencing technical difficulties. Please try again later or contact support.",
            "error": True
        })

@app.route('/live_stream')
def live_stream():
    """Render the live court streaming page."""
    return render_template('live_stream.html')

@socketio.on('create')
def on_create(data):
    room = data['room']
    join_room(room)  # Join the room
    emit('status', {'msg': f"{data['username']} created and joined the room."}, room=room)
    emit('status', {'msg': f"Room {room} has been created."}, room=room)

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)  # Join the room
    emit('status', {'msg': f"{data['username']} has entered the room."}, room=room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)  # Leave the room
    emit('status', {'msg': f"{data['username']} has left the room."}, room=room)

@socketio.on('offer')
def handle_offer(data):
    emit('offer', data, room=data['to'])

@socketio.on('answer')
def handle_answer(data):
    emit('answer', data, room=data['to'])

@socketio.on('ice-candidate')
def handle_ice_candidate(data):
    emit('ice-candidate', data, room=data['to'])

@app.route('/send-email', methods=['POST'])
def send_email():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        msg = Message(subject=f"New message from {name}",
                      recipients=[os.environ.get('EMAIL_USER')],  # Your email address
                      body=f"Name: {name}\nEmail: {email}\nMessage: {message}")
        
        try:
            mail.send(msg)
            return "Email sent successfully!"
        except Exception as e:
            logging.error(f"Error sending email: {e}")
            return "Failed to send email", 500
    else:
        logging.error(f"Method {request.method} not allowed for /send-email")
        return "Method Not Allowed", 405

@app.route('/knowledge_base')
def knowledge_base():
    return render_template('knowledge_base.html')

@app.route('/private-chat')
def private_chat():
    """Render the private chat interface."""
    return render_template('private_chat_interface.html')

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    """Handle speech input from the microphone."""
    try:
        # Get audio data from the request
        audio_data = request.json.get('audio')
        if not audio_data:
            return jsonify({'error': 'No audio data received'}), 400

        # Decode base64 audio data
        audio_bytes = base64.b64decode(audio_data.split(',')[1])
        
        # Initialize speech client
        client = speech.SpeechClient()

        # Create audio object
        audio = speech.RecognitionAudio(content=audio_bytes)

        # Configure recognition
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code="en-US",
            sample_rate_hertz=16000,
        )

        # Perform the transcription
        response = client.recognize(config=config, audio=audio)

        # Get the transcription text
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript

        return jsonify({'text': transcript})

    except Exception as e:
        logging.error(f"Error processing speech: {e}")
        return jsonify({'error': 'Failed to process speech'}), 500

@app.route('/rate-limit-status')
def rate_limit_status():
    """Check current rate limit status"""
    global request_timestamps
    current_time = time.time()
    
    # Clean up old timestamps
    request_timestamps = [ts for ts in request_timestamps if current_time - ts < RATE_LIMIT_WINDOW]
    
    remaining_requests = MAX_REQUESTS_PER_MINUTE - len(request_timestamps)
    time_until_reset = 0
    
    if request_timestamps:
        oldest_request = min(request_timestamps)
        time_until_reset = max(0, RATE_LIMIT_WINDOW - (current_time - oldest_request))
    
    return jsonify({
        "remaining_requests": max(0, remaining_requests),
        "requests_used": len(request_timestamps),
        "max_requests": MAX_REQUESTS_PER_MINUTE,
        "time_until_reset": round(time_until_reset, 2),
        "rate_limited": remaining_requests <= 0
    })

if __name__ == "__main__":
    logger.debug("Starting application...")
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
    logger.debug("Running socketio server...")
    try:
        # Try different ports if 5002 is in use
        port = 5002
        max_attempts = 5
        
        for attempt in range(max_attempts):
            try:
                logger.debug(f"Attempting to start server on port {port}")
                socketio.run(app, host='127.0.0.1', port=port, debug=True, use_reloader=False)
                break
            except OSError:
                logger.warning(f"Port {port} is in use, trying next port")
                port += 1
                if attempt == max_attempts - 1:
                    logger.error("Could not find an available port")
                    raise
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        raise
