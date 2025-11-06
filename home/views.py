from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Avg, Max
from django.utils import timezone
import json
from .models import Student, Test, Question, Answer, TestResult, StudentLogin, StudentActivity

def index(request):
    """Asosiy sahifa"""
    return render(request, 'index.html')

@csrf_exempt
@require_http_methods(["POST"])
def student_login_credentials(request):
    """Login va parol orqali tizimga kirish"""
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        print(f"Login urinishi: {username}")
        
        # Demo admin login
        if username == "admin" and password == "admin123":
            request.session['is_admin'] = True
            request.session['admin_name'] = "Admin User"
            request.session['student_id'] = None
            return JsonResponse({
                'success': True, 
                'message': "Admin sifatida muvaffaqiyatli kirdingiz!",
                'is_admin': True,
                'redirect_url': '/admin-dashboard/'
            })
        
        # Student login - Database dan tekshirish
        try:
            student_login = StudentLogin.objects.select_related('student').get(username=username)
            student = student_login.student
            
            # Bloklanganligini tekshirish
            if student.locked_until and student.locked_until > timezone.now():
                lock_time = student.locked_until - timezone.now()
                minutes = int(lock_time.total_seconds() // 60) + 1
                return JsonResponse({
                    'success': False, 
                    'error': f"Siz bloklangansiz! {minutes} daqiqadan keyin qayta urinib ko'ring."
                })
            
            # Parolni tekshirish
            if student_login.check_password(password):
                # Muvaffaqiyatli login
                student.login_attempts = 0
                student.locked_until = None
                student.is_online = True
                student.save()
                
                # Session ma'lumotlarini o'rnatish
                request.session['student_id'] = student.id
                request.session['student_name'] = f"{student.familya} {student.ism}"
                request.session['is_admin'] = False
                request.session['admin_name'] = None
                
                # Faollikni log qilish
                StudentActivity.objects.create(
                    student=student,
                    activity_type='login',
                    details='Login/parol orqali tizimga kirdi'
                )
                
                return JsonResponse({
                    'success': True, 
                    'message': f"Xush kelibsiz, {request.session['student_name']}!",
                    'is_admin': False,
                    'redirect_url': '/student-dashboard/',
                    'student_name': request.session['student_name'],
                    'student_id': student.id
                })
            else:
                # Noto'g'ri parol
                student.login_attempts += 1
                
                if student.login_attempts >= 3:
                    student.locked_until = timezone.now() + timezone.timedelta(minutes=5)
                    student.save()
                    return JsonResponse({
                        'success': False, 
                        'error': "Noto'g'ri parol! Siz 5 daqiqaga bloklandingiz."
                    })
                else:
                    student.save()
                    return JsonResponse({
                        'success': False, 
                        'error': f"Noto'g'ri parol! {3 - student.login_attempts} marta urinish qoldi."
                    })
            
        except StudentLogin.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': "Login topilmadi! Iltimos, admin bilan bog'laning."
            })
            
    except Exception as e:
        print(f"Login xatosi: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': f"Xatolik: {str(e)}"
        })

def admin_dashboard(request):
    """Admin paneli - FAQAT ADMIN KIRA OLADI"""
    if not request.session.get('is_admin'):
        messages.error(request, "Iltimos, avval tizimga kiring")
        return redirect('index')
    
    # Statistik ma'lumotlar
    students_count = Student.objects.count()
    tests_count = Test.objects.count()
    active_tests_count = Test.objects.filter(is_active=True).count()
    completed_tests_count = TestResult.objects.count()
    
    context = {
        'admin_name': request.session.get('admin_name', 'Admin'),
        'students_count': students_count,
        'tests_count': tests_count,
        'active_tests_count': active_tests_count,
        'completed_tests_count': completed_tests_count,
    }
    return render(request, 'admin_dashboard.html', context)

def student_dashboard(request):
    """Student paneli - FAQAT STUDENT KIRA OLADI"""
    if not request.session.get('student_id'):
        messages.error(request, "Iltimos, avval tizimga kiring")
        return redirect('index')
    
    context = {
        'student_name': request.session.get('student_name', 'Student'),
    }
    return render(request, 'student_dashboard.html', context)

def logout_view(request):
    """Chiqish"""
    student_id = request.session.get('student_id')
    if student_id:
        try:
            student = Student.objects.get(id=student_id)
            student.is_online = False
            student.save()
            
            # Log activity
            StudentActivity.objects.create(
                student=student,
                activity_type='logout',
                details='Tizimdan chiqdi'
            )
        except Student.DoesNotExist:
            pass
    
    request.session.flush()
    messages.success(request, "Tizimdan muvaffaqiyatli chiqdingiz")
    return redirect('index')

# ==================== ADMIN API FUNCTIONS ====================
@csrf_exempt
@require_http_methods(["POST"])
def create_test(request):
    """Yangi test yaratish - FAQAT ADMIN"""
    if not request.session.get('is_admin'):
        return JsonResponse({'success': False, 'error': 'Ruxsat etilmagan!'})
    
    try:
        data = json.loads(request.body)
        
        # Test yaratish
        test = Test.objects.create(
            title=data['title'],
            description=data.get('description', ''),
            time_limit=data.get('time_limit', 60),
            max_score=data.get('max_score', 100),
            is_active=True
        )
        
        # Savollar va javoblarni yaratish
        for question_data in data.get('questions', []):
            question = Question.objects.create(
                test=test,
                text=question_data['text'],
                order=question_data.get('order', 0)
            )
            
            for answer_data in question_data.get('answers', []):
                Answer.objects.create(
                    question=question,
                    text=answer_data['text'],
                    is_correct=answer_data.get('is_correct', False)
                )
        
        return JsonResponse({
            'success': True, 
            'test_id': test.id,
            'message': f'"{test.title}" testi muvaffaqiyatli yaratildi!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def create_student_with_login(request):
    """Yangi o'quvchi yaratish - FAQAT ADMIN"""
    if not request.session.get('is_admin'):
        return JsonResponse({'success': False, 'error': 'Ruxsat etilmagan!'})
    
    try:
        data = json.loads(request.body)
        
        # Validatsiya
        required_fields = ['familya', 'ism', 'username', 'password']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False, 
                    'error': f"'{field}' maydoni to'ldirilishi shart!"
                })
        
        # Username bandligini tekshirish
        if StudentLogin.objects.filter(username=data['username']).exists():
            return JsonResponse({
                'success': False, 
                'error': "Bu login band! Boshqa login tanlang."
            })
        
        # Student yaratish
        student = Student.objects.create(
            familya=data['familya'],
            ism=data['ism'],
            group=data.get('group', ''),
            is_online=False,
            login_attempts=0
        )
        
        # Login ma'lumotlarini yaratish
        student_login = StudentLogin.objects.create(
            student=student,
            username=data['username']
        )
        student_login.set_password(data['password'])
        student_login.save()
        
        return JsonResponse({
            'success': True, 
            'student_id': student.id,
            'message': f"O'quvchi muvaffaqiyatli yaratildi! Login: {data['username']}"
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["GET"])
def get_tests(request):
    """Testlar ro'yxatini olish"""
    if not request.session.get('is_admin') and not request.session.get('student_id'):
        return JsonResponse({'success': False, 'error': 'Ruxsat etilmagan!'})
    
    tests = Test.objects.annotate(
        questions_count=Count('questions')
    ).values(
        'id', 'title', 'description', 'time_limit', 'max_score', 'is_active', 'questions_count', 'created_at'
    ).order_by('-created_at')
    
    # Agar student bo'lsa, faqat faol testlarni ko'rsatish
    if request.session.get('student_id'):
        tests = tests.filter(is_active=True)
    
    return JsonResponse({'success': True, 'tests': list(tests)})

@csrf_exempt
@require_http_methods(["GET"])
def get_students(request):
    """O'quvchilar ro'yxatini olish - FAQAT ADMIN"""
    if not request.session.get('is_admin'):
        return JsonResponse({'success': False, 'error': 'Ruxsat etilmagan!'})
    
    students = Student.objects.all().values(
        'id', 'ism', 'familya', 'group', 'is_online', 'login_attempts', 'created_at'
    ).order_by('-created_at')
    
    return JsonResponse({'success': True, 'students': list(students)})

@csrf_exempt
@require_http_methods(["GET"])
def get_results(request):
    """Natijalar ro'yxatini olish - FAQAT ADMIN"""
    if not request.session.get('is_admin'):
        return JsonResponse({'success': False, 'error': 'Ruxsat etilmagan!'})
    
    results = TestResult.objects.select_related('student', 'test').all().values(
        'id', 'student__ism', 'student__familya', 'test__title', 'score', 
        'correct_answers', 'total_questions', 'completed_at'
    ).order_by('-completed_at')
    
    return JsonResponse({'success': True, 'results': list(results)})

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_student(request, student_id):
    """O'quvchini o'chirish - FAQAT ADMIN"""
    if not request.session.get('is_admin'):
        return JsonResponse({'success': False, 'error': 'Ruxsat etilmagan!'})
    
    try:
        student = get_object_or_404(Student, id=student_id)
        
        # Login ma'lumotlarini ham o'chirish
        StudentLogin.objects.filter(student=student).delete()
        student.delete()
        
        return JsonResponse({'success': True, 'message': 'O\'quvchi muvaffaqiyatli o\'chirildi'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_test(request, test_id):
    """Testni o'chirish - FAQAT ADMIN"""
    if not request.session.get('is_admin'):
        return JsonResponse({'success': False, 'error': 'Ruxsat etilmagan!'})
    
    try:
        test = get_object_or_404(Test, id=test_id)
        test.delete()
        return JsonResponse({'success': True, 'message': 'Test muvaffaqiyatli o\'chirildi'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ==================== STUDENT API FUNCTIONS ====================
@csrf_exempt
@require_http_methods(["GET"])
def get_student_results(request):
    """O'quvchi natijalarini olish - FAQAT STUDENT"""
    if not request.session.get('student_id'):
        return JsonResponse({'success': False, 'error': 'Ruxsat etilmagan!'})
    
    student_id = request.session['student_id']
    student = get_object_or_404(Student, id=student_id)
    
    results = TestResult.objects.filter(student=student).select_related('test').values(
        'id', 'test__title', 'score', 'correct_answers', 'total_questions', 'completed_at'
    ).order_by('-completed_at')
    
    return JsonResponse({'success': True, 'results': list(results)})

@csrf_exempt
@require_http_methods(["GET"])
def get_test_questions(request, test_id):
    """Test savollarini olish - FAQAT STUDENT"""
    if not request.session.get('student_id'):
        return JsonResponse({'success': False, 'error': 'Ruxsat etilmagan!'})
    
    try:
        test = get_object_or_404(Test, id=test_id, is_active=True)
        questions = Question.objects.filter(test=test).prefetch_related('answers')
        
        questions_data = []
        for question in questions:
            answers_data = []
            for answer in question.answers.all():
                answers_data.append({
                    'id': answer.id,
                    'text': answer.text
                    # is_correct ni yubormaymiz
                })
            
            questions_data.append({
                'id': question.id,
                'text': question.text,
                'order': question.order,
                'answers': answers_data
            })
        
        return JsonResponse({
            'success': True, 
            'questions': questions_data,
            'test_title': test.title,
            'time_limit': test.time_limit
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def submit_test(request):
    """Test natijasini yuborish - FAQAT STUDENT"""
    if not request.session.get('student_id'):
        return JsonResponse({'success': False, 'error': 'Ruxsat etilmagan!'})
    
    try:
        data = json.loads(request.body)
        student_id = request.session['student_id']
        test_id = data['test_id']
        answers = data['answers']  # {question_id: answer_id}
        
        student = get_object_or_404(Student, id=student_id)
        test = get_object_or_404(Test, id=test_id)
        
        # Ball hisoblash
        total_questions = test.questions.count()
        correct_answers = 0
        
        for question_id, answer_id in answers.items():
            try:
                question = Question.objects.get(id=question_id, test=test)
                correct_answer = question.answers.filter(is_correct=True).first()
                
                if correct_answer and str(correct_answer.id) == str(answer_id):
                    correct_answers += 1
            except (Question.DoesNotExist, Answer.DoesNotExist):
                continue
        
        score = (correct_answers / total_questions) * test.max_score if total_questions > 0 else 0
        
        # Natijani saqlash
        TestResult.objects.create(
            student=student,
            test=test,
            score=score,
            total_questions=total_questions,
            correct_answers=correct_answers,
            answers_data=answers
        )
        
        # Faollikni log qilish
        StudentActivity.objects.create(
            student=student,
            activity_type='test_complete',
            details=f'"{test.title}" testini {score:.1f} ball bilan yakunladi'
        )

        return JsonResponse({
            'success': True,
            'score': round(score, 1),
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'message': f'Test muvaffaqiyatli yakunlandi! Siz {score:.1f} ball to\'pladingiz.'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ==================== RANKING FUNCTIONS ====================
@csrf_exempt
@require_http_methods(["GET"])
def get_ranking_admin(request):
    """Reyting ro'yxatini olish - FAQAT ADMIN"""
    if not request.session.get('is_admin'):
        return JsonResponse({'success': False, 'error': 'Ruxsat etilmagan!'})
    
    try:
        # Faqat test topshirgan o'quvchilarni olish
        ranking = Student.objects.annotate(
            avg_score=Avg('testresult__score'),
            tests_taken=Count('testresult')
        ).filter(tests_taken__gt=0).order_by('-avg_score')
        
        ranking_data = []
        for student in ranking:
            ranking_data.append({
                'id': student.id,
                'ism': student.ism,
                'familya': student.familya,
                'avg_score': float(student.avg_score or 0),
                'tests_taken': student.tests_taken
            })
        
        return JsonResponse({'success': True, 'ranking': ranking_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["GET"])
def get_student_ranking(request):
    """O'quvchi reytingini olish - FAQAT STUDENT"""
    if not request.session.get('student_id'):
        return JsonResponse({'success': False, 'error': 'Ruxsat etilmagan!'})
    
    try:
        # Faqat test topshirgan o'quvchilarni olish
        ranking = Student.objects.annotate(
            avg_score=Avg('testresult__score'),
            tests_taken=Count('testresult'),
            max_score=Max('testresult__score')
        ).filter(tests_taken__gt=0).order_by('-max_score', '-avg_score')
        
        ranking_data = []
        for student in ranking:
            # Eng yuqori ballni olish
            max_score = TestResult.objects.filter(student=student).aggregate(max_score=Max('score'))['max_score'] or 0
            
            ranking_data.append({
                'id': student.id,
                'ism': student.ism,
                'familya': student.familya,
                'max_score': float(max_score),
                'avg_score': float(student.avg_score or 0),
                'tests_taken': student.tests_taken
            })
        
        # Joriy o'quvchining o'rni
        current_student_id = request.session['student_id']
        current_rank = None
        
        for i, student in enumerate(ranking_data, 1):
            if student['id'] == current_student_id:
                current_rank = i
                break
        
        return JsonResponse({
            'success': True, 
            'ranking': ranking_data,
            'current_rank': current_rank
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Xatolik handlerlari
def handler404(request, exception):
    return render(request, '404.html', status=404)

def handler500(request):
    return render(request, '500.html', status=500)