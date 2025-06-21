from django.db import models

# Create your models here.
# models.py

class Lawyer(models.Model):
    name = models.CharField(max_length=100)
    profile_image = models.ImageField(upload_to='profiles/')
    introduction = models.TextField()
    rating = models.FloatField(default=0.0)
    specialty = models.JSONField(default=list)
    firm = models.CharField(max_length=200)

class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lawyer = models.ForeignKey(Lawyer, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    detail = models.TextField()
    price = models.PositiveIntegerField()
    is_paid = models.BooleanField(default=False)
