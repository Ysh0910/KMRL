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
    

