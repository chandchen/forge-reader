from django.shortcuts import render
from django.views.generic import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect

from django.conf import settings

from forgereader.core.models import Issue, User, Project
from forgereader.core.utils import update_remote_data


forge_url = settings.SITE_URL


class IssueListView(TemplateView):
    template_name = "core/issue_list.html"

    def get(self, request, *args, **kwargs):
        filters = {}
        show_statistics = False

        project_selected_id = request.GET.get('project', 0)
        if project_selected_id != 0:
            filters['project_id'] = project_selected_id
        assignee_selected_id = request.GET.get('assignee', 0)
        assignee_name = ''
        if assignee_selected_id != 0:
            filters['assignee_id'] = assignee_selected_id
            assignee_name = User.objects.get(
                pk=assignee_selected_id).full_name
            show_statistics = True
        time = request.GET.get('time', '')

        issues = Issue.objects.filter(**filters)
        issue_count = issues.count()

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
        }

        contents = {
            'forge_url': forge_url,
            'issues': issue_list,
            'project_selected_id': int(project_selected_id),
            'assignee_selected_id': int(assignee_selected_id),
            'time': time,
            'users': user_options,
            'projects': project_options,
            'infos': infos,
            'show_statistics': show_statistics,
        }
        return render(request, self.template_name, contents)


class UserListView(TemplateView):
    template_name = "core/user_list.html"

    def get(self, request, *args, **kwargs):
        users = User.objects.all()
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

        projects = Project.objects.filter(namespace=settings.REPO_NAMESPACE)

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
