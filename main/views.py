from django.http import HttpResponse
from django.shortcuts import render


def home(request):
    context = {
        'page_title': 'Home Page',
        'welcome_message': 'Welcome to our ILEFN project!'
    }
    return render(request, 'main/index.html', context)

def programs(request):
    return render(request, 'main/programs.html')

def licence_test(request):
    return render(request, 'main/licence_test.html')

def gallery(request):
    return render(request, 'main/gallery.html')

def program1(request):
    return render(request, 'main/program1.html')

def program2(request):
    return render(request, 'main/program2.html')

def program3(request):
    return render(request, 'main/program3.html')

def program4(request):
    return render(request, 'main/program4.html')

from django.shortcuts import render

def ilfen_test_view(request):
    """
    View for the ILFEN entrepreneurship test page.
    This page provides information about the test and allows users to start it.
    """
    context = {
        'page_title': 'اختبار ILFEN - اختبار سمات رائد الأعمال',
        'test_features': {
            'questions_count': '40-50 سؤال متعدد الاختيارات',
            'test_duration': '40-45 دقيقة',
            'certificate': 'معتمدة من جمعية ريادة الاعمال في جامعة الملك سعود'
        }
    }
    return render(request, 'main/ilfen_test.html', context)


def junior_ilfen_test_view(request):
    context = {
        'page_title': 'مقياس ILFEN للناشئين - اكتشاف المهارات الريادية',
    }
    return render(request, 'main/junior_ilfen_test.html', context)


from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .forms import TestRegistrationForm
from .models import TestRegistration
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from decimal import Decimal
import json

from .forms import TestRegistrationForm
from .models import TestRegistration, Question, Trait, TestSession, TestResult
from .utils import generate_certificate, calculate_test_results

class TestRegistrationView(View):
    """View for test registration"""
    template_name = 'main/test_registration.html'
    form_class = TestRegistrationForm

    def get(self, request):
        form = self.form_class()
        context = {
            'form': form,
            'page_title': 'التسجيل بالاختبار - ILEFN',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            name = form.cleaned_data['name']

            # Check if registration exists
            registration, created = TestRegistration.objects.get_or_create(
                email=email,
                defaults={'name': name, 'has_taken_test': False}
            )

            if not created and registration.has_taken_test:
                # User already took the test
                context = {
                    'form': self.form_class(),
                    'page_title': 'التسجيل بالاختبار - ILEFN',
                    'error_message': 'هذا البريد الإلكتروني قد قام بالاختبار من قبل. كل بريد إلكتروني يمكنه إجراء الاختبار مرة واحدة فقط.'
                }
                return render(request, self.template_name, context)

            # Update name if it changed
            if not created:
                registration.name = name
                registration.save()

            # Create or get test session
            session, _ = TestSession.objects.get_or_create(
                registration=registration,
                defaults={'is_completed': False}
            )

            # Store session ID in cookie and redirect to test
            response = redirect('take_test')
            response.set_cookie('test_session_id', session.id, max_age=86400)  # 24 hours
            return response

        context = {
            'form': form,
            'page_title': 'التسجيل بالاختبار - ILEFN',
        }
        return render(request, self.template_name, context)


def take_test(request):
    """View for taking the test"""
    # Get session from cookie
    session_id = request.COOKIES.get('test_session_id')
    if not session_id:
        return redirect('test_registration')

    try:
        session = TestSession.objects.get(id=session_id, is_completed=False)
    except TestSession.DoesNotExist:
        return redirect('test_registration')

    # Get all active questions
    questions = Question.objects.filter(is_active=True).select_related('trait').order_by('order')

    if request.method == 'POST':
        # Save answers - automatically assign 0 to unanswered questions
        answers = {}
        for question in questions:
            answer_key = f'question_{question.id}'
            if answer_key in request.POST:
                raw_answer = float(request.POST[answer_key])

                # Handle reverse scoring
                if question.is_reverse_scored:
                    # Reverse the score: 2->0, 1.5->0.5, 1->1, 0.5->1.5, 0->2
                    raw_answer = 2.0 - raw_answer

                answers[str(question.id)] = raw_answer
            else:
                # Assign 0 points to unanswered questions
                answers[str(question.id)] = 0.0

        # Save answers to session
        session.set_answers(answers)
        session.completed_at = timezone.now()
        session.is_completed = True
        session.save()

        # Mark registration as completed
        session.registration.has_taken_test = True
        session.registration.save()

        # Calculate results using the exact formula from documentation
        result = calculate_test_results_exact(session)

        # Generate certificate
        certificate_path = generate_certificate(session.registration, result)
        result.certificate_path = certificate_path
        result.save()

        # Redirect to results
        response = redirect('test_result')
        return response

    # Get current answers if any
    current_answers = session.get_answers()

    context = {
        'page_title': 'اختبار ILFEN - تقييم السمات الريادية',
        'questions': questions,
        'total_questions': questions.count(),
        'current_answers': current_answers,
        'session': session,
        'answer_choices': [
            (2, 'ينطبق تماما'),
            (1.5, 'ينطبق نوعا ما'),
            (1, 'محايد (لست متأكدا)'),
            (0.5, 'لا ينطبق نوعا ما'),
            (0, 'لا ينطبق إطلاقا'),
        ]
    }
    return render(request, 'main/take_test.html', context)


def calculate_test_results_exact(session):
    """
    Calculate test results following the EXACT methodology from documentation:
    1. For each trait: percentage = score / totalScore (where totalScore = questions × 2)
    2. weightedScore = percentage × relativeWeight
    3. Sum all weightedScores
    4. finalScore = (Σ weightedScores / Σ relativeWeights) × 100
    """
    from decimal import Decimal

    answers = session.get_answers()
    traits = Trait.objects.filter(is_active=True).prefetch_related('questions')

    total_weighted_score = Decimal('0')
    total_weights = Decimal('0')
    trait_results = {}

    for trait in traits:
        # Get questions for this trait
        trait_questions = trait.questions.filter(is_active=True)

        if not trait_questions.exists():
            continue

        # Calculate score for this trait
        trait_score = Decimal('0')
        questions_count = 0

        for question in trait_questions:
            questions_count += 1
            # Get the answer value (already reversed if needed during form submission)
            answer_value = answers.get(str(question.id), 0.0)
            trait_score += Decimal(str(answer_value))

        # Calculate total possible score (questions_count × 2)
        total_score = Decimal(str(questions_count * 2))

        # Calculate percentage (score / totalScore)
        if total_score > 0:
            percentage = trait_score / total_score
        else:
            percentage = Decimal('0')

        # Get relative weight
        relative_weight = Decimal(str(trait.weight))

        # Calculate weighted score (percentage × relativeWeight)
        weighted_score = percentage * relative_weight

        # Accumulate totals
        total_weighted_score += weighted_score
        total_weights += relative_weight

        # Store trait result for display
        trait_results[trait.name] = {
            'percentage': float(percentage * 100),  # Display as 0-100%
            'weighted_score': float(weighted_score),
            'weight': float(relative_weight),
            'score': float(trait_score),
            'total_score': float(total_score),
            'questions_count': questions_count
        }

    # Calculate final score: (totalWeightedScore / totalWeights) × 100
    if total_weights > 0:
        final_score = (total_weighted_score / total_weights) * Decimal('100')
    else:
        final_score = Decimal('0')

    # Calculate time taken
    time_taken = (session.completed_at - session.started_at).total_seconds() / 60

    # Create test result
    result = TestResult.objects.create(
        session=session,
        total_score=final_score,
        time_taken_minutes=int(time_taken)
    )

    result.set_trait_scores(trait_results)
    return result


def test_result(request):
    """View for displaying test results"""
    # Get session from cookie
    session_id = request.COOKIES.get('test_session_id')
    if not session_id:
        return redirect('test_registration')

    try:
        session = TestSession.objects.get(id=session_id, is_completed=True)
        result = session.result
    except (TestSession.DoesNotExist, TestResult.DoesNotExist):
        return redirect('test_registration')

    # Get trait scores
    trait_scores = result.get_trait_scores()

    # Calculate time taken in minutes and seconds
    time_taken_seconds = (session.completed_at - session.started_at).total_seconds()
    time_taken_minutes = int(time_taken_seconds // 60)
    time_taken_remaining_seconds = int(time_taken_seconds % 60)

    # Format time as "X د Y ث"
    time_taken_formatted = f"{time_taken_minutes} د {time_taken_remaining_seconds} ث"

    context = {
        'page_title': 'نتيجة المقياس - ILEFN',
        'registration': session.registration,
        'result': result,
        'trait_scores': trait_scores,
        'time_taken': time_taken_formatted,  # Formatted as "X د Y ث"
        'time_taken_minutes': time_taken_minutes,
        'time_taken_seconds': time_taken_remaining_seconds,
        'date': session.completed_at.strftime('%Y-%m-%d'),
    }
    return render(request, 'main/test_result.html', context)

import os
from django.conf import settings
def download_certificate(request):
    """View for downloading certificate"""
    session_id = request.COOKIES.get('test_session_id')
    if not session_id:
        return HttpResponse('غير مصرح', status=403)

    try:
        session = TestSession.objects.get(id=session_id, is_completed=True)
        result = session.result
    except (TestSession.DoesNotExist, TestResult.DoesNotExist):
        return HttpResponse('لم يتم العثور على النتيجة', status=404)

    # Return certificate file
    if result.certificate_path:
        certificate_full_path = os.path.join(settings.MEDIA_ROOT, result.certificate_path)
        if os.path.exists(certificate_full_path):
            with open(certificate_full_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='image/png')
                response['Content-Disposition'] = f'attachment; filename="ILEFN_Certificate_{session.registration.name}.png"'
                return response

    return HttpResponse('الشهادة غير متوفرة', status=404)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Question, Trait, TestRegistration, TestSession, TestResult, DirectorProfile
from .forms import DirectorLoginForm, TraitForm, QuestionForm


def director_login(request):
    """Director login view"""
    print(f"=== DIRECTOR LOGIN VIEW ===")
    print(f"Method: {request.method}")
    print(f"User authenticated: {request.user.is_authenticated}")

    if request.user.is_authenticated:
        if hasattr(request.user, 'directorprofile'):
            print("User has director profile, redirecting to dashboard")
            return redirect('director_dashboard')
        else:
            print("User authenticated but no director profile, logging out")
            logout(request)

    if request.method == 'POST':
        print("POST request received")
        print(f"POST data: {request.POST}")

        form = DirectorLoginForm(request.POST)
        print(f"Form is valid: {form.is_valid()}")

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            print(f"Attempting to authenticate user: {username}")

            user = authenticate(request, username=username, password=password)
            print(f"Authentication result - User: {user}")

            if user is not None:
                print(f"User found: {user.username}")
                print(f"User is staff: {user.is_staff}")
                print(f"User is superuser: {user.is_superuser}")
                print(f"Has directorprofile: {hasattr(user, 'directorprofile')}")

                # Allow staff/superusers or users with director profile
                if hasattr(user, 'directorprofile') or user.is_staff or user.is_superuser:
                    login(request, user)
                    print("Login successful, redirecting to dashboard")
                    return redirect('director_dashboard')
                else:
                    error_msg = 'ليس لديك صلاحية للوصول إلى لوحة المدير'
                    print(f"Error: {error_msg}")
                    form.add_error(None, error_msg)
            else:
                error_msg = 'بيانات الدخول غير صحيحة'
                print(f"Error: {error_msg}")
                form.add_error(None, error_msg)
        else:
            print("Form errors:", form.errors)
    else:
        print("GET request, showing empty form")
        form = DirectorLoginForm()

    context = {
        'form': form,
        'page_title': 'تسجيل دخول المدير'
    }
    return render(request, 'director/login.html', context)


@login_required
def director_logout(request):
    """Director logout view"""
    logout(request)
    return redirect('director_login')


@login_required
def director_dashboard(request):
    """Main director dashboard"""
    if not hasattr(request.user, 'directorprofile'):
        return redirect('director_login')

    # Regular statistics
    total_questions = Question.objects.count()
    active_questions = Question.objects.filter(is_active=True).count()
    total_traits = Trait.objects.count()
    total_registrations = TestRegistration.objects.count()
    completed_tests = TestSession.objects.filter(is_completed=True).count()

    # Junior statistics
    junior_total_questions = JuniorQuestion.objects.count()
    junior_active_questions = JuniorQuestion.objects.filter(is_active=True).count()
    junior_total_traits = JuniorTrait.objects.count()
    junior_total_registrations = JuniorTestRegistration.objects.count()
    junior_completed_tests = JuniorTestSession.objects.filter(is_completed=True).count()

    # Recent activity
    recent_registrations = TestRegistration.objects.order_by('-created_at')[:5]
    recent_sessions = TestSession.objects.filter(is_completed=True).select_related('registration', 'result').order_by('-completed_at')[:5]

    # Trait statistics
    trait_stats = Trait.objects.annotate(question_count=Count('questions'))
    junior_trait_stats = JuniorTrait.objects.annotate(question_count=Count('questions'))

    context = {
        'page_title': 'لوحة التحكم - المدير',
        'total_questions': total_questions,
        'active_questions': active_questions,
        'total_traits': total_traits,
        'total_registrations': total_registrations,
        'completed_tests': completed_tests,
        'junior_total_questions': junior_total_questions,
        'junior_active_questions': junior_active_questions,
        'junior_total_traits': junior_total_traits,
        'junior_total_registrations': junior_total_registrations,
        'junior_completed_tests': junior_completed_tests,
        'recent_registrations': recent_registrations,
        'recent_sessions': recent_sessions,
        'trait_stats': trait_stats,
        'junior_trait_stats': junior_trait_stats,
    }
    return render(request, 'director/dashboard.html', context)


@login_required
def question_list(request):
    """List all questions"""
    if not hasattr(request.user, 'directorprofile'):
        return redirect('director_login')

    questions = Question.objects.select_related('trait').order_by('order', 'id')

    context = {
        'page_title': 'إدارة الأسئلة',
        'questions': questions,
    }
    return render(request, 'director/question_list.html', context)


@login_required
def question_create(request):
    """Create new question"""
    if not hasattr(request.user, 'directorprofile'):
        return redirect('director_login')

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('question_list')
    else:
        form = QuestionForm()

    context = {
        'page_title': 'إضافة سؤال جديد',
        'form': form,
    }
    return render(request, 'director/question_form.html', context)


@login_required
def question_edit(request, pk):
    """Edit existing question"""
    if not hasattr(request.user, 'directorprofile'):
        return redirect('director_login')

    question = get_object_or_404(Question, pk=pk)

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect('question_list')
    else:
        form = QuestionForm(instance=question)

    context = {
        'page_title': 'تعديل السؤال',
        'form': form,
        'question': question,
    }
    return render(request, 'director/question_form.html', context)


@login_required
def question_delete(request, pk):
    """Delete question"""
    if not hasattr(request.user, 'directorprofile'):
        return redirect('director_login')

    question = get_object_or_404(Question, pk=pk)

    if request.method == 'POST':
        question.delete()
        return redirect('question_list')

    context = {
        'page_title': 'حذف السؤال',
        'question': question,
    }
    return render(request, 'director/question_confirm_delete.html', context)


@login_required
def trait_list(request):
    """List all traits"""
    if not hasattr(request.user, 'directorprofile'):
        return redirect('director_login')

    traits = Trait.objects.annotate(question_count=Count('questions')).order_by('order', 'id')

    context = {
        'page_title': 'إدارة السمات',
        'traits': traits,
    }
    return render(request, 'director/trait_list.html', context)


@login_required
def trait_create(request):
    """Create new trait"""
    if not hasattr(request.user, 'directorprofile'):
        return redirect('director_login')

    if request.method == 'POST':
        form = TraitForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('trait_list')
    else:
        form = TraitForm()

    context = {
        'page_title': 'إضافة سمة جديدة',
        'form': form,
    }
    return render(request, 'director/trait_form.html', context)


@login_required
def trait_edit(request, pk):
    """Edit existing trait"""
    if not hasattr(request.user, 'directorprofile'):
        return redirect('director_login')

    trait = get_object_or_404(Trait, pk=pk)

    if request.method == 'POST':
        form = TraitForm(request.POST, instance=trait)
        if form.is_valid():
            form.save()
            return redirect('trait_list')
    else:
        form = TraitForm(instance=trait)

    context = {
        'page_title': 'تعديل السمة',
        'form': form,
        'trait': trait,
    }
    return render(request, 'director/trait_form.html', context)


@login_required
def trait_delete(request, pk):
    """Delete trait"""
    if not hasattr(request.user, 'directorprofile'):
        return redirect('director_login')

    trait = get_object_or_404(Trait, pk=pk)

    if request.method == 'POST':
        trait.delete()
        return redirect('trait_list')

    context = {
        'page_title': 'حذف السمة',
        'trait': trait,
    }
    return render(request, 'director/trait_confirm_delete.html', context)


@login_required
def test_results(request):
    """View all test results"""
    if not hasattr(request.user, 'directorprofile'):
        return redirect('director_login')

    results = TestResult.objects.select_related('session__registration').order_by('-created_at')

    context = {
        'page_title': 'نتائج الاختبارات',
        'results': results,
    }
    return render(request, 'director/test_results.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.utils import timezone
from django.db.models import Count, Avg
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from datetime import datetime
import json
from decimal import Decimal

from .models import JuniorTestRegistration, JuniorTestSession, JuniorTestResult, JuniorQuestion, JuniorTrait
from .forms import JuniorTestRegistrationForm


# Junior Test Views
class JuniorTestRegistrationView(View):
    """View for junior test registration"""
    template_name = 'main/junior_test_registration.html'
    form_class = JuniorTestRegistrationForm

    def get(self, request):
        form = self.form_class()
        context = {
            'form': form,
            'page_title': 'التسجيل باختبار الناشئين - ILFEN',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            name = form.cleaned_data['name']

            # Check if registration exists
            registration, created = JuniorTestRegistration.objects.get_or_create(
                email=email,
                defaults={'name': name, 'has_taken_test': False}
            )

            if not created and registration.has_taken_test:
                # User already took the test
                context = {
                    'form': self.form_class(),
                    'page_title': 'التسجيل باختبار الناشئين - ILFEN',
                    'error_message': 'هذا البريد الإلكتروني قد قام بالاختبار من قبل. كل بريد إلكتروني يمكنه إجراء الاختبار مرة واحدة فقط.'
                }
                return render(request, self.template_name, context)

            # Update name if it changed
            if not created:
                registration.name = name
                registration.save()

            # Create test session
            session = JuniorTestSession.objects.create(
                registration=registration,
                is_completed=False
            )

            # Store session ID in cookie and redirect to test
            response = redirect('junior_take_test')
            response.set_cookie('junior_test_session_id', session.id, max_age=86400)  # 24 hours
            return response

        context = {
            'form': form,
            'page_title': 'التسجيل باختبار الناشئين - ILFEN',
        }
        return render(request, self.template_name, context)


def junior_take_test(request):
    """View for taking the junior test"""
    # Get session from cookie
    session_id = request.COOKIES.get('junior_test_session_id')
    if not session_id:
        return redirect('junior_test_registration')

    try:
        session = JuniorTestSession.objects.get(id=session_id, is_completed=False)
    except JuniorTestSession.DoesNotExist:
        return redirect('junior_test_registration')

    # Get all active questions
    questions = JuniorQuestion.objects.filter(is_active=True).select_related('trait').order_by('order')

    if request.method == 'POST':
        # Save answers - handle reverse scoring
        answers = {}
        for question in questions:
            answer_key = f'question_{question.id}'
            if answer_key in request.POST:
                raw_answer = float(request.POST[answer_key])

                # Handle reverse scoring for junior questions
                if question.is_reverse_scored:
                    # Reverse the score: 2->0, 1.5->0.5, 1->1, 0.5->1.5, 0->2
                    raw_answer = 2.0 - raw_answer

                answers[str(question.id)] = raw_answer
            else:
                # Assign 0 points to unanswered questions
                answers[str(question.id)] = 0.0

        # Save answers to session
        session.set_answers(answers)
        session.completed_at = timezone.now()
        session.is_completed = True
        session.save()

        # Mark registration as completed
        session.registration.has_taken_test = True
        session.registration.save()

        # Calculate results
        result = calculate_junior_test_results(session)

        # Generate certificate
        from .utils import generate_junior_certificate
        certificate_path = generate_junior_certificate(session.registration, result)
        result.certificate_path = certificate_path
        result.save()

        # Redirect to results
        response = redirect('junior_test_result')
        return response

    # Get current answers if any
    current_answers = session.get_answers()

    context = {
        'page_title': 'اختبار ILFEN للناشئين - تقييم السمات الريادية',
        'questions': questions,
        'total_questions': questions.count(),
        'current_answers': current_answers,
        'session': session,
        'answer_choices': [
            (2, 'ينطبق تماما'),
            (1.5, 'ينطبق نوعا ما'),
            (1, 'محايد (لست متأكدا)'),
            (0.5, 'لا ينطبق نوعا ما'),
            (0, 'لا ينطبق إطلاقا'),
        ]
    }
    return render(request, 'main/junior_take_test.html', context)


def calculate_junior_test_results(session):
    """Calculate test results based on the scoring logic"""
    answers = session.get_answers()
    questions = JuniorQuestion.objects.filter(is_active=True).select_related('trait')

    # Group answers by trait
    trait_scores = {}
    trait_max_scores = {}

    for question in questions:
        trait_id = question.trait.id
        trait_weight = question.trait.weight

        if trait_id not in trait_scores:
            trait_scores[trait_id] = 0
            trait_max_scores[trait_id] = 0

        # Get user's score for this question
        user_score = answers.get(str(question.id), 0.0)
        max_score = 2.0  # Maximum score per question

        trait_scores[trait_id] += float(user_score)
        trait_max_scores[trait_id] += max_score

    # Calculate percentage for each trait
    trait_results = {}
    total_weighted_score = Decimal('0')
    total_weight = Decimal('0')

    for trait_id, user_score in trait_scores.items():
        trait = JuniorTrait.objects.get(id=trait_id)
        max_score = trait_max_scores[trait_id]

        if max_score > 0:
            trait_percentage = Decimal(str(user_score / max_score * 100))
            trait_weight_decimal = Decimal(str(trait.weight))
            weighted_score = (trait_percentage * trait_weight_decimal) / Decimal('100')

            trait_results[trait.name] = {
                'percentage': float(trait_percentage),
                'weighted_score': float(weighted_score),
                'weight': float(trait_weight_decimal)
            }

            total_weighted_score += weighted_score
            total_weight += trait_weight_decimal

    # Calculate total score
    if total_weight > 0:
        total_score = (total_weighted_score / total_weight) * Decimal('100')
    else:
        total_score = Decimal('0')

    # Calculate time taken
    time_taken = (session.completed_at - session.started_at).total_seconds() / 60

    # Create test result
    result = JuniorTestResult.objects.create(
        session=session,
        total_score=float(total_score),  # Convert to float for storage
        time_taken_minutes=int(time_taken)
    )

    result.set_trait_scores(trait_results)
    return result


def junior_test_result(request):
    """View for displaying junior test results"""
    # Get session from cookie
    session_id = request.COOKIES.get('junior_test_session_id')
    if not session_id:
        return redirect('junior_test_registration')

    try:
        session = JuniorTestSession.objects.get(id=session_id, is_completed=True)
        result = session.result
    except (JuniorTestSession.DoesNotExist, JuniorTestResult.DoesNotExist):
        return redirect('junior_test_registration')

    # Get trait scores
    trait_scores = result.get_trait_scores()

    # Calculate time taken properly
    time_diff = (session.completed_at - session.started_at).total_seconds()

    # Format time as MM:SS
    minutes = int(time_diff // 60)
    seconds = int(time_diff % 60)
    time_taken_formatted = f"{minutes}:{seconds:02d}"

    # Also provide separate values for flexibility
    time_taken_minutes = minutes
    time_taken_seconds = seconds

    context = {
        'page_title': 'نتيجة مقياس الناشئين - ILFEN',
        'registration': session.registration,
        'result': result,
        'trait_scores': trait_scores,
        'time_taken': time_taken_formatted,  # Formatted as MM:SS
        'time_taken_minutes': time_taken_minutes,
        'time_taken_seconds': time_taken_seconds,
        'date': session.completed_at.strftime('%Y-%m-%d'),
    }
    return render(request, 'main/junior_test_result.html', context)


def junior_download_certificate(request):
    """View for downloading junior certificate"""
    session_id = request.COOKIES.get('junior_test_session_id')
    if not session_id:
        return HttpResponse('غير مصرح', status=403)

    try:
        session = JuniorTestSession.objects.get(id=session_id, is_completed=True)
        result = session.result
    except (JuniorTestSession.DoesNotExist, JuniorTestResult.DoesNotExist):
        return HttpResponse('لم يتم العثور على النتيجة', status=404)

    # Generate certificate if not exists
    if not result.certificate_path:
        from .utils import generate_junior_certificate
        certificate_path = generate_junior_certificate(session.registration, result)
        result.certificate_path = certificate_path
        result.save()

    # Return certificate file - construct full path
    if result.certificate_path:
        try:
            # Construct the full file path
            certificate_full_path = os.path.join(settings.MEDIA_ROOT, result.certificate_path)

            if os.path.exists(certificate_full_path):
                with open(certificate_full_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='image/png')
                    response[
                        'Content-Disposition'] = f'attachment; filename="ILEFN_Junior_Certificate_{session.registration.name}.png"'
                    return response
            else:
                # If file doesn't exist, regenerate it
                from .utils import generate_junior_certificate
                certificate_path = generate_junior_certificate(session.registration, result)
                result.certificate_path = certificate_path
                result.save()

                certificate_full_path = os.path.join(settings.MEDIA_ROOT, certificate_path)
                if os.path.exists(certificate_full_path):
                    with open(certificate_full_path, 'rb') as f:
                        response = HttpResponse(f.read(), content_type='image/png')
                        response[
                            'Content-Disposition'] = f'attachment; filename="ILEFN_Junior_Certificate_{session.registration.name}.png"'
                        return response
                else:
                    return HttpResponse('الشهادة غير متوفرة', status=404)

        except FileNotFoundError:
            return HttpResponse('الشهادة غير متوفرة', status=404)

    return HttpResponse('الشهادة غير متوفرة', status=404)


from .forms import JuniorQuestionForm,JuniorTraitForm
@login_required
def junior_question_list(request):
    """List all junior questions"""
    if not hasattr(request.user, 'directorprofile'):
        return redirect('director_login')

    questions = JuniorQuestion.objects.select_related('trait').order_by('order', 'id')

    context = {
        'page_title': 'إدارة أسئلة الناشئين',
        'questions': questions,
    }
    return render(request, 'director/junior_question_list.html', context)

@login_required
def junior_question_create(request):
    """Create new junior question"""
    if not hasattr(request.user, 'directorprofile'):
        return redirect('director_login')

    if request.method == 'POST':
        form = JuniorQuestionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('junior_question_list')
    else:
        form = JuniorQuestionForm()

    context = {
        'page_title': 'إضافة سؤال جديد للناشئين',
        'form': form,
    }
    return render(request, 'director/junior_question_form.html', context)

@login_required
def junior_question_edit(request, pk):
    """Edit existing junior question"""
    if not hasattr(request.user, 'directorprofile'):
        return redirect('director_login')

    question = get_object_or_404(JuniorQuestion, pk=pk)

    if request.method == 'POST':
        form = JuniorQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect('junior_question_list')
    else:
        form = JuniorQuestionForm(instance=question)

    context = {
        'page_title': 'تعديل سؤال الناشئين',
        'form': form,
        'question': question,
    }
    return render(request, 'director/junior_question_form.html', context)

@login_required
def junior_question_delete(request, pk):
    """Delete junior question"""
    if not hasattr(request.user, 'directorprofile'):
        return redirect('director_login')

    question = get_object_or_404(JuniorQuestion, pk=pk)

    if request.method == 'POST':
        question.delete()
        return redirect('junior_question_list')

    context = {
        'page_title': 'حذف سؤال الناشئين',
        'question': question,
    }
    return render(request, 'director/junior_question_confirm_delete.html', context)

@login_required
def junior_trait_list(request):
    """List all junior traits"""
    if not hasattr(request.user, 'directorprofile'):
        return redirect('director_login')

    traits = JuniorTrait.objects.annotate(question_count=Count('questions')).order_by('order', 'id')

    context = {
        'page_title': 'إدارة سمات الناشئين',
        'traits': traits,
    }
    return render(request, 'director/junior_trait_list.html', context)

@login_required
def junior_trait_create(request):
    """Create new junior trait"""
    if not hasattr(request.user, 'directorprofile'):
        return redirect('director_login')

    if request.method == 'POST':
        form = JuniorTraitForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('junior_trait_list')
    else:
        form = JuniorTraitForm()

    context = {
        'page_title': 'إضافة سمة جديدة للناشئين',
        'form': form,
    }
    return render(request, 'director/junior_trait_form.html', context)

@login_required
def junior_trait_edit(request, pk):
    """Edit existing junior trait"""
    if not hasattr(request.user, 'directorprofile'):
        return redirect('director_login')

    trait = get_object_or_404(JuniorTrait, pk=pk)

    if request.method == 'POST':
        form = JuniorTraitForm(request.POST, instance=trait)
        if form.is_valid():
            form.save()
            return redirect('junior_trait_list')
    else:
        form = JuniorTraitForm(instance=trait)

    context = {
        'page_title': 'تعديل سمة الناشئين',
        'form': form,
        'trait': trait,
    }
    return render(request, 'director/junior_trait_form.html', context)

@login_required
def junior_trait_delete(request, pk):
    """Delete junior trait"""
    if not hasattr(request.user, 'directorprofile'):
        return redirect('director_login')

    trait = get_object_or_404(JuniorTrait, pk=pk)

    if request.method == 'POST':
        trait.delete()
        return redirect('junior_trait_list')

    context = {
        'page_title': 'حذف سمة الناشئين',
        'trait': trait,
    }
    return render(request, 'director/junior_trait_confirm_delete.html', context)

