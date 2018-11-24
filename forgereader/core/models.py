from django.db import models


ISSUE_STATUS_CHOICES = (
    (0, 'open'),
    (1, 'closed'),
)


class ForgeUser(models.Model):
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


class Label(models.Model):
    name = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=256, null=True, blank=True)
    when = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='labels')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['pk']


class Milestone(models.Model):
    name = models.CharField(max_length=30, unique=True)
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
        ForgeUser, on_delete=models.CASCADE,
        related_name='created_issues')
    assignee = models.ForeignKey(
        ForgeUser, on_delete=models.CASCADE, null=True, blank=True,
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

    OPEN = 0
    CLOSED = 1

    def __str__(self):
        return '{} - {}'.format(self.title, self.author)

    class Meta:
        ordering = ['pk']
