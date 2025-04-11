 console.log('Script cargado');
        $(document).ready(function() {
            $('#simulationTable').DataTable({
                paging: false,
                info: false,
                searching: false,
                ordering: true
            });

            const rows = document.querySelectorAll('table tbody tr');

            rows.forEach((row, rowIndex) => {
                const cells = row.querySelectorAll('td');

                cells.forEach((cell, cellIndex) => {
                    let valueText = cell.textContent.trim();
                    let value;

                    if (cellIndex === 1) { // Segunda columna
                        value = parseFloat(valueText.replace('%', ''));
                        if (rowIndex === 3) { // Tercera fila (índice 2)
                            if (value > 60) {
                                cell.classList.add('value-red');
                            } else {
                                cell.classList.add('value-green');
                            }
                        } else {
                            if (value > 60) {
                                cell.classList.add('value-green');
                            } else {
                                cell.classList.add('value-red');
                            }
                        }
                    }

                    if (cellIndex === 2) { // Tercera columna
                        if (valueText.toLowerCase().includes('non')) {
                            cell.classList.add('value-red');
                        } else {
                            cell.classList.add('value-green');
                        }
                    }
                });
            });
        });