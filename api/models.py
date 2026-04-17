from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    pass

# --- NUEVO MODELO: El Catálogo ---
class Exercise(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50) # Aquí guardaremos el "Músculo"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.category})"

# --- TU MODELO ACTUALIZADO ---
class Workout(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Relacionamos el entrenamiento con un ejercicio del catálogo
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, null=True) 
    title = models.CharField(max_length=255) 
    weight = models.FloatField(default=0) # Para que guardes tus kilos
    reps = models.CharField(max_length=100, default="0") # Cambiado de IntegerField a CharField
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Profile(models.Model):
    # Opciones predefinidas para tu modelo de negocio
    EXPERIENCE_CHOICES = [
        ('principiante', 'Principiante'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
    ]
    
    GOAL_CHOICES = [
        ('masa_muscular', 'Aumento de masa muscular'),
        ('perdida_grasa', 'Pérdida de grasa'),
        ('fuerza', 'Aumento de fuerza'),
        ('recomposicion', 'Recomposición corporal'),
    ]
    # 1. Datos físicos base (agregamos los que faltaban)
    gender = models.CharField(max_length=1, choices=[('M', 'Hombre'), ('F', 'Mujer')], default='M')
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    activity_level = models.FloatField(default=1.55) # El multiplicador
    
    # 2. Las metas calculadas por el algoritmo
    target_calories = models.IntegerField(null=True, blank=True)
    target_protein = models.IntegerField(null=True, blank=True)
    target_carbs = models.IntegerField(null=True, blank=True)
    target_fat = models.IntegerField(null=True, blank=True)

    # OneToOneField significa que 1 Usuario solo puede tener 1 Perfil
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.IntegerField(null=True, blank=True)
    height = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True) # Ej. 1.76
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='principiante')
    gym_goal = models.CharField(max_length=20, choices=GOAL_CHOICES, default='masa_muscular')
    
    # Campo booleano para saber si el usuario ya pasó por la pantalla de Onboarding
    is_onboarded = models.BooleanField(default=False)
    is_pro = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
            return f"Perfil de {self.user.username} - {'PRO' if self.is_pro else 'FREE'}"


    

class WeightLog(models.Model):
    # ForeignKey significa que 1 Usuario puede tener MUCHOS registros de peso (para la gráfica)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weight_logs')
    weight = models.DecimalField(max_digits=5, decimal_places=2) # Ej. 73.00
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.weight}kg - {self.user.username} ({self.date.strftime('%Y-%m-%d')})"
    
    # Agrégalo al final de api/models.py

class SleepLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    wake_time = models.CharField(max_length=10, default="06:30")
    
    # Checklist de Higiene del Sueño
    no_screens = models.BooleanField(default=False)
    light_dinner = models.BooleanField(default=False)
    dark_room = models.BooleanField(default=False)
    supplements = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"Sueño de {self.user.username} - {self.date}"
    
# --- NUEVOS MODELOS: Templates de Entrenamiento ---

class WorkoutTemplate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='templates')
    name = models.CharField(max_length=100) # Ej: "Día de Empuje (Pecho y Tríceps)"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"

class TemplateExercise(models.Model):
    template = models.ForeignKey(WorkoutTemplate, on_delete=models.CASCADE, related_name='exercises')
    # Lo enlazamos a tu catálogo de ejercicios existente
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE) 
    
    # Valores objetivo que el usuario planea hacer
    target_sets = models.IntegerField(default=3)
    target_reps = models.CharField(max_length=50, default="10") 
    rest_time = models.IntegerField(default=90)
    order = models.IntegerField(default=0) # Para que los ejercicios salgan en el orden que él decida

    class Meta:
        ordering = ['order'] # Django siempre los ordenará por este campo

    def __str__(self):
        return f"{self.exercise.name} en {self.template.name}"
    
class NutritionPlan(models.Model):
    # Conectamos el plan directamente al usuario
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='nutrition_plan')
    
    # Macros
    target_calories = models.IntegerField(null=True, blank=True)
    target_protein = models.IntegerField(null=True, blank=True)
    target_carbs = models.IntegerField(null=True, blank=True)
    target_fat = models.IntegerField(null=True, blank=True)
    
    # Timestamps para saber cuándo se actualizó la dieta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Plan de nutrición de {self.user.username}"