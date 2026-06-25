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
    console.log("Clic detectado en modo:", modoActual);
    if (modoActual !== 'editar') return;
    console.log("Abriendo modal para ID:", id);
    // Solo permitimos editar si estamos en el modo correcto

    const form = document.querySelector('.modal-barberia');
    const urlBase = document.getElementById('url-data').dataset.editarBase;
    
    form.action = urlBase.replace('0', id);
    document.querySelector('input[name="nombreservicio"]').value = nombre;
    document.querySelector('input[name="precio"]').value = precio;
    document.querySelector('input[name="duracion"]').value = duracion;
    document.querySelector('select[name="tiposervicio"]').value = tipo;
    
    new bootstrap.Modal(document.getElementById('modalServicio')).show();
}

function prepararModalCrear() {
    desactivarModos(); // Limpiamos cualquier modo antes de crear
    const form = document.querySelector('.modal-barberia');
    form.action = document.getElementById('url-data').dataset.crear;
    form.reset();
    document.getElementById('modalServicioLabel').innerText = "Nuevo Servicio";
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