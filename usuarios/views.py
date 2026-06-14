from django.shortcuts import render, redirect
from .models import Usuario, Rol

# Vista para la página principal (la que te daba el error 404)
def home(request):
    return render(request, 'index.html')  # Asegúrate de tener tu index.html

# Vista completa de registro
def registrarse(request):
    if request.method == 'POST':
        try:
            # 1. Capturar datos del POST
            nombre = request.POST.get('nombre')
            apellido = request.POST.get('apellido')
            cedula = request.POST.get('cedula')
            correo = request.POST.get('correo')
            password = request.POST.get('password')
            telefono = request.POST.get('telefono')
            fecha = request.POST.get('fecha')
            
            # 2. Buscar el Rol (ID 3 = Cliente)
            rol_cliente = Rol.objects.get(idrol=3)

            # 3. Crear el objeto Usuario
            # Usamos el nombre del campo tal cual lo definiste en models.py
            nuevo_usuario = Usuario.objects.create(
                cedula=cedula,
                nombre=f"{nombre} {apellido}",
                correo=correo,
                contrasena=password,  # Nota: En producción, recuerda usar make_password
                numcelular=telefono,
                fechanacimiento=fecha,
                idrolfk=rol_cliente
            )
            
            print("DEBUG: Usuario guardado exitosamente")
            return redirect('index') # Asegúrate de que esta URL exista en tus urls.py

        except Exception as e:
            # Esto imprimirá el error real en tu consola (terminal de VS Code)
            print(f"DEBUG: ERROR AL GUARDAR EN BD: {e}")
            return render(request, 'registrarse.html', {'error': f"Error al registrar: {e}"})
    
    # Si es GET, solo renderizamos el formulario
    return render(request, 'registrarse.html')