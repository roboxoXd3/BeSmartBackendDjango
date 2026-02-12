from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import CurrencyRate, UserCurrencyPreference
from .serializers import (
    CurrencyRateSerializer, 
    UserCurrencyPreferenceSerializer, 
    CurrencyConversionSerializer
)
from drf_spectacular.utils import extend_schema
from decimal import Decimal

class CurrencyRateListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = CurrencyRate.objects.filter(is_active=True)
    serializer_class = CurrencyRateSerializer
    pagination_class = None

class UserCurrencyPreferenceView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserCurrencyPreferenceSerializer

    def get_object(self):
        obj, created = UserCurrencyPreference.objects.get_or_create(user=self.request.user)
        return obj

class CurrencyConversionView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=CurrencyConversionSerializer, responses=CurrencyConversionSerializer)
    def post(self, request):
        serializer = CurrencyConversionSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            from_currency = serializer.validated_data['from_currency']
            to_currency = serializer.validated_data['to_currency']

            # Basic conversion logic assuming Base Currency is NGN (Rate 1.0)
            # or data is stored relative to one base.
            # If from_currency != Base, convert to Base first.
            
            try:
                from_rate_obj = CurrencyRate.objects.get(currency_code=from_currency)
                from_rate = from_rate_obj.exchange_rate
            except CurrencyRate.DoesNotExist:
                # Fallback if base currency NGN isn't needed in DB or handled as 1.0 explicit logic
                if from_currency == 'NGN': 
                    from_rate = Decimal('1.0')
                else:
                    return Response({"error": f"Currency {from_currency} not found"}, status=400)

            try:
                to_rate_obj = CurrencyRate.objects.get(currency_code=to_currency)
                to_rate = to_rate_obj.exchange_rate
            except CurrencyRate.DoesNotExist:
                if to_currency == 'NGN':
                    to_rate = Decimal('1.0')
                else:
                    return Response({"error": f"Currency {to_currency} not found"}, status=400)
            
            # Formula: (Amount / FromRate) * ToRate
            # Example: 100 USD to EUR. 
            # USD Rate (vs NGN): 1500. EUR Rate (vs NGN): 1600.
            # Wait, usually rates are stored as: 1 USD = X NGN. 
            # So if Rate is "How much NGN is 1 Unit", then: 
            # AmountInNGN = Amount * FromRate
            # AmountInTarget = AmountInNGN / ToRate
            
            # Let's assume Rate = Value in Base Currency (NGN).
            # 1 USD = 1500 NGN. Rate = 1500.
            amount_in_base = amount * from_rate
            converted_amount = amount_in_base / to_rate

            return Response({
                "amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "converted_amount": round(converted_amount, 2),
                "rate": round(to_rate / from_rate, 6) # Effective rate
            })
        
        return Response(serializer.errors, status=400)

# Admin ViewSet for managing rates
class CurrencyRateViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated] # Should be IsSuperAdmin
    queryset = CurrencyRate.objects.all()
    serializer_class = CurrencyRateSerializer
