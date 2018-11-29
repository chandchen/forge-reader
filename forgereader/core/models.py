from django.db import models

from django.conf import settings


ISSUE_STATUS_CHOICES = (
    (0, 'open'),
    (1, 'closed'),
)


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
        action = self.actions.filter(
            action__icontains='added Doing').first()
        if action:
            return action.created
        else:
            return self.created

    @property
    def closed_datetime(self):
        action = self.actions.filter(
            action__icontains='closed').last()
        if action:
            return action.created
        else:
            return None

    @property
    def time_spent(self):
        time_spent = 0
        if self.closed_datetime:
            time_spent = (self.closed_datetime - self.started_datetime).days
        return int(time_spent)

    @property
    def time_spent_label(self):
        if self.status == self.CLOSED:
            return '{} days'.format(self.time_spent)
        return '-'

    @property
    def reopen_times(self):
        return self.actions.filter(action__icontains='reopened').count()

    @property
    def issue_link(self):
        return '{}/{}/issues/{}'.format(
            settings.SITE_URL, self.project.repo_name, self.number)


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
