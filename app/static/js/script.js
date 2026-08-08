const API_URL = 'http://localhost:5000/api';
let uploadedAttachments = [];
let currentTemplate = null;

// Frontend validation utilities
const Validator = {
    validateEmail: (email) => {
        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!email) return { valid: false, message: 'Email is required' };
        if (!emailRegex.test(email)) return { valid: false, message: 'Invalid email format' };
        if (email.length > 254) return { valid: false, message: 'Email is too long' };
        return { valid: true };
    },
    
    validateSubject: (subject) => {
        if (!subject) return { valid: false, message: 'Subject is required' };
        if (subject.trim().length === 0) return { valid: false, message: 'Subject cannot be empty' };
        if (subject.length > 998) return { valid: false, message: 'Subject is too long' };
        return { valid: true };
    },
    
    validateBody: (body) => {
        if (!body) return { valid: false, message: 'Body is required' };
        if (body.trim().length === 0) return { valid: false, message: 'Body cannot be empty' };
        if (body.length > 1000000) return { valid: false, message: 'Body is too long' };
        return { valid: true };
    },
    
    validateScheduledTime: (scheduledTime) => {
        if (!scheduledTime) return { valid: false, message: 'Scheduled time is required' };
        const scheduledDate = new Date(scheduledTime);
        if (isNaN(scheduledDate.getTime())) return { valid: false, message: 'Invalid datetime format' };
        if (scheduledDate <= new Date()) return { valid: false, message: 'Scheduled time must be in the future' };
        if (scheduledDate > new Date(new Date().setFullYear(new Date().getFullYear() + 1))) {
            return { valid: false, message: 'Scheduled time cannot be more than 1 year in the future' };
        }
        return { valid: true };
    },
    
    validateTemplateVariables: (variables) => {
        for (const [key, value] of Object.entries(variables)) {
            if (typeof key !== 'string' || key.length > 50) {
                return { valid: false, message: `Invalid variable key: ${key}` };
            }
            if (typeof value !== 'string' || value.length > 10000) {
                return { valid: false, message: `Variable value too long for: ${key}` };
            }
        }
        return { valid: true };
    },
    
    validateFile: (file) => {
        if (!file) return { valid: false, message: 'No file selected' };
        if (file.size > 25 * 1024 * 1024) return { valid: false, message: 'File size exceeds 25MB limit' };
        const safeFilenameRegex = /^[a-zA-Z0-9._-]+$/;
        if (!safeFilenameRegex.test(file.name)) {
            return { valid: false, message: 'Filename contains invalid characters' };
        }
        return { valid: true };
    }
};

function showTab(tabName, buttonElement) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab
    const targetTab = document.getElementById(tabName);
    if (targetTab) {
        targetTab.classList.add('active');
    }
    
    // Activate the clicked button
    if (buttonElement) {
        buttonElement.classList.add('active');
    }
    
    // Load data when specific tabs are opened
    if (tabName === 'templates') {
        loadTemplates();
    }
    
    if (tabName === 'analytics') {
        loadAnalytics();
    }
}

async function generateEmail() {
    const recipient = document.getElementById('recipient').value;
    const context = document.getElementById('context').value;
    const tone = document.getElementById('tone').value;
    const button = document.querySelector('button[onclick="generateEmail()"]');
    
    // Validate inputs
    const emailValidation = Validator.validateEmail(recipient);
    if (!emailValidation.valid) {
        showStatus('Email: ' + emailValidation.message, 'error');
        return;
    }
    
    if (!context || context.trim().length === 0) {
        showStatus('Context is required', 'error');
        return;
    }
    
    if (context.length > 5000) {
        showStatus('Context is too long (max 5000 characters)', 'error');
        return;
    }
    
    showLoadingState(button, 'Generate Email');
    
    try {
        const response = await fetch(`${API_URL}/generate-email`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ recipient, context, tone })
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('email-body').value = data.content;
            document.getElementById('generated-email').classList.remove('hidden');
            showStatus('Email generated successfully!', 'success');
        } else {
            showStatus('Error: ' + data.message, 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    } finally {
        resetButtonState(button);
    }
}

async function sendEmail() {
    const to = document.getElementById('recipient').value;
    const subject = document.getElementById('subject').value;
    const body = document.getElementById('email-body').value;
    
    // Validate inputs
    const emailValidation = Validator.validateEmail(to);
    if (!emailValidation.valid) {
        showStatus('Email: ' + emailValidation.message, 'error');
        return;
    }
    
    const subjectValidation = Validator.validateSubject(subject);
    if (!subjectValidation.valid) {
        showStatus('Subject: ' + subjectValidation.message, 'error');
        return;
    }
    
    const bodyValidation = Validator.validateBody(body);
    if (!bodyValidation.valid) {
        showStatus('Body: ' + bodyValidation.message, 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/send-email`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ to, subject, body, attachments: uploadedAttachments })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('Email sent successfully!', 'success');
            // Clear form
            document.getElementById('recipient').value = '';
            document.getElementById('context').value = '';
            document.getElementById('subject').value = '';
            document.getElementById('email-body').value = '';
            document.getElementById('generated-email').classList.add('hidden');
            uploadedAttachments = [];
            updateAttachmentList();
        } else {
            showStatus('Error: ' + data.message, 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    }
}

async function loadUnreadEmails() {
    try {
        const response = await fetch(`${API_URL}/unread-emails?limit=10`);
        const data = await response.json();
        
        if (data.success) {
            const emailList = document.getElementById('email-list');
            emailList.innerHTML = '';
            
            data.emails.forEach(email => {
                const emailDiv = document.createElement('div');
                emailDiv.className = 'email-item';
                emailDiv.innerHTML = `
                    <strong>From:</strong> ${email.from}<br>
                    <strong>Subject:</strong> ${email.subject}
                `;
                emailDiv.onclick = () => showEmailDetail(email);
                emailList.appendChild(emailDiv);
            });
            
            showStatus(`Loaded ${data.emails.length} unread emails`, 'success');
        } else {
            showStatus('Error: ' + data.message, 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    }
}

async function loadEmailThreads() {
    try {
        const response = await fetch(`${API_URL}/email-threads?limit=20`);
        const data = await response.json();
        
        if (data.success) {
            const threadList = document.getElementById('thread-list');
            threadList.innerHTML = '';
            
            data.threads.forEach(thread => {
                const threadDiv = document.createElement('div');
                threadDiv.className = 'thread-item';
                threadDiv.innerHTML = `
                    <strong>Subject:</strong> ${thread.subject}<br>
                    <div class="thread-meta">
                        <span>Participants: ${thread.participants.length}</span> |
                        <span>Messages: ${thread.email_count}</span> |
                        <span>Last: ${new Date(thread.last_date).toLocaleDateString()}</span>
                    </div>
                `;
                threadDiv.onclick = () => showThreadDetail(thread);
                threadList.appendChild(threadDiv);
            });
            
            showStatus(`Loaded ${data.threads.length} email threads`, 'success');
        } else {
            showStatus('Error: ' + data.message, 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    }
}

function showEmailDetail(email) {
    // Simple alert for now - could be enhanced with a modal
    alert(`From: ${email.from}\nSubject: ${email.subject}\n\n${email.body.substring(0, 200)}...`);
}

function showThreadDetail(thread) {
    const modal = document.getElementById('thread-modal');
    document.getElementById('thread-subject').textContent = thread.subject;
    document.getElementById('thread-messages').innerHTML = '';
    document.getElementById('thread-summary').innerHTML = '';
    
    // Store thread ID for summarization
    modal.dataset.threadId = thread.thread_id;
    
    // Load thread conversation
    loadThreadConversation(thread.thread_id);
    
    modal.style.display = 'block';
}

async function loadThreadConversation(threadId) {
    try {
        const response = await fetch(`${API_URL}/thread-conversation/${threadId}?limit=10`);
        const threadData = await response.json();
        
        if (threadData.success) {
            const messagesDiv = document.getElementById('thread-messages');
            messagesDiv.innerHTML = '';
            
            threadData.conversation.forEach(msg => {
                const msgDiv = document.createElement('div');
                msgDiv.className = 'thread-message';
                msgDiv.innerHTML = `
                    <div class="thread-message-header">
                        From: ${msg.from} | Date: ${new Date(msg.date).toLocaleString()}
                    </div>
                    <div class="thread-message-body">${msg.body.substring(0, 500)}${msg.body.length > 500 ? '...' : ''}</div>
                `;
                messagesDiv.appendChild(msgDiv);
            });
        } else {
            showStatus('Error: ' + threadData.message, 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    }
}

function closeThreadModal() {
    document.getElementById('thread-modal').style.display = 'none';
}

async function summarizeThread() {
    const modal = document.getElementById('thread-modal');
    const threadId = modal.dataset.threadId;
    
    if (!threadId) {
        showStatus('No thread selected', 'error');
        return;
    }
    
    try {
        // First get the thread content
        const response = await fetch(`${API_URL}/thread-conversation/${threadId}?limit=10`);
        const threadData = await response.json();
        
        if (threadData.success) {
            // Combine all messages for summarization
            const threadContent = threadData.conversation.map(msg => 
                `From: ${msg.from}\nDate: ${msg.date}\n${msg.body}`
            ).join('\n\n---\n\n');
            
            // Call summarization API
            const summaryResponse = await fetch(`${API_URL}/summarize-thread`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ thread_content: threadContent })
            });
            
            const summaryData = await summaryResponse.json();
            
            if (summaryData.success) {
                document.getElementById('thread-summary').innerHTML = `
                    <h3>Thread Summary</h3>
                    <p>${summaryData.summary}</p>
                `;
                showStatus('Thread summarized successfully', 'success');
            } else {
                showStatus('Error: ' + summaryData.message, 'error');
            }
        } else {
            showStatus('Error: ' + threadData.message, 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    }
}

function showStatus(message, type) {
    const status = document.getElementById('status');
    status.textContent = message;
    status.className = 'status ' + type;
    status.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        status.style.display = 'none';
    }, 5000);
}

function toggleScheduleOptions() {
    const scheduleToggle = document.getElementById('schedule-toggle');
    const scheduleOptions = document.getElementById('schedule-options');
    const scheduleBtn = document.getElementById('schedule-btn');
    
    if (scheduleToggle.checked) {
        scheduleOptions.classList.remove('hidden');
        scheduleBtn.classList.remove('hidden');
    } else {
        scheduleOptions.classList.add('hidden');
        scheduleBtn.classList.add('hidden');
    }
}

async function scheduleEmail() {
    const to = document.getElementById('recipient').value;
    const subject = document.getElementById('subject').value;
    const body = document.getElementById('email-body').value;
    const scheduledTime = document.getElementById('scheduled-time').value;
    
    // Validate inputs
    const emailValidation = Validator.validateEmail(to);
    if (!emailValidation.valid) {
        showStatus('Email: ' + emailValidation.message, 'error');
        return;
    }
    
    const subjectValidation = Validator.validateSubject(subject);
    if (!subjectValidation.valid) {
        showStatus('Subject: ' + subjectValidation.message, 'error');
        return;
    }
    
    const bodyValidation = Validator.validateBody(body);
    if (!bodyValidation.valid) {
        showStatus('Body: ' + bodyValidation.message, 'error');
        return;
    }
    
    const timeValidation = Validator.validateScheduledTime(scheduledTime);
    if (!timeValidation.valid) {
        showStatus('Scheduled time: ' + timeValidation.message, 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/schedule-email`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                to, 
                subject, 
                body, 
                scheduled_time: scheduledTime,
                attachments: uploadedAttachments
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus(`Email scheduled for ${new Date(scheduledTime).toLocaleString()}`, 'success');
            // Clear form
            document.getElementById('recipient').value = '';
            document.getElementById('context').value = '';
            document.getElementById('subject').value = '';
            document.getElementById('email-body').value = '';
            document.getElementById('scheduled-time').value = '';
            document.getElementById('generated-email').classList.add('hidden');
            document.getElementById('schedule-toggle').checked = false;
            toggleScheduleOptions();
            uploadedAttachments = [];
            updateAttachmentList();
        } else {
            showStatus('Error: ' + data.message, 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    }
}

async function loadScheduledEmails() {
    try {
        const response = await fetch(`${API_URL}/scheduled-emails`);
        const data = await response.json();
        
        if (data.success) {
            const scheduledList = document.getElementById('scheduled-list');
            scheduledList.innerHTML = '';
            
            if (data.scheduled_emails.length === 0) {
                scheduledList.innerHTML = '<p>No scheduled emails</p>';
                showStatus('No scheduled emails found', 'success');
                return;
            }
            
            data.scheduled_emails.forEach(email => {
                const emailDiv = document.createElement('div');
                emailDiv.className = `scheduled-item ${email.status}`;
                
                const scheduledDate = new Date(email.scheduled_time);
                const statusClass = email.status;
                
                emailDiv.innerHTML = `
                    <strong>To:</strong> ${email.to}<br>
                    <strong>Subject:</strong> ${email.subject}<br>
                    <div class="scheduled-meta">
                        <span>Scheduled: ${scheduledDate.toLocaleString()}</span> |
                        <span class="status-badge ${statusClass}">${email.status}</span>
                    </div>
                    ${email.status === 'pending' ? `<button onclick="cancelScheduledEmail('${email.schedule_id}')" style="margin-top: 10px; background: #dc3545;">Cancel</button>` : ''}
                `;
                scheduledList.appendChild(emailDiv);
            });
            
            showStatus(`Loaded ${data.scheduled_emails.length} scheduled emails`, 'success');
        } else {
            showStatus('Error: ' + data.message, 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    }
}

async function cancelScheduledEmail(scheduleId) {
    if (!confirm('Are you sure you want to cancel this scheduled email?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/cancel-scheduled-email/${scheduleId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('Scheduled email cancelled', 'success');
            loadScheduledEmails(); // Refresh the list
        } else {
            showStatus('Error: ' + data.message, 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    }
}

// Template functions
async function loadTemplates() {
    try {
        const response = await fetch(`${API_URL}/templates`);
        const data = await response.json();
        
        if (data.success) {
            const templateSelect = document.getElementById('template-select');
            const templatesList = document.getElementById('templates-list');
            
            // Update select dropdown
            templateSelect.innerHTML = '<option value="">-- Select Template --</option>';
            
            // Update templates list
            templatesList.innerHTML = '';
            
            data.templates.forEach(template => {
                // Add to select dropdown
                const option = document.createElement('option');
                option.value = template.id;
                option.textContent = template.name;
                templateSelect.appendChild(option);
                
                // Add to templates list
                const templateDiv = document.createElement('div');
                templateDiv.className = 'template-item';
                templateDiv.innerHTML = `
                    <strong>${template.name}</strong>
                    <div class="template-meta">
                        <span class="template-category">${template.category}</span> |
                        <span>${template.description}</span>
                    </div>
                    <div class="template-meta">
                        Variables: ${template.variables.join(', ')}
                    </div>
                `;
                templateDiv.onclick = () => previewTemplate(template.id);
                templatesList.appendChild(templateDiv);
            });
            
            showStatus(`Loaded ${data.templates.length} templates`, 'success');
        } else {
            showStatus('Error: ' + data.message, 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    }
}

async function loadTemplate() {
    const templateId = document.getElementById('template-select').value;
    if (!templateId) {
        currentTemplate = null;
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/templates/${templateId}`);
        const data = await response.json();
        
        if (data.success) {
            currentTemplate = data.template;
            showTemplateVariables(data.template);
        } else {
            showStatus('Error: ' + data.message, 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    }
}

function showTemplateVariables(template) {
    const modal = document.getElementById('template-modal');
    const variablesDiv = document.getElementById('template-variables');
    
    variablesDiv.innerHTML = '';
    
    template.variables.forEach(variable => {
        const formGroup = document.createElement('div');
        formGroup.className = 'form-group';
        formGroup.innerHTML = `
            <label>${variable}:</label>
            <input type="text" class="template-variable-input" data-variable="${variable}" placeholder="Enter ${variable}">
        `;
        variablesDiv.appendChild(formGroup);
    });
    
    modal.style.display = 'block';
}

function closeTemplateModal() {
    document.getElementById('template-modal').style.display = 'none';
}

async function applyTemplate() {
    if (!currentTemplate) {
        showStatus('No template selected', 'error');
        return;
    }
    
    const variables = {};
    document.querySelectorAll('.template-variable-input').forEach(input => {
        variables[input.dataset.variable] = input.value;
    });
    
    // Validate variables
    const variablesValidation = Validator.validateTemplateVariables(variables);
    if (!variablesValidation.valid) {
        showStatus('Variables: ' + variablesValidation.message, 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/templates/${currentTemplate.id}/render`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ variables })
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('subject').value = data.subject;
            document.getElementById('email-body').value = data.body;
            document.getElementById('generated-email').classList.remove('hidden');
            closeTemplateModal();
            showStatus('Template applied successfully', 'success');
        } else {
            showStatus('Error: ' + data.message, 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    }
}

async function createTemplate() {
    const templateData = {
        name: document.getElementById('template-name').value,
        description: document.getElementById('template-description').value,
        category: document.getElementById('template-category').value,
        subject: document.getElementById('template-subject').value,
        body: document.getElementById('template-body').value,
        variables: document.getElementById('template-variables').value.split(',').map(v => v.trim()).filter(v => v)
    };
    
    if (!templateData.name || !templateData.subject || !templateData.body) {
        showStatus('Please fill in required fields', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/templates`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(templateData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('Template created successfully', 'success');
            // Clear form
            document.getElementById('template-name').value = '';
            document.getElementById('template-description').value = '';
            document.getElementById('template-category').value = '';
            document.getElementById('template-subject').value = '';
            document.getElementById('template-body').value = '';
            document.getElementById('template-variables').value = '';
            loadTemplates(); // Refresh template list
        } else {
            showStatus('Error: ' + data.message, 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    }
}

// Attachment functions
async function handleAttachmentUpload() {
    const input = document.getElementById('attachment-input');
    const files = input.files;
    
    for (let file of files) {
        // Validate file
        const fileValidation = Validator.validateFile(file);
        if (!fileValidation.valid) {
            showStatus('File validation: ' + fileValidation.message, 'error');
            continue;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch(`${API_URL}/upload`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                uploadedAttachments.push(data.filepath);
                updateAttachmentList();
                showStatus(`File uploaded: ${data.filename}`, 'success');
            } else {
                showStatus('Error: ' + data.message, 'error');
            }
        } catch (error) {
            showStatus('Error: ' + error.message, 'error');
        }
    }
    
    // Clear input
    input.value = '';
}

function updateAttachmentList() {
    const attachmentList = document.getElementById('attachment-list');
    attachmentList.innerHTML = '';
    
    uploadedAttachments.forEach((filepath, index) => {
        const filename = filepath.split('/').pop();
        const attachmentDiv = document.createElement('div');
        attachmentDiv.className = 'attachment-item';
        attachmentDiv.innerHTML = `
            <span>${filename}</span>
            <button onclick="removeAttachment(${index})">Remove</button>
        `;
        attachmentList.appendChild(attachmentDiv);
    });
}

function removeAttachment(index) {
    uploadedAttachments.splice(index, 1);
    updateAttachmentList();
}

// Analytics functions
async function loadAnalytics() {
    try {
        // Load all analytics data in parallel
        const [summary, categories, dailyActivity, topContacts, templateUsage, activityLog, trends] = await Promise.all([
            fetch(`${API_URL}/analytics/summary`).then(r => r.json()),
            fetch(`${API_URL}/analytics/categories`).then(r => r.json()),
            fetch(`${API_URL}/analytics/daily-activity?days=30`).then(r => r.json()),
            fetch(`${API_URL}/analytics/top-contacts?limit=10`).then(r => r.json()),
            fetch(`${API_URL}/analytics/template-usage`).then(r => r.json()),
            fetch(`${API_URL}/analytics/activity-log?limit=20`).then(r => r.json()),
            fetch(`${API_URL}/analytics/trends?days=7`).then(r => r.json())
        ]);
        
        // Display summary
        displayAnalyticsSummary(summary.summary);
        
        // Display categories
        displayCategories(categories.categories);
        
        // Display daily activity
        displayDailyActivity(dailyActivity.daily_activity);
        
        // Display top contacts
        displayTopContacts(topContacts.top_contacts);
        
        // Display template usage
        displayTemplateUsage(templateUsage.template_usage);
        
        // Display activity log
        displayActivityLog(activityLog.activity_log);
        
        // Display trends
        displayTrends(trends.trends);
        
        showStatus('Analytics loaded successfully', 'success');
    } catch (error) {
        showStatus('Error loading analytics: ' + error.message, 'error');
    }
}

function displayAnalyticsSummary(summary) {
    const container = document.getElementById('analytics-summary');
    container.innerHTML = `
        <div class="analytics-grid">
            <div class="stat-card">
                <div class="stat-value">${summary.total_emails}</div>
                <div class="stat-label">Total Emails</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${summary.emails_sent}</div>
                <div class="stat-label">Emails Sent</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${summary.emails_received}</div>
                <div class="stat-label">Emails Received</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${summary.emails_scheduled}</div>
                <div class="stat-label">Emails Scheduled</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${summary.unique_contacts}</div>
                <div class="stat-label">Unique Contacts</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${summary.average_response_time_minutes ? summary.average_response_time_minutes.toFixed(1) + ' min' : 'N/A'}</div>
                <div class="stat-label">Avg Response Time</div>
            </div>
        </div>
    `;
}

function displayCategories(categories) {
    const container = document.getElementById('email-categories');
    const total = Object.values(categories).reduce((a, b) => a + b, 0);
    
    let html = '';
    for (const [category, count] of Object.entries(categories)) {
        const percentage = total > 0 ? (count / total * 100).toFixed(1) : 0;
        html += `
            <div class="category-bar">
                <div class="category-label">${category}</div>
                <div class="category-bar-container">
                    <div class="category-bar-fill" style="width: ${percentage}%"></div>
                </div>
                <div class="category-count">${count}</div>
            </div>
        `;
    }
    
    container.innerHTML = html || '<p>No category data available</p>';
}

function displayDailyActivity(dailyActivity) {
    const container = document.getElementById('daily-activity');
    const dates = Object.keys(dailyActivity).sort();
    const values = dates.map(date => dailyActivity[date]);
    const maxValue = Math.max(...values, 1);
    
    let html = '<div style="display: flex; align-items: flex-end; height: 150px; gap: 2px;">';
    dates.forEach(date => {
        const value = dailyActivity[date];
        const height = (value / maxValue) * 100;
        const dateObj = new Date(date);
        const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'short' });
        
        html += `
            <div style="flex: 1; display: flex; flex-direction: column; align-items: center;">
                <div style="width: 100%; background: #667eea; height: ${height}%; border-radius: 3px 3px 0 0; min-height: 2px;"></div>
                <div style="font-size: 10px; margin-top: 5px; color: #666;">${dayName}</div>
            </div>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
}

function displayTopContacts(topContacts) {
    const container = document.getElementById('top-contacts');
    
    let html = '';
    topContacts.forEach(contact => {
        html += `
            <div class="contact-item">
                <span>${contact.email}</span>
                <span>${contact.count} emails</span>
            </div>
        `;
    });
    
    container.innerHTML = html || '<p No contact data available</p>';
}

function displayTemplateUsage(templateUsage) {
    const container = document.getElementById('template-usage');
    
    let html = '';
    for (const [templateId, count] of Object.entries(templateUsage)) {
        html += `
            <div class="contact-item">
                <span>${templateId}</span>
                <span>${count} uses</span>
            </div>
        `;
    }
    
    container.innerHTML = html || '<p>No template usage data available</p>';
}

function displayActivityLog(activityLog) {
    const container = document.getElementById('activity-log');
    
    let html = '';
    activityLog.slice().reverse().forEach(activity => {
        const timestamp = new Date(activity.timestamp).toLocaleString();
        html += `
            <div class="activity-item">
                <div class="timestamp">${timestamp}</div>
                <div><strong>${activity.action}</strong></div>
                ${activity.to ? `<div>To: ${activity.to}</div>` : ''}
                ${activity.from ? `<div>From: ${activity.from}</div>` : ''}
                ${activity.category ? `<div>Category: ${activity.category}</div>` : ''}
            </div>
        `;
    });
    
    container.innerHTML = html || '<p>No activity data available</p>';
}

function displayTrends(trends) {
    const container = document.getElementById('email-trends');
    const trendClass = trends.trend_percentage >= 0 ? 'trend-up' : 'trend-down';
    const trendIcon = trends.trend_percentage >= 0 ? '↑' : '↓';
    
    container.innerHTML = `
        <div class="stat-card">
            <div class="stat-value">
                <span class="${trendClass}">${trendIcon} ${Math.abs(trends.trend_percentage)}%</span>
            </div>
            <div class="stat-label">
                Current: ${trends.current_period_emails} emails | 
                Previous: ${trends.previous_period_emails} emails
            </div>
        </div>
    `;
}

async function resetAnalytics() {
    if (!confirm('Are you sure you want to reset all analytics data? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/analytics/reset`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('Analytics data reset successfully', 'success');
            loadAnalytics(); // Reload analytics
        } else {
            showStatus('Error: ' + data.message, 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    }
}