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
    foto_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True, db_column='foto_perfil')
    class Meta:
        managed = False 
        db_table = 'usuario'

    def __str__(self):
        return self.nombre


class Cliente(models.Model):
    idcliente = models.AutoField(db_column='idCliente', primary_key=True)
    idusuariofk = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='idUsuarioFk', related_name='perfil_cliente')
    direccion = models.CharField(max_length=100, blank=True, null=True)
    fecharegistro = models.DateField(db_column='fechaRegistro', blank=True, null=True)
    contactoemergencia = models.CharField(db_column='contactoEmergencia', max_length=100)

    class Meta:
        managed = False
        db_table = 'cliente'
        

class Pago(models.Model):
    """
    Mapea la tabla `pago`, que ya existía en la base de datos pero no estaba
    expuesta en el ORM. Aquí es donde vive el método de pago elegido por el
    cliente (Efectivo, PSE, Tarjeta...). No se hace ninguna validación
    bancaria real: solo se registra la elección del usuario.
    """
    METODO_EFECTIVO = 'Efectivo'
    METODO_PSE = 'PSE'
    METODO_TARJETA = 'Tarjeta'

    METODO_PAGO_CHOICES = (
        (METODO_EFECTIVO, 'Efectivo'),
        (METODO_PSE, 'PSE'),
        (METODO_TARJETA, 'Tarjeta de Crédito/Débito'),
    )

    ESTADO_PAGADO = 'PAGADO'
    ESTADO_PENDIENTE = 'PENDIENTE'
    ESTADO_CANCELADO = 'CANCELADO'

    ESTADO_PAGO_CHOICES = (
        (ESTADO_PAGADO, 'Pagado'),
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_CANCELADO, 'Cancelado'),
    )

    idpago = models.AutoField(db_column='idPago', primary_key=True)
    metodopago = models.CharField(
        db_column='metodoPago', max_length=35,
        choices=METODO_PAGO_CHOICES, default=METODO_EFECTIVO
    )
    montototal = models.DecimalField(
        db_column='montoTotal', max_digits=10, decimal_places=2,
        null=True, blank=True
    )
    fechapago = models.DateTimeField(db_column='fechaPago', null=True, blank=True)
    estadopago = models.CharField(
        db_column='estadoPago', max_length=15,
        choices=ESTADO_PAGO_CHOICES, default=ESTADO_PENDIENTE,
        null=True, blank=True
    )
    codigofactura = models.CharField(db_column='codigoFactura', max_length=20, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pago'

    def __str__(self):
        return f"{self.metodopago} - {self.estadopago}"


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
    idpagofk = models.ForeignKey(
        Pago, on_delete=models.DO_NOTHING, db_column='idPagoFk',
        null=True, blank=True, related_name='citas'
    )
    observaciones = models.TextField(db_column='observaciones', blank=True, null=True)
    calificacion_omitida = models.BooleanField(db_column='calificacionOmitida', default=False)

    class Meta:
        managed = False
        db_table = 'cita'

    @property
    def esta_completada(self):
        """
        No existe una columna `estado` en la tabla `cita`; el estado de
        'Completada' se sigue infiriendo del texto de `observaciones`,
        igual que ya hacía la vista `completar_cita`. Se centraliza aquí
        para no repetir el mismo `in` en todas partes.
        """
        return bool(self.observaciones) and 'Completado' in self.observaciones

class Notificacion(models.Model):
    idnotificacion = models.AutoField(primary_key=True)
    idusuariofk = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='idUsuarioFk',
        related_name='notificaciones'
    )
    # Tipos usados: 'reserva_creada' (cliente), 'nueva_cita' (barbero), 'cita_confirmada' (admin)
    tipo = models.CharField(max_length=30, default='info')
    mensaje = models.CharField(max_length=255)
    leida = models.BooleanField(default=False)
    fechacreacion = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        db_table = 'notificacion'
        ordering = ['-fechacreacion']
 
    def __str__(self):
        return f"[{self.tipo}] {self.mensaje[:40]}"
    
class Calificacion(models.Model):
    idcalificacion = models.AutoField(primary_key=True)

    # OneToOne: garantiza automáticamente "una calificación por cita"
    idcitafk = models.OneToOneField(
        'Cita',
        on_delete=models.CASCADE,
        db_column='idCitaFk',
        related_name='calificacion'   # permite: cita.calificacion / Cita.objects.filter(calificacion__isnull=True)
    )
    idclientefk = models.ForeignKey(
        'Cliente',
        on_delete=models.CASCADE,
        db_column='idClienteFk',
        related_name='calificaciones'
    )
    calificacion = models.PositiveSmallIntegerField(
        choices=[(i, f"{i} estrella{'s' if i > 1 else ''}") for i in range(1, 6)]
    )
    comentario = models.TextField(blank=True, null=True)  # 100% opcional
    fechacreacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'calificacion'
        ordering = ['-fechacreacion']

    def __str__(self):
        return f"{self.calificacion}★ - Cita #{self.idcitafk_id}"