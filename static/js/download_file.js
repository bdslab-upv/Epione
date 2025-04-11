document.getElementById("download-btn").addEventListener("click", function() {
            // Generar contenido CSV desde la tabla
            var csvContent = "data:text/csv;charset=utf-8,";
            var rows = document.querySelectorAll("table tr");

            rows.forEach(function(row) {
                var rowData = [];
                row.querySelectorAll("td").forEach(function(cell) {
                    rowData.push(cell.textContent.trim());
                });
                csvContent += rowData.join(",") + "\n";
            });

            // Crear un enlace temporal y simular clic para descargar
            var encodedUri = encodeURI(csvContent);
            var link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", "outcomes.csv");
            document.body.appendChild(link);
            link.click();
        });
