from django.shortcuts import render
from django.views.generic import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect

from django.conf import settings
from django.utils import timezone

from forgereader.core.models import Issue, User, Project
from forgereader.core.utils import update_remote_data


forge_url = settings.SITE_URL


class IssueListView(TemplateView):
    template_name = "core/issue_list.html"

    def get(self, request, *args, **kwargs):
        filters = {}
        show_statistics = False

        project_selected_id = int(request.GET.get('project', 0))
        if project_selected_id != 0:
            filters['project_id'] = project_selected_id
        assignee_selected_id = int(request.GET.get('assignee', 0))
        assignee_name = ''
        if assignee_selected_id != 0:
            filters['assignee_id'] = assignee_selected_id
            assignee_name = User.objects.get(
                pk=assignee_selected_id).full_name
            show_statistics = True
        time_selected = int(request.GET.get('time', 0))
        if time_selected != 0:
            selected_time = timezone.now() - timezone.timedelta(
                days=time_selected)
            filters['created__gt'] = selected_time

        issues = Issue.objects.filter(**filters).order_by('-number')
        issue_count = issues.count()
        total_time = 0
        avg_time_spent = 0

        reopen_count = 0
        if show_statistics:
            for issue in issues:
                total_time += issue.time_spent
                reopen_count += issue.reopen_times
        if issue_count and total_time:
            avg_time_spent = round(total_time / issue_count)

        project_options = Project.objects.filter(
            name__in=settings.REPO_NAME).order_by('name')
        user_options = User.objects.filter(
            username__in=settings.DEVELOPERS).order_by('username')

        paginator = Paginator(issues, 20)

        page = request.GET.get('page')
        try:
            issue_list = paginator.page(page)
        except PageNotAnInteger:
            issue_list = paginator.page(1)
        except EmptyPage:
            issue_list = paginator.page(paginator.num_pages)

        # fetch statistics info here
        infos = {
            'assignee_name': assignee_name,
            'issue_count': issue_count,
            'total_spent': total_time,
            'avg_spent': avg_time_spent,
            'reopen_count': reopen_count,
        }

        contents = {
            'forge_url': forge_url,
            'issues': issue_list,
            'project_selected_id': int(project_selected_id),
            'assignee_selected_id': int(assignee_selected_id),
            'time_selected': int(time_selected),
            'time_options': settings.TIME_OPTION,
            'users': user_options,
            'projects': project_options,
            'infos': infos,
            'show_statistics': show_statistics,
        }
        return render(request, self.template_name, contents)


class UserListView(TemplateView):
    template_name = "core/user_list.html"

    def get(self, request, *args, **kwargs):
        users = User.objects.filter(username__in=settings.DEVELOPERS)
        paginator = Paginator(users, 15)

        page = request.GET.get('page')
        try:
            user_list = paginator.page(page)
        except PageNotAnInteger:
            user_list = paginator.page(1)
        except EmptyPage:
            user_list = paginator.page(paginator.num_pages)
        return render(request, self.template_name, {
            'users': user_list,
            'forge_url': forge_url})


class ProjectListView(TemplateView):
    template_name = "core/project_list.html"

    def get(self, request, *args, **kwargs):
        msg = request.GET.get('msg', '')

        projects = Project.objects.filter(
            namespace=settings.REPO_NAMESPACE, name__in=settings.REPO_NAME)

        paginator = Paginator(projects, 15)

        page = request.GET.get('page')
        try:
            project_list = paginator.page(page)
        except PageNotAnInteger:
            project_list = paginator.page(1)
        except EmptyPage:
            project_list = paginator.page(paginator.num_pages)

        contents = {
            'msg': msg,
            'projects': project_list,
            'namespace': settings.REPO_NAMESPACE}
        return render(request, self.template_name, contents)


class SyncView(TemplateView):

    def get(self, request, *args, **kwargs):
        update_remote_data()
        return HttpResponseRedirect('/?msg=ok')
