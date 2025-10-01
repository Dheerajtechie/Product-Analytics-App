import sys
import os

# Add the parent directory to sys.path to import the main app
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import main
import streamlit.web.cli as stcli

def handler(event, context):
    """Netlify function handler for Streamlit app"""
    
    # Run Streamlit app
    try:
        # Set up Streamlit configuration for serverless
        os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
        os.environ['STREAMLIT_SERVER_PORT'] = '8501'
        os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
        
        # Import and run the main app
        main()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            },
            'body': 'Streamlit app is running'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }

if __name__ == '__main__':
    # For local testing
    main()