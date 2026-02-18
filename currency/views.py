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


class CurrencyRateListView(views.APIView):
    """GET /api/currency/rates/
    Returns supported currencies + nested exchange rate map for the Flutter app."""
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: {'type': 'object'}})
    def get(self, request):
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
            'supportedCurrencies': supported,
            'exchangeRates': dict(exchange_rates),
            'lastUpdated': last_updated.isoformat() if last_updated else None,
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
