import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from imapclient import IMAPClient
import email
from email.header import decode_header
import os
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import uuid
import mimetypes
from ..utils.validation import InputValidator

load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.imap_host = os.getenv('IMAP_HOST')
        self.imap_user = os.getenv('IMAP_USER')
        self.imap_password = os.getenv('IMAP_PASSWORD')
        
        # Initialize scheduler for email scheduling
        try:
            self.scheduler = BackgroundScheduler()
            self.scheduler.start()
            self.scheduled_emails = {}  # Store scheduled email info
        except Exception as e:
            print(f"Warning: Could not initialize scheduler: {e}")
            self.scheduler = None
            self.scheduled_emails = {}
        
        # Upload directory for attachments
        self.upload_dir = 'app/uploads'
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def send_email(self, to, subject, body, attachments=None):
        """Send an email using SMTP with optional attachments"""
        try:
            # Additional service-level validation
            if not self.smtp_user or not self.smtp_password:
                return {"success": False, "message": "SMTP credentials not configured"}
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = to
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments if provided
            if attachments:
                for attachment_path in attachments:
                    if os.path.exists(attachment_path):
                        self._add_attachment(msg, attachment_path)
            
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return {"success": True, "message": f"Email sent to {to}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def get_unread_emails(self, limit=10):
        """Fetch unread emails using IMAP"""
        try:
            with IMAPClient(self.imap_host) as client:
                client.login(self.imap_user, self.imap_password)
                client.select_folder('INBOX')
                
                messages = client.search(['UNSEEN'])
                emails = []
                
                for msg_id in messages[:limit]:
                    raw_message = client.fetch([msg_id], ['RFC822'])
                    email_data = self._parse_email(raw_message[msg_id][b'RFC822'])
                    email_data['id'] = msg_id
                    emails.append(email_data)
                
                return {"success": True, "emails": emails}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def get_email_threads(self, limit=20):
        """Fetch emails grouped by thread"""
        try:
            with IMAPClient(self.imap_host) as client:
                client.login(self.imap_user, self.imap_password)
                client.select_folder('INBOX')
                
                messages = client.search(['ALL'])
                emails = []
                
                for msg_id in messages[:limit]:
                    raw_message = client.fetch([msg_id], ['RFC822'])
                    email_data = self._parse_email(raw_message[msg_id][b'RFC822'])
                    email_data['id'] = msg_id
                    emails.append(email_data)
                
                threads = self._group_by_thread(emails)
                return {"success": True, "threads": threads}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def get_thread_conversation(self, thread_id, email_limit=10):
        """Get all emails in a specific thread"""
        try:
            with IMAPClient(self.imap_host) as client:
                client.login(self.imap_user, self.imap_password)
                client.select_folder('INBOX')
                
                # Search for emails with the same thread ID or subject
                messages = client.search(['ALL'])
                conversation_emails = []
                
                for msg_id in messages:
                    raw_message = client.fetch([msg_id], ['RFC822'])
                    email_data = self._parse_email(raw_message[msg_id][b'RFC822'])
                    email_data['id'] = msg_id
                    
                    # Match by thread ID or subject (for threading)
                    if email_data.get('thread_id') == thread_id or \
                       email_data.get('subject', '').startswith(thread_id):
                        conversation_emails.append(email_data)
                
                # Sort by date
                conversation_emails.sort(key=lambda x: x.get('date', ''))
                
                return {"success": True, "conversation": conversation_emails[:email_limit]}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _parse_email(self, raw_email):
        """Parse raw email content and extract headers"""
        msg = email.message_from_bytes(raw_email)
        
        def decode_header_value(header_value):
            if header_value is None:
                return ""
            decoded_parts = decode_header(header_value)
            decoded_string = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
                else:
                    decoded_string += str(part)
            return decoded_string
        
        subject = decode_header_value(msg.get('Subject', ''))
        from_addr = decode_header_value(msg.get('From', ''))
        to_addr = decode_header_value(msg.get('To', ''))
        date = msg.get('Date', '')
        message_id = msg.get('Message-ID', '')
        references = msg.get('References', '')
        in_reply_to = msg.get('In-Reply-To', '')
        
        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = str(msg.get_payload())
        
        # Generate thread ID from Message-ID, References, or In-Reply-To
        thread_id = message_id
        if references:
            thread_id = references.split()[0] if isinstance(references, str) else references
        elif in_reply_to:
            thread_id = in_reply_to
        
        return {
            'subject': subject,
            'from': from_addr,
            'to': to_addr,
            'date': date,
            'body': body,
            'message_id': message_id,
            'thread_id': thread_id,
            'references': references,
            'in_reply_to': in_reply_to
        }
    
    def _group_by_thread(self, emails):
        """Group emails by thread ID or subject"""
        threads = defaultdict(list)
        
        for email in emails:
            thread_id = email.get('thread_id', email.get('message_id', ''))
            if not thread_id:
                # Fallback to subject-based threading
                subject = email.get('subject', '').lower()
                # Remove common prefixes for better grouping
                subject = subject.replace('re:', '').replace('fw:', '').strip()
                thread_id = subject
            
            threads[thread_id].append(email)
        
        # Convert to list and sort by most recent
        thread_list = []
        for thread_id, thread_emails in threads.items():
            thread_emails.sort(key=lambda x: x.get('date', ''), reverse=True)
            thread_list.append({
                'thread_id': thread_id,
                'subject': thread_emails[0].get('subject', 'No Subject'),
                'participants': list(set([e.get('from', '') for e in thread_emails])),
                'email_count': len(thread_emails),
                'last_date': thread_emails[0].get('date', ''),
                'emails': thread_emails
            })
        
        # Sort threads by most recent activity
        thread_list.sort(key=lambda x: x['last_date'], reverse=True)
        
        return thread_list
    
    def schedule_email(self, to, subject, body, scheduled_time, attachments=None):
        """Schedule an email to be sent at a specific time with optional attachments"""
        try:
            # Validate scheduled time
            if isinstance(scheduled_time, str):
                scheduled_time = datetime.fromisoformat(scheduled_time)
            
            if scheduled_time < datetime.now():
                return {"success": False, "message": "Scheduled time must be in the future"}
            
            # Generate unique ID for this scheduled email
            schedule_id = str(uuid.uuid4())
            
            # Store email details
            self.scheduled_emails[schedule_id] = {
                'to': to,
                'subject': subject,
                'body': body,
                'scheduled_time': scheduled_time.isoformat(),
                'status': 'pending',
                'attachments': attachments or []
            }
            
            # Schedule the email
            self.scheduler.add_job(
                self._send_scheduled_email,
                'date',
                run_date=scheduled_time,
                args=[schedule_id],
                id=schedule_id
            )
            
            return {
                "success": True,
                "message": f"Email scheduled for {scheduled_time}",
                "schedule_id": schedule_id,
                "scheduled_time": scheduled_time.isoformat()
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def cancel_scheduled_email(self, schedule_id):
        """Cancel a scheduled email"""
        try:
            if schedule_id not in self.scheduled_emails:
                return {"success": False, "message": "Scheduled email not found"}
            
            if self.scheduled_emails[schedule_id]['status'] != 'pending':
                return {"success": False, "message": "Email has already been sent or cancelled"}
            
            # Remove from scheduler
            self.scheduler.remove_job(schedule_id)
            
            # Update status
            self.scheduled_emails[schedule_id]['status'] = 'cancelled'
            
            return {"success": True, "message": "Scheduled email cancelled"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def get_scheduled_emails(self):
        """Get all scheduled emails"""
        try:
            scheduled_list = []
            for schedule_id, email_info in self.scheduled_emails.items():
                scheduled_list.append({
                    'schedule_id': schedule_id,
                    'to': email_info['to'],
                    'subject': email_info['subject'],
                    'scheduled_time': email_info['scheduled_time'],
                    'status': email_info['status']
                })
            
            return {"success": True, "scheduled_emails": scheduled_list}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _send_scheduled_email(self, schedule_id):
        """Internal method to send a scheduled email"""
        try:
            if schedule_id not in self.scheduled_emails:
                return
            
            email_info = self.scheduled_emails[schedule_id]
            
            # Send the email with attachments
            result = self.send_email(
                email_info['to'],
                email_info['subject'],
                email_info['body'],
                email_info.get('attachments')
            )
            
            # Update status
            if result['success']:
                self.scheduled_emails[schedule_id]['status'] = 'sent'
                self.scheduled_emails[schedule_id]['sent_time'] = datetime.now().isoformat()
            else:
                self.scheduled_emails[schedule_id]['status'] = 'failed'
                self.scheduled_emails[schedule_id]['error'] = result['message']
                
        except Exception as e:
            if schedule_id in self.scheduled_emails:
                self.scheduled_emails[schedule_id]['status'] = 'failed'
                self.scheduled_emails[schedule_id]['error'] = str(e)
    
    def _add_attachment(self, msg, file_path):
        """Add an attachment to an email message"""
        try:
            # Get the file's MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'
            
            main_type, sub_type = mime_type.split('/', 1)
            
            # Read the file
            with open(file_path, 'rb') as f:
                attachment = MIMEBase(main_type, sub_type)
                attachment.set_payload(f.read())
            
            # Encode the attachment
            encoders.encode_base64(attachment)
            
            # Add header
            filename = os.path.basename(file_path)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(attachment)
        except Exception as e:
            print(f"Error adding attachment {file_path}: {str(e)}")
    
    def save_uploaded_file(self, file):
        """Save an uploaded file to the upload directory"""
        try:
            if not file:
                return {"success": False, "message": "No file provided"}
            
            # Validate filename
            is_valid, error_message = InputValidator.validate_filename(file.filename)
            if not is_valid:
                return {"success": False, "message": f"Invalid filename: {error_message}"}
            
            # Generate safe filename
            safe_filename = str(uuid.uuid4()) + '_' + file.filename
            filepath = os.path.join(self.upload_dir, safe_filename)
            
            # Save file
            file.save(filepath)
            
            return {"success": True, "filepath": filepath, "filename": file.filename}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def delete_file(self, filepath):
        """Delete a file from the upload directory"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return {"success": True, "message": "File deleted"}
            return {"success": False, "message": "File not found"}
        except Exception as e:
            return {"success": False, "message": str(e)}