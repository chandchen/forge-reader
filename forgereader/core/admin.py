from django.contrib import admin

from forgereader.core.models import (
    ForgeUser, Label, Milestone, Issue, Project, Action)


class ForgeUserAdmin(admin.ModelAdmin):
    model = ForgeUser
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


class ActionAdmin(admin.ModelAdmin):
    model = Issue
    list_display = ('action', 'created', 'when')
    raw_id_fields = ('issue', 'owner')


admin.site.register(ForgeUser, ForgeUserAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Label, LabelAdmin)
admin.site.register(Milestone, MilestoneAdmin)
admin.site.register(Issue, IssueAdmin)
admin.site.register(Action, ActionAdmin)
