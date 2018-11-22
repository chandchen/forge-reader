from django.contrib import admin

from forgereader.core.models import (
    ForgeUser, Label, Milestone, Issue)


class ForgeUserAdmin(admin.ModelAdmin):
    model = ForgeUser
    list_display = ('username', 'full_name', 'when')
    search_fields = ('username', 'full_name')


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
    list_display = ('title', 'serial_number', 'when')
    raw_id_fields = ('author', 'assignee', 'milestone')


admin.site.register(ForgeUser, ForgeUserAdmin)
admin.site.register(Label, LabelAdmin)
admin.site.register(Milestone, MilestoneAdmin)
admin.site.register(Issue, IssueAdmin)
