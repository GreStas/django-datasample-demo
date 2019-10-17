import pickle
import json
import sqlparse
from yapf.yapflib.yapf_api import FormatCode
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import permission_required

import datasample
from . import models
from .forms import SampleForm, CheckDatasampleForm


@permission_required('datasamples.view_sample')
def index(request):
    return render(request,
                  'datasamples/list_samples.html',
                  {'samples': models.Sample.objects.all().order_by('pk')})


@permission_required('datasamples.add_sample')
def create_sample(request):
    instance = models.Sample()
    if request.method == 'POST':
        form = SampleForm(request.POST, instance=instance)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.author = request.user
            instance.publisher = request.user
            instance.obj = pickle.dumps(datasample.Sample())
            instance.save()
            return redirect('datasamples:all-samples')
    form = SampleForm(
        instance=instance,
        initial={'src_json':
                     json.dumps(pickle.loads(instance.obj).state, ensure_ascii=False, indent=2)
                     if instance.obj else '{}'
                 },
    )
    return render(request, 'datasamples/edit_sample.html', {'form': form})


@permission_required('datasamples.change_sample')
def edit_sample(request, pk):
    instance = get_object_or_404(models.Sample, pk=pk)
    secure_fields = {'is_active', 'name', 'description', 'deleted', 'version'}
    if request.method == 'POST':
        form = SampleForm(request.POST, instance=instance)
        if form.has_changed() and form.is_valid():
            try:
                instance = form.save(commit=False)
                # publisher устанавливается, если is_active меняет состояние
                if not secure_fields.isdisjoint(form.changed_data):
                    instance.publisher = request.user
                instance.save()
            except datasample.SampleElementError as e:
                for name, msg in e.errors.items():
                    messages.add_message(request, messages.ERROR, f"'{name}': {msg}")
            except Exception as e:  # TODO конкретизировать список исключений
                messages.add_message(request, messages.ERROR, str(e))
            return redirect('datasamples:all-samples')
    form = SampleForm(
        instance=instance,
    )
    return render(request, 'datasamples/edit_sample.html', {'form': form})


@permission_required('datasamples.view_sample')
def check_datasample(request, pk):

    def get_initial(request, form):
        initial = {key: value for key, value in request.POST.items()}
        initial["src_python"] = form.cleaned_data["src_python"]
        initial["params_python"] = form.cleaned_data["params_python"]
        initial["options_python"] = form.cleaned_data["options_python"]
        return initial

    def get_header(sample_meta, options):
        return [sample_meta['fields'][field_name]['label'] for field_name, _ in options['fields']]

    dataset = []
    header = []
    instance = get_object_or_404(models.Sample, pk=pk)
    if request.method == 'POST':
        form = CheckDatasampleForm(
            request.POST,
            instance=instance,
        )
        button = request.POST.get('btnOK', 'Reload')
        if button == 'Reload':
            instance = get_object_or_404(models.Sample, pk=pk)
            initial = {key: value for key, value in request.POST.items()}
            initial['src_json'] = json.dumps(pickle.loads(instance.obj).state, ensure_ascii=False, indent=2)
            form = CheckDatasampleForm(
                instance=instance,
                initial=initial,
            )
        elif form.has_changed() and form.is_valid():
            try:
                if button == 'SaveSample':
                    # author устанавливается, если изменяется obj
                    if 'src_json' in form.changed_data:
                        instance = form.save(commit=False)
                        instance.author = request.user
                        instance.save()
                        messages.add_message(request, messages.INFO,
                                             "Описание схемы доступа к данным успешно сохранена в БД")
                    else:
                        messages.add_message(request, messages.INFO,
                                             "Описание схемы доступа к данным не было изменено "
                                             "и не теребует сохранения в БД")

                elif button == 'PythonSample':
                    sample = datasample.Sample(json.loads(form.cleaned_data['src_json']))
                    initial = get_initial(request, form)
                    initial["src_python"], _ = FormatCode(repr(sample),
                                                          style_config='pep8')
                    form = CheckDatasampleForm(instance=instance, initial=initial)

                elif button == 'PythonParams':
                    initial = get_initial(request, form)
                    if form.cleaned_data['params_json']:
                        initial["params_python"], _ = FormatCode(repr(json.loads(form.cleaned_data['params_json'])),
                                                                 style_config='pep8')
                    else:
                        initial["params_python"] = ''
                    form = CheckDatasampleForm(instance=instance, initial=initial)

                elif button == 'PythonOptions':
                    initial = get_initial(request, form)
                    if form.cleaned_data['options_json']:
                        initial["options_python"], _ = FormatCode(repr(json.loads(form.cleaned_data['options_json'])),
                                                                  style_config='pep8')
                    else:
                        initial["options_python"] = ''
                    form = CheckDatasampleForm(instance=instance, initial=initial)

                elif button == 'CheckSample':
                    sample = datasample.Sample(json.loads(form.cleaned_data['src_json']))
                    messages.add_message(request, messages.INFO,
                                         "Описание схемы доступа к данным корректно")

                elif button == 'CheckParams':
                    sample = datasample.Sample(json.loads(form.cleaned_data['src_json']))
                    params = json.loads(form.cleaned_data['params_json'])
                    datasample.check_params(params, sample)
                    initial = get_initial(request, form)
                    form = CheckDatasampleForm(instance=instance, initial=initial)
                    messages.add_message(request, messages.INFO, "Описание параметров корректно")

                elif button == 'CheckOptions':
                    sample = datasample.Sample(json.loads(form.cleaned_data['src_json']))
                    options = json.loads(form.cleaned_data['options_json'])
                    datasample.check_options(options, sample)
                    initial = get_initial(request, form)
                    form = CheckDatasampleForm(instance=instance, initial=initial)
                    messages.add_message(request, messages.INFO, "Описание параметров корректно")

                elif button == 'Сompose':
                    initial = get_initial(request, form)
                    sample_meta = json.loads(form.cleaned_data['src_json'])
                    options = json.loads(form.cleaned_data['options_json'])
                    query, kwargs = datasample.compose(
                        sample_meta=sample_meta,
                        params=json.loads(form.cleaned_data['params_json']),
                        options=options,
                    )
                    initial['sql_stmt'] = sqlparse.format(str(query))
                    initial['sql_kwargs'], _ = FormatCode(repr(kwargs), style_config='pep8')
                    header = get_header(sample_meta, options)
                    form = CheckDatasampleForm(instance=instance, initial=initial)

                elif button == 'Execute':
                    sample_meta = json.loads(form.cleaned_data['src_json'])
                    options = json.loads(form.cleaned_data['options_json'])
                    header = get_header(sample_meta, options)
                    dataset = datasample.execute(
                        sample_meta=sample_meta,
                        params=json.loads(form.cleaned_data['params_json']),
                        options=options,
                        db_settings={
                            'USER': form.cleaned_data['db_user'],
                            'PASSWORD': form.cleaned_data['db_password'] if form.cleaned_data['db_password'] else '',
                            'HOST': form.cleaned_data['db_host'],
                            'PORT': form.cleaned_data['db_port'],
                            'NAME': form.cleaned_data['db_name'],
                        }
                    )

            except datasample.SampleElementError as e:
                messages.add_message(request, messages.ERROR, str(e))
            except Exception as e:  # TODO конкретизировать список исключений
                messages.add_message(request, messages.ERROR, str(e))
    else:
        db_settings = settings.DATABASES.get('default')
        initial = {
            'src_json': json.dumps(pickle.loads(instance.obj).state, ensure_ascii=False, indent=2),
            'db_user': db_settings.get('USER'),
            'db_host': db_settings.get('HOST'),
            'db_port': db_settings.get('PORT') if db_settings.get('PORT') else '5432',
            'db_name': db_settings.get('NAME'),
        }
        form = CheckDatasampleForm(instance=instance, initial=initial)
    return render(request, 'datasamples/check_datasample.html', {'form': form, 'header': header, 'dataset': dataset})
