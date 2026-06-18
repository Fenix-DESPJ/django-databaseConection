from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages
from django.db import connection 
import random
from datetime import datetime

from servicios.models import Servicio, Pago
from usuarios.models import Usuario
from .models import Cita

def crear_reserva(request):
    # Verificación de seguridad: Asegurar que el usuario esté autenticado
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para realizar una reserva.")
        return redirect('login') 

    if request.method == 'POST':
        fecha_reserva = request.POST.get('fecha')
        hora_reserva = request.POST.get('hora')
        servicio_id = request.POST.get('servicio')
        barbero_id = request.POST.get('barbero')
        metodo_pago = request.POST.get('metodo_pago')
        
        if not all([fecha_reserva, hora_reserva, servicio_id, barbero_id, metodo_pago]):
            messages.error(request, "Por favor completa todos los campos del formulario.")
            return redirect('crear_reserva')
            
        try:
            # 1. Obtener el ID del usuario de la sesión activa
            # 1. Obtener el ID del usuario de la sesión activa
            user_sistema = request.user
            try:
                # SE CAMBIÓ 'correoUsuario' POR 'correo' QUE ES EL CAMPO REAL DE TU MODELO
                usuario_actual = Usuario.objects.get(correo=user_sistema.email)
                id_usuario_buscar = usuario_actual.idusuario  # Asegúrate de usarlo en minúscula según las opciones del error
            except (Usuario.DoesNotExist, AttributeError):
                id_usuario_buscar = user_sistema.id 

            # 2. CONSULTA DIRECTA A MYSQL: Obtener los IDs de las tablas intermedias
            with connection.cursor() as cursor:
                # Corregido campo a minúsculas 'idusuariofk' según el mapeo de Django
                cursor.execute("SELECT idcliente FROM cliente WHERE idusuariofk = %s", [id_usuario_buscar])
                fila_cliente = cursor.fetchone()
                
                # Corregido campo a minúsculas 'idusuariofk' y 'idbarbero'
                cursor.execute("SELECT idbarbero FROM barbero WHERE idusuariofk = %s", [barbero_id])
                fila_barbero = cursor.fetchone()

            # Mensaje de depuración por si vuelve a fallar (mira la consola de la terminal)
            print(f"--- DEBUG RESERVA --- ID Usuario Buscar: {id_usuario_buscar} | ID Barbero Recibido: {barbero_id} | Fila Barbero Encontrada: {fila_barbero}")

            if not fila_cliente:
                messages.error(request, f"Tu usuario (ID {id_usuario_buscar}) no posee un perfil de Cliente asociado.")
                return redirect('crear_reserva')
                
            if not fila_barbero:
                messages.error(request, f"El barbero seleccionado (ID Usuario: {barbero_id}) no está registrado formalmente en la tabla de barberos.")
                return redirect('crear_reserva')

            id_cliente_real = fila_cliente[0]
            id_barbero_real = fila_barbero[0]

            # 3. Obtener el servicio para capturar su precio actual
            servicio = Servicio.objects.get(idservicio=servicio_id)
            
            # 4. Registrar el Pago en la base de datos
            estado_pago = "PENDIENTE" if metodo_pago == "Efectivo" else "PAGADO"
            codigo_factura = f"FAC{random.randint(10000, 99999)}"
            
            # SE CORRIGIERON LOS CAMPOS A MINÚSCULAS: metodopago, montototal, fechapago, estadopago, codigofactura
            nuevo_pago = Pago(
                metodopago=metodo_pago,
                montototal=servicio.precio,
                fechapago=timezone.now(),
                estadopago=estado_pago,
                codigofactura=codigo_factura
            )
            nuevo_pago.save()
            
            # 5. Formatear la hora al estándar TimeField
            hora_objeto = datetime.strptime(hora_reserva, '%H:%M').time()
            
            # 6. Crear la Cita (Campos corregidos a minúsculas según tu estándar)
            nueva_cita = Cita(
                fecha=fecha_reserva,
                horainicio=hora_objeto,       # Antes: horaInicio
                idserviciofk=servicio,        # Antes: idServicioFk
                idpagofk=nuevo_pago,          # Antes: idPagoFk
                observaciones="Reserva realizada desde la web"
            )
            nueva_cita.idclientefk_id = id_cliente_real  # Antes: idClienteFk_id
            nueva_cita.idbarberofk_id = id_barbero_real  # Antes: idBarberoFk_id
            nueva_cita.save()
            
            messages.success(request, "¡Cita reservada y guardada exitosamente!")
            return redirect('crear_reserva')
            
        except Exception as e:
            messages.error(request, f"Hubo un problema al guardar la reserva: {e}")
            return redirect('crear_reserva')
    
    # =========================================================================
    # --- MÉTODO GET: Consultas SQL limpias mediante cursor directo ---
    # =========================================================================
    try:
        with connection.cursor() as cursor:
            # Traer servicios usando el nombre exacto de la tabla física
            cursor.execute("SELECT idServicio, nombreServicio, precio FROM servicio")
            columnas_serv = [col[0] for col in cursor.description]
            todos_los_servicios = [dict(zip(columnas_serv, fila)) for fila in cursor.fetchall()]

            # Traer barberos (usuarios con idRolFk = 2) filtrando directamente por tu BD
            cursor.execute("SELECT idUsuario, nombre FROM usuario WHERE idRolFk = 2")
            columnas_barb = [col[0] for col in cursor.description]
            todos_los_barberos = [dict(zip(columnas_barb, fila)) for fila in cursor.fetchall()]
            
    except Exception as e:
        todos_los_servicios = []
        todos_los_barberos = []
        print(f"Error al ejecutar consulta SQL nativa en el GET: {e}")
    
    contexto = {
        'servicios': todos_los_servicios,
        'barberos': todos_los_barberos
    }
    
    return render(request, 'reservas.html', contexto)