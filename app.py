"""
Flask-based Deep Research App with Shader Background
Simple fix for streaming completion
"""

from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from research_manager import ResearchManager
import asyncio
import json
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(override=True)

app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)
CORS(app)

@app.route('/')
def index():
    """Serve the main page"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Template rendering failed: {e}")
        return f"<h1>Application Error</h1><p>Template not found. Error: {str(e)}</p>", 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/research', methods=['POST'])
def research():
    """Handle research requests with streaming response"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({'error': 'Empty query provided'}), 400
        
        logger.info(f"Starting research for query: {query[:50]}...")
        
        def generate():
            """Generator function for streaming response"""
            loop = None
            try:
                # Create event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def async_research():
                    async for chunk in ResearchManager().run(query):
                        yield chunk
                
                # Run the async generator
                gen = async_research()
                while True:
                    try:
                        chunk = loop.run_until_complete(gen.__anext__())
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                    except StopAsyncIteration:
                        # Research completed successfully
                        break
                    except Exception as e:
                        logger.error(f"Error in research stream: {e}")
                        yield f"data: {json.dumps({'error': f'Research error: {str(e)}'})}\n\n"
                        break
                        
            except Exception as e:
                logger.error(f"Critical error in generate: {e}")
                yield f"data: {json.dumps({'error': f'Critical error: {str(e)}'})}\n\n"
            finally:
                # Clean shutdown of event loop
                if loop and not loop.is_closed():
                    try:
                        # Cancel any pending tasks
                        pending = asyncio.all_tasks(loop)
                        for task in pending:
                            task.cancel()
                        
                        # Give a moment for cleanup
                        if pending:
                            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        
                        loop.close()
                    except Exception as cleanup_error:
                        logger.warning(f"Loop cleanup warning: {cleanup_error}")
                        
            # Send completion signal - outside the try/finally to avoid loop issues
            yield f"data: {json.dumps({'complete': True})}\n\n"
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
        
    except Exception as e:
        logger.error(f"Error in research endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'environment': os.getenv('FLASK_ENV', 'production')
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.getenv('FLASK_RUN_PORT', 8000))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)