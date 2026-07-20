import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import logging
import os
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    
    def send_email_alert(self, recipient: str, subject: str, body: str) -> bool:
        """Send email alert"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent to {recipient}")
            return True
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            return False
    
    def send_telegram_alert(self, message: str) -> bool:
        """Send Telegram alert"""
        if not self.telegram_token or not self.telegram_chat_id:
            logger.error("Telegram credentials not configured")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("Telegram alert sent")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
            return False
    
    def send_risk_alert(self, risk_data: Dict) -> None:
        """Send alerts for high-risk events"""
        risk_score = risk_data.get("risk_score", 0)
        
        if risk_score > 70:
            # Prepare alert message
            subject = f"🚨 High Risk Alert: {risk_data.get('event_title', 'Supply Chain Disruption')}"
            
            body = f"""
            <h2>⚠️ High Risk Alert</h2>
            <p><strong>Event:</strong> {risk_data.get('event_title', 'Unknown')}</p>
            <p><strong>Risk Score:</strong> {risk_score:.0f}/100</p>
            <p><strong>Revenue at Risk:</strong> ${risk_data.get('revenue_exposure', 0):,.0f}M</p>
            <p><strong>Affected Suppliers:</strong> {len(risk_data.get('affected_suppliers', []))}</p>
            <p><strong>Affected Products:</strong> {len(risk_data.get('affected_products', []))}</p>
            <hr>
            <h3>Recommendations:</h3>
            <ul>
            {' '.join([f'<li>{r}</li>' for r in risk_data.get('recommendations', [])])}
            </ul>
            <hr>
            <p>Full report available in the chainSol AI dashboard.</p>
            """
            
            telegram_message = f"""
            🚨 <b>HIGH RISK ALERT</b>
            
            Event: {risk_data.get('event_title', 'Unknown')}
            Risk Score: {risk_score:.0f}/100
            Revenue at Risk: ${risk_data.get('revenue_exposure', 0):,.0f}M
            Affected Suppliers: {len(risk_data.get('affected_suppliers', []))}
            Affected Products: {len(risk_data.get('affected_products', []))}
            
            Recommendations:
            {'\n'.join([f'• {r}' for r in risk_data.get('recommendations', [])])}
            """
            
            # Send alerts
            if self.smtp_user:
                # Send to all admin users (this would be implemented with proper user querying)
                self.send_email_alert(self.smtp_user, subject, body)
            
            if self.telegram_token:
                self.send_telegram_alert(telegram_message)

# Singleton instance
alert_service = AlertService()