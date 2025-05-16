fetch('full_sport_by_country.json')
  .then(response => response.json())
  .then(data => {
    // Préparation des séries : { name: sport, data: [{name: pays, value: total}, …] }
    const series = [];
    Object.entries(data).forEach(([country, sports]) => {
      Object.entries(sports).forEach(([sport, medals]) => {
        const total = medals.gold + medals.silver + medals.bronze;
        if (total === 0) return; // on ignore les pays sans médailles pour ce sport

        let serie = series.find(s => s.name === sport);
        if (!serie) {
          serie = { name: sport, data: [] };
          series.push(serie);
        }
        serie.data.push({ name: country, value: total });
      });
    });

    Highcharts.chart('container', {
      chart: {
        type: 'packedbubble',
        height: '100%'
      },
      title: {
        text: 'Médailles totales par pays regroupées par sport',
        align: 'left'
      },
      subtitle: {
        text: 'Source: olympics-statistics.com',
        align: 'left'
      },
      tooltip: {
        useHTML: true,
        pointFormat: '<b>{point.name}</b>: {point.value} médailles'
      },
      plotOptions: {
        packedbubble: {
          minSize: '10%',
          maxSize: '100%',
          zMin: 0,
          layoutAlgorithm: {
            gravitationalConstant: 0.02,
            splitSeries: true,
            seriesInteraction: false,
            dragBetweenSeries: true,
            parentNodeLimit: true
          },
          dataLabels: {
            enabled: true,
            format: '{point.name}',
            filter: {
              property: 'value',   // << correction ici
              operator: '>',
              value: 1
            },
            style: {
              color: 'black',
              textOutline: 'none',
              fontWeight: 'normal'
            }
          }
        }
      },
      series: series
    });
  })
  .catch(err => console.error(err));