from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.urls import reverse

class AdminUserMiddleware:
    """
    Middleware to prevent admin/staff users from accessing the website.
    Admin users must log in through /admin/ only.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Paths where admin users are allowed
        self.allowed_paths = ['/admin/', '/logout/', '/myadmin/', '/chatbot/']
    
    def __call__(self, request):
        # Always allow myadmin paths - don't check them
        if request.path.startswith('/myadmin/'):
            response = self.get_response(request)
            return response
        
        # Check if user is logged in and is admin/staff
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            # Check if current path is NOT in allowed paths
            if not any(request.path.startswith(path) for path in self.allowed_paths):
                # Log out the admin user from the website
                logout(request)
                # Don't show message here to avoid dialog issues
                return redirect('/')
        
        response = self.get_response(request)
        return response
