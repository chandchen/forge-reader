from django.db import models


class ForgeUser(models.Model):
    username = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=150, blank=True)
    when = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

    class Meta:
        ordering = ['pk']


class Label(models.Model):
    name = models.CharField(max_length=30, unique=True)
    when = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['pk']


class Milestone(models.Model):
    name = models.CharField(max_length=30, unique=True)
    when = models.DateTimeField(auto_now_add=True)

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
    serial_number = models.CharField(max_length=64)
    milestone = models.ForeignKey(
        Milestone, on_delete=models.CASCADE, related_name='issues')

    labels = models.ManyToManyField(Label, related_name='issues', blank=True)

    when = models.DateTimeField(auto_now_add=True)
