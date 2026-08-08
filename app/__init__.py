from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from .agents.email_agent import EmailAgent
from .services.email_service import EmailService
from .services.template_service import TemplateService
from .services.analytics_service import AnalyticsService
from .utils.validation import InputValidator, ValidationError
import os
import atexit
import sys
import signal

app = Flask(__name__)
CORS(app)

# Initialize services
try:
    agent = EmailAgent()
    email_service = EmailService()
    template_service = TemplateService()
    analytics_service = AnalyticsService()
except Exception as e:
    print(f"Error initializing services: {e}")
    agent = None
    email_service = None
    template_service = None
    analytics_service = None

@app.route('/')
def index():
    return render_template('index.html')

# API endpoints
@app.route('/api/generate-email', methods=['POST'])
def generate_email():
    if not agent:
        return jsonify({"success": False, "message": "Agent not initialized"})
    
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "No data provided"})
    
    recipient = data.get('recipient')
    context = data.get('context')
    tone = data.get('tone', 'professional')
    
    # Validate inputs
    is_valid, error_message = InputValidator.validate_email(recipient)
    if not is_valid:
        return jsonify({"success": False, "message": f"Invalid email: {error_message}"})
    
    if not context or not isinstance(context, str):
        return jsonify({"success": False, "message": "Context is required and must be a string"})
    
    if len(context) > 5000:
        return jsonify({"success": False, "message": "Context is too long (max 5000 characters)"})
    
    valid_tones = ['professional', 'friendly', 'formal', 'casual']
    if tone not in valid_tones:
        return jsonify({"success": False, "message": f"Invalid tone. Must be one of: {', '.join(valid_tones)}"})
    
    result = agent.generate_email(recipient, context, tone)
    return jsonify(result)

@app.route('/api/send-email', methods=['POST'])
def send_email():
    if not email_service:
        return jsonify({"success": False, "message": "Email service not initialized"})
    
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "No data provided"})
    
    to = data.get('to')
    subject = data.get('subject')
    body = data.get('body')
    attachments = data.get('attachments', [])
    category = data.get('category', 'general')
    template_id = data.get('template_id')
    
    # Validate inputs
    is_valid, error_message = InputValidator.validate_email(to)
    if not is_valid:
        return jsonify({"success": False, "message": f"Invalid email: {error_message}"})
    
    is_valid, error_message = InputValidator.validate_subject(subject)
    if not is_valid:
        return jsonify({"success": False, "message": f"Invalid subject: {error_message}"})
    
    is_valid, error_message = InputValidator.validate_body(body)
    if not is_valid:
        return jsonify({"success": False, "message": f"Invalid body: {error_message}"})
    
    # Validate category
    is_valid, error_message = InputValidator.validate_category(category)
    if not is_valid:
        return jsonify({"success": False, "message": f"Invalid category: {error_message}"})
    
    # Validate attachments
    if attachments:
        if not isinstance(attachments, list):
            return jsonify({"success": False, "message": "Attachments must be a list"})
        
        for attachment in attachments:
            if not isinstance(attachment, str):
                return jsonify({"success": False, "message": "Each attachment must be a file path string"})
    
    result = email_service.send_email(to, subject, body, attachments)
    
    # Track analytics if email was sent successfully
    if result.get('success') and analytics_service:
        analytics_service.track_email_sent(to, category, template_id)
    
    return jsonify(result)

@app.route('/api/unread-emails', methods=['GET'])
def get_unread_emails():
    if not email_service:
        return jsonify({"success": False, "message": "Email service not initialized"})
    
    limit = request.args.get('limit', 10)
    limit = InputValidator.validate_limit(limit, default=10, max_limit=50)
    
    result = email_service.get_unread_emails(limit)
    return jsonify(result)

@app.route('/api/analyze-email', methods=['POST'])
def analyze_email():
    if not agent:
        return jsonify({"success": False, "message": "Agent not initialized"})
    data = request.json
    content = data.get('content')
    
    result = agent.analyze_email(content)
    return jsonify(result)

@app.route('/api/summarize-email', methods=['POST'])
def summarize_email():
    if not agent:
        return jsonify({"success": False, "message": "Agent not initialized"})
    data = request.json
    content = data.get('content')
    max_length = data.get('max_length', 150)
    
    result = agent.summarize_email(content, max_length)
    return jsonify(result)

@app.route('/api/summarize-thread', methods=['POST'])
def summarize_thread():
    if not agent:
        return jsonify({"success": False, "message": "Agent not initialized"})
    data = request.json
    thread_content = data.get('thread_content')
    
    result = agent.summarize_thread(thread_content)
    return jsonify(result)

@app.route('/api/email-threads', methods=['GET'])
def get_email_threads():
    if not email_service:
        return jsonify({"success": False, "message": "Email service not initialized"})
    
    limit = request.args.get('limit', 20)
    limit = InputValidator.validate_limit(limit, default=20, max_limit=100)
    
    result = email_service.get_email_threads(limit)
    return jsonify(result)

@app.route('/api/thread-conversation/<thread_id>', methods=['GET'])
def get_thread_conversation(thread_id):
    if not email_service:
        return jsonify({"success": False, "message": "Email service not initialized"})
    
    # Validate thread ID
    is_valid, error_message = InputValidator.validate_template_id(thread_id)
    if not is_valid:
        return jsonify({"success": False, "message": f"Invalid thread ID: {error_message}"})
    
    email_limit = request.args.get('limit', 10)
    email_limit = InputValidator.validate_limit(email_limit, default=10, max_limit=50)
    
    result = email_service.get_thread_conversation(thread_id, email_limit)
    return jsonify(result)

@app.route('/api/schedule-email', methods=['POST'])
def schedule_email():
    if not email_service:
        return jsonify({"success": False, "message": "Email service not initialized"})
    
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "No data provided"})
    
    to = data.get('to')
    subject = data.get('subject')
    body = data.get('body')
    scheduled_time = data.get('scheduled_time')
    attachments = data.get('attachments', [])
    
    # Validate inputs
    is_valid, error_message = InputValidator.validate_email(to)
    if not is_valid:
        return jsonify({"success": False, "message": f"Invalid email: {error_message}"})
    
    is_valid, error_message = InputValidator.validate_subject(subject)
    if not is_valid:
        return jsonify({"success": False, "message": f"Invalid subject: {error_message}"})
    
    is_valid, error_message = InputValidator.validate_body(body)
    if not is_valid:
        return jsonify({"success": False, "message": f"Invalid body: {error_message}"})
    
    is_valid, error_message, scheduled_dt = InputValidator.validate_schedule_time(scheduled_time)
    if not is_valid:
        return jsonify({"success": False, "message": f"Invalid scheduled time: {error_message}"})
    
    # Validate attachments
    if attachments:
        if not isinstance(attachments, list):
            return jsonify({"success": False, "message": "Attachments must be a list"})
        
        for attachment in attachments:
            if not isinstance(attachment, str):
                return jsonify({"success": False, "message": "Each attachment must be a file path string"})
    
    result = email_service.schedule_email(to, subject, body, scheduled_dt, attachments)
    return jsonify(result)

@app.route('/api/cancel-scheduled-email/<schedule_id>', methods=['DELETE'])
def cancel_scheduled_email(schedule_id):
    if not email_service:
        return jsonify({"success": False, "message": "Email service not initialized"})
    result = email_service.cancel_scheduled_email(schedule_id)
    return jsonify(result)

@app.route('/api/scheduled-emails', methods=['GET'])
def get_scheduled_emails():
    if not email_service:
        return jsonify({"success": False, "message": "Email service not initialized"})
    result = email_service.get_scheduled_emails()
    return jsonify(result)

# Template endpoints
@app.route('/api/templates', methods=['GET'])
def get_templates():
    if not template_service:
        return jsonify({"success": False, "message": "Template service not initialized"})
    result = template_service.get_all_templates()
    return jsonify(result)

@app.route('/api/templates/<template_id>', methods=['GET'])
def get_template(template_id):
    if not template_service:
        return jsonify({"success": False, "message": "Template service not initialized"})
    result = template_service.get_template(template_id)
    return jsonify(result)

@app.route('/api/templates', methods=['POST'])
def create_template():
    if not template_service:
        return jsonify({"success": False, "message": "Template service not initialized"})
    
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "No data provided"})
    
    # Validate template name
    name = data.get('name')
    is_valid, error_message = InputValidator.validate_template_name(name)
    if not is_valid:
        return jsonify({"success": False, "message": f"Invalid template name: {error_message}"})
    
    # Validate subject and body exist
    if not data.get('subject'):
        return jsonify({"success": False, "message": "Template subject is required"})
    
    if not data.get('body'):
        return jsonify({"success": False, "message": "Template body is required"})
    
    result = template_service.create_template(data)
    return jsonify(result)

@app.route('/api/templates/<template_id>', methods=['PUT'])
def update_template(template_id):
    if not template_service:
        return jsonify({"success": False, "message": "Template service not initialized"})
    
    # Validate template ID
    is_valid, error_message = InputValidator.validate_template_id(template_id)
    if not is_valid:
        return jsonify({"success": False, "message": f"Invalid template ID: {error_message}"})
    
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "No data provided"})
    
    result = template_service.update_template(template_id, data)
    return jsonify(result)

@app.route('/api/templates/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    if not template_service:
        return jsonify({"success": False, "message": "Template service not initialized"})
    
    # Validate template ID
    is_valid, error_message = InputValidator.validate_template_id(template_id)
    if not is_valid:
        return jsonify({"success": False, "message": f"Invalid template ID: {error_message}"})
    
    result = template_service.delete_template(template_id)
    return jsonify(result)

@app.route('/api/templates/<template_id>/render', methods=['POST'])
def render_template_endpoint(template_id):
    if not template_service:
        return jsonify({"success": False, "message": "Template service not initialized"})
    
    # Validate template ID
    is_valid, error_message = InputValidator.validate_template_id(template_id)
    if not is_valid:
        return jsonify({"success": False, "message": f"Invalid template ID: {error_message}"})
    
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "No data provided"})
    
    variables = data.get('variables', {})
    
    # Validate variables
    is_valid, error_message = InputValidator.validate_template_variables(variables)
    if not is_valid:
        return jsonify({"success": False, "message": f"Invalid variables: {error_message}"})
    
    result = template_service.render_template(template_id, variables)
    return jsonify(result)

@app.route('/api/templates/category/<category>', methods=['GET'])
def get_templates_by_category(category):
    if not template_service:
        return jsonify({"success": False, "message": "Template service not initialized"})
    result = template_service.get_templates_by_category(category)
    return jsonify(result)

# File upload endpoint
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if not email_service:
        return jsonify({"success": False, "message": "Email service not initialized"})
    
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file provided"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"})
    
    # Validate filename
    is_valid, error_message = InputValidator.validate_filename(file.filename)
    if not is_valid:
        return jsonify({"success": False, "message": f"Invalid filename: {error_message}"})
    
    # Validate file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    is_valid, error_message = InputValidator.validate_file_size(file_size)
    if not is_valid:
        return jsonify({"success": False, "message": f"Invalid file size: {error_message}"})
    
    result = email_service.save_uploaded_file(file)
    return jsonify(result)

# Analytics endpoints
@app.route('/api/analytics/summary', methods=['GET'])
def get_analytics_summary():
    if not analytics_service:
        return jsonify({"success": False, "message": "Analytics service not initialized"})
    result = analytics_service.get_analytics_summary()
    return jsonify(result)

@app.route('/api/analytics/categories', methods=['GET'])
def get_email_categories():
    if not analytics_service:
        return jsonify({"success": False, "message": "Analytics service not initialized"})
    result = analytics_service.get_email_categories()
    return jsonify(result)

@app.route('/api/analytics/daily-activity', methods=['GET'])
def get_daily_activity():
    if not analytics_service:
        return jsonify({"success": False, "message": "Analytics service not initialized"})
    
    days = request.args.get('days', 30)
    days = InputValidator.validate_limit(days, default=30, max_limit=365)
    
    result = analytics_service.get_daily_activity(days)
    return jsonify(result)

@app.route('/api/analytics/top-contacts', methods=['GET'])
def get_top_contacts():
    if not analytics_service:
        return jsonify({"success": False, "message": "Analytics service not initialized"})
    
    limit = request.args.get('limit', 10)
    limit = InputValidator.validate_limit(limit, default=10, max_limit=50)
    
    result = analytics_service.get_top_contacts(limit)
    return jsonify(result)

@app.route('/api/analytics/template-usage', methods=['GET'])
def get_template_usage():
    if not analytics_service:
        return jsonify({"success": False, "message": "Analytics service not initialized"})
    result = analytics_service.get_template_usage()
    return jsonify(result)

@app.route('/api/analytics/activity-log', methods=['GET'])
def get_activity_log():
    if not analytics_service:
        return jsonify({"success": False, "message": "Analytics service not initialized"})
    
    limit = request.args.get('limit', 50)
    limit = InputValidator.validate_limit(limit, default=50, max_limit=200)
    
    result = analytics_service.get_activity_log(limit)
    return jsonify(result)

@app.route('/api/analytics/hourly-activity', methods=['GET'])
def get_hourly_activity():
    if not analytics_service:
        return jsonify({"success": False, "message": "Analytics service not initialized"})
    result = analytics_service.get_hourly_activity()
    return jsonify(result)

@app.route('/api/analytics/trends', methods=['GET'])
def get_analytics_trends():
    if not analytics_service:
        return jsonify({"success": False, "message": "Analytics service not initialized"})
    
    days = request.args.get('days', 7)
    days = InputValidator.validate_limit(days, default=7, max_limit=90)
    
    result = analytics_service.get_analytics_trends(days)
    return jsonify(result)

@app.route('/api/analytics/reset', methods=['POST'])
def reset_analytics():
    if not analytics_service:
        return jsonify({"success": False, "message": "Analytics service not initialized"})
    result = analytics_service.reset_analytics()
    return jsonify(result)

if __name__ == '__main__':
    # Shutdown scheduler when app exits
    def shutdown_scheduler():
        if email_service and hasattr(email_service, 'scheduler') and email_service.scheduler:
            email_service.scheduler.shutdown()
    
    atexit.register(shutdown_scheduler)
    
    # Handle signals for graceful shutdown
    def handle_signal(sig_num, frame):
        shutdown_scheduler()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    app.run(debug=True, port=5000)