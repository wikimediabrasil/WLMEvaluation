from django.core.management.base import BaseCommand
from django.db import transaction

from evaluations.models import Campaign, Image, Juror, Pair
from evaluations.pairing import schedule


class Command(BaseCommand):
    help = "It creates a campaign from a txtCria uma campanha a partir de um .txt com um nome de arquivo do Commons por linha."

    def add_arguments(self, parser):
        parser.add_argument("--name", required=True)
        parser.add_argument("--files", required=True)
        parser.add_argument("--jurors", required=True, help='"Fulano,Beltrano,..."')
        parser.add_argument("--blocks", type=int, default=9)
        parser.add_argument("--seed", type=int)

    @transaction.atomic
    def handle(self, *args, **o):
        with open(o["files"], encoding="utf-8") as fh:
            names = list(dict.fromkeys(
                line.strip().removeprefix("File:").replace("_", " ") for line in fh if line.strip()
            ))
        jurors = [j.strip() for j in o["jurors"].split(",") if j.strip()]

        campaign = Campaign.objects.create(name=o["name"])
        Image.objects.bulk_create(Image(campaign=campaign, filename=n) for n in names)
        images = {img.id: img for img in campaign.images.all()}

        for username, pairs in zip(jurors, schedule(list(images), len(jurors), o["blocks"], o["seed"])):
            juror = Juror.objects.create(campaign=campaign, username=username)
            Pair.objects.bulk_create(
                Pair(juror=juror, position=i, left=images[a], right=images[b])
                for i, (a, b) in enumerate(pairs, 1)
            )

        self.stdout.write(self.style.SUCCESS(
            f"Campanha {campaign.id}: {len(images)} imagens, {len(jurors)} jurados, "
            f"{len(pairs)} pares por jurado."
        ))