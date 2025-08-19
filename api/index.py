import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_web_chatbot import app

# Vercel serverless function handler
handler = app