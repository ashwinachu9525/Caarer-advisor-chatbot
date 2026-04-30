from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from config import Config
from flask_session import Session
import uuid
from services.document_service import DocumentService
from services.chat_manager import ChatManager
import markdown
import os

app = Flask(__name__)
app.config.from_object(Config)


# ==========================================
# ENTERPRISE FIX: Server-Side Sessions
# Stores heavy charts/text on the server, 
# preventing the 4KB browser cookie crash.
# ==========================================
session_dir = os.path.join(app.root_path, 'flask_session')
if not os.path.exists(session_dir):
    os.makedirs(session_dir)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = session_dir # Explicitly tell it where to save
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
Session(app)
# ==========================================

chat_manager = ChatManager()

@app.before_request
def ensure_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

@app.route('/')
def index():
    has_resume = 'resume_text' in session
    return render_template('index.html', has_resume=has_resume, summary=session.get('resume_summary'))

@app.route('/upload', methods=['POST'])
def upload():
    if 'document' not in request.files:
        return "No file uploaded", 400
    
    file = request.files['document']
    provider = request.form.get('provider', 'openai')

    if file.filename != '':
        # Use our new DocumentService to handle PDF, DOCX, and TXT
        text = DocumentService.extract_text(file, file.filename)
        
        if not text.strip():
            return "Could not extract text from the document.", 400

        session['resume_text'] = text
        session['active_provider'] = provider
        chat_manager.clear_history(session['session_id'])
        
        # Generate intelligent summary AND analytics
        analysis_data = chat_manager.generate_summary(text, provider)

        # Convert the AI's Markdown response into clean HTML using Python
        raw_summary_markdown = analysis_data['summary_text']
        clean_html_summary = markdown.markdown(raw_summary_markdown)

      
        # Store in session for the frontend
        session['resume_summary'] = clean_html_summary
        session['ats_score'] = analysis_data['ats_score']
        session['chart_base64'] = analysis_data['chart_base64']
        
    return redirect(url_for('index'))

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question')
    provider = data.get('provider', session.get('active_provider', 'openai'))

    if not question:
        return jsonify({"error": "No question provided"}), 400

    resume_text = session.get('resume_text', '')
    if not resume_text:
        return jsonify({"error": "No resume context found. Please re-upload."}), 400

    try:
        answer = chat_manager.ask_question(session['session_id'], resume_text, question, provider)
        return jsonify({"question": question, "answer": answer})
    except Exception as e:
        print(f"Chat Error: {str(e)}")
        return jsonify({"error": "An error occurred generating the response."}), 500

@app.route('/clear')
def clear_session():
    chat_manager.clear_history(session.get('session_id', ''))
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True, port=5000)