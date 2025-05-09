document.addEventListener('DOMContentLoaded', function() {
    // 移動平均線の表示/非表示
    const toggleMAButton = document.getElementById('toggleMA');
    const chartContainer = document.getElementById('chartContainer');
    
    if (toggleMAButton && chartContainer) {
        toggleMAButton.addEventListener('click', function() {
            const plotlyDiv = chartContainer.querySelector('.js-plotly-plot');
            if (plotlyDiv) {
                const traces = plotlyDiv.data;
                // 移動平均線のトレース（インデックス1,2,3）の表示/非表示を切り替え
                for (let i = 1; i <= 3; i++) {
                    if (traces[i]) {
                        const visible = traces[i].visible;
                        Plotly.restyle(plotlyDiv, {visible: !visible}, i);
                    }
                }
                
                // ボタンのテキストを更新
                if (traces[1].visible) {
                    toggleMAButton.textContent = '移動平均線を非表示';
                } else {
                    toggleMAButton.textContent = '移動平均線を表示';
                }
            }
        });
        
    }

    // 財務データの表示/非表示
    const toggleFinancialDataRawTableButton = document.getElementById('toggleFinancialDataRawTableButton');
    const financialRawDataTableContainer = document.getElementById('financialRawDataTableContainer');
    
    if (toggleFinancialDataRawTableButton && financialRawDataTableContainer) {
        toggleFinancialDataRawTableButton.addEventListener('click', function() {
            if (financialRawDataTableContainer.style.display === 'none') {
                financialRawDataTableContainer.style.display = 'block';
                toggleFinancialDataRawTableButton.textContent = '財務データを非表示';
            } else {
                financialRawDataTableContainer.style.display = 'none';
                toggleFinancialDataRawTableButton.textContent = '財務データを表示';
            }
        });
    }
    
    // テーブルの表示/非表示
    const toggleButton = document.getElementById('toggleTable');
    const tableContainer = document.getElementById('tableContainer');
    
    if (toggleButton && tableContainer) {
        toggleButton.addEventListener('click', function() {
            if (tableContainer.style.display === 'none') {
                tableContainer.style.display = 'block';
                toggleButton.textContent = '日足株価を非表示';
            } else {
                tableContainer.style.display = 'none';
                toggleButton.textContent = '日足株価を表示';
            }
        });
    }
}); 