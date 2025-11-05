from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import time
import os
import logging

app = Flask(__name__)

# Configure CORS for production
CORS(app, resources={
    r"/check-pnr": {
        "origins": "*",  # Update with your frontend domain in production
        "methods": ["POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint for Render."""
    return jsonify({'status': 'healthy'}), 200

@app.route('/check-pnr', methods=['POST'])
def check_pnr():
    """API endpoint to check PNR status using Indian Railways NTES API."""
    try:
        data = request.get_json()
        pnr = data.get('pnr', '').strip()
        
        # Validate PNR
        if not pnr:
            return jsonify({'error': 'PNR number is required'}), 400
        
        if len(pnr) != 10:
            return jsonify({'error': 'PNR must be exactly 10 digits'}), 400
        
        if not pnr.isdigit():
            return jsonify({'error': 'PNR must contain only digits'}), 400
        
        start_time = time.time()
        
        # NTES API endpoint
        url = f'https://www.indianrail.gov.in/enquiry/PNR/GetPnrStatus/{pnr}'
        
        # Headers to mimic browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.indianrail.gov.in/enquiry/PNR/PnrEnquiry.html'
        }
        
        # Make API request
        response = requests.get(
            url,
            headers=headers,
            verify=True,
            timeout=15
        )
        response.raise_for_status()
        
        api_result = response.json()
        end_time = time.time()
        
        # Check if PNR is valid
        if api_result.get('error') or not api_result.get('trainNo'):
            error_msg = api_result.get('errorMessage', 'Invalid PNR or PNR not found')
            return jsonify({'error': error_msg}), 404
        
        # Transform NTES API response to match frontend expectations
        result = {
            'BrdPointName': api_result.get('boardingPoint', 'N/A'),
            'DestStnName': api_result.get('reservationUpTo', 'N/A'),
            'trainNumber': api_result.get('trainNo', 'N/A'),
            'trainName': api_result.get('trainName', 'N/A'),
            'dateOfJourney': api_result.get('dateOfJourney', 'N/A'),
            'className': api_result.get('journeyClass', 'N/A'),
            'quota': api_result.get('quota', 'N/A'),
            'passengerList': [],
            'processingTime': round(end_time - start_time, 3)
        }
        
        # Transform passenger data
        if api_result.get('passengerList'):
            for passenger in api_result['passengerList']:
                transformed_passenger = {
                    'passengerSerialNumber': passenger.get('passengerSerialNumber', 'N/A'),
                    'currentStatus': passenger.get('currentStatusDetails', passenger.get('currentStatus', 'N/A')),
                    'currentCoachId': passenger.get('currentCoachId', ''),
                    'currentBerthNo': passenger.get('currentBerthNo', passenger.get('currentBerthCode', '')),
                    'bookingStatus': passenger.get('bookingStatusDetails', passenger.get('bookingStatus', 'N/A'))
                }
                result['passengerList'].append(transformed_passenger)
        
        logger.info(f"PNR check successful for: {pnr[:3]}***")
        return jsonify(result), 200
        
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        return jsonify({'error': 'API request timed out. Please try again.'}), 504
    except requests.exceptions.RequestException as e:
        logger.error(f"API connection error: {str(e)}")
        return jsonify({'error': 'Unable to connect to Indian Railways server. Please try again.'}), 500
    except ValueError as e:
        logger.error(f"Invalid JSON response: {str(e)}")
        return jsonify({'error': 'Invalid response from server.'}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500

if __name__ == '__main__':
    # Get port from environment variable (Render provides this)
    port = int(os.environ.get('PORT', 5000))
    # Don't use debug=True in production
    app.run(host='0.0.0.0', port=port)
