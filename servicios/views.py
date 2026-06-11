from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def servicios(request):
    return render(request, 'servicios.html')

def servicios_ind(request):
    return render(request, 'servicios-ind.html')

def servicios_paq(request):
    return render(request, 'servicios-paq-1.html')

def servicios_paq_2(request):
    return render(request, 'servicios-paq-2.html')

def reservas(request):
    return render(request, 'reservas.html')

def agenda(request):
    return render(request, 'agenda.html')

def perfil(request):
    return render(request, 'perfil.html') # Aquí quitamos la coma y cerramos el paréntesis correctamente

def iniciar_sesion(request):
    return render(request, 'iniciarsesion.html')

def registrarse(request):
    return render(request, 'registrarse.html')