import pickle
import json
from django import forms

import datasample
from .models import Sample


class SampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        fields = ['name', 'description', 'is_active', 'deleted', 'version', 'revision']

    revision = forms.IntegerField(disabled=True)


class CheckDatasampleForm(forms.ModelForm):
    """
        Форма для проверки соответсвия параметров и настроек описанию схемы доступа к данным

        На форме должны быть предусмотрены кнопки:
        [ Изменить описание схемы ] - открывает диалог редактора Sample
        [ Download repr(Sample) ]
        [ Download repr(Params) ]
        [ Download repr(Options) ]
        [ Проверить ]
        [ Выполнить ]
    """
    class Meta:
        model = Sample
        fields = [
            'name', 'revision',
            'src_json', 'params_json', 'options_json',
            'db_user', 'db_password', 'db_host', 'db_port', 'db_name',
        ]
    name = forms.CharField(disabled=True)
    revision = forms.CharField(disabled=True)
    # ------------------------------------------------- metadata for compose --
    src_json = forms.CharField(label="Sample in JSON",
                               widget=forms.Textarea(attrs={'cols': 60}))
    src_python = forms.CharField(label="Sample in Python", required=False,  # disabled=True,
                                 widget=forms.Textarea(attrs={'cols': 80}))
    params_json = forms.CharField(label="Params in JSON", required=False,
                                  widget=forms.Textarea(attrs={'cols': 60}))
    params_python = forms.CharField(label="Params in Python", required=False,  # disabled=True,
                                    widget=forms.Textarea(attrs={'cols': 80}))
    options_json = forms.CharField(label="Options in JSON", required=False,
                                   widget=forms.Textarea(attrs={'cols': 60}))
    options_python = forms.CharField(label="Options in Python", required=False,  # disabled=True,
                                     widget=forms.Textarea(attrs={'cols': 80}))
    # ------------------------------------------------------------------ SQL --
    sql_stmt = forms.CharField(label="SQL statement", required=False, disabled=True,
                               widget=forms.Textarea(attrs={'cols': 80}))
    sql_kwargs = forms.CharField(label="Bindary variables", required=False, disabled=True,
                                 widget=forms.Textarea(attrs={'cols': 40}))
    # -------------------------------------------------------- DB connection --
    db_user = forms.CharField(label="DB User", required=False)
    db_password = forms.CharField(label="DB Password", required=False,
                                  widget=forms.PasswordInput)
    db_host = forms.CharField(label="DB Host", required=False)
    db_port = forms.CharField(label="DB Port", required=False)
    db_name = forms.CharField(label="DB Name", required=False)

    def save(self, commit=True):
        instance = super().save(commit=commit)
        instance.obj = pickle.dumps(datasample.Sample(json.loads(self.cleaned_data['src_json'])))
        return instance
