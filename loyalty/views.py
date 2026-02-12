from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import (
    LoyaltyPoints, LoyaltyTransaction, LoyaltyReward, 
    LoyaltyVoucher, LoyaltyBadge
)
from .serializers import (
    LoyaltyPointsSerializer, LoyaltyTransactionSerializer, 
    LoyaltyRewardSerializer, LoyaltyVoucherSerializer, 
    LoyaltyBadgeSerializer, RedeemRewardSerializer
)
from drf_spectacular.utils import extend_schema
import uuid
import random
import string

class LoyaltyPointsView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoyaltyPointsSerializer

    def get_object(self):
        obj, created = LoyaltyPoints.objects.get_or_create(user=self.request.user)
        return obj

class LoyaltyTransactionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoyaltyTransactionSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return LoyaltyTransaction.objects.none()
        return LoyaltyTransaction.objects.filter(user=self.request.user).order_by('-created_at')

class LoyaltyRewardListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny] # Rewards catalog is public
    serializer_class = LoyaltyRewardSerializer
    queryset = LoyaltyReward.objects.filter(is_active=True).order_by('display_order')

class LoyaltyVoucherListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoyaltyVoucherSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return LoyaltyVoucher.objects.none()
        return LoyaltyVoucher.objects.filter(user=self.request.user).order_by('-created_at')

class LoyaltyBadgeListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoyaltyBadgeSerializer
    queryset = LoyaltyBadge.objects.filter(is_active=True).order_by('display_order')

class RedeemRewardView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=RedeemRewardSerializer, responses={201: LoyaltyVoucherSerializer})
    def post(self, request):
        serializer = RedeemRewardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reward_id = serializer.validated_data['reward_id']
        reward = get_object_or_404(LoyaltyReward, id=reward_id, is_active=True)
        
        # Check points
        user_points, _ = LoyaltyPoints.objects.get_or_create(user=request.user)
        if user_points.points_balance < reward.points_required:
            return Response(
                {"error": "Insufficient points"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process redemption
        # 1. Deduct points
        user_points.points_balance -= reward.points_required
        user_points.save()

        # 2. Log transaction
        LoyaltyTransaction.objects.create(
            user=request.user,
            points_change=-reward.points_required,
            transaction_type='redeem',
            description=f"Redeemed reward: {reward.name}",
            points_balance_after=user_points.points_balance
        )

        # 3. Create Voucher
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        voucher = LoyaltyVoucher.objects.create(
            user=request.user,
            reward=reward,
            voucher_code=code,
            points_spent=reward.points_required,
            discount_type=reward.reward_type,
            discount_value=reward.discount_amount if reward.discount_amount else reward.discount_percentage,
            minimum_order_amount=reward.minimum_order_amount,
            expires_at=timezone.now() + timezone.timedelta(days=reward.validity_days)
        )

        return Response(LoyaltyVoucherSerializer(voucher).data, status=status.HTTP_201_CREATED)
