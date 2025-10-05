from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class TestRegistration(models.Model):
    name = models.CharField(max_length=200, verbose_name="الاسم")
    email = models.EmailField(unique=True, verbose_name="البريد الإلكتروني")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاريخ التسجيل")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    has_taken_test = models.BooleanField(default=False, verbose_name="أخذ الاختبار")

    class Meta:
        verbose_name = "تسجيل الاختبار"
        verbose_name_plural = "تسجيلات الاختبار"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.email}"


from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import json
from decimal import Decimal


class Trait(models.Model):
    """السمات الريادية - Entrepreneurial Traits"""
    name = models.CharField(max_length=200, verbose_name="اسم السمة")
    name_en = models.CharField(max_length=200, verbose_name="Trait Name (English)", blank=True)
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('100.00'))],
        verbose_name="الوزن النسبي",
        help_text="القيمة النسبية لهذه السمة (0.01-100.00)"
    )
    description = models.TextField(verbose_name="وصف السمة", blank=True)
    order = models.IntegerField(default=0, verbose_name="الترتيب")
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    class Meta:
        verbose_name = "سمة ريادية"
        verbose_name_plural = "السمات الريادية"
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} (وزن: {self.weight})"


class Question(models.Model):
    """أسئلة الاختبار"""
    trait = models.ForeignKey(
        Trait,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="السمة المرتبطة"
    )
    text = models.TextField(verbose_name="نص السؤال")
    order = models.IntegerField(default=0, verbose_name="الترتيب")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    is_reverse_scored = models.BooleanField(
        default=False,
        verbose_name="عكس التقييم",
        help_text="إذا كانت الإجابة الإيجابية تعني درجة منخفضة"
    )

    class Meta:
        verbose_name = "سؤال"
        verbose_name_plural = "الأسئلة"
        ordering = ['order']

    def __str__(self):
        return f"س{self.order}: {self.text[:50]}..."


class TestSession(models.Model):
    """جلسة اختبار"""
    registration = models.OneToOneField(
        TestRegistration,
        on_delete=models.CASCADE,
        related_name='test_session',
        verbose_name="التسجيل"
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="بدأ في")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="انتهى في")
    is_completed = models.BooleanField(default=False, verbose_name="مكتمل")
    answers_json = models.TextField(blank=True, verbose_name="الإجابات (JSON)")

    class Meta:
        verbose_name = "جلسة اختبار"
        verbose_name_plural = "جلسات الاختبار"
        ordering = ['-started_at']

    def __str__(self):
        return f"جلسة: {self.registration.name} - {self.started_at.strftime('%Y-%m-%d')}"

    def set_answers(self, answers_dict):
        """حفظ الإجابات كـ JSON"""
        self.answers_json = json.dumps(answers_dict, ensure_ascii=False)
        self.save()

    def get_answers(self):
        """استرجاع الإجابات من JSON"""
        if self.answers_json:
            return json.loads(self.answers_json)
        return {}


class TestResult(models.Model):
    """نتائج الاختبار"""
    session = models.OneToOneField(
        TestSession,
        on_delete=models.CASCADE,
        related_name='result',
        verbose_name="الجلسة"
    )
    total_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="الدرجة الكلية (%)"
    )
    trait_scores_json = models.TextField(verbose_name="درجات السمات (JSON)")
    certificate_path = models.CharField(max_length=500, blank=True, verbose_name="مسار الشهادة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    time_taken_minutes = models.IntegerField(default=0, verbose_name="الوقت المستغرق (دقائق)")

    class Meta:
        verbose_name = "نتيجة اختبار"
        verbose_name_plural = "نتائج الاختبارات"
        ordering = ['-created_at']

    def __str__(self):
        return f"نتيجة: {self.session.registration.name} - {self.total_score}%"

    def set_trait_scores(self, trait_scores_dict):
        """حفظ درجات السمات كـ JSON"""
        self.trait_scores_json = json.dumps(trait_scores_dict, ensure_ascii=False)
        self.save()

    def get_trait_scores(self):
        """استرجاع درجات السمات من JSON"""
        if self.trait_scores_json:
            return json.loads(self.trait_scores_json)
        return {}

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import json
from django.contrib.auth.models import User

class DirectorProfile(models.Model):
    """Director profile for dashboard access"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_director = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "مدير"
        verbose_name_plural = "المدراء"

    def __str__(self):
        return f"مدير: {self.user.username}"


from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class JuniorTestRegistration(models.Model):
    name = models.CharField(max_length=200, verbose_name="الاسم")
    email = models.EmailField(unique=True, verbose_name="البريد الإلكتروني")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاريخ التسجيل")
    has_taken_test = models.BooleanField(default=False, verbose_name="أخذ الاختبار")

    class Meta:
        verbose_name = "تسجيل اختبار الناشئين"
        verbose_name_plural = "تسجيلات اختبار الناشئين"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.email}"


class JuniorTrait(models.Model):
    """السمات الريادية للناشئين"""
    name = models.CharField(max_length=200, verbose_name="اسم السمة")
    name_en = models.CharField(max_length=200, verbose_name="Trait Name (English)", blank=True)
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('100.00'))],
        verbose_name="الوزن النسبي",
        help_text="القيمة النسبية لهذه السمة (0.01-100.00)"
    )
    description = models.TextField(verbose_name="وصف السمة", blank=True)
    order = models.IntegerField(default=0, verbose_name="الترتيب")
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    class Meta:
        verbose_name = "سمة ريادية للناشئين"
        verbose_name_plural = "السمات الريادية للناشئين"
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} (وزن: {self.weight})"


class JuniorQuestion(models.Model):
    """أسئلة اختبار الناشئين"""
    trait = models.ForeignKey(
        JuniorTrait,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="السمة المرتبطة"
    )
    text = models.TextField(verbose_name="نص السؤال")
    order = models.IntegerField(default=0, verbose_name="الترتيب")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    is_reverse_scored = models.BooleanField(
        default=False,
        verbose_name="عكس التقييم",
        help_text="إذا كانت الإجابة الإيجابية تعني درجة منخفضة"
    )

    class Meta:
        verbose_name = "سؤال الناشئين"
        verbose_name_plural = "أسئلة الناشئين"
        ordering = ['order']

    def __str__(self):
        return f"س{self.order}: {self.text[:50]}..."


class JuniorTestSession(models.Model):
    """جلسة اختبار الناشئين"""
    registration = models.OneToOneField(
        JuniorTestRegistration,
        on_delete=models.CASCADE,
        related_name='test_session',
        verbose_name="التسجيل"
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="بدأ في")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="انتهى في")
    is_completed = models.BooleanField(default=False, verbose_name="مكتمل")
    answers_json = models.TextField(blank=True, verbose_name="الإجابات (JSON)")

    class Meta:
        verbose_name = "جلسة اختبار الناشئين"
        verbose_name_plural = "جلسات اختبار الناشئين"
        ordering = ['-started_at']

    def __str__(self):
        return f"جلسة ناشئين: {self.registration.name} - {self.started_at.strftime('%Y-%m-%d')}"

    def set_answers(self, answers_dict):
        """حفظ الإجابات كـ JSON"""
        self.answers_json = json.dumps(answers_dict, ensure_ascii=False)
        self.save()

    def get_answers(self):
        """استرجاع الإجابات من JSON"""
        if self.answers_json:
            return json.loads(self.answers_json)
        return {}


class JuniorTestResult(models.Model):
    """نتائج اختبار الناشئين"""
    session = models.OneToOneField(
        JuniorTestSession,
        on_delete=models.CASCADE,
        related_name='result',
        verbose_name="الجلسة"
    )
    total_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="الدرجة الكلية (%)"
    )
    trait_scores_json = models.TextField(verbose_name="درجات السمات (JSON)")
    certificate_path = models.CharField(max_length=500, blank=True, verbose_name="مسار الشهادة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    time_taken_minutes = models.IntegerField(default=0, verbose_name="الوقت المستغرق (دقائق)")

    class Meta:
        verbose_name = "نتيجة اختبار الناشئين"
        verbose_name_plural = "نتائج اختبارات الناشئين"
        ordering = ['-created_at']

    def __str__(self):
        return f"نتيجة ناشئين: {self.session.registration.name} - {self.total_score}%"

    def set_trait_scores(self, trait_scores_dict):
        """حفظ درجات السمات كـ JSON"""
        self.trait_scores_json = json.dumps(trait_scores_dict, ensure_ascii=False)
        self.save()

    def get_trait_scores(self):
        """استرجاع درجات السمات من JSON"""
        if self.trait_scores_json:
            return json.loads(self.trait_scores_json)
        return {}