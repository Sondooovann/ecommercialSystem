# core/permissions.py

from rest_framework import permissions


class IsCustomer(permissions.BasePermission):
    """
    Permission to only allow customers to access the view.
    """

    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.role == 'customer'
        )


class IsShopOwner(permissions.BasePermission):
    """
    Permission to only allow shop owners to access the view.
    """

    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.role == 'shop_owner'
        )


class IsAdmin(permissions.BasePermission):
    """
    Permission to only allow admin users to access the view.
    """

    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.role == 'admin'
        )


class IsActiveUser(permissions.BasePermission):
    """
    Permission to only allow active users to access the view.
    """
    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.status == 'active'
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to only allow owners of an object or admins to access the view.
    Requires the view/model to have an 'owner' attribute or a get_owner() method.
    """

    def has_object_permission(self, request, view, obj):
        # Admins always have permission
        if request.user.role == 'admin':
            return True

        # Check if object has an owner attribute or method
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'get_owner'):
            return obj.get_owner() == request.user

        return False