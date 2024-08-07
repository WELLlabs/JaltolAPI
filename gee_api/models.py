# models.py

from django.db import models

class State(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class District(models.Model):
    name = models.CharField(max_length=255)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class SubDistrict(models.Model):
    name = models.CharField(max_length=255)
    district = models.ForeignKey(District, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Village(models.Model):
    name = models.CharField(max_length=255)
    subdistrict = models.ForeignKey(SubDistrict, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
