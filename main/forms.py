from django import forms
from .models import TestRegistration, TestSession

class TestRegistrationForm(forms.ModelForm):
    class Meta:
        model = TestRegistration
        fields = ['name', 'email']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'ex: Mohammed Ahmed',
                'required': True,
                'dir': 'ltr',
                'id': 'name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'ex: mohammed@example.com',
                'required': True,
                'id': 'email'
            }),
        }
        labels = {
            'name': 'الاسم (باللغة الإنجليزية) *',
            'email': 'البريد الإلكتروني *',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['email'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email has already taken the test
        if TestRegistration.objects.filter(email=email, has_taken_test=True).exists():
            raise forms.ValidationError(
                'هذا البريد الإلكتروني قد قام بالاختبار من قبل. كل بريد إلكتروني يمكنه إجراء الاختبار مرة واحدة فقط.'
            )
        return email


class TestAnswerForm(forms.Form):
    """نموذج لتقديم إجابة واحدة"""
    question_id = forms.IntegerField(widget=forms.HiddenInput())
    answer = forms.ChoiceField(
        choices=[
            (2, 'ينطبق تماما'),
            (1.5, 'ينطبق نوعا ما'),
            (1, 'محايد (لست متأكدا)'),
            (0.5, 'لا ينطبق نوعا ما'),
            (0, 'لا ينطبق إطلاقا'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'answer-option'}),
        label='',
        required=True
    )


from django import forms
from .models import TestRegistration, TestSession, Question, Trait, DirectorProfile
from django.contrib.auth.models import User

class DirectorLoginForm(forms.Form):
    username = forms.CharField(
        label='اسم المستخدم',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'أدخل اسم المستخدم',
            'required': True
        })
    )
    password = forms.CharField(
        label='كلمة المرور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'أدخل كلمة المرور',
            'required': True
        })
    )

from django import forms
from .models import TestRegistration, TestSession, Question, Trait, DirectorProfile
from django.contrib.auth.models import User
from decimal import Decimal

class TraitForm(forms.ModelForm):
    class Meta:
        model = Trait
        fields = ['name', 'name_en', 'weight', 'description', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'اسم السمة بالعربية',
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Trait name in English',
                'dir': 'ltr'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0.01',
                'max': '100.00',
                'step': '0.01',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'وصف السمة',
                'rows': 3
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 0
            }),
        }
        labels = {
            'name': 'اسم السمة *',
            'name_en': 'اسم السمة (إنجليزي)',
            'weight': 'الوزن *',
            'description': 'الوصف',
            'order': 'الترتيب',
            'is_active': 'نشط'
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['trait', 'text', 'order', 'is_active', 'is_reverse_scored']
        widgets = {
            'trait': forms.Select(attrs={
                'class': 'form-input',
                'required': True
            }),
            'text': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'أدخل نص السؤال',
                'rows': 3,
                'required': True
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 0
            }),
        }
        labels = {
            'trait': 'السمة المرتبطة *',
            'text': 'نص السؤال *',
            'order': 'الترتيب',
            'is_active': 'نشط',
            'is_reverse_scored': 'عكس التقييم'
        }


from django import forms
from .models import JuniorTestRegistration, JuniorQuestion, JuniorTrait

class JuniorTestRegistrationForm(forms.ModelForm):
    class Meta:
        model = JuniorTestRegistration
        fields = ['name', 'email']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'اكتب اسمك هنا',
                'required': True,
                'dir': 'rtl'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'اكتب بريدك الإلكتروني هنا',
                'required': True,
                'dir': 'ltr'
            }),
        }
        labels = {
            'name': 'الاسم *',
            'email': 'البريد الإلكتروني *',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email has already taken the test
        if JuniorTestRegistration.objects.filter(email=email, has_taken_test=True).exists():
            raise forms.ValidationError(
                'هذا البريد الإلكتروني قد قام بالاختبار من قبل. كل بريد إلكتروني يمكنه إجراء الاختبار مرة واحدة فقط.'
            )
        return email

class JuniorTraitForm(forms.ModelForm):
    class Meta:
        model = JuniorTrait
        fields = ['name', 'name_en', 'weight', 'description', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'اسم السمة بالعربية',
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Trait name in English',
                'dir': 'ltr'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0.01',
                'max': '100.00',
                'step': '0.01',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'وصف السمة',
                'rows': 3
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 0
            }),
        }

class JuniorQuestionForm(forms.ModelForm):
    class Meta:
        model = JuniorQuestion
        fields = ['trait', 'text', 'order', 'is_active', 'is_reverse_scored']
        widgets = {
            'trait': forms.Select(attrs={
                'class': 'form-input',
                'required': True
            }),
            'text': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'أدخل نص السؤال',
                'rows': 3,
                'required': True
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 0
            }),
        }
        labels = {
            'trait': 'السمة المرتبطة *',
            'text': 'نص السؤال *',
            'order': 'الترتيب',
            'is_active': 'نشط',
            'is_reverse_scored': 'عكس التقييم'
        }



