from django.db import models

# Test simple model
class TestModel(models.Model):
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nombre
