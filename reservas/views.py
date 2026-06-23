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
            user_sistema = request.user
            try:
                usuario_actual = Usuario.objects.get(correo=user_sistema.email)
                id_usuario_buscar = usuario_actual.idusuario
            except (Usuario.DoesNotExist, AttributeError):
                id_usuario_buscar = user_sistema.id 

            # 2. CONSULTA DIRECTA A MYSQL: Obtener los IDs de las tablas intermedias
            with connection.cursor() as cursor:
                cursor.execute("SELECT idcliente FROM cliente WHERE idusuariofk = %s", [id_usuario_buscar])
                fila_cliente = cursor.fetchone()
                
                cursor.execute("SELECT idbarbero FROM barbero WHERE idusuariofk = %s", [barbero_id])
                fila_barbero = cursor.fetchone()

            print(f"--- DEBUG RESERVA --- ID Usuario Buscar: {id_usuario_buscar} | ID Barbero Recibido: {barbero_id} | Fila Barbero Encontrada: {fila_barbero}")

            if not fila_cliente:
                messages.error(request, f"Tu usuario (ID {id_usuario_buscar}) no posee un perfil de Cliente asociado.")
                return redirect('crear_reserva')
                
            if not fila_barbero:
                messages.error(request, f"El barbero seleccionado (ID Usuario: {barbero_id}) no está registrado formalmente.")
                return redirect('crear_reserva')

            id_cliente_real = fila_cliente[0]
            id_barbero_real = fila_barbero[0]

            # 3. Obtener el servicio para capturar su precio actual
            servicio = Servicio.objects.get(idservicio=servicio_id)
            
            # 4. Registrar el Pago en la base de datos
            estado_pago = "PENDIENTE" if metodo_pago == "Efectivo" else "PAGADO"
            codigo_factura = f"FAC{random.randint(10000, 99999)}"
            
            nuevo_pago = Pago(
                metodopago=metodo_pago,
                montototal=servicio.precioservicio,  # Corregido a precioservicio según error anterior
                fechapago=timezone.now(),
                estadopago=estado_pago,
                codigofactura=codigo_factura
            )
            nuevo_pago.save()
            
            # 5. Formatear la hora al estándar TimeField
            hora_objeto = datetime.strptime(hora_reserva, '%H:%M').time()

            # =========================================================================
            # ¡EL CAMBIO CLAVE!: INSERTAR LA AGENDA MEDIANTE CURSOR Y CAPTURAR SU ID
            # =========================================================================
            with connection.cursor() as cursor:
                # Insertamos el bloque de tiempo en la tabla física 'agenda'
                cursor.execute(
                    "INSERT INTO agenda (idBarberoFk, fecha, horaInicio) VALUES (%s, %s, %s)",
                    [id_barbero_real, fecha_reserva, hora_objeto]
                )
                # MySQL nos devuelve el ID numérico autoincremental exacto que se acaba de generar
                cursor.execute("SELECT LAST_INSERT_ID()")
                id_agenda_creada = cursor.fetchone()[0]

            # =========================================================================
            # 6. Crear la Cita (Asignándole la agenda real)
            # =========================================================================
            nueva_cita = Cita(
                fecha=fecha_reserva,
                horainicio=hora_objeto,
                idserviciofk=servicio,
                idpagofk=nuevo_pago,
                observaciones="Reserva realizada desde la web"
            )
            nueva_cita.idclientefk_id = id_cliente_real
            nueva_cita.idbarberofk_id = id_barbero_real
            nueva_cita.idagendafk_id = id_agenda_creada  # <-- Clavamos el ID autoincremental de la agenda
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
        # 1. Traemos todos los servicios directamente usando su modelo de Django
        todos_los_servicios = Servicio.objects.all()
        print(f"--- DEBUG GET --- Servicios cargados con éxito: {todos_los_servicios.count()}")
        
        # 2. Traemos los usuarios que tengan asignado el rol de barbero
        # Como en tu modelo 'Usuario' el campo es idrolfk, filtramos por su ID (Rol 2 = Barbero)
        todos_los_barberos = Usuario.objects.filter(idrolfk=2)
        print(f"--- DEBUG GET --- Barberos (Rol 2) cargados: {todos_los_barberos.count()}")
            
    except Exception as e:
        todos_los_servicios = []
        todos_los_barberos = []
        print(f"❌ Error crítico al cargar los datos desde Django: {e}")
    
    contexto = {
        'servicios': todos_los_servicios,
        'barberos': todos_los_barberos
    }
    
    return render(request, 'reservas.html', contexto)