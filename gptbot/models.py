# gptbot/models.py
from django.db import models

class Embedding(models.Model):
    text = models.TextField()
    embedding = models.TextField()  # JSON 문자열로 저장

    def __str__(self):
        return self.text[:30]
