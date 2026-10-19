from django import forms
from django.utils.translation import gettext_lazy as _

from .services import clean_filename
from .models import normalize_username


def lines(text):
    """Splits a text by \n"""
    return list(dict.fromkeys(l.strip() for l in text.splitlines() if l.strip()))


class CampaignForm(forms.Form):
    """Campaign form"""
    name = forms.CharField(label=_("Name"), max_length=200)
    files = forms.CharField(label=_("Commons files"), widget=forms.Textarea(attrs={"rows": 12, "spellcheck": "false"}), help_text=_("One file name per line."))
    jurors = forms.CharField(label=_("Jurors"), widget=forms.Textarea(attrs={"rows": 6, "spellcheck": "false"}), help_text=_("One Wikimedia username per line."))
    blocks = forms.IntegerField(label=_("Blocks per juror"), initial=9, min_value=1)

    def clean_files(self):
        files = list(dict.fromkeys(clean_filename(f) for f in lines(self.cleaned_data["files"])))
        if len(files) < 2:
            raise forms.ValidationError(_("Provide at least two files."))
        return files

    def clean_jurors(self):
        jurors = list(dict.fromkeys(normalize_username(j) for j in lines(self.cleaned_data["jurors"])))
        if not jurors:
            raise forms.ValidationError(_("Provide at least one juror."))
        return jurors