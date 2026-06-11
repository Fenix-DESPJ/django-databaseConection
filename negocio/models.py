# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
# negocio/models.py
from django.db import models
from usuarios.models import Usuario

class Barbero(models.Model):
    idbarbero = models.AutoField(db_column='idBarbero', primary_key=True)
    idusuariofk = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='idUsuarioFk')
    especialidad = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'barbero'

class Agenda(models.Model):
    idagenda = models.AutoField(db_column='idAgenda', primary_key=True)
    idbarberofk = models.ForeignKey(Barbero, on_delete=models.DO_NOTHING, db_column='idBarberoFk')
    fecha = models.DateField()
    horainicio = models.TimeField(db_column='horaInicio')

    class Meta:
        managed = False
        db_table = 'agenda'