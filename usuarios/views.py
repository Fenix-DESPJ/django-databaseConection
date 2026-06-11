from django.shortcuts import render, redirect
from .models import Usuario, Rol

def registrarse(request):
    if request.method == 'POST':
        try:
            # Capturamos todos los campos necesarios
            nombre = request.POST.get('nombre')
            apellido = request.POST.get('apellido')
            
            # Buscamos el rol 3 (Cliente)
            rol_cliente = Rol.objects.get(idrol=3)

            # ... dentro de tu bloque try
            nuevo_usuario = Usuario.objects.create(
                cedula=request.POST.get('cedula'),
                nombre=f"{nombre} {apellido}",
                correo=request.POST.get('correo'),
                contrasena=request.POST.get('password'),
                numcelular=request.POST.get('telefono'),
                fechanacimiento=request.POST.get('fecha'), # Debe coincidir con el nombre de arriba
                idrolfk=rol_cliente
            )
            print("DEBUG: Usuario guardado exitosamente")
            return redirect('index')
        except Exception as e:
            # ESTO TE DIRÁ EL ERROR REAL DE LA BASE DE DATOS
            print(f"DEBUG: ERROR AL GUARDAR EN BD: {e}")
            return render(request, 'registrarse.html', {'error': str(e)})
    
    return render(request, 'registrarse.html')