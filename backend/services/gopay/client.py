from gopay import payments

def create_gopay_client():
    return payments({
        'goid': '1234567890',  # ← Nahraď svým testovacím GoID
        'clientId': 'your-client-id',
        'clientSecret': 'your-client-secret',
        'gatewayUrl': 'https://gw.sandbox.gopay.com/api',
        'scope': 'payment-create'
    })
