from django.shortcuts import render
from django.views.generic import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect

from django.conf import settings

from forgereader.core.models import Issue, ForgeUser, Project
from forgereader.core.utils import update_forge_data


forge_url = settings.FORGE_URL


class IssueListView(TemplateView):
    template_name = "core/issue_list.html"

    def get(self, request, *args, **kwargs):
        filters = {}
        project_pk = request.GET.get('project', '')
        assignee = request.GET.get('assignee', '')
        # time = request.GET.get('time', '')
        project_name = 'all'
        if project_pk:
            project = Project.objects.get(pk=project_pk)
            filters['project'] = project
            project_name = project.name

        assignee_selected = ''
        if assignee:
            assignee = ForgeUser.objects.filter(username=assignee).first()
            filters['assignee'] = assignee
            assignee_selected = assignee.username

        user_options = ForgeUser.objects.filter(
            pk__in=list(range(1, 10))).values_list('username', flat=True)
        # filters['assignee'] = user

        issues = Issue.objects.filter(**filters)
        paginator = Paginator(issues, 20)

        page = request.GET.get('page')
        try:
            issue_list = paginator.page(page)
        except PageNotAnInteger:
            issue_list = paginator.page(1)
        except EmptyPage:
            issue_list = paginator.page(paginator.num_pages)
        return render(request, self.template_name, {
            'issues': issue_list,
            'forge_url': forge_url,
            'project': project_name,
            'users': user_options,
            'assignee_selected': assignee_selected,
        })


class ForgeUserListView(TemplateView):
    template_name = "core/user_list.html"

    def get(self, request, *args, **kwargs):
        users = ForgeUser.objects.all()
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
        update_forge_data()
        return HttpResponseRedirect('/?msg=ok')
