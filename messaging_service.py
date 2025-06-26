import requests
import os
from typing import List, Dict

class WhatsAppSender:
    def __init__(self, access_token: str = None, phone_number_id: str = None):
        self.access_token = access_token or os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = phone_number_id or os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.base_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
        
    def send_message(self, to_number: str, message: str) -> bool:
        """
        Envia uma mensagem de texto via WhatsApp Business API
        """
        if not self.access_token or not self.phone_number_id:
            raise ValueError("WhatsApp access token and phone number ID are required")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Remove caracteres especiais do número
        clean_number = ''.join(filter(str.isdigit, to_number))
        
        # Adiciona código do país se não estiver presente
        if not clean_number.startswith('55'):
            clean_number = '55' + clean_number
            
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_number,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            if 'messages' in result:
                print(f"Mensagem enviada com sucesso para {to_number}")
                return True
            else:
                print(f"Erro ao enviar mensagem para {to_number}: {result}")
                return False
                
        except requests.RequestException as e:
            print(f"Erro na requisição para {to_number}: {e}")
            return False
    
    def send_template_message(self, to_number: str, template_name: str, 
                            language_code: str = 'pt_BR', 
                            parameters: List[str] = None) -> bool:
        """
        Envia uma mensagem usando template aprovado
        """
        if not self.access_token or not self.phone_number_id:
            raise ValueError("WhatsApp access token and phone number ID are required")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        clean_number = ''.join(filter(str.isdigit, to_number))
        if not clean_number.startswith('55'):
            clean_number = '55' + clean_number
            
        template_data = {
            "name": template_name,
            "language": {
                "code": language_code
            }
        }
        
        if parameters:
            template_data["components"] = [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": param} for param in parameters]
                }
            ]
        
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_number,
            "type": "template",
            "template": template_data
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            if 'messages' in result:
                print(f"Template enviado com sucesso para {to_number}")
                return True
            else:
                print(f"Erro ao enviar template para {to_number}: {result}")
                return False
                
        except requests.RequestException as e:
            print(f"Erro na requisição de template para {to_number}: {e}")
            return False

class EmailSender:
    def __init__(self, smtp_server: str = None, smtp_port: int = 587,
                 email: str = None, password: str = None):
        self.smtp_server = smtp_server or os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))
        self.email = email or os.getenv('EMAIL_ADDRESS')
        self.password = password or os.getenv('EMAIL_PASSWORD')
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        Envia um email
        """
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        if not self.email or not self.password:
            print("Credenciais de email não configuradas")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            
            text = msg.as_string()
            server.sendmail(self.email, to_email, text)
            server.quit()
            
            print(f"Email enviado com sucesso para {to_email}")
            return True
            
        except Exception as e:
            print(f"Erro ao enviar email para {to_email}: {e}")
            return False

class MessageDispatcher:
    def __init__(self, whatsapp_sender: WhatsAppSender = None, 
                 email_sender: EmailSender = None):
        self.whatsapp_sender = whatsapp_sender or WhatsAppSender()
        self.email_sender = email_sender or EmailSender()
    
    def send_news_digest(self, recipients: List[Dict], news_summaries: List[str]) -> Dict:
        """
        Envia resumo de notícias para todos os destinatários
        """
        if not news_summaries:
            print("Nenhuma notícia para enviar")
            return {'success': 0, 'failed': 0}
        
        # Combina todas as notícias em uma mensagem
        digest_message = "🗞️ *Resumo Diário de Notícias*\n\n"
        digest_message += "\n\n" + "="*50 + "\n\n".join(news_summaries)
        digest_message += f"\n\n📊 Total de notícias: {len(news_summaries)}"
        
        success_count = 0
        failed_count = 0
        
        for recipient in recipients:
            recipient_type = recipient.get('type')
            address = recipient.get('address')
            
            if recipient_type == 'whatsapp':
                if self.whatsapp_sender.send_message(address, digest_message):
                    success_count += 1
                else:
                    failed_count += 1
                    
            elif recipient_type == 'email':
                subject = f"Resumo Diário de Notícias - {len(news_summaries)} artigos"
                # Converte markdown para texto simples para email
                email_body = digest_message.replace('*', '').replace('_', '')
                
                if self.email_sender.send_email(address, subject, email_body):
                    success_count += 1
                else:
                    failed_count += 1
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total_news': len(news_summaries)
        }

