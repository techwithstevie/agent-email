import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)

class InputValidator:
    """Comprehensive input validation utilities"""
    
    # Email validation regex
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # URL validation regex
    URL_REGEX = re.compile(
        r'^https?://[^\s/$.?#].[^\s]*$'
    )
    
    # Safe filename regex
    SAFE_FILENAME_REGEX = re.compile(
        r'^[a-zA-Z0-9._-]+$'
    )
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """Validate email format"""
        if not email:
            return False, "Email is required"
        
        if not isinstance(email, str):
            return False, "Email must be a string"
        
        if len(email) > 254:  # RFC 5321 limit
            return False, "Email is too long"
        
        if not InputValidator.EMAIL_REGEX.match(email):
            return False, "Invalid email format"
        
        return True, None
    
    @staticmethod
    def validate_subject(subject: str) -> Tuple[bool, Optional[str]]:
        """Validate email subject"""
        if not subject:
            return False, "Subject is required"
        
        if not isinstance(subject, str):
            return False, "Subject must be a string"
        
        if len(subject) > 998:  # RFC 5322 limit
            return False, "Subject is too long (max 998 characters)"
        
        if len(subject.strip()) == 0:
            return False, "Subject cannot be empty"
        
        return True, None
    
    @staticmethod
    def validate_body(body: str) -> Tuple[bool, Optional[str]]:
        """Validate email body"""
        if not body:
            return False, "Body is required"
        
        if not isinstance(body, str):
            return False, "Body must be a string"
        
        if len(body) > 1000000:  # Reasonable limit
            return False, "Body is too long (max 1MB)"
        
        if len(body.strip()) == 0:
            return False, "Body cannot be empty"
        
        return True, None
    
    @staticmethod
    def validate_schedule_time(scheduled_time: str) -> Tuple[bool, Optional[str], Optional[datetime]]:
        """Validate scheduled time format and value"""
        if not scheduled_time:
            return False, "Scheduled time is required", None
        
        try:
            # Try parsing as ISO format
            if isinstance(scheduled_time, str):
                scheduled_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            else:
                return False, "Scheduled time must be a string", None
            
            # Check if time is in the future
            if scheduled_dt <= datetime.now():
                return False, "Scheduled time must be in the future", None
            
            # Check if time is too far in the future (more than 1 year)
            if scheduled_dt > datetime.now().replace(year=datetime.now().year + 1):
                return False, "Scheduled time cannot be more than 1 year in the future", None
            
            return True, None, scheduled_dt
            
        except ValueError as e:
            return False, f"Invalid datetime format: {str(e)}", None
    
    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, Optional[str]]:
        """Validate filename for security"""
        if not filename:
            return False, "Filename is required"
        
        if not isinstance(filename, str):
            return False, "Filename must be a string"
        
        if len(filename) > 255:
            return False, "Filename is too long"
        
        # Check for path traversal attempts
        if '..' in filename or filename.startswith('/'):
            return False, "Invalid filename: path traversal detected"
        
        # Check for safe characters
        if not InputValidator.SAFE_FILENAME_REGEX.match(filename):
            return False, "Filename contains invalid characters"
        
        return True, None
    
    @staticmethod
    def validate_file_size(size: int, max_size: int = 25 * 1024 * 1024) -> Tuple[bool, Optional[str]]:
        """Validate file size (default max 25MB)"""
        if size <= 0:
            return False, "File size must be positive"
        
        if size > max_size:
            return False, f"File size exceeds maximum allowed size ({max_size / (1024*1024)}MB)"
        
        return True, None
    
    @staticmethod
    def validate_template_id(template_id: str) -> Tuple[bool, Optional[str]]:
        """Validate template ID"""
        if not template_id:
            return False, "Template ID is required"
        
        if not isinstance(template_id, str):
            return False, "Template ID must be a string"
        
        if len(template_id) > 100:
            return False, "Template ID is too long"
        
        if not InputValidator.SAFE_FILENAME_REGEX.match(template_id):
            return False, "Template ID contains invalid characters"
        
        return True, None
    
    @staticmethod
    def validate_template_variables(variables: Dict) -> Tuple[bool, Optional[str]]:
        """Validate template variables"""
        if not isinstance(variables, dict):
            return False, "Variables must be a dictionary"
        
        for key, value in variables.items():
            if not isinstance(key, str):
                return False, f"Variable key '{key}' must be a string"
            
            if len(key) > 50:
                return False, f"Variable key '{key}' is too long"
            
            if not isinstance(value, str):
                return False, f"Variable value for '{key}' must be a string"
            
            if len(value) > 10000:
                return False, f"Variable value for '{key}' is too long"
        
        return True, None
    
    @staticmethod
    def validate_limit(limit: int, default: int = 10, max_limit: int = 100) -> int:
        """Validate and sanitize limit parameter"""
        try:
            limit = int(limit)
            if limit < 1:
                return default
            if limit > max_limit:
                return max_limit
            return limit
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def validate_category(category: str) -> Tuple[bool, Optional[str]]:
        """Validate email category"""
        if not category:
            return False, "Category is required"
        
        if not isinstance(category, str):
            return False, "Category must be a string"
        
        valid_categories = ['general', 'business', 'personal', 'work', 'social', 'promotional', 'onboarding']
        category_lower = category.lower().strip()
        
        if category_lower not in valid_categories:
            return False, f"Invalid category. Must be one of: {', '.join(valid_categories)}"
        
        return True, None
    
    @staticmethod
    def validate_template_name(name: str) -> Tuple[bool, Optional[str]]:
        """Validate template name"""
        if not name:
            return False, "Template name is required"
        
        if not isinstance(name, str):
            return False, "Template name must be a string"
        
        if len(name) > 100:
            return False, "Template name is too long"
        
        if len(name.strip()) == 0:
            return False, "Template name cannot be empty"
        
        return True, None
    
    @staticmethod
    def sanitize_html(input_string: str) -> str:
        """Basic HTML sanitization"""
        if not isinstance(input_string, str):
            return ""
        
        # Remove potentially dangerous HTML tags
        dangerous_tags = ['<script', '</script>', '<iframe', '</iframe>', '<object', '</object>', '<embed', '</embed>']
        sanitized = input_string
        
        for tag in dangerous_tags:
            sanitized = sanitized.replace(tag, '')
        
        return sanitized
    
    @staticmethod
    def validate_phone_number(phone: str) -> Tuple[bool, Optional[str]]:
        """Basic phone number validation"""
        if not phone:
            return True, None  # Phone is optional
        
        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
        
        if not cleaned.isdigit():
            return False, "Phone number must contain only digits"
        
        if len(cleaned) < 10 or len(cleaned) > 15:
            return False, "Phone number must be between 10 and 15 digits"
        
        return True, None
    
    @staticmethod
    def validate_pagination(page: int, per_page: int, max_per_page: int = 50) -> Tuple[int, int]:
        """Validate pagination parameters"""
        try:
            page = max(1, int(page))
            per_page = max(1, min(int(per_page), max_per_page))
            return page, per_page
        except (ValueError, TypeError):
            return 1, 10