from decimal import Decimal
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings
from .models import Question, Trait, TestResult


def calculate_test_results(session):
    """
    Calculate test results following the exact methodology from documentation:
    1. For each trait: percentage = score / totalScore (where totalScore = questions × 2)
    2. weightedScore = percentage × relativeWeight
    3. Sum all weightedScores
    4. finalScore = (Σ weightedScores / Σ relativeWeights) × 100
    """
    from decimal import Decimal

    answers = session.get_answers()
    traits = Trait.objects.filter(is_active=True).prefetch_related('questions')

    trait_scores = {}
    total_weighted_score = Decimal('0')
    total_weight = Decimal('0')

    for trait in traits:
        # Get all questions for this trait
        questions = trait.questions.filter(is_active=True)

        if not questions.exists():
            continue

        # Calculate score for this trait
        user_score = Decimal('0')
        max_score = Decimal('0')

        for question in questions:
            max_score += Decimal('2')  # Each question max is 2

            # Get user's answer (default to 0 if not found)
            answer_value = Decimal(str(answers.get(str(question.id), '0')))

            # Note: Reverse scoring should already be handled when saving answers
            # Do NOT reverse here if already reversed in the view
            user_score += answer_value

        # Calculate percentage for this trait (as decimal, not ×100 yet)
        if max_score > 0:
            trait_percentage_decimal = user_score / max_score
            trait_percentage_display = trait_percentage_decimal * Decimal('100')  # For display
        else:
            trait_percentage_decimal = Decimal('0')
            trait_percentage_display = Decimal('0')

        # Calculate weighted score (percentage × weight)
        trait_weight = Decimal(str(trait.weight))
        weighted_score = trait_percentage_decimal * trait_weight

        # Store trait score
        trait_scores[trait.name] = {
            'name': trait.name,
            'name_en': trait.name_en,
            'percentage': float(trait_percentage_display),  # Display as 0-100
            'user_score': float(user_score),
            'max_score': float(max_score),
            'weight': float(trait_weight),
            'weighted_score': float(weighted_score)
        }

        total_weighted_score += weighted_score
        total_weight += trait_weight

    # Calculate final score percentage: (sum of weighted scores / sum of weights) × 100
    if total_weight > 0:
        final_score = (total_weighted_score / total_weight) * Decimal('100')  # ✅ NOW MULTIPLY BY 100
    else:
        final_score = Decimal('0')

    # Create or update result
    result, created = TestResult.objects.update_or_create(
        session=session,
        defaults={
            'total_score': final_score,  # This should now be 0-100 range
        }
    )

    result.set_trait_scores(trait_scores)

    # Calculate time taken
    if session.completed_at and session.started_at:
        time_diff = session.completed_at - session.started_at
        result.time_taken_minutes = int(time_diff.total_seconds() / 60)
        result.save()

    return result

from decimal import Decimal
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings
from datetime import datetime

    
def generate_certificate(registration, result):
    """
    Generate an adult certificate with proper text positioning
    """
    template_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'Frame 2 Gold.png')

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Certificate template not found at {template_path}")

    # Load and prepare image
    img = Image.open(template_path).convert('RGBA')
    overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    width, height = img.size

    # Load fonts with error handling
    try:
        font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'alexandria.ttf')
        font_name = ImageFont.truetype(font_path, 70)
        font_label = ImageFont.truetype(font_path, 24)
        font_score = ImageFont.truetype(font_path, 40)
        font_date = ImageFont.truetype(font_path, 22)
    except Exception as e:
        print(f"Font loading error: {e}")
        font_name = font_label = font_score = font_date = ImageFont.load_default()

    # Colors
    black = (0, 0, 0, 255)
    gold = (255, 192, 0, 255)
    white = (255, 255, 255, 255)

    # Cover existing content areas with white
    # Name area
    draw.rectangle([(80, 310), (width - 80, 430)], fill=white)
    # Score area
    draw.rectangle([(width // 2 - 220, 430), (width // 2 + 220, 520)], fill=white)
    # Date area
    draw.rectangle([(100, 680), (370, 750)], fill=white)

    # Draw participant name (centered)
    name_text = registration.name
    name_bbox = draw.textbbox((0, 0), name_text, font=font_name)
    name_width = name_bbox[2] - name_bbox[0]
    name_x = (width - name_width) // 2
    draw.text((name_x, 310), name_text, fill=black, font=font_name)

    # Draw participation label
    participation_text = "على المشاركة في اختبار السمات الريادية"
    label_bbox = draw.textbbox((0, 0), participation_text, font=font_label)
    label_width = label_bbox[2] - label_bbox[0]
    label_x = (width - label_width) // 2
    draw.text((label_x, 430), participation_text, fill=black, font=font_label)

    # Draw score label
    score_label = "والحصول على درجة"
    label2_bbox = draw.textbbox((0, 0), score_label, font=font_label)
    label2_width = label2_bbox[2] - label2_bbox[0]
    label2_x = (width - label2_width) // 2
    draw.text((label2_x, 460), score_label, fill=black, font=font_label)

    # Draw percentage score (gold color)
    score_text = f"{round(result.total_score)}%"
    score_bbox = draw.textbbox((0, 0), score_text, font=font_score)
    score_width = score_bbox[2] - score_bbox[0]
    score_x = (width - score_width) // 2
    draw.text((score_x, 490), score_text, fill=gold, font=font_score)

    # Draw issue date (consistent format)
    date_text = result.created_at.strftime("%Y/%m/%d")
    draw.text((160, 695), date_text, fill=black, font=font_date)

    # Composite and save
    img = Image.alpha_composite(img, overlay)
    img = img.convert('RGB')

    # Save with unique filename
    certificates_dir = os.path.join(settings.MEDIA_ROOT, 'certificates')
    os.makedirs(certificates_dir, exist_ok=True)

    filename = f'certificate_{registration.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    filepath = os.path.join(certificates_dir, filename)
    img.save(filepath, 'PNG', quality=95)

    # Return relative path from MEDIA_ROOT instead of absolute path
    relative_path = os.path.join('certificates', filename)
    return relative_path  # Change this line



def generate_junior_certificate(registration, result):
    """
    Generate a junior certificate with colorful design
    """
    template_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'image.png')

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Junior certificate template not found at {template_path}")

    # Load and prepare image
    img = Image.open(template_path).convert('RGBA')
    overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    width, height = img.size

    # Load fonts
    try:
        font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'alexandria.ttf')
        font_name = ImageFont.truetype(font_path, 70)
        font_label = ImageFont.truetype(font_path, 24)
        font_score = ImageFont.truetype(font_path, 40)
        font_date = ImageFont.truetype(font_path, 20)
    except Exception as e:
        print(f"Font loading error: {e}")
        font_name = font_label = font_score = font_date = ImageFont.load_default()

    # Colors
    black = (0, 0, 0, 255)
    gold = (255, 192, 0, 255)
    white = (255, 255, 255, 255)

    # Cover existing content with white rectangles
    # Name area
    draw.rectangle([(80, 310), (width - 80, 430)], fill=white)
    # Score/label area
    draw.rectangle([(width // 2 - 260, 430), (width // 2 + 260, 550)], fill=white)
    # Date value area only (avoiding the label)
    draw.rectangle([(100, 680), (370, 750)], fill=white)

    # Draw participant name (centered)
    name_text = registration.name
    name_bbox = draw.textbbox((0, 0), name_text, font=font_name)
    name_width = name_bbox[2] - name_bbox[0]
    name_x = (width - name_width) // 2
    draw.text((name_x, 310), name_text, fill=black, font=font_name)

    # Draw participation label
    participation_text = "على المشاركة في اختبار السمات الريادية"
    label_bbox = draw.textbbox((0, 0), participation_text, font=font_label)
    label_width = label_bbox[2] - label_bbox[0]
    label_x = (width - label_width) // 2
    draw.text((label_x, 430), participation_text, fill=black, font=font_label)

    # Draw score label
    score_label = "والحصول على درجة"
    label2_bbox = draw.textbbox((0, 0), score_label, font=font_label)
    label2_width = label2_bbox[2] - label2_bbox[0]
    label2_x = (width - label2_width) // 2
    draw.text((label2_x, 460), score_label, fill=black, font=font_label)

    # Draw percentage score (gold color)
    score_text = f"{round(result.total_score)}%"
    score_bbox = draw.textbbox((0, 0), score_text, font=font_score)
    score_width = score_bbox[2] - score_bbox[0]
    score_x = (width - score_width) // 2
    draw.text((score_x, 490), score_text, fill=gold, font=font_score)

    # Draw dates (consistent format)
    # Start date
    if hasattr(result.session, 'started_at') and result.session.started_at:
        start_date = result.session.started_at.strftime("%Y/%m/%d")
        draw.text((160, 680), start_date, fill=black, font=font_date)



    # Composite and save
    img = Image.alpha_composite(img, overlay)
    img = img.convert('RGB')

    # Save certificate
    # Save certificate
    certificates_dir = os.path.join(settings.MEDIA_ROOT, 'certificates', 'junior')
    os.makedirs(certificates_dir, exist_ok=True)

    filename = f'junior_certificate_{registration.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    filepath = os.path.join(certificates_dir, filename)
    img.save(filepath, 'PNG', quality=95)

    # Return relative path from MEDIA_ROOT instead of absolute path
    relative_path = os.path.join('certificates', 'junior', filename)
    return relative_path  # Change this line


def get_trait_recommendations(trait_scores, total_score):
    """
    Generate recommendations based on trait scores
    Returns a dictionary with weak and strong traits
    """
    # Sort traits by score
    sorted_traits = sorted(
        trait_scores.items(),
        key=lambda x: x[1]['percentage'],
        reverse=True
    )

    # Get top 3 strongest and weakest traits
    strong_traits = sorted_traits[:3]
    weak_traits = sorted_traits[-3:]

    recommendations = {
        'strong_traits': [
            {
                'name': trait[0],
                'percentage': trait[1]['percentage']
            }
            for trait in strong_traits
        ],
        'weak_traits': [
            {
                'name': trait[0],
                'percentage': trait[1]['percentage']
            }
            for trait in weak_traits
        ],
        'overall_level': get_overall_level(total_score)
    }

    return recommendations


def get_overall_level(score):
    """
    Determine overall entrepreneurship level based on score
    """
    score = float(score)

    if score >= 80:
        return {
            'level': 'ممتاز',
            'description': 'لديك سمات رائد أعمال قوية جداً',
            'color': '#0ecd73'
        }
    elif score >= 60:
        return {
            'level': 'جيد جداً',
            'description': 'لديك سمات ريادية جيدة مع مجال للتطوير',
            'color': '#2A5F73'
        }
    elif score >= 40:
        return {
            'level': 'جيد',
            'description': 'لديك أساس جيد ولكن تحتاج إلى تطوير بعض المهارات',
            'color': '#f4a340'
        }
    else:
        return {
            'level': 'يحتاج إلى تطوير',
            'description': 'ننصح بالعمل على تطوير السمات الريادية',
            'color': '#e74c3c'
        }
