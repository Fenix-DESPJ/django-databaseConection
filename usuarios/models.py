# usuarios/models.py
from django.db import models
from django.contrib.auth.models import User

class Rol(models.Model):
    idrol = models.AutoField(db_column='idRol', primary_key=True)
    nombrerol = models.CharField(db_column='nombreRol', max_length=15)

    class Meta:
        managed = False
        db_table = 'rol'

    def __str__(self):
        return self.nombrerol


class Usuario(models.Model):
    idusuario = models.AutoField(db_column='idUsuario', primary_key=True)
    cedula = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    correo = models.CharField(db_column='correoUsuario', max_length=50)
    contrasena = models.CharField(max_length=255)
    numcelular = models.CharField(db_column='numCelular', max_length=15)
    fechanacimiento = models.DateField(db_column='fechaNacimiento') 
    idrolfk = models.ForeignKey(Rol, on_delete=models.DO_NOTHING, db_column='idRolFk')

    class Meta:
        managed = False 
        db_table = 'usuario'

    def __str__(self):
        return self.nombre


class Cliente(models.Model):
    idcliente = models.AutoField(db_column='idCliente', primary_key=True)
    idusuariofk = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='idUsuarioFk', related_name='perfil_cliente')

    class Meta:
        managed = False
        db_table = 'cliente'


class Servicio(models.Model):
    idservicio = models.AutoField(db_column='idServicio', primary_key=True)
    nombreservicio = models.CharField(db_column='nombreServicio', max_length=45)
    precioservicio = models.DecimalField(db_column='precio', max_length=10, max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'servicio'

    def __str__(self):
        return self.nombreservicio


class PerfilUsuario(models.Model):
    id = models.BigAutoField(primary_key=True)
    ROLES = (
        ('administrador', 'Administrador'),
        ('barbero', 'Barbero'),
        ('cliente', 'Cliente'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')
    telefono = models.CharField(max_length=20, blank=True, null=True)


class Cita(models.Model):
    idcita = models.AutoField(db_column='idCita', primary_key=True)
    idclientefk = models.ForeignKey(Cliente, on_delete=models.DO_NOTHING, db_column='idClienteFk')
    idbarberofk = models.ForeignKey('negocio.Barbero', on_delete=models.DO_NOTHING, db_column='idBarberoFk')
    idserviciofk = models.ForeignKey(Servicio, on_delete=models.DO_NOTHING, db_column='idServicioFk')
    idagendafk = models.ForeignKey('negocio.Agenda', on_delete=models.DO_NOTHING, db_column='idAgendaFk')
    observaciones = models.TextField(db_column='observaciones', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cita'