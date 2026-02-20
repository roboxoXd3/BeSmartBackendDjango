from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum
from .models import (
    LoyaltyPoints, LoyaltyTransaction, LoyaltyReward, 
    LoyaltyVoucher, LoyaltyBadge, UserBadge
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

class LoyaltyPointsView(views.APIView):
    """GET /api/loyalty/points/ — balance + inline tier info so the client
    doesn't need a second request to /tier-info/."""
    permission_classes = [permissions.IsAuthenticated]

    TIERS = [('bronze', 0), ('silver', 500), ('gold', 2000), ('platinum', 5000)]
    TIER_MULTIPLIERS = {'bronze': 1.0, 'silver': 1.25, 'gold': 1.5, 'platinum': 2.0}

    @extend_schema(responses={200: LoyaltyPointsSerializer})
    def get(self, request):
        lp, _ = LoyaltyPoints.objects.get_or_create(user=request.user)
        data = LoyaltyPointsSerializer(lp).data

        tier = lp.tier or 'bronze'
        lifetime = lp.lifetime_points or 0
        idx = next((i for i, (t, _) in enumerate(self.TIERS) if t == tier), 0)
        next_tier = self.TIERS[idx + 1] if idx + 1 < len(self.TIERS) else None
        pts_to_next = max(0, (next_tier[1] - lifetime)) if next_tier else 0
        tier_range = (next_tier[1] - self.TIERS[idx][1]) if next_tier and next_tier[1] > self.TIERS[idx][1] else 1
        tier_progress = min(100.0, (lifetime - self.TIERS[idx][1]) / tier_range * 100) if next_tier else 100.0

        data['tier_multiplier'] = self.TIER_MULTIPLIERS.get(tier, 1.0)
        data['tier_progress'] = round(tier_progress, 1)
        data['next_tier'] = next_tier[0] if next_tier else None
        data['points_to_next_tier'] = pts_to_next

        return Response(data)

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


class ValidateVoucherView(views.APIView):
    """POST /api/loyalty/validate-voucher/"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request={'type': 'object', 'properties': {'voucher_code': {'type': 'string'}, 'order_subtotal': {'type': 'number'}, 'voucherCode': {'type': 'string'}, 'orderAmount': {'type': 'number'}}}, responses={200: {'type': 'object'}})
    def post(self, request):
        code = (request.data.get('voucher_code') or request.data.get('voucherCode') or '').strip().upper()
        subtotal = float(request.data.get('order_subtotal') or request.data.get('orderAmount') or 0)
        if not code:
            return Response({"valid": False, "error": "Voucher code required"})
        v = LoyaltyVoucher.objects.filter(user=request.user, voucher_code=code, status='active', expires_at__gt=timezone.now()).first()
        if not v:
            return Response({"valid": False, "error": "Invalid or expired voucher"})
        min_amt = float(v.minimum_order_amount or 0)
        if subtotal < min_amt:
            return Response({"valid": False, "error": f"Minimum order amount is {min_amt}"})
        discount = float(v.discount_value)
        if v.discount_type == 'discount_percentage':
            discount = subtotal * (discount / 100)
        return Response({
            "valid": True, "voucher_id": str(v.id), "voucher_code": v.voucher_code,
            "discount_type": v.discount_type, "discount_amount": discount,
            "discount_value": float(v.discount_value), "apply_to_shipping": False,
            "minimum_order_amount": min_amt
        })


class UserBadgesView(views.APIView):
    """GET /api/loyalty/user-badges/ — all badges with user earned status"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: {'type': 'array'}})
    def get(self, request):
        from django.db.models import Q
        earned_ids = set()
        earned_at = {}
        try:
            for ub in UserBadge.objects.filter(user=request.user).values('badge_id', 'earned_at'):
                bid = str(ub['badge_id'])
                earned_ids.add(bid)
                earned_at[bid] = ub['earned_at']
        except Exception:
            pass
        from orders.models import Order
        order_count = Order.objects.filter(user=request.user, status='delivered').count()
        total_spent = Order.objects.filter(user=request.user, status='delivered').aggregate(s=Sum('total'))['s'] or 0
        badges = []
        for b in LoyaltyBadge.objects.filter(is_active=True).order_by('display_order', 'name'):
            eid = str(b.id)
            is_earned = eid in earned_ids or (b.badge_type == 'order_count' and b.requirement_value and order_count >= b.requirement_value) or (b.badge_type == 'spending_amount' and b.requirement_value and float(total_spent) >= float(b.requirement_value))
            badges.append({
                "id": str(b.id), "name": b.name, "description": b.description, "icon_url": b.icon_url,
                "badge_type": b.badge_type, "requirement_value": b.requirement_value or 0,
                "bonus_points": b.bonus_points, "display_order": b.display_order,
                "is_active": b.is_active, "is_earned": is_earned,
                "earned_at": earned_at.get(eid), "progress": 100.0 if is_earned else min(100, (order_count / (b.requirement_value or 1)) * 100) if b.badge_type == 'order_count' else min(100, (float(total_spent) / (float(b.requirement_value or 1))) * 100) if b.badge_type == 'spending_amount' else 0,
                "current_value": order_count if b.badge_type == 'order_count' else float(total_spent)
            })
        return Response(badges)


class BadgeProgressView(views.APIView):
    """GET /api/loyalty/badge-progress/"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: {'type': 'object'}})
    def get(self, request):
        from orders.models import Order
        order_count = Order.objects.filter(user=request.user, status='delivered').count()
        total_spent = Order.objects.filter(user=request.user, status='delivered').aggregate(s=Sum('total'))['s'] or 0
        badges = []
        for b in LoyaltyBadge.objects.filter(is_active=True).order_by('display_order'):
            req = b.requirement_value or 0
            cur = order_count if b.badge_type == 'order_count' else float(total_spent)
            prog = min(100, (cur / req) * 100) if req else 100
            badges.append({"badge_id": str(b.id), "badge_name": b.name, "progress": round(prog, 1), "current_value": cur, "requirement_value": req, "is_earned": cur >= req})
        return Response({"badges": badges})


class TierInfoView(views.APIView):
    """GET /api/loyalty/tier-info/ — bronze 0, silver 500, gold 2000, platinum 5000"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: {'type': 'object'}})
    def get(self, request):
        lp, _ = LoyaltyPoints.objects.get_or_create(user=request.user)
        tiers = LoyaltyPointsView.TIERS
        mult = LoyaltyPointsView.TIER_MULTIPLIERS
        tier = lp.tier or 'bronze'
        lifetime = lp.lifetime_points or 0
        idx = next((i for i, (t, _) in enumerate(tiers) if t == tier), 0)
        next_tier = tiers[idx + 1] if idx + 1 < len(tiers) else None
        pts_to_next = max(0, (next_tier[1] - lifetime)) if next_tier else 0
        tier_range = (next_tier[1] - tiers[idx][1]) if next_tier and next_tier[1] > tiers[idx][1] else 1
        next_prog = min(100.0, (lifetime - tiers[idx][1]) / tier_range * 100) if next_tier else 100
        return Response({
            "tier": tier, "tier_multiplier": mult.get(tier, 1.0),
            "tier_progress": round(next_prog, 1), "next_tier": next_tier[0] if next_tier else None,
            "points_to_next_tier": pts_to_next, "lifetime_points": lifetime,
            "points_balance": lp.points_balance or 0
        })
