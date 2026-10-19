from django.contrib import admin
from .models import Campaign, Image, Juror, Pair, Vote


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "is_open", "results_published", "blocks_per_juror", "seed")
    list_editable = ("is_open", "results_published")
    readonly_fields = ("blocks_per_juror", "seed")


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("pair", "choice", "created_at")
    list_filter = ("pair__juror__campaign", "pair__juror")

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Pair)
class PairAdmin(admin.ModelAdmin):
    readonly_fields = ("choice", "voted_at")

@admin.register(Juror)
class JurorAdmin(admin.ModelAdmin):
    list_display = ("username", "campaign", "dashboard_seen_at")
    list_filter = ("campaign",)