// Seleccionar el botón por su ID
var simulateBtn = document.getElementById('simulateBtn');

// Función para verificar el estado de los campos del formulario
function checkFormFields() {
  // Obtener los valores de los campos del formulario
  var population = document.getElementById('steps').value;

  // Verificar si todos los campos tienen valores
  if (population !== '') {
    // Si todos los campos tienen valores, habilitar el botón
    simulateBtn.disabled = false;
  } else {
    // Si algún campo está vacío, deshabilitar el botón
    simulateBtn.disabled = true;
  }
}

document.addEventListener('DOMContentLoaded', function() {
  checkFormFields();

  document.querySelectorAll('form input, form select').forEach(function(input) {
    input.addEventListener('change', checkFormFields);
  });
});
