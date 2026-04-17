import stripe
from django.conf import settings
from django.db import IntegrityError
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date
import re
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Exercise, Workout, WorkoutTemplate, TemplateExercise
import unicodedata  # <--- AGREGAR ESTA LÍNEA AQUÍ


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import Workout, Exercise, Profile, WeightLog, SleepLog, NutritionPlan
from .serializers import WorkoutSerializer, ExerciseSerializer, ProfileSerializer, WeightLogSerializer, WorkoutTemplateSerializer

User = get_user_model()

# --- VISTAS GENERALES ---

@api_view(['GET'])
@permission_classes([AllowAny])
def check_status(request):
    return Response({"message": "Backend de Django conectado con éxito"})

@api_view(['POST'])
@permission_classes([AllowAny])
def handle_register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')
    first_name = request.data.get('first_name', '')
    
    if not username or not password:
        return Response({"error": "El correo y la contraseña son obligatorios"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        User.objects.create_user(
            username=username, 
            password=password, 
            email=email, 
            first_name=first_name
        )
        return Response({"message": "¡Atleta creado con éxito!"}, status=status.HTTP_201_CREATED)
    except IntegrityError:
        return Response({"error": "Este correo ya está registrado. Por favor, inicia sesión."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# --- VISTAS DE ENTRENAMIENTOS Y EJERCICIOS ---

@api_view(['GET', 'POST'])
@permission_classes([AllowAny]) 
def handle_workouts(request):
    if request.method == 'GET':
        workouts = Workout.objects.all().order_by('-created_at')
        serializer = WorkoutSerializer(workouts, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        user_id = request.data.get('user')
        try:
            user_instance = User.objects.get(id=user_id)
            serializer = WorkoutSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=user_instance)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "Usuario inválido"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'DELETE'])
@permission_classes([AllowAny])
def workout_detail(request, pk):
    try:
        workout = Workout.objects.get(pk=pk)
    except Workout.DoesNotExist:
        return Response({"error": "No encontrado"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = WorkoutSerializer(workout, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        workout.delete()
        return Response({"message": "Entrenamiento borrado"}, status=status.HTTP_204_NO_CONTENT)
    
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def handle_exercises(request):
    if request.method == 'GET':
        exercises = Exercise.objects.all().order_by('category', 'name')
        serializer = ExerciseSerializer(exercises, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        user = User.objects.first() 
        serializer = ExerciseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user) 
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([AllowAny])
def exercise_detail(request, pk):
    try:
        exercise = Exercise.objects.get(pk=pk)
        exercise.delete()
        return Response({"message": "Ejercicio eliminado del catálogo"}, status=status.HTTP_204_NO_CONTENT)
    except Exercise.DoesNotExist:
        return Response({"error": "Ejercicio no encontrado"}, status=status.HTTP_404_NOT_FOUND)

# --- PERFIL Y PESO ---

@api_view(['GET', 'PUT'])
@permission_classes([AllowAny])
def handle_profile(request):
    user_id = request.GET.get('user_id') or request.data.get('user_id')
    if not user_id:
        return Response({"error": "Falta identificar al usuario (user_id)"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user_instance = User.objects.get(id=user_id)
        profile, created = Profile.objects.get_or_create(user=user_instance)
        if request.method == 'GET':
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)
        if request.method == 'PUT':
            serializer = ProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(is_onboarded=True)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def handle_weight_logs(request):
    user_id = request.GET.get('user_id') or request.data.get('user_id')
    if not user_id:
        return Response({"error": "Falta el user_id"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user_instance = User.objects.get(id=user_id)
        if request.method == 'GET':
            logs = WeightLog.objects.filter(user=user_instance).order_by('date')
            serializer = WeightLogSerializer(logs, many=True)
            return Response(serializer.data)
        if request.method == 'POST':
            serializer = WeightLogSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=user_instance)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_heatmap_data(request):
    user_id = request.GET.get('user_id')
    if not user_id:
        return Response({"error": "Falta el user_id"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from django.utils import timezone
        from datetime import timedelta
        
        # 1. Buscamos entrenamientos de los últimos 7 días
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_workouts = Workout.objects.filter(
            user_id=user_id,
            created_at__gte=seven_days_ago
        ).order_by('-created_at')

        # 2. Mapeo de fatiga por texto del título
        muscle_history = {}
        for w in recent_workouts:
            try:
                # Extrae "Pecho" de "Pecho: Press..."
                muscle = w.title.split(':')[0].strip()
                if muscle and muscle not in muscle_history:
                    muscle_history[muscle] = w.created_at
            except: continue

        heatmap_data = []
        now = timezone.now()
        # Grupos que manejas en tu EXERCISES_DATABASE de page.tsx
        muscles = ['Pecho', 'Triceps', 'Bicep', 'Espalda', 'Pierna', 'Hombro', 'Abdomen']

        for m in muscles:
            if m in muscle_history:
                hours = (now - muscle_history[m]).total_seconds() / 3600
                recovery = min(int((hours / 72) * 100), 100)
                status_text = 'Destruido' if hours < 24 else 'Recuperándose' if hours < 72 else 'Fresco'
                time_str = 'Hoy' if hours < 24 else 'Ayer' if hours < 48 else f'Hace {int(hours/24)} días'
            else:
                recovery, status_text, time_str = 100, 'Fresco', 'Sin registrar'

            heatmap_data.append({
                'muscle': m, 'recovery': recovery, 'status': status_text, 'lastTrained': time_str
            })

        return Response(sorted(heatmap_data, key=lambda x: x['recovery']), status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)



# --- STRIPE LOGIC ---
@api_view(['POST'])
@permission_classes([AllowAny])
def create_customer_portal(request):
    user_id = request.data.get('user_id')
    
    if not user_id:
        return Response({"error": "Falta el user_id"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        profile = Profile.objects.get(user_id=user_id)
        
        if not profile.stripe_customer_id:
            return Response({"error": "Este usuario no tiene un ID de cliente en Stripe"}, status=status.HTTP_400_BAD_REQUEST)

        # Le pedimos a Stripe que genere el link del portal
        portal_session = stripe.billing_portal.Session.create(
            customer=profile.stripe_customer_id,
            return_url=settings.FRONTEND_URL + '/perfil', # A dónde regresa cuando cierre el portal
        )
        
        return Response({'url': portal_session.url}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def create_checkout_session(request):
    try:
        user_id = request.data.get('user_id')
        plan_type = request.data.get('plan_type') # Aquí Next.js nos dice qué botón presionó
        
        if not user_id or not plan_type:
            return Response({"error": "Faltan datos para procesar el pago"}, status=status.HTTP_400_BAD_REQUEST)

        # Mapeamos la palabra que manda Next.js con el ID de Stripe en tu settings
        price_ids = {
            'Mensual': settings.FITMO_PRO_MENSUAL_PRICE_ID,
            'Semestral': settings.FITMO_PRO_SEMESTRAL_PRICE_ID,
            'Anual': settings.FITMO_PRO_ANUAL_PRICE_ID
        }

        # Elegimos el ID correcto
        selected_price_id = price_ids.get(plan_type)

        if not selected_price_id:
            return Response({"error": "El tipo de plan no es válido"}, status=status.HTTP_400_BAD_REQUEST)

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price': selected_price_id, 'quantity': 1}],
            mode='subscription',
            client_reference_id=str(user_id),
            success_url=settings.FRONTEND_URL + '/pro/exito?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=settings.FRONTEND_URL + '/pro',
        )
        return Response({'url': checkout_session.url}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        print("🔴 Error de Payload")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        print("🔴 Error de Firma (La clave en tu .env es vieja o está mal)")
        return HttpResponse(status=400)

    # 1. CUANDO UN ATLETA PAGA O MEJORA SU PLAN
    if event.type == 'checkout.session.completed':
        session = event.data.object
        user_id = session.client_reference_id
        stripe_customer_id = session.customer 
        
        if user_id:
            try:
                profile = Profile.objects.get(user_id=user_id)
                profile.is_pro = True
                
                if stripe_customer_id:
                    profile.stripe_customer_id = stripe_customer_id
                    
                profile.save()
                print(f"🟢 ¡ÉXITO TOTAL! Atleta con ID {user_id} ahora es PRO. Stripe ID: {stripe_customer_id}")
            except Profile.DoesNotExist:
                print(f"🟡 El pago pasó, pero no existe el Perfil para el usuario ID {user_id}.")
                return HttpResponse(status=404)

    # 2. CUANDO LA SUSCRIPCIÓN DE UN ATLETA SE CANCELA DEFINITIVAMENTE
    elif event.type == 'customer.subscription.deleted':
        subscription = event.data.object 
        stripe_customer_id = subscription.customer 

        try:
            profile = Profile.objects.get(stripe_customer_id=stripe_customer_id)
            
            # ¡Le quitamos el acceso Pro!
            profile.is_pro = False
            profile.save()
            
            print(f"🔴 Suscripción terminada. El usuario {profile.user.username} ahora es FREE.")
        except Profile.DoesNotExist:
            print("🟡 El webhook de cancelación llegó, pero no encontramos al atleta en la base de datos.")

    return HttpResponse(status=200)

@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    email = request.data.get('email')
    name = request.data.get('name', '')

    if not email:
        return Response({"error": "El correo es obligatorio"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 1. Buscamos si el usuario ya existe por su correo
        user = User.objects.filter(email=email).first()
        
        # 2. Si no existe, lo creamos desde cero
        if not user:
            user = User.objects.create(
                username=email, # Usamos el email como username
                email=email,
                first_name=name.split()[0] if name else ''
            )
            user.set_unusable_password()
            user.save()

        # 3. Nos aseguramos de que tenga su Perfil (esto no falla si ya lo tiene)
        Profile.objects.get_or_create(user=user)

        # 4. Generamos los tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'id': user.id,
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)

    except Exception as e:
        # ESTO IMPRIMIRÁ EL ERROR EXACTO EN TU TERMINAL SI ALGO FALLA
        print("🔴 Error en Google Login (Django):", str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@api_view(['PUT'])
def update_nutrition_profile(request):
    user_id = request.data.get('user_id')
    
    try:
        profile = Profile.objects.get(user_id=user_id)
        
        # Actualizamos los datos físicos
        profile.age = request.data.get('age', profile.age)
        profile.height = request.data.get('height', profile.height)
        profile.weight = request.data.get('weight', profile.weight)
        profile.gender = request.data.get('gender', profile.gender)
        profile.activity_level = request.data.get('activity_level', profile.activity_level)
        profile.gym_goal = request.data.get('goal', profile.gym_goal)
        
        # Guardamos los resultados del algoritmo
        profile.target_calories = request.data.get('target_calories')
        profile.target_protein = request.data.get('target_protein')
        profile.target_carbs = request.data.get('target_carbs')
        profile.target_fat = request.data.get('target_fat')
        
        profile.save()

        # 2. 🚀 NUEVO: Guardamos los macros en el modelo NutritionPlan
        # get_or_create es mágico: si no tiene plan, lo crea; si ya tiene, lo actualiza.
        nutrition_plan, created = NutritionPlan.objects.get_or_create(user_id=user_id)
        nutrition_plan.target_calories = request.data.get('target_calories')
        nutrition_plan.target_protein = request.data.get('target_protein')
        nutrition_plan.target_carbs = request.data.get('target_carbs')
        nutrition_plan.target_fat = request.data.get('target_fat')
        nutrition_plan.save()
        
        return Response({"message": "¡Dieta guardada con éxito en la base de datos!"}, status=status.HTTP_200_OK)
        
    except Profile.DoesNotExist:
        return Response({"error": "Perfil no encontrado"}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['POST'])
def save_sleep_log(request):
    user_id = request.data.get('user_id')
    
    try:
        # Actualiza el registro de hoy o crea uno nuevo
        sleep_log, created = SleepLog.objects.update_or_create(
            user_id=user_id,
            date=date.today(),
            defaults={
                'wake_time': request.data.get('wake_time', '06:30'),
                'no_screens': request.data.get('no_screens', False),
                'light_dinner': request.data.get('light_dinner', False),
                'dark_room': request.data.get('dark_room', False),
                'supplements': request.data.get('supplements', False),
            }
        )
        return Response({"message": "Registro de sueño actualizado correctamente"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
# Función auxiliar para quitar acentos (ej. "jalón" -> "jalon")
def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

# El catálogo base espejo de tu frontend
DEFAULT_CATALOG = {
    "Pecho": ["press inclinado", "press recto", "peck flys", "peckdeck", "press de banca", "press de pecho"],
    "Triceps": ["jalon con polea", "overhead", "press de triceps", "skullcrushers", "fondos", "extensiones"],
    "Bicep": ["curl mancuernas", "curl barra", "martillos", "curl predicador", "curl concentrado", "spider curl", "bicep"],
    "Espalda": ["remo", "pulldown", "pullover", "dominadas", "jalon al pecho"],
    "Pierna": ["sentadilla", "abductor", "desplantes", "curl de cuadricep", "femoral", "hip thrust", "prensa", "peso muerto"],
    "Abdomen": ["crunches", "twist ruso", "plancha", "elevaciones", "abdomen"],
    "Hombro": ["press militar", "laterales", "frontales", "elevaciones laterales"]
}

@api_view(['POST'])
def process_voice_workout(request):
    user_id = request.data.get('user_id')
    voice_text = request.data.get('text', '')
    
    # Normalizamos el texto (minúsculas y sin acentos)
    clean_voice_text = remove_accents(voice_text.lower())

    if not user_id or not clean_voice_text:
        return Response({"error": "Faltan datos"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 1. EXTRAER EL PESO
        weight_match = re.search(r'(\d+)\s*(kilo|kilos|kg)', clean_voice_text)
        weight = int(weight_match.group(1)) if weight_match else 0

        # 2. EXTRAER SERIES Y REPETICIONES
        sets_match = re.search(r'(\d+)\s*(series? de|por|x)\s*(\d+)', clean_voice_text)
        if sets_match:
            num_sets = int(sets_match.group(1))
            num_reps = int(sets_match.group(3))
            reps_string = ', '.join([str(num_reps) for _ in range(num_sets)])
        else:
            reps_match = re.search(r'(\d+)\s*(repeticion|repeticiones|reps)', clean_voice_text)
            reps_string = reps_match.group(1) if reps_match else "0"
        
        # 3. IDENTIFICAR EL EJERCICIO (VERSIÓN INTELIGENTE)
        identified_exercise = None
        identified_muscle = "General"

        # A) Recopilar todos los ejercicios posibles en una sola lista
        all_possible_exercises = []

        # Primero metemos TUS ejercicios personalizados (Tienen prioridad)
        user_exercises = Exercise.objects.filter(user_id=user_id)
        for custom_ex in user_exercises:
            all_possible_exercises.append({
                "name": custom_ex.name,
                "muscle": custom_ex.category,
                "clean_name": remove_accents(custom_ex.name.lower())
            })

        # Luego metemos los del catálogo por defecto de Fitmo
        for muscle, exercises in DEFAULT_CATALOG.items():
            for ex in exercises:
                all_possible_exercises.append({
                    "name": ex.title(),
                    "muscle": muscle,
                    "clean_name": remove_accents(ex.lower())
                })

        # REEMPLAZA EL BLOQUE DE BÚSQUEDA EN process_voice_workout
        
        # 1. Unificamos todo el conocimiento en una lista
        all_exercises = []
        
        # Agregamos los tuyos (con prioridad)
        for ce in Exercise.objects.filter(user_id=user_id):
            all_exercises.append({"name": ce.name, "muscle": ce.category})
        
        # Agregamos los de fábrica
        for m, exs in DEFAULT_CATALOG.items():
            for e in exs:
                all_exercises.append({"name": e, "muscle": m})

        # 2. EL FIX: Ordenamos por longitud de mayor a menor
        # Esto asegura que "Press de banca inclinado" se evalúe ANTES que "Press de banca"
        all_exercises.sort(key=lambda x: len(x["name"]), reverse=True)

        identified_exercise = "Ejercicio Desconocido"
        identified_muscle = "General"

        # 3. Buscamos la coincidencia
        for item in all_exercises:
            clean_item = remove_accents(item["name"].lower())
            if clean_item in clean_voice_text:
                identified_exercise = item["name"].title()
                identified_muscle = item["muscle"]
                break

        

        # Si de plano no encuentra nada
        if not identified_exercise:
            identified_exercise = "Ejercicio Desconocido"



        # 4. ARMAR TÍTULO
        full_title = f"{identified_muscle}: {identified_exercise} | {weight}kg | Reps: {reps_string}"

        # 5. GUARDAR EN LA DB
        Workout.objects.create(
            user_id=user_id,
            title=full_title,
            weight=weight
        )

        return Response({
            "message": "¡Entrenamiento registrado con voz!",
            "parsed_data": {
                "muscle": identified_muscle,
                "exercise": identified_exercise,
                "weight": weight,
                "reps": reps_string
            },
            "saved_title": full_title
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# --- 1. CRUD DE TEMPLATES ---
@api_view(['GET', 'POST'])
def handle_templates(request):
    user_id = request.query_params.get('user_id') or request.data.get('user_id')

    if request.method == 'GET':
        templates = WorkoutTemplate.objects.filter(user_id=user_id)
        serializer = WorkoutTemplateSerializer(templates, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        name = request.data.get('name')
        exercises_data = request.data.get('exercises', []) 

        template = WorkoutTemplate.objects.create(user_id=user_id, name=name)

        for idx, ex_data in enumerate(exercises_data):
            # MAGIA: Buscamos el ejercicio, si no existe, lo creamos al vuelo.
            exercise_obj, created = Exercise.objects.get_or_create(
                user_id=user_id,
                name=ex_data['name'],
                defaults={'category': ex_data['category']}
            )
            
            TemplateExercise.objects.create(
                template=template,
                exercise=exercise_obj,
                target_sets=ex_data.get('target_sets', 3),
                target_reps=ex_data.get('target_reps', "10"),
                rest_time=ex_data.get('rest_time', 90), # <--- AGREGAR ESTO
                order=idx
            )
        return Response({"message": "Template creado con éxito"}, status=status.HTTP_201_CREATED)
    

   

# --- 2. EL MOTOR DE PREDICCIÓN CONTEXTUAL ---
@api_view(['GET'])
def predict_next_workout(request):
    user_id = request.query_params.get('user_id')
    
    # Buscamos qué fue lo último que registró el usuario
    last_workout = Workout.objects.filter(user_id=user_id).order_by('-created_at').first()
    templates = WorkoutTemplate.objects.filter(user_id=user_id)
    
    if not templates.exists():
        return Response({"prediction": None, "reason": "Crea tu primer template para empezar a predecir."})

    if not last_workout:
        # Si es su primer día en la app, le sugerimos su primer template
        serializer = WorkoutTemplateSerializer(templates.first())
        return Response({"prediction": serializer.data, "reason": "¡Día 1! Empecemos con tu primera rutina."})

    # Extraemos qué músculo entrenó ayer (Ej: "Pecho: Press inclinado" -> "Pecho")
    last_muscle = "Desconocido"
    if ":" in last_workout.title:
        last_muscle = last_workout.title.split(":")[0].strip()

    # Buscamos un template que NO use las fibras musculares de ayer
    suggested_template = None
    for template in templates:
        muscles_in_template = [te.exercise.category for te in template.exercises.all()]
        if last_muscle not in muscles_in_template:
            suggested_template = template
            break

    # Si todo falla (ej. hace rutinas Full Body todos los días), sugerimos el primero
    if not suggested_template:
        suggested_template = templates.first()

    serializer = WorkoutTemplateSerializer(suggested_template)
    return Response({
        "prediction": serializer.data,
        "reason": f"Tu último entrenamiento fue de {last_muscle}. Hoy vamos a darle descanso a esas fibras."
    })

@api_view(['GET', 'PUT', 'DELETE'])
def template_detail(request, pk):
    template = get_object_or_404(WorkoutTemplate, pk=pk)

    if request.method == 'GET':
        serializer = WorkoutTemplateSerializer(template)
        return Response(serializer.data)

    elif request.method == 'PUT':
        # Actualizamos el nombre
        template.name = request.data.get('name', template.name)
        template.save()

        # Para hacerlo limpio: Borramos los ejercicios viejos de este template y creamos los nuevos
        template.exercises.all().delete()
        exercises_data = request.data.get('exercises', [])

        for idx, ex_data in enumerate(exercises_data):
            exercise_obj, created = Exercise.objects.get_or_create(
                user_id=template.user_id,
                name=ex_data['name'],
                defaults={'category': ex_data['category']}
            )
            TemplateExercise.objects.create(
                template=template,
                exercise=exercise_obj,
                target_sets=ex_data.get('target_sets', 3),
                target_reps=ex_data.get('target_reps', "10"),
                rest_time=ex_data.get('rest_time', 90), # <--- AGREGAR ESTO
                order=idx
            )
        return Response({"message": "Template actualizado"}, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        template.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_nutrition_plan(request):
    user_id = request.query_params.get('user_id')
    
    if not user_id:
        return Response({"error": "Falta el user_id"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Buscamos el plan que ya estás creando en update_nutrition_profile
        plan = NutritionPlan.objects.get(user_id=user_id)
        
        if plan.target_calories:
            return Response({
                "id": plan.id,
                "target_calories": plan.target_calories,
                "target_protein": plan.target_protein,
                "target_carbs": plan.target_carbs,
                "target_fat": plan.target_fat
            }, status=status.HTTP_200_OK)
        else:
            return Response({}, status=status.HTTP_200_OK)
            
    except NutritionPlan.DoesNotExist:
        # Si el usuario es nuevo y no tiene plan, regresamos vacío para que Next.js muestre la tarjeta
        return Response({}, status=status.HTTP_200_OK)