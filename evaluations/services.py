import random
from django.db import transaction

from .models import Campaign, Image, Juror, Pair
from .pairing import schedule


def clean_filename(name):
    """It clears the file name of namespace 'File' and encoded formatting"""
    return name.strip().removeprefix("File:").replace("_", " ")


@transaction.atomic
def create_campaign(name, files, jurors, blocks=9, seed=None):
    """Creates a campaign so jury can vote on"""
    if seed is None:
        seed = random.randrange(1_000_000)

    campaign = Campaign.objects.create(name=name, blocks_per_juror=blocks, seed=seed)
    Image.objects.bulk_create(Image(campaign=campaign, filename=f) for f in files)
    images = {img.id: img for img in campaign.images.all()}
    for username, pairs in zip(jurors, schedule(list(images), len(jurors), blocks, seed)):
        juror = Juror.objects.create(campaign=campaign, username=username)
        Pair.objects.bulk_create(
            Pair(juror=juror, position=i, left=images[a], right=images[b])
            for i, (a, b) in enumerate(pairs, 1)
        )
    return campaign