from rest_framework import serializers
from .models import Workout, Exercise, Profile, WeightLog, SleepLog, WorkoutTemplate, TemplateExercise

class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        # Estos son los campos que tu botón de Next.js enviará:
        # El nombre del ejercicio y el músculo (category)
        fields = ['id', 'name', 'category', 'created_at']
        read_only_fields = ['id', 'created_at']

class WorkoutSerializer(serializers.ModelSerializer):
    # Opcional: Esto mostrará el nombre del ejercicio en lugar de solo el ID
    exercise_name = serializers.ReadOnlyField(source='exercise.name')

    class Meta:
        model = Workout
        # Añadimos los nuevos campos que pusimos en el modelo
        fields = ['id', 'user', 'exercise', 'exercise_name', 'title', 'weight', 'unit', 'reps', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        # Agregamos los nuevos campos del Motor Nutricional a la lista
        fields = [
            'id', 'user', 'age', 'height', 'experience_level', 'gym_goal', 
            'is_onboarded', 'is_pro', 'gender', 'weight', 'activity_level', 
            'target_calories', 'target_protein', 'target_carbs', 'target_fat'
        ]
        read_only_fields = ['user', 'is_pro'] # Por seguridad, nadie puede cambiar el dueño del perfil

class WeightLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeightLog
        fields = ['id', 'user', 'weight', 'date']
        read_only_fields = ['user', 'date']

class SleepLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SleepLog
        fields = ['id', 'user', 'date', 'wake_time', 'no_screens', 'light_dinner', 'dark_room', 'supplements']
        read_only_fields = ['user', 'date']

class TemplateExerciseSerializer(serializers.ModelSerializer):
    exercise_name = serializers.ReadOnlyField(source='exercise.name')
    category = serializers.ReadOnlyField(source='exercise.category')

    class Meta:
        model = TemplateExercise
        fields = ['id', 'exercise', 'exercise_name', 'category', 'target_sets', 'target_reps', 'rest_time', 'order']

class WorkoutTemplateSerializer(serializers.ModelSerializer):
    # Esto le dice a Django: "Trae todos los ejercicios conectados a este template"
    exercises = TemplateExerciseSerializer(many=True, read_only=True)

    class Meta:
        model = WorkoutTemplate
        fields = ['id', 'user', 'name', 'created_at', 'exercises']