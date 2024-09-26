# gee_api/models.py

from django.db import models

class State(models.Model):
    """
    Model representing a State.
    """
    name: str = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name


class District(models.Model):
    """
    Model representing a District belonging to a specific State.
    """
    name: str = models.CharField(max_length=100)
    state: State = models.ForeignKey(State, related_name='districts', on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name


class SubDistrict(models.Model):
    """
    Model representing a SubDistrict belonging to a specific District.
    """
    name: str = models.CharField(max_length=100)
    district: District = models.ForeignKey(District, related_name='subdistricts', on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name


class Village(models.Model):
    """
    Model representing a Village belonging to a specific SubDistrict.
    """
    name: str = models.CharField(max_length=100)
    subdistrict: SubDistrict = models.ForeignKey(SubDistrict, related_name='villages', on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name
