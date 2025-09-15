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
    PROGRESS_CHOICES = (
        ('COMPLETED', 'completed'),
        ('INPROGRESS', 'inprogress'),
    )
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name="maintenance_records")
    description = models.TextField(null=True, blank = True)
    maintaince_certificate = models.ImageField(upload_to="maintenance_certificates/")
    date_start = models.DateField(null = True)
    date_end = models.DateField(null = True)
    status = models.CharField(choices=PROGRESS_CHOICES,default = 'waiting')
    bay = models.ForeignKey(Bay, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.train.train_id} maintenance is {self.progress}'
    
class BrandingContract(models.Model):
    train = models.ManyToManyField(Train, related_name = "branding_contracts")
    branding_firm = models.CharField(max_length = 100, null = True, blank = True)
    impressions = models.DecimalField(max_digits = 15, decimal_places=2)
    start_date = models.DateField(null = True)
    end_date = models.DateField(null = True)
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