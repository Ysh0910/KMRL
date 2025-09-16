from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class CustomUserManager(BaseUserManager):
    #this function is used to create an user, default one is shitty
    def create_user(self, email, password = None):
        if(not email):
            raise ValueError('Email is Required!')
        #convert email to all lowercase
        normailzedEmail = self.normalize_email(email)
        user = self.model(email = normailzedEmail) #fetch the user model
            
        user.set_password(password)
        user.save()

        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('none', 'None'),
        ('admin', 'Admin'),
        ('maintenance_manager', 'Maintenance Manager'),
        ('stable_manager', 'Stable Manager'),
        ('Fitness_manager', 'Fitness Manager')
    )
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=20, null=False, blank=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    role = models.CharField(max_length = 50, choices=ROLE_CHOICES, default = 'none')
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'

    def get_name(self):
        return self.name
    
    def __str__(self):
        return self.email
    

class Train(models.Model):
    train_id = models.CharField(max_length = 20, unique = True, primary_key=True)
    train_name = models.CharField(max_length=50)

    def __str__(self):
        return self.train_id

class FitnessDepartment(models.Model):
    fitness_cerficate = models.ImageField(upload_to = 'fitness_certificates/')
    train = models.ForeignKey(Train, on_delete = models.CASCADE, related_name="fitness_records")
    signal = models.CharField(max_length=20,null = True)
    structural_integrity = models.CharField(max_length=20,null = True)
    braking = models.CharField(max_length=20,null = True)
    issue_date = models.CharField(max_length=20,null=True)
    expiry_date = models.CharField(max_length=20,null = True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.train.train_id} is {self.validy}'
    
class Bay(models.Model):
    bay_id = models.CharField(max_length = 20, unique=True)
    bay_name = models.CharField(max_length=50, null = True, blank = True)

    def __str__(self):
        return self.bay_id

class Maintenance(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name="maintenance_records")
    description = models.TextField(null=True, blank = True)
    maintaince_certificate = models.ImageField(upload_to="maintenance_certificates/")
    date_start = models.CharField(max_length=20,null = True)
    date_end = models.CharField(max_length = 20,null = True)
    status = models.CharField(max_length=100)
    parts_used = models.CharField(max_length = 100 ,null = True, blank = True)
    technician = models.CharField(max_length=50, null = True, blank = True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.train.train_id} maintenance is {self.progress}'
    
class BrandingContract(models.Model):
    train = models.ForeignKey(Train, default="", on_delete=models.CASCADE, related_name = "branding_contracts")
    branding_firm = models.CharField(max_length = 100, null = True, blank = True)
    impressions = models.DecimalField(max_digits = 15, decimal_places=2)
    start_date = models.CharField(max_length=20,null = True)
    end_date = models.CharField(max_length=20,null = True)
    description = models.TextField(null = True, blank = True)
    revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank = True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.branding_firm} is funding {self.train}'
    
class Stable(models.Model):
    stable_id = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.stable_id

class StableDepartment(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name="stable_records")
    stable = models.ForeignKey(Stable, on_delete=models.CASCADE)
    entry_time = models.DateTimeField(null = True)
    exit_time = models.DateTimeField(null = True)
    first_trip  = models.DateTimeField(null=True)
    kilometers_ran = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=0)
    recently_maintained = models.BooleanField(default = False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.train} was in stable {self.stable}'

class TestImage(models.Model):
    image = models.ImageField(upload_to = 'test_images/')


class Mileage(models.Model):
    train = models.ForeignKey(Train, on_delete = models.CASCADE, related_name = "milage_records")
    total_kilometers = models.DecimalField(null=True, max_digits=10, decimal_places=2)
    kilometers_ran_since_last_maintenance = models.DecimalField(null=True, max_digits=10, decimal_places=2)
    average_daily_kilometeres = models.DecimalField(null=True, max_digits=10, decimal_places=2)
    total_mileage_for_the_period = models.DecimalField(null=True, max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] 

class ModelChache(models.Model):
    train_id = models.ForeignKey(Train, on_delete = models.CASCADE,default = "", related_name = 'model_chache')
    fitness_certificates = models.CharField(max_length=20, null=True)
    job_cards = models.CharField(max_length=20, null=True)
    branding_priority = models.IntegerField(null=True)
    current_mileage = models.DecimalField(null=True, decimal_places=2, max_digits=16)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']