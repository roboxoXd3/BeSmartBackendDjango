import requests
import hashlib
import hmac
import json
from decimal import Decimal
from django.conf import settings
from typing import Dict, Optional


class SquadPaymentService:
    """Service class to interact with Squad API"""
    
    def __init__(self):
        self.secret_key = settings.SQUAD_CONFIG['SECRET_KEY']
        self.public_key = settings.SQUAD_CONFIG['PUBLIC_KEY']
        self.base_url = settings.SQUAD_CONFIG['BASE_URL']
        self.webhook_secret = settings.SQUAD_CONFIG['WEBHOOK_SECRET']
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for Squad API"""
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
    
    def initiate_payment(
        self,
        amount: Decimal,
        email: str,
        transaction_ref: str,
        currency: str = 'NGN',
        callback_url: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Initiate payment with Squad
        
        Args:
            amount: Payment amount in naira (will be converted to kobo)
            email: Customer email
            transaction_ref: Unique transaction reference
            currency: Currency code (default: NGN)
            callback_url: URL to redirect after payment
            metadata: Additional data to store
        
        Returns:
            Dict containing checkout_url and transaction details
        """
        url = f"{self.base_url}/transaction/initiate"
        
        # Convert amount to smallest currency unit (kobo)
        amount_in_kobo = int(amount * 100)
        
        payload = {
            'amount': amount_in_kobo,
            'email': email,
            'currency': currency,
            'initiate_type': 'inline',
            'transaction_ref': transaction_ref,
            'callback_url': callback_url or settings.PAYMENT_CONFIG['CALLBACK_URL'],
        }
        
        if metadata:
            payload['metadata'] = metadata
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Squad API Error: {str(e)}")
    
    def verify_transaction(self, transaction_ref: str) -> Dict:
        """
        Verify transaction status with Squad
        
        Args:
            transaction_ref: Transaction reference to verify
        
        Returns:
            Dict containing transaction details
        """
        url = f"{self.base_url}/transaction/verify/{transaction_ref}"
        
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Squad Verification Error: {str(e)}")
    
    def validate_webhook_signature(self, payload: Dict, signature: str) -> bool:
        """
        Validate webhook signature from Squad
        
        Args:
            payload: Webhook payload
            signature: Signature from x-squad-encrypted-body header
        
        Returns:
            Boolean indicating if signature is valid
        """
        payload_string = json.dumps(payload, separators=(',', ':'))
        
        computed_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload_string.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(computed_signature, signature)


class SquadTransferService:
    """Service class for Squad transfer/payout operations"""
    
    def __init__(self):
        self.secret_key = settings.SQUAD_CONFIG['SECRET_KEY']
        self.base_url = settings.SQUAD_CONFIG['BASE_URL']
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
    
    def lookup_account(self, bank_code: str, account_number: str) -> Dict:
        """
        Lookup and verify bank account details
        
        Args:
            bank_code: Bank's NIP code
            account_number: Account number to verify
        
        Returns:
            Dict containing account name and number
        """
        url = f"{self.base_url}/payout/account/lookup"
        
        payload = {
            'bank_code': bank_code,
            'account_number': account_number
        }
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 200 and data.get('success'):
                return {
                    'success': True,
                    'account_name': data['data']['account_name'],
                    'account_number': data['data']['account_number']
                }
            else:
                return {
                    'success': False,
                    'message': data.get('message', 'Account lookup failed')
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f"Lookup Error: {str(e)}"
            }
    
    def initiate_transfer(
        self,
        transaction_ref: str,
        amount: Decimal,
        bank_code: str,
        account_number: str,
        account_name: str,
        remark: str = 'Vendor payout',
        currency: str = 'NGN'
    ) -> Dict:
        """
        Initiate bank transfer to vendor
        
        Args:
            transaction_ref: Unique transaction reference (must include merchant ID)
            amount: Transfer amount in naira (will be converted to kobo)
            bank_code: Bank's NIP code
            account_number: Recipient account number
            account_name: Account name from lookup
            remark: Transfer description
            currency: Currency code
        
        Returns:
            Dict containing transfer status
        """
        url = f"{self.base_url}/payout/transfer"
        
        # Convert to kobo
        amount_in_kobo = str(int(amount * 100))
        
        payload = {
            'transaction_reference': transaction_ref,
            'amount': amount_in_kobo,
            'bank_code': bank_code,
            'account_number': account_number,
            'account_name': account_name,
            'currency_id': currency,
            'remark': remark
        }
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Transfer Error: {str(e)}")
    
    def query_transfer_status(self, transaction_ref: str) -> Dict:
        """
        Query the status of a transfer
        
        Args:
            transaction_ref: Transfer reference to query
        
        Returns:
            Dict containing transfer status
        """
        url = f"{self.base_url}/payout/requery"
        
        payload = {'transaction_reference': transaction_ref}
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Query Error: {str(e)}")
