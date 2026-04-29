(function () {
  const analyticsCanvas = document.getElementById('analyticsChart') || document.getElementById('studioChart');
  if (!analyticsCanvas || typeof Chart === 'undefined') return;

  fetch(analyticsCanvas.dataset.endpoint)
    .then((r) => r.json())
    .then((rows) => {
      const labels = rows.map((r) => r.date);
      const views = rows.map((r) => r.views);
      new Chart(analyticsCanvas, {
        type: 'line',
        data: {
          labels,
          datasets: [{
            label: 'Views',
            data: views,
            borderColor: '#06b6d4',
            backgroundColor: 'rgba(6,182,212,0.2)',
            tension: 0.3,
            fill: true,
          }],
        },
        options: {
          plugins: { legend: { labels: { color: '#f0f0ff' } } },
          scales: {
            x: { ticks: { color: '#94a3b8' } },
            y: { ticks: { color: '#94a3b8' } },
          },
        },
      });
    })
    .catch(() => {});
})();
