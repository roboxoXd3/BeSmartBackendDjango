from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.response import Response
from .models import CurrencyRate, UserCurrencyPreference
from .serializers import (
    CurrencyRateSerializer,
    UserCurrencyPreferenceSerializer,
    CurrencyConversionSerializer,
)
from drf_spectacular.utils import extend_schema
from decimal import Decimal
from collections import defaultdict
import threading
import urllib.request
import json
import logging
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

CURRENCY_META = {
    'NGN': {'symbol': '₦', 'name': 'Nigerian Naira'},
    'USD': {'symbol': '$', 'name': 'US Dollar'},
    'EUR': {'symbol': '€', 'name': 'Euro'},
    'GBP': {'symbol': '£', 'name': 'British Pound'},
    'INR': {'symbol': '₹', 'name': 'Indian Rupee'},
    'CAD': {'symbol': 'C$', 'name': 'Canadian Dollar'},
    'AUD': {'symbol': 'A$', 'name': 'Australian Dollar'},
    'JPY': {'symbol': '¥', 'name': 'Japanese Yen'},
}

# ── Background rate updater ──────────────────────────────────────────
_update_lock = threading.Lock()
_RATE_MAX_AGE = timedelta(hours=24)
_API_URL = 'https://open.er-api.com/v6/latest/NGN'


def fetch_and_update_rates():
    """Fetch latest rates from ExchangeRate-API (NGN base) and update every
    existing CurrencyRate row by deriving cross-rates mathematically.

    Called in a background thread — must not raise into the caller.
    """
    try:
        logger.info('Currency update: fetching rates from %s', _API_URL)
        req = urllib.request.Request(_API_URL, headers={'User-Agent': 'BeSmart/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        if data.get('result') != 'success':
            logger.warning('Currency update: API returned non-success: %s', data.get('result'))
            return

        ngn_rates = data['rates']  # e.g. {"NGN": 1, "USD": 0.000728, "EUR": 0.000646, ...}

        rows = list(CurrencyRate.objects.all())
        updated_count = 0

        for row in rows:
            from_c = row.from_currency
            to_c = row.to_currency

            # Skip identity rates
            if from_c == to_c:
                continue

            ngn_to_from = ngn_rates.get(from_c)
            ngn_to_to = ngn_rates.get(to_c)

            if ngn_to_from is None or ngn_to_to is None or ngn_to_from == 0:
                logger.debug('Currency update: skipping %s->%s (missing in API)', from_c, to_c)
                continue

            # Derive: from->to = (1 / NGN->from) * NGN->to  =  NGN->to / NGN->from
            new_rate = Decimal(str(ngn_to_to)) / Decimal(str(ngn_to_from))
            row.rate = new_rate.quantize(Decimal('0.000001'))
            row.source = 'exchangerate-api'
            updated_count += 1

        if updated_count:
            CurrencyRate.objects.bulk_update(rows, ['rate', 'source', 'updated_at'])
            logger.info('Currency update: updated %d rates', updated_count)
        else:
            logger.warning('Currency update: no rows were updated')

    except Exception:
        logger.exception('Currency update: failed')


def _trigger_update_if_needed():
    """If the newest rate is older than 24 h, kick off a background refresh.
    Non-blocking — returns immediately."""
    newest = CurrencyRate.objects.order_by('-updated_at').values_list('updated_at', flat=True).first()
    if newest is None:
        return

    if timezone.now() - newest < _RATE_MAX_AGE:
        return  # still fresh

    # Try to acquire the lock without blocking; skip if another thread is already updating
    if _update_lock.acquire(blocking=False):
        try:
            t = threading.Thread(target=_do_update_with_lock, daemon=True)
            t.start()
        except Exception:
            _update_lock.release()
            raise


def _do_update_with_lock():
    """Wrapper that releases the lock after fetch_and_update_rates finishes."""
    try:
        fetch_and_update_rates()
    finally:
        _update_lock.release()



class CurrencyRateListView(views.APIView):
    """GET /api/currency/rates/
    Returns supported currencies + nested exchange rate map for the Flutter app."""
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: {'type': 'object'}})
    def get(self, request):
        _trigger_update_if_needed()
        rows = CurrencyRate.objects.all()

        codes = set()
        exchange_rates = defaultdict(dict)
        last_updated = None

        for row in rows:
            codes.add(row.from_currency)
            codes.add(row.to_currency)
            exchange_rates[row.from_currency][row.to_currency] = {
                'rate': float(row.rate),
            }
            if last_updated is None or row.updated_at > last_updated:
                last_updated = row.updated_at

        supported = []
        priority = ['NGN', 'USD', 'EUR', 'GBP', 'INR', 'CAD', 'AUD', 'JPY']
        ordered = [c for c in priority if c in codes] + sorted(codes - set(priority))
        for code in ordered:
            meta = CURRENCY_META.get(code, {'symbol': code, 'name': code})
            supported.append({
                'code': code,
                'symbol': meta['symbol'],
                'name': meta['name'],
            })

        return Response({
            'success': True,
            'data': {
                'supportedCurrencies': supported,
                'exchangeRates': dict(exchange_rates),
                'lastUpdated': last_updated.isoformat() if last_updated else None,
                'defaultCurrency': 'USD' # Or whatever the default is, next.js expects this
            }
        })


class UserCurrencyPreferenceView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserCurrencyPreferenceSerializer

    def get_object(self):
        obj, _ = UserCurrencyPreference.objects.get_or_create(user=self.request.user)
        return obj


class CurrencyConversionView(views.APIView):
    """POST /api/currency/convert/"""
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=CurrencyConversionSerializer, responses={200: {'type': 'object'}})
    def post(self, request):
        _trigger_update_if_needed()
        serializer = CurrencyConversionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        amount = serializer.validated_data['amount']
        from_cur = serializer.validated_data['from_currency'].upper()
        to_cur = serializer.validated_data['to_currency'].upper()

        if from_cur == to_cur:
            return Response({
                'amount': float(amount),
                'from_currency': from_cur,
                'to_currency': to_cur,
                'converted_amount': float(amount),
                'rate': 1.0,
            })

        rate = _get_rate(from_cur, to_cur)
        if rate is None:
            return Response({'error': f'No rate found for {from_cur} → {to_cur}'}, status=400)

        converted = float(amount) * rate
        return Response({
            'amount': float(amount),
            'from_currency': from_cur,
            'to_currency': to_cur,
            'converted_amount': round(converted, 2),
            'rate': round(rate, 6),
        })


class CurrencyExchangeRateView(views.APIView):
    """GET /api/currency/rate/?from=USD&to=NGN"""
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: {'type': 'object'}})
    def get(self, request):
        _trigger_update_if_needed()
        from_cur = request.query_params.get('from', '').upper()
        to_cur = request.query_params.get('to', '').upper()

        if not from_cur or not to_cur:
            return Response({'error': "Both 'from' and 'to' query params required."}, status=400)

        if from_cur == to_cur:
            return Response({'from_currency': from_cur, 'to_currency': to_cur, 'rate': 1.0})

        rate = _get_rate(from_cur, to_cur)
        if rate is None:
            return Response({'error': f'No rate found for {from_cur} → {to_cur}'}, status=400)

        return Response({
            'from_currency': from_cur,
            'to_currency': to_cur,
            'rate': round(rate, 6),
        })


class CurrencyRateViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = CurrencyRate.objects.all()
    serializer_class = CurrencyRateSerializer


def _get_rate(from_cur: str, to_cur: str):
    """Look up direct rate, or cross via USD."""
    try:
        row = CurrencyRate.objects.get(from_currency=from_cur, to_currency=to_cur)
        return float(row.rate)
    except CurrencyRate.DoesNotExist:
        pass

    # Cross via USD
    try:
        from_usd = CurrencyRate.objects.get(from_currency=from_cur, to_currency='USD')
        usd_to = CurrencyRate.objects.get(from_currency='USD', to_currency=to_cur)
        return float(from_usd.rate) * float(usd_to.rate)
    except CurrencyRate.DoesNotExist:
        pass

    return None
