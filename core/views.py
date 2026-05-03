from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Project, ProjectMember, Task
from .serializers import (
    RegisterSerializer, UserSerializer,
    ProjectSerializer, ProjectMemberSerializer, TaskSerializer
)


# ─── Template Views (Frontend) ────────────────────────────────────────────────

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        if password != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/signup.html')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'auth/signup.html')

        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name
        )
        login(request, user)
        messages.success(request, f'Welcome, {user.username}!')
        return redirect('dashboard')

    return render(request, 'auth/signup.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    user = request.user
    # Projects the user belongs to or created
    user_projects = Project.objects.filter(
        Q(creator=user) | Q(members=user)
    ).distinct()

    # Tasks visible to this user
    user_tasks = Task.objects.filter(
        Q(project__creator=user) |
        Q(project__members=user) |
        Q(assigned_to=user)
    ).distinct()

    today = timezone.now().date()
    context = {
        'total_tasks': user_tasks.count(),
        'todo_tasks': user_tasks.filter(status='todo').count(),
        'in_progress_tasks': user_tasks.filter(status='in_progress').count(),
        'done_tasks': user_tasks.filter(status='done').count(),
        'overdue_tasks': user_tasks.filter(due_date__lt=today).exclude(status='done').count(),
        'recent_tasks': user_tasks.order_by('-updated_at')[:5],
        'projects': user_projects,
        'project_count': user_projects.count(),
    }
    return render(request, 'dashboard.html', context)


@login_required
def project_list_view(request):
    user = request.user
    projects = Project.objects.filter(
        Q(creator=user) | Q(members=user)
    ).distinct().order_by('-created_at')
    return render(request, 'projects/list.html', {'projects': projects})


@login_required
def project_create_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if not name:
            messages.error(request, 'Project name is required.')
            return render(request, 'projects/create.html')
        project = Project.objects.create(name=name, description=description, creator=request.user)
        # Creator is automatically an admin member
        ProjectMember.objects.create(project=project, user=request.user, role='admin')
        messages.success(request, f'Project "{project.name}" created!')
        return redirect('project_detail', pk=project.pk)
    return render(request, 'projects/create.html')


@login_required
def project_detail_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    user = request.user

    if not project.is_member(user):
        messages.error(request, 'You are not a member of this project.')
        return redirect('project_list')

    is_admin = project.is_admin(user)
    tasks = project.tasks.all().order_by('status', '-priority', 'due_date')
    members = project.projectmember_set.select_related('user').all()
    all_users = User.objects.exclude(id__in=project.members.values_list('id', flat=True)).exclude(id=project.creator.id)

    context = {
        'project': project,
        'tasks': tasks,
        'members': members,
        'is_admin': is_admin,
        'all_users': all_users,
        'todo_tasks': tasks.filter(status='todo'),
        'in_progress_tasks': tasks.filter(status='in_progress'),
        'done_tasks': tasks.filter(status='done'),
    }
    return render(request, 'projects/detail.html', context)


@login_required
def project_delete_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not project.is_admin(request.user):
        messages.error(request, 'Only admins can delete projects.')
        return redirect('project_detail', pk=pk)
    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Project deleted.')
        return redirect('project_list')
    return render(request, 'projects/confirm_delete.html', {'project': project})


@login_required
def add_member_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not project.is_admin(request.user):
        messages.error(request, 'Only admins can add members.')
        return redirect('project_detail', pk=pk)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        role = request.POST.get('role', 'member')
        try:
            user = User.objects.get(pk=user_id)
            ProjectMember.objects.get_or_create(project=project, user=user, defaults={'role': role})
            messages.success(request, f'{user.username} added to project.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    return redirect('project_detail', pk=pk)


@login_required
def remove_member_view(request, pk, user_id):
    project = get_object_or_404(Project, pk=pk)
    if not project.is_admin(request.user):
        messages.error(request, 'Only admins can remove members.')
        return redirect('project_detail', pk=pk)
    if request.user.id == user_id:
        messages.error(request, 'You cannot remove yourself.')
        return redirect('project_detail', pk=pk)
    ProjectMember.objects.filter(project=project, user_id=user_id).delete()
    messages.success(request, 'Member removed.')
    return redirect('project_detail', pk=pk)


@login_required
def task_create_view(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if not project.is_admin(request.user):
        messages.error(request, 'Only project admins can create tasks.')
        return redirect('project_detail', pk=project_pk)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        priority = request.POST.get('priority', 'medium')
        due_date = request.POST.get('due_date') or None
        assigned_to_id = request.POST.get('assigned_to') or None

        if not title:
            messages.error(request, 'Task title is required.')
            return render(request, 'tasks/create.html', {'project': project})

        assigned_to = None
        if assigned_to_id:
            try:
                assigned_to = User.objects.get(pk=assigned_to_id)
            except User.DoesNotExist:
                pass

        Task.objects.create(
            project=project,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            assigned_to=assigned_to,
            created_by=request.user,
        )
        messages.success(request, f'Task "{title}" created!')
        return redirect('project_detail', pk=project_pk)

    members = project.projectmember_set.select_related('user').all()
    return render(request, 'tasks/create.html', {'project': project, 'members': members})


@login_required
def task_detail_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    project = task.project
    user = request.user

    if not project.is_member(user):
        messages.error(request, 'Access denied.')
        return redirect('project_list')

    is_admin = project.is_admin(user)
    can_edit = is_admin or task.assigned_to == user

    if request.method == 'POST' and can_edit:
        new_status = request.POST.get('status')
        if new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status

        if is_admin:
            task.title = request.POST.get('title', task.title).strip()
            task.description = request.POST.get('description', task.description).strip()
            task.priority = request.POST.get('priority', task.priority)
            task.due_date = request.POST.get('due_date') or task.due_date
            assigned_id = request.POST.get('assigned_to')
            if assigned_id:
                try:
                    task.assigned_to = User.objects.get(pk=assigned_id)
                except User.DoesNotExist:
                    pass
            elif assigned_id == '':
                task.assigned_to = None

        task.save()
        messages.success(request, 'Task updated.')
        return redirect('task_detail', pk=pk)

    members = project.projectmember_set.select_related('user').all()
    context = {
        'task': task,
        'project': project,
        'is_admin': is_admin,
        'can_edit': can_edit,
        'members': members,
    }
    return render(request, 'tasks/detail.html', context)


@login_required
def task_delete_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    project = task.project
    if not project.is_admin(request.user):
        messages.error(request, 'Only admins can delete tasks.')
        return redirect('task_detail', pk=pk)
    if request.method == 'POST':
        project_pk = project.pk
        task.delete()
        messages.success(request, 'Task deleted.')
        return redirect('project_detail', pk=project_pk)
    return render(request, 'tasks/confirm_delete.html', {'task': task})


# ─── REST API Views ────────────────────────────────────────────────────────────

class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class ProjectListCreateAPI(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(
            Q(creator=user) | Q(members=user)
        ).distinct()

    def perform_create(self, serializer):
        project = serializer.save(creator=self.request.user)
        ProjectMember.objects.create(project=project, user=self.request.user, role='admin')


class ProjectDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(Q(creator=user) | Q(members=user)).distinct()

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        if not project.is_admin(request.user):
            return Response({'detail': 'Only admins can delete projects.'}, status=403)
        return super().destroy(request, *args, **kwargs)


class TaskListCreateAPI(generics.ListCreateAPIView):
    serializer_class = TaskSerializer

    def get_queryset(self):
        user = self.request.user
        project_id = self.kwargs.get('project_pk')
        project = get_object_or_404(Project, pk=project_id)

        if not project.is_member(user):
            return Task.objects.none()

        # Admins see all tasks; members see only assigned tasks
        if project.is_admin(user):
            return project.tasks.all()
        return project.tasks.filter(assigned_to=user)

    def perform_create(self, serializer):
        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        if not project.is_admin(self.request.user):
            raise permissions.PermissionDenied('Only admins can create tasks.')
        serializer.save(project=project, created_by=self.request.user)


class TaskDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(
            Q(project__creator=user) |
            Q(project__members=user)
        ).distinct()

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        user = request.user
        is_admin = task.project.is_admin(user)
        is_assignee = task.assigned_to == user

        if not is_admin and not is_assignee:
            return Response({'detail': 'Permission denied.'}, status=403)

        # Members can only update status
        if not is_admin:
            allowed = {'status': request.data.get('status', task.status)}
            request._full_data = allowed

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        task = self.get_object()
        if not task.project.is_admin(request.user):
            return Response({'detail': 'Only admins can delete tasks.'}, status=403)
        return super().destroy(request, *args, **kwargs)


@api_view(['GET'])
def dashboard_stats_api(request):
    user = request.user
    tasks = Task.objects.filter(
        Q(project__creator=user) | Q(project__members=user) | Q(assigned_to=user)
    ).distinct()

    today = timezone.now().date()
    return Response({
        'total_tasks': tasks.count(),
        'todo': tasks.filter(status='todo').count(),
        'in_progress': tasks.filter(status='in_progress').count(),
        'done': tasks.filter(status='done').count(),
        'overdue': tasks.filter(due_date__lt=today).exclude(status='done').count(),
    })


@api_view(['POST'])
def add_member_api(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not project.is_admin(request.user):
        return Response({'detail': 'Only admins can add members.'}, status=403)

    user_id = request.data.get('user_id')
    role = request.data.get('role', 'member')
    user = get_object_or_404(User, pk=user_id)
    member, created = ProjectMember.objects.get_or_create(
        project=project, user=user, defaults={'role': role}
    )
    return Response(ProjectMemberSerializer(member).data, status=201 if created else 200)


@api_view(['DELETE'])
def remove_member_api(request, pk, user_id):
    project = get_object_or_404(Project, pk=pk)
    if not project.is_admin(request.user):
        return Response({'detail': 'Only admins can remove members.'}, status=403)
    ProjectMember.objects.filter(project=project, user_id=user_id).delete()
    return Response(status=204)
