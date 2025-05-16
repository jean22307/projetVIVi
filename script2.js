// script2.js
// Top 4 des nations par médailles Gold, Silver et Bronze (bar chart)

fetch('fullStat_nation.json')
  .then(res => res.json())
  .then(data => {
    // Calcule le total pour trier, mais conserve séparément chaque type
    const stats = data.map(e => ({
      country: e.country,
      total:   e.gold + e.silver + e.bronze,
      gold:    e.gold,
      silver:  e.silver,
      bronze:  e.bronze
    }));

    // Trie décroissant par total et ne garde que les 4 premiers
    const top4 = stats
      .sort((a, b) => b.total - a.total)
      .slice(0, 4);

    // Prépare les catégories (pays) et les trois séries
    const categories = top4.map(d => d.country);
    const goldData   = top4.map(d => d.gold);
    const silverData = top4.map(d => d.silver);
    const bronzeData = top4.map(d => d.bronze);

    Highcharts.chart('container-bar', {
      chart: { type: 'bar' },
      title: { text: 'Top 4 des nations – Médailles par type' },
      subtitle: { text: 'Source : fullStat_nation.json' },
      xAxis: {
        categories,
        title: { text: null },
        gridLineWidth: 1,
        lineWidth: 0
      },
      yAxis: {
        min: 0,
        title: {
          text: 'Nombre de médailles',
          align: 'high'
        },
        labels: { overflow: 'justify' },
        gridLineWidth: 0
      },
      tooltip: {
        shared: true,
        valueSuffix: ' médailles'
      },
      plotOptions: {
        bar: {
          borderRadius: 5,
          dataLabels: { enabled: true },
          groupPadding: 0.1
        }
      },
      legend: {
        layout: 'vertical',
        align: 'right',
        verticalAlign: 'top',
        x: -40,
        y: 80,
        floating: true,
        borderWidth: 1,
        backgroundColor:
          Highcharts.defaultOptions.legend.backgroundColor || '#FFFFFF',
        shadow: true
      },
      credits: { enabled: false },
      series: [
        { name: 'Gold',   data: goldData   },
        { name: 'Silver', data: silverData },
        { name: 'Bronze', data: bronzeData }
      ]
    });
  })
  .catch(err => console.error('Erreur chargement JSON :', err));
