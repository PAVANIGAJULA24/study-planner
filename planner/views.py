from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Case, When, Value, IntegerField, Q
from .models import Task
import calendar
from datetime import datetime, date, timedelta

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next') or request.POST.get('next') or 'dashboard'
            return redirect(next_url)
        else:
            error = 'Invalid username or password.'

    context = {'error': error}
    return render(request, 'registration/login.html', context)


def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = request.POST.get('email', '').strip()
            user.save()
            login(request, user)
            messages.success(request, 'Account created successfully.')
            next_url = request.GET.get('next') or request.POST.get('next') or 'dashboard'
            return redirect(next_url)
    else:
        form = UserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def task_list(request):
    tasks = Task.objects.filter(user=request.user)

    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter == 'completed':
        tasks = tasks.filter(completed=True)
        page_title = 'Completed Tasks'
    elif status_filter == 'pending':
        tasks = tasks.filter(completed=False)
        page_title = 'Pending Tasks'
    else:
        page_title = 'All Tasks'

    # Filter by priority
    priority_filter = request.GET.get('priority')
    if priority_filter in [Task.PRIORITY_HIGH, Task.PRIORITY_MEDIUM, Task.PRIORITY_LOW]:
        tasks = tasks.filter(priority=priority_filter)

    # Search by title or subject
    search_query = request.GET.get('q', '').strip()
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) | Q(subject__icontains=search_query)
        )

    tasks = tasks.annotate(
        priority_order=Case(
            When(priority='High', then=Value(1)),
            When(priority='Medium', then=Value(2)),
            When(priority='Low', then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
    ).order_by('completed', 'priority_order', 'deadline')

    total_tasks = tasks.count()
    completed_tasks = tasks.filter(completed=True).count()
    pending_tasks = total_tasks - completed_tasks

    progress = 0
    if total_tasks > 0:
        progress = int((completed_tasks / total_tasks) * 100)

    context = {
        'tasks': tasks,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'progress': progress,
        'progress_style': f'width: {progress}%;',
        'page_title': page_title,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
    }

    return render(request, 'tasks.html', context)

@login_required
def add_task(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        subject = request.POST.get('subject')
        deadline = request.POST.get('deadline')
        priority = request.POST.get('priority', 'Medium')
        Task.objects.create(
            user=request.user,
            title=title,
            subject=subject,
            deadline=deadline,
            priority=priority,
        )
        return redirect('tasks')
    return render(request, 'add_task.html')

@login_required
def edit_task(request, id):
    task = Task.objects.get(id=id, user=request.user)
    if request.method == 'POST':
        task.title = request.POST.get('title')
        task.subject = request.POST.get('subject')
        task.deadline = request.POST.get('deadline')
        task.priority = request.POST.get('priority', task.priority)
        task.save()
        return redirect('tasks')
    context = {'task': task}
    return render(request, 'edit_task.html', context)

@login_required
def delete_task(request, id):
    task = Task.objects.get(id=id, user=request.user)
    task.delete()
    return redirect('tasks')

@login_required
def complete_task(request, id):
    task = Task.objects.get(id=id, user=request.user)
    task.completed = True
    task.save()
    return redirect('tasks')

@login_required
def profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    return render(request, 'profile.html')

@login_required
def dashboard(request):
    tasks = Task.objects.filter(user=request.user)

    total_tasks = tasks.count()
    completed_tasks = tasks.filter(completed=True).count()
    pending_tasks = total_tasks - completed_tasks

    progress = 0
    if total_tasks > 0:
        progress = int((completed_tasks / total_tasks) * 100)

    # Today's tasks (pending tasks due today)
    today = date.today()
    todays_tasks = tasks.filter(deadline=today, completed=False)

    # Deadline reminders / notifications
    upcoming_tasks = tasks.filter(
        completed=False,
        deadline__range=(today + timedelta(days=1), today + timedelta(days=3))
    ).order_by('deadline')
    overdue_tasks = tasks.filter(
        completed=False,
        deadline__lt=today
    ).order_by('deadline')

    # Chart data: Tasks by subject (pie chart)
    from django.db.models import Count
    subject_data = tasks.values('subject').annotate(count=Count('subject')).order_by('-count')
    subject_labels = [item['subject'] for item in subject_data]
    subject_counts = [item['count'] for item in subject_data]

    # Chart data: Weekly completion progress (last 7 days)
    weekly_labels = []
    weekly_completed = []
    weekly_pending = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_tasks = tasks.filter(deadline=day)
        completed = day_tasks.filter(completed=True).count()
        pending = day_tasks.filter(completed=False).count()

        weekly_labels.append(day.strftime('%a'))
        weekly_completed.append(completed)
        weekly_pending.append(pending)

    # Personal welcome data
    now = datetime.now()
    current_hour = now.hour
    current_day = now.strftime('%A')
    current_date = now.strftime('%B %d, %Y')

    # Time-based greeting
    if current_hour < 12:
        greeting = "Good morning"
    elif current_hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    # Motivational messages based on progress
    if progress == 100:
        motivation = "🎉 Excellent work! All tasks completed!"
    elif progress >= 75:
        motivation = "🚀 You're almost there! Keep pushing!"
    elif progress >= 50:
        motivation = "💪 Great progress! Stay focused!"
    elif progress >= 25:
        motivation = "📈 Good start! Keep building momentum!"
    else:
        motivation = "🌟 Every journey begins with a single step. Let's get started!"

    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'progress': progress,
        'todays_tasks': todays_tasks,
        'upcoming_tasks': upcoming_tasks,
        'overdue_tasks': overdue_tasks,
        'greeting': greeting,
        'current_day': current_day,
        'current_date': current_date,
        'motivation': motivation,
        # Chart data
        'subject_labels': subject_labels,
        'subject_counts': subject_counts,
        'weekly_labels': weekly_labels,
        'weekly_completed': weekly_completed,
        'weekly_pending': weekly_pending,
    }

    return render(request, 'dashboard.html', context)

@login_required
def monthly_planner(request):
    # Get current year and month, or from GET parameters
    year = int(request.GET.get('year', datetime.now().year))
    month = int(request.GET.get('month', datetime.now().month))

    # Get tasks for the user in the selected month
    tasks = Task.objects.filter(
        user=request.user,
        deadline__year=year,
        deadline__month=month
    ).order_by('deadline')

    # Create calendar
    cal = calendar.monthcalendar(year, month)

    # Prepare calendar data with tasks
    calendar_data = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': 0, 'tasks': []})
            else:
                day_tasks = tasks.filter(deadline__day=day)
                week_data.append({
                    'day': day,
                    'tasks': list(day_tasks),
                    'has_tasks': day_tasks.exists()
                })
        calendar_data.append(week_data)

    # Navigation
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    context = {
        'calendar_data': calendar_data,
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'today': date.today(),
    }

    return render(request, 'monthly_planner.html', context)