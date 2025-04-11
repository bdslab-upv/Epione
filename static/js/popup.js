const botonCargar = document.getElementById('simulateBtn');
const modalCargando = new bootstrap.Modal(document.getElementById('cargandoModal'), {
    backdrop: 'static',
    keyboard: false // Esto desactiva la capacidad de cerrar el modal al presionar la tecla Esc
});
botonCargar.addEventListener('click', function () {
  // Mostrar el modal de carga
  modalCargando.show();

});

document.addEventListener("DOMContentLoaded", function() {
  // Hacer una solicitud AJAX al servidor para indicar que la carga ha finalizado
  var xhr = new XMLHttpRequest();
  xhr.open("GET", "/carga-finalizada");
  xhr.send();
});