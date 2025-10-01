#!/usr/bin/env python3
"""Vercel serverless function for Streamlit app"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to import the main app
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Set environment variables for Streamlit
os.environ.setdefault('STREAMLIT_SERVER_HEADLESS', 'true')
os.environ.setdefault('STREAMLIT_SERVER_PORT', '8501')
os.environ.setdefault('STREAMLIT_SERVER_ENABLE_CORS', 'false')
os.environ.setdefault('STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION', 'false')

try:
    import streamlit as st
    from streamlit.web import cli as stcli
    import streamlit.web.bootstrap as bootstrap
    from streamlit.runtime import Runtime
    from streamlit.runtime.app_session import AppSession
    from streamlit.runtime.scriptrunner import ScriptRunner
    
    # Import the main app
    from app import main
    
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback response
    def app(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-type', 'text/plain')]
        start_response(status, headers)
        return [f'Import Error: {e}'.encode()]
else:
    def app(environ, start_response):
        """WSGI application entry point for Vercel"""
        try:
            # Create a simple HTTP response for Streamlit
            status = '200 OK'
            headers = [
                ('Content-type', 'text/html'),
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Content-Type')
            ]
            
            # Basic HTML response that redirects to Streamlit Cloud
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Product Analytics - Redirecting...</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', roboto, oxygen, ubuntu, cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                        text-align: center;
                    }}
                    .container {{
                        background: rgba(255, 255, 255, 0.1);
                        backdrop-filter: blur(10px);
                        padding: 3rem;
                        border-radius: 20px;
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                        max-width: 600px;
                    }}
                    h1 {{ margin-bottom: 1.5rem; font-size: 2.5rem; }}
                    p {{ margin-bottom: 2rem; font-size: 1.2rem; opacity: 0.9; }}
                    .btn {{
                        background: linear-gradient(45deg, #ff6b6b, #ee5a24);
                        color: white;
                        padding: 1rem 2rem;
                        border: none;
                        border-radius: 50px;
                        font-size: 1.1rem;
                        font-weight: 600;
                        text-decoration: none;
                        display: inline-block;
                        transition: transform 0.2s;
                        margin: 0.5rem;
                    }}
                    .btn:hover {{ transform: translateY(-2px); }}
                    .spinner {{
                        border: 3px solid rgba(255, 255, 255, 0.3);
                        border-top: 3px solid white;
                        border-radius: 50%;
                        width: 40px;
                        height: 40px;
                        animation: spin 1s linear infinite;
                        margin: 2rem auto;
                    }}
                    @keyframes spin {{
                        0% {{ transform: rotate(0deg); }}
                        100% {{ transform: rotate(360deg); }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📊 Product Analytics</h1>
                    <p>This app is optimized for Streamlit Cloud deployment.</p>
                    <div class="spinner"></div>
                    <p>Redirecting to the live application...</p>
                    <a href="https://product-analytics-dheerajtechie.streamlit.app" class="btn">🚀 Open App</a>
                    <a href="https://github.com/Dheerajtechie/Product-Analytics-App" class="btn">📖 View Code</a>
                </div>
                <script>
                    setTimeout(() => {{
                        window.location.href = 'https://product-analytics-dheerajtechie.streamlit.app';
                    }}, 3000);
                </script>
            </body>
            </html>
            """
            
            start_response(status, headers)
            return [html_content.encode('utf-8')]
            
        except Exception as e:
            status = '500 Internal Server Error'
            headers = [('Content-type', 'text/plain')]
            start_response(status, headers)
            return [f'Error: {str(e)}'.encode()]

# For Vercel, we need to export the WSGI app
application = app

if __name__ == '__main__':
    # For local testing
    from wsgiref.simple_server import make_server
    
    httpd = make_server('', 8000, app)
    print("Serving on port 8000...")
    httpd.serve_forever()