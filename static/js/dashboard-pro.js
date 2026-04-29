(function () {
  const bars = document.getElementById('chartBars');
  const vals = [28, 45, 38, 60, 42, 74, 55, 82, 63, 91, 70, 84, 77, 95];
  const colors = ['#7c3aed', '#8b46f0', '#9a52f3', '#06b6d4', '#7c3aed', '#06b6d4', '#7c3aed', '#06b6d4', '#7c3aed', '#a78bfa', '#67e8f9', '#7c3aed', '#06b6d4', '#f59e0b'];

  if (bars) {
    vals.forEach((v, i) => {
      const b = document.createElement('div');
      b.className = 'bar';
      b.style.height = v + '%';
      b.style.background = colors[i];
      b.style.opacity = String(0.5 + v / 200);
      bars.appendChild(b);
    });
  }
})();
