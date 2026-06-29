// --- VARIABLES GLOBALMENTE DECLARADAS PARA MODALES BOOTSTRAP ---
let pseModal, cardModal, successModal, reservationToast;

document.addEventListener("DOMContentLoaded", () => {
  // Inicialización del módulo si la vista de reservas está activa en el DOM
  if (document.getElementById("reservation-module-wrapper")) {
    inicializarModuloReservas();
  }
});

function inicializarModuloReservas() {
  // --- SELECTORES DEL DOM ---
  const formReservas = document.getElementById("formReservas");
  const calendarDays = document.getElementById("calendarDays");
  const currentMonthYear = document.getElementById("currentMonthYear");
  const prevMonth = document.getElementById("prevMonth");
  const nextMonth = document.getElementById("nextMonth");
  const hoursGrid = document.getElementById("hoursGrid");

  // Selectores de los elementos Select generados por Django
  const selectServicio = document.getElementById("servicio");
  const selectBarbero = document.getElementById("barbero");

  // Selectores para los Inputs Ocultos (Hidden) destinados al POST de Django
  const inputFecha = document.getElementById("input_fecha_seleccionada");
  const inputHora = document.getElementById("input_hora_seleccionada");
  const inputMetodoPago = document.getElementById("input_metodo_pago");

  // Selectores del Resumen de Reserva lateral derecho
  const summaryService = document.getElementById("summaryService");
  const summaryBarber = document.getElementById("summaryBarber");
  const summaryDate = document.getElementById("summaryDate");
  const summaryHour = document.getElementById("summaryHour");
  const summaryPayment = document.getElementById("summaryPayment");
  const selectedMethodDisplay = document.getElementById("selectedMethodDisplay");

  // Botón principal del flujo
  const btnReservar = document.getElementById("btnReservar");

  // --- ESTADO INTERNO DEL CLIENTE ---
  let estadoReserva = {
    fecha: "",
    hora: "",
    metodoPago: ""
  };

  let mesOffset = 0;

  // --- NUEVA LÓGICA: Auto-seleccionar servicio desde URL ---
  const urlParams = new URLSearchParams(window.location.search);
  const servicioId = urlParams.get('servicio_id');

  if (servicioId && selectServicio) {
    // Intentamos asignar el ID al select
    selectServicio.value = servicioId;
    
    // Verificamos si el valor existía (por si el ID en la URL no coincide con ninguno en el select)
    if (selectServicio.value === servicioId) {
        // Disparamos el evento para que se actualice el resumen y la UI
        selectServicio.dispatchEvent(new Event('change'));
    }
  }

  // --- INICIALIZACIÓN DE MODALES Y TOASTS (BOOTSTRAP) ---
  pseModal = new bootstrap.Modal(document.getElementById("pseModal"));
  cardModal = new bootstrap.Modal(document.getElementById("cardModal"));
  successModal = new bootstrap.Modal(document.getElementById("successModal"));
  
  const toastEl = document.getElementById("reservationToast");
  if (toastEl) {
    reservationToast = new bootstrap.Toast(toastEl, { delay: 3000 });
  }

  // --- ESCUCHADORES DE SELECTS (SINCRO CON EL RESUMEN) ---
  if (selectServicio) {
    actualizarTextoServicio();
    selectServicio.addEventListener("change", actualizarTextoServicio);
  }

  if (selectBarbero) {
    actualizarTextoBarbero();
    selectBarbero.addEventListener("change", actualizarTextoBarbero);
  }

  function actualizarTextoServicio() {
    if (summaryService && selectServicio) {
      const textoSeleccionado = selectServicio.options[selectServicio.selectedIndex].text;
      summaryService.textContent = selectServicio.value ? textoSeleccionado : "Selecciona un servicio";
    }
  }

  function actualizarTextoBarbero() {
    if (summaryBarber && selectBarbero) {
      const textoSeleccionado = selectBarbero.options[selectBarbero.selectedIndex].text;
      summaryBarber.textContent = selectBarbero.value ? textoSeleccionado : "Selecciona tu barbero";
    }
  }

  // --- ESCUCHA DEL DROPDOWN PERSONALIZADO DE MÉTODOS DE PAGO ---
  const paymentOptions = document.querySelectorAll(".payment-option");
  paymentOptions.forEach(option => {
    option.addEventListener("click", (e) => {
      e.preventDefault();
      const metodo = option.getAttribute("data-method");
      
      estadoReserva.metodoPago = metodo;
      if (inputMetodoPago) inputMetodoPago.value = metodo;

      if (selectedMethodDisplay) selectedMethodDisplay.textContent = metodo;
      if (summaryPayment) summaryPayment.textContent = metodo;
    });
  });

  // Validar cuando confirman dentro del modal de PSE o Tarjeta
  const btnPagarPSE = document.getElementById("btnPagarPSE");
  if (btnPagarPSE) {
    btnPagarPSE.addEventListener("click", () => {
      inputMetodoPago.value = "PSE";
      if (selectedMethodDisplay) selectedMethodDisplay.textContent = "PSE";
      if (summaryPayment) summaryPayment.textContent = "PSE";
      if (reservationToast) reservationToast.show();
    });
  }

  const btnPagarCard = document.getElementById("btnPagarCard");
  if (btnPagarCard) {
    btnPagarCard.addEventListener("click", () => {
      inputMetodoPago.value = "Tarjeta de Crédito";
      if (selectedMethodDisplay) selectedMethodDisplay.textContent = "Tarjeta de Crédito";
      if (summaryPayment) summaryPayment.textContent = "Tarjeta de Crédito";
      if (reservationToast) reservationToast.show();
    });
  }

  // --- RENDERIZACIÓN DINÁMICA DEL CALENDARIO ---
  function renderizarCalendario() {
    const fechaBase = new Date();
    fechaBase.setMonth(fechaBase.getMonth() + mesOffset);

    const nombreMes = fechaBase.toLocaleDateString("es-ES", {
      month: "long",
      year: "numeric",
    });
    
    if (currentMonthYear) {
      currentMonthYear.textContent = nombreMes.charAt(0).toUpperCase() + nombreMes.slice(1);
    }

    if (!calendarDays) return;
    calendarDays.innerHTML = "";

    let primerDia = new Date(fechaBase.getFullYear(), fechaBase.getMonth(), 1).getDay();
    const diasEnMes = new Date(fechaBase.getFullYear(), fechaBase.getMonth() + 1, 0).getDate();
    let offset = primerDia === 0 ? 6 : primerDia - 1;

    for (let i = 0; i < offset; i++) {
      const divVacio = document.createElement("div");
      divVacio.classList.add("day", "empty"); 
      calendarDays.appendChild(divVacio);
    }

    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    
    const fechaLimite = new Date();
    fechaLimite.setDate(hoy.getDate() + 30);
    fechaLimite.setHours(0, 0, 0, 0);

    const listadoHoras = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"];

    for (let dia = 1; dia <= diasEnMes; dia++) {
      const fechaIteradaObj = new Date(fechaBase.getFullYear(), fechaBase.getMonth(), dia);
      
      const horasDisponibles = listadoHoras.filter(hora => {
        const [h, m] = hora.split(":").map(Number);
        const horaCita = new Date(fechaIteradaObj);
        horaCita.setHours(h, m, 0, 0);
        
        const esHoy = fechaIteradaObj.toDateString() === hoy.toDateString();
        const unaHoraEnMs = 60 * 60 * 1000;
        
        return !(esHoy && (horaCita - new Date() < unaHoraEnMs));
      }).length;

      const btonDia = document.createElement("button");
      btonDia.type = "button";
      btonDia.classList.add("day"); 
      btonDia.textContent = dia;

      if (fechaIteradaObj < hoy || fechaIteradaObj > fechaLimite || horasDisponibles === 0) {
        btonDia.classList.add("disabled");
        btonDia.disabled = true;
      }

      const mesFormateado = String(fechaBase.getMonth() + 1).padStart(2, '0');
      const diaFormateado = String(dia).padStart(2, '0');
      const fechaIterada = `${fechaBase.getFullYear()}-${mesFormateado}-${diaFormateado}`;
      
      if (estadoReserva.fecha === fechaIterada) {
        btonDia.classList.add("selected");
      }

      if (!btonDia.disabled) {
        btonDia.addEventListener("click", () => {
          document.querySelectorAll(".day").forEach(b => b.classList.remove("selected"));
          btonDia.classList.add("selected");
          
          estadoReserva.fecha = fechaIterada;
          if (inputFecha) inputFecha.value = fechaIterada;
          if (summaryDate) summaryDate.textContent = fechaIterada;

          renderizarHoras();
        });
      }

      calendarDays.appendChild(btonDia);
    }
  }

  // --- RENDERIZACIÓN DE LAS HORAS EN LA GRILLA ---
  function renderizarHoras() {
    if (!hoursGrid) return;
    hoursGrid.innerHTML = "";

    const listadoHoras = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"];
    const ahora = new Date();
    const fechaSeleccionada = new Date(estadoReserva.fecha + "T00:00:00");
    const esHoy = fechaSeleccionada.toDateString() === ahora.toDateString();

    listadoHoras.forEach(hora => {
      const [h, m] = hora.split(":").map(Number);
      const horaCita = new Date(fechaSeleccionada);
      horaCita.setHours(h, m, 0, 0);

      const btonHora = document.createElement("button");
      btonHora.type = "button";
      btonHora.classList.add("hour-btn");
      btonHora.textContent = hora;

      if (esHoy && (horaCita - ahora < 3600000)) {
        btonHora.classList.add("disabled");
        btonHora.disabled = true;
      } else {
        if (estadoReserva.hora === hora) {
          btonHora.classList.add("selected");
        }

        btonHora.addEventListener("click", () => {
          document.querySelectorAll(".hour-btn").forEach(b => b.classList.remove("selected"));
          btonHora.classList.add("selected");
          
          estadoReserva.hora = hora;
          if (inputHora) inputHora.value = hora;
          if (summaryHour) summaryHour.textContent = hora;
        });
      }

      hoursGrid.appendChild(btonHora);
    });
  }

  // --- FLUJO DE CONTROL: BOTÓN FINAL DE RESERVA ---
  if (btnReservar) {
    btnReservar.addEventListener("click", () => {
      if (!selectServicio || !selectServicio.value) {
        alert("Por favor, selecciona un servicio.");
        return;
      }
      if (!selectBarbero || !selectBarbero.value) {
        alert("Por favor, selecciona un barbero de preferencia.");
        return;
      }
      if (!inputFecha || !inputFecha.value) {
        alert("Por favor, selecciona un día válido en el calendario.");
        return;
      }
      if (!inputHora || !inputHora.value) {
        alert("Por favor, selecciona un horario disponible.");
        return;
      }
      if (!inputMetodoPago || !inputMetodoPago.value) {
        alert("Por favor, selecciona tu método de pago.");
        return;
      }

      if (successModal) {
        successModal.show();
      }
    });
  }

  // Capturar el envío del Formulario Real desde el Modal de éxito
  const btnVerMisReservas = document.getElementById("btnVerMisReservas");
  if (btnVerMisReservas) {
    btnVerMisReservas.addEventListener("click", () => {
      successModal.hide();
      if (formReservas) {
        formReservas.submit(); // Dispara el POST nativo hacia Django
      }
    });
  }

  if (prevMonth) {
    prevMonth.addEventListener("click", () => { mesOffset--; renderizarCalendario(); });
  }
  if (nextMonth) {
    nextMonth.addEventListener("click", () => { mesOffset++; renderizarCalendario(); });
  }

  renderizarCalendario();
}

/* Estado Centralizado */
let modoActual = null; // 'editar', 'borrar', o null

function cambiarModo(nuevoModo) {
    console.log("Cambiando a modo:", nuevoModo);
  // Si el usuario presiona el mismo botón que ya está activo, cancelamos todo
    if (modoActual === nuevoModo) {
        desactivarModos();
        return;
    }

    // Si no, activamos el nuevo modo y desactivamos el anterior
    desactivarModos();
    modoActual = nuevoModo;

    const btnEditar = document.getElementById('btn-editar-toggle');
    const btnBorrar = document.querySelector('.btn-danger');
    const tarjetas = document.querySelectorAll('.card-precio');

    if (modoActual === 'editar') {
        btnEditar.innerText = "Cancelar Edición";
        tarjetas.forEach(c => c.classList.add('border-editar'));
    } 
    else if (modoActual === 'borrar') {
        btnBorrar.innerText = "Cancelar Borrado";
        tarjetas.forEach(c => {
            c.classList.add('border-borrar');
            c.onclick = function() {
                const id = this.getAttribute('data-id');
                if(confirm('¿Seguro que deseas eliminar este servicio?')) {
                    const url = document.querySelector('[data-url-eliminar]').dataset.urlEliminar;
                    window.location.href = url.replace('0', id);
                }
            };
        });
    }
}

function desactivarModos() {
    modoActual = null;
    document.getElementById('btn-editar-toggle').innerText = "Editar Servicio";
    document.querySelector('.btn-danger').innerText = "Borrar Servicio";
    
    document.querySelectorAll('.card-precio').forEach(c => {
        c.classList.remove('border-editar', 'border-borrar');
        c.onclick = null; // Esto es vital para borrar los clics de borrado
    });
}

// Para editar, necesitamos que al hacer clic la tarjeta siempre intente abrir el modal
// pero solo si estamos en modo editar.
function abrirModalEditar(id, nombre, precio, duracion, tipo) {
    // 1. Obtener referencia al modal y elementos
    const modal = document.getElementById('modalServicio');
    const form = document.getElementById('formServicio');
    const titulo = document.getElementById('modalServicioLabel');
    
    // 2. Cambiar título y acción del formulario
    titulo.innerText = "Editar Servicio: " + nombre;
    
    // Usamos el data-editar-base que ya tienes en el HTML (reemplazando el 0 por el id real)
    const urlBase = document.getElementById('url-data').getAttribute('data-editar-base');
    form.action = urlBase.replace('0', id);
    
    // 3. Llenar los campos del formulario
    form.querySelector('[name="nombreservicio"]').value = nombre;
    form.querySelector('[name="precio"]').value = precio;
    form.querySelector('[name="duracion"]').value = duracion;
    form.querySelector('[name="tiposervicio"]').value = tipo;
    
    // 4. Mostrar el modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

function prepararModalCrear() {
    const form = document.getElementById('formServicio');
    const titulo = document.getElementById('modalServicioLabel');
    
    titulo.innerText = "Nuevo Servicio";
    form.action = document.getElementById('url-data').getAttribute('data-crear');
    form.reset(); // Limpiar campos
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.card-precio').forEach(card => {
        card.addEventListener('click', function() {
            if (modoActual === 'editar') {
                const id = this.getAttribute('data-id');
                // Buscamos los datos en la tarjeta (asegúrate de tenerlos en data-atributos)
                const nombre = this.getAttribute('data-nombre');
                const precio = this.getAttribute('data-precio');
                const duracion = this.getAttribute('data-duracion');
                const tipo = this.getAttribute('data-tipo');
                
                abrirModalEditar(id, nombre, precio, duracion, tipo);
            }
        });
    });
});

/* js reportes admin */
document.addEventListener('DOMContentLoaded', function() {
    // 1. Verificamos que Chart esté cargado
    if (typeof Chart === 'undefined') {
        console.error("Chart.js no se ha cargado. Revisa tu etiqueta <script> en base.html");
        return;
    }

    const el = document.getElementById('datos-reporte');
    const canvas = document.getElementById('graficoIngresos');

    if (el && canvas) {
        try {
            const nombres = JSON.parse(el.dataset.nombres);
            const totales = JSON.parse(el.dataset.totales);

            const ctx = canvas.getContext('2d');
            
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: nombres,
                    datasets: [{
                        label: 'Ingresos ($)',
                        data: totales,
                        backgroundColor: '#ffc107',
                        borderRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, ticks: { color: '#ffffff' } },
                        x: { ticks: { color: '#ffffff' } }
                    }
                }
            });
        } catch (e) {
            console.error("Error al procesar los datos de la gráfica:", e);
        }
    } else {
        console.error("No se encontró el contenedor de datos o el canvas.");
    }
});


document.addEventListener("DOMContentLoaded", function() {
    // Buscamos las alertas de Django con la clase 'alert'
    const alerts = document.querySelectorAll('.alert');
        
    alerts.forEach(function(alert) {
        setTimeout(function() {
            // Validación segura: si Bootstrap JS está disponible, lo usa
            if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            } else {
                // Si no, lo desvanece con CSS puro para no romper nada
                alert.style.transition = "opacity 0.5s ease";
                alert.style.opacity = "0";
                setTimeout(() => alert.remove(), 500);
            }
        }, 3000); 
    });
});



document.querySelectorAll('.toggle-password').forEach(button => {
    button.addEventListener('click', function() {
        // Buscamos el input que está justo antes del contenedor del ojo
        const input = this.parentElement.querySelector('input');
        const icon = this.querySelector('i');
        
        if (input.type === 'password') {
            input.type = 'text';
            // Cambia el icono al ojo abierto
            icon.classList.remove('bi-eye-slash');
            icon.classList.add('bi-eye');
        } else {
            input.type = 'password';
            // Cambia el icono de vuelta al ojo cerrado
            icon.classList.remove('bi-eye');
            icon.classList.add('bi-eye-slash');
        }
    });
});
