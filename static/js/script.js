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
    // Inicializar texto del resumen con la opción por defecto elegida o vacía
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
      
      // Persistir valor en el estado de JS y en el input oculto de Django
      estadoReserva.metodoPago = metodo;
      if (inputMetodoPago) inputMetodoPago.value = metodo;

      // Actualizar los textos informativos en pantalla
      if (selectedMethodDisplay) selectedMethodDisplay.textContent = metodo;
      if (summaryPayment) summaryPayment.textContent = metodo;
    });
  });

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

    // Lista de horas para validar disponibilidad
    const listadoHoras = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"];

    for (let dia = 1; dia <= diasEnMes; dia++) {
      const fechaIteradaObj = new Date(fechaBase.getFullYear(), fechaBase.getMonth(), dia);
      
      // Calcular si hay al menos una hora disponible en este día
      const horasDisponibles = listadoHoras.filter(hora => {
        const [h, m] = hora.split(":").map(Number);
        const horaCita = new Date(fechaIteradaObj);
        horaCita.setHours(h, m, 0, 0);
        
        const esHoy = fechaIteradaObj.toDateString() === hoy.toDateString();
        const unaHoraEnMs = 60 * 60 * 1000;
        
        // La hora es válida si no es hoy, O si es hoy y falta más de 1 hora
        return !(esHoy && (horaCita - new Date() < unaHoraEnMs));
      }).length;

      const btonDia = document.createElement("button");
      btonDia.type = "button";
      btonDia.classList.add("day"); 
      btonDia.textContent = dia;

      // Inhabilitar si es pasado, muy lejano o NO hay horas disponibles
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
    
    // Obtenemos la hora actual (23 de junio, 2026, 16:26)
    const ahora = new Date();
    
    // Convertimos la fecha seleccionada en el estado a objeto Date
    // Asumimos que estadoReserva.fecha viene como "YYYY-MM-DD"
    const fechaSeleccionada = new Date(estadoReserva.fecha + "T00:00:00");
    
    // Verificamos si la fecha seleccionada es hoy
    const esHoy = fechaSeleccionada.toDateString() === ahora.toDateString();

    listadoHoras.forEach(hora => {
      const [h, m] = hora.split(":").map(Number);
      const horaCita = new Date(fechaSeleccionada);
      horaCita.setHours(h, m, 0, 0);

      const btonHora = document.createElement("button");
      btonHora.type = "button";
      btonHora.classList.add("hour-btn");
      btonHora.textContent = hora;

      // Lógica de restricción: 1 hora de antelación (3600000 ms)
      if (esHoy && (horaCita - ahora < 3600000)) {
        btonHora.classList.add("disabled");
        btonHora.disabled = true;
      } else {
        // Si el botón está disponible, aplicamos la lógica de selección normal
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

  // --- REACCIONES DE BOTONES DE ACCIÓN EN LOS PASOS DE PAGO ---
  const btnPagarPSE = document.getElementById("btnPagarPSE");
  if (btnPagarPSE) {
    btnPagarPSE.addEventListener("click", () => {
      if (reservationToast) reservationToast.show();
    });
  }

  const btnPagarCard = document.getElementById("btnPagarCard");
  if (btnPagarCard) {
    btnPagarCard.addEventListener("click", () => {
      if (reservationToast) reservationToast.show();
    });
  }

  // --- FLUJO DE CONTROL: BOTÓN FINAL DE RESERVA ---
  if (btnReservar) {
    btnReservar.addEventListener("click", () => {
      // Validaciones lógicas obligatorias de Inputs
      if (!selectServicio || !selectServicio.value) {
        alert("Por favor, selecciona un servicio.");
        return;
      }
      if (!selectBarbero || !selectBarbero.value) {
        alert("Por favor, selecciona un barbero de preferencia.");
        return;
      }
      if (!estadoReserva.fecha) {
        alert("Por favor, selecciona un día válido en el calendario.");
        return;
      }
      if (!estadoReserva.hora) {
        alert("Por favor, selecciona un horario disponible.");
        return;
      }
      if (!estadoReserva.metodoPago) {
        alert("Por favor, selecciona tu método de pago.");
        return;
      }

      // Si todo es válido, abrimos el modal de confirmación final
      if (successModal) {
        successModal.show();
      }
    });
  }

  // Capturar el envío del Formulario Real cuando el usuario ve el éxito completo
  const btnVerMisReservas = document.getElementById("btnVerMisReservas");
  if (btnVerMisReservas) {
    btnVerMisReservas.addEventListener("click", () => {
      successModal.hide();
      if (formReservas) {
        formReservas.submit(); // Dispara la petición POST nativa a Django
      }
    });
  }

  // Controles del paginador de meses del calendario
  if (prevMonth) {
    prevMonth.addEventListener("click", () => { mesOffset--; renderizarCalendario(); });
  }
  if (nextMonth) {
    nextMonth.addEventListener("click", () => { mesOffset++; renderizarCalendario(); });
  }

  // Render inicial de elementos visuales
  renderizarCalendario();

  const parametrosUrl = new URLSearchParams(window.location.search);
  const idServicioUrl = parametrosUrl.get('servicio_id');

  // Validamos que 'idServicioUrl' tenga contenido real y no sea una cadena vacía
  if (idServicioUrl && idServicioUrl.trim() !== "" && selectServicio) {
    selectServicio.value = String(idServicioUrl).trim();
    selectServicio.dispatchEvent(new Event('change'));
  }


  
}

document.addEventListener("DOMContentLoaded", function() {
    const paymentOptions = document.querySelectorAll(".payment-option");
    const selectedMethodDisplay = document.getElementById("selectedMethodDisplay");
    const dropdownBoton = document.getElementById("dropdownMetodoBoton");
    const inputMetodoPago = document.getElementById("input_metodo_pago");
    const summaryPayment = document.getElementById("summaryPayment");

    // Escuchar la selección directa en el Dropdown
    paymentOptions.forEach(option => {
        option.addEventListener("click", function(e) {
            const metodo = this.getAttribute("data-method");
            inputMetodoPago.value = metodo;
            selectedMethodDisplay.textContent = metodo;
            dropdownBoton.textContent = metodo;
            if(summaryPayment) summaryPayment.textContent = metodo;
        });
    });

    // Validar cuando confirman dentro del modal de PSE
    document.getElementById("btnPagarPSE").addEventListener("click", function() {
        inputMetodoPago.value = "PSE";
        selectedMethodDisplay.textContent = "PSE";
        dropdownBoton.textContent = "PSE";
        if(summaryPayment) summaryPayment.textContent = "PSE";
    });

    // Validar cuando confirman dentro del modal de Tarjeta
    document.getElementById("btnPagarCard").addEventListener("click", function() {
        inputMetodoPago.value = "Tarjeta de Crédito";
        selectedMethodDisplay.textContent = "Tarjeta de Crédito";
        dropdownBoton.textContent = "Tarjeta de Crédito";
        if(summaryPayment) summaryPayment.textContent = "Tarjeta de Crédito";
    });

    // Al hacer clic en "Reservar Cita"
    const btnReservar = document.getElementById("btnReservar");
    btnReservar.addEventListener("click", function() {
        const fecha = document.getElementById("input_fecha_seleccionada").value;
        const hora = document.getElementById("input_hora_seleccionada").value;
        const servicio = document.getElementById("servicio").value;
        const barbero = document.getElementById("barbero").value;
        const metodoPago = inputMetodoPago.value;

        if (!fecha || !hora || !servicio || !barbero || !metodoPago) {
            alert("Por favor, asegúrate de seleccionar Fecha, Hora, Servicio, Barbero y un Método de pago.");
            return;
        }

        // Mostrar modal de éxito antes del guardado final
        const successModal = new bootstrap.Modal(document.getElementById('successModal'));
        successModal.show();
    });

    // Enviar formulario POST definitivo a Django al presionar el botón del modal de éxito
    document.getElementById("btnVerMisReservas").addEventListener("click", function() {
        document.getElementById("formReservas").submit();
    });
});
