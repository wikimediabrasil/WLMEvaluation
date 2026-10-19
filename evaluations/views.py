from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.translation import gettext as _
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_GET

from .models import Juror, Pair, normalize_username, Campaign

from .forms import CampaignForm
from .services import create_campaign
from .ranking import bradley_terry
from .agreement import juror_agreement, split_half


@user_passes_test(lambda u: u.is_staff)
def campaign_create(request):
    form = CampaignForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        campaign = create_campaign(**form.cleaned_data)
        messages.success(request, _("Campaign “%(name)s” created.") % {"name": campaign.name})
        return redirect("evaluations:home")
    return render(request, "evaluations/campaign_form.html", {"form": form})


@require_GET
def home(request):
    rows = []
    if request.user.is_authenticated:
        me = normalize_username(request.user.username)
        my_jurors = {
            j.campaign_id: j
            for j in Juror.objects.filter(username=me).annotate(
                total=Count("pairs"), done=Count("pairs", filter=~Q(pairs__choice=""))
            )
        }
        campaigns = Campaign.objects.all() if request.user.is_staff else Campaign.objects.filter(id__in=my_jurors)
        for campaign in campaigns.order_by("-id"):
            juror = my_jurors.get(campaign.id)
            finished = juror is not None and juror.done == juror.total
            rows.append({
                "campaign": campaign,
                "juror": juror,
                "can_vote": juror is not None and not finished and campaign.is_open,
                "can_see_dashboard": request.user.is_staff or finished,
            })
    return render(request, "home.html", {"rows": rows})


def get_juror(request, campaign_id):
    return get_object_or_404(Juror, campaign_id=campaign_id,
                             username=normalize_username(request.user.username))


@require_GET
@login_required
def vote(request, campaign_id):
    juror = get_juror(request, campaign_id)
    pair = juror.pairs.filter(choice="").first()
    if pair is None:
        messages.success(request, _("You have voted on every pair."))
        return redirect("evaluations:home")
    return redirect("evaluations:pair", campaign_id, pair.position)


@login_required
def pair(request, campaign_id, position):
    juror = get_juror(request, campaign_id)
    pair = get_object_or_404(juror.pairs.select_related("left", "right"), position=position)
    can_vote = juror.campaign.is_open and not juror.votes_locked

    if request.method == "POST":
        if not can_vote:
            raise PermissionDenied
        choice = request.POST.get("choice")
        if choice not in dict(Pair.CHOICES):
            return HttpResponseBadRequest()
        pair.record_vote(choice)
        return redirect("evaluations:vote", campaign_id)

    return render(request, "evaluations/pair.html", {
        "campaign": juror.campaign,
        "juror": juror,
        "pair": pair,
        "can_vote": can_vote,
        "total": juror.pairs.count(),
        "done": juror.pairs.exclude(choice="").count(),
    })


def _access(request, campaign):
    """Returns (juror, full_view, own_view) for the current user."""
    juror = None
    if request.user.is_authenticated:
        juror = campaign.jurors.filter(username=normalize_username(request.user.username)).first()
    finished = juror is not None and not juror.pairs.filter(choice="").exists()
    released = campaign.results_published and not campaign.is_open
    full_view = request.user.is_staff or (juror is not None and released)
    own_view = not full_view and finished
    return juror, full_view, own_view


def _lock_votes(juror):
    """Opening the dashboard locks the juror's votes (first time only)."""
    if juror.dashboard_seen_at is None:
        juror.dashboard_seen_at = timezone.now()
        juror.save(update_fields=["dashboard_seen_at"])


def _scope(request, campaign, juror, own_view):
    """Which juror's votes to show, and which jurors appear in the progress list."""
    if own_view:
        return juror.username, campaign.jurors.filter(pk=juror.pk)
    return request.GET.get("juror"), campaign.jurors.all()


def _ranking(campaign, pairs):
    images = {img.id: img for img in campaign.images.all()}
    rows = bradley_terry(pairs.values_list("left_id", "right_id", "choice"), list(images))
    for r in rows:
        r["img"] = images[r["item"]]
    return rows


@require_GET
def results(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    juror, full_view, own_view = _access(request, campaign)
    if not (full_view or own_view):
        raise PermissionDenied

    is_staff = request.user.is_staff
    if juror and not is_staff:
        _lock_votes(juror)

    selected, jurors = _scope(request, campaign, juror, own_view)
    pairs = Pair.objects.filter(juror__campaign=campaign).exclude(choice="")
    if selected:
        pairs = pairs.filter(juror__username=selected)
    rows = _ranking(campaign, pairs)

    partial = bool(request.GET.get("partial"))
    context = {
        "campaign": campaign,
        "rows": rows,
        "top": rows[:10],
        "selected": selected,
        "n_votes": pairs.count(),
        "is_staff": is_staff,
        "full_view": full_view,
        "jurors": jurors.annotate(
            total=Count("pairs"),
            done=Count("pairs", filter=~Q(pairs__choice="")),
        ),
    }
    if full_view and not partial:
        context["agreement"] = juror_agreement(campaign)
        context["split_half"] = split_half(campaign) if len(context["agreement"]) >= 2 else None

    template = "evaluations/_ranking.html" if partial else "evaluations/results.html"
    return render(request, template, context)