import json
import os
from jinja2 import Template
from typing import Dict, List, Optional
from ..utils.validation import InputValidator

class TemplateService:
    def __init__(self, templates_dir='app/email_templates'):
        self.templates_dir = templates_dir
        try:
            self._ensure_templates_dir()
        except Exception as e:
            print(f"Warning: Could not ensure templates directory: {e}")
    
    def _ensure_templates_dir(self):
        """Ensure templates directory exists"""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
    
    def get_all_templates(self) -> Dict:
        """Get all available email templates"""
        try:
            templates = []
            if not os.path.exists(self.templates_dir):
                return {"success": True, "templates": []}
            
            for filename in os.listdir(self.templates_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.templates_dir, filename)
                    with open(filepath, 'r') as f:
                        template_data = json.load(f)
                        template_data['id'] = filename.replace('.json', '')
                        templates.append(template_data)
            
            return {"success": True, "templates": templates}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def get_template(self, template_id: str) -> Dict:
        """Get a specific template by ID"""
        try:
            filepath = os.path.join(self.templates_dir, f'{template_id}.json')
            if not os.path.exists(filepath):
                return {"success": False, "message": "Template not found"}
            
            with open(filepath, 'r') as f:
                template_data = json.load(f)
                template_data['id'] = template_id
            
            return {"success": True, "template": template_data}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def create_template(self, template_data: Dict) -> Dict:
        """Create a new email template"""
        try:
            template_id = template_data.get('id', '').lower().replace(' ', '_')
            if not template_id:
                return {"success": False, "message": "Template ID is required"}
            
            filepath = os.path.join(self.templates_dir, f'{template_id}.json')
            
            # Prepare template data
            template_to_save = {
                "name": template_data.get('name', 'Untitled'),
                "description": template_data.get('description', ''),
                "subject": template_data.get('subject', ''),
                "body": template_data.get('body', ''),
                "variables": template_data.get('variables', []),
                "category": template_data.get('category', 'custom')
            }
            
            with open(filepath, 'w') as f:
                json.dump(template_to_save, f, indent=2)
            
            return {"success": True, "message": "Template created", "template_id": template_id}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def update_template(self, template_id: str, template_data: Dict) -> Dict:
        """Update an existing template"""
        try:
            filepath = os.path.join(self.templates_dir, f'{template_id}.json')
            if not os.path.exists(filepath):
                return {"success": False, "message": "Template not found"}
            
            # Load existing template
            with open(filepath, 'r') as f:
                existing_template = json.load(f)
            
            # Update with new data
            existing_template.update({
                "name": template_data.get('name', existing_template.get('name')),
                "description": template_data.get('description', existing_template.get('description')),
                "subject": template_data.get('subject', existing_template.get('subject')),
                "body": template_data.get('body', existing_template.get('body')),
                "variables": template_data.get('variables', existing_template.get('variables')),
                "category": template_data.get('category', existing_template.get('category'))
            })
            
            with open(filepath, 'w') as f:
                json.dump(existing_template, f, indent=2)
            
            return {"success": True, "message": "Template updated"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def delete_template(self, template_id: str) -> Dict:
        """Delete a template"""
        try:
            filepath = os.path.join(self.templates_dir, f'{template_id}.json')
            if not os.path.exists(filepath):
                return {"success": False, "message": "Template not found"}
            
            os.remove(filepath)
            return {"success": True, "message": "Template deleted"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def render_template(self, template_id: str, variables: Dict) -> Dict:
        """Render a template with provided variables"""
        try:
            template_result = self.get_template(template_id)
            if not template_result['success']:
                return template_result
            
            template = template_result['template']
            
            # Render subject
            subject_template = Template(template['subject'])
            rendered_subject = subject_template.render(**variables)
            
            # Render body
            body_template = Template(template['body'])
            rendered_body = body_template.render(**variables)
            
            return {
                "success": True,
                "subject": rendered_subject,
                "body": rendered_body
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def get_templates_by_category(self, category: str) -> Dict:
        """Get templates filtered by category"""
        try:
            all_templates = self.get_all_templates()
            if not all_templates['success']:
                return all_templates
            
            filtered = [t for t in all_templates['templates'] if t.get('category') == category]
            return {"success": True, "templates": filtered}
        except Exception as e:
            return {"success": False, "message": str(e)}