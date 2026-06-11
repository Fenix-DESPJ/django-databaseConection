# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
# servicios/models.py
from django.db import models

class Servicio(models.Model):
    idservicio = models.AutoField(db_column='idServicio', primary_key=True)
    nombreservicio = models.CharField(db_column='nombreServicio', max_length=60)
    duracion = models.IntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    tiposervicio = models.CharField(db_column='tipoServicio', max_length=60)

    class Meta:
        managed = False  # Django no creará la tabla, ya existe en MySQL
        db_table = 'servicio'

class Pago(models.Model):
    idpago = models.AutoField(db_column='idPago', primary_key=True)
    metodopago = models.CharField(db_column='metodoPago', max_length=35)
    montototal = models.DecimalField(db_column='montoTotal', max_digits=10, decimal_places=2)
    fechapago = models.DateTimeField(db_column='fechaPago')
    estadopago = models.CharField(db_column='estadoPago', max_length=20)
    codigofactura = models.CharField(db_column='codigoFactura', max_length=20)

    class Meta:
        managed = False
        db_table = 'pago'

class Cita(models.Model):
    idcita = models.AutoField(db_column='idCita', primary_key=True)
    # Ajusta los campos según los que tengas en tu base de datos real
    fecha = models.DateField()
    horainicio = models.TimeField(db_column='horaInicio')
    idserviciofk = models.ForeignKey(Servicio, on_delete=models.DO_NOTHING, db_column='idServicioFk')
    # ... otros campos que tenga tu tabla cita en MySQL ...

    class Meta:
        managed = False
        db_table = 'cita'