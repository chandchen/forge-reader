from django.shortcuts import render
from django.views.generic import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.conf import settings

from forgereader.core.models import Issue, ForgeUser


forge_url = settings.FORGE_URL


class IssueListView(TemplateView):
    template_name = "core/issue_list.html"

    def get(self, request, *args, **kwargs):
        # form = self.form_class(initial=self.initial)
        user = ForgeUser.objects.filter(username='chand.chen').first()
        issues = Issue.objects.filter(assignee=user)
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
