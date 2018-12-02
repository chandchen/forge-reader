from django.contrib import admin

from forgereader.core.models import (
    User, Label, Milestone, Issue, Project, Action, SyncInfo)


class UserAdmin(admin.ModelAdmin):
    model = User
    list_display = ('username', 'full_name', 'when')
    search_fields = ('username', 'full_name')


class ProjectAdmin(admin.ModelAdmin):
    model = Project
    list_display = ('name', 'namespace', 'when')
    search_fields = ('name', 'namespace')


class LabelAdmin(admin.ModelAdmin):
    model = Label
    list_display = ('name', 'when')
    search_fields = ('name', )


class MilestoneAdmin(admin.ModelAdmin):
    model = Milestone
    list_display = ('name', 'when')
    search_fields = ('name', )


class IssueAdmin(admin.ModelAdmin):
    model = Issue
    list_display = ('title', 'number', 'when')
    raw_id_fields = ('author', 'assignee', 'milestone')
    search_fields = ('title', )


class ActionAdmin(admin.ModelAdmin):
    model = Issue
    list_display = ('action', 'issue', 'created', 'when')
    raw_id_fields = ('issue', 'owner')
    search_fields = ('issue__title', 'action')


class SyncInfoAdmin(admin.ModelAdmin):
    model = SyncInfo
    list_display = ('owner', 'when')


admin.site.register(User, UserAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Label, LabelAdmin)
admin.site.register(Milestone, MilestoneAdmin)
admin.site.register(Issue, IssueAdmin)
admin.site.register(Action, ActionAdmin)
admin.site.register(SyncInfo, SyncInfoAdmin)
