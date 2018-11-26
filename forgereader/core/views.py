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
        project_name = request.GET.get('project')
        if project_name:
            project = Project.objects.filter(name=project_name).first()
            filters['project'] = project

        user = ForgeUser.objects.filter(username='chand.chen').first()
        filters['assignee'] = user
        print(filters)
        issues = Issue.objects.filter(**filters)
        paginator = Paginator(issues, 15)

        page = request.GET.get('page')
        try:
            issue_list = paginator.page(page)
        except PageNotAnInteger:
            issue_list = paginator.page(1)
        except EmptyPage:
            issue_list = paginator.page(paginator.num_pages)
        return render(request, self.template_name, {
            'issues': issue_list,
            'forge_url': forge_url})


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
