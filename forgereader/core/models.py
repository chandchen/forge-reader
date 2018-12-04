from django.db import models

from django.conf import settings
from django.contrib.auth.models import User as D_User


ISSUE_STATUS_CHOICES = (
    (0, 'open'),
    (1, 'closed'),
)


def formated_datetime(original):
    if original:
        return original.strftime("%Y-%m-%d %H:%M")
    return '-'


class User(models.Model):
    username = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=150, blank=True)
    when = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

    class Meta:
        ordering = ['pk']


class Project(models.Model):
    name = models.CharField(max_length=30)
    namespace = models.CharField(max_length=30)
    when = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['pk']

    @property
    def repo_name(self):
        return '{}/{}'.format(self.namespace, self.name)

    @property
    def issue_count(self):
        return self.issues.count()


class Label(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=256, null=True, blank=True)
    when = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='labels')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['pk']


class Milestone(models.Model):
    name = models.CharField(max_length=30)
    milestone_range = models.CharField(max_length=128, null=True, blank=True)
    status = models.CharField(max_length=128, null=True, blank=True)
    when = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='milestones')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['pk']


class Issue(models.Model):
    title = models.CharField(max_length=256)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='created_issues')
    assignee = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True,
        related_name='assigned_issues')
    number = models.IntegerField(default=0)
    milestone = models.ForeignKey(
        Milestone, on_delete=models.CASCADE, related_name='issues',
        null=True, blank=True)

    labels = models.ManyToManyField(
        Label, related_name='issues', blank=True)

    status = models.IntegerField(
        choices=ISSUE_STATUS_CHOICES, default=0)
    when = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='issues')
    created = models.DateTimeField(null=True, blank=True)

    started = models.DateTimeField(null=True, blank=True)
    closed = models.DateTimeField(null=True, blank=True)

    participants = models.ManyToManyField(
        User, related_name='participated_issues', blank=True)

    OPEN = 0
    CLOSED = 1

    def __str__(self):
        return '{} - {}'.format(self.title, self.author)

    class Meta:
        ordering = ['pk']

    @property
    def status_display(self):
        return self.get_status_display().capitalize()

    @property
    def started_datetime(self):
        string = 'added {}'.format(settings.DOING_LABELS[self.project.name])
        action = self.actions.filter(
            action__icontains=string).order_by('created').first()
        if action:
            return action.created
        else:
            return None

    @property
    def started_string(self):
        return formated_datetime(self.started)

    @property
    def closed_datetime(self):
        action = self.actions.filter(
            action__icontains='closed').order_by('created').last()
        if action:
            return action.created
        else:
            return None

    @property
    def closed_string(self):
        return formated_datetime(self.closed)

    @property
    def time_spent(self):
        time_spent = 0
        if self.closed_datetime and self.started_datetime:
            time_spent = (self.closed_datetime - self.started_datetime).days
        return int(time_spent)

    @property
    def time_spent_label(self):
        if self.status == self.CLOSED:
            if self.time_spent <= 1:
                if self.started is None or self.closed is None:
                    return '-'
                return '1 day'
            return '{} days'.format(self.time_spent)
        return '-'

    @property
    def reopen_times(self):
        return self.actions.filter(action__icontains='reopened').count()

    @property
    def issue_link(self):
        return '{}/{}/issues/{}'.format(
            settings.SITE_URL, self.project.repo_name, self.number)

    @property
    def labels_display(self):
        label_list = []
        for label in self.labels.all():
            label_list.append(label.name)
        return label_list

    @property
    def labels_string(self):
        if self.labels_display:
            return ', '.join(self.labels_display)

        return '-'

    def participated(self, user):
        action = self.actions.filter(
            owner=user, action__icontains='added Doing').first()
        if action:
            return action.created
        return None

    @property
    def participation(self):
        participant_list = []
        for participant in self.participants.all():
            participated_time = self.participated(participant)
            participated_time_spent = '-'
            if participated_time and self.closed_datetime:
                time_spent = (
                    self.closed_datetime - participated_time).days
                if time_spent <= 1:
                    participated_time_spent = '1 day'
                else:
                    participated_time_spent = '{} days'.format(time_spent)
                participated_time = participated_time.strftime(
                    "%Y-%m-%d %H:%M")
            dic = {
                'name': participant.username,
                'time': participated_time,
                'time_spent': participated_time_spent,
            }
            participant_list.append(dic)
        return participant_list

    @property
    def participation_string(self):
        if self.participation:
            user_list = []
            for user in self.participation:
                user_list.append(user['name'])
            return ', '.join(user_list)
        return '-'

    @property
    def participation_string_with_time(self):
        if self.participation:
            contents = []
            for user in self.participation:
                u_string = '{}({})'.format(user['name'], user['time'])
                contents.append(u_string)
            return ', '.join(contents)
        return '-'


class Action(models.Model):
    issue = models.ForeignKey(
        Issue, on_delete=models.CASCADE,
        related_name='actions')
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='actions')
    created = models.DateTimeField(null=True, blank=True)
    action = models.CharField(max_length=512)
    when = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{} - {}'.format(self.action, self.owner)

    class Meta:
        ordering = ['pk']


class SyncInfo(models.Model):
    owner = models.ForeignKey(
        D_User, on_delete=models.CASCADE,
        related_name='sync_infos')
    when = models.DateTimeField(auto_now_add=True)
