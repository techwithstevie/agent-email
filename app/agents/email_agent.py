from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv

load_dotenv()

class EmailAgent:
    def __init__(self):
        self.llm = OllamaLLM(
            base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
            model=os.getenv('MODEL_NAME', 'llama3.2')
        )
        
        self.email_template = PromptTemplate(
            input_variables=["recipient", "context", "tone"],
            template="""
            You are an AI email assistant. Write a professional email based on the following:
            
            Recipient: {recipient}
            Context: {context}
            Tone: {tone}
            
            Write only the email body, no subject line. Keep it concise and appropriate.
            """
        )
        
        self.chain = self.email_template | self.llm | StrOutputParser()
    
    def generate_email(self, recipient, context, tone="professional"):
        """Generate email content using AI"""
        try:
            result = self.chain.invoke(
                {
                    "recipient": recipient,
                    "context": context,
                    "tone": tone
                }
            )
            return {"success": True, "content": result.strip()}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def analyze_email(self, email_content):
        """Analyze email content and suggest actions"""
        prompt = f"""
        Analyze the following email and suggest:
        1. Priority level (high/medium/low)
        2. Required action (reply/forward/archive)
        3. Brief summary
        
        Email: {email_content}
        """
        
        try:
            result = self.llm(prompt)
            return {"success": True, "analysis": result}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def summarize_email(self, email_content, max_length=150):
        """Generate a concise summary of email content"""
        summary_template = PromptTemplate(
            input_variables=["email_content", "max_length"],
            template="""
            Summarize the following email in {max_length} words or less. 
            Focus on the main points, action items, and key information.
            
            Email: {email_content}
            
            Provide only the summary, no additional commentary.
            """
        )
        
        summary_chain = summary_template | self.llm | StrOutputParser()
        
        try:
            result = summary_chain.invoke({
                "email_content": email_content,
                "max_length": max_length
            })
            return {"success": True, "summary": result.strip()}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def summarize_thread(self, thread_content):
        """Summarize an entire email thread conversation"""
        thread_template = PromptTemplate(
            input_variables=["thread_content"],
            template="""
            Summarize the following email thread conversation. Include:
            1. Main topic/purpose of the thread
            2. Key participants
            3. Important decisions or agreements made
            4. Outstanding action items
            
            Thread:
            {thread_content}
            
            Provide a comprehensive but concise summary.
            """
        )
        
        thread_chain = thread_template | self.llm | StrOutputParser()
        
        try:
            result = thread_chain.invoke({"thread_content": thread_content})
            return {"success": True, "summary": result.strip()}
        except Exception as e:
            return {"success": False, "message": str(e)}