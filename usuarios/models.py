# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
# usuarios/models.py
from django.db import models

class Rol(models.Model):
    idrol = models.AutoField(db_column='idRol', primary_key=True)
    nombrerol = models.CharField(db_column='nombreRol', max_length=15)

    class Meta:
        managed = False
        db_table = 'rol'

class Usuario(models.Model):
    idusuario = models.AutoField(db_column='idUsuario', primary_key=True)
    cedula = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    correo = models.CharField(db_column='correoUsuario', max_length=50)
    contrasena = models.CharField(max_length=255)
    numcelular = models.CharField(db_column='numCelular', max_length=15)
    # AÑADE ESTA LÍNEA (ajusta el nombre del db_column si es diferente en tu BD):
    fechanacimiento = models.DateField(db_column='fechaNacimiento') 
    idrolfk = models.ForeignKey(Rol, on_delete=models.DO_NOTHING, db_column='idRolFk')

    class Meta:
        managed = False 
        db_table = 'usuario'

from django.db import models
from django.contrib.auth.models import User

# Extensión del usuario nativo para manejar roles
class PerfilUsuario(models.Model):
    ROLES = (
        ('administrador', 'Administrador'),
        ('barbero', 'Barbero'),
        ('cliente', 'Cliente'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_rol_display()}"

# Modelo para las Citas de la Barbería
class Cita(models.Model):
    ESTADOS = (
        ('pendiente', 'En espera'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    )
    
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='citas_solicitadas')
    barbero = models.ForeignKey(User, on_delete=models.CASCADE, related_name='citas_asignadas')
    servicio = models.CharField(max_length=100)
    precio = models.IntegerField()
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(max_length=15, choices=ESTADOS, default='pendiente')

    def __str__(self):
        return f"{self.hora} - {self.cliente.first_name} con {self.barbero.first_name}"