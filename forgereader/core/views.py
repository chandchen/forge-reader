from django.shortcuts import render
from django.views.generic import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import FileResponse
from django.contrib.auth.mixins import LoginRequiredMixin

from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from forgereader.core.models import Issue, User, Project, SyncInfo
from forgereader.core.utils import (
    update_remote_data, generate_csv_file, update_issue_infos,
    update_issue_time_infos)


class IssueListView(TemplateView):
    template_name = "core/issue_list.html"

    def get(self, request, *args, **kwargs):
        filters = {
            'status': Issue.CLOSED
        }
        show_statistics = False
        show_assignee_statistics = False
        show_author_statistics = False

        project_selected_id = int(request.GET.get('project', 0))
        if project_selected_id != 0:
            filters['project_id'] = project_selected_id
        assignee_selected_id = int(request.GET.get('assignee', 0))
        assignee_name = ''
        as_p = ''
        if assignee_selected_id != 0:
            assignee = User.objects.get(pk=assignee_selected_id)
            as_p = Q(assignee=assignee) | Q(participants=assignee)
            assignee_name = assignee.full_name
            show_statistics = True
            show_assignee_statistics = True
        time_selected = int(request.GET.get('time', 0))
        if time_selected != 0:
            selected_time = timezone.now() - timezone.timedelta(
                days=time_selected)
            filters['closed__gt'] = selected_time
        author_selected = int(request.GET.get('author', 0))
        author_name = ''
        if author_selected != 0:
            filters['author_id'] = author_selected
            author_name = User.objects.get(
                pk=author_selected).full_name
            show_statistics = True
            show_author_statistics = True

        if as_p:
            issues = Issue.objects.filter(as_p, **filters).order_by('-number')
        else:
            issues = Issue.objects.filter(**filters).order_by('-number')
        issue_count = issues.count()

        total_time = 0
        avg_time_spent = 0
        bug_issue_count = 0
        enhancement_count = 0

        reopen_count = 0
        if show_statistics:
            for issue in issues:
                total_time += issue.time_spent
                reopen_count += issue.reopen_times
                label_string = ''.join(issue.labels_display).lower()
                if 'bug' in label_string:
                    bug_issue_count += 1
                if 'enhancement' in label_string:
                    enhancement_count += 1
        if issue_count and total_time:
            avg_time_spent = round(total_time / issue_count)

        if avg_time_spent != 0:
            avg_time_spent_label = '{} days'.format(avg_time_spent)
        else:
            avg_time_spent_label = '1 day'

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
            'avg_spent': avg_time_spent_label,
            'reopen_count': reopen_count,
        }

        author_infos = {
            'author_name': author_name,
            'bug_issue_count': bug_issue_count,
            'enhancement_count': enhancement_count,
            'others_count': issue_count - bug_issue_count - enhancement_count,
        }

        contents = {
            'issues': issue_list,
            'project_selected_id': int(project_selected_id),
            'assignee_selected_id': int(assignee_selected_id),
            'author_selected': int(author_selected),
            'time_selected': int(time_selected),
            'time_options': settings.TIME_OPTION,
            'users': user_options,
            'projects': project_options,
            'infos': infos,
            'show_statistics': show_statistics,
            'show_assignee_statistics': show_assignee_statistics,
            'show_author_statistics': show_author_statistics,
            'author_infos': author_infos,
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
            'users': user_list, })


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

        sync_info = SyncInfo.objects.last()
        last_updated = ''
        if sync_info:
            last_updated = sync_info.when

        contents = {
            'msg': msg,
            'projects': project_list,
            'namespace': settings.REPO_NAMESPACE,
            'last_updated': last_updated,
        }
        return render(request, self.template_name, contents)


class SyncView(LoginRequiredMixin, TemplateView):
    template_name = "core/syncing.html"

    def get(self, request, *args, **kwargs):
        msg = ''
        info = int(request.GET.get('info', 0))
        if info == 1:
            success = update_remote_data()
            if success:
                msg = 'success'

        records = int(request.GET.get('record', 0))
        if records > 0:
            success = update_issue_infos(records)
            if success:
                msg = 'success'

        if msg == 'success':
            update_issue_time_infos()
            SyncInfo.objects.create(owner=request.user)
        contents = {
            'msg': msg
        }
        return render(request, self.template_name, contents)


class Download(TemplateView):

    def get(self, request, *args, **kwargs):
        filters = {
            'status': Issue.CLOSED
        }
        project = ''
        assignee_name = ''
        author = ''

        project_selected = int(request.GET.get('project', 0))
        if project_selected != 0:
            filters['project_id'] = project_selected
            project = Project.objects.get(pk=project_selected).name

        assignee_selected = int(request.GET.get('assignee', 0))
        as_p = ''
        if assignee_selected != 0:
            assignee = User.objects.get(pk=assignee_selected)
            as_p = Q(assignee=assignee) | Q(participants=assignee)
            assignee_name = assignee.username

        time_selected = int(request.GET.get('time', 0))
        if time_selected != 0:
            selected_time = timezone.now() - timezone.timedelta(
                days=time_selected)
            filters['closed__gt'] = selected_time

        author_selected = int(request.GET.get('author', 0))
        if author_selected != 0:
            filters['author_id'] = author_selected
            author = User.objects.get(pk=author_selected).username

        if as_p:
            issues = Issue.objects.filter(as_p, **filters).order_by('-number')
        else:
            issues = Issue.objects.filter(**filters).order_by('-number')

        now = timezone.localtime(timezone.now()).strftime("%Y-%m-%d-%H%M")

        p_string = '{}-'.format(project) if project else ''
        a1_string = 'assignee@{}-'.format(
            assignee_name) if assignee_name else ''
        a2_string = 'author@{}-'.format(author) if author else ''

        file_name = '{}{}{}{}.csv'.format(p_string, a1_string, a2_string, now)

        generate_csv_file(issues, file_name)

        file = open('{}{}'.format(settings.DOWNLOAD_PATH, file_name), 'rb')
        response = FileResponse(file)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename="{}"'.format(
            file_name)
        return response
