from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404
from accessibility_monitoring_platform.apps.users.forms import (
    CustomUserCreationForm,
    UpdateUser
)


def register(request):
    form = CustomUserCreationForm(
        data=request.POST or None,
        request=request
    )
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            user.username = form.cleaned_data['email']
            user.save()
            login(request, user)
            return redirect(reverse('dashboard:home'))
    context = {
        'form': form,
        'form_groups': ['last_name', 'email_confirm']
    }
    return render(request, 'users/register.html', context)


@login_required
def account_details(request):
    user = get_object_or_404(
        User,
        id=request.user.id
    )
    initial = model_to_dict(user)
    initial['email_confirm'] = initial['email']
    form = UpdateUser(
        data=request.POST or None,
        request=request,
        initial=initial
    )

    if request.method == 'POST':
        if form.is_valid():
            user.username = form.cleaned_data['email']
            user.email = form.cleaned_data['email']
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()
            login(request, user)
            messages.success(request, 'Successfully saved details!')
            return redirect('users:account_details')
        messages.error(request, 'There were errors in the form')

    context = {
        'form': form,
        'form_groups': ['last_name', 'email_confirm']
    }
    return render(request, 'users/account_details.html', context)
