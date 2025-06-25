# DOJ-CHATBOT

Justice at Your Fingertips: An AI-powered legal chatbot and support platform for the Department of Justice.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Setup & Installation](#setup--installation)
  - [Python Backend (Flask)](#python-backend-flask)
  - [Node.js WebSocket Server](#nodejs-websocket-server)
  - [Frontend](#frontend)
- [Environment Variables](#environment-variables)
- [Firebase Setup](#firebase-setup)
- [MongoDB Setup](#mongodb-setup)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

DOJ-CHATBOT is a web-based platform that provides legal information, live chat, video calls, and a knowledge base for users seeking justice-related support. It leverages AI (Google Gemini Pro, OpenAI) and real-time communication tools to connect users with legal experts and resources.

## Features
- **AI Chatbot**: Get instant answers to legal questions using Google Gemini Pro and OpenAI models.
- **Authentication**: Secure login and registration with Firebase Auth (email/password, Google sign-in).
- **Knowledge Base**: Searchable legal articles and resources.
- **Live Chat & Private Chat**: Real-time chat with legal experts and other users.
- **Live Video Streaming**: Video call interface for consultations.
- **Admin Panel**: Manage users, chat rooms, video calls, and appointments.
- **Email Notifications**: Send notifications and confirmations via email.
- **Rate Limiting**: Prevents abuse of the AI API.

## Tech Stack
- **Backend**: Python (Flask, Flask-SocketIO, Flask-Mail, Flask-Bcrypt, Flask-CORS, PyMongo, Google Generative AI, Google Cloud Speech, Firebase Admin SDK, python-dotenv)
- **Frontend**: HTML, CSS (Tailwind), JavaScript, Firebase Auth
- **WebSocket Server**: Node.js (`ws`)
- **Database**: MongoDB
- **AI/ML**: Google Gemini Pro, OpenAI (for QAchat.py)

## Setup & Installation

### Python Backend (Flask)
1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd DOJ-CHATBOT
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   Create a `requirements.txt` with the following (or use your preferred tool):
   ```
   Flask
   Flask-Cors
   Flask-Bcrypt
   Flask-SocketIO
   Flask-Mail
   pymongo
   google-generativeai
   google-cloud-speech
   firebase-admin
   python-dotenv
   eventlet
   ```
   Then install:
   ```bash
   pip install -r requirements.txt
   ```
4. **Set up environment variables:** See [Environment Variables](#environment-variables).
5. **Run the Flask app:**
   ```bash
   python app.py
   ```
   The app will start on `http://127.0.0.1:5002` by default.

### Node.js WebSocket Server
1. **Install Node.js dependencies:**
   ```bash
   npm install
   ```
2. **Run the WebSocket server:**
   ```bash
   node server.js
   ```
   The WebSocket server runs on `ws://localhost:8080`.

### Frontend
- All HTML templates are in the `templates/` directory.
- Static JS/CSS in `static/`.
- Open `http://127.0.0.1:5002` in your browser after starting the backend.

## Environment Variables
Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_google_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
EMAIL_USER=your_gmail_address@gmail.com
EMAIL_PASS=your_gmail_app_password
MONGODB_URI=mongodb://localhost:27017/
FLASK_SECRET_KEY=your_flask_secret_key
```

## Firebase Setup
- Place your Firebase Admin SDK JSON file (e.g., `login2-cc64e-firebase-adminsdk-xxxx.json`) in the project root.
- Update `static/firebase-config.js` and the HTML templates with your Firebase project config.
- Enable Email/Password and Google sign-in in your Firebase console.

## MongoDB Setup
- By default, the app connects to `mongodb://localhost:27017/` and uses the `knowledge_base_db` database.
- You can use a cloud MongoDB URI by setting `MONGODB_URI` in your `.env`.

## API Endpoints
See `postman_test_cases.md` for detailed request/response examples.

- `POST /chat` — Get AI-powered legal answers.
- `GET /knowledge_base` — View/search legal knowledge base.
- `GET /live_stream` — Access video call interface.
- `GET /private-chat` — Private chat with legal expert.
- `POST /send-email` — Send email notifications.
- `GET /rate-limit-status` — Check API rate limit status.
- Auth endpoints: `/login`, `/register`, `/verify-token`, `/logout`

## Testing
- Use the provided `DOJ_Chatbot_API.postman_collection.json` and `postman_test_cases.md` for API testing in Postman.
- Manual UI testing: Register/login, chat, knowledge base, video call, admin panel.

## Contributing
1. Fork the repo and create your branch: `git checkout -b feature/your-feature`
2. Commit your changes: `git commit -am 'Add new feature'`
3. Push to the branch: `git push origin feature/your-feature`
4. Open a pull request.

## License
[MIT](LICENSE)

---

**Note:**
- For production, secure your API keys and sensitive files.
- Do not commit your `.env` or Firebase admin JSON to public repositories.
- For any issues, please open an issue or contact the maintainer.
