from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from urllib.parse import quote


def normalize_username(name):
    name = name.strip().replace("_", " ")
    return name[:1].upper() + name[1:]


class Campaign(models.Model):
    """Identifiable name of the campaign, sufficient to disambiguate them"""
    name = models.CharField(_("Name"), max_length=255)
    is_open = models.BooleanField(_("Open for voting"), default=True)
    coordinators = models.TextField(_("Coordinators"), blank=True, help_text=_("One username per line, without 'User:'"))
    results_published = models.BooleanField(_("results published"), default=False)
    blocks_per_juror = models.PositiveSmallIntegerField(_("blocks per juror"), default=9)
    seed = models.IntegerField(_("random seed"), null=True, blank=True)

    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")

    def __str__(self):
        return self.name


class Image(models.Model):
    """File to be voted on"""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="images")
    filename = models.CharField(_("File name"), max_length=255)
    mid = models.CharField(_("MID"), max_length=32, blank=True)

    def _path(self):
        return quote(self.filename.replace(" ", "_"))

    @property
    def thumb(self):
        return f"https://commons.wikimedia.org/wiki/Special:FilePath/{self._path()}?width=1280"

    @property
    def page_url(self):
        return f"https://commons.wikimedia.org/wiki/File:{self._path()}"

    class Meta:
        constraints = [models.UniqueConstraint(fields=["campaign", "filename"], name="unique_image")]
        verbose_name = _("Image")
        verbose_name_plural = _("Images")

    def __str__(self):
        return self.filename


class Juror(models.Model):
    """Person that will judge the images"""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="jurors")
    username = models.CharField(_("username"), max_length=255)
    dashboard_seen_at = models.DateTimeField(_("dashboard first seen at"), null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["campaign", "username"], name="unique_juror")]
        verbose_name = _("Juror")
        verbose_name_plural = _("Jurors")

    def __str__(self):
        return self.username

    @property
    def votes_locked(self):
        return self.dashboard_seen_at is not None


class Pair(models.Model):
    """Pair of images to be voted on, either the left or the right one, or a tie"""
    LEFT_DECISION, RIGHT_DECISION, TIE_DECISION = "L", "R", "T"
    CHOICES = [(LEFT_DECISION, _("left")), (RIGHT_DECISION, _("right")), (TIE_DECISION, _("tie"))]

    juror = models.ForeignKey(Juror, on_delete=models.CASCADE, related_name="pairs")
    position = models.PositiveIntegerField()
    left = models.ForeignKey(Image, on_delete=models.CASCADE, related_name="+")
    right = models.ForeignKey(Image, on_delete=models.CASCADE, related_name="+")
    choice = models.CharField(max_length=1, choices=CHOICES, blank=True)
    voted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["juror", "position"], name="unique_position"),
            models.CheckConstraint(condition=~models.Q(left=models.F("right")), name="distinct_images"),
        ]
        verbose_name = _("Pair")
        verbose_name_plural = _("Pairs")

    def record_vote(self, choice):
        if choice not in (self.LEFT_DECISION, self.RIGHT_DECISION, self.TIE_DECISION):
            raise ValueError(choice)
        if choice == self.choice:
            return
        with transaction.atomic():
            self.choice = choice
            self.voted_at = timezone.now()
            self.save(update_fields=["choice", "voted_at"])
            Vote.objects.create(pair=self, choice=choice)

    def __str__(self):
        return f"{self.juror} #{self.position}"


class Vote(models.Model):
    """Register the vote in the log"""
    pair = models.ForeignKey(Pair, on_delete=models.CASCADE, related_name="votes")
    choice = models.CharField(max_length=1, choices=Pair.CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]