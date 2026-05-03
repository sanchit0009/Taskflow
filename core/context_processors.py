from django.db.models import Q
from .models import Project


def user_projects(request):
    """Inject the user's projects into all templates for the sidebar."""
    if request.user.is_authenticated:
        projects = Project.objects.filter(
            Q(creator=request.user) | Q(members=request.user)
        ).distinct().order_by('name')[:8]
        return {'user_projects': projects}
    return {'user_projects': []}
