from rest_framework import permissions
from vendors.models import Vendor

class IsAdminOrProductVendor(permissions.BasePermission):
    """
    Allows access only to admin users or the vendor that owns the product.
    Assumes the view handles a single Product or VendorSizeChartTemplate object.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow admin access
        if request.user and request.user.is_staff:
            return True
            
        # Check if obj is a Product
        if hasattr(obj, 'vendor_id'):
            vendor_id = obj.vendor_id
        # Check if obj is a VendorSizeChartTemplate (which has vendor foreign key)
        elif hasattr(obj, 'vendor'):
            # In Django, obj.vendor might be the instance, so we can check obj.vendor.user
            vendor_id = obj.vendor_id if hasattr(obj, 'vendor_id') else (obj.vendor.id if obj.vendor else None)
        else:
            return False
            
        if not vendor_id:
            return False

        return Vendor.objects.filter(id=vendor_id, user=request.user, status='approved', is_active=True).exists()
