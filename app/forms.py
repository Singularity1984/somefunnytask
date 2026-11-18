from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from .models import DeliverySlot, Packaging


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'styled-input field-input',
            'autofocus': True,
        })
        self.fields['password'].widget.attrs.update({
            'class': 'styled-input field-input',
        })


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        label="Электронная почта",
        required=True,
        widget=forms.EmailInput(attrs={'class': 'styled-input field-input'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('username', 'password1', 'password2'):
            self.fields[name].widget.attrs.update({'class': 'styled-input field-input'})


class CheckoutForm(forms.Form):
    address = forms.CharField(
        label="Адрес доставки",
        max_length=300,
        widget=forms.TextInput(attrs={
            'class': 'form-input form-input-gap',
            'placeholder': 'Город, улица, дом, квартира',
        }),
    )
    slot = forms.ModelChoiceField(
        label="Интервал доставки",
        queryset=DeliverySlot.objects.all(),
        empty_label="-- Выберите удобное время --",
        widget=forms.Select(attrs={'class': 'form-select form-input-gap'}),
    )
    phone = forms.CharField(
        label="Телефон",
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-input form-input-gap',
            'placeholder': '+7 (999) 123-45-67',
        }),
    )

    def clean_address(self):
        address = self.cleaned_data['address'].strip()
        if len(address) < 10:
            raise forms.ValidationError("Адрес слишком короткий, укажите город и улицу.")
        return address

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        digits = ''.join(ch for ch in phone if ch.isdigit())
        if len(digits) < 10:
            raise forms.ValidationError("Телефон должен содержать не меньше 10 цифр.")
        return phone


class ConstructorForm(forms.Form):
    packaging = forms.ModelChoiceField(
        label="Упаковка",
        queryset=Packaging.objects.all(),
        required=False,
        empty_label="Без упаковки (крафтовая бумага в подарок)",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    card_text = forms.CharField(
        label="Текст открытки",
        max_length=255,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'placeholder': 'Ваши пожелания...',
            'rows': 4,
        }),
    )


class PhotoUploadForm(forms.Form):
    photo = forms.ImageField(
        label="Фото букета",
        widget=forms.ClearableFileInput(attrs={'class': 'file-input'}),
    )

    def clean_photo(self):
        photo = self.cleaned_data['photo']
        if photo.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Файл слишком большой, максимум 5 МБ.")
        return photo


class PasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('old_password', 'new_password1', 'new_password2'):
            self.fields[name].widget.attrs.update({'class': 'styled-input field-input'})
