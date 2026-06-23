from django.db import models
from servicios.models import Servicio
from usuarios.models import Usuario
from servicios.models import Servicio, Pago
# Create your models here.

class Cita(models.Model):
    idCita = models.AutoField(db_column='idCita', primary_key=True)
    # Asegúrate de usar los nombres exactos de tu SQL
    idbarberofk = models.ForeignKey(Usuario, models.DO_NOTHING, db_column='idBarberoFk', related_name='citas_como_barbero', null=True, blank=True)
    idclientefk = models.ForeignKey(Usuario, models.DO_NOTHING, db_column='idClienteFk', related_name='citas_como_cliente', null=True, blank=True)
    idserviciofk = models.ForeignKey(Servicio, models.DO_NOTHING, db_column='idServicioFk', related_name='citas_modulo_reservas')
    idpagofk = models.ForeignKey(Pago, models.DO_NOTHING, db_column='idPagoFk', null=True, blank=True, related_name='citas')
    idagendafk = models.IntegerField(db_column='idAgendaFk', null=True, blank=True)
    fecha = models.DateField(db_column='fecha') # Añadir db_column
    horainicio = models.TimeField(db_column='horaInicio')
    observaciones = models.CharField(max_length=255, db_column='observaciones', null=True, blank=True)
    
    class Meta:
        managed = False
        db_table = 'cita'
    
    def __str__(self):
        return f"Cita {self.idCita} - Fecha: {self.fecha} - Hora: {self.horainicio}"   