#!/usr/bin/env python
"""
Simple runner script for the Flask app
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    try:
        from app import app, init_db
        print("=" * 60)
        print("Starting AIMT Flask Application")
        print("=" * 60)
        print(f"Debug Mode: {app.debug}")
        print(f"Running on: http://127.0.0.1:5000")
        print("Press CTRL+C to stop the server")
        print("=" * 60)
        
        # Initialize database
        init_db()
        
        # Run the app
        app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=True)
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
