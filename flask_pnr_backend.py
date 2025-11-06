from flask import Flask, render_template, request, jsonify
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from base64 import b64encode
import requests
from json import loads
import time

app = Flask(__name__)

def encrypt_pnr(pnr):
    """Encrypts the PNR number using AES CBC encryption with PKCS7 padding.

    Args:
        pnr (str): The PNR number to encrypt.

    Returns:
        str: The base64-encoded encrypted PNR.
    """
    data = bytes(pnr, 'utf-8')
    backend = default_backend()
    padder = padding.PKCS7(128).padder()

    data = padder.update(data) + padder.finalize()
    key = b'8080808080808080'
    iv = b'8080808080808080'
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()
    ct = encryptor.update(data) + encryptor.finalize()
    enc_pnr = b64encode(ct)
    return enc_pnr.decode('utf-8')

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/check-pnr', methods=['POST'])
def check_pnr():
    """API endpoint to check PNR status."""
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
        
        # Encrypt PNR
        encrypted_pnr = encrypt_pnr(pnr)
        
        # Prepare request data
        json_data = {
            'pnrNumber': encrypted_pnr,
        }
        
        # Make API request
        response = requests.post(
            'https://railways.easemytrip.com/Train/PnrchkStatus',
            json=json_data,
            verify=True,
            timeout=10
        )
        response.raise_for_status()
        
        result = loads(response.content)
        end_time = time.time()
        
        # Add processing time to result
        result['processingTime'] = round(end_time - start_time, 3)
        
        return jsonify(result), 200
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'API connection error: {str(e)}'}), 500
    except ValueError as e:
        return jsonify({'error': f'Invalid API response: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)