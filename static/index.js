document.addEventListener('DOMContentLoaded', function() {
    const toggleButton = document.getElementById('toggleTable');
    const tableContainer = document.getElementById('tableContainer');
    
    if (toggleButton && tableContainer) {
        toggleButton.addEventListener('click', function() {
            if (tableContainer.style.display === 'none') {
                tableContainer.style.display = 'block';
                toggleButton.textContent = 'テーブルを非表示';
            } else {
                tableContainer.style.display = 'none';
                toggleButton.textContent = 'テーブルを表示';
            }
        });
    }
}); 