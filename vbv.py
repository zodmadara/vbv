from flask import Flask, request, jsonify
import logging
import requests

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def tokenize_credit_card(user, card_details):
    headers = {
        'authority': 'payments.braintree-api.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'authorization': 'Bearer YOUR_BRAINTREE_AUTH_TOKEN',  # Replace with actual token
        'braintree-version': '2018-05-10',
        'content-type': 'application/json',
        'origin': 'https://assets.braintreegateway.com',
        'referer': 'https://assets.braintreegateway.com/',
        'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': user,
    }

    json_data = {
        'clientSdkMetadata': {
            'source': 'client',
            'integration': 'dropin2',
            'sessionId': '7823fe02-9ed1-496e-9946-314466a1a6ec',
        },
        'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token creditCard { bin brandCode last4 cardholderName expirationMonth expirationYear binData { prepaid healthcare debit durbinRegulated commercial payroll issuingBank countryOfIssuance productId } } } }',
        'variables': {
            'input': {
                'creditCard': {
                    'number': card_details['number'],
                    'expirationMonth': card_details['expirationMonth'],
                    'expirationYear': card_details['expirationYear'],
                    'cvv': card_details['cvv'],
                    'cardholderName': 'User',  # Default name
                },
                'options': {
                    'validate': False,
                },
            },
        },
        'operationName': 'TokenizeCreditCard',
    }

    response = requests.post('https://payments.braintree-api.com/graphql', headers=headers, json=json_data)

    if response.status_code == 200:
        logging.info('Tokenization successful')
        response_json = response.json()
        token = response_json['data']['tokenizeCreditCard']['token']
        return token
    else:
        logging.error(f"Error during tokenization: {response.status_code}, {response.text}")
        return None


def process_payment(token, user):
    headers = {
        'authority': 'api.braintreegateway.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://www.autoone.com.au',
        'referer': 'https://www.autoone.com.au/',
        'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': user,
    }

    json_data = {
        'amount': '249',
        'additionalInfo': {
            'acsWindowSize': '03',
            'billingLine1': 'St Louis mo St Louis mo NEW MOONTA',
            'billingLine2': None,
            'billingCity': 'NEW MOONTA',
            'billingState': 'QLD',
            'billingPostalCode': '4671',
            'billingCountryCode': 'AU',
            'billingPhoneNumber': '8435491348',
            'billingGivenName': 'Sora',
            'billingSurname': 'Okwara',
            'email': 'zoror@hdkdiu.com',
        },
        'bin': '533621',
        'dfReferenceId': '0_4b74b5cf-ce7c-416e-b760-ef9ffa419d35',
        'clientMetadata': {
            'requestedThreeDSecureVersion': '2',
            'sdkVersion': 'web/3.74.0',
            'cardinalDeviceDataCollectionTimeElapsed': 1956,
            'issuerDeviceDataCollectionTimeElapsed': 22,
            'issuerDeviceDataCollectionResult': True,
        },
        'authorizationFingerprint': 'YOUR_AUTH_FINGERPRINT',  # Replace with actual fingerprint
        'braintreeLibraryVersion': 'braintree/web/3.74.0',
        '_meta': {
            'merchantAppId': 'www.autoone.com.au',
            'platform': 'web',
            'sdkVersion': '3.74.0',
            'source': 'client',
            'integration': 'custom',
            'integrationType': 'custom',
            'sessionId': '7823fe02-9ed1-496e-9946-314466a1a6ec',
        },
    }

    url = f'https://api.braintreegateway.com/merchants/dwk5spdgw7qscdkp/client_api/v1/payment_methods/{token}/three_d_secure/lookup'
    response = requests.post(url, headers=headers, json=json_data)

    if response.status_code == 200:
        logging.info('Payment processing successful')
        response_json = response.json()
        status = response_json.get('status')

        if status == 'authenticate_attempt_successful':
            return 'non-vbv'
        elif status in ['authenticate_rejected', 'lookup_error']:
            return 'vbv'
        else:
            logging.warning(f"Unknown status: {status}")
            return 'unknown'

    else:
        logging.error(f"Error during payment processing: {response.status_code}, {response.text}")
        return 'error'


@app.route('/card=<card_info>', methods=['GET'])
def handle_card(card_info):
    # Split card details from the URL format "number|expirationMonth|expirationYear|cvv"
    try:
        card_number, expiration_month, expiration_year, cvv = card_info.split('|')
    except ValueError:
        return jsonify({'error': 'Invalid card format. Expected format: card_number|expiration_month|expiration_year|cvv'}), 400

    # User agent
    user_agent = request.headers.get('User-Agent')

    card_details = {
        'number': card_number,
        'expirationMonth': expiration_month,
        'expirationYear': expiration_year,
        'cvv': cvv,
    }

    # Step 1: Tokenize the credit card
    token = tokenize_credit_card(user_agent, card_details)

    if token:
        # Step 2: Process the payment
        vbv_status = process_payment(token, user_agent)
        return jsonify({'status': vbv_status})
    else:
        return jsonify({'error': 'Failed to tokenize the credit card'}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)