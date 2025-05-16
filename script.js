// script.js
// Répartition des médailles par pays et par type (map chart)

fetch('fullStat_nation.json')
  .then(response => response.json())
  .then(fullStats => {
    const goldData   = fullStats.map(e => ({ name: e.country, value: e.gold   }));
    const silverData = fullStats.map(e => ({ name: e.country, value: e.silver }));
    const bronzeData = fullStats.map(e => ({ name: e.country, value: e.bronze }));

    Highcharts.getJSON(
      'https://code.highcharts.com/mapdata/custom/world.topo.json',
      topology => {
        Highcharts.mapChart('container-map', {
          chart: { map: topology },
          title: {
            text: 'Répartition des médailles par pays et par type',
            align: 'left', floating: true,
            style: { textOutline: '2px white' }
          },
          mapNavigation: {
            enabled: true,
            enableDoubleClickZoomTo: true,
            buttonOptions: { verticalAlign: 'bottom' }
          },
          mapView: { projection: { name: 'Orthographic', rotation: [60, -30] }, maxZoom: 30 },
          colorAxis: { minColor: '#EFEFEF', maxColor: '#800000' },
          tooltip: {
            headerFormat: '<b>{series.name}</b><br>',
            pointFormat: '{point.name}: {point.value} médailles'
          },
          series: [
            {
              name: 'Gold',
              data: goldData,
              joinBy: 'name',
              states: { hover: { color: '#FFD700' } },
              dataLabels: { enabled: false }
            },
            {
              name: 'Silver',
              data: silverData,
              joinBy: 'name',
              states: { hover: { color: '#C0C0C0' } },
              dataLabels: { enabled: false }
            },
            {
              name: 'Bronze',
              data: bronzeData,
              joinBy: 'name',
              states: { hover: { color: '#CD7F32' } },
              dataLabels: { enabled: false }
            }
          ]
        });
      }
    );
  })
  .catch(err => console.error('Erreur de chargement du JSON :', err));
